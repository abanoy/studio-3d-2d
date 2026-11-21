"""Focused opt-in following checks; optionally use an existing prepared native snapshot."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tests'))
from run import command
from verify_character_parts import windows_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-snapshot', type=Path)
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()
    if args.benchmark and not args.native_snapshot:
        parser.error('--benchmark requires --native-snapshot')
    output = ROOT/'output'/('character-parts-follow-'+str(time.time_ns()))
    output.mkdir(parents=True)
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE='1', HYBRID_PYTHON=sys.executable)
    for key, leaf in (('APPDATA', 'Roaming'), ('LOCALAPPDATA', 'Local')):
        folder = output/leaf; folder.mkdir(); env[key] = str(folder)
    log = output/'engine.log'
    extra = ['--audio-driver', 'Dummy', '--log-file', str(log)]
    if args.native_snapshot:
        extra += ['--', str(args.native_snapshot.resolve(strict=True))]
    script = 'tests/character_parts_follow_benchmark.gd' if args.benchmark else 'tests/character_parts_follow_smoke.gd'
    engine = command(script, headless=True, extra=extra)
    if os.name == 'nt':
        code = windows_case(engine, output, env)
    else:
        completed = subprocess.run(engine, cwd=ROOT, env=env, capture_output=True, timeout=125)
        code = completed.returncode
        (output/'process-stdout.log').write_bytes(completed.stdout)
        (output/'process-stderr.log').write_bytes(completed.stderr)
    text = log.read_text(encoding='utf-8', errors='replace')
    print(text)
    prefix = 'PARTS_FOLLOW_BENCHMARK ' if args.benchmark else 'CHARACTER_PARTS_FOLLOW '
    reports = [json.loads(line[len(prefix):]) for line in text.splitlines() if line.startswith(prefix)]
    expected = 54 if args.native_snapshot else 47
    valid = len(reports) == 1 and reports[0].get('authored_poses_unchanged') is True if args.benchmark else reports == [{'checks': expected, 'failures': 0}]
    if code != 0 or re.search(r'SCRIPT ERROR|^ERROR:|^FAIL |ObjectDB instances leaked', text, re.M) or not valid:
        raise RuntimeError('Parts following check failed: '+str(output))
    result = {'status': 'MEASURED' if args.benchmark else 'PASS', 'checks': 0 if args.benchmark else expected,
              'actual_prepared_native_rigs': bool(args.native_snapshot),
              'native_fidelity_qualified': False, 'output': str(output)}
    if args.benchmark:
        result['benchmark'] = reports[0]
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
