"""Root-only original camera and Neon/control checks after the one-call fix."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
support = ROOT / 'experiments/run_neon_scene_followup_20261117.py'
assert hashlib.sha256(support.read_bytes()).hexdigest() == '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
spec = importlib.util.spec_from_file_location('root_original_camera_neon_strong_runner', support)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

def main():
    original = json.loads((host.REVIEW / 'output/windows-neon-00bf0f9-replay2-20261117T155709412051/source-before.json').read_bytes())
    current = host.sources()
    expected = {
        'src/app.gd': '79b34e7d591f433e060edf72888d22443d1a0fc5e22dd2a246eb77c83fcad1b6',
        'tests/helper_preview_port_files.json': 'e4fd9597bbf1f9371cece5379a62c0982f53bbc32e83fafef13e19c361beebba',
        'tests/wind_review_port_files.json': '2db0f61835d9b1918385a31202123b7cbf2e993b047d608a9f0dd1eec4b84de7',
    }
    assert len(current) == 1029 and set(current) == set(original['source_sha256'])
    assert {n for n in current if current[n] != original['source_sha256'][n]} == set(expected)
    assert all(current[n] == pin for n, pin in expected.items())
    assert host.sha(host.REVIEW / 'tests/camera_range_smoke.gd') == 'e8b8287451874d26fed4f6ed7d91e463322ed08af179fc80b330150cde841bef'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=host.REVIEW).strip() != b'00bf0f916a549f5e858cb39dd91a149071fd5181'
    assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=host.REVIEW).strip()
    os.environ['HYBRID_NATIVE_FIXTURES'] = str(ROOT / 'output')
    os.environ['HYBRID_SOURCEIO'] = str(host.REVIEW / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
    os.environ['HYBRID_FFMPEG'] = r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
    host.CASES = (
        ('camera', 'verify_camera_range.py', [], 'camera-range-verification.json', 270),
        ('neon', 'verify_neon_workspace.py', ['--lease-confirmed', '--parse-scripts'], 'neon-workspace-verification.json', 990),
        ('controls', 'verify_workspace_controls.py', [], 'workspace-controls-verification.json', 330),
    )
    return host.main()

if __name__ == '__main__':
    raise SystemExit(main())
