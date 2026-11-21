"""Root-only private distance-face captures. Source only; no rendering diagnosis."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import struct
import sys
import time
import uuid
import zipfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = 'e0879c7df74bc3704902bfdaf4ff74eee40c3aea'
Q_PIN = (21967, 'dfb0cf83cef6dc455d5da9f1c1631f1f0ee053b6e4a646c9045e90e7e9967a3e')
INPUT_PIN = (1711, 'fd9f699b902e6487f9e14a7233cfccd590d0ec1c282b5b49665157b37b1f0bcc')
PROJECT_SHA = 'd304744dea70a05e7176b668bc10b0058b8cb4e6b1ffe5fc9fab05303da60efb'
ASSET_SHA = 'e3e233004f2ce1aed3c2f221f7d92d9218c0de1f133cad88557f8181644e6e8c'
SCRIPT_PIN = (9796, 'dcf31f5511273b077b1fa6da4d53e949acbf7f9dcf07492c1087b1894e906b58')


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_nlink, info.st_mode, getattr(info, 'st_file_attributes', 0))


def source_module(name, path, pin):
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0)&0x400:
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


def protected_project(H, path):
    expected = ROOT/'output/owner-stuff-project-1795238638994/stuff.has'
    H.need(H.safe(path).resolve() == expected.resolve(), 'EXACT_PROTECTED_COPY_PATH_REQUIRED')
    raw = H.read(path, 5194461, PROJECT_SHA)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        H.need(len(archive.infolist()) == 4 and len({row.filename for row in archive.infolist()}) == 4,
               'EXACT_FOUR_SAVED_ENTRIES')
        manifest = archive.getinfo('project.json')
        asset = archive.getinfo('assets/'+ASSET_SHA+'.glb')
        H.need(manifest.file_size == 114480 and asset.file_size == 7734476, 'SEALED_PROJECT_ENTRY_LENGTHS')
        project = H.parse(archive.read(manifest))
        H.need(H.sha(archive.read(asset)) == ASSET_SHA, 'SEALED_EMBEDDED_GLB')
    H.need(type(project.get('video')) is dict and project['video']['width'] == 1920
           and project['video']['height'] == 1080
           and type(project.get('world')) is dict and len(project['world']['objects']) == 1,
           'EXACT_SAVED_FACE_CASE')
    return raw


def capture_contract(H, folder):
    result = H.parse(H.read(folder/'PRIVATE_RESULT.json', limit=4*1024*1024))
    H.need(result.get('format') == 'has_private_close_face_diagnostic_1'
           and result.get('status') == 'CAPTURED_FOR_REVIEW'
           and result.get('diagnosis_proven') is False
           and result.get('fixture_sha256') == PROJECT_SHA
           and result.get('saved_data_unchanged') is True
           and result.get('fixture_sha256_unchanged') is True, 'PRIVATE_CAPTURE_PRESERVATION_CONTRACT')
    rows = result.get('captures')
    H.need(type(rows) is list and len(rows) == 40, 'EXACT_FORTY_PRIVATE_CAPTURES')
    controls = ('baseline', 'near_tenth', 'double_sided', 'opaque_face', 'bounds_margin')
    cells = [(frame, editing, backoff, control) for frame, editing in ((0, False), (43, True))
             for backoff in (0.0, 0.1, 0.3, 1.0) for control in controls]
    names = set()
    images = []
    for row, (frame, editing, backoff, control) in zip(rows, cells, strict=True):
        H.need(type(row) is dict and row.get('frame') == frame
               and row.get('editing_draft_context') is editing
               and row.get('backoff') == backoff and row.get('control') == control
               and row.get('save_error') == 0 and 'error' not in row
               and row.get('camera_fov') == 60 and row.get('camera_far') == 2000
               and row.get('face_material_name') == 'face'
               and row.get('image_dimensions') == [1920, 1080], 'EXACT_CAPTURE_CELL_AND_CAMERA_SEMANTICS')
        expected_near = 0.05000000074505806*(0.1 if control == 'near_tenth' else 1.0)
        # The pinned single-precision Camera3D property stores float32. Compare
        # that exact representation; this does not judge face visibility.
        expected_native_near = struct.unpack('<f', struct.pack('<f', expected_near))[0]
        H.need(type(row.get('camera_near')) in (int, float)
               and row['camera_near'] == expected_native_near, 'CAPTURE_NEAR_BRANCH')
        name = row.get('image')
        H.need(type(name) is str and H.rel(name) == name and '/' not in name and '\\' not in name
               and name.endswith('.png') and name not in names, 'UNIQUE_LOCAL_CAPTURE_NAME')
        names.add(name)
        image = H.read(folder/name, limit=32*1024*1024)
        H.need(len(image) >= 24 and image[:8] == b'\x89PNG\r\n\x1a\n'
               and int.from_bytes(image[16:20], 'big') == 1920
               and int.from_bytes(image[20:24], 'big') == 1080, 'PRIVATE_PNG_DIMENSIONS')
        H.need(type(row.get('image_raw_sha256')) is str
               and re.fullmatch('[0-9a-f]{64}', row['image_raw_sha256']) is not None, 'PRIVATE_IMAGE_HASH_RECORDED')
        images.append({'name': name, 'bytes': len(image), 'sha256': H.sha(image)})
    H.read(folder/'private-model.glb', 7734476, ASSET_SHA)
    return {'capture_count': len(images), 'contexts': 2, 'backoffs': 4, 'controls': 5,
            'dimensions': [1920, 1080], 'private_image_pins': images,
            'diagnosis_proven': False, 'saved_data_unchanged': True,
            'fixture_sha256_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-sha256', required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--protected-project', type=Path, required=True)
    parser.add_argument('--owner-original', type=Path, required=True)
    parser.add_argument('--root-exclusive-lane-confirmed', action='store_true', required=True)
    options = parser.parse_args()
    Q = source_module('_close_face_owned_ui_helpers', HERE/'qualified_ui_host.py', Q_PIN)
    H, _ = Q.load_pinned('_close_face_owned_helpers', HERE/'qualified_helpers.py', *Q.HELPER_PIN)
    H.need(H.ROOT == ROOT and os.name == 'nt' and sys.version_info[:2] == (3, 13)
           and not sys.flags.optimize and options.root_exclusive_lane_confirmed, 'ROOT_WINDOWS313_EXCLUSIVE_LANE')
    H.need(re.fullmatch('[0-9a-f]{40}', options.expected_head) is not None
           and re.fullmatch('[0-9a-f]{64}', options.self_sha256) is not None, 'EXPLICIT_PINS_REQUIRED')
    H.read(Path(__file__), digest=options.self_sha256)
    H.read(HERE/'qualified_ui_host.py', *Q_PIN)
    inputs = H.parse(H.read(HERE/'INPUT_PINS.json', *INPUT_PIN))
    H.need(inputs.get('format') == 'has_private_close_face_host_inputs_1'
           and inputs.get('baseline_revision') == BASE and len(inputs.get('files', [])) == 9,
           'EXACT_FACE_SOURCE_INPUTS')
    for row in inputs['files']:
        H.read(HERE/H.rel(row['path']), row['bytes'], row['sha256'])
    B, _ = Q.load_pinned('_close_face_snapshot_reader', HERE/'qualified_snapshot_reader.py', *Q.READER_PIN)
    H.need(B.ROOT == ROOT, 'SAME_OWNED_ROOT')
    _full, catalogue, proofs = B.validate_full(H.FULL, Q.FULL_REVISION, H.FULL_SHA)
    for path in proofs:
        H.read(path)
    for name in ('source-before.json', 'source-after.json'):
        H.read(H.FULL/name, digest=H.SOURCE_SHA)
    H.need(H.head() == options.expected_head, 'PUBLICATION_HEAD_CHANGED')
    frozen = B.source_blobs(BASE, catalogue)
    H.need(len(frozen) == 1087, 'PINNED_BASE_RUNTIME')
    expected, modified = Q.validate_composite(H, catalogue, frozen)
    name = 'tests/close_face_distance_diagnostic.gd'
    H.need(name not in frozen, 'FACE_SCRIPT_MUST_BE_NEW')
    frozen[name] = H.read(HERE/'diagnostic/close_face_distance_diagnostic.gd', *SCRIPT_PIN)
    H.need(len(frozen) == 1090, 'EXACT_OWNED_FACE_RUNTIME')
    protected = protected_project(H, options.protected_project)
    owner_path = H.safe(options.owner_original)
    expected_owner = ROOT.parent/'HAS-Review-Neon-973039e-native/Studio/stuff.has'
    H.need(owner_path.resolve() == expected_owner.resolve()
           and owner_path.resolve() != options.protected_project.resolve(), 'SEPARATE_OWNER_ORIGINAL_REQUIRED')
    owner_bytes = H.read(owner_path, limit=16*1024*1024)
    # A user resave is allowed. Its current identity is protected, but is never
    # copied into the reproducer or mistaken for the historical d304 fixture.
    owner_pin = {'bytes': len(owner_bytes), 'sha256': H.sha(owner_bytes),
                 'mtime_ns': str(owner_path.lstat().st_mtime_ns)}
    lock = H.parse(H.read(H.LOCK, digest=H.LOCK_SHA))
    runtime = lock['runtime_paths']
    H.need(len(lock['runtime_executables']) == 6, 'SIX_APPROVED_RUNTIME_PINS')
    for path, row in lock['runtime_executables'].items():
        H.read(path, row['bytes'], row['sha256'], limit=1024*1024*1024)
        H.need(Path(path).lstat().st_mtime_ns == row['mtime_ns'], 'RUNTIME_STAMP_CHANGED')
    H.need(Path(sys.executable).resolve() == Path(runtime['python']).resolve(), 'APPROVED_PYTHON')
    stage = ROOT.parent/('has-close-face-captures-'+str(time.time_ns()))
    H.safe(stage, missing=True)
    lane = ROOT/'output/source-close-face-captures.lock'
    fd = None; lane_identity = None; stage_owned = False; primary = None
    token = uuid.uuid4().hex.encode()
    parent_environment = dict(os.environ)
    result = {'format': 'has_private_close_face_owned_qualification_1', 'status': 'FAIL',
              'private_do_not_publish': True, 'baseline_revision': BASE,
              'expected_head': options.expected_head, 'current_functional_sources': 1086,
              'owned_runtime_files': 1090, 'protected_fixture_sha256': PROJECT_SHA,
              'owner_current_pin': owner_pin, 'owner_original_reproduced': False,
              'new_full_claimed': False, 'application_adopted': False,
              'diagnosis_proven': False, 'sourceio_or_converter_requested': False,
              'jobs': [], 'cases': []}
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
        H.new(studio/'override.cfg', ('[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name='+json.dumps('HAS Close Face '+uuid.uuid4().hex)+'\n').encode())
        private_inputs = stage/'PRIVATE_INPUTS'; private_inputs.mkdir()
        fixture = private_inputs/'stuff.has'; H.new(fixture, protected)
        captures = stage/'PRIVATE_CAPTURES'
        H.safe(captures, missing=True)  # The frozen script requires a NEW directory.
        H.json_new(stage/'SOURCE_SNAPSHOT.json', {'format': 'has_close_face_owned_source_snapshot_1',
                   'baseline_revision': BASE, 'publication_head': options.expected_head,
                   'qualified_current_eight': sorted(modified),
                   'files': {name: {'bytes': len(raw), 'sha256': H.sha(raw)} for name, raw in frozen.items()}})
        Q.run_case(H, stage, studio, runtime, result, 'import', None, [], None, 0, graphical=False, timeout=90)
        Q.run_case(H, stage, studio, runtime, result, 'private-captures', 'tests/close_face_distance_diagnostic.gd',
                   [fixture, captures], None, 0, graphical=True, timeout=205)
        result['capture_summary'] = capture_contract(H, captures)
        H.need(len(result['jobs']) == 2 and result['capture_summary']['capture_count'] == 40,
               'TWO_PRIVATE_JOBS_AND_FORTY_CAPTURES')
        result['status'] = 'CAPTURED_FOR_PRIVATE_REVIEW'
    except BaseException as error:
        primary = error
        result['error_type'] = type(error).__name__
        result['error_code'] = str(error) if isinstance(error, H.Refusal) else 'CLOSE_FACE_CAPTURE_EXCEPTION'
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
            result['current_functional_domain_preserved'] = Q.source_domain(H) == set(expected)
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
            public = {key: result[key] for key in ('format', 'status', 'expected_head', 'current_functional_sources',
                'owned_runtime_files', 'protected_fixture_sha256', 'owner_original_reproduced',
                'new_full_claimed', 'application_adopted', 'diagnosis_proven', 'sourceio_or_converter_requested',
                'all_owned_launchers_reaped', 'all_attempted_private_jobs_closed', 'parent_environment_unchanged',
                'head_unchanged', 'all_admitted_inputs_preserved', 'current_functional_domain_preserved',
                'owned_lock_removed', 'owned_lock_retained')}
            public['capture_count'] = result.get('capture_summary', {}).get('capture_count', 0)
            public['private_job_count'] = len(result['jobs'])
            public['error_code'] = result.get('error_code')
            public['error_type'] = result.get('error_type')
            H.json_new(stage/'PUBLIC_RESULT.json', public)
            print(json.dumps({'status': result['status'], 'captures': public['capture_count'],
                              'result': str(stage/'PUBLIC_RESULT.json')}), flush=True)
    return 0 if result['status'] == 'CAPTURED_FOR_PRIVATE_REVIEW' and primary is None else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'PREFLIGHT_REFUSED', 'error_type': type(error).__name__, 'detail': str(error)}), flush=True)
        raise SystemExit(2)
