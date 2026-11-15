"""One gated CPU preview child; stdout is a single completion frame, not a file."""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
import stat
import sys

PREFIX = b'WIND_HELPER_COMPLETE '
START = 'has_wind_owned_start_1'
COMPLETE = 'has_wind_owned_completion_1'
MAX_START = 4096


def file_sha(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists():
            item = part.lstat()
            if stat.S_ISLNK(item.st_mode) or getattr(item, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Worker refuses reparse code/job paths')
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def code_paths(main_root):
    here = Path(__file__).resolve().parent
    return {'worker': here / 'wind_preview_worker.py', 'protocol': here / 'wind_helper_preview.py',
            'adapter': here / 'wind_preview_owned.py', 'native_job_layout': main_root / 'tools/private_desktop.py',
            'helpers': main_root / 'tools/secondary_helpers.py', 'batch': main_root / 'tools/secondary_helpers_batch.py'}


def self_owner():
    if os.name != 'nt': raise RuntimeError('This bounded worker adapter requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.GetProcessTimes.argtypes = [W.HANDLE, *([ctypes.POINTER(W.FILETIME)] * 4)]
    kernel.GetProcessTimes.restype = W.BOOL
    times = [W.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(kernel.GetCurrentProcess(), *(ctypes.byref(t) for t in times)):
        raise OSError(ctypes.get_last_error(), 'Read worker creation identity')
    return {'pid': os.getpid(), 'created_100ns': str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)}


def emit(packet):
    raw = PREFIX + json.dumps(packet, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii') + b'\n'
    if len(raw) > 16 * 1024: raise ValueError('Completion frame exceeds16KiB')
    sys.stdout.buffer.write(raw); sys.stdout.buffer.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument('--main-root', type=Path, required=True)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--owned-root', type=Path, required=True); parser.add_argument('--job', type=Path, required=True)
    options = parser.parse_args(argv)
    try:
        # No helper import or build happens until the parent assigns its Job and
        # sends this gate. Parent death before assignment closes stdin -> EOF.
        raw = sys.stdin.buffer.readline(MAX_START + 1)
        if not raw.endswith(b'\n') or len(raw) > MAX_START: raise ValueError('Missing/bounded owned start gate')
        gate = json.loads(raw)
        if gate.get('format') != START: raise ValueError('Wrong owned start gate')
        main_root = options.main_root.absolute()
        if not (main_root / 'project.godot').is_file(): raise ValueError('Actual main source root is required')
        if not options.work_root.is_absolute(): raise ValueError('Explicit absolute preview work root required')
        work_root = options.work_root.absolute(); owned_root = options.owned_root.absolute(); job = options.job.absolute()
        if owned_root == work_root or not owned_root.resolve().is_relative_to(work_root.resolve()) or job == owned_root or not job.resolve().is_relative_to(owned_root.resolve()):
            raise ValueError('Worker job must stay in its explicit owned output family')
        paths = code_paths(main_root)
        actual = {name: file_sha(path) for name, path in paths.items()}
        if gate.get('source_sha256') != actual: raise ValueError('Worker code differs from launch-bound source')
        executable = Path(sys.executable).resolve(strict=True)
        python_identity = {'path': str(executable), 'sha256': file_sha(executable)}
        approved = gate.get('python', {})
        if os.path.normcase(str(approved.get('path', ''))) != os.path.normcase(str(executable)) or approved.get('sha256') != python_identity['sha256']:
            raise ValueError('Worker executable differs from approved Python fingerprint')
        request_path = job / 'request.json'
        if request_path.stat().st_size > 1024 * 1024: raise ValueError('Preview request exceeds1MiB')
        request_raw = request_path.read_bytes(); request = json.loads(request_raw)
        if type(gate.get('generation')) is not int or gate.get('request_file_sha256') != hashlib.sha256(request_raw).hexdigest() or gate['generation'] != request.get('generation') or gate.get('nonce') != request.get('nonce'):
            raise ValueError('Owned start gate does not match this exact draft')
        owner = self_owner()
        if gate.get('owner') != owner: raise ValueError('Owned start gate identifies a different child incarnation')
        sys.path.insert(0, str(main_root / 'tools'))
        import importlib.util
        spec = importlib.util.spec_from_file_location('wind_helper_preview', paths['protocol'])
        protocol = importlib.util.module_from_spec(spec); spec.loader.exec_module(protocol)
        protocol.owned(owned_root, work_root); protocol.owned(job, owned_root)
        prepared = protocol.build_candidate(job, owned_root)
        packet = {'format': COMPLETE, 'owner': owner, 'source_sha256': actual, 'python': python_identity,
                  'completion': prepared['completion']}
        emit(packet)
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'error': type(error).__name__ + ': ' + str(error)[:1000]}), file=sys.stderr, flush=True)
        return 2


if __name__ == '__main__': raise SystemExit(main())
