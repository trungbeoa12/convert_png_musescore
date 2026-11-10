"""Local image -> Audiveris MusicXML -> MuseScore MSCZ pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
import platform
import importlib.metadata
import xml.etree.ElementTree as ET
from datetime import datetime
from fractions import Fraction

from PIL import Image, ImageOps
from .preprocessing import prepare, straighten_staff_lines
from .score_audit import snapshot, compare, summarize, engine_review, normalize_short_page

PACKAGE_DIR = Path(__file__).resolve().parent
BASE = PACKAGE_DIR.parent
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}


class ConversionError(RuntimeError):
    pass


def find_tool(env_name, candidates):
    configured = os.environ.get(env_name)
    for item in ([configured] if configured else candidates):
        path = Path(item).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        found = shutil.which(str(item))
        if found:
            return found
    raise ConversionError(f'Không tìm thấy {env_name}. Xem phần cài đặt trong README.md.')


def tools():
    return (
        find_tool('AUDIVERIS_BIN', [
            BASE / 'tools/Audiveris.app/Contents/MacOS/Audiveris',
            '/Applications/Audiveris.app/Contents/MacOS/Audiveris', 'audiveris']),
        find_tool('MUSESCORE_BIN', [
            '/Applications/MuseScore 4.app/Contents/MacOS/mscore',
            'MuseScore4', 'mscore', 'musescore']),
    )


def audiveris_command(executable, image, output, adaptive_std=None):
    command = [executable, '-batch', '-transcribe', '-export', '-save']
    if adaptive_std is not None:
        if not 0 <= adaptive_std <= 1.5:
            raise ConversionError('Hệ số nhị phân phải trong khoảng 0–1.5.')
        command += ['-constant', 'org.audiveris.omr.image.AdaptiveDescriptor.meanCoeff=0.7',
                    '-constant', f'org.audiveris.omr.image.AdaptiveDescriptor.stdDevCoeff={adaptive_std}']
    return command + ['-output', str(output), '--', str(image)]


def prepare_image(source: Path, target: Path, enhance=True, profile='auto'):
    try:
        return prepare(source, target, enhance, profile)
    except ValueError as exc:
        raise ConversionError(str(exc)) from exc


def run_command(command, log_path, cancel, timeout, notify):
    if cancel.is_set():
        raise ConversionError('Đã hủy chuyển đổi.')
    notify('Đang chạy ' + Path(command[0]).name + '…')
    with log_path.open('a', encoding='utf-8') as log:
        log.write('\nCOMMAND: ' + repr(command) + '\n')
        log.flush()
        env = os.environ.copy()
        if (BASE / 'tools/tessdata_legacy/eng.traineddata').is_file():
            env.setdefault('TESSDATA_PREFIX', str(BASE / 'tools/tessdata_legacy'))
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        started = time.monotonic()
        try:
            while process.poll() is None:
                if cancel.is_set():
                    raise ConversionError('Đã hủy chuyển đổi.')
                if time.monotonic() - started > timeout:
                    raise ConversionError(f'Quá thời gian chờ {timeout}s. Xem {log_path}')
                cancel.wait(0.2)
            if process.returncode:
                raise ConversionError(f'{Path(command[0]).name} lỗi (mã {process.returncode}). Xem {log_path}')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def read_musicxml(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            container = ET.fromstring(archive.read('META-INF/container.xml'))
            roots = [e.attrib['full-path'] for e in container.iter()
                     if e.tag.split('}')[-1] == 'rootfile']
            if not roots:
                raise ConversionError('MusicXML nén không có bản nhạc.')
            root = ET.fromstring(archive.read(roots[0]))
    else:
        root = ET.parse(path).getroot()
    for element in root.iter():
        element.tag = element.tag.split('}')[-1]
    if root.tag != 'score-partwise':
        raise ConversionError('Chưa hỗ trợ cấu trúc MusicXML này.')
    return root


def inspect_score(path):
    """Check measure extents using backup/forward, chords and grace notes."""
    root = read_musicxml(path)
    warnings, measures, notes = [], 0, 0
    for part in root.findall('part'):
        divisions, expected = 1, None
        for measure in part.findall('measure'):
            measures += 1
            attr = measure.find('attributes')
            if attr is not None:
                divisions = int(attr.findtext('divisions', str(divisions)))
                ts = attr.find('time')
                if ts is not None:
                    beats, types = ts.findall('beats'), ts.findall('beat-type')
                    expected = sum((sum(Fraction(x) for x in b.text.split('+')) * 4 / int(t.text)
                                    for b, t in zip(beats, types)), Fraction()) if beats else None
            cursor, end, onset = Fraction(), Fraction(), Fraction()
            for item in measure:
                if item.tag in ('backup', 'forward'):
                    duration = Fraction(item.findtext('duration', '0')) / divisions
                    cursor += duration * (-1 if item.tag == 'backup' else 1)
                    end = max(end, cursor)
                elif item.tag == 'note':
                    if item.find('pitch') is not None:
                        notes += 1
                    if item.find('grace') is not None:
                        continue
                    duration = Fraction(item.findtext('duration', '0')) / divisions
                    if item.find('chord') is None:
                        onset = cursor
                        cursor += duration
                    end = max(end, onset + duration)
            if expected is None:
                warnings.append(f"Bè {part.get('id')}, ô {measure.get('number')}: thiếu số chỉ nhịp; chưa kiểm chứng được tổng phách.")
            if expected and end != expected:
                warnings.append(f"Bè {part.get('id')}, ô {measure.get('number')}: "
                                f"độ dài {end} phách đen, dự kiến {expected} (có thể là ô lấy đà).")
    if not notes:
        raise ConversionError('Không nhận được nốt nhạc nào. Thử ảnh rõ hơn hoặc cắt sát vùng khuông nhạc.')
    return {'parts': len(root.findall('part')), 'measures': measures,
            'pitched_notes_including_grace': notes, 'warnings': warnings}


def convert(source, output_root=None, enhance=True, notify=print, cancel=None,
            profile='auto', render=True, adaptive_std=None):
    source = Path(source).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ConversionError('Hãy chọn ảnh PNG, JPG, TIFF, BMP hoặc WebP có thật.')
    audiveris, musescore = tools()
    cancel = cancel or threading.Event()
    output_root = Path(output_root or BASE / 'output').resolve()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder = output_root / f'{source.stem}_{stamp}_{uuid.uuid4().hex[:6]}'
    folder.mkdir(parents=True)
    log = folder / 'conversion.log'
    try:
        notify('Chuẩn bị ảnh…')
        prepared = folder / 'input.png'
        shutil.copy2(source, folder / ('original' + source.suffix.lower()))
        image_profile = 'legacy' if profile == 'photo' else profile
        preparation = prepare_image(source, prepared, enhance, image_profile)
        run_command(audiveris_command(audiveris, prepared, folder / 'omr', adaptive_std), log, cancel, 600, notify)
        geometry = None
        first_pass = sorted((folder / 'omr').rglob('*.mxl'))
        first_omr = sorted((folder / 'omr').rglob('*.omr'))
        # Darkness is not evidence of curvature, nor is successful export evidence
        # that a warp improved recognition. Geometry is an explicit experiment.
        use_geometry = enhance and profile == 'photo'
        if use_geometry and first_pass and len(first_omr) == 1:
            notify('Ảnh nền tối/ảnh chụp: thử làm thẳng đường khuông, giữ kết quả lượt đầu…')
            corrected = folder / 'staff_straightened.png'
            geometry = {'selected': False, 'reason': 'Explicit photo profile; experimental selection by user, not an accuracy ranking'}
            try:
                geometry.update(straighten_staff_lines(prepared, first_omr[0], corrected))
                run_command(audiveris_command(audiveris, corrected, folder / 'omr_geometry', adaptive_std),
                            log, cancel, 600, notify)
                second = sorted((folder / 'omr_geometry').rglob('*.mxl'))
                if len(second) != len(first_pass):
                    raise ValueError('Số bản nhạc giữa hai lượt thay đổi; giữ lượt đầu để tránh bỏ mất phần nhạc.')
                for item in second:
                    inspect_score(item)
                geometry['selected'] = True
                geometry['comparison_to_first_pass'] = [compare(snapshot(read_musicxml(a)), snapshot(read_musicxml(b)))
                                                        for a,b in zip(first_pass, second)]
            except (ValueError, ConversionError) as exc:
                if cancel.is_set():
                    raise
                geometry['fallback_reason'] = str(exc)
                preparation['warnings'].append('Không áp dụng sửa hình học: ' + str(exc))
        omr_folder = folder / ('omr_geometry' if geometry and geometry['selected'] else 'omr')
        selected_image = folder / 'staff_straightened.png' if geometry and geometry['selected'] else prepared
        candidates = sorted(omr_folder.rglob('*.mxl'))
        if not candidates:
            candidates = sorted(omr_folder.rglob('*.musicxml'))
        if not candidates:
            raise ConversionError('Audiveris không xuất được MusicXML. Thử ảnh rõ, thẳng và đủ khuông nhạc.')
        notify('Kiểm tra nhịp và xuất MuseScore…')
        results = []
        for index, musicxml in enumerate(candidates, 1):
            if cancel.is_set():
                raise ConversionError('Đã hủy chuyển đổi.')
            stats = inspect_score(musicxml)
            suffix = f'_{index}' if len(candidates) > 1 else ''
            target = folder / f'{source.stem}{suffix}.mscz'
            layout_copy = folder / (target.stem + '_import.musicxml')
            layout_normalized = normalize_short_page(read_musicxml(musicxml), layout_copy)
            import_source = layout_copy if layout_normalized else musicxml
            run_command([musescore, '-o', str(target), str(import_source)], log, cancel, 180, notify)
            if not target.is_file() or not zipfile.is_zipfile(target):
                raise ConversionError('MuseScore chưa tạo được file .mscz hợp lệ.')
            with zipfile.ZipFile(target) as archive:
                if not any(n.endswith('.mscx') for n in archive.namelist()):
                    raise ConversionError('File .mscz không chứa bản nhạc.')
            audit = snapshot(read_musicxml(musicxml))
            raw_xml = folder / (target.stem + '_audiveris.musicxml')
            ET.ElementTree(read_musicxml(musicxml)).write(raw_xml, encoding='utf-8', xml_declaration=True)
            (folder / (target.stem + '_events.json')).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
            # Re-export the saved MSCZ to separate engine errors from importer/exporter changes.
            roundtrip = folder / (target.stem + '_roundtrip.musicxml')
            run_command([musescore, '-o', str(roundtrip), str(target)], log, cancel, 180, notify)
            exported_audit = snapshot(read_musicxml(roundtrip))
            export_comparison = compare(audit, exported_audit)
            review_images = []
            if render:
                run_command([musescore, '-r', '110', '-o', str(folder / (target.stem + '_preview.png')), str(target)],
                            log, cancel, 180, notify)
                review_images = [str(p) for p in sorted(folder.glob(target.stem + '_preview*.png'))]
            results.append({'mscz': str(target), 'musicxml': str(musicxml), 'raw_musicxml': str(raw_xml), **stats,
                            'layout_normalized': layout_normalized, 'import_source': str(import_source),
                            'symbols': summarize(audit), 'roundtrip': str(roundtrip),
                            'export_comparison': export_comparison, 'preview_images': review_images})
        recognition_warnings = [line.strip() for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
                                if any(s in line for s in ('WARN ', 'ERROR ', 'no correct rhythm', 'No timeOffset',
                                                           'too long', 'Missing support for', 'Could not initialize',
                                                           'No reliable beam', 'No stem peak'))]
        location_reviews = []
        engine_metadata = []
        for omr in omr_folder.rglob('*.omr'):
            with zipfile.ZipFile(omr) as archive:
                book = ET.fromstring(archive.read('book.xml'))
                engine_metadata.append({'project': str(omr), 'version': book.get('software-version'),
                                        'build': book.get('software-build'),
                                        'binary_sha256': {n: hashlib.sha256(archive.read(n)).hexdigest()
                                                          for n in archive.namelist() if n.endswith('/BINARY.png')}})
            try:
                location_reviews.append(engine_review(omr, selected_image, folder / ('review_' + omr.stem), log))
            except (ValueError, KeyError, ET.ParseError, OSError) as exc:
                recognition_warnings.append('Không tạo được đánh dấu vị trí: ' + str(exc))
        priority_count = sum(r['priority_count'] for r in location_reviews)
        report = {'source': str(source), 'results': results, 'recognition_warnings': recognition_warnings,
                  'preprocessing': preparation, 'geometry': geometry,
                  'review_priority_count': priority_count,
                  'rhythm_review_regions': sum(r['rhythm_region_count'] for r in location_reviews),
                  'provenance': {'source_sha256': hashlib.sha256((folder / ('original' + source.suffix.lower())).read_bytes()).hexdigest(),
                                 'engine_projects': engine_metadata,
                                 'selected_image_sha256': hashlib.sha256(selected_image.read_bytes()).hexdigest(),
                                 'python': platform.python_version(), 'platform': platform.platform(),
                                 'packages': {name: importlib.metadata.version(name) for name in ('Pillow', 'numpy', 'opencv-python-headless')},
                                 'tessdata_prefix': os.environ.get('TESSDATA_PREFIX', str(BASE / 'tools/tessdata_legacy')),
                                 'adaptive_std_override': adaptive_std,
                                 'audiveris': audiveris, 'musescore': musescore,
                                 'code_sha256': {name: hashlib.sha256((PACKAGE_DIR / name).read_bytes()).hexdigest()
                                                 for name in ('converter.py', 'preprocessing.py', 'score_audit.py')}},
                  'selected_image': str(selected_image),
                  'verification': 'No ground truth supplied to converter. Measure totals and engine grades are diagnostics, not accuracy.',
                  'notice': 'Đã tạo bản chép tự động, CHƯA xác minh đúng nốt. Có thể sai cao độ, trường độ, '
                            'dấu hóa, bè và dấu nối. Đủ phách không có nghĩa là đúng. '
                            'Khung đỏ trong review_overlay là vị trí ưu tiên xem lại; điểm engine không phải phần trăm tin cậy.'}
        (folder / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        lines = [report['notice'], '']
        for result in results:
            lines += [Path(result['mscz']).name,
                      f"{result['parts']} bè; {result['measures']} ô nhịp; {result['pitched_notes_including_grace']} nốt (kể cả hoa mỹ)."]
            lines += result['warnings'] or ['Không phát hiện ô nhịp lệch tổng phách.']
        lines += ['', f'{priority_count} ký hiệu được đánh dấu ưu tiên xem lại; xem review_*/review_overlay.png và locations.json.']
        lines += preparation['warnings']
        if geometry:
            lines += ['Sửa hình học: ' + ('đã dùng lượt hai; lượt đầu giữ ở omr/' if geometry['selected'] else 'giữ lượt đầu')]
        for result in results:
            if (any(result['export_comparison']['edit_distances'].values())
                    or not result['export_comparison']['structure_equal']
                    or not result['export_comparison']['annotations_equal']
                    or not result['export_comparison']['credits_equal']):
                lines += ['Có thay đổi ngữ nghĩa khi MuseScore nhập/xuất; xem export_comparison trong report.json.']
        if recognition_warnings:
            lines += ['', 'Cảnh báo từ bộ nhận dạng (có thể đã bỏ sót nốt):', *recognition_warnings]
        (folder / 'Kiem_tra.txt').write_text('\n'.join(lines), encoding='utf-8')
        notify('Hoàn tất. Hãy nghe và đối chiếu bản nhạc với ảnh gốc.')
        return folder, report
    except Exception as exc:
        (folder / 'ERROR.txt').write_text(str(exc), encoding='utf-8')
        raise ConversionError(f'{exc}\nThư mục kiểm tra: {folder}') from exc


def main():
    parser = argparse.ArgumentParser(description='Chuyển một ảnh bản nhạc sang .mscz bằng Audiveris + MuseScore.')
    parser.add_argument('image', nargs='?')
    parser.add_argument('--output', type=Path, default=BASE / 'output')
    parser.add_argument('--no-enhance', action='store_true')
    parser.add_argument('--profile', choices=['auto', 'legacy', 'original', 'photo', 'illumination', 'deskew'], default='auto')
    parser.add_argument('--no-render', action='store_true', help='Không xuất ảnh xem lại')
    parser.add_argument('--adaptive-std', type=float, help='Hệ số std nhị phân Audiveris (thử nghiệm, 0–1.5); mean=0.7')
    parser.add_argument('--check', action='store_true', help='Kiểm tra đường dẫn công cụ')
    args = parser.parse_args()
    try:
        if args.check:
            print('\n'.join(tools()))
        elif args.image:
            folder, _ = convert(args.image, args.output, not args.no_enhance, profile=args.profile, render=not args.no_render,
                                adaptive_std=args.adaptive_std)
            print(f'Kết quả: {folder}')
        else:
            parser.error('Cần đường dẫn ảnh hoặc --check.')
    except (ConversionError, OSError) as exc:
        parser.exit(1, f'Lỗi: {exc}\n')


if __name__ == '__main__':
    main()
