"""Root-only unchanged native catalogue/comparison/height checks with fixture override."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
support = ROOT / 'experiments/run_neon_scene_followup_20261117.py'
assert hashlib.sha256(support.read_bytes()).hexdigest() == '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
spec = importlib.util.spec_from_file_location('root_catalogue_original_strong_runner', support)
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=host.REVIEW, text=True).strip() == '00bf0f916a549f5e858cb39dd91a149071fd5181'
    for name, pin in (('tests/verify_shape_catalog.py', '54431c2c486bce9828ec47ebe046da9f413b3854e8c0290829c24183fe72e057'),
                      ('tests/verify_character_height.py', 'cccfb7d472b5d552cbd3cfc07dc9058c1789b9c1947f6a1a548c924dd38a3f79')):
        assert host.sha(host.REVIEW / name) == pin
    assert not subprocess.check_output(['git', 'diff', '--name-only', '--', 'src', 'tests', 'tools', 'data', 'examples', 'project.godot', 'main.tscn', 'run.py', 'launch.pyw'], cwd=host.REVIEW).strip()
    prepared = json.loads((ROOT / 'experiments/neon_shape_catalog_fixture_actual_inputs_20261117/PREPARATION.json').read_bytes())
    scene = Path(prepared['bundle']) / 'scene.glb'
    assert scene.stat().st_size == prepared['scene']['bytes'] and host.sha(scene) == prepared['scene']['sha256']
    assert host.sha(Path(prepared['descriptor_path'])) == prepared['descriptor_sha256']
    os.environ['HYBRID_NATIVE_FIXTURES'] = str(ROOT / 'output')
    host.CASES = (('catalogue', 'verify_shape_catalog.py', [], 'shape-catalog-verification.json', 250),
                  ('comparison', 'verify_shape_comparison.py', [], 'shape-comparison-verification.json', 270),
                  ('height', 'verify_character_height.py', [], 'character-height-verification.json', 390))
    return host.main()

if __name__ == '__main__':
    raise SystemExit(main())
