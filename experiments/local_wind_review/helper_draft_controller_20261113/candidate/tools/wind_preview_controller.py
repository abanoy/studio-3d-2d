"""Bounded preview-only CPU controller; not a Godot/UI integration."""
from pathlib import Path
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
import queue
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I deliberately omits the script directory.
P = A = WORKER = None

COMMAND = 'has_wind_preview_controller_command_1'
EVENT = 'has_wind_preview_controller_event_1'
MAX_COMMAND = 1024 * 1024
MAX_EVENT = 16 * 1024
MAX_COMMANDS = 128


def load(main_root):
    global P, A, WORKER
    main_root = Path(main_root).absolute()
    if not (main_root/'project.godot').is_file(): raise ValueError('Actual main root required')
    sys.path.insert(1, str(main_root/'tools'))
    import wind_helper_preview as protocol
    import wind_preview_owned as adapter
    import wind_preview_worker as worker
    for module, name in ((protocol, 'wind_helper_preview.py'), (adapter, 'wind_preview_owned.py'), (worker, 'wind_preview_worker.py')):
        if Path(module.__file__).resolve() != HERE/name: raise ValueError('Foreign controller dependency import')
    P, A, WORKER = protocol, adapter, worker


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def constant(value): raise ValueError('Nonfinite JSON constant')
    return json.loads(raw.decode('ascii'), object_pairs_hook=pairs, parse_constant=constant)


class ParentLease:
    """Retains a query/synchronize handle; never terminates a host by PID."""
    def __init__(self, pid, created):
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        def api(name, result, *args):
            method = getattr(self.kernel, name); method.restype = result; method.argtypes = args; return method
        self.open = api('OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
        self.getpid = api('GetProcessId', W.DWORD, W.HANDLE)
        self.times = api('GetProcessTimes', W.BOOL, W.HANDLE, *([C.POINTER(W.FILETIME)] * 4))
        self.wait = api('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        self.close_native = api('CloseHandle', W.BOOL, W.HANDLE)
        self.handle = None; self.closed = False
        if type(pid) is not int or pid <= 0 or pid == os.getpid() or not created.isdigit() or int(created) <= 0:
            raise ValueError('Explicit host PID and creation identity required')
        self.expected = {'pid': pid, 'created_100ns': created}
        self.handle = self.open(0x100000 | 0x1000, False, pid)
        if not self.handle: raise OSError(C.get_last_error(), 'Open explicit host lifetime lease')
        try:
            times = [W.FILETIME() for _ in range(4)]
            if not self.times(self.handle, *(C.byref(t) for t in times)):
                raise OSError(C.get_last_error(), 'Query retained host creation identity')
            actual = {'pid': int(self.getpid(self.handle)), 'created_100ns': str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)}
            if actual != self.expected: raise ValueError('Explicit host incarnation differs')
            if not self.alive(): raise ValueError('Explicit host already ended')
        except BaseException:
            self.close(); raise

    def alive(self):
        value = self.wait(self.handle, 0)
        if value not in (0, 258): raise OSError(C.get_last_error(), 'Host lifetime observation failed')
        return value == 258

    def close(self):
        if self.closed: return
        if self.handle and not self.close_native(self.handle): raise OSError(C.get_last_error(), 'Close retained host handle')
        self.closed = True; self.handle = None


class Transport:
    """Bounded I/O threads cannot block the ownership service loop."""
    def __init__(self):
        self.inputs = queue.Queue(4); self.outputs = queue.Queue(4)
        self.eof = False; self.error = ''; self.writer_busy = False
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.writer = threading.Thread(target=self.write, daemon=True)
        self.reader.start(); self.writer.start()

    def read(self):
        pending = bytearray()
        try:
            while True:
                block = os.read(0, 4096)
                if not block:
                    if pending: self.error = 'Unterminated command frame'
                    self.eof = True; return
                pending.extend(block)
                while b'\n' in pending:
                    index = pending.index(10)
                    if index + 1 > MAX_COMMAND: raise ValueError('Command frame exceeds1MiB')
                    frame = bytes(pending[:index]); del pending[:index+1]
                    self.inputs.put_nowait(frame)
                if len(pending) >= MAX_COMMAND: raise ValueError('Command frame exceeds1MiB')
        except BaseException as error: self.error = type(error).__name__ + ': ' + str(error)[:256]

    def write(self):
        try:
            while True:
                raw = self.outputs.get()
                if raw is None: self.outputs.task_done(); return
                self.writer_busy = True
                while raw:
                    count = os.write(1, raw)
                    if count <= 0: raise RuntimeError('Controller output closed')
                    raw = raw[count:]
                self.writer_busy = False; self.outputs.task_done()
        except BaseException as error: self.error = type(error).__name__ + ': ' + str(error)[:256]

    def emit(self, value):
        raw = P.encoded(value)
        if len(raw) > MAX_EVENT: raise ValueError('Controller event exceeds16KiB')
        self.outputs.put_nowait(raw)

    def finish(self):
        # Child ownership has already been closed; a host that stopped draining
        # output cannot keep that child alive. Daemon writer uses os.write only.
        until = time.monotonic() + 1
        while self.outputs.unfinished_tasks and not self.error and time.monotonic() < until: time.sleep(.01)
        try: self.outputs.put_nowait(None)
        except queue.Full: pass


class Controller:
    def __init__(self, options, parent, transport):
        self.options = options; self.parent = parent; self.transport = transport
        self.session = options.session; self.seq = 0; self.count = 0; self.records = []
        self.lease = P.DraftLease(options.owned_root)
        self.adapter = A.OwnedPreviewJob(self.lease, options.main_root, approved_python_sha256=options.python_sha256)
        self.context = None; self.completion = None; self.reason = ''; self.exit_code = 0
        self.closed = False; self.prepared_exposed = False
        self.fingerprints = {name: WORKER.file_sha(path) for name, path in WORKER.code_paths(options.main_root).items()}
        self.fingerprints['controller'] = WORKER.file_sha(Path(__file__))
        send_start = self.adapter._send_start
        def checked_start_gate():
            self.require_live_host_transport()
            send_start()
        self.adapter._send_start = checked_start_gate

    def ticket(self):
        return {'generation': self.lease.generation, 'nonce': self.lease.pending['nonce'] if self.lease.pending else None}

    def event(self, kind, **values):
        return {'format': EVENT, 'session': self.session, 'seq': self.seq, 'event': kind,
                'ticket': self.ticket(), 'phase': self.lease.phase, **values}

    def emit(self, kind, **values): self.transport.emit(self.event(kind, **values))

    def check_ticket(self, message):
        expected = self.ticket()
        if type(message.get('generation')) is not int or message['generation'] != expected['generation'] or message.get('nonce') != expected['nonce']:
            raise ValueError('Stale draft generation/nonce; current ticket unchanged')

    def require_live_host_transport(self):
        reason = 'host process ended' if not self.parent.alive() else 'host input EOF' if self.transport.eof else 'transport error: '+self.transport.error if self.transport.error else ''
        if reason:
            self.reason = reason; self.closed = True
            self.stop(reason)
            raise RuntimeError(reason)
        if WORKER.file_sha(Path(__file__)) != self.fingerprints['controller']:
            self.stop('controller source changed')
            raise RuntimeError('Controller source fingerprint changed')

    def stop(self, reason):
        # Invalidate before disposal, including already prepared tickets. No
        # callback/event from the prior generation may become visible afterward.
        if self.lease.phase != 'stopped' or self.lease.pending is not None or self.context is not None:
            self.lease.invalidate(reason)
        self.completion = None; self.context = None
        self.adapter.close()
        if self.adapter.process is not None or self.adapter.native is not None:
            raise RuntimeError('Controller could not close owned worker handles')

    def dispatch(self, message):
        if not isinstance(message, dict) or message.get('format') != COMMAND or message.get('session') != self.session:
            raise ValueError('Foreign controller session or format')
        seq = message.get('seq')
        if type(seq) is not int or seq != self.seq + 1 or not 1 <= seq <= MAX_COMMANDS:
            raise ValueError('Replay/out-of-order command sequence')
        self.seq = seq; self.count += 1
        op = message.get('op'); self.check_ticket(message)
        if op == 'start':
            if self.adapter.process is not None or self.lease.phase == 'building': raise ValueError('Cancel the current draft before starting another')
            source = message.get('source'); items = message.get('items'); context = message.get('context'); mode = message.get('mode', 'focused-single')
            # Validate without creating a directory. Only a valid start may
            # establish a lease or launch/prepare a worker.
            P.make_envelope(source, items, context, self.lease.generation + 1, mode)
            self.require_live_host_transport()
            token = self.lease.begin(source, items, context, mode)
            self.context = context.copy(); self.completion = None
            self.require_live_host_transport()
            owner = self.adapter.start(token)
            self.require_live_host_transport()
            self.emit('started', owner=owner, job=str(token['job']))
        elif op == 'poll':
            if self.lease.pending is None: raise ValueError('No started draft to poll')
            context = message.get('context')
            if context != self.context:
                self.stop('original context changed'); self.emit('invalidated', reason='original context changed'); return
            if self.lease.phase == 'prepared_hidden':
                # Adapter caches success after exit; refresh the actual receipt
                # and original source here before exposing another ready event.
                try:
                    P.check_receipt(self.lease.pending['job'], self.lease.owned_root,
                        self.lease.pending['request_sha256'], context, self.completion['receipt_sha256'])
                except Exception:
                    self.stop('prepared source/receipt changed'); raise
                self.require_live_host_transport()
                self.prepared_exposed = True; self.emit('prepared', job=str(self.lease.pending['job']), completion=self.completion); return
            result = self.adapter.poll(context)
            if result['state'] == 'prepared_hidden':
                self.completion = A.decode_completion(bytes(self.adapter.readers[0].data), self.adapter.owner,
                    self.adapter.sources, self.adapter.token, self.adapter.python_identity)
                self.require_live_host_transport()
                self.prepared_exposed = True
                self.emit('prepared', job=str(self.lease.pending['job']), completion=self.completion,
                    owner=self.adapter.ownership_token(), job_closed=self.adapter.job_closed,
                    process_handle_closed=self.adapter.handle_closed)
            elif result['state'] == 'running': self.emit('running', owner=self.adapter.ownership_token())
            else:
                self.stop('worker refused or stopped')
                self.emit('invalidated', reason=result.get('error', 'worker refused or stopped'))
        elif op == 'cancel':
            if self.lease.pending is None: raise ValueError('No started draft to cancel')
            self.stop('host cancelled'); self.emit('cancelled')
        elif op == 'close':
            self.stop('host closed'); self.reason = 'host closed'; self.closed = True; self.emit('closed')
        else: raise ValueError('Unsupported preview controller operation')

    def run(self):
        last = time.monotonic()
        self.emit('ready', controller=WORKER.self_owner(), host=self.parent.expected,
            source_sha256=self.fingerprints, python=self.adapter.python_identity)
        try:
            while not self.closed:
                if not self.parent.alive(): self.reason = 'host process ended'; break
                if self.transport.error: self.reason = 'transport error: ' + self.transport.error; self.exit_code = 2; break
                if self.transport.eof: self.reason = 'host input EOF'; break
                if time.monotonic() - last > self.options.idle_timeout: self.reason = 'host transport idle timeout'; self.exit_code = 2; break
                if self.adapter.process is not None:
                    if time.monotonic()-self.adapter.started > self.adapter.timeout or any(r.overflow or r.error for r in self.adapter.readers):
                        self.stop('worker timeout or pipe limit'); self.emit('invalidated', reason='worker timeout or pipe limit')
                try: raw = self.transport.inputs.get(timeout=.02)
                except queue.Empty: continue
                last = time.monotonic()
                try:
                    message = strict_json(raw)
                    self.dispatch(message)
                    self.records.append({'seq': message.get('seq'), 'op': message.get('op'), 'outcome': 'handled', 'ticket': self.ticket()})
                except Exception as error:
                    self.records.append({'seq': self.seq, 'outcome': 'refused', 'error': type(error).__name__+': '+str(error)[:256], 'ticket': self.ticket()})
                    self.emit('refused', reason=type(error).__name__+': '+str(error)[:256])
                if len(self.records) >= MAX_COMMANDS: self.reason = 'controller command budget ended'; self.exit_code = 2; break
        except BaseException as error:
            self.reason = type(error).__name__ + ': ' + str(error)[:256]; self.exit_code = 2
        finally:
            try: self.stop(self.reason or 'controller ended')
            except BaseException as error: self.reason += '; cleanup: '+str(error)[:256]; self.exit_code = 2
            try: self.parent.close()
            except BaseException as error: self.reason += '; host handle: '+str(error)[:256]; self.exit_code = 2
            outcome = {'format': 'has_wind_preview_controller_outcome_1', 'controller': WORKER.self_owner(),
                'host': self.parent.expected, 'host_handle_closed': self.parent.closed, 'session': self.session,
                'reason': self.reason, 'exit': self.exit_code, 'ticket': self.ticket(), 'phase': self.lease.phase,
                'worker_owner': self.adapter.ownership_token() if self.adapter.token else None,
                'job_closed': self.adapter.job_closed, 'process_handle_closed': self.adapter.handle_closed,
                'worker_started': self.adapter.token is not None, 'prepared_exposed': self.prepared_exposed,
                'source_sha256': self.fingerprints, 'python': self.adapter.python_identity, 'commands': self.records,
                'godot_started': False, 'renderer_acceptance': False}
            try: P.publish(self.options.owned_root / 'controller-outcome.json', outcome, 128*1024)
            except BaseException: self.exit_code = 2
            self.transport.finish()
        return self.exit_code


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--main-root', type=Path, required=True); parser.add_argument('--owned-root', type=Path, required=True)
    parser.add_argument('--parent-pid', type=int, required=True); parser.add_argument('--parent-created-100ns', required=True)
    parser.add_argument('--session', required=True); parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--python-sha256', required=True); parser.add_argument('--idle-timeout', type=float, default=30)
    options = parser.parse_args(argv); parent = None
    try:
        if os.name != 'nt': raise ValueError('Windows controller candidate only')
        load(options.main_root)
        if WORKER.file_sha(Path(__file__)) != options.controller_sha256: raise ValueError('Controller source fingerprint differs')
        if WORKER.file_sha(Path(sys.executable)) != options.python_sha256: raise ValueError('Controller Python fingerprint differs')
        if len(options.session) != 32 or any(c not in '0123456789abcdef' for c in options.session): raise ValueError('Bounded session nonce required')
        if not 0 < options.idle_timeout <= 120: raise ValueError('Bounded host idle timeout required')
        options.main_root = options.main_root.absolute(); options.owned_root = options.owned_root.absolute()
        P.owned(options.owned_root, options.main_root/'output')
        options.owned_root.mkdir(parents=True, exist_ok=False)
        parent = ParentLease(options.parent_pid, options.parent_created_100ns)
        controller = Controller(options, parent, Transport())
        return controller.run()
    except BaseException as error:
        if parent is not None: parent.close()
        # Startup failures occur before the ownership service starts. Keep this
        # diagnostic bounded; no worker can have started here.
        os.write(2, (type(error).__name__+': '+str(error)[:512]+'\n').encode('ascii', 'backslashreplace'))
        return 2


if __name__ == '__main__': raise SystemExit(main())
