"""Resolve native catalogue inputs against current saved fixture provenance.

Historical height-audit paths are observations, not portable fixture inputs.
Current saved projects supply root orientation and metadata only when their
embedded asset checksum matches the catalogue's actual source bytes.
"""
from pathlib import Path
import hashlib
import json
import zipfile
from native_fixture_root import fixture_output

ROOT = Path(__file__).resolve().parents[1]


def catalogue_native_plans():
    report_path = ROOT / 'output/shape-catalog-verification.json'
    if not report_path.is_file():
        return []
    report = json.loads(report_path.read_bytes())
    plans = json.loads((Path(report['folder']) / 'catalogue-plans.json').read_bytes())[1:]
    saved = {}
    for relative in ('pose-smoke/miku-project', 'source-smoke/source-project', 'sfm-smoke/project'):
        folder = fixture_output() / relative
        if not (folder / 'project.json').is_file():
            continue
        project = json.loads((folder / 'project.json').read_bytes())
        rows = project.get('world', {}).get('objects', [])
        if not rows and project.get('model'):
            rows = [project['model']]
        for row in rows:
            if row.get('kind', 'model') != 'model':
                continue
            path = (folder / row['path']).resolve(strict=True)
            assert path.is_relative_to(folder.resolve()), 'Native fixture asset escapes its project'
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == row['sha256'], 'Native fixture asset checksum differs'
            if row.get('metadata', {}).get('native_parameters'):
                saved[digest] = row
    result = []
    for plan in plans:
        path = Path(plan['source']).resolve(strict=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row = saved.get(digest, {})
        result.append({**plan, 'source': str(path), 'source_sha256': digest,
                       'rotation_xyzw': row.get('rotation_xyzw', [0, 0, 0, 1]),
                       'metadata': row.get('metadata', plan.get('metadata', {})),
                       'orientation_provenance': 'checksum-matched current saved fixture' if row else 'prepared GLB coordinate frame'})
    return result


def recorded_native_models():
    """Use this fixture root's current core recording, retaining exact key data."""
    report_path = fixture_output() / 'physics-recording-result.json'
    if not report_path.is_file():
        return [], None
    report = json.loads(report_path.read_bytes())
    if not report.get('native_models', 0):
        return [], None
    packed = Path(report['folder']) / 'native-recording.has'
    with zipfile.ZipFile(packed) as archive:
        project = json.loads(archive.read('project.json'))
    models = [row for row in project['world']['objects'] if row.get('kind') == 'model']
    assert len(models) >= report['native_models'], 'Native recorded models are missing from the packed fixture'
    return models, packed
