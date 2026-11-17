"""Original Source foundation under the existing strict root-only hidden runner."""
from pathlib import Path
import hashlib
import importlib.util
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
support = ROOT / 'experiments/run_neon_scene_followup_20261117.py'
assert hashlib.sha256(support.read_bytes()).hexdigest() == '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
spec = importlib.util.spec_from_file_location('root_original_foundation_runner_support', support)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

def main():
    assert sys.argv.count('--label') == 1
    label = sys.argv[sys.argv.index('--label') + 1]
    assert host.re.fullmatch('[a-z0-9-]{3,70}', label)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=host.REVIEW, text=True).strip() == 'fe9aace86f7a349c90a951ff26d76f746d1e4701'
    assert hashlib.sha256((host.REVIEW / 'tests/source_bone_bindings_unit.gd').read_bytes()).hexdigest() == '80764dea7982a11f1d42a9bcbfb36b74c44edb6e620ddb585fa37dc1c8ab1e09'
    assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=host.REVIEW).strip()
    child = host.REVIEW / 'output' / label / 'source-choices'
    host.CASES = (('foundation', 'verify_source_choice_foundation.py', ['--output', str(child)], label + '/source-choices/verification.json', 370),)
    return host.main()

if __name__ == '__main__':
    raise SystemExit(main())
