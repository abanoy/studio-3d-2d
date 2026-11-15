"""Windows-only single CPU child owner; no Godot or native converter is invoked.

The trusted completion stays in the retained parent's pipe memory until native
exit0, EOF, identity, generation and cleanup checks pass. No PID reopen/kill API.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time

import wind_helper_preview as protocol
import wind_preview_worker as worker

MAX_STDOUT = 16 * 1024
MAX_STDERR = 256 * 1024


class NativeJob:
    def __init__(self, main_root):
        if os.name != 'nt': raise RuntimeError('Owned CPU preview requires Windows; no fallback')
        if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 13):
            raise RuntimeError('This candidate is tested against the approved CPython3.13 handle API')
        # Reuse the exact existing native Job layout; importing this module does
        # not call its graphical/private-desktop launcher.
        path = Path(main_root) / 'tools/private_desktop.py'
        spec = importlib.util.spec_from_file_location('wind_owned_job_layout', path)
        existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        def api(name, result, *args):
            value = getattr(self.kernel, name); value.restype = result; value.argtypes = args; return value
        self.create = api('CreateJobObjectW', W.HANDLE, C.c_void_p, W.LPCWSTR)
        self.configure = api('SetInformationJobObject', W.BOOL, W.HANDLE, C.c_int, C.c_void_p, W.DWORD)
        self.assign_native = api('AssignProcessToJobObject', W.BOOL, W.HANDLE, W.HANDLE)
        self.terminate_native = api('TerminateJobObject', W.BOOL, W.HANDLE, W.UINT)
        self.close_native = api('CloseHandle', W.BOOL, W.HANDLE)
        self.process_id = api('GetProcessId', W.DWORD, W.HANDLE)
        self.times = api('GetProcessTimes', W.BOOL, W.HANDLE, *([C.POINTER(W.FILETIME)] * 4))
        self.wait_native = api('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        self.handle = self.create(None, None); self.assigned = False; self.closed = False
        if not self.handle: raise OSError(C.get_last_error(), 'Create owned CPU Job')
        try:
            limits = existing.ExtendedLimits()
            # Kill on last Job handle close, exactly one process,1GiB Job memory.
            limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x8 | 0x200
            limits.BasicLimitInformation.ActiveProcessLimit = 1
            limits.JobMemoryLimit = 1024 * 1024 * 1024
            if not self.configure(self.handle, 9, C.byref(limits), C.sizeof(limits)):
                raise OSError(C.get_last_error(), 'Configure owned CPU Job')
        except BaseException:
            self.close(); raise

    def identity(self, process):
        handle = process._handle  # CPython3.13 retains this exact created process.
        pid = self.process_id(handle); times = [W.FILETIME() for _ in range(4)]
        if not pid or not self.times(handle, *(C.byref(t) for t in times)):
            raise OSError(C.get_last_error(), 'Read exact owned child identity')
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        if not created: raise RuntimeError('Owned child creation identity is empty')
        return {'pid': int(pid), 'created_100ns': str(created)}

    def assign(self, process):
        if not self.assign_native(self.handle, process._handle):
            raise OSError(C.get_last_error(), 'Assign gated CPU child to its Job')
        self.assigned = True

    def state(self, process):
        value = self.wait_native(process._handle, 0)
        if value not in (0, 258): raise OSError(C.get_last_error(), 'Cannot observe exact owned child')
        return value

    def terminate(self):
        if not self.closed and self.assigned and not self.terminate_native(self.handle, 0xC000013A):
            raise OSError(C.get_last_error(), 'Stop only the owned CPU Job')

    def close(self):
        if self.closed: return
        if self.handle and not self.close_native(self.handle):
            raise OSError(C.get_last_error(), 'Close owned CPU Job')
        self.closed = True; self.handle = None


class CappedReader:
    def __init__(self, pipe, limit):
        self.pipe = pipe; self.limit = limit; self.data = bytearray(); self.total = 0
        self.overflow = False; self.eof = False; self.error = None
        self.thread = threading.Thread(target=self.read, daemon=True); self.thread.start()

    def read(self):
        try:
            while True:
                block = self.pipe.read1(4096)
                if not block: self.eof = True; return
                self.total += len(block)
                self.data.extend(block[:max(0, self.limit - len(self.data))])
                self.overflow = self.total > self.limit
                # Continue draining/discarding after cap; do not deadlock the
                # child while the owner observes the flag and stops its Job.
        except BaseException as error: self.error = str(error)

    def join(self):
        self.thread.join(2)
        if self.thread.is_alive() or not self.eof or self.error:
            raise RuntimeError('Owned completion pipes did not reach clean EOF')


def decode_completion(raw, owner, sources, token, python_identity):
    if len(raw) > MAX_STDOUT or not raw.startswith(worker.PREFIX) or not raw.endswith(b'\n') or raw.count(b'\n') != 1:
        raise ValueError('Expected exactly one bounded completion frame and EOF')
    packet = json.loads(raw[len(worker.PREFIX):-1].decode('ascii'))
    if packet.get('format') != worker.COMPLETE or packet.get('owner') != owner or packet.get('source_sha256') != sources:
        raise ValueError('Completion has a foreign child incarnation/source identity')
    executable = packet.get('python', {})
    if not isinstance(executable, dict) or os.path.normcase(str(executable.get('path', ''))) != os.path.normcase(python_identity['path']) or executable.get('sha256') != python_identity['sha256']:
        raise ValueError('Completion has a foreign Python executable fingerprint')
    completion = packet.get('completion')
    if not isinstance(completion, dict) or type(completion.get('generation')) is not int or completion['generation'] != token['generation'] or completion.get('nonce') != token['nonce'] or completion.get('request_file_sha256') != token['request_sha256']:
        raise ValueError('Completion belongs to a late/different draft generation')
    return completion


class OwnedPreviewJob:
    def __init__(self, lease, main_root, python=sys.executable, timeout=120, approved_python_sha256=None, work_root=None):
        for module, name in ((protocol, 'wind_helper_preview.py'), (worker, 'wind_preview_worker.py')):
            if Path(module.__file__).resolve() != Path(__file__).with_name(name).resolve():
                raise ValueError('Adapter imported a different ' + name)
        self.lease = lease; self.main_root = Path(main_root).absolute(); self.python = Path(python).resolve(strict=True)
        if not self.python.is_file() or self.python.suffix.lower() != '.exe': raise ValueError('Select the approved absolute Python executable')
        if approved_python_sha256 is None and self.python != Path(sys.executable).resolve(strict=True):
            raise ValueError('A different Python executable needs its explicit approved fingerprint')
        self.python_identity = {'path': str(self.python), 'sha256': approved_python_sha256 or worker.file_sha(self.python)}
        if worker.file_sha(self.python) != self.python_identity['sha256']: raise ValueError('Python executable differs from approved fingerprint')
        if not (self.main_root / 'project.godot').is_file(): raise ValueError('Actual main source root required')
        if not 0 < timeout <= 120: raise ValueError('Worker timeout must be within120seconds')
        if work_root is None or not Path(work_root).is_absolute(): raise ValueError('Explicit absolute preview work root required')
        self.work_root = Path(work_root).absolute()
        protocol.owned(lease.owned_root, self.work_root)
        self.timeout = timeout; self.lock = threading.RLock(); self.process = None; self.native = None
        self.token = None; self.owner = None; self.sources = {}; self.readers = []; self.started = 0
        self.state = 'idle'; self.error = ''; self.receipt = None; self.job_closed = False; self.handle_closed = False
        self.exit_code = None

    def command(self, job):
        return [str(self.python), '-I', '-B', '-u', str(Path(worker.__file__).resolve()),
                '--main-root', str(self.main_root), '--work-root', str(self.work_root), '--owned-root', str(self.lease.owned_root), '--job', str(job)]

    def _same_pending(self):
        return self.lease.pending is not None and self.token is not None and self.lease.pending['generation'] == self.token['generation'] and self.lease.pending['nonce'] == self.token['nonce']

    def _send_start(self):
        gate = {'format': worker.START, 'owner': self.owner, 'generation': self.token['generation'],
                'nonce': self.token['nonce'], 'request_file_sha256': self.token['request_sha256'],
                'source_sha256': self.sources, 'python': self.python_identity}
        raw = protocol.encoded(gate)
        if len(raw) > worker.MAX_START: raise ValueError('Owned start gate exceeds budget')
        self.process.stdin.write(raw); self.process.stdin.flush(); self.process.stdin.close()

    def start(self, token):
        with self.lock:
            if self.process is not None or self.native is not None: raise RuntimeError('One owned CPU worker at a time; finish cleanup first')
            if self.lease.pending != token or self.lease.phase != 'building': raise ValueError('Only the current live draft ticket may start')
            self.token = dict(token); self.receipt = None; self.error = ''; self.state = 'starting'
            self.job_closed = False; self.handle_closed = False; self.readers = []
            self.exit_code = None
            try:
                paths = worker.code_paths(self.main_root)
                self.sources = {name: worker.file_sha(path) for name, path in paths.items()}
                if worker.file_sha(self.python) != self.python_identity['sha256']: raise ValueError('Approved Python changed before launch')
                raw = protocol.regular(token['job'] / 'request.json', protocol.MAX_REQUEST).read_bytes()
                if protocol.digest(raw) != token['request_sha256']: raise ValueError('Draft request changed before launch')
                self.context = protocol.validate_envelope(json.loads(raw))['context']
                self.native = NativeJob(self.main_root)
                command = self.command(token['job'])
                self.process = subprocess.Popen(command, cwd=token['job'],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                self.owner = self.native.identity(self.process)
                if self.owner['pid'] != self.process.pid: raise RuntimeError('Created child identity differs')
                self.readers = [CappedReader(self.process.stdout, MAX_STDOUT), CappedReader(self.process.stderr, MAX_STDERR)]
                self.native.assign(self.process)
                self.started = time.monotonic(); self.state = 'running'; self._send_start()
                protocol.publish(token['job'] / 'owned-launch.json', {'format': 'has_wind_owned_launch_1',
                    'owner': self.ownership_token(), 'command': command,
                    'source_sha256': self.sources, 'python': self.python_identity,
                    'job_assigned': True, 'kill_on_close': True, 'active_process_limit': 1,
                    'no_window': True, 'request_file_sha256': token['request_sha256']}, 32*1024)
                return self.ownership_token()
            except BaseException:
                self.state = 'failed'; self.error = 'Owned worker launch failed'
                if self._same_pending(): self.lease.invalidate(self.error)
                self._dispose(stop=True); self._save_outcome(); raise

    def ownership_token(self):
        with self.lock:
            return {**(self.owner or {}), 'generation': self.token['generation'], 'nonce': self.token['nonce']}

    def _dispose(self, stop=False):
        errors = []
        if self.process is not None and self.process.stdin and not self.process.stdin.closed:
            try: self.process.stdin.close()
            except BaseException as error: errors.append(str(error))
        if self.native:
            try:
                if stop: self.native.terminate()
            except BaseException as error: errors.append(str(error))
            try: self.native.close(); self.job_closed = self.native.closed
            except BaseException as error: errors.append(str(error))
        if self.process is not None:
            try:
                # Before assignment no build could start; EOF is the cooperative
                # exit. Retain the exact Popen handle for a bounded fallback kill.
                try: self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill(); self.process.wait(timeout=3)
                for reader in self.readers: reader.join()
                self.exit_code = self.process.returncode
            except BaseException as error: errors.append(str(error))
            try:
                for pipe in (self.process.stdout, self.process.stderr):
                    if pipe: pipe.close()
                if self.process.returncode is None: raise RuntimeError('Cannot close a live owned process handle')
                self.process._handle.Close(); self.handle_closed = True
            except BaseException as error: errors.append(str(error))
        if self.process is not None and self.handle_closed: self.process = None
        if self.process is None and self.native is not None and self.native.closed: self.native = None
        if errors: raise RuntimeError('; '.join(errors))

    def _save_outcome(self):
        if self.token is None: return
        job = self.token['job']
        for index, name in enumerate(('owned-stdout.log', 'owned-stderr.log')):
            if index < len(self.readers) and not (job / name).exists():
                with (job / name).open('xb') as stream: stream.write(self.readers[index].data)
        name = 'owned-outcome.json' if not (job / 'owned-outcome.json').exists() else 'owned-cleanup-after-failure.json'
        if not (job / name).exists():
            protocol.publish(job / name, {'format': 'has_wind_owned_outcome_1', 'state': self.state,
                'owner': self.ownership_token(), 'exit': self.exit_code, 'error': self.error,
                'job_closed': self.job_closed, 'process_handle_closed': self.handle_closed,
                'pipe_eof': [reader.eof for reader in self.readers],
                'pipe_bytes': [reader.total for reader in self.readers],
                'pipe_overflow': [reader.overflow for reader in self.readers],
                'source_sha256': self.sources, 'python': self.python_identity,
                'render_admitted': False}, 32*1024)

    def cancel(self, expected_owner=None, reason='cancelled'):
        with self.lock:
            if self.process is None: return False
            if expected_owner is not None and expected_owner != self.ownership_token():
                raise ValueError('Stale cancellation token cannot affect the current worker')
            if self.native.identity(self.process) != self.owner:
                raise RuntimeError('Owned process handle identity changed; no PID fallback')
            self.state = 'cancelled'; self.error = reason
            if self._same_pending(): self.lease.invalidate(reason)
            self._dispose(stop=True)
            self._save_outcome()
            return True

    def poll(self, current_context):
        with self.lock:
            if self.process is None: return {'state': self.state, 'error': self.error, 'receipt': self.receipt}
            try:
                if not self._same_pending(): self.cancel(reason='draft generation changed'); return self.poll(current_context)
                if self.context != current_context: self.cancel(reason='original context changed'); return self.poll(current_context)
                if time.monotonic() - self.started > self.timeout: self.cancel(reason='owned worker timed out'); return self.poll(current_context)
                if any(reader.overflow or reader.error for reader in self.readers):
                    self.cancel(reason='owned completion pipe limit/error'); return self.poll(current_context)
                if self.native.identity(self.process) != self.owner: raise RuntimeError('Owned child incarnation changed')
                state = self.native.state(self.process); code = self.process.poll()
                if state == 258:
                    if code is None: return {'state': 'running', 'owner': self.ownership_token()}
                    # The process may exit between the two native observations.
                    if self.native.state(self.process) != 0: raise RuntimeError('Owned child exit observations disagree')
                if code is None: raise RuntimeError('Owned native exit lacks an exit code')
                for reader in self.readers: reader.join()
                raw = bytes(self.readers[0].data); stderr = bytes(self.readers[1].data)
                if any(reader.overflow or reader.error for reader in self.readers): raise RuntimeError('Owned completion pipe budget/error')
                # Preserve bounded diagnostics, but never use a mutable file as
                # the expected completion token. Success requires native exit0.
                for name, data in (('owned-stdout.log', raw), ('owned-stderr.log', stderr)):
                    with (self.token['job'] / name).open('xb') as stream: stream.write(data)
                if code != 0: raise RuntimeError('Owned CPU worker exited ' + str(code))
                if stderr: raise RuntimeError('Owned worker produced unexpected diagnostics')
                completion = decode_completion(raw, self.owner, self.sources, self.token, self.python_identity)
                if {name: worker.file_sha(path) for name, path in worker.code_paths(self.main_root).items()} != self.sources:
                    raise ValueError('Launch-bound worker/protocol source changed before admission')
                if worker.file_sha(self.python) != self.python_identity['sha256']:
                    raise ValueError('Approved Python fingerprint changed before admission')
                self._dispose(stop=False)
                if not self.job_closed or not self.handle_closed: raise RuntimeError('Owned worker cleanup did not complete')
                self.receipt = self.lease.accept(current_context, completion); self.state = 'prepared_hidden'
                self._save_outcome()
                return {'state': self.state, 'receipt': self.receipt, 'owner': self.ownership_token(),
                        'job_closed': self.job_closed, 'process_handle_closed': self.handle_closed}
            except BaseException as error:
                self.state = 'failed'; self.error = type(error).__name__ + ': ' + str(error)
                if self._same_pending(): self.lease.invalidate(self.error)
                if self.process is not None:
                    try: self._dispose(stop=True)
                    except BaseException as cleanup: self.error += '; cleanup: ' + str(cleanup)
                self._save_outcome()
                return {'state': self.state, 'error': self.error, 'receipt': None}

    def close(self):
        with self.lock:
            if self.process is not None:
                try: self.cancel(reason='owner closed')
                except BaseException:
                    self.state = 'failed'
                    if self._same_pending(): self.lease.invalidate('owner cleanup failed')
                    # This Job is the one created/assigned by this owner; close
                    # it even if a query failed. No process is reopened by PID.
                    self._dispose(stop=True)
                    raise
            elif self.native is not None:
                self.native.close(); self.job_closed = self.native.closed; self.native = None
                self._save_outcome()
