"""Controlled image trials. Never use reference notes to modify engine output."""
import argparse
import hashlib
import json
import shutil
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_omr.converter import BASE, audiveris_command, prepare_image, read_musicxml, run_command, tools
from score_omr.preprocessing import deskew_image
from score_omr.score_audit import compare, snapshot, summarize

VARIANTS = ('control', 'deskew', 'light_denoise', 'scale_150', 'adaptive_0.3', 'adaptive_0.5')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--output', type=Path, default=BASE / 'output/trials')
    parser.add_argument('--variants', default=','.join(VARIANTS), help='Comma-separated variants: ' + ', '.join(VARIANTS))
    args = parser.parse_args()
    selected = args.variants.split(',')
    if not selected or any(v not in VARIANTS for v in selected) or len(set(selected)) != len(selected):
        parser.error('Unknown or repeated variant.')
    if not args.source.is_file():
        parser.error('Source image does not exist.')
    reference = snapshot(read_musicxml(args.reference)) if args.reference else None
    audiveris, _ = tools()
    folder = args.output / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    original = folder / ('original' + args.source.suffix.lower())
    shutil.copy2(args.source, original)
    prepared = folder / 'legacy.png'
    preparation = prepare_image(original, prepared, profile='legacy')
    a = np.array(Image.open(prepared))
    results = []
    for name in selected:
        target_folder = folder / name
        target_folder.mkdir()
        metadata = {}
        if name == 'deskew':
            im, metadata = deskew_image(Image.fromarray(a))
            img = np.array(im)
        elif name == 'light_denoise':
            img = cv2.GaussianBlur(a, (3, 3), .4)
            metadata = {'kernel': [3, 3], 'sigma': .4}
        elif name == 'scale_150':
            img = cv2.resize(a, None, fx=.75, fy=.75, interpolation=cv2.INTER_AREA)
            metadata = {'scale_relative_to_legacy': .75, 'interpolation': 'INTER_AREA'}
        else:
            img = a
        image_path = target_folder / 'input.png'
        Image.fromarray(img).save(image_path)
        adaptive_std = float(name.split('_')[1]) if name.startswith('adaptive_') else None
        command = audiveris_command(audiveris, image_path, target_folder / 'omr', adaptive_std)
        manifest = {'command': command, 'operations': metadata, 'preparation': preparation,
                    'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                    'input_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                    'size_width_height': [img.shape[1], img.shape[0]]}
        (target_folder / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        try:
            run_command(command, target_folder / 'conversion.log', threading.Event(), 600, print)
            paths = sorted((target_folder / 'omr').rglob('*.mxl'))
            if len(paths) != 1:
                raise ValueError(f'Expected one score for comparison, got {len(paths)}; inspect all engine outputs.')
            score = snapshot(read_musicxml(paths[0]))
            result = {'variant': name, 'musicxml': str(paths[0]), 'summary': summarize(score)}
            if reference:
                result['comparison'] = compare(reference, score)
        except Exception as exc:
            result = {'variant': name, 'error': str(exc)}
        results.append(result)
        (folder / 'trial_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2), flush=True)
    print(f'Results: {folder}')
    return 1 if any('error' in r for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
