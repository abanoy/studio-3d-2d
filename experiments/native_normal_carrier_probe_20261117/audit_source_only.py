"""Preparation audit only: pinned tool sources + synthetic Python tests. No native staging."""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCK = ROOT / 'experiments/replay_audio_fix_20261115/builder/input-lock.json'
READER = ROOT / 'experiments/resume_root_20261115/audit_protected_inputs_before_cleanup.py'
PINS = {'lock': '3bb7c2ce75f55dcb53143aab0df5ab8b39c68180617092664a579126fb09cfb6',
        'reader': '5be1d34aa6aced8fc112bee3ecadd489be9b7f38ab710553385bfd77ca500d83'}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def assignments(path, name):
    tree = ast.parse(path.read_bytes().decode('utf-8'))
    values = [node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    assert len(values) == 1
    return ast.literal_eval(values[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    destination = options.output.resolve()
    assert destination.parent in (HERE, ROOT / 'output') and destination.suffix == '.json' and not destination.exists()
    assert sha(LOCK.read_bytes()) == PINS['lock'] and sha(READER.read_bytes()) == PINS['reader']
    lock = json.loads(LOCK.read_bytes())
    roles = assignments(ROOT / 'experiments/normal_setter_boundary_sentinel_20261117/setter_support.py', 'ROLES')
    assert type(roles) is set and len(roles) == 26
    spec = importlib.util.spec_from_file_location('carrier_preparation_source_identity', READER)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    exporter = Path(lock['exporter_root'])
    before = {'SourceIO': reader.metadata_map(reader.SOURCEIO), 'exporter': reader.metadata_map(exporter, 'exporter')}
    assert before['SourceIO'] == lock['sourceio_files'] and len(before['SourceIO']) == 574
    assert before['exporter'] == lock['exporter_noncache_sources'] and len(before['exporter']) == 120
    assert len(lock['runtime_executables']) == 6
    # No runtime executable identities or owner inputs are read by this audit.
    command = [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_observer_and_joins.py', '-v']
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert process.returncode == 0 and 'Ran 16 tests' in process.stderr and process.stderr.rstrip().endswith('OK')
    after = {'SourceIO': reader.metadata_map(reader.SOURCEIO), 'exporter': reader.metadata_map(exporter, 'exporter')}
    assert before == after
    bridge = ROOT / 'tools/blender_source_bridge.py'
    overlay_source = ROOT / 'tools/source_bone_export.py'
    overlay = assignments(overlay_source, 'EXPLICIT_KWARGS')
    assert len(overlay) == 10
    flags = {'export_format': 'GLB', 'use_selection': True, 'export_animations': False,
             'export_cameras': False, 'export_lights': True, 'export_extras': False,
             'export_yup': True, 'export_image_format': 'AUTO'}
    gltf_calls = [node for node in ast.walk(ast.parse(bridge.read_bytes().decode())) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'gltf']
    assert len(gltf_calls) == 1
    actual_flags = {keyword.arg: ast.literal_eval(keyword.value) for keyword in gltf_calls[0].keywords if keyword.arg != 'filepath'}
    assert actual_flags == flags
    report = {'format': 'has_carrier_next_probe_source_only_audit_1',
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'native_stage_ready': False, 'native_stager_or_launcher_executed': False,
              'native_assets_or_private_arrays_read': False, 'installed_exporter_methods_executed': False,
              'engines_CIM_Git_or_main_review_source_edits': False,
              'original_primary_role_names': sorted(roles), 'primary_roles': 26,
              'tool_source_catalogues_before_after_exact': {'SourceIO': 574, 'exporter': 120},
              'catalogue_metadata_sha256': {key: sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()) for key, value in before.items()},
              'runtime_executable_count_from_lock_only': 6, 'runtime_executable_identities_freshly_checked': False,
              'source_refs': {str(path): sha(path.read_bytes()) for path in [LOCK, READER, bridge, overlay_source,
                  exporter / 'blender/exp/primitive_extract.py', exporter / 'blender/exp/material/encode_image.py',
                  exporter / 'blender/exp/material/image.py']},
              'common_bridge_export_flags': flags, 'conditional_source_bone_export_overlay': overlay,
              'historical_original_B_option_branch_qualified': False,
              'tests': 16, 'failures': 0, 'errors': 0, 'test_command': command,
              'test_stdout': process.stdout, 'test_stderr': process.stderr}
    with destination.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'source_only_audit': str(destination), 'sha256': sha(destination.read_bytes()), 'tests': 16,
                      'source_catalogue_entries': [574, 120], 'native_stage_ready': False}))


if __name__ == '__main__': main()
