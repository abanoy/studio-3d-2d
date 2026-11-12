"""Recreate the retained native face-test fixture from the owner's original RAR.

Uses the checksum manifest in the retained pilot report, existing 7-Zip and the
approved pinned SourceIO runtime. No model data is downloaded or installed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from source_archive import resource_path, RESOURCE_EXTENSIONS

ORIGINAL_SHA256 = 'b0a4b19afc4cf8d8a17351848e11cf4738fa0a7436d58699a66a4c4be501a50a'
MEMBER = 'mima/models/koikatsu/touhou/mima head.mdl'


def identity(path):
    return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pilot-report', type=Path, default=ROOT / 'output/sfm-face-pilot.json')
    parser.add_argument('--seven-zip', type=Path, default=Path(r'C:\Program Files\7-Zip\7z.exe'))
    parser.add_argument('--sourceio', type=Path)
    options = parser.parse_args()
    source = options.archive.resolve(strict=True)
    report_path = options.pilot_report.resolve(strict=True)
    folder = options.output.resolve()
    if not folder.is_relative_to(ROOT / 'output') or folder == ROOT / 'output' or folder.exists():
        parser.error('Choose a new session-owned directory inside this checkout/output.')
    pilot = json.loads(report_path.read_bytes())
    before = identity(source)
    assert source.stat().st_size <= 512 * 1024 * 1024
    assert before[0] == pilot['source_sha256'] == ORIGINAL_SHA256, 'Original Mima archive checksum differs.'
    stage = folder / 'stage'
    stage.mkdir(parents=True, exist_ok=False)
    (folder / 'historical-pilot.json').write_bytes(report_path.read_bytes())
    rows = []
    total = 0
    for name, expected in pilot['staged_sha256'].items():
        name = resource_path(name)
        target = stage / name
        assert target.resolve().is_relative_to(stage.resolve())
        assert Path(name).suffix.lower() in RESOURCE_EXTENSIONS
        result = subprocess.run([str(options.seven_zip), 'x', '-so', '-spd', str(source), name],
                                capture_output=True, check=True, timeout=30)
        assert hashlib.sha256(result.stdout).hexdigest() == expected, name
        total += len(result.stdout)
        assert total <= 512 * 1024 * 1024
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)
        rows.append({'path': name, 'bytes': len(result.stdout), 'sha256': expected})
    assert MEMBER in pilot['staged_sha256'] and identity(source) == before
    receipt = {'source': str(source), 'original_sha256': before[0], 'original_mtime_ns': before[1],
               'resource_files': rows, 'bytes': total, 'original_unchanged': True}
    (folder / 'staging.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    bundle = folder / 'prepared-head'
    args = [sys.executable, '-u', 'tools/prepare_source.py', str(stage / MEMBER), '--output', str(bundle)]
    if options.sourceio:
        args += ['--sourceio', str(options.sourceio.resolve(strict=True))]
    with (folder / 'prepare.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(args, cwd=ROOT, stdout=log, stderr=log, timeout=250)
    assert result.returncode == 0, folder / 'prepare.log'
    assert identity(source) == before
    assert all(hashlib.sha256((stage / row['path']).read_bytes()).hexdigest() == row['sha256'] for row in rows)
    glb = bundle / 'scene.glb'
    pilot.update(folder=str(folder), bundle=str(bundle), source=str(source),
                 archive_stat=[source.stat().st_size, source.stat().st_mtime_ns], staged_mdl=str(stage / MEMBER),
                 preparation_complete=True, parameters=json.loads((bundle / 'parameters.json').read_bytes()),
                 glb_bytes=glb.stat().st_size, glb_sha256=identity(glb)[0], source_and_stage_unchanged=True)
    report_path.write_text(json.dumps(pilot, indent=2), encoding='utf-8')
    print(json.dumps({'bundle': str(bundle), 'resource_files': len(rows), 'staged_bytes': total,
                      'glb_sha256': pilot['glb_sha256'], 'original_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
