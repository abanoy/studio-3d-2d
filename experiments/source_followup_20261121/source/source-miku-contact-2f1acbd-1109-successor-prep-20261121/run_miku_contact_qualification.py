"""Root-only saved-Miku contact qualification. Authored SOURCE ONLY, UNRUN.
Uses existing authenticated ownership/snapshot helpers. Private inputs/results
remain local; this is not a new Full, product adoption, or body-triangle proof.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import time
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '2f1acbd7867087d9f18cfbc1122cc0c883c5f788'
S_PIN = (11221, '0afe7a6d1ceda9ddce6de26dcadb213cb7306fdf5907709ffd57c4765c14262d')
Q_PIN = (21967, 'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
INPUT_PIN = (6784, '4cd20b8c02c813e6d90fab4547f87c6e2b7ecab9f51be59c2a4dd53176e19363')
PRIVATE_MANIFEST_PIN = (1385, 'ef0df6fdf61ef0baf95e5170a95b6c72e2ae934919e1d4191bfd156136b8bb8c')
PROJECT_SHA = '036eb37fcb17d71e6292751bb1af4b73350512c69a0c31a59efb4fa6a4341101'
ASSET_SHA = 'cc040e35f47280599ea083ac78d36855c99861791b0e66a28e091c12655c5aaf'
COLLIDER_SHA = 'e3ada9ac313b21919c3a0d35617d8ec1dbd8cdf6abfe5dec0d8af4f7dd699971'
ALIGNMENT_SHA = '6ebf7e4793550a14a29ae569afaeb863cc458582aa07398fa5218948c89b2b7c'


def identity(info):
    # Access-time changes caused by reading are deliberately excluded.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, info.st_mode, getattr(info, 'st_file_attributes', 0))


def source_module(name, path, pin):
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('SOURCE_HELPER_ALIAS')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != pin[0]:
        raise RuntimeError('SOURCE_HELPER_REGULAR_PIN')
    raw = path.read_bytes()
    if identity(before) != identity(path.lstat()) or len(raw) != pin[0] or hashlib.sha256(raw).hexdigest() != pin[1]:
        raise RuntimeError('SOURCE_HELPER_IDENTITY_OR_BYTES')
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def private_inputs(H, path):
    document = H.parse(H.read(H.safe(path), *PRIVATE_MANIFEST_PIN, limit=65536))
    H.need(document.get('format') == 'has_local_private_miku_contact_references_1'
           and document.get('private_do_not_publish') is True, 'PRIVATE_MANIFEST_REQUIRED')
    rows = document.get('files')
    H.need(type(rows) is list and len(rows) == 4
           and {row.get('role') for row in rows} == {'saved_copy', 'owner_original', 'colliders', 'alignment'},
           'EXACT_FOUR_PRIVATE_INPUTS')
    expected = {'saved_copy': PROJECT_SHA, 'colliders': COLLIDER_SHA, 'alignment': ALIGNMENT_SHA}
    blobs = {}
    for row in rows:
        H.need(type(row.get('path')) is str and Path(row['path']).is_absolute()
               and type(row.get('bytes')) is int and 0 < row['bytes'] <= 16*1024*1024
               and type(row.get('mtime_ns')) is str and row['mtime_ns'].isdigit()
               and re.fullmatch('[0-9a-f]{64}', row.get('sha256', '')) is not None, 'PRIVATE_EXACT_REGULAR_REFERENCE')
        if row['role'] in expected:
            H.need(row['sha256'] == expected[row['role']], 'SEALED_PRIVATE_HASH_DIFFERS')
        original = H.safe(Path(row['path']))
        raw = H.read(original, row['bytes'], row['sha256'], limit=16*1024*1024)
        H.need(original.lstat().st_mtime_ns == int(row['mtime_ns']), 'PRIVATE_INPUT_STAMP_CHANGED')
        if row['role'] != 'owner_original':
            blobs[row['role']] = raw
    return document, blobs


def public_case(private):
    """Only hashes, counts, named gates and bounded diagnostic codes leave private results."""
    allowed = ('status', 'checks', 'failures', 'initial_editing_context', 'collision_profile',
               'ticks', 'actual_saved_case_loaded', 'calibration_qualified', 'capsule_contact_qualified',
               'initial_clean_start', 'candidate_contact_gate', 'raw_fk_reconstruction_agrees',
               'saved_draft_channels', 'stored_pose_channels', 'saved_context_observation', 'saved_fan_count', 'sampled_pose_sha256', 'saved_fan_field_sha256',
               'private_render_captures', 'contact_failure_code', 'error_code',
               'actual_owner_contact_reproduced', 'body_triangle_contact_qualified',
               'swept_contact_qualified', 'skin_shader_equivalence_qualified',
               'moving_actor_inertia_qualified', 'gravity_rest_settling_qualified', 'application_adopted')
    result = {key: private[key] for key in allowed if key in private}
    # Geometry minima, radii, transforms, binding IDs and private paths are excluded.
    for stage, row in private.get('measurements', {}).items():
        if type(row) is dict:
            result[stage+'_counts'] = {key: value for key, value in row.items() if key.startswith('penetrating_') and type(value) is int}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--private-manifest', type=Path, required=True)
    parser.add_argument('--full-folder', type=Path, required=True)
    parser.add_argument('--full-completion-sha256', required=True)
    parser.add_argument('--full-source-sha256', required=True)
    parser.add_argument('--full-report-sha256', required=True)
    parser.add_argument('--full-outer-folder', type=Path, required=True)
    parser.add_argument('--full-outer-launch-sha256', required=True)
    parser.add_argument('--full-outer-completion-sha256', required=True)
    parser.add_argument('--full-postflight-sha256', required=True)
    parser.add_argument('--ticks', type=int, default=480)
    parser.add_argument('--root-exclusive-lane-confirmed', action='store_true', required=True)
    options = parser.parse_args()
    Q = source_module('_miku_owned_ui_helpers', HERE/'qualified_ui_host.py', Q_PIN)
    H, _ = Q.load_pinned('_miku_owned_helpers', HERE/'qualified_helpers.py', *Q.HELPER_PIN)
    H.need(H.ROOT == ROOT and os.name == 'nt' and sys.version_info[:2] == (3, 13)
           and not sys.flags.optimize and options.root_exclusive_lane_confirmed, 'ROOT_WINDOWS313_EXCLUSIVE_LANE')
    H.need(options.expected_head == BASE and re.fullmatch('[0-9a-f]{40}', options.expected_head) is not None
           and re.fullmatch('[0-9a-f]{64}', options.self_sha256) is not None
           and 120 <= options.ticks <= 1200, 'EXPLICIT_BOUNDED_OPTIONS')
    H.read(Path(__file__), digest=options.self_sha256)
    H.read(HERE/'qualified_ui_host.py', *Q_PIN)
    inputs = H.parse(H.read(HERE/'INPUT_PINS.json', *INPUT_PIN))
    H.need(inputs.get('format') == 'has_miku_contact_source_inputs_1109_1'
           and inputs.get('baseline_revision') == BASE and len(inputs.get('targets', [])) == 13,
           'EXACT_MIKU_1109_SOURCE_INPUT_DOMAIN')
    for row in inputs['files']:
        H.read(HERE/H.rel(row['path']), row['bytes'], row['sha256'])
    S, _ = Q.load_pinned('_miku_current1109_source', HERE/'source1109.py', *S_PIN)
    H.need(H.head() == BASE, 'PUBLICATION_HEAD_CHANGED')
    expected = S.admit_full(H, Q, ROOT, HERE, options.full_folder,
        options.full_completion_sha256, options.full_source_sha256, options.full_report_sha256,
        options.full_outer_folder, options.full_outer_launch_sha256, options.full_outer_completion_sha256, options.full_postflight_sha256)
    frozen = S.immutable_runtime(H, Q, ROOT, expected)
    immutable_runtime_count = len(frozen)
    for row in inputs['targets']:
        name = H.rel(row['path'])
        H.need(name not in frozen and name.startswith(('src/', 'tests/')), 'ONLY_THIRTEEN_NEW_PROBE_TARGETS')
        frozen[name] = H.read(HERE/'payload'/name, row['bytes'], row['sha256'])
    H.need(len(frozen) == immutable_runtime_count + 13, 'EXACT_OWNED_1109_SUCCESSOR_RUNTIME')
    lock = H.parse(H.read(H.LOCK, digest=H.LOCK_SHA))
    runtime = lock['runtime_paths']
    H.need(len(lock['runtime_executables']) == 6, 'SIX_APPROVED_RUNTIME_PINS')
    for path, row in lock['runtime_executables'].items():
        H.read(path, row['bytes'], row['sha256'], limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns == row['mtime_ns'], 'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve() == Path(runtime['python']).resolve(), 'APPROVED_PYTHON')
    _private, private_blobs = private_inputs(H, options.private_manifest)
    stage = ROOT.parent/('has-miku-contact-qualification-'+str(time.time_ns()))
    H.safe(stage, missing=True)
    lane = ROOT/'output/source-miku-contact-1109-qualification.lock'
    fd = None; lane_identity = None; stage_owned = False; primary = None
    token = uuid.uuid4().hex.encode()
    parent_environment = dict(os.environ)
    result = {'format': 'has_miku_contact_source_qualification_1109_1', 'status': 'FAIL',
              'baseline_revision': BASE, 'expected_head': options.expected_head,
              'qualified_full_revision': BASE, 'full_completion_sha256': options.full_completion_sha256,
              'full_source_sha256': options.full_source_sha256, 'full_report_sha256': options.full_report_sha256,
              'full_outer_launch_sha256': options.full_outer_launch_sha256,
              'full_outer_completion_sha256': options.full_outer_completion_sha256,
              'immutable_runtime_files': immutable_runtime_count, 'owned_runtime_files': len(frozen),
              'current_functional_source_count': 1109, 'full_groups': 183, 'required_import_info_checks': 267, 'required_editor_camera_checks': 626, 'required_movie_groups': 21, 'root_postflight_sha256': options.full_postflight_sha256, 'new_source_targets': 13,
              'source_project_sha256': PROJECT_SHA, 'source_asset_sha256': ASSET_SHA,
              'private_input_manifest_sha256': H.sha(H.read(options.private_manifest, limit=65536)),
              'new_full_claimed': False, 'application_adopted': False,
              'sourceio_or_converter_requested': False, 'private_arrays_published': False,
              'actual_owner_contact_reproduced': False, 'body_triangle_contact_qualified': False,
              'swept_contact_qualified': False, 'skin_shader_equivalence_qualified': False,
              'moving_actor_inertia_qualified': False, 'gravity_rest_settling_qualified': False,
              'jobs': [], 'cases': [], 'contact_cases': []}
    try:
        H.safe(lane, missing=True); fd = os.open(lane, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd, token) == len(token), 'OWNED_LOCK_SHORT_WRITE'); os.fsync(fd)
        lane_identity = H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False); stage_owned = True
        studio = stage/'Studio'; studio.mkdir(); (stage/'Verification').mkdir()
        for name, raw in frozen.items():
            target = studio/H.rel(name); target.parent.mkdir(parents=True, exist_ok=True); H.new(target, raw)
        (studio/'output/private-desktop').mkdir(parents=True)
        H.need(H.sha(H.read(studio/'tools/private_desktop.py')) == H.PRIVATE_SHA, 'PRIVATE_LAUNCHER_PIN')
        H.new(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Miku Contact '+uuid.uuid4().hex)+'\n').encode())
        private_folder = stage/'PRIVATE_INPUTS'; private_folder.mkdir()
        private_paths = {}
        for role, raw in private_blobs.items():
            private_paths[role] = private_folder/('stuff2.has' if role == 'saved_copy' else role+'.json')
            H.new(private_paths[role], raw)
        H.json_new(stage/'SOURCE_SNAPSHOT.json', {'format': 'has_miku_contact_owned_snapshot_1', 'baseline_revision': BASE,
                   'publication_head': options.expected_head, 'qualified_functional_source_count': 1109, 'full_completion_sha256': options.full_completion_sha256,
                   'files': {name: {'bytes': len(raw), 'sha256': H.sha(raw)} for name, raw in frozen.items()}})
        Q.run_case(H, stage, studio, runtime, result, 'import', None, [], None, 0, graphical=False, timeout=90)
        for name, script, marker, count in (
            ('probe-unit', 'tests/secondary_collision_probe_unit.gd', 'MIKU_COLLISION_PROBE_UNIT ', 40),
            ('binding-unit', 'tests/miku_collider_binding_unit.gd', 'MIKU_BINDING_UNIT ', 27),
            ('geometry-unit', 'tests/secondary_collision_geometry_unit.gd', 'COLLISION_GEOMETRY_UNIT ', 26),
            ('conversion-unit', 'tests/godot_skin_weight_conversion_unit.gd', 'GODOT_SKIN_WEIGHT_CONVERSION_UNIT ', 24),
            ('skin-unit', 'tests/miku_skin_binding_unit.gd', 'MIKU_SKIN_BINDING_UNIT ', 54)):
            Q.run_case(H, stage, studio, runtime, result, name, script, [], marker, count, graphical=False, timeout=25)
        result['pure_checks'] = sum(row.get('checks', 0) for row in result['cases'])
        H.need(result['pure_checks'] == 171, 'ALL_171_PURE_CONTROLS')
        Q.run_case(H, stage, studio, runtime, result, 'weight-engine-conformance',
                   'tests/godot_skin_weight_engine_conformance.gd', [], 'GODOT_SKIN_WEIGHT_ENGINE_CONFORMANCE ', 13,
                   graphical=False, timeout=25)
        result['engine_weight_conformance_checks'] = 13
        native_failures = []
        for editing in (True, False):
            for profile in ('original_zero_colliders', 'upper_only', 'full_lower_envelope'):
                name = ('pose' if editing else 'timeline')+'-'+profile
                output = stage/name; output.mkdir()
                arguments = [output, private_paths['saved_copy'], private_paths['colliders'], private_paths['alignment'],
                             'editing_true' if editing else 'editing_false', profile, options.ticks]
                job_passed = False
                try:
                    Q.run_case(H, stage, studio, runtime, result, name, 'tests/miku_contact_qualification.gd', arguments,
                               'MIKU_CONTACT_QUALIFICATION ', 14, graphical=True, timeout=175)
                    job_passed = True
                except Exception as error:
                    native_failures.append({'case': name, 'error_type': type(error).__name__,
                                            'error_code': str(error) if isinstance(error, H.Refusal) else 'NATIVE_CASE_EXCEPTION'})
                H.need(all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
                       and all(row.get('reaped') is True for _process, row in H.OWNED),
                       'NATIVE_CASE_CLOSURE_UNPROVEN_STOP')
                report = output/'PRIVATE_CONTACT_RESULT.json'
                if report.exists():
                    private_result = H.parse(H.read(report, limit=4*1024*1024))
                    H.need(private_result.get('format') == 'has_private_miku_saved_contact_qualification_1'
                           and private_result.get('private_do_not_publish') is True
                           and private_result.get('source_project_sha256') == PROJECT_SHA
                           and private_result.get('source_asset_sha256') == ASSET_SHA
                           and private_result.get('initial_editing_context') is editing
                           and private_result.get('collision_profile') == profile
                           and private_result.get('application_adopted') is False, 'PRIVATE_CASE_IDENTITY')
                    summary = public_case(private_result)
                    summary['qualified_runtime_job_passed'] = job_passed
                    if not job_passed:
                        summary['measurement_report_status'] = summary.get('status')
                        summary['status'] = 'FAIL'
                        summary['capsule_contact_qualified'] = False
                    result['contact_cases'].append(summary)
                    if job_passed and private_result.get('status') == 'PASS':
                        H.need(private_result.get('checks') == 14 and private_result.get('failures') == 0
                               and private_result.get('ticks') == options.ticks
                               and private_result.get('calibration_qualified') is True
                               and private_result.get('actual_saved_case_loaded') is True
                               and private_result.get('saved_draft_channels') == 6 and private_result.get('stored_pose_channels') == 156
                               and private_result.get('saved_context_observation', {}).get('accepted') is True
                               and private_result.get('saved_fan_count') == 1
                               and private_result.get('private_render_captures') == 1, 'FULL_NATIVE_PASS_CONTRACT')
                        image = output/'PRIVATE_LIVE_FRAME.png'; H.read(image, limit=32*1024*1024)
                else:
                    native_failures.append({'case': name, 'error_code': 'PRIVATE_CASE_RESULT_MISSING'})
        result['native_failures'] = native_failures
        poses = [{row.get('sampled_pose_sha256') for row in result['contact_cases']
                  if row.get('initial_editing_context') is context} for context in (True, False)]
        fans = {row.get('saved_fan_field_sha256') for row in result['contact_cases']}
        result['explicit_contexts_distinct_and_stable'] = all(len(values) == 1 and None not in values for values in poses) and poses[0] != poses[1]
        result['saved_fan_fields_identical_between_cases'] = len(fans) == 1 and None not in fans
        result['all_six_cold_cases_complete'] = len(result['contact_cases']) == 6 and len(result['jobs']) == 13 and len(result['cases']) == 13
        result['all_capsule_candidates_passed'] = result['all_six_cold_cases_complete'] and all(row.get('status') == 'PASS' for row in result['contact_cases'])
        result['status'] = 'PASS' if not native_failures and result['all_six_cold_cases_complete'] and result['all_capsule_candidates_passed'] and result['explicit_contexts_distinct_and_stable'] and result['saved_fan_fields_identical_between_cases'] else 'FAIL'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, H.Refusal) else 'MIKU_QUALIFICATION_EXCEPTION'
    finally:
        for process, row in H.OWNED:
            row['reaped'] = H.reap(process)
        result['all_owned_launchers_reaped'] = all(row.get('reaped') is True for _process, row in H.OWNED)
        result['all_attempted_private_jobs_closed'] = all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
        result['parent_environment_unchanged'] = dict(os.environ) == parent_environment
        try:
            result['head_unchanged'] = H.head() == options.expected_head
        except BaseException:
            result['head_unchanged'] = False
        result['preservation_failures'] = H.preserve()
        result['all_admitted_inputs_preserved'] = not result['preservation_failures']
        try:
            result['current_functional_domain_preserved'] = S.domain(H, ROOT) == set(expected)
        except BaseException:
            result['current_functional_domain_preserved'] = False
        closure = result['all_owned_launchers_reaped'] and result['all_attempted_private_jobs_closed']
        result['owned_lock_removed'] = False
        if fd is not None:
            try:
                H.need(closure and H.stamp(os.fstat(fd)) == lane_identity and H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_RETAINED')
                os.lseek(fd, 0, os.SEEK_SET); H.need(os.read(fd, 128) == token, 'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd); fd = None; H.need(H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_PATH_CHANGED')
                lane.unlink(); result['owned_lock_removed'] = True
            except BaseException as error:
                result['lock_error_type'] = type(error).__name__
            finally:
                if fd is not None: os.close(fd)
        result['owned_lock_retained'] = lane_identity is not None and not result['owned_lock_removed']
        if not (closure and result['parent_environment_unchanged'] and result['head_unchanged']
                and result['all_admitted_inputs_preserved'] and result['current_functional_domain_preserved']
                and result['owned_lock_removed']):
            result['status'] = 'FAIL'
        if stage_owned:
            H.json_new(stage/'PRIVATE_COORDINATOR_RESULT.json', result)
            public = {key: value for key, value in result.items() if key not in ('jobs', 'cases', 'preservation_failures')}
            public['private_job_count'] = len(result['jobs'])
            public['preservation_failure_count'] = len(result['preservation_failures'])
            public['cases'] = [{key: value for key, value in row.items() if key in ('name', 'status', 'checks', 'graphical')} for row in result['cases']]
            H.json_new(stage/'PUBLIC_RESULT.json', public)
            print(json.dumps({'status': result['status'], 'pure_checks': result.get('pure_checks'),
                              'native_cases': len(result['contact_cases']), 'error_code': result.get('error_code'),
                              'result': str(stage/'PUBLIC_RESULT.json')}), flush=True)
    return 0 if result['status'] == 'PASS' and primary is None else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'PREFLIGHT_REFUSED', 'error_type': type(error).__name__, 'detail': str(error)}), flush=True)
        raise SystemExit(2)
