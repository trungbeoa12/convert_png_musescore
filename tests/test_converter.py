import sys
import tempfile
import threading
import unittest
from pathlib import Path
from PIL import Image

from score_omr.converter import ConversionError, inspect_score, prepare_image, run_command
from score_omr.converter import read_musicxml
from score_omr.score_audit import snapshot, compare


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def score(self, body):
        path = self.path / 'score.musicxml'
        path.write_text('<score-partwise><part id="P1"><measure number="1">'
                        '<attributes><divisions>4</divisions><time><beats>2</beats>'
                        '<beat-type>4</beat-type></time></attributes>' + body +
                        '</measure></part></score-partwise>')
        return path

    def test_grace_does_not_add_time_and_chord_does_not_double_time(self):
        note = '<pitch><step>C</step><octave>4</octave></pitch>'
        path = self.score(f'<note><grace/>{note}</note><note>{note}<duration>8</duration></note>'
                          f'<note><chord/>{note}<duration>8</duration></note>')
        report = inspect_score(path)
        self.assertEqual(report['warnings'], [])
        self.assertEqual(report['pitched_notes_including_grace'], 3)

    def test_backup_for_second_voice_and_incomplete_measure(self):
        n = '<note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>'
        self.assertEqual(len(inspect_score(self.score(n))['warnings']), 1)
        self.assertEqual(inspect_score(self.score(n + n + '<backup><duration>8</duration></backup>' + n + n))['warnings'], [])

    def test_blank_recognition_is_not_success(self):
        with self.assertRaises(ConversionError):
            inspect_score(self.score('<note><rest/><duration>8</duration></note>'))

    def test_transparent_background_becomes_white(self):
        source, target = self.path / 'in.png', self.path / 'out.png'
        Image.new('RGBA', (100, 100), (0, 0, 0, 0)).save(source)
        prepare_image(source, target)
        with Image.open(target) as im:
            self.assertEqual(im.getpixel((80, 80)), 255)

    def test_cancel_terminates_child(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaisesRegex(ConversionError, 'hủy'):
            run_command([sys.executable, '-c', 'import time; time.sleep(30)'],
                        self.path / 'log', cancel, 60, lambda _: None)

    def test_missing_time_is_not_reported_as_valid(self):
        path = self.score('<note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>')
        path.write_text(path.read_text().replace('<time><beats>2</beats><beat-type>4</beat-type></time>', ''))
        self.assertIn('thiếu số chỉ nhịp', inspect_score(path)['warnings'][0])

    def test_longer_chord_member_extends_measure(self):
        pitch = '<pitch><step>C</step><octave>4</octave></pitch>'
        path = self.score(f'<note>{pitch}<duration>4</duration></note><note><chord/>{pitch}<duration>12</duration></note>')
        self.assertIn('độ dài 3', inspect_score(path)['warnings'][0])

    def test_enough_beats_does_not_hide_pitch_error(self):
        p = self.score('<note><pitch><step>C</step><octave>4</octave></pitch><duration>8</duration></note>')
        reference = snapshot(read_musicxml(p))
        p.write_text(p.read_text().replace('<step>C</step>', '<step>D</step>'))
        self.assertEqual(inspect_score(p)['warnings'], [])
        comparison = compare(reference, snapshot(read_musicxml(p)))
        self.assertEqual(comparison['edit_distances']['pitch'], 1)
        self.assertEqual(comparison['edit_distances']['duration'], 0)
        self.assertEqual(comparison['changed_event_regions'][0]['actual'][0]['measure'], '1')

    def test_auto_preserves_legacy_pixels_for_clear_input(self):
        from PIL import ImageDraw, ImageOps
        source, target = self.path / 'clear.png', self.path / 'input.png'
        im = Image.new('L', (400, 200), 255)
        draw = ImageDraw.Draw(im)
        for y in range(60, 120, 12):
            draw.line((20, y, 380, y), fill=0, width=2)
        draw.ellipse((60, 70, 65, 75), fill=0)
        im.save(source)
        expected = ImageOps.expand(ImageOps.autocontrast(im, cutoff=0.1).resize((800, 400), Image.Resampling.BICUBIC), 30, 255)
        info = prepare_image(source, target)
        with Image.open(target) as actual:
            self.assertEqual(actual.tobytes(), expected.tobytes())
        self.assertFalse(info['uneven_or_dark_paper'])

    def test_geometry_rejects_incomplete_staff(self):
        from zipfile import ZipFile
        from score_omr.preprocessing import straighten_staff_lines
        source, omr = self.path / 'image.png', self.path / 'book.omr'
        Image.new('L', (200, 100), 255).save(source)
        with ZipFile(omr, 'w') as z:
            z.writestr('sheet#1/sheet#1.xml', '<sheet><staff><lines><line/></lines></staff></sheet>')
        with self.assertRaisesRegex(ValueError, '5 đường'):
            straighten_staff_lines(source, omr, self.path / 'warped.png')

    def test_short_page_layout_fix_keeps_all_music(self):
        from score_omr.score_audit import normalize_short_page
        import xml.etree.ElementTree as ET
        p = self.score('<note><pitch><step>C</step><octave>4</octave></pitch><duration>8</duration></note>')
        root = read_musicxml(p)
        root.insert(0, ET.fromstring('<defaults><scaling><millimeters>7</millimeters><tenths>40</tenths></scaling>'
                                    '<page-layout><page-height>300</page-height><page-width>1000</page-width></page-layout></defaults>'))
        before = snapshot(root)
        target = self.path / 'import.musicxml'
        self.assertTrue(normalize_short_page(root, target))
        self.assertEqual(before, snapshot(read_musicxml(target)))
        self.assertEqual(root.findtext('defaults/page-layout/page-height'), '300')

    def test_same_flat_notes_different_measures_are_reported(self):
        import xml.etree.ElementTree as ET
        p = self.score('<note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>'
                       '<note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration></note>')
        root = read_musicxml(p)
        before = snapshot(root)
        measure = root.find('part/measure')
        note = measure.findall('note')[-1]
        measure.remove(note)
        ET.SubElement(root.find('part'), 'measure', number='2').append(note)
        result = compare(before, snapshot(root))
        self.assertEqual(result['edit_distances']['pitch_duration'], 0)
        self.assertFalse(result['structure_equal'])

    def test_ocr_and_barline_change_are_reported(self):
        import xml.etree.ElementTree as ET
        p = self.score('<note><pitch><step>C</step><octave>4</octave></pitch><duration>8</duration></note>')
        root = read_musicxml(p)
        credit = ET.SubElement(ET.SubElement(root, 'credit'), 'credit-words')
        credit.text = 'Tempo di marcia'
        before = snapshot(root)
        credit.text = 'Tempo dim'
        ET.SubElement(ET.SubElement(root.find('part/measure'), 'barline'), 'bar-style').text='light-heavy'
        result = compare(before, snapshot(root))
        self.assertFalse(result['credits_equal'])
        self.assertFalse(result['annotations_equal'])


if __name__ == '__main__':
    unittest.main()
