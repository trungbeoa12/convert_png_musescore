"""Convert an image and optionally compare against evaluation-only MusicXML."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_omr.converter import BASE, convert, read_musicxml
from score_omr.score_audit import compare, snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--profile', choices=['auto', 'legacy', 'original', 'deskew', 'photo', 'illumination'], default='auto')
    parser.add_argument('--output', type=Path, default=BASE / 'output/evaluation')
    args = parser.parse_args()
    if args.reference and not args.reference.is_file():
        parser.error('Reference MusicXML does not exist.')
    folder, report = convert(args.source, args.output, profile=args.profile)
    if args.reference:
        reference = snapshot(read_musicxml(args.reference))
        comparisons = [{'musicxml': r['musicxml'],
                        'comparison': compare(reference, snapshot(read_musicxml(r['musicxml'])))}
                       for r in report['results']]
        (folder / 'reference_comparison.json').write_text(json.dumps(comparisons, indent=2), encoding='utf-8')
        print(json.dumps(comparisons, indent=2))
    print(f'Results: {folder}')


if __name__ == '__main__':
    main()
