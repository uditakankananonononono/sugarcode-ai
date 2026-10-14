"""Run explicitly listed source mutants against a pair's unchanged unittest suite.

Every mutant is compiled into a separate source file and loaded by the test suite
through MUTANT_MODULE/MUTANT_PATH. A nonzero test exit kills it; timeouts and
invalid source are reported separately, never counted as killed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads(Path(args.manifest).read_text())
    env = dict(os.environ, PYTHONPATH=str(root / 'src'))
    cmd = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/extra_doc', '-p', manifest['suite']]
    baseline = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    if baseline.returncode:
        print(baseline.stdout + baseline.stderr)
        raise SystemExit('baseline failed')
    results = []
    with tempfile.TemporaryDirectory() as directory:
        for index, mutant in enumerate(manifest['mutants']):
            source = (root / mutant['source']).read_text()
            if source.count(mutant['old']) != 1:
                raise SystemExit('mutation anchor is not unique: ' + mutant['name'])
            changed = source.replace(mutant['old'], mutant['new'])
            try:
                compile(changed, mutant['source'], 'exec')
            except SyntaxError:
                status = 'invalid'
            else:
                path = Path(directory) / ('mutant_' + str(index) + '.py')
                path.write_text(changed)
                altered = dict(env, MUTANT_MODULE=mutant['module'], MUTANT_PATH=str(path))
                try:
                    proc = subprocess.run(cmd, cwd=root, env=altered, capture_output=True, text=True, timeout=20)
                    status = 'killed' if proc.returncode else 'survived'
                except subprocess.TimeoutExpired:
                    status = 'timeout'
            results.append({'name': mutant['name'], 'status': status})
    print(json.dumps({'python': sys.version.split()[0], 'baseline': 'passed', 'results': results,
                      'counts': {key: sum(r['status'] == key for r in results)
                                 for key in ('killed', 'survived', 'timeout', 'invalid')}}, indent=2))
    return any(r['status'] not in ('killed', 'survived') for r in results)


if __name__ == '__main__':
    sys.exit(main())
