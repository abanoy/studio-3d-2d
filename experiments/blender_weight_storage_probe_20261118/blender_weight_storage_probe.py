"""UNRUN finite synthetic Blender weight-storage probe; Root owns native launch.

Only two owned copied scripts and a fresh owned request are read. No owner scene,
native model, texture, saved array, exporter, process or window API is accessed.
"""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import weight_storage_contract as C

WORKSPACE_OUTPUT = Path(r'C:\a\Programming\cloudflare\has-acceptance-session-20261111\output')
SOURCEIO_IMPORTER_SHA256 = C.SOURCEIO_IMPORTER_SHA256


def _ids(collection):
    return frozenset(item.as_pointer() for item in collection)


def _read_rows(mesh):
    return tuple(tuple((entry.group, C.float_word(entry.weight)) for entry in vertex.groups)
                 for vertex in mesh.vertices)


def exercise_storage_api(bpy, run_id):
    """Call the exact positive-only SourceIO add structure on owned loose points.

    Callable with CPU fakes. Nothing returned here alone qualifies native storage.
    """
    C.require(type(run_id) is str and re.fullmatch('[0-9a-f]{32}', run_id), 'Fresh hex run ID required')
    catalogue = C.cases()
    report = {'format': 'has_synthetic_blender_weight_storage_observation_1',
              'status': 'PROBE_FAILED', 'run_id': run_id, 'case_count': C.CASE_COUNT,
              'group_count': C.GROUP_COUNT, 'group_alphabet': list(C.GROUP_IDS),
              'weight_word_alphabet': [f'{word:08x}' for word in C.WEIGHT_WORDS],
              'case_catalogue_sha256': C.case_digest(catalogue),
              'expected_positive_add_calls': C.POSITIVE_WRITE_COUNT,
              'sourceio_importer_rule_sha256': SOURCEIO_IMPORTER_SHA256,
              'native_storage_rule_qualified': False, 'universal_group_or_F32_domain_qualified': False,
              'actual_source_rows_or_saved_scene_qualified': False,
              'native_fidelity_export_repair_adoption_qualified': False}
    before_objects, before_meshes = _ids(bpy.data.objects), _ids(bpy.data.meshes)
    mesh = obj = None
    cleanup_errors = []
    try:
        prefix = 'HAS_WEIGHT_STORAGE_' + run_id
        C.require(bpy.data.meshes.get(prefix + '_MESH') is None and
                  bpy.data.objects.get(prefix + '_OBJECT') is None, 'Owned synthetic names already exist')
        mesh = bpy.data.meshes.new(prefix + '_MESH')
        obj = bpy.data.objects.new(prefix + '_OBJECT', mesh)
        mesh.vertices.add(C.CASE_COUNT)
        mesh.update()
        C.require(len(mesh.vertices) == C.CASE_COUNT, 'Synthetic point allocation differs')
        groups = []
        for index in range(C.GROUP_COUNT):
            name = f'HAS_WEIGHT_GROUP_{index:03d}'
            group = obj.vertex_groups.new(name=name)
            C.require(type(group.index) is int and group.index == index and group.name == name,
                      'Exact synthetic native-order group identity differs')
            groups.append(group)
        add_calls = 0
        # Same n -> slots -> weight>0 -> add([n], weight, 'REPLACE') order as
        # pinned SourceIO. Fixture values do not come from expected row order.
        for n, slots in enumerate(catalogue):
            for bone_index, word in slots:
                weight = C.word_float(word)
                if weight > 0:
                    groups[bone_index].add([n], weight, 'REPLACE')
                    add_calls += 1
        report['positive_add_calls'] = add_calls
        C.require(add_calls == C.POSITIVE_WRITE_COUNT, 'Incomplete synthetic SourceIO write history')
        immediate_rows = _read_rows(mesh)
        report['immediate'] = C.compare_readback(catalogue, immediate_rows)
        # SourceIO calls the no-argument validate after its weight writes.
        validated = mesh.validate()
        C.require(type(validated) is bool, 'Mesh validate result type differs')
        report['mesh_validate_reported_change'] = validated
        after_rows = _read_rows(mesh)
        report['after_validate'] = C.compare_readback(catalogue, after_rows)
        report['immediate_vs_after_validate_exact'] = immediate_rows == after_rows
        report['synthetic_group_indices_exact'] = True
        if report['immediate']['all_cases_match'] and report['after_validate']['all_cases_match'] and immediate_rows == after_rows:
            report['status'] = 'BOUNDED_SYNTHETIC_STORAGE_MATCH'
        else:
            report['status'] = 'BOUNDED_SYNTHETIC_STORAGE_MISMATCH'
    except Exception as error:
        report['error_type'] = type(error).__name__
    finally:
        if obj is not None:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception as error:
                cleanup_errors.append('object:' + type(error).__name__)
        if mesh is not None:
            try:
                bpy.data.meshes.remove(mesh, do_unlink=True)
            except Exception as error:
                cleanup_errors.append('mesh:' + type(error).__name__)
        report['owned_object_mesh_cleanup_exact'] = (_ids(bpy.data.objects) == before_objects and
                                                     _ids(bpy.data.meshes) == before_meshes)
        report['cleanup_error_types'] = cleanup_errors
        if cleanup_errors or not report['owned_object_mesh_cleanup_exact']:
            report['status'] = 'PROBE_FAILED'
    return report


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        C.require(key not in result, 'Duplicate request key')
        result[key] = value
    return result


def _safe(path):
    C.require(type(path) is str, 'Literal path string required')
    value = Path(path)
    C.require(value.is_absolute(), 'Absolute owned path required')
    for item in (value, *value.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        C.require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                  'Reparse/symlink path refused')
    return value.resolve()


def _bounded_regular_bytes(path, maximum, expected_size=None):
    path = _safe(str(path))
    def stamp(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                info.st_nlink, getattr(info, 'st_file_attributes', 0))
    before = path.lstat()
    C.require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
              0 < before.st_size <= maximum, 'Bounded single-link regular owned file required')
    if expected_size is not None:
        C.require(type(expected_size) is int and 0 < expected_size <= maximum and
                  before.st_size == expected_size, 'Owned file declared size differs')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        C.require(stamp(opened) == stamp(before), 'Owned file changed before read')
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    C.require(len(raw) == before.st_size and len(raw) <= maximum and
              stamp(before) == stamp(after) == stamp(final), 'Owned file changed during bounded read')
    return raw


def read_plan(path):
    plan_path = _safe(str(path))
    C.require(plan_path.is_relative_to(WORKSPACE_OUTPUT.resolve()) and plan_path.name == 'request.json',
              'Fresh owned workspace-output request required')
    raw = _bounded_regular_bytes(plan_path, 32 * 1024)
    plan = json.loads(raw, object_pairs_hook=_unique_pairs)
    fields = {'format', 'phase', 'run_id', 'expires_utc', 'owned_root', 'owned_temp',
              'public_output', 'runtime', 'scripts'}
    C.require(type(plan) is dict and set(plan) == fields and
              plan['format'] == 'has_fresh_synthetic_weight_storage_request_1' and
              plan['phase'] == 'ROOT_APPROVED_FRESH_SYNTHETIC_ONLY', 'Fresh synthetic-only Root request required')
    C.require(type(plan['run_id']) is str and re.fullmatch('[0-9a-f]{32}', plan['run_id']), 'Fresh run ID required')
    C.require(type(plan['expires_utc']) is str, 'Explicit UTC expiry required')
    expiry = datetime.fromisoformat(plan['expires_utc'])
    now = datetime.now(timezone.utc)
    C.require(expiry.tzinfo is not None and expiry.utcoffset() == timedelta(0) and
              now < expiry <= now + timedelta(minutes=15), 'Fresh bounded UTC request required')
    owned = _safe(plan['owned_root']); temp = _safe(plan['owned_temp']); public = _safe(plan['public_output'])
    C.require(owned == plan_path.parent and owned != WORKSPACE_OUTPUT.resolve() and
              owned.is_relative_to(WORKSPACE_OUTPUT.resolve()) and temp == owned / 'temp' and
              temp.is_dir() and public == owned / 'PUBLIC_WEIGHT_STORAGE.json' and not public.exists(),
              'Exact fresh owned output/temp paths required')
    C.require(HERE == owned / 'source', 'Only fresh owned copied probe scripts may execute')
    C.require(_safe(str(C.__file__)) == HERE / 'weight_storage_contract.py', 'Actual imported contract path differs')
    C.require(all(_safe(os.environ.get(name, '')) == temp for name in ('TEMP', 'TMP')),
              'Root must bind TEMP and TMP to the owned directory before launch')
    C.require(type(plan['runtime']) is dict and set(plan['runtime']) == {'path', 'bytes', 'sha256'},
              'Explicit Root-verified runtime identity required')
    runtime = plan['runtime']
    _safe(runtime['path'])
    C.require(type(runtime['bytes']) is int and runtime['bytes'] > 0 and
              type(runtime['sha256']) is str and re.fullmatch('[0-9a-f]{64}', runtime['sha256']),
              'Runtime identity schema differs')
    C.require(type(plan['scripts']) is dict and set(plan['scripts']) ==
              {'blender_weight_storage_probe.py', 'weight_storage_contract.py'}, 'Exact two owned scripts required')
    C.require({item.name for item in HERE.iterdir()} == set(plan['scripts']), 'Only two owned source files required')
    for name, identity in plan['scripts'].items():
        C.require(type(identity) is dict and set(identity) == {'bytes', 'sha256'} and
                  type(identity['bytes']) is int and type(identity['sha256']) is str and
                  re.fullmatch('[0-9a-f]{64}', identity['sha256']), 'Script identity schema differs')
        content = _bounded_regular_bytes(HERE / name, 64 * 1024, identity['bytes'])
        C.require(len(content) == identity['bytes'] and hashlib.sha256(content).hexdigest() == identity['sha256'],
                  'Owned script identity differs')
    return plan, hashlib.sha256(raw).hexdigest()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    arguments = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    plan, plan_sha = read_plan(arguments.plan)
    import bpy
    C.require(not bpy.data.filepath and bpy.app.background is True and bpy.app.online_access is False and
              bpy.context.preferences.filepaths.use_scripts_auto_execute is False,
              'Factory/no-file/background/offline/disabled-autoexec context required')
    C.require(_safe(bpy.app.binary_path) == _safe(plan['runtime']['path']), 'Actual runtime path differs')
    report = exercise_storage_api(bpy, plan['run_id'])
    # Recheck owned request/scripts and their expiry before publishing evidence.
    checked, after_sha = read_plan(arguments.plan)
    C.require(checked == plan and after_sha == plan_sha, 'Synthetic request/source changed')
    report.update({'request_sha256': plan_sha, 'copied_script_identities': plan['scripts'],
                   'Root_expected_runtime_identity': plan['runtime'],
                   'runtime_binary_hash_verified_by_probe': False,
                   'runtime_version': list(bpy.app.version),
                   'runtime_version_string': str(bpy.app.version_string),
                   'runtime_build_hash': bytes(bpy.app.build_hash).decode('ascii', errors='replace'),
                   'native_API_execution_observed_by_this_script': True,
                   'factory_background_no_model_file': True,
                   'scene_or_native_model_files_opened': False, 'files_exported_or_blend_saved': False,
                   'window_or_desktop_API_called_by_probe': False})
    with Path(plan['public_output']).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write('\n')
    print('HAS_SYNTHETIC_WEIGHT_STORAGE ' + json.dumps({'status': report['status'], 'request_sha256': plan_sha,
          'cases': C.CASE_COUNT, 'owned_cleanup_exact': report['owned_object_mesh_cleanup_exact']}))
    return 0 if report['status'] == 'BOUNDED_SYNTHETIC_STORAGE_MATCH' else 1


if __name__ == '__main__':
    raise SystemExit(main())
