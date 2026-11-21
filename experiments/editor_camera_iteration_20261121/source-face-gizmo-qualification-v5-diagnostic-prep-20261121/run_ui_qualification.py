"""Root-only UI source qualification in a fresh owned snapshot. SOURCE AUTHORED, UNRUN.
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
INPUT_PIN = (2816, '83ff4b2177d8a614f2956d97a3329792915dff00f14a01c1d160d734158663b3')
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


def generated_shape(H, studio, destination):
    # These three pinned shipping Python sources contain only synthetic geometry.
    # The function performs no native lookup and does not invoke subprocess tools.
    old_path = list(sys.path)
    wanted = {'test_helper_morphs': studio/'tests/test_helper_morphs.py',
              'test_secondary_helpers': studio/'tests/test_secondary_helpers.py',
              'secondary_helpers': studio/'tools/secondary_helpers.py'}
    H.need(not any(name in sys.modules for name in wanted), 'FIXTURE_MODULE_ALREADY_IMPORTED')
    try:
        sys.path[:0] = [str(studio/'tests'), str(studio/'tools')]
        import test_helper_morphs as shapes
        for name, path in wanted.items():
            H.need(Path(sys.modules[name].__file__).resolve() == path.resolve(), 'FIXTURE_MODULE_NOT_OWNED')
            H.read(path)
        shapes.shape_fixture(destination)
    finally:
        sys.path[:] = old_path
    H.read(destination, limit=1024*1024)


def run_case(H, stage, studio, runtime, result, name, script, args, marker,
             count, *, graphical, timeout, report=None, tail=None):
    case = stage/'Verification'/name
    case.mkdir()
    user = stage/'UserData'/name
    for leaf in ('Roaming', 'Local', 'Temp'):
        (user/leaf).mkdir(parents=True)
    profile = 'HAS UI Qualification '+stage.name+' '+name+' '+uuid.uuid4().hex
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


def face_contract(H, value):
    rows = value.get('resize_cases')
    H.need(type(rows) is list and len(rows) == 2
           and [row.get('interface_scale') for row in rows] == [1.0, 1.5]
           and all(row.get('controlled_late_size_signal') is True for row in rows)
           and value.get('lifecycle_checks') == 6
           and value.get('application_adopted') is False and value.get('owner_layout_acceptance') is False,
           'FACE_TWO_DPI_AND_CONTROLLED_SIGNAL_CONTRACT')


def handle_contract(H, value):
    rows = value.get('cases')
    H.need(type(rows) is list and len(rows) == 4
           and [(row.get('window'), row.get('interface_scale')) for row in rows]
           == [('(1600, 1000)', 1.0), ('(1600, 1000)', 1.5), ('(3440, 1440)', 1.0), ('(3440, 1440)', 1.5)]
           and all(row.get('ring_pixel_hits', 0) >= 5 and row.get('wrong_band_hits', 99) <= 1 for row in rows)
           and value.get('application_adopted') is False and value.get('owner_hand_comfort_certified') is False,
           'HANDLE_FOUR_REAL_PIXEL_AND_PICK_CASES')


def rotation_contract(H, value):
    H.need(len(value.get('cases', [])) == 24 and len(value.get('view_cases', [])) == 24, 'EXISTING_ROTATION_CASES_RETAINED')


def handle_diagnostic_artifacts(H, stage):
    """Readback only. Diagnostic validity can never override a failed test."""
    folder = stage/'Handles'
    path = folder/'handle-size-result.json'
    value = H.parse(H.read(path, limit=4*1024*1024))
    H.need(value.get('diagnostic_measurements_only') is True
           and value.get('original_assertions_unchanged') == 27
           and value.get('checks') == 27 and type(value.get('failures')) is int,
           'HANDLE_DIAGNOSTIC_ORIGINAL_ASSERTIONS_REQUIRED')
    cases = value.get('cases')
    H.need(type(cases) is list and len(cases) == 4, 'FOUR_HANDLE_DIAGNOSTIC_CASES')
    images = []
    for index, case in enumerate(cases):
        measurement = case.get('measurement')
        H.need(type(measurement) is dict and measurement.get('image') == 'handle-case-'+str(index)+'.png'
               and measurement.get('image_save_error') == 0
               and type(measurement.get('clipping')) is dict
               and type(measurement.get('near_scene_contains')) is bool
               and type(measurement.get('samples')) is list and len(measurement['samples']) == 6,
               'HANDLE_DIAGNOSTIC_MEASUREMENT_REQUIRED')
        image_path = folder/measurement['image']
        raw = H.read(image_path, limit=32*1024*1024)
        H.need(len(raw) >= 24 and raw[:8] == b'\x89PNG\r\n\x1a\n', 'HANDLE_DIAGNOSTIC_PNG_REQUIRED')
        extent = [int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')]
        H.need(all(size > 0 for size in extent) and extent == measurement.get('image_size'),
               'HANDLE_DIAGNOSTIC_PNG_EXTENT_MATCH')
        images.append({'path': str(image_path), 'bytes': len(raw), 'sha256': H.sha(raw), 'dimensions': extent,
                       'window': case.get('window'), 'interface_scale': case.get('interface_scale')})
    return {'report': str(path), 'report_sha256': H.sha(H.read(path)), 'checks': value['checks'],
            'failures': value['failures'], 'images': images, 'diagnosis_proven': False,
            'qualification_status_overridden': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--root-exclusive-lane-confirmed', action='store_true', required=True)
    options = parser.parse_args()
    H, helper_raw = load_pinned('_ui_qualified_helpers', HERE/'qualified_helpers.py', *HELPER_PIN)
    H.need(H.ROOT == ROOT and os.name == 'nt' and sys.version_info[:2] == (3, 13)
           and not sys.flags.optimize and options.root_exclusive_lane_confirmed, 'ROOT_APPROVED_WINDOWS313_EXCLUSIVE_LANE')
    H.need(re.fullmatch('[0-9a-f]{40}', options.expected_head) is not None
           and re.fullmatch('[0-9a-f]{64}', options.self_sha256) is not None, 'EXPLICIT_PINS_REQUIRED')
    H.read(Path(__file__).resolve(), digest=options.self_sha256)
    H.read(HERE/'qualified_helpers.py', *HELPER_PIN)
    inputs = H.parse(H.read(HERE/'INPUT_PINS.json', *INPUT_PIN))
    H.need(inputs.get('baseline_revision') == BASE and inputs.get('qualified_full_revision') == FULL_REVISION
           and len(inputs.get('files', [])) == 15, 'UI_INPUT_DOMAIN')
    for row in inputs['files']:
        H.read(HERE/H.rel(row['path']), row['bytes'], row['sha256'])
    B, reader_raw = load_pinned('_ui_qualified_reader', HERE/'qualified_snapshot_reader.py', *READER_PIN)
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
    targets = H.parse(H.read(HERE/'inputs/UI_TARGETS.json'))['targets']
    H.need(len(targets) == 9 and len({row['path'] for row in targets}) == 9, 'EXACT_NINE_UI_TARGETS')
    for row in targets:
        name = H.rel(row['path'])
        if row['operation'] == 'replace':
            H.need(name in frozen and len(frozen[name]) == row['base_bytes']
                   and H.sha(frozen[name]) == row['base_sha256'], 'UI_BASE_PIN_CHANGED')
        else:
            H.need(row['operation'] == 'new' and name not in frozen, 'UI_NEW_PATH_EXISTS')
        frozen[name] = H.read(HERE/'payload'/name, row['bytes'], row['sha256'])
    H.need(len(frozen) == 1094, 'UI_OWNED_RUNTIME_1094')
    stage = ROOT.parent/('has-face-gizmo-qualification-'+str(time.time_ns()))
    H.safe(stage, missing=True)
    lane = ROOT/'output/source-face-gizmo-qualification.lock'
    lane_fd = None
    lane_identity = None
    token = uuid.uuid4().hex.encode()
    stage_owned = False
    primary = None
    parent_environment = dict(os.environ)
    result = {'format': 'has_face_gizmo_source_snapshot_qualification_1', 'status': 'FAIL',
              'baseline_revision': BASE, 'expected_head': options.expected_head, 'qualified_historical_full_revision': FULL_REVISION,
              'current_functional_source_count': 1086, 'current_changed_functional_files': 8,
              'owned_runtime_files': 1094, 'ui_targets': 9, 'expected_assertion_checks': 413,
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
        profile = 'HAS UI Qualification '+uuid.uuid4().hex
        H.new(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps(profile)+'\n').encode())
        (stage/'Fixtures').mkdir()
        fixture = stage/'Fixtures/shape.glb'
        generated_shape(H, studio, fixture)
        H.json_new(stage/'SOURCE_SNAPSHOT.json', {'format': 'has_ui_owned_source_snapshot_1', 'baseline_revision': BASE,
                   'publication_head': options.expected_head, 'files': {name: {'bytes': len(raw), 'sha256': H.sha(raw)} for name, raw in frozen.items()},
                   'current_functional_catalogue': expected, 'qualified_current_eight': sorted(modified)})
        run_case(H, stage, studio, runtime, result, 'import', None, [], None, 0, graphical=False, timeout=90)
        run_case(H, stage, studio, runtime, result, 'geometry', 'tests/editor_geometry_unit.gd', [],
                 'EDITOR_GEOMETRY_UNIT ', 37, graphical=False, timeout=20)
        face = stage/'Face'
        face.mkdir()
        run_case(H, stage, studio, runtime, result, 'face', 'tests/face_window_layout_smoke.gd', [face, fixture],
                 'FACE_WINDOW_LAYOUT ', 36, graphical=True, timeout=90, report=face/'face-window-layout-result.json', tail=face_contract)
        handle = stage/'Handles'
        handle.mkdir()
        run_case(H, stage, studio, runtime, result, 'handles', 'tests/pose_handle_size_smoke.gd', [handle],
                 'HANDLE_SIZE_SMOKE ', 27, graphical=True, timeout=120, report=handle/'handle-size-result.json', tail=handle_contract)
        rotation = stage/'Rotation'
        rotation.mkdir()
        run_case(H, stage, studio, runtime, result, 'rotation-write', 'tests/rotation_gizmo_smoke.gd', [rotation],
                 'ROTATION_GIZMO ', 309, graphical=True, timeout=130, report=studio/'output/rotation-gizmo-result.json', tail=rotation_contract)
        run_case(H, stage, studio, runtime, result, 'rotation-read', 'tests/rotation_gizmo_smoke.gd', [rotation, '--read'],
                 'ROTATION_GIZMO_COLD ', 4, graphical=True, timeout=130, report=studio/'output/rotation-gizmo-cold-result.json')
        result['checks'] = sum(row.get('checks', 0) for row in result['cases'])
        H.need(result['checks'] == 413 and len(result['jobs']) == 6, 'ALL_413_CHECKS_AND_SIX_JOBS_REQUIRED')
        result['status'] = 'PASS'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, H.Refusal) else 'UI_QUALIFICATION_EXCEPTION'
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
        if stage_owned and (stage/'Handles/handle-size-result.json').is_file():
            try:
                result['handle_diagnostic_artifacts'] = handle_diagnostic_artifacts(H, stage)
            except BaseException as error:
                result['status'] = 'FAIL'
                result['diagnostic_readback_error_type'] = type(error).__name__
                result['diagnostic_readback_error'] = str(error) if isinstance(error, H.Refusal) else 'HANDLE_DIAGNOSTIC_READBACK_EXCEPTION'
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
            H.json_new(stage/'UI_QUALIFICATION_RESULT.json', result)
            print(json.dumps({'status': result['status'], 'checks': result.get('checks'), 'error_code': result.get('error_code'),
                              'result': str(stage/'UI_QUALIFICATION_RESULT.json')}), flush=True)
    return 0 if result['status'] == 'PASS' and primary is None else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'PREFLIGHT_REFUSED', 'error_type': type(error).__name__, 'detail': str(error)}), flush=True)
        raise SystemExit(2)
