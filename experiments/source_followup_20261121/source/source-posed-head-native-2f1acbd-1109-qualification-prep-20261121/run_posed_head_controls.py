"""Root-only derived-head control after independently completed2f1acbd Full183 and Rootpostflight.
SOURCE ONLY / UNRUN. Never modifies Main, the Full checkout or owner originals.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import struct
import sys
import time
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REVISION = '2f1acbd7867087d9f18cfbc1122cc0c883c5f788'
Q_PIN = (21967, 'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
S_PIN = (11221, '0afe7a6d1ceda9ddce6de26dcadb213cb7306fdf5907709ffd57c4765c14262d')
INPUT_PIN = (3378, '339a51334a49bbad75f45f53a70067fb096674dbc03fa783f866d7fd5e6c8400')
ARCHIVE_SHA = 'd304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb'
ASSET_SHA = 'e3e233004f2ce1aed3c2f221f7d92d9218c0de1f133cad88557f8181644e6e8c'
OLD_PRIVATE_SHA = 'a6282215949e591855adb9ee7145dd7934c370bb9b85702ba55452e563b9503b'
OLD_PUBLIC_SHA = 'c459b1b08ffe7be9b7ebe8c2ea423ff437810e27f06f331069704070ab81aaaa'

def identity(info):
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

def png(H, path):
    raw = H.read(path, limit=32*1024*1024)
    H.need(len(raw) >= 33 and raw[:8] == b'\x89PNG\r\n\x1a\n'
           and raw[12:16] == b'IHDR' and struct.unpack('>II', raw[16:24]) == (1920, 1080),
           'EXACT_BOUNDED_PRIVATE1920_IMAGE')
    return {'bytes': len(raw), 'sha256': H.sha(raw)}

def admit_original_inputs(H):
    protected = ROOT/'output/owner-stuff-project-1795238638994/stuff.has'
    archive = H.read(protected, digest=ARCHIVE_SHA, limit=128*1024*1024)
    owner = ROOT.parent/'HAS-Review-Neon-973039e-native/Studio/stuff.has'
    # Current owner-original identity is pinned separately, regardless of resave.
    # Its bytes are preserved but never parsed, copied or called a reproduction.
    H.read(owner, limit=128*1024*1024)
    old = ROOT.parent/'has-close-face-captures-1795251016424609500'
    previous = H.parse(H.read(old/'PRIVATE_CAPTURES/PRIVATE_RESULT.json', digest=OLD_PRIVATE_SHA, limit=4*1024*1024))
    public = H.parse(H.read(old/'PUBLIC_RESULT.json', digest=OLD_PUBLIC_SHA, limit=1024*1024))
    H.need(public.get('status') == 'CAPTURED_FOR_PRIVATE_REVIEW' and public.get('capture_count') == 40
           and previous.get('fixture_sha256') == ARCHIVE_SHA and previous.get('saved_data_unchanged') is True
           and previous.get('fixture_sha256_unchanged') is True and len(previous.get('captures', [])) == 40,
           'EXACT_ORIGINAL40_PRIVATE_EVIDENCE')
    expected = {f'frame{frame}_{label}_backoff{backoff:.2f}_{kind}.png'
                for frame, label in ((0, 'playback'), (43, 'draft'))
                for backoff in (0., .1, .3, 1.)
                for kind in ('baseline', 'near_tenth', 'double_sided', 'opaque_face', 'bounds_margin')}
    actual = [row.get('image') for row in previous['captures']]
    H.need(len(set(actual)) == 40 and set(actual) == expected, 'EXACT_ORIGINAL40_IMAGE_NAMES')
    for name in sorted(expected):
        png(H, old/'PRIVATE_CAPTURES'/H.rel(name))
    H.read(old/'PRIVATE_CAPTURES/private-model.glb', digest=ASSET_SHA, limit=128*1024*1024)
    return archive

def marker_contract(H, value, mode):
    count = 22 if mode == 'cpu' else 49
    H.need(type(value) is dict and type(value.get('checks')) is int and value['checks'] == count
           and type(value.get('failures')) is int and value['failures'] == 0
           and value.get('context_count') == 2 and value.get('capture_count') == (0 if mode == 'cpu' else 16)
           and value.get('source_archive_sha256') == ARCHIVE_SHA and value.get('source_asset_sha256') == ASSET_SHA
           and value.get('head_vertices') == 5361 and value.get('face_surface_vertices') == 1489
           and value.get('neutral_imported_morph_targets') == 85
           and value.get('application_adopted') is False and value.get('visual_face_restoration_qualified') is False,
           'EXACT_SCOPED_NATIVE_CONTROL_MARKER')

def private_contract(H, path, mode):
    value = H.parse(H.read(path, limit=4*1024*1024))
    H.need(value.get('format') == 'has_private_posed_head_1103_controls_1'
           and value.get('private_do_not_publish') is True and value.get('mode') == mode
           and value.get('source_archive_sha256') == ARCHIVE_SHA and value.get('source_asset_sha256') == ASSET_SHA
           and type(value.get('checks')) is int and value['checks'] == (22 if mode == 'cpu' else 49)
           and type(value.get('failures')) is int and value['failures'] == 0
           and value.get('head_vertices') == 5361 and value.get('face_surface_vertices') == 1489
           and value.get('neutral_imported_morph_targets') == 85
           and value.get('application_adopted') is False and value.get('visual_face_restoration_qualified') is False
           and value.get('nonuniform_renderer_order_qualified') is False and value.get('export_or_cold_qualified') is False,
           'EXACT_PRIVATE_NATIVE_CONTROL_RESULT')
    rows = value.get('rows')
    H.need(type(rows) is list and len(rows) == (2 if mode == 'cpu' else 8), 'EXACT_PRIVATE_CONTROL_ROW_COUNT')
    for index, row in enumerate(rows):
        context = index if mode == 'cpu' else index//4
        H.need(type(row) is dict and type(row.get('frame')) in (int, float)
               and row['frame'] == (0, 43)[context] and row.get('editing') is (False, True)[context]
               and all(re.fullmatch('[0-9a-f]{64}', row.get(key, '')) is not None for key in ('pose_sha256', 'binding_sha256'))
               and type(row.get('derived_margin')) in (int, float) and math.isfinite(row['derived_margin'])
               and row['derived_margin'] >= 0 and row.get('actual_neutral_morphs_before_geometry') is True,
               'EXACT_NATIVE_CONTEXT_AND_GEOMETRY_TOKEN')
        if mode == 'cpu':
            H.need(row.get('vertices') == 5361 and row.get('contained') is True
                   and row.get('warm50_unchanged') is True, 'NATIVE_CPU_ALL_VERTICES_AND_CACHE_ADMISSION')
        else:
            H.need(type(row.get('backoff')) in (int, float) and row['backoff'] == (0., .1, .3, 1.)[index % 4]
                   and row.get('native_cpu_geometry_admitted') is True, 'EXACT_NATIVE_CAPTURE_BACKOFF')
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--full-folder', type=Path, required=True)
    parser.add_argument('--full-completion-sha256', required=True)
    parser.add_argument('--full-source-sha256', required=True)
    parser.add_argument('--full-report-sha256', required=True)
    parser.add_argument('--full-outer-folder', type=Path, required=True)
    parser.add_argument('--full-outer-launch-sha256', required=True)
    parser.add_argument('--full-outer-completion-sha256', required=True)
    parser.add_argument('--full-postflight-sha256', required=True)
    parser.add_argument('--root-exclusive-lane-confirmed', action='store_true', required=True)
    options = parser.parse_args()
    Q = source_module('_posed_head_qualified_job_helpers', HERE/'qualified_ui_host.py', Q_PIN)
    H, _ = Q.load_pinned('_posed_head_owned_helpers', HERE/'qualified_helpers.py', *Q.HELPER_PIN)
    H.need(H.ROOT == ROOT and os.name == 'nt' and sys.version_info[:2] == (3, 13)
           and not sys.flags.optimize and options.root_exclusive_lane_confirmed, 'ROOT_WINDOWS313_EXCLUSIVE_LANE')
    H.need(options.expected_head == REVISION and re.fullmatch('[0-9a-f]{64}', options.self_sha256) is not None,
           'EXACT2f1acbd_AND_SELF_PIN_REQUIRED')
    H.read(Path(__file__), digest=options.self_sha256)
    H.need(INPUT_PIN is not None, 'SOURCE_PACKET_NOT_FROZEN')
    inputs = H.parse(H.read(HERE/'INPUT_PINS.json', *INPUT_PIN))
    H.need(inputs.get('format') == 'has_posed_head_1109_control_inputs_1'
           and inputs.get('revision') == REVISION and len(inputs.get('targets', [])) == 5,
           'EXACT_DERIVED_HEAD_SOURCE_SCOPE')
    for row in inputs['files']:
        H.read(HERE/H.rel(row['path']), row['bytes'], row['sha256'])
    S, _ = Q.load_pinned('_posed_head_1109_admission', HERE/'source1109.py', *S_PIN)
    H.need(H.head() == REVISION, 'PUBLICATION_HEAD_CHANGED')
    expected = S.admit_full(H, Q, ROOT, HERE, options.full_folder,
        options.full_completion_sha256, options.full_source_sha256, options.full_report_sha256,
        options.full_outer_folder, options.full_outer_launch_sha256, options.full_outer_completion_sha256, options.full_postflight_sha256)
    frozen = S.immutable_runtime(H, Q, ROOT, expected)
    original_runtime_count = len(frozen)
    for row in inputs['targets']:
        name = H.rel(row['path'])
        H.need(name not in frozen and name.startswith(('src/', 'tests/')), 'ONLY_FIVE_NEW_CONTROL_TARGETS')
        frozen[name] = H.read(HERE/'payload'/name, row['bytes'], row['sha256'])
    H.need(len(frozen) == original_runtime_count+5, 'EXACT_DERIVED_CONTROL_RUNTIME')
    lock = H.parse(H.read(H.LOCK, digest=H.LOCK_SHA));runtime = lock['runtime_paths']
    H.need(len(lock['runtime_executables']) == 6, 'SIX_APPROVED_RUNTIME_PINS')
    for path, row in lock['runtime_executables'].items():
        H.read(path, row['bytes'], row['sha256'], limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns == row['mtime_ns'], 'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve() == Path(runtime['python']).resolve(), 'APPROVED_PYTHON')
    archive = admit_original_inputs(H)
    stage = ROOT.parent/('has-posed-head-native-controls-'+str(time.time_ns()));H.safe(stage, missing=True)
    lane = ROOT/'output/source-posed-head-native-1109.lock';token = uuid.uuid4().hex.encode()
    fd = None;lane_identity = None;stage_owned = False;primary = None
    parent_environment = dict(os.environ)
    result = {'format': 'has_posed_head_native_1109_control_1', 'status': 'FAIL', 'revision': REVISION,
              'source_context': 'completed2f1acbd_Full1109_183_and_b91_postflight_then_separate_owned_control_snapshot',
              'full_completion_sha256': options.full_completion_sha256, 'full_source_sha256': options.full_source_sha256,
              'full_report_sha256': options.full_report_sha256,
              'full_outer_launch_sha256': options.full_outer_launch_sha256,
              'full_outer_completion_sha256': options.full_outer_completion_sha256,
              'current_functional_source_count': 1109, 'full_groups': 183,
              'required_new_group_checks': 626, 'required_import_info_checks': 267, 'required_movie_groups': 21,
              'required_headless_lifecycle_jobs': 5, 'root_postflight_sha256': options.full_postflight_sha256,
              'immutable_runtime_files': original_runtime_count, 'owned_runtime_files': len(frozen), 'new_source_targets': 5,
              'source_archive_sha256': ARCHIVE_SHA, 'source_asset_sha256': ASSET_SHA,
              'owner_original_reproduced': False, 'original40_inputs_preserved': False,
              'new_Full_claimed': False, 'application_adopted': False, 'native_fix_qualified': False,
              'visual_face_restoration_qualified': False, 'nonuniform_renderer_order_qualified': False,
              'export_or_cold_qualified': False, 'private_arrays_published': False,
              'jobs': [], 'cases': []}
    try:
        H.safe(lane, missing=True);fd = os.open(lane, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        H.need(os.write(fd, token) == len(token), 'OWNED_LOCK_SHORT_WRITE');os.fsync(fd);lane_identity = H.stamp(os.fstat(fd))
        stage.mkdir(exist_ok=False);stage_owned = True;studio = stage/'Studio';studio.mkdir();(stage/'Verification').mkdir()
        for name, raw in frozen.items():
            target = studio/H.rel(name);target.parent.mkdir(parents=True, exist_ok=True);H.new(target, raw)
            H.read(target, len(raw), H.sha(raw))
        (studio/'output/private-desktop').mkdir(parents=True)
        H.need(H.sha(H.read(studio/'tools/private_desktop.py')) == H.PRIVATE_SHA, 'PRIVATE_LAUNCHER_PIN')
        H.new(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Posed Head '+uuid.uuid4().hex)+'\n').encode())
        private = stage/'PRIVATE_INPUTS';private.mkdir();saved = private/'protected.has';H.new(saved, archive)
        H.read(saved, len(archive), ARCHIVE_SHA)
        H.json_new(stage/'SOURCE_SNAPSHOT.json', {'format': 'has_posed_head_owned_source_1', 'revision': REVISION,
                   'files': {name: {'bytes': len(raw), 'sha256': H.sha(raw)} for name, raw in frozen.items()}})
        Q.run_case(H, stage, studio, runtime, result, 'import', None, [], None, 0, graphical=False, timeout=90)
        Q.run_case(H, stage, studio, runtime, result, 'envelope-unit', 'tests/posed_render_envelope_unit.gd', [],
                   'POSED_RENDER_ENVELOPE ', 21, graphical=False, timeout=25)
        Q.run_case(H, stage, studio, runtime, result, 'control-unit', 'tests/posed_render_bounds_unit.gd', [],
                   'POSED_RENDER_BOUNDS ', 22, graphical=False, timeout=25)
        cpu = stage/'PRIVATE_CPU_GEOMETRY'
        Q.run_case(H, stage, studio, runtime, result, 'native-cpu-geometry', 'tests/posed_head_native_controls.gd',
                   [saved, cpu, 'cpu', '-'], 'POSED_HEAD_NATIVE_CPU ', 22, graphical=False, timeout=120,
                   tail=lambda helper, value: marker_contract(helper, value, 'cpu'))
        cpu_file = cpu/'PRIVATE_RESULT.json';admission = private_contract(H, cpu_file, 'cpu')
        H.read(cpu/'private-model.glb', digest=ASSET_SHA, limit=128*1024*1024)
        H.need(all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
               and all(row.get('reaped') is True for _process, row in H.OWNED), 'CPU_ADMISSION_CLOSURE_REQUIRED_BEFORE_GPU')
        pictures = stage/'PRIVATE_CAPTURES'
        Q.run_case(H, stage, studio, runtime, result, 'native-captures', 'tests/posed_head_native_controls.gd',
                   [saved, pictures, 'captures', cpu_file], 'POSED_HEAD_NATIVE_CAPTURES ', 49,
                   graphical=True, timeout=150, tail=lambda helper, value: marker_contract(helper, value, 'captures'))
        captured = private_contract(H, pictures/'PRIVATE_RESULT.json', 'captures')
        H.read(pictures/'private-model.glb', digest=ASSET_SHA, limit=128*1024*1024)
        image_names = set()
        for index, row in enumerate(captured['rows']):
            native = admission['rows'][index//4]
            H.need(all(row[key] == native[key] for key in ('pose_sha256', 'binding_sha256')), 'GRAPHICAL_SOURCE_BOUND_CPU_GEOMETRY_DIFFERS')
            prefix = f"frame{int(row['frame'])}_{'draft' if row['editing'] else 'playback'}_backoff{row['backoff']:.2f}"
            for kind in ('baseline', 'derived'):
                cell = row.get(kind)
                expected_name = prefix+'_'+kind+'.png'
                H.need(type(cell) is dict and cell.get('image') == expected_name
                       and cell.get('dimensions') == [1920, 1080]
                       and re.fullmatch('[0-9a-f]{64}', cell.get('image_raw_sha256', '')) is not None
                       and expected_name not in image_names, 'EXACT_PRIVATE16_IMAGE_ROW')
                png(H, pictures/expected_name);image_names.add(expected_name)
        H.need(len(image_names) == 16 and len(result['jobs']) == 5 and len(result['cases']) == 5
               and sum(row.get('checks', 0) for row in result['cases']) == 114, 'EXACT_FIVE_JOBS114_CHECKS16_CAPTURES')
        result.update(status='CAPTURED_FOR_PRIVATE_REVIEW', pure_checks=43, native_cpu_geometry_checks=22,
                      native_capture_controls=49, private_capture_count=16, native_cpu_geometry_admitted=True)
    except BaseException as error:
        primary = error;result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, H.Refusal) else 'POSED_HEAD_CONTROL_EXCEPTION'
    finally:
        for process, row in H.OWNED:row['reaped'] = H.reap(process)
        result['all_owned_launchers_reaped'] = all(row.get('reaped') is True for _process, row in H.OWNED)
        result['all_attempted_private_jobs_closed'] = all(row.get('private_job_closed') is True and row.get('desktop_closed') is True for row in result['jobs'])
        result['parent_environment_unchanged'] = dict(os.environ) == parent_environment
        try:result['head_unchanged'] = H.head() == REVISION
        except BaseException:result['head_unchanged'] = False
        result['preservation_failures'] = H.preserve();result['all_admitted_inputs_preserved'] = not result['preservation_failures']
        result['original40_inputs_preserved'] = result['all_admitted_inputs_preserved']
        try:result['current_functional_domain_preserved'] = S.domain(H, ROOT) == set(expected)
        except BaseException:result['current_functional_domain_preserved'] = False
        closure = result['all_owned_launchers_reaped'] and result['all_attempted_private_jobs_closed']
        result['owned_lock_removed'] = False
        if fd is not None:
            try:
                H.need(closure and H.stamp(os.fstat(fd)) == lane_identity and H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_RETAINED')
                os.lseek(fd, 0, os.SEEK_SET);H.need(os.read(fd, 128) == token, 'OWNED_LOCK_TOKEN_CHANGED')
                os.close(fd);fd = None;H.need(H.stamp(lane.lstat()) == lane_identity, 'OWNED_LOCK_PATH_CHANGED')
                lane.unlink();result['owned_lock_removed'] = True
            except BaseException as error:result['lock_error_type'] = type(error).__name__
            finally:
                if fd is not None:os.close(fd)
        result['owned_lock_retained'] = lane_identity is not None and not result['owned_lock_removed']
        if not (closure and result['parent_environment_unchanged'] and result['head_unchanged']
                and result['all_admitted_inputs_preserved'] and result['current_functional_domain_preserved']
                and result['owned_lock_removed']):result['status'] = 'FAIL'
        if stage_owned:
            H.json_new(stage/'PRIVATE_COORDINATOR_RESULT.json', result)
            public = {key: value for key, value in result.items() if key not in ('jobs', 'cases', 'preservation_failures')}
            public['private_job_count'] = len(result['jobs']);public['preservation_failure_count'] = len(result['preservation_failures'])
            public['cases'] = [{key: value for key, value in row.items() if key in ('name', 'status', 'checks', 'graphical')} for row in result['cases']]
            H.json_new(stage/'PUBLIC_RESULT.json', public)
            print(json.dumps({'status': result['status'], 'result': str(stage/'PUBLIC_RESULT.json')}), flush=True)
    return 0 if result['status'] == 'CAPTURED_FOR_PRIVATE_REVIEW' and primary is None else 1

if __name__ == '__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'PREFLIGHT_REFUSED', 'error_type': type(error).__name__, 'detail': str(error)}), flush=True)
        raise SystemExit(2)
