"""Run the two clear-image fixtures against preserved Audiveris baselines."""
import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_omr.converter import BASE, convert, read_musicxml
from score_omr.score_audit import compare, snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'output/regression')
    args = parser.parse_args()
    folder = args.output / (datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6])
    folder.mkdir(parents=True)
    results = []
    for name in ['test2', 'test3']:
        _, report = convert(BASE / f'samples/images/{name}.png', folder)
        baseline = BASE / f'samples/baselines/{name}.mxl'
        expected = snapshot(read_musicxml(baseline))
        actual = snapshot(read_musicxml(report['results'][0]['musicxml']))
        diff = compare(expected, actual)
        passed = (len(report['results']) == 1 and not any(diff['edit_distances'].values())
                  and all(diff[k] for k in ('structure_equal', 'contexts_equal', 'annotations_equal', 'credits_equal')))
        results.append({'sample': name, 'passed': passed, 'comparison': diff, 'results': report['results']})
        (folder / 'regression.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(f'{name}: {"PASS" if passed else "DIFFERENT"}', flush=True)
    print(f'Results: {folder}')
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
