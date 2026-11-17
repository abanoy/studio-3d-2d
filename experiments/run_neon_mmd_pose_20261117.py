"""Root-only focused MMD pose using the retained scoped followup host."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT.parent / 'has-neon-review-20261116-c2d52ff'
parent = ROOT / 'experiments/run_neon_scene_followup_20261117.py'
raw = parent.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '07e37aa4ddba05e31658f2fe14bda53a25ce0f7646f2c966961a635ef6b85255'
scope = {'__file__': str(parent), '__name__': 'root_mmd_pose_followup_host'}
exec(compile(raw, str(parent), 'exec'), scope)
scope['CASES'] = (('pose', str(ROOT / 'experiments/neon_mmd_pose_check_20261117.py'),
                   [], 'pose-smoke/result.json', 240),)


def main():
    run = REVIEW / 'output/windows-neon-3a3701a-20261117T185401541257'
    before = json.loads((run / 'source-before.json').read_bytes())['source_sha256']
    assert len(before) == 1029 and scope['sources']() == before
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REVIEW).strip() == b'3a3701ab6edfa81dc883759403c170b8555aab07'
    staged = json.loads((ROOT / 'output/PRIVATE-neon-mmd-pose-fixture-stage-20261117/PROVENANCE.json').read_bytes())
    assert staged['all_originals_preserved'] is True and staged['all_copies_equal'] is True and staged['files'] == 18
    for row in staged['rows']:
        for folder, key in ((Path(staged['source']), 'source'), (Path(staged['target']), 'copy')):
            path = folder / row['relative']
            assert scope['sha'](path) == row[key]['sha256']
            info = path.stat()
            assert all(getattr(info, name) == value for name, value in row[key]['identity'].items())
    os.environ['HYBRID_NATIVE_FIXTURES'] = str(ROOT / 'output')
    os.environ['HYBRID_NATIVE_INPUTS'] = r'C:\a\dump'
    os.environ['HYBRID_HECATIA_KRA'] = str(ROOT / 'output/owner-fixtures/hecatia.kra')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['HYBRID_SOURCEIO'] = str(REVIEW / 'output/dependencies/sourceio-fe24260b97ac03b899d9b5d4f0fd7b34772f3647')
    os.environ['HYBRID_BLENDER'] = r'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe'
    os.environ['HYBRID_FFMPEG'] = r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
    result = scope['main']()
    label = sys.argv[sys.argv.index('--label') + 1]
    assert label.startswith('neon-mmd-pose-3a-')
    report = json.loads((REVIEW / 'output' / label / 'verification.json').read_bytes())
    assert result == 0 and report['passed'] is True and len(report['rows']) == 1
    row = report['rows'][0]
    assert row['report']['checks'] == 45 and row['report']['failures'] == 0
    assert row['report']['actual_mmd_tested'] is True and len(row['report']['movies']) == 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
