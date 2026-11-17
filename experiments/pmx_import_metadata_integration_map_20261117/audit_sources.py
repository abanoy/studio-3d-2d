"""Read explicit public source files; rerun authored CPU reader tests only."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
READER = ROOT / 'experiments/pmx_physics_native_reader_prototype_20261117'
PROTOCOL = ROOT / 'experiments/pmx_native_read_qualification_protocol_20261117'
SOURCE_NAMES = (
    'tools/prepare_mmd.py', 'tools/blender_mmd_bridge.py', 'tools/mmd_ik.py',
    'tools/asset_audit.py', 'tools/has_project.py',
    'src/pose_editor.gd', 'src/model.gd', 'src/secondary_rig.gd',
    'src/physics_rig.gd', 'src/source_secondary.gd', 'src/scene3d.gd',
    'src/source_shape.gd', 'src/expression_presets.gd', 'src/world_document.gd',
    'src/world_runtime.gd', 'src/storage.gd', 'src/asset_package.gd',
    'src/has_project.gd', 'src/has_project_loader.gd', 'src/source_import.gd',
    'docs/RESUME_MASTER_PLAN.md', 'docs/standard_model.md', 'docs/import_physics.md',
)


def sha(data): return hashlib.sha256(data).hexdigest()


def save(name, obj):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def regular(path):
    for part in (path, *path.parents):
        assert not part.is_symlink() and not getattr(part.lstat(), 'st_file_attributes', 0) & 0x400
    assert path.is_file()


def frozen_packet(folder, expected):
    index_raw = (folder / 'INDEX.json').read_bytes()
    assert sha(index_raw) == expected
    index = json.loads(index_raw)
    for row in index['payloads']:
        path = folder / row['path']; regular(path)
        data = path.read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    return {'path': folder.relative_to(ROOT).as_posix(), 'INDEX_sha256': expected,
            'payloads_verified': len(index['payloads'])}


def main():
    assert not (HERE / 'INDEX.json').exists()
    packets = [
        frozen_packet(READER, '9946bf2bccbe5e289fea013ec702c97775b33b9a64dc3bce7979d21d08e92487'),
        frozen_packet(PROTOCOL, 'c36c29928185bd9ce8cf521caf43bb873a0ca171bff847e0a9c5f6772cd099a8'),
    ]
    source = {}
    for name in SOURCE_NAMES:
        path = ROOT / name; regular(path)
        data = path.read_bytes()
        source[name] = {'bytes': len(data), 'sha256': sha(data)}
    sys.path.insert(0, str(READER))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(
        unittest.defaultTestLoader.discover(str(READER), pattern='test_*.py'))
    save('CPU_RECEIPT.json', {'format': 'has_pmx_integration_map_existing_reader_cpu_rerun_1',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'passed': result.wasSuccessful(), 'stdout': output.getvalue(),
        'authored_synthetic_only': True, 'native_model_reads_or_engine_runs': False})
    assert result.wasSuccessful() and result.testsRun == 33
    for name, row in source.items():
        data = (ROOT / name).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
    assert frozen_packet(READER, packets[0]['INDEX_sha256']) == packets[0]
    assert frozen_packet(PROTOCOL, packets[1]['INDEX_sha256']) == packets[1]
    save('SOURCE_AUDIT.json', {'format': 'has_pmx_import_metadata_source_map_1',
        'passed': True, 'scope': 'SOURCE_REVIEW_AND_EXISTING_SYNTHETIC_CPU_ONLY',
        'source_identities_before_after_equal': source, 'sealed_dependencies': packets,
        'proposed_capsule_location': 'asset.extras.has_native_physics_archive',
        'location_is_design_only': True, 'production_integration_implemented': False,
        'native_qualification_performed': False,
        'native_assets_engines_CIM_remote_Git_or_active_review_read_or_modified': False,
        'portable_capacity_compatibility_or_solver_claimed': False})
    files = []
    for path in sorted(HERE.iterdir(), key=lambda p: p.name.lower()):
        regular(path); data = path.read_bytes()
        files.append({'path': path.name, 'bytes': len(data), 'sha256': sha(data)})
    save('INDEX.json', {'format': 'has_source_experiment_index_1', 'packet': HERE.name,
        'status': 'SEALED_SOURCE_ONLY_IMPLEMENTATION_MAP_NOT_ADOPTION', 'files': files})
    print(json.dumps({'passed': True, 'reader_CPU_methods': result.testsRun,
        'source_files': len(source), 'INDEX_sha256': sha((HERE / 'INDEX.json').read_bytes())}))


if __name__ == '__main__': main()
