"""Root-only camera source qualification in a fresh owned snapshot. SOURCE AUTHORED, UNRUN.
No owner assets, SourceIO, converters, installed-app writes, or Full-verifier claims.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
import types
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = 'e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
FULL_REVISION = '36044471151a6e561d6d3a404859e76ddd05738d'
INPUT_PIN = (5757, 'ef15f3c52b4806454d37d3467e594870417cd211cc1258f60fe63f34677b4b5c')
HELPER_PIN = (26455, '990c37ddca7b1301613f5efc5a7e5a30ce2723369112ef274ee78d2d4dc34087')
READER_PIN = (22176, 'd5ab807301d2b51b9ecea5fab1624b12addffe8247f5eafae60bf02c63c6dcec')
EXPERIMENTS = tuple('experiments/reference_body_20261120/'+name for name in (
    'receipt_provenance.py', 'run_full.py', 'run_scoped.py', 'stage_legacy_inputs.py',
    'test_receipt_provenance.py', 'verify_units.py'))
ROOT_FILES = ('dependencies.json', 'launch.pyw', 'main.tscn', 'project.godot', 'run.py')
BAD_LOG = ('SCRIPT ERROR', 'SHADER ERROR', 'FAIL ', 'ObjectDB instances leaked', '_set_transient_exclusive_child')


def bootstrap_identity(info):
    # Reading may legitimately update atime. Bind every source identity field
    # used here explicitly, including nanosecond mtime, mode and file attributes.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, info.st_mode, getattr(info, 'st_file_attributes', 0))


def load_pinned(name, path, count, digest):
    # Bootstrap only the two immutable helper definitions. Never call their mains.
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('HELPER_ALIAS_PATH')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != count:
        raise RuntimeError('HELPER_REGULAR_PIN_REQUIRED')
    raw = path.read_bytes()
    after = path.lstat()
    if bootstrap_identity(before) != bootstrap_identity(after) or len(raw) != count or hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError('HELPER_BYTES_OR_IDENTITY_CHANGED')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module, raw


def source_domain(H):
    names = set(ROOT_FILES) | set(EXPERIMENTS)
    for prefix in ('src', 'tests', 'tools', 'examples', 'data'):
        for folder, dirs, files in os.walk(H.safe(ROOT/prefix), followlinks=False):
            for item in dirs:
                H.safe(Path(folder)/item)
            dirs[:] = [item for item in dirs if item not in ('__pycache__', '.godot', '.git')]
            for item in files:
                if item.endswith(('.pyc', '.pyo')):
                    continue
                path = H.safe(Path(folder)/item)
                H.need(stat.S_ISREG(path.lstat().st_mode), 'SPECIAL_SOURCE_PATH')
                names.add(path.relative_to(ROOT).as_posix())
    H.need(len({name.casefold() for name in names}) == len(names), 'SOURCE_CASE_COLLISION')
    return names


def validate_composite(H, catalogue, frozen):
    adoption = H.parse(H.read(HERE/'inputs/IMPORT_OFF_MAP_ADOPTION.json'))
    H.need(adoption.get('format') == 'has_exact_import_off_map_adoption_1'
           and adoption.get('status') == 'APPLIED_READBACK_VERIFIED'
           and adoption.get('base_revision') == BASE
           and adoption.get('functional_baseline_count') == 1084
           and adoption.get('functional_target_count') == 1086, 'QUALIFIED_ADOPTION_REQUIRED')
    changes = [row for row in adoption['targets'] if row.get('kind') == 'functional']
    H.need(len(changes) == 8 and len({row['path'] for row in changes}) == 8, 'EXACT_EIGHT_CHANGES')
    style = H.parse(H.read(HERE/'inputs/SOURCE_LIGHT_TEST_STYLE_FINAL.json'))
    H.need(style.get('format') == 'has_source_light_test_style_delta_2'
           and style.get('path') == 'tests/test_source_lights.py'
           and style.get('production_source_changed') is False
           and style.get('final') == {'bytes': 8417, 'sha256': 'a714eda74f3fc3d0ed06fef287dca740298e5d841ede236ae1370e60adfbc3c4'}, 'FINAL_STYLE_PIN')
    expected = {name: {'bytes': row['bytes'], 'sha256': row['sha256']} for name, row in catalogue.items()}
    modified = set()
    for row in changes:
        name = H.rel(row['path'])
        if row['baseline'] is None:
            H.need(name not in expected and row['operation'] == 'add', 'ADD_BASE_MISMATCH')
        else:
            H.need(expected.get(name) == row['baseline'] and row['operation'] == 'modify', 'CHANGE_BASE_MISMATCH')
        expected[name] = row['target']
        modified.add(name)
    H.need(expected[style['path']] == style['original'], 'STYLE_ORIGINAL_PIN')
    H.need(style['path'] in modified, 'STYLE_PATH_MUST_BE_ONE_OF_QUALIFIED_EIGHT')
    expected[style['path']] = style['final']
    H.need(len(expected) == 1086 and source_domain(H) == set(expected), 'CURRENT_1086_EXACT_DOMAIN')
    current = {}
    for name, row in expected.items():
        path = ROOT/H.rel(name)
        current[name] = H.read(path, row['bytes'], row['sha256'])
        if name not in modified:
            H.need(path.lstat().st_mtime_ns == catalogue[name]['mtime_ns'], 'UNTOUCHED_SOURCE_STAMP_DIFFERS')
    for name in modified:
        frozen[name] = current[name]
    H.need(len(frozen) == 1089, 'QUALIFIED_COMPOSITE_RUNTIME_1089')
    H.need(all(name in frozen and len(frozen[name]) == row['bytes'] and H.sha(frozen[name]) == row['sha256']
               for name, row in expected.items() if not name.startswith('experiments/')), 'EXACT_CURRENT_RUNTIME_BYTES')
    return expected, modified


def run_case(H, stage, studio, runtime, result, name, script, args, marker,
             count, *, graphical, timeout, report=None, tail=None):
    case = stage/'Verification'/name
    case.mkdir()
    user = stage/'UserData'/name
    for leaf in ('Roaming', 'Local', 'Temp'):
        (user/leaf).mkdir(parents=True)
    profile = 'HAS Camera Qualification '+stage.name+' '+name+' '+uuid.uuid4().hex
    H.replace_owned(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith('HYBRID_') or key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONPYCACHEPREFIX'):
            env.pop(key, None)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               HYBRID_PYTHON=runtime['python'], HYBRID_GODOT=runtime['godot'], HYBRID_FFMPEG=runtime['ffmpeg'],
               APPDATA=str(user/'Roaming'), LOCALAPPDATA=str(user/'Local'), TEMP=str(user/'Temp'), TMP=str(user/'Temp'))
    receipt = studio/'output/private-desktop'/(name+'.json')
    command = [runtime['pythonw'], str(studio/'tools/private_desktop.py'), '--receipt', str(receipt), '--', runtime['godot']]
    if not graphical:
        command.append('--headless')
    command += ['--audio-driver', 'Dummy', '--path', str(studio), '--log-file', str(case/'engine.log')]
    if script:
        command += ['--script', script]
        if args:
            command += ['--', *map(str, args)]
    else:
        command += ['--editor', '--import', '--quit']
    state = {'name': name, 'status': 'RUNNING', 'expected_checks': count, 'graphical': graphical, 'custom_user_profile': profile}
    result['cases'].append(state)
    try:
        completed = H.owned_command(command, case, studio, runtime, env, result['jobs'], window=graphical, timeout=timeout)
        proof = H.parse(H.read(receipt, limit=1024*1024))
        H.need(not graphical or proof.get('private_window_seen') is True, 'ACTUAL_PRIVATE_WINDOW_REQUIRED')
        H.need(completed.returncode == 0, 'CASE_NONZERO_EXIT')
        log = completed.stdout+'\n'+completed.stderr
        H.need(not any(text in log for text in BAD_LOG), 'CASE_ERROR_OR_LEAK')
        engine = H.read(case/'engine.log', limit=H.MAX_LOG).decode('utf-8', 'replace')
        H.need(not any(text in engine for text in BAD_LOG) and not re.search(r'(?m)^ERROR:', engine), 'ENGINE_LOG_ERROR_OR_LEAK')
        if marker:
            hits = [line[len(marker):] for line in completed.stdout.splitlines() if line.startswith(marker)]
            H.need(len(hits) == 1, 'EXACT_ONE_CASE_MARKER')
            value = H.parse(hits[0])
            H.need(type(value.get('checks')) is int and value['checks'] == count
                   and type(value.get('failures')) is int and value['failures'] == 0, 'EXACT_CASE_ASSERTION_COUNT')
            H.need(sum(line.startswith('PASS ') for line in completed.stdout.splitlines()) == count, 'EXACT_PASS_LINE_COUNT')
            if report:
                H.need(H.parse(H.read(report, limit=4*1024*1024)) == value, 'RESULT_FILE_MARKER_MISMATCH')
            if tail:
                tail(H, value)
            state['checks'] = count
            state['result'] = value
        state['status'] = 'PASS'
    except BaseException:
        state['status'] = 'FAIL'
        raise


def timeline_contract(H, value):
    H.need(value.get('controlled_focus_loss_notification') is True,
           'CONTROLLED_FOCUS_LOSS_SCOPE_REQUIRED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--root-exclusive-lane-confirmed', action='store_true', required=True)
    parser.add_argument('--pure-only', action='store_true', help='Run import plus38pure checks; no app-window jobs')
    options = parser.parse_args()
    H, helper_raw = load_pinned('_camera_qualified_helpers', HERE/'qualified_helpers.py', *HELPER_PIN)
    H.need(H.ROOT == ROOT and os.name == 'nt' and sys.version_info[:2] == (3, 13)
           and not sys.flags.optimize and options.root_exclusive_lane_confirmed, 'ROOT_APPROVED_WINDOWS313_EXCLUSIVE_LANE')
    H.need(re.fullmatch('[0-9a-f]{40}', options.expected_head) is not None
           and re.fullmatch('[0-9a-f]{64}', options.self_sha256) is not None, 'EXPLICIT_PINS_REQUIRED')
    H.read(Path(__file__).resolve(), digest=options.self_sha256)
    H.read(HERE/'qualified_helpers.py', *HELPER_PIN)
    inputs = H.parse(H.read(HERE/'INPUT_PINS.json', *INPUT_PIN))
    H.need(inputs.get('baseline_revision') == BASE and inputs.get('qualified_full_revision') == FULL_REVISION
           and len(inputs.get('files', [])) == 32
           and inputs.get('candidate_manifest_sha256') == '6fa07005ce67dfa3d48e0abdde5c8570f7d95d6e28865a339fc5d029c6c4b8b7', 'CAMERA_INPUT_DOMAIN')
    for row in inputs['files']:
        H.read(HERE/H.rel(row['path']), row['bytes'], row['sha256'])
    B, reader_raw = load_pinned('_camera_qualified_reader', HERE/'qualified_snapshot_reader.py', *READER_PIN)
    H.need(B.ROOT == ROOT, 'SNAPSHOT_READER_ROOT')
    # Historical Full remains immutable; this does not reclassify it as a new Full.
    full, catalogue, proofs = B.validate_full(H.FULL, FULL_REVISION, H.FULL_SHA)
    for path in proofs:
        H.read(path)
    for leaf in ('source-before.json', 'source-after.json'):
        H.read(H.FULL/leaf, digest=H.SOURCE_SHA)
    H.need(H.head() == options.expected_head, 'EXPECTED_PUBLICATION_HEAD_CHANGED')
    frozen = B.source_blobs(BASE, catalogue)
    H.need(len(frozen) == 1087, 'IMMUTABLE_BASE_RUNTIME_1087')
    expected, modified = validate_composite(H, catalogue, frozen)
    lock = H.parse(H.read(H.LOCK, digest=H.LOCK_SHA))
    runtime = lock['runtime_paths']
    H.need(len(lock['runtime_executables']) == 6, 'EXACT_SIX_APPROVED_RUNTIME_PINS')
    for path, row in lock['runtime_executables'].items():
        H.read(path, row['bytes'], row['sha256'], limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns == row['mtime_ns'], 'RUNTIME_MTIME_CHANGED')
    H.need(Path(sys.executable).resolve() == Path(runtime['python']).resolve(), 'APPROVED_PYTHON_REQUIRED')
    candidate = H.parse(H.read(HERE/'candidate/SOURCE_PINS.json', 4202,
                             '6fa07005ce67dfa3d48e0abdde5c8570f7d95d6e28865a339fc5d029c6c4b8b7'))
    H.need(candidate.get('format') == 'has_source_camera_timeline_ux_manifest_1'
           and len(candidate.get('files', [])) == 25, 'EXACT_26_FILE_CAMERA_CANDIDATE')
    for row in candidate['files']:
        H.read(HERE/'candidate'/H.rel(row['path']), row['bytes'], row['sha256'])
    target_document = H.parse(H.read(HERE/'inputs/CAMERA_TARGETS.json'))
    targets = target_document['targets']
    H.need(target_document.get('format') == 'has_exact_camera_qualification_targets_1'
           and target_document.get('literal_patch_count') == 13
           and len(targets) == 10 and len({row['path'] for row in targets}) == 10,
           'EXACT_TEN_CAMERA_TARGETS')
    H.need(sum(row['operation'] == 'replace' for row in targets) == 3
           and sum(row['operation'] == 'new' for row in targets) == 7,
           'CAMERA_THREE_REPLACED_SEVEN_NEW')
    # Independently reproduce all13literal integration anchors. The two full
    # Timeline payloads must equal their anchors; app has only its five anchors.
    patches = H.parse(H.read(HERE/'candidate/PATCHES.json'))
    H.need(patches.get('format') == 'has_unadopted_camera_timeline_ux_patch_1'
           and patches.get('base_revision') == BASE and len(patches.get('patches', [])) == 13,
           'EXACT_CAMERA_ANCHOR_DOCUMENT')
    replacements = {row['path']: row for row in targets if row['operation'] == 'replace'}
    H.need(set(replacements) == {row['path'] for row in patches['patches']}, 'EXACT_PATCH_TARGET_DOMAIN')
    for name, row in replacements.items():
        H.need(name in frozen and len(frozen[name]) == row['base_bytes']
               and H.sha(frozen[name]) == row['base_sha256'], 'CAMERA_BASE_PIN_CHANGED')
        text = frozen[name].decode('utf-8')
        for patch in (part for part in patches['patches'] if part['path'] == name):
            H.need(patch.get('base_bytes') == row['base_bytes']
                   and patch.get('base_sha256') == row['base_sha256']
                   and type(patch.get('before')) is str and patch['before']
                   and type(patch.get('after')) is str and text.count(patch['before']) == 1,
                   'UNIQUE_CAMERA_INTEGRATION_ANCHOR')
            text = text.replace(patch['before'], patch['after'], 1)
        H.need(text.encode('utf-8') == H.read(HERE/H.rel(row['input']), row['bytes'], row['sha256']),
               'CAMERA_FULL_PAYLOAD_MUST_EQUAL_ANCHORS')
    for row in targets:
        name = H.rel(row['path'])
        if row['operation'] == 'new':
            H.need(name not in frozen, 'CAMERA_NEW_PATH_EXISTS')
        frozen[name] = H.read(HERE/H.rel(row['input']), row['bytes'], row['sha256'])
    H.need(len(frozen) == 1096, 'CAMERA_OWNED_RUNTIME_1096')
    stage = ROOT.parent/('has-camera-qualification-'+str(time.time_ns()))
    H.safe(stage, missing=True)
    lane = ROOT/'output/source-camera-qualification.lock'
    lane_fd = None
    lane_identity = None
    token = uuid.uuid4().hex.encode()
    stage_owned = False
    primary = None
    parent_environment = dict(os.environ)
    result = {'format': 'has_camera_source_snapshot_qualification_1', 'status': 'FAIL',
              'baseline_revision': BASE, 'expected_head': options.expected_head, 'qualified_historical_full_revision': FULL_REVISION,
              'current_functional_source_count': 1086, 'current_changed_functional_files': 8,
              'owned_runtime_files': 1096, 'camera_targets': 10, 'candidate_manifest_sha256': '6fa07005ce67dfa3d48e0abdde5c8570f7d95d6e28865a339fc5d029c6c4b8b7',
              'mode': 'pure_only' if options.pure_only else 'eight_style_scale_workspace_variants',
              'expected_assertion_checks': 38 if options.pure_only else 486,
              'new_whole_full_claimed': False, 'application_adopted': False, 'owner_acceptance_claimed': False,
              'native_owner_assets_read': False, 'sourceio_or_native_conversion_started': False, 'jobs': [], 'cases': []}
    try:
        H.safe(lane, missing=True)
        lane_fd = os.open(lane, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(lane_fd, token) == len(token), 'OWNED_LANE_SHORT_WRITE')
        os.fsync(lane_fd)
        lane_identity = H.stamp(os.fstat(lane_fd))
        stage.mkdir(exist_ok=False)
        stage_owned = True
        studio = stage/'Studio'
        studio.mkdir()
        (stage/'Verification').mkdir()
        for name, raw in frozen.items():
            path = studio/H.rel(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            H.new(path, raw)
        (studio/'output/private-desktop').mkdir(parents=True)
        H.need(H.sha(H.read(studio/'tools/private_desktop.py')) == H.PRIVATE_SHA, 'QUALIFIED_PRIVATE_LAUNCHER_PIN')
        profile = 'HAS Camera Qualification '+uuid.uuid4().hex
        H.new(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
        H.json_new(stage/'SOURCE_SNAPSHOT.json', {'format': 'has_camera_owned_source_snapshot_1', 'baseline_revision': BASE,
                   'publication_head': options.expected_head, 'files': {name: {'bytes': len(raw), 'sha256': H.sha(raw)} for name, raw in frozen.items()},
                   'current_functional_catalogue': expected, 'qualified_current_eight': sorted(modified)})
        run_case(H, stage, studio, runtime, result, 'import', None, [], None, 0, graphical=False, timeout=90)
        run_case(H, stage, studio, runtime, result, 'key-edits', 'tests/camera_key_edits_unit.gd', [],
                 'CAMERA_KEY_EDITS_UNIT ', 26, graphical=False, timeout=30)
        run_case(H, stage, studio, runtime, result, 'lens-planning', 'tests/camera_lens_gesture_unit.gd', [],
                 'CAMERA_LENS_GESTURE_UNIT ', 12, graphical=False, timeout=30)
        if not options.pure_only:
            for theme in ('classic', 'neon'):
                for scale in (100, 150):
                    for advanced in (False, True):
                        label = theme+'-'+str(scale)+'-'+('advanced' if advanced else 'simple')
                        flags = (['--classic'] if theme == 'classic' else [])
                        flags += ['--150'] if scale == 150 else []
                        flags += ['--advanced'] if advanced else []
                        timeline = stage/('Timeline-'+label)
                        timeline.mkdir()
                        run_case(H, stage, studio, runtime, result, 'timeline-'+label,
                                 'tests/camera_timeline_ux_smoke.gd', [timeline, *flags],
                                 'CAMERA_TIMELINE_UX_SMOKE ', 34, graphical=True, timeout=175,
                                 tail=timeline_contract)
                        image = H.read(timeline/'camera-timeline.png', limit=32*1024*1024)
                        H.need(len(image) >= 24 and image[:8] == b'\x89PNG\r\n\x1a\n'
                               and int.from_bytes(image[16:20], 'big') > 0
                               and int.from_bytes(image[20:24], 'big') > 0,
                               'TIMELINE_SCREENSHOT_MUST_EXIST')
                        lens = stage/('Lens-'+label)
                        lens.mkdir()
                        run_case(H, stage, studio, runtime, result, 'lens-'+label,
                                 'tests/camera_lens_gesture_smoke.gd', [lens, *flags],
                                 'CAMERA_LENS_GESTURE_SMOKE ', 22, graphical=True, timeout=165)
        result['checks'] = sum(row.get('checks', 0) for row in result['cases'])
        result['app_variant_count'] = 0 if options.pure_only else 8
        H.need(result['checks'] == (38 if options.pure_only else 486)
               and len(result['jobs']) == (3 if options.pure_only else 19),
               'ALL_PLANNED_CHECKS_AND_PRIVATE_JOBS_REQUIRED')
        result['status'] = 'PASS'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, H.Refusal) else 'CAMERA_QUALIFICATION_EXCEPTION'
    finally:
        for process, row in H.OWNED:
            row['reaped'] = H.reap(process)
        result['all_owned_launchers_reaped'] = all(row.get('reaped') is True for _p, row in H.OWNED)
        result['all_attempted_private_jobs_closed'] = all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
        result['parent_environment_unchanged'] = dict(os.environ) == parent_environment
        try:
            result['head_unchanged'] = H.head() == options.expected_head
        except BaseException:
            result['head_unchanged'] = False
        failures = H.preserve()
        result['preservation_failures'] = failures
        result['all_admitted_inputs_preserved'] = not failures
        try:
            result['current_functional_domain_preserved'] = source_domain(H) == set(expected)
        except BaseException:
            result['current_functional_domain_preserved'] = False
        result['admitted_inputs'] = len(H.EXPECTED)
        closure = result['all_owned_launchers_reaped'] and result['all_attempted_private_jobs_closed']
        result['owned_lock_removed'] = False
        if lane_fd is not None:
            try:
                H.need(closure and H.stamp(os.fstat(lane_fd)) == lane_identity and H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_RETAINED_CLOSURE_OR_IDENTITY')
                os.lseek(lane_fd, 0, os.SEEK_SET)
                H.need(os.read(lane_fd, 128) == token, 'OWNED_LOCK_TOKEN_CHANGED')
                os.close(lane_fd)
                lane_fd = None
                H.need(H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_PATH_CHANGED')
                lane.unlink()
                result['owned_lock_removed'] = True
            except BaseException as error:
                result['lock_error_type'] = type(error).__name__
            finally:
                if lane_fd is not None:
                    os.close(lane_fd)
        result['owned_lock_retained'] = lane_identity is not None and not result['owned_lock_removed']
        if not (closure and result['parent_environment_unchanged'] and result['head_unchanged']
                and result['all_admitted_inputs_preserved'] and result['current_functional_domain_preserved'] and result['owned_lock_removed']):
            result['status'] = 'FAIL'
        if stage_owned:
            H.json_new(stage/'CAMERA_QUALIFICATION_RESULT.json', result)
            print(json.dumps({'status': result['status'], 'checks': result.get('checks'), 'error_code': result.get('error_code'),
                              'result': str(stage/'CAMERA_QUALIFICATION_RESULT.json')}), flush=True)
    return 0 if result['status'] == 'PASS' and primary is None else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'PREFLIGHT_REFUSED', 'error_type': type(error).__name__, 'detail': str(error)}), flush=True)
        raise SystemExit(2)
