"""Root-only cold material-only inspection on a byte-identical owned B.

The unchanged published coordinator supplies full/source/runtime/physical guards.
No SourceIO import, geometry relabelling, image buffer, export or save.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GUARD = ROOT / 'experiments/source_current_native_ids_20261120/run_probe.py'
GUARD_PIN = (51728, 'f9bc228e02f3097548fad9ed1e83bc7c3d475abc40c088cd3c236e91f1dbf324')
SUPPORT = ROOT / 'experiments/source_current_native_ids_20261120/fresh_current_id_probe.py'
SUPPORT_PIN = (35572, 'd78369585463dcc2a511e00889f7e768e10c61004cf4f3fac0df3885b7d60c93')
SENTINEL = ROOT / 'experiments/normal_setter_boundary_sentinel_20261117/setter_probe.py'
SENTINEL_PIN = (17989, '034122697e8fa0e7a855ea42b51eddc351b647ae5f7641cad8d02994a51fc3c3')
ORIGINAL = ROOT.parent / 'has-acceptance-session-20261111/output/sfm-bone-bindings-native-launch-20261114T033026205/run/Studio/output/compatibility/source-1794627119-888-34370685/editable.blend'
BLEND_PIN = (2423175, 'ead1f1913812593abd69e353fed375944a15f280738784886fcef7fda3ee65c6')
WORKER_PIN = (18486, 'd78b5d843ac3cad1d56626b454fe8d9e89c6f1da8ad255e2df40aa023d64f245')
MODULES = {
    'enumeration_module': ('library_enumeration.py', 18845, '6c3aeff6a56b22a448d3ca093997ca866e76ac6ec2fb3948c811abad9c86f903'),
    'inspection_module': ('material_inspection.py', 24579, '5efd488d7912e7b032f5590a85e1a20419913f5f6736d906b126c4e8a6280d17'),
    'metadata_reader': ('material_metadata.py', 13818, 'c04c4e20705b490ed7633855b2e3bdde14350adec35c8b2a25afc42b69508395'),
}
WORKER_ROLES = frozenset(('probe', 'support_worker', 'sentinel', 'blend', 'full_completion',
                          'graphics_release', 'blender_exe', 'root_request', *MODULES,
                          'native_mdl', 'native_vvd', 'native_vtx'))
FALSE_FLAGS = ('original_B_scene_opened', 'image_pixels_read', 'image_buffer_getters_used', 'blend_saved',
               'exporter_invoked', 'native_arrays_published', 'native_or_historical_point_identity_qualified',
               'resource_or_export_qualified', 'resource_equivalence_qualified', 'normal_fidelity_qualified',
               'application_adoption_qualified', 'material_binding_qualified', 'dependency_closure_qualified',
               'non_normal_semantic_equivalence_qualified', 'transient_ID_or_C_level_read_absence_qualified',
               'outer_physical_closure_verified_by_worker')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def guard_module():
    # Bootstrap only the exact known guard, without a second loader read/pyc.
    for item in (GUARD, *GUARD.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400 or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
            raise ValueError('PUBLISHED_GUARD_LINK_OR_REPARSE')
    identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                              info.st_nlink, getattr(info, 'st_file_attributes', 0) & ~0x40000)
    before = GUARD.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != GUARD_PIN[0]:
        raise ValueError('PUBLISHED_GUARD_TYPE_OR_SIZE')
    with GUARD.open('rb') as stream:
        if identity(os.fstat(stream.fileno())) != identity(before):
            raise ValueError('PUBLISHED_GUARD_CHANGED_BEFORE_READ')
        raw = stream.read(GUARD_PIN[0] + 1)
        opened = os.fstat(stream.fileno())
    if identity(opened) != identity(before) or identity(GUARD.lstat()) != identity(before) or len(raw) != GUARD_PIN[0] or sha(raw) != GUARD_PIN[1]:
        raise ValueError('PUBLISHED_GUARD_IDENTITY_DIFFERS')
    spec = importlib.util.spec_from_file_location('has_library_guard_f9bc', GUARD)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(GUARD), 'exec', dont_inherit=True), module.__dict__)
    module._library_guard_row = dict(bytes=len(raw), mtime_ns=before.st_mtime_ns, sha256=sha(raw))
    module._library_guard_stamp = identity(before)
    return module


def remember_file(checks, guard, label, path, pin, row, identity):
    """Register immediately after a successful read, before later work can fail."""
    guard.need(label not in checks, 'DUPLICATE_PRESERVATION_LABEL')
    def check():
        _raw, after, after_identity = guard.read_checked(path, pin)
        return after == row and after_identity == identity
    checks[label] = check


def preservation_results(checks):
    results = {}
    for label, check in checks.items():
        try:
            results[label] = check() is True
        except BaseException:
            results[label] = False
    return results


def new_stage(guard):
    candidate = ROOT / 'output' / ('source-material-inspection2-run-' + str(time.time_ns()))
    guard.safe(candidate, exists=False)
    guard.need(candidate.parent == ROOT/'output' and not candidate.exists(), 'FRESH_LIBRARY_STAGE_REQUIRED')
    candidate.mkdir()
    return candidate


def failed_audit(guard, checks, error, *, process, launched, receipt_present, closure_observer):
    """No failed launch becomes success, even if every later check passes."""
    reaped = guard.reap_owned_launcher(process) if process is not None else False
    results = preservation_results(checks)
    physical, confirmed = None, False
    try:
        physical = closure_observer()
        guard.validate_fresh_physical(physical)
        confirmed = not launched or reaped
    except BaseException:
        pass
    return dict(format='has_owned_B_material_inspection_failed_run_2', status='UNQUALIFIED_FAILED_RUN',
                error_type=type(error).__name__, error_code=str(error) if isinstance(error, guard.Refusal) else type(error).__name__,
                launched=launched, launcher_reaped=reaped, worker_receipt_present=receipt_present,
                preservation_checks=results, all_attempted_checks_passed=all(results.values()),
                physical_closure_attempted=True, physical_closure_confirmed=confirmed,
                physical_after=physical, owned_lock_retained=True, runtime_lane_released=False,
                material_append_may_have_occurred=launched, dependency_closure_qualified=False,
                old_B_point_identity_qualified=False, material_binding_qualified=False,
                resource_equivalence_qualified=False, non_normal_semantic_equivalence_qualified=False,
                normal_fidelity_qualified=False, exporter_qualified=False, application_adoption_qualified=False)


def release_owned_lock(guard, path, expected, *, release_allowed):
    result = dict(owned_lock_retained=True, owned_lock_cleanup_refused=False)
    if not release_allowed:
        return result
    try:
        guard.need(expected is not None, 'OWNED_LIBRARY_LOCK_IDENTITY_MISSING')
        guard.safe(path)
        guard.need(guard.stamp(path.lstat()) == expected, 'OWNED_LIBRARY_LOCK_CHANGED')
        path.unlink()
        result['owned_lock_retained'] = False
    except BaseException:
        result['owned_lock_cleanup_refused'] = True
    return result


def public_summary_observation(value):
    """Retain scalar census evidence on refusal without copying names/arrays."""
    if type(value) is not dict or value.get('format') != 'has_empty_library_enumeration_summary_2':
        return None
    result = {'format': value['format']}
    for key in ('before_id_count', 'after_id_count', 'id_collections', 'source_id_types',
                'source_catalogue_name_count', 'source_materials', 'destination_request_types'):
        if type(value.get(key)) in (int, bool):
            result[key] = value[key]
    for key in ('all_destination_requests_empty', 'actual_id_census_unchanged'):
        if type(value.get(key)) is bool:
            result[key] = value[key]
    for key in ('source_material_names_sha256', 'source_catalogue_sha256'):
        if type(value.get(key)) is str and re.fullmatch('[0-9a-f]{64}', value[key]) is not None:
            result[key] = value[key]
    return result


def public_worker_observation(worker):
    """Allowlisted evidence survives refusal; private names/arrays never copied."""
    if type(worker) is not dict:
        return None
    result = {'enumeration_summary': public_summary_observation(worker.get('enumeration_summary'))}
    scalar_keys = {
        'native_subset_summary': ('native_materials', 'available_materials', 'unrequested_catalogue_materials',
            'exact_native_name_subset', 'native_geometry_decoded', 'native_engine_semantics_qualified'),
        'inspection_summary': ('requested_materials', 'available_materials', 'unrequested_catalogue_materials',
            'append_requested', 'append_completed', 'before_id_count', 'after_id_count', 'surviving_originals_unchanged',
            'inspected_material_graphs', 'reached_images', 'shared_image_references', 'packed_bytes_copied',
            'prospective_rgba_f32_bytes', 'post_failure_census_unavailable', 'retained_owned_source_libraries',
            'owned_source_library_validation_attempted', 'retained_owned_source_library_verified'),
        'node_type_diagnostic': ('materials', 'nodes', 'image_buffer_getters_used'),
    }
    digest_keys = ('requested_names_sha256', 'material_names_sha256', 'graph_metadata_sha256',
                   'packed_observation_sha256', 'retained_library_filepath_sha256')
    for key, fields in scalar_keys.items():
        value = worker.get(key)
        if type(value) is dict:
            safe = {name: value[name] for name in fields if type(value.get(name)) in (int, bool)}
            for name in ('format', 'status', 'refusal_code'):
                if type(value.get(name)) is str and re.fullmatch('[A-Za-z0-9_]{1,192}', value[name]) is not None:
                    safe[name] = value[name]
            for name in digest_keys:
                if type(value.get(name)) is str and re.fullmatch('[0-9a-f]{64}', value[name]) is not None:
                    safe[name] = value[name]
            for name, pattern in (('added_id_counts', '[a-z][a-z0-9_]{0,63}'),
                                  ('node_type_counts', '[A-Za-z][A-Za-z0-9_]{0,127}')):
                counts = value.get(name)
                if type(counts) is dict and len(counts) <= 128:
                    safe[name] = {kind: count for kind, count in counts.items() if type(kind) is str and
                                  re.fullmatch(pattern, kind) is not None and type(count) is int and 0 <= count <= 4096}
            result[key] = safe
    for key in ('status', 'phase', 'error_type', 'error_code'):
        value = worker.get(key)
        if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,192}', value) is not None:
            result[key] = value
    return result


def owned_library_path_digest(path):
    key = ntpath.normcase(ntpath.normpath(str(path)))
    return sha(json.dumps(key, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':')).encode())


def validate_library_result(guard, worker, placement, desktop, *, launcher_exit, expected_inputs, expected_owned_path):
    guard.need(type(desktop) is dict and desktop.get('format') == 'studio_private_desktop_1' and
               type(desktop.get('desktop')) is str and desktop['desktop'].startswith('HAS_Test_') and
               type(desktop.get('child_pid')) is int and desktop['child_pid'] > 0 and
               type(desktop.get('exit')) is int and desktop['exit'] == 0 and type(launcher_exit) is int and launcher_exit == 0 and
               desktop.get('job_memory_limit_bytes') == 4096 * 1024 * 1024, 'PRIVATE_LIBRARY_JOB_FAILED')
    for key in ('private_window_seen', 'child_desktop_confirmed', 'job_closed', 'desktop_closed'):
        guard.need(desktop.get(key) is True, 'PRIVATE_' + key.upper())
    guard.need(desktop.get('foreground_child_observed') is False and desktop.get('desktop_switch_requested') is False and
               not any(key in desktop for key in ('error', 'monitor_error', 'desktop_enumeration_error', 'cancelled')),
               'PRIVATE_LIBRARY_VISIBILITY_OR_FAILURE')
    guard.need(type(worker) is dict and worker.get('format') == 'has_owned_B_material_inspection_result_2' and
               worker.get('status') == 'MATERIAL_ONLY_OWNED_LIBRARY_AND_PACKED_HEADER_INSPECTION_MATCHED_2', 'LIBRARY_WORKER_NOT_QUALIFIED')
    for key in ('all_read_inputs_hash_size_stamp_unchanged', 'hidden_placement_verified',
                'library_enumeration_executed', 'complete_actual_ID_census_observed',
                'native_metadata_derived_without_geometry', 'material_inspection_attempted', 'material_inspection_executed'):
        guard.need(worker.get(key) is True, 'LIBRARY_REQUIRED_' + key.upper())
    for key in FALSE_FLAGS:
        guard.need(worker.get(key) is False, 'LIBRARY_SCOPE_' + key.upper())
    guard.need(type(expected_inputs) is dict and set(expected_inputs) == WORKER_ROLES and
               worker.get('input_identities') == expected_inputs, 'EXACT_LIBRARY_WORKER_READS')
    for row in expected_inputs.values():
        guard.need(type(row) is dict and set(row) == {'bytes', 'sha256'} and type(row['bytes']) is int and row['bytes'] > 0 and
                   type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}', row['sha256']) is not None,
                   'LIBRARY_INPUT_IDENTITY_SCHEMA')
    summary = worker.get('enumeration_summary')
    guard.need(type(summary) is dict and summary.get('format') == 'has_empty_library_enumeration_summary_2' and
               summary.get('all_destination_requests_empty') is True and summary.get('actual_id_census_unchanged') is True,
               'EXACT_LIBRARY_EMPTY_CENSUS_RESULT')
    for key, maximum in (('before_id_count', 4096), ('after_id_count', 4096), ('id_collections', 128),
                         ('source_id_types', 128), ('source_catalogue_name_count', 16384), ('destination_request_types', 128)):
        guard.need(type(summary.get(key)) is int and 0 < summary[key] <= maximum, 'LIBRARY_CENSUS_COUNT_DOMAIN')
    guard.need(summary['before_id_count'] == summary['after_id_count'] and
               summary['source_id_types'] == summary['destination_request_types'] and
               type(summary.get('source_materials')) is int and 1 <= summary['source_materials'] <= 256 and
               summary['source_catalogue_name_count'] >= summary['source_materials'], 'LIBRARY_CENSUS_CARDINALITY')
    for key in ('source_material_names_sha256', 'source_catalogue_sha256'):
        guard.need(type(summary.get(key)) is str and re.fullmatch('[0-9a-f]{64}', summary[key]) is not None,
                   'LIBRARY_CENSUS_DIGEST')
    selection = worker.get('native_subset_summary')
    guard.need(type(selection) is dict and selection.get('format') == 'has_native_material_name_subset_1' and
               selection.get('exact_native_name_subset') is True and type(selection.get('native_materials')) is int and
               selection['native_materials'] == 4 and selection.get('available_materials') == summary['source_materials'] and
               type(selection.get('available_materials')) is int and selection['available_materials'] >= 4 and
               type(selection.get('unrequested_catalogue_materials')) is int and
               selection['unrequested_catalogue_materials'] == summary['source_materials'] - 4 and
               selection.get('native_geometry_decoded') is False and selection.get('native_engine_semantics_qualified') is False,
               'EXACT_NATIVE_MATERIAL_SUBSET_REQUIRED')
    guard.need(type(selection.get('requested_names_sha256')) is str and
               re.fullmatch('[0-9a-f]{64}', selection['requested_names_sha256']) is not None, 'NATIVE_SUBSET_DIGEST')
    inspected = worker.get('inspection_summary')
    guard.need(type(inspected) is dict and inspected.get('format') == 'has_material_only_library_inspection_summary_2' and
               inspected.get('status') == 'INSPECTED_MATERIAL_ONLY_OWNED_LIBRARY_AND_PACKED_PNG_HEADERS_2' and
               inspected.get('append_requested') is True and inspected.get('append_completed') is True and
               inspected.get('surviving_originals_unchanged') is True and type(inspected.get('requested_materials')) is int and
               inspected['requested_materials'] == 4 and type(inspected.get('inspected_material_graphs')) is int and
               inspected['inspected_material_graphs'] == 4 and type(inspected.get('available_materials')) is int and
               type(inspected.get('unrequested_catalogue_materials')) is int and
               inspected.get('available_materials') == summary['source_materials'] and
               inspected.get('unrequested_catalogue_materials') == summary['source_materials'] - 4 and
               inspected.get('material_names_sha256') == selection['requested_names_sha256'], 'EXACT_MATERIAL_INSPECTION_REQUIRED')
    for key in ('material_binding_qualified', 'resource_equivalence_qualified', 'B_dependency_closure_qualified',
                'non_normal_semantic_equivalence_qualified', 'native_or_historical_point_identity_qualified',
                'exporter_qualified', 'normal_fidelity_qualified', 'application_adoption_qualified',
                'transient_ID_or_C_level_read_absence_qualified', 'image_buffer_getters_used', 'blend_saved',
                'exporter_invoked', 'external_filepath_retrieval_attempted'):
        guard.need(inspected.get(key) is False, 'INSPECTION_SCOPE_' + key.upper())
    for key, maximum in (('reached_images', 128), ('shared_image_references', 4),
                         ('packed_bytes_copied', 128 * 1024 * 1024), ('prospective_rgba_f32_bytes', 128 * 1024 * 1024),
                         ('before_id_count', 4096), ('after_id_count', 4096)):
        guard.need(type(inspected.get(key)) is int and 0 <= inspected[key] <= maximum, 'INSPECTION_COUNT_BUDGET')
    added = inspected.get('added_id_counts')
    library_count = inspected.get('retained_owned_source_libraries')
    guard.need(type(library_count) is int and library_count in (0, 1) and
               inspected.get('owned_source_library_validation_attempted') is bool(library_count) and
               inspected.get('retained_owned_source_library_verified') is bool(library_count),
               'EXACT_OWNED_SOURCE_LIBRARY_OBSERVATION_REQUIRED')
    if library_count:
        guard.need(inspected.get('retained_library_filepath_sha256') == owned_library_path_digest(expected_owned_path),
                   'RETAINED_LIBRARY_PATH_IS_NOT_AUTHENTICATED_OWNED_B')
    else:
        guard.need('retained_library_filepath_sha256' not in inspected, 'ZERO_LIBRARY_CANNOT_CLAIM_SOURCE_PATH')
    guard.need(type(added) is dict and set(added) <= {'materials', 'images', 'libraries'} and added.get('materials') == 4 and
               type(added.get('materials')) is int and type(added.get('images', 0)) is int and
               added.get('images', 0) == inspected['reached_images'] and
               type(added.get('libraries', 0)) is int and added.get('libraries', 0) == library_count and
               inspected['before_id_count'] == summary['after_id_count'] and
               inspected['after_id_count'] == inspected['before_id_count'] + 4 + inspected['reached_images'] + library_count,
               'INSPECTION_ADDED_ID_CARDINALITY')
    for key in ('graph_metadata_sha256', 'packed_observation_sha256'):
        guard.need(type(inspected.get(key)) is str and re.fullmatch('[0-9a-f]{64}', inspected[key]) is not None,
                   'INSPECTION_DIGEST_REQUIRED')
    diagnostic = worker.get('node_type_diagnostic')
    guard.need(type(diagnostic) is dict and diagnostic.get('format') == 'has_material_node_type_counts_1' and
               type(diagnostic.get('materials')) is int and diagnostic['materials'] == 4 and
               type(diagnostic.get('nodes')) is int and 8 <= diagnostic['nodes'] <= 12 and
               diagnostic.get('image_buffer_getters_used') is False and type(diagnostic.get('node_type_counts')) is dict,
               'MATERIAL_NODE_TYPE_DIAGNOSTIC_REQUIRED')
    counts = diagnostic['node_type_counts']
    guard.need(set(counts) <= {'ShaderNodeOutputMaterial', 'ShaderNodeBsdfPrincipled', 'ShaderNodeTexImage'} and
               all(type(v) is int and v > 0 for v in counts.values()) and sum(counts.values()) == diagnostic['nodes'] and
               counts.get('ShaderNodeOutputMaterial') == 4 and counts.get('ShaderNodeBsdfPrincipled') == 4 and
               inspected['reached_images'] + inspected['shared_image_references'] == counts.get('ShaderNodeTexImage', 0),
               'MATERIAL_NODE_TYPE_COUNTS')
    guard.need(type(placement) is dict and placement.get('format') == 'has_owned_B_material_inspection_placement_2' and
               placement.get('worker_verified_hidden_sentinel_closed') is True, 'LIBRARY_SENTINEL_NOT_CLOSED')
    policy = placement.get('policy')
    guard.need(type(policy) is dict and policy.get('format') == 'has_hidden_background_desktop_placement_sentinel_1' and
               policy.get('class') == 'STATIC' and policy.get('requested_size_pixels') == [0, 0], 'LIBRARY_SENTINEL_POLICY')
    for key in ('disabled', 'noactivate_style', 'toolwindow_style', 'destroyed_in_finally', 'owned_pid_and_thread_verified'):
        guard.need(policy.get(key) is True, 'LIBRARY_SENTINEL_' + key.upper())
    for key in ('visible_at_creation', 'visible_before_destruction', 'show_or_activation_calls', 'thread_desktop_switch_calls'):
        guard.need(policy.get(key) is False, 'LIBRARY_SENTINEL_' + key.upper())
    return dict(enumeration_summary=summary, native_subset_summary=selection, inspection_summary=inspected,
                node_type_diagnostic=diagnostic)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-lane-confirmed', action='store_true')
    parser.add_argument('--driver-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    args = parser.parse_args()
    guard = guard_module()
    guard.need(args.root_lane_confirmed and sys.dont_write_bytecode, 'ROOT_LANE_AND_NO_BYTECODE_REQUIRED')
    guard.need(args.worker_sha256 == WORKER_PIN[1], 'FROZEN_LIBRARY_WORKER_REQUIRED')
    own_raw, own_row, own_stamp = guard.read_checked(Path(__file__))
    guard.need(sha(own_raw) == args.driver_sha256, 'ROOT_LIBRARY_DRIVER_DIFFERS')
    context = {'root_lane_confirmed': True}
    proof = {}
    full = ROOT / 'output' / guard.FULL_NAME
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'),
                      ('before', 'source-before.json'), ('after', 'source-after.json'),
                      ('committed', 'committed-source-blobs.json')):
        context[key], proof[key] = guard.json_read(full / name)
    guard.validate_full(context)
    guard.need(guard.source_snapshot(context['after']) == context['after'], 'SOURCE_SNAPSHOT_DIFFERS')
    initial_git = guard.git_proof()
    guard.validate_git(initial_git, context)
    guard.need(proof['completion']['mtime_ns'] >= context['launch']['started_ns'] and
               proof['after']['mtime_ns'] >= context['launch']['started_ns'], 'FULL_PROOFS_PREDATE_LAUNCH')
    checks = {
        'functional_source': lambda: guard.source_snapshot(context['after']) == context['after'],
        'head_and_committed_source': lambda: guard.git_proof() == initial_git,
    }
    remember_file(checks, guard, 'root_driver', Path(__file__), (len(own_raw), args.driver_sha256), own_row, own_stamp)
    remember_file(checks, guard, 'published_guard', GUARD, GUARD_PIN,
                  guard._library_guard_row, guard._library_guard_stamp)
    for key, name in (('completion', 'completion.json'), ('launch', 'launch.json'), ('before', 'source-before.json'),
                      ('after', 'source-after.json'), ('committed', 'committed-source-blobs.json')):
        def check_proof(key=key, name=name):
            _value, identity = guard.json_read(full / name)
            return identity == proof[key]
        checks['full_proof_' + key] = check_proof
    lock_path = ROOT / 'output/source-current-id-root-lane.lock'
    guard.safe(lock_path, exists=False)
    lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    lock_stamp = None
    stage = None
    process = None
    launcher_reaped = closure_confirmed = False
    launched = False
    before = {}
    runtimes = {}
    sources = {}
    success_result = audit = primary_error = None
    observed_worker_summary = None
    preservation = {}
    try:
        os.write(lock_fd, (str(os.getpid())+'\n').encode('ascii'))
        lock_stamp = guard.stamp(os.fstat(lock_fd))
        stage = new_stage(guard)
        for name in ('inputs', 'result', 'temp', 'user-config', 'user-scripts', 'user-datafiles', 'home'):
            (stage/name).mkdir()
        def runtime_reader():
            runtimes.update(guard.runtime_check(ROOT/guard.LOCK_REL))
            checks['approved_runtime_SDK_exporter'] = lambda: guard.runtime_check(ROOT/guard.LOCK_REL) == runtimes
            return runtimes
        admitted = guard.admit(context, source_reader=lambda: guard.source_snapshot(context['after']),
                               git_reader=guard.git_proof,
                               physical_reader=lambda: guard.observe_physical(stage, context['launch'], 'BEFORE'),
                               runtime_reader=runtime_reader)
        raw, original, original_stamp = guard.read_checked(ORIGINAL, BLEND_PIN)
        remember_file(checks, guard, 'protected_original_B', ORIGINAL, BLEND_PIN, original, original_stamp)
        owned = stage/'inputs/material-source.blend'
        # Register even a failed/partial copy attempt. The stronger inode/stamp
        # check is added once the complete owned copy is independently admitted.
        checks['owned_B_expected_content'] = lambda: guard.read_checked(owned, BLEND_PIN)[1] == original
        with owned.open('xb') as stream:
            stream.write(raw)
        os.utime(owned, ns=(ORIGINAL.stat().st_atime_ns, original['mtime_ns']))
        _, owned_row, owned_stamp = guard.read_checked(owned, BLEND_PIN)
        remember_file(checks, guard, 'owned_B_copy', owned, BLEND_PIN, owned_row, owned_stamp)
        guard.need(owned_row == original, 'OWNED_B_COPY_DIFFERS')
        (stage/'inputs/native').mkdir()
        native_inputs = []
        for key, (name, count, hash_) in guard.NATIVE.items():
            original_native = guard.OLD/guard.FAMILY/name
            native_raw, native_row, native_stamp = guard.read_checked(original_native, (count, hash_))
            remember_file(checks, guard, 'protected_original_native_' + key, original_native,
                          (count, hash_), native_row, native_stamp)
            native_owned = stage/'inputs'/name
            checks['owned_native_expected_content_' + key] = (
                lambda path=native_owned, pin=(count, hash_), row=native_row: guard.read_checked(path, pin)[1] == row)
            with native_owned.open('xb') as stream:
                stream.write(native_raw)
            os.utime(native_owned, ns=(original_native.stat().st_atime_ns, native_row['mtime_ns']))
            _, copied_row, copied_stamp = guard.read_checked(native_owned, (count, hash_))
            remember_file(checks, guard, 'owned_native_copy_' + key, native_owned, (count, hash_), copied_row, copied_stamp)
            guard.need(copied_row == native_row, 'OWNED_NATIVE_METADATA_COPY_DIFFERS')
            native_inputs.append(('native_' + key, native_owned, (count, hash_)))
        module_inputs = [(role, HERE/name, (count, hash_)) for role, (name, count, hash_) in MODULES.items()]
        for role, path, pin in [
                                ('probe', HERE/'inspection_worker.py', WORKER_PIN), ('support_worker', SUPPORT, SUPPORT_PIN),
                                ('sentinel', SENTINEL, SENTINEL_PIN), ('blend', owned, BLEND_PIN),
                                ('blender_exe', guard.BLENDER, guard.RUNTIME_PINS[str(guard.BLENDER)]),
                                *module_inputs, *native_inputs]:
            raw, row, identity = guard.read_checked(path, pin)
            if role == 'probe':
                guard.need(sha(raw) == args.worker_sha256, 'LIBRARY_WORKER_IDENTITY_DIFFERS')
            sources[role] = dict(path=str(path), bytes=row['bytes'], sha256=row['sha256'])
            before[role] = (row, identity)
            remember_file(checks, guard, 'worker_input_' + role, path, (row['bytes'], row['sha256']), row, identity)
        graphics = dict(format='has_B_material_inspection_root_release_2', full_suite_passed=True,
                        tested_revision=guard.TESTED, current_head=admitted['head'], functional_file_count=guard.COUNT,
                        exact_source_hash_bytes_nsmtime=True, full_job_physically_closed=True,
                        root_lane_explicitly_confirmed=True, exclusive_runtime_lease=True,
                        physical_observation_is_global_lease=False,
                        full_completion_sha256=proof['completion']['sha256'],
                        observed_ns=admitted['physical']['observed_ns'], scope='MATERIAL_ONLY_APPEND_INSPECTION')
        graphics_row = guard.write_new(stage/'graphics-release.json', graphics)
        _, graphics_identity, graphics_stamp = guard.read_checked(stage/'graphics-release.json',
            (graphics_row['bytes'], graphics_row['sha256']))
        remember_file(checks, guard, 'graphics_release', stage/'graphics-release.json',
                      (graphics_row['bytes'], graphics_row['sha256']), graphics_identity, graphics_stamp)
        guard.write_new(stage/'physical-closure.json', admitted['physical'])
        sources['full_completion'] = dict(path=str(full/'completion.json'), bytes=proof['completion']['bytes'],
                                          sha256=proof['completion']['sha256'])
        sources['graphics_release'] = {key: graphics_row[key] for key in ('path','bytes','sha256')}
        now = dt.datetime.now(dt.timezone.utc)
        request = dict(format='has_owned_B_material_inspection_request_2',
                       phase='ROOT_APPROVED_AFTER_FULL_PHYSICALLY_CLOSED', created_utc=now.isoformat(),
                       expires_utc=(now+dt.timedelta(minutes=30)).isoformat(), private_arrays_public=False,
                       owned_stage=str(stage), owned_output=str(stage/'result'), owned_temp=str(stage/'temp'), files=sources,
                       source_context=dict(full_suite_passed=True, full_job_physically_closed=True,
                                           exclusive_runtime_lease=True, observed_owned_processes=0,
                                           functional_file_count=guard.COUNT, tested_revision=guard.TESTED,
                                           full_completion_sha256=proof['completion']['sha256'],
                                           graphics_release_sha256=graphics_row['sha256']))
        request_row = guard.write_new(stage/'ROOT_MATERIAL_INSPECTION2_REQUEST.json', request)
        _, request_identity, request_stamp = guard.read_checked(stage/'ROOT_MATERIAL_INSPECTION2_REQUEST.json',
            (request_row['bytes'], request_row['sha256']))
        remember_file(checks, guard, 'root_request', stage/'ROOT_MATERIAL_INSPECTION2_REQUEST.json',
                      (request_row['bytes'], request_row['sha256']), request_identity, request_stamp)
        guard.write_new(stage/'PRIVATE_BEFORE.json', dict(original=original, owned=owned_row, runtime=runtimes,
                                                         proof=proof, driver=own_row, sources=sources, git=initial_git))
        env = os.environ.copy()
        for key in ('PYTHONPATH','PYTHONHOME','BLENDER_SYSTEM_SCRIPTS','BLENDER_SYSTEM_DATAFILES','BLENDER_SYSTEM_PYTHON'):
            env.pop(key, None)
        env.update(TEMP=str(stage/'temp'), TMP=str(stage/'temp'), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                   BLENDER_USER_CONFIG=str(stage/'user-config'), BLENDER_USER_SCRIPTS=str(stage/'user-scripts'),
                   BLENDER_USER_DATAFILES=str(stage/'user-datafiles'), HOME=str(stage/'home'), USERPROFILE=str(stage/'home'))
        command=[str(guard.PYTHONW),'-B',str(ROOT/'tools/private_desktop.py'),'--receipt',str(stage/'private-desktop.json'),
                 '--timeout','150','--memory-limit-mib','4096','--',str(guard.BLENDER),'--background','--factory-startup',
                 '--disable-autoexec','--offline-mode','--python-exit-code','1','--python',str(HERE/'inspection_worker.py'),
                 '--','--request',str(stage/'ROOT_MATERIAL_INSPECTION2_REQUEST.json'),'--request-sha256',request_row['sha256']]
        guard.need(guard.source_snapshot(context['after'])==context['after'] and guard.git_proof()==initial_git,
                   'PRELAUNCH_SOURCE_OR_HEAD_CHANGED')
        guard.observe_physical(stage, context['launch'], 'PRELAUNCH')
        with (stage/'PRIVATE_stdout.log').open('xb') as out, (stage/'PRIVATE_stderr.log').open('xb') as err:
            process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            launched=True
            guard.wait_recorded_owned(process, lambda: guard.write_new(stage/'PRIVATE_launch.json',
                dict(pid=process.pid,coordinator_pid=os.getpid(),started_ns=time.time_ns(),args=command)))
        launcher_reaped=process.poll() is not None
        desktop,desktop_row=guard.json_read(stage/'private-desktop.json')
        guard.need(type(desktop.get('child_pid')) is int and desktop['child_pid']>0, 'PRIVATE_CHILD_PID_REQUIRED')
        physical=guard.observe_physical(stage,dict(pid=process.pid,coordinator_pid=context['launch']['coordinator_pid'],
                     extra_absent_pids=[desktop['child_pid'],context['launch']['pid']]),'AFTER')
        guard.validate_fresh_physical(physical)
        closure_confirmed=True
        preservation = preservation_results(checks)
        guard.need(all(preservation.values()), 'POST_LIBRARY_PRESERVATION_CHECK_FAILED')
        worker,worker_row=guard.json_read(stage/'result/PUBLIC_MATERIAL_INSPECTION2.json',64*1024)
        observed_worker_summary = public_worker_observation(worker)
        placement,placement_row=guard.json_read(stage/'result/PLACEMENT_MATERIAL_INSPECTION2.json',64*1024)
        expected={role:{key:row[key] for key in ('bytes','sha256')} for role,row in sources.items()}
        expected['root_request']={key:request_row[key] for key in ('bytes','sha256')}
        summary = validate_library_result(guard, worker, placement, desktop,
                                          launcher_exit=process.returncode, expected_inputs=expected, expected_owned_path=owned)
        success_result=dict(format='has_root_owned_B_material_inspection_2',status='MATERIAL_ONLY_OWNED_LIBRARY_INSPECTION_QUALIFIED_2',
                    tested_revision=guard.TESTED,current_source_head=initial_git['head'],functional_source_count=guard.COUNT,
                    worker_reads=14,private_job_closed=True,launcher_reaped=True,physical_after=physical,
                    source_runtime_original_and_owned_hash_size_nsmtime_unchanged=True,
                    material_append_requested=True,old_B_point_identity_qualified=False,normal_fidelity_qualified=False,
                    dependency_closure_qualified=False,exporter_qualified=False,application_adoption_qualified=False,
                    resource_equivalence_qualified=False,non_normal_semantic_equivalence_qualified=False,
                    whole_catalogue_materials=summary['enumeration_summary']['source_materials'], material_binding_qualified=False,
                    four_native_records_do_not_bound_whole_B_catalogue=True,
                    summary=summary,worker_result=worker_row,placement_result=placement_row,desktop_result=desktop_row,
                    preservation_checks=preservation)
    except BaseException as error:
        primary_error = error
        if stage is not None:
            def failure_observer():
                launch = dict(pid=process.pid if process is not None else context['launch']['pid'],
                              coordinator_pid=context['launch']['coordinator_pid'],
                              extra_absent_pids=[context['launch']['pid']])
                receipt = stage/'private-desktop.json'
                # A missing/malformed receipt must not skip the actual observer.
                try:
                    value, _row = guard.json_read(receipt)
                    if type(value.get('child_pid')) is int and value['child_pid'] > 0:
                        launch['extra_absent_pids'].append(value['child_pid'])
                except BaseException:
                    pass
                return guard.observe_physical(stage, launch, 'FAILURE')
            audit = failed_audit(guard, checks, error, process=process, launched=launched,
                                 receipt_present=(stage/'private-desktop.json').is_file(),
                                 closure_observer=failure_observer)
            audit['observed_worker_summary'] = observed_worker_summary
            launcher_reaped = audit['launcher_reaped']
            closure_confirmed = audit['physical_closure_confirmed']
        else:
            audit = dict(format='has_owned_B_material_inspection_failed_run_2', status='FAILED_BEFORE_STAGE',
                         error_type=type(error).__name__, error_code=str(error) if isinstance(error,guard.Refusal) else type(error).__name__,
                         preservation_checks=preservation_results(checks), launched=False,
                         physical_closure_attempted=False, physical_closure_confirmed=False,
                         owned_lock_retained=True, runtime_lane_released=False,
                         normal_fidelity_qualified=False, application_adoption_qualified=False)
    finally:
        if process is not None and process.poll() is None:
            guard.reap_owned_launcher(process)
        close_error = None
        try:
            os.close(lock_fd)
        except BaseException as error:
            close_error = error
        lock_result = release_owned_lock(guard, lock_path, lock_stamp,
                                         release_allowed=closure_confirmed or not launched)
        if close_error is not None:
            lock_result['owned_lock_cleanup_refused'] = True
    if audit is None and (lock_result['owned_lock_retained'] or lock_result['owned_lock_cleanup_refused']):
        audit = dict(format='has_owned_B_material_inspection_failed_run_2', status='UNQUALIFIED_FAILED_RUN',
                     error_type='Refusal', error_code='OWNED_LIBRARY_LOCK_CLEANUP_REFUSED',
                     launched=launched, launcher_reaped=launcher_reaped, preservation_checks=preservation,
                     physical_closure_confirmed=closure_confirmed, runtime_lane_released=False,
                     normal_fidelity_qualified=False, application_adoption_qualified=False)
    if audit is not None:
        audit.update(lock_result)
        audit['runtime_lane_released'] = False
        if stage is not None:
            try: guard.write_new(stage/'PUBLIC_MATERIAL_INSPECTION2_FAILED_RUN.json', audit)
            except BaseException: pass
        print(json.dumps({key:audit.get(key) for key in ('status','error_type','error_code','physical_closure_confirmed','owned_lock_retained')}))
        return 1
    guard.need(success_result is not None, 'LIBRARY_SUCCESS_RESULT_MISSING')
    guard.write_new(stage/'PUBLIC_MATERIAL_INSPECTION2_ROOT_RESULT.json', success_result)
    print(json.dumps(dict(status=success_result['status'],folder=stage.name,summary=success_result['summary'])))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps(dict(status='REFUSED_PREFLIGHT_OR_PUBLICATION', error_type=type(error).__name__)))
        raise SystemExit(1)
