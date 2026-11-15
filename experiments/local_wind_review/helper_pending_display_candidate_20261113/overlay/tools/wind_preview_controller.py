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
MAX_COMMAND = 2048
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
    def __init__(self, pid, expected_image, expected_sha):
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        def api(name, result, *args):
            method = getattr(self.kernel, name); method.restype = result; method.argtypes = args; return method
        self.open = api('OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
        self.getpid = api('GetProcessId', W.DWORD, W.HANDLE)
        self.times = api('GetProcessTimes', W.BOOL, W.HANDLE, *([C.POINTER(W.FILETIME)] * 4))
        self.wait = api('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        self.close_native = api('CloseHandle', W.BOOL, W.HANDLE)
        self.image_native = api('QueryFullProcessImageNameW', W.BOOL, W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
        self.handle = None; self.closed = False
        if type(pid) is not int or pid <= 0 or pid == os.getpid():
            raise ValueError('Explicit live host PID required')
        image = Path(expected_image)
        if not image.is_absolute() or not image.is_file() or len(expected_sha)!=64 or any(c not in '0123456789abcdef' for c in expected_sha):
            raise ValueError('Approved absolute host image and fingerprint required')
        self.handle = self.open(0x100000 | 0x1000, False, pid)
        if not self.handle: raise OSError(C.get_last_error(), 'Open explicit host lifetime lease')
        try:
            times = [W.FILETIME() for _ in range(4)]
            if not self.times(self.handle, *(C.byref(t) for t in times)):
                raise OSError(C.get_last_error(), 'Query retained host creation identity')
            buffer = C.create_unicode_buffer(32768); size = W.DWORD(len(buffer))
            if not self.image_native(self.handle, 0, buffer, C.byref(size)) or not 0<size.value<len(buffer):
                raise OSError(C.get_last_error(), 'Query retained host image')
            queried = Path(buffer.value).resolve(strict=True)
            if os.path.normcase(str(queried)) != os.path.normcase(str(image.resolve(strict=True))):
                raise ValueError('Retained host image path differs')
            actual_sha = WORKER.file_sha(queried)
            self.expected = {'pid': int(self.getpid(self.handle)), 'created_100ns': str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime),
                'image_path': str(queried), 'image_sha256': actual_sha}
            if self.expected['pid']!=pid or int(self.expected['created_100ns'])<=0 or actual_sha!=expected_sha:
                raise ValueError('Retained host image fingerprint differs')
            if not self.alive(): raise ValueError('Retained host ended during bootstrap')
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
                    if index + 1 > MAX_COMMAND: raise ValueError('Control frame exceeds2048bytes')
                    frame = bytes(pending[:index]); del pending[:index+1]
                    self.inputs.put_nowait(frame)
                if len(pending) >= MAX_COMMAND: raise ValueError('Control frame exceeds2048bytes')
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


class LifetimeWatchdog:
    """On host/pipe loss, force only this controller to exit if service blocks.

    Windows closes this process's non-inherited Job handle on os._exit; the
    watchdog never opens/terminates a PID, and does not perform filesystem I/O.
    """
    def __init__(self, parent, transport, grace):
        self.parent = parent; self.transport = transport; self.grace = grace
        self.stopping = threading.Event(); self.reason = ''; self.loss_at = None
        self.thread = threading.Thread(target=self.run, daemon=True); self.thread.start()

    def run(self):
        while not self.stopping.wait(.02):
            try:
                reason = 'host ended' if not self.parent.alive() else 'input EOF' if self.transport.eof else 'transport error' if self.transport.error else ''
            except BaseException: reason = 'host observation failed'
            if reason and self.loss_at is None: self.reason = reason; self.loss_at = time.monotonic()
            if self.loss_at is not None and time.monotonic()-self.loss_at >= self.grace:
                os._exit(74)  # This controller only. Job/pipe handles close in OS.

    def stop(self):
        self.stopping.set(); self.thread.join(1)
        if self.thread.is_alive(): os._exit(76)


class Controller:
    def __init__(self, options, parent, transport, watchdog):
        self.options = options; self.parent = parent; self.transport = transport
        self.watchdog = watchdog
        self.session = options.session; self.seq = 0; self.count = 0; self.records = []
        self.lease = P.DraftLease(options.owned_root)
        self.adapter = A.OwnedPreviewJob(self.lease, options.main_root, approved_python_sha256=options.python_sha256, work_root=options.work_root)
        self.context = None; self.completion = None; self.reason = ''; self.exit_code = 0
        self.closed = False; self.prepared_exposed = False
        self.submission = None; self.submitted_identity = None
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

    def load_submission(self, reference, generation, nonce):
        if not isinstance(reference,dict) or set(reference)!={'path','sha256','bytes','context_sha256','source','source_sha256'}:
            raise ValueError('Complete bounded submission reference required')
        for name in ('sha256','context_sha256','source_sha256'):
            value=reference[name]
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value): raise ValueError('Invalid submission digest')
        if type(reference['bytes']) is not int or not 0<reference['bytes']<=P.MAX_REQUEST: raise ValueError('Submission bytecount exceeds budget')
        boundary=self.lease.owned_root/'requests';path=P.owned(reference['path'],boundary)
        if path.parent!=boundary:raise ValueError('Submission must be a direct owned request file')
        path=P.regular(path,P.MAX_REQUEST)
        with path.open('rb') as stream:raw=stream.read(P.MAX_REQUEST+1)
        if len(raw)!=reference['bytes'] or P.digest(raw)!=reference['sha256']:raise ValueError('Submission raw bytes changed')
        value=strict_json(raw)
        if not isinstance(value,dict) or value.get('format')!='has_wind_preview_submission_1' or value.get('purpose')!='preview_only' or value.get('session')!=self.session or type(value.get('generation')) is not int or value['generation']!=generation or value.get('nonce')!=nonce:
            raise ValueError('Submission belongs to another session/purpose/ticket')
        context_raw=value.get('context_json')
        if not isinstance(context_raw,str) or len(context_raw)>16384:raise ValueError('Bounded exact context bytes required')
        context_bytes=context_raw.encode('ascii')
        if P.digest(context_bytes)!=reference['context_sha256'] or strict_json(context_bytes)!=value.get('context'):
            raise ValueError('Submission context binding differs')
        source=Path(str(value.get('source','')))
        if not source.is_absolute() or os.path.normcase(str(source))!=os.path.normcase(str(Path(reference['source']))) or value.get('source_sha256')!=reference['source_sha256']:
            raise ValueError('Submission source path/hash binding differs')
        current=P.identity(source)
        if type(value.get('source_bytes')) is not int or current['bytes']!=value['source_bytes'] or current['sha256']!=reference['source_sha256']:
            raise ValueError('Submission source changed')
        return value,current

    def check_submission(self):
        if self.submission is None:raise ValueError('No bound submission')
        value,current=self.load_submission(self.submission,self.submission_generation,self.submission_nonce)
        if current!=self.submitted_identity:raise ValueError('Submission source identity changed')
        return value

    def submission_fields(self):
        return {'submission_sha256':self.submission['sha256'],'context_sha256':self.submission['context_sha256']}

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
        self.submission = None;self.submitted_identity = None
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
            if set(message)!={'format','session','seq','op','generation','nonce','submission'}:raise ValueError('Start accepts only a bound submission reference')
            reference=message.get('submission');value,current=self.load_submission(reference,self.lease.generation,self.ticket()['nonce'])
            source=value.get('source');items=value.get('items');context=value.get('context');mode=value.get('mode','focused-single')
            # Validate without creating a directory. Only a valid start may
            # establish a lease or launch/prepare a worker.
            P.make_envelope(source, items, context, self.lease.generation + 1, mode)
            self.require_live_host_transport()
            token = self.lease.begin(source, items, context, mode)
            self.context = context.copy(); self.completion = None
            self.submission=dict(reference);self.submitted_identity=current
            self.submission_generation=message['generation'];self.submission_nonce=message['nonce']
            self.require_live_host_transport()
            owner = self.adapter.start(token)
            self.require_live_host_transport()
            self.emit('started', owner=owner, job=str(token['job']), request_file_sha256=token['request_sha256'],**self.submission_fields())
        elif op == 'poll':
            if self.lease.pending is None: raise ValueError('No started draft to poll')
            if set(message)!={'format','session','seq','op','generation','nonce','context_sha256'}:raise ValueError('Poll accepts only the current context digest')
            if message.get('context_sha256') != self.submission['context_sha256']:
                self.stop('original context changed'); self.emit('invalidated', reason='original context changed'); return
            context=self.context
            if self.lease.phase == 'prepared_hidden':
                # Adapter caches success after exit; refresh the actual receipt
                # and original source here before exposing another ready event.
                try:
                    self.check_submission()
                    P.check_receipt(self.lease.pending['job'], self.lease.owned_root,
                        self.lease.pending['request_sha256'], context, self.completion['receipt_sha256'])
                except Exception:
                    self.stop('prepared source/receipt changed'); raise
                self.require_live_host_transport()
                self.prepared_exposed = True; self.emit('prepared', job=str(self.lease.pending['job']), completion=self.completion,**self.submission_fields()); return
            result = self.adapter.poll(context)
            if result['state'] == 'prepared_hidden':
                try:self.check_submission()
                except Exception:
                    self.stop('submission changed before preparation');raise
                self.completion = A.decode_completion(bytes(self.adapter.readers[0].data), self.adapter.owner,
                    self.adapter.sources, self.adapter.token, self.adapter.python_identity)
                self.require_live_host_transport()
                self.prepared_exposed = True
                self.emit('prepared', job=str(self.lease.pending['job']), completion=self.completion,
                    owner=self.adapter.ownership_token(), job_closed=self.adapter.job_closed,
                    process_handle_closed=self.adapter.handle_closed,**self.submission_fields())
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
            if self.adapter.process is not None or self.adapter.native is not None:
                os._exit(75)  # Retained own Job closes even if cleanup failed.
            self.watchdog.stop()  # No wait thread may race the next handle close.
            try: self.parent.close()
            except BaseException as error: self.reason += '; host handle: '+str(error)[:256]; self.exit_code = 2
            outcome = {'format': 'has_wind_preview_controller_outcome_1', 'controller': WORKER.self_owner(),
                'host': self.parent.expected, 'host_handle_closed': self.parent.closed, 'session': self.session,
                'reason': self.reason, 'exit': self.exit_code, 'ticket': self.ticket(), 'phase': self.lease.phase,
                'worker_owner': self.adapter.ownership_token() if self.adapter.token else None,
                'job_closed': self.adapter.job_closed, 'process_handle_closed': self.adapter.handle_closed,
                'worker_started': self.adapter.token is not None, 'prepared_exposed': self.prepared_exposed,
                'source_sha256': self.fingerprints, 'python': self.adapter.python_identity, 'commands': self.records,
                'watchdog_stopped': not self.watchdog.thread.is_alive(), 'watchdog_loss': self.watchdog.reason,
                'godot_started': False, 'renderer_acceptance': False}
            try: P.publish(self.options.owned_root / 'controller-outcome.json', outcome, 128*1024)
            except BaseException: self.exit_code = 2
            self.transport.finish()
        return self.exit_code


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--main-root', type=Path, required=True); parser.add_argument('--work-root', type=Path, required=True); parser.add_argument('--owned-root', type=Path, required=True)
    parser.add_argument('--parent-pid', type=int, required=True); parser.add_argument('--parent-image', required=True)
    parser.add_argument('--parent-image-sha256', required=True)
    parser.add_argument('--session', required=True); parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--python-sha256', required=True); parser.add_argument('--idle-timeout', type=float, default=30)
    parser.add_argument('--watchdog-grace', type=float, default=.75)
    options = parser.parse_args(argv); parent = None; watchdog = None
    try:
        if os.name != 'nt': raise ValueError('Windows controller candidate only')
        load(options.main_root)
        if WORKER.file_sha(Path(__file__)) != options.controller_sha256: raise ValueError('Controller source fingerprint differs')
        if WORKER.file_sha(Path(sys.executable)) != options.python_sha256: raise ValueError('Controller Python fingerprint differs')
        if len(options.session) != 32 or any(c not in '0123456789abcdef' for c in options.session): raise ValueError('Bounded session nonce required')
        if not 0 < options.idle_timeout <= 120: raise ValueError('Bounded host idle timeout required')
        if not .1 <= options.watchdog_grace <= 2: raise ValueError('Bounded watchdog grace required')
        if not options.work_root.is_absolute(): raise ValueError('Explicit absolute preview work root required')
        options.main_root = options.main_root.absolute(); options.owned_root = options.owned_root.absolute(); options.work_root = options.work_root.absolute()
        P.owned(options.owned_root, options.work_root)
        options.owned_root.mkdir(parents=True, exist_ok=False)
        parent = ParentLease(options.parent_pid, options.parent_image, options.parent_image_sha256)
        transport = Transport(); watchdog = LifetimeWatchdog(parent, transport, options.watchdog_grace)
        controller = Controller(options, parent, transport, watchdog)
        return controller.run()
    except BaseException as error:
        if watchdog is not None: watchdog.stop()
        if parent is not None: parent.close()
        # Startup failures occur before the ownership service starts. Keep this
        # diagnostic bounded; no worker can have started here.
        os.write(2, (type(error).__name__+': '+str(error)[:512]+'\n').encode('ascii', 'backslashreplace'))
        return 2


if __name__ == '__main__': raise SystemExit(main())
