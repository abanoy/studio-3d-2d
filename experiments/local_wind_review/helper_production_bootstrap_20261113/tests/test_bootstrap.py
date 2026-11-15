"""Production-shaped host bootstrap and large-reference CPU bridge checks.

No main project is launched, no renderer/model/native converter is exercised.
The only terminations use an exact created Popen handle or an already retained,
creation-verified controller handle. Worker observation handles cannot terminate.
"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib
import io
import json
import os
import subprocess
import sys
import threading
import time
import unittest
import uuid

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parents[1]
TOOLS = OUT / 'candidate/tools'
PROJECT = OUT / 'isolated'
GODOT = Path(r'C:\a\tools\Godot\Godot_v4.6-stable_win64.exe')
PYTHON = Path(r'C:\Program Files\Python313\python.exe')
sys.path[:0] = [str(TOOLS), str(ROOT / 'tools'), str(ROOT / 'tests')]
from test_secondary_helpers import two_panel_fixture, request
import wind_helper_preview as P

RUN = OUT / 'cpu-results' / uuid.uuid4().hex


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def publish(path, value):
    """Fresh owned metadata only; never replace a published action."""
    raw = (json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii')
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise ValueError('Refuse to replace fixture metadata')
    os.replace(temporary, path)


def owner(value):
    """Godot JSON numeric PID tokens arrive as doubles; validate before int."""
    pid = value.get('pid')
    if type(pid) not in (int, float) or not 0 < pid < 2**32 or int(pid) != pid:
        raise ValueError('Exact bounded process PID required')
    created = value.get('created_100ns')
    if not isinstance(created, str) or not created.isdigit() or int(created) <= 0:
        raise ValueError('Exact process creation string required')
    return {'pid': int(pid), 'created_100ns': created}


class Observer:
    """Retained native handles, never reopen a PID for termination."""
    def __init__(self):
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        def api(name, result, *args):
            fn = getattr(self.kernel, name)
            fn.restype = result
            fn.argtypes = args
            return fn
        self.open = api('OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
        self.current = api('GetCurrentProcess', W.HANDLE)
        self.pid = api('GetProcessId', W.DWORD, W.HANDLE)
        self.times = api('GetProcessTimes', W.BOOL, W.HANDLE, *([C.POINTER(W.FILETIME)] * 4))
        self.wait = api('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        self.exit_code = api('GetExitCodeProcess', W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
        self.terminate_native = api('TerminateProcess', W.BOOL, W.HANDLE, W.UINT)
        self.handle_count_native = api('GetProcessHandleCount', W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
        self.close_native = api('CloseHandle', W.BOOL, W.HANDLE)
        self.watches = []
        self.records = []

    def identity(self, handle):
        times = [W.FILETIME() for _ in range(4)]
        if not self.times(handle, *(C.byref(item) for item in times)):
            raise OSError(C.get_last_error(), 'Read retained process creation time')
        return owner({'pid': int(self.pid(handle)),
                      'created_100ns': str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)})

    def retain(self, expected, label, terminate=False):
        expected = owner(expected)
        handle = self.open(0x100000 | 0x1000 | (1 if terminate else 0), False, expected['pid'])
        if not handle:
            raise OSError(C.get_last_error(), 'Retain exact known process')
        watch = {'handle': handle, 'owner': expected, 'label': label,
                 'may_terminate': terminate, 'observations': [], 'observer_handle_closed': False}
        self.watches.append(watch)  # Register before any query can fail.
        if self.identity(handle) != expected:
            raise AssertionError('Retained process has a different incarnation')
        return watch

    def terminate(self, watch, code=93):
        if not watch['may_terminate']:
            raise ValueError('Observation-only worker handle cannot terminate')
        if self.identity(watch['handle']) != watch['owner']:
            raise AssertionError('Retained controller identity differs')
        if not self.terminate_native(watch['handle'], code):
            raise OSError(C.get_last_error(), 'Terminate exact retained controller')
        watch['terminated_through_retained_verified_handle'] = True

    def observe(self, watch, label, timeout=4000):
        started = time.monotonic()
        state = self.wait(watch['handle'], timeout)
        if state not in (0, 258):
            raise OSError(C.get_last_error(), 'Observe retained native process')
        observed = self.identity(watch['handle'])
        code = W.DWORD()
        if not self.exit_code(watch['handle'], C.byref(code)):
            raise OSError(C.get_last_error(), 'Read retained process exit')
        value = {'label': label, 'owner': watch['owner'], 'observed': observed,
                 'signaled': state == 0, 'exit_code_u32': int(code.value),
                 'wait_elapsed_seconds': time.monotonic() - started}
        watch['observations'].append(value)
        return value

    def handle_count(self, handle):
        count = W.DWORD()
        if not self.handle_count_native(handle, C.byref(count)):
            raise OSError(C.get_last_error(), 'Read retained Godot process handle count')
        return int(count.value)

    def close_all(self):
        errors = []
        observer = self.identity(self.current())
        for watch in self.watches:
            if watch['observer_handle_closed']:
                continue
            try:
                self.observe(watch, 'final cleanup observation', timeout=4000)
            except BaseException as error:
                watch['cleanup_observation_error'] = type(error).__name__ + ': ' + str(error)
                errors.append(str(error))
            finally:
                watch['observer_handle_closed'] = bool(self.close_native(watch['handle']))
                if not watch['observer_handle_closed']:
                    errors.append('Retained observation handle close failed')
                self.records.append({key: value for key, value in watch.items() if key != 'handle'} |
                                    {'observer': observer, 'generic_pid_termination': False})
        return errors


@unittest.skipUnless(os.name == 'nt', 'Windows retained-process ownership')
class GodotBridge(unittest.TestCase):
    def setUp(self):
        if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 13) or Path(sys.executable).resolve() != PYTHON.resolve():
            self.fail('Use the existing approved CPython3.13 executable')
        self.root = RUN / hashlib.sha256(self._testMethodName.encode()).hexdigest()[:10]
        self.root.mkdir(parents=True, exist_ok=False)
        publish(self.root / 'testcase.json', {'test': self._testMethodName})
        self.source = self.root / 'source.glb'
        self.glb = two_panel_fixture(self.source)
        self.before = P.identity(self.source)
        self.context = {'actor_id': 'CPU-日本語', 'root_instance_id': str(2**63 + 1),
                        'revision': '8', 'frame': '12', 'authored_sha256': 'a' * 64,
                        'shape_sha256': 'b' * 64, 'bindings_sha256': 'c' * 64}
        self.observer = Observer()
        self.godot = None
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.readers = []
        self.drain_errors = []
        self.action_number = 0
        self.event_number = 0
        self.controller = None
        self.worker = None
        self.send_metrics = []
        self.expected_bridge_failure = False
        self.addCleanup(self.cleanup)

    def wait_json(self, path, timeout=6):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if path.is_file():
                try:
                    return json.loads(path.read_bytes())
                except (json.JSONDecodeError, OSError):
                    pass  # The GDScript fixture publishes before closing its file.
            failure = self.root / 'bridge-failure.json'
            if failure.is_file() and path != failure and not self.expected_bridge_failure:
                try:
                    raise AssertionError('Node bridge failed: ' + str(json.loads(failure.read_bytes())))
                except json.JSONDecodeError:
                    pass
            if self.godot is not None and self.godot.poll() is not None:
                # An expected exit can precede an audit file flush by a moment;
                # keep the bounded wait, retaining logs for failure diagnosis.
                time.sleep(.01)
            else:
                time.sleep(.01)
        self.fail('Fixture evidence watchdog: ' + str(path) + '\n' + bytes(self.stderr).decode('utf-8', 'replace'))

    def launch(self, wrapper=None, config_overrides=None, expect_ready=True):
        if not GODOT.is_file() or not PYTHON.is_file():
            self.fail('Approved existing runtimes are unavailable')
        self.godot_sha256 = sha(GODOT)
        self.python_sha256 = sha(PYTHON)
        self.controller_source = TOOLS / 'wind_preview_controller.py'
        launcher = wrapper or self.controller_source
        args = [str(GODOT), '--headless', '--path', str(PROJECT), '--script', 'res://fixture.gd',
                '--log-file', str(self.root / 'engine.log'), '--', str(self.root)]
        self.godot = subprocess.Popen(args, cwd=PROJECT, stdin=subprocess.DEVNULL,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)
        self.godot_owner = self.observer.identity(self.godot._handle)
        def drain(pipe, target):
            try:
                while True:
                    data = pipe.read1(4096)
                    if not data:
                        return
                    target.extend(data[:max(0, 256 * 1024 - len(target))])
            except BaseException as error:
                self.drain_errors.append(type(error).__name__ + ': ' + str(error))
        for pipe, target in ((self.godot.stdout, self.stdout), (self.godot.stderr, self.stderr)):
            thread = threading.Thread(target=drain, args=(pipe, target), daemon=True)
            thread.start()
            self.readers.append(thread)
        self.owned = self.root / 'controller-jobs'
        # Host identity is intentionally absent. The Node derives its own PID
        # and approved engine image; its controller queries the retained handle.
        config = {'main_root': str(ROOT), 'owned_root': str(self.owned),
                  'session': uuid.uuid4().hex, 'python': str(PYTHON), 'python_sha256': self.python_sha256,
                  'controller': str(self.controller_source), 'controller_sha256': sha(self.controller_source),
                  'launcher': str(launcher), 'launcher_sha256': sha(launcher)}
        config.update(config_overrides or {})
        for key in ('host', 'host_pid', 'host_image', 'host_image_sha256', 'parent_pid', 'parent_created_100ns'):
            self.assertNotIn(key, config)
        publish(self.root / 'launch-record.json', {'args': args, 'godot_sha256': self.godot_sha256,
                  'python_sha256': self.python_sha256, 'host': self.godot_owner,
                  'observer': self.observer.identity(self.observer.current()), 'config': config,
                  'headless_only': True, 'main_project_launched': False})
        publish(self.root / 'config.json', config)
        if not expect_ready:
            return None
        ready = self.event('ready')
        self.assertEqual(owner(ready['host']), self.godot_owner)
        self.assertEqual(os.path.normcase(str(Path(ready['host']['image_path']).resolve())),
                         os.path.normcase(str(GODOT.resolve())))
        self.assertEqual(ready['host']['image_sha256'], self.godot_sha256)
        self.ready_host = ready['host']
        self.controller = self.observer.retain(ready['controller'], 'Godot-created controller', terminate=True)
        return ready

    def event(self, expected=None):
        self.event_number += 1
        value = self.wait_json(self.root / ('event-%03d.json' % self.event_number))
        if expected:
            self.assertEqual(value['event'], expected, value)
        return value

    def action(self, op, fields=None, check_send=True):
        self.action_number += 1
        number = self.action_number
        publish(self.root / ('action-%03d.json' % number), {'op': op, 'fields': fields or {}})
        if check_send and op not in ('free', 'tree_exit', 'quit', 'close_pipes', 'release', 'pause_node', 'late_event'):
            result = self.wait_json(self.root / ('send-%03d.json' % number))
            self.assertEqual(result['error'], '', result)
            count = result.get('control_bytes')
            self.assertIn(type(count), (int, float), result)
            self.assertTrue(0 < count <= 2048 and int(count) == count, result)
            self.send_metrics.append({'action': number, 'op': op, 'control_bytes': int(count)})
        return number

    def start(self):
        self.action('start', {'source': str(self.source), 'items': [request(self.glb), dict(request(self.glb), component=1)],
                             'context': self.context, 'mode': 'included-batch'})
        return self.event('started')

    def prepare(self):
        until = time.monotonic() + 5
        while time.monotonic() < until:
            self.action('poll', {'context': self.context})
            value = self.event()
            if value['event'] == 'prepared':
                return value
            self.assertEqual(value['event'], 'running', value)
            time.sleep(.02)
        self.fail('Node/controller preparation watchdog')

    def submission_files(self):
        return sorted((self.owned / 'requests').glob('submission-*.json'))

    def assert_submission_binding(self, started, prepared=None, require_large=False):
        matches = [path for path in self.submission_files() if sha(path) == started['submission_sha256']]
        # Rejected attempts can publish identical bytes under distinct fresh
        # paths; SHA binds content, not a unique filesystem name. All such
        # copies must be byte-identical. The latest attempt is the current one.
        self.assertGreaterEqual(len(matches), 1, started)
        self.assertTrue(all(path.read_bytes()==matches[0].read_bytes() for path in matches))
        path = matches[-1]
        value = json.loads(path.read_bytes())
        self.assertEqual(value['format'], 'has_wind_preview_submission_1')
        self.assertEqual(value['purpose'], 'preview_only')
        self.assertEqual(value['source_sha256'], self.before['sha256'])
        self.assertEqual(value['source_bytes'], self.before['bytes'])
        context_bytes = value['context_json'].encode('ascii')
        self.assertEqual(json.loads(context_bytes), self.context)
        context_sha = hashlib.sha256(context_bytes).hexdigest()
        self.assertEqual(started['context_sha256'], context_sha)
        self.assertEqual(started['request_file_sha256'], sha(Path(started['job']) / 'request.json'))
        if require_large:
            self.assertGreater(path.stat().st_size, 2048)
            session = json.loads((self.root / 'config.json').read_bytes())['session']
            inline_poll = {'format': 'has_wind_preview_controller_command_1', 'session': session,
                           'seq': 1, 'op': 'poll', **started['ticket'], 'context': self.context}
            inline_bytes = len((json.dumps(inline_poll, ensure_ascii=True, separators=(',', ':')) + '\n').encode('ascii'))
            self.assertGreater(inline_bytes, 2048)
            self.assertTrue(any(item['op'] == 'start' for item in self.send_metrics))
            if prepared is not None:
                self.assertTrue(any(item['op'] == 'poll' for item in self.send_metrics))
            publish(self.root / (path.stem + '-transport-metrics.json'),
                    {'submission_file': str(path), 'submission_bytes': path.stat().st_size,
                     'byte_identical_submission_paths': [str(item) for item in matches],
                     'context_ascii_bytes': len(context_bytes), 'would_be_inline_poll_bytes': inline_bytes,
                     'actual_successful_control_frames': list(self.send_metrics),
                     'all_actual_control_frames_at_most_2048': all(item['control_bytes'] <= 2048 for item in self.send_metrics)})
        if prepared is not None:
            self.assertEqual(prepared['submission_sha256'], sha(path))
            self.assertEqual(prepared['context_sha256'], context_sha)
            self.assertEqual(prepared['completion']['request_file_sha256'], started['request_file_sha256'])
        return path

    def use_large_context(self):
        # Every context field remains within the real protocol's 256-character
        # bound; the exact file envelope exceeds the 2048-byte pipe frame cap.
        self.context.update(actor_id='髪' * 220, root_instance_id='編' * 220,
                            revision='風' * 220, frame='揺' * 220)
        self.assertTrue(all(len(self.context[key]) <= 256 for key in ('actor_id', 'root_instance_id', 'revision', 'frame')))
        self.assertGreater(len(json.dumps({'context': self.context}, ensure_ascii=True).encode('ascii')), 2048)

    def close_prepared(self):
        self.action('close')
        self.closed_or_ended()
        self.ended(self.controller, 'controller closes after prepared fixture')
        self.action('free', check_send=False)
        self.wait_json(self.root / 'node-freed.json')
        self.quit_godot()

    def wrapper(self, body):
        path = self.root / 'controller-wrapper.py'
        header = ('from pathlib import Path\nimport sys,time,json,ctypes as ctypes\nfrom ctypes import wintypes\n'
                  'sys.path.insert(0,' + repr(str(TOOLS)) + ')\nimport wind_preview_controller as C\n'
                  'C.load(Path(' + repr(str(ROOT)) + '))\n')
        path.write_text(header + body + '\nraise SystemExit(C.main())\n', encoding='utf-8')
        return path

    def sleeping_worker_wrapper(self, block_poll=False, emit_unknown=False):
        child = self.root / 'sleeping-worker.py'
        child.write_text('import sys,time,json\nfrom pathlib import Path\nsys.path.insert(0,' + repr(str(TOOLS)) + ')\n'
                         'import wind_preview_worker as W\ncode=W.main()\nif code:raise SystemExit(code)\n'
                         'sys.stdin.close()\njob=Path(sys.argv[sys.argv.index("--job")+1])\n'
                         '(job/"awake.json").write_text(json.dumps({"no_more_stdin_reads":True}))\ntime.sleep(30)\n', encoding='utf-8')
        marker = self.root / 'assigned.json'
        body = ('old_command=C.A.OwnedPreviewJob.command\ndef command(self,job):\n args=old_command(self,job);args[4]=' + repr(str(child)) + ';return args\n'
                'C.A.OwnedPreviewJob.command=command\nold_assign=C.A.NativeJob.assign\ndef assign(self,process):\n'
                ' old_assign(self,process)\n fn=self.kernel.IsProcessInJob;fn.restype=wintypes.BOOL;fn.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]\n'
                ' inside=wintypes.BOOL()\n if not fn(process._handle,self.handle,ctypes.byref(inside)):raise OSError(ctypes.get_last_error())\n'
                ' job=process.args[process.args.index("--job")+1]\n Path(' + repr(str(marker)) + ').write_text(json.dumps({"child":self.identity(process),"assigned":self.assigned,"inside_exact_job":bool(inside.value),"job":job}))\n'
                'C.A.NativeJob.assign=assign\n')
        if block_poll:
            body += ('old_dispatch=C.Controller.dispatch\ndef dispatch(self,message):\n'
                     ' if message.get("op")=="poll":\n  Path(' + repr(str(self.root / 'service-blocked.json')) + ').write_text(json.dumps({"blocked":True}))\n  while True:time.sleep(.05)\n'
                     ' return old_dispatch(self,message)\nC.Controller.dispatch=dispatch\n')
        if emit_unknown:
            body += ('old_emit=C.Controller.emit\ndef emit(self,kind,**values):\n'
                     ' return old_emit(self,"alien" if kind=="running" else kind,**values)\nC.Controller.emit=emit\n')
        return self.wrapper(body)

    def live_worker(self, block_poll=False, emit_unknown=False):
        self.launch(self.sleeping_worker_wrapper(block_poll, emit_unknown))
        self.start()
        assigned = self.wait_json(self.root / 'assigned.json')
        self.assertTrue(assigned['assigned'])
        self.assertTrue(assigned['inside_exact_job'])
        self.wait_json(Path(assigned['job']) / 'awake.json')
        self.worker = self.observer.retain(assigned['child'], 'Job-owned nonreading CPU worker')
        self.assertFalse(self.observer.observe(self.worker, 'alive before lifecycle action', timeout=0)['signaled'])
        return assigned

    def ended(self, watch, label, expected_exit=None):
        value = self.observer.observe(watch, label)
        self.assertTrue(value['signaled'], value)
        self.assertEqual(value['observed'], watch['owner'])
        if expected_exit is not None:
            self.assertEqual(value['exit_code_u32'], expected_exit, value)
        return value

    def quit_godot(self):
        if self.godot.poll() is None:
            self.action('quit', check_send=False)
            self.godot.wait(timeout=5)
        self.assertEqual(self.godot.returncode, 0, bytes(self.stderr).decode('utf-8', 'replace'))

    def closed_or_ended(self):
        # A short-lived controller can exit before the Node reads its final
        # queued acknowledgement. Native exit0 is a valid close observation.
        until = time.monotonic() + 5
        while time.monotonic() < until:
            path = self.root / ('event-%03d.json' % (self.event_number + 1))
            if path.exists():
                return self.event('closed')
            if (self.root / 'node-ended.json').exists():
                value = self.wait_json(self.root / 'node-ended.json')
                self.assertEqual(value.get('exit', value.get('code')), 0, value)
                return value
            if (self.root / 'bridge-failure.json').exists():
                self.fail(str(self.wait_json(self.root / 'bridge-failure.json')))
            time.sleep(.01)
        self.fail('Node close/exit acknowledgement watchdog')

    def stable_handle_count(self):
        values = []
        for _ in range(3):
            values.append(self.observer.handle_count(self.godot._handle))
            time.sleep(.03)
        self.assertEqual(min(values), max(values), values)
        return values[0]

    def test_real_node_normal_prepared_transport_and_unicode_context(self):
        self.launch()
        self.assertFalse(any(self.owned.glob('*/request.json')))
        started = self.start()
        prepared = self.prepare()
        self.assertEqual(prepared['ticket'], started['ticket'])
        self.assertTrue(prepared['job_closed'])
        self.assertTrue(prepared['process_handle_closed'])
        request_value = json.loads((Path(prepared['job']) / 'request.json').read_bytes())
        self.assertEqual(request_value['context']['actor_id'], self.context['actor_id'])
        self.assertIs(type(request_value['generation']), int)
        self.assertIs(type(request_value['items'][0]['node']), int)
        self.assert_submission_binding(started, prepared)
        self.action('close')
        self.closed_or_ended()
        self.ended(self.controller, 'controller closed after Node command')
        self.action('free', check_send=False)
        self.assertTrue(self.wait_json(self.root / 'node-freed.json')['freed'])
        self.quit_godot()

    def test_node_free_ends_controller_and_owned_live_worker(self):
        self.live_worker()
        self.action('free', check_send=False)
        self.assertTrue(self.wait_json(self.root / 'node-freed.json')['freed'])
        self.ended(self.controller, 'Node free closes controller ownership')
        self.ended(self.worker, 'Node free closes worker Job')
        self.assertIsNone(self.godot.poll())
        self.quit_godot()

    def test_node_tree_exit_ends_controller_and_owned_live_worker(self):
        self.live_worker()
        self.action('tree_exit', check_send=False)
        value = self.wait_json(self.root / 'node-left-tree.json')
        self.assertFalse(value['inside'])
        self.assertTrue(value['stopped'])
        self.ended(self.controller, 'Node tree exit closes controller')
        self.ended(self.worker, 'Node tree exit closes worker Job')
        self.quit_godot()

    def test_normal_godot_tree_shutdown_ends_controller_and_worker(self):
        self.live_worker()
        self.quit_godot()
        self.ended(self.controller, 'normal Godot tree shutdown')
        self.ended(self.worker, 'normal Godot shutdown releases worker Job')

    def test_abrupt_godot_death_ends_controller_and_worker(self):
        self.live_worker()
        self.assertEqual(self.observer.identity(self.godot._handle), self.godot_owner)
        self.godot.kill()  # Exact Popen-created process handle, no PID lookup.
        self.godot.wait(timeout=4)
        self.ended(self.controller, 'abrupt exact Godot death')
        self.ended(self.worker, 'abrupt Godot death releases controller Job')

    def test_controller_death_ends_worker_and_node_detects_exit(self):
        self.live_worker()
        self.observer.terminate(self.controller)
        self.ended(self.controller, 'exact retained controller termination', expected_exit=93)
        self.ended(self.worker, 'controller death closes worker Job')
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertIn('Controller ended', failure['reason'])
        self.quit_godot()

    def test_watchdog_forces_only_self_after_host_loss_during_blocked_service(self):
        self.live_worker(block_poll=True)
        self.action('poll', {'context': self.context})
        self.wait_json(self.root / 'service-blocked.json')
        self.assertEqual(self.observer.identity(self.godot._handle), self.godot_owner)
        self.godot.kill()
        self.godot.wait(timeout=4)
        self.ended(self.controller, 'independent watchdog exits blocked controller', expected_exit=74)
        self.ended(self.worker, 'self-exit closes blocked controller Job')
        self.assertFalse((self.owned / 'controller-outcome.json').exists())

    def test_mapped_release_closes_two_godot_handles_exactly_once(self):
        self.live_worker()
        self.action('pause_node', check_send=False)
        self.wait_json(self.root / 'node-paused.json')
        self.action('close_pipes', check_send=False)
        self.wait_json(self.root / 'pipes-closed.json')
        self.ended(self.controller, 'EOF before mapped release')
        self.ended(self.worker, 'EOF closes worker before mapped release')
        before = self.stable_handle_count()
        index = self.action('release', check_send=False)
        first = self.wait_json(self.root / ('release-%03d.json' % index))
        after = self.stable_handle_count()
        self.assertTrue(first['attempted'], first)
        self.assertEqual(first['release_calls'], 1, first)
        self.assertEqual(before - after, 2)
        index = self.action('release', check_send=False)
        second = self.wait_json(self.root / ('release-%03d.json' % index))
        repeated = self.stable_handle_count()
        self.assertFalse(second['attempted'], second)
        self.assertEqual(second['release_calls'], 1, second)
        self.assertEqual(repeated, after)
        self.action('late_event', check_send=False)
        late = self.wait_json(self.root / 'late-event.json')
        self.assertFalse(late['admitted'], late)
        self.assertEqual(late['release_calls'], 1, late)
        publish(self.root / 'mapped-release-counts.json', {'before': before, 'after': after, 'repeated': repeated,
                                                       'delta': before - after, 'repeated_delta': repeated - after,
                                                       'first': first, 'second': second})
        self.action('free', check_send=False)
        self.wait_json(self.root / 'node-freed.json')
        # Fixture consumes action files in sequence; successful quit proves it
        # processed this second free without another Node/process cleanup call.
        self.action('free', check_send=False)
        self.quit_godot()

    def test_missing_runtime_never_reserves_process_map_entry(self):
        self.launch(config_overrides={'python': str(self.root / 'absent-python.exe')}, expect_ready=False)
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertIn('fingerprint differs', failure['reason'])
        self.assertFalse(failure['release']['attempted'], failure)
        self.assertEqual(failure['release']['release_calls'], 0, failure)
        self.godot.wait(timeout=4)
        self.assertEqual(self.godot.returncode, 2)
        self.assertFalse(self.owned.exists())

    def test_createprocess_empty_return_never_reserves_process_map_entry(self):
        # This owned invalid-image fixture passes the test-only fingerprint
        # gate, then exercises the actual OS.execute_with_pipe empty result.
        # The expected Godot CreateProcess diagnostic remains in retained logs.
        invalid = self.root / 'not-executable.exe'
        invalid.write_bytes(b'Owned CPU fixture: this text is not an executable image.\n')
        self.launch(config_overrides={'python': str(invalid), 'python_sha256': sha(invalid)}, expect_ready=False)
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertEqual(failure['reason'], 'Controller did not start', failure)
        self.assertFalse(failure['release']['attempted'], failure)
        self.assertEqual(failure['release']['release_calls'], 0, failure)
        self.godot.wait(timeout=4)
        self.assertEqual(self.godot.returncode, 2)
        self.assertFalse(self.owned.exists())

    def test_malformed_nested_ready_fails_closed_without_worker_start(self):
        marker = self.root / 'uncorrupted-owner.json'
        release = self.root / 'release-corruption'
        body = ('old_emit=C.Transport.emit\ndef emit(self,value):\n'
                ' if value.get("event")=="ready":\n  Path(' + repr(str(marker)) + ').write_text(json.dumps(value["controller"]))\n'
                '  while not Path(' + repr(str(release)) + ').exists():time.sleep(.01)\n'
                '  value["controller"]=[]\n old_emit(self,value)\nC.Transport.emit=emit\n')
        self.launch(self.wrapper(body), expect_ready=False)
        exact = self.wait_json(marker)
        self.controller = self.observer.retain(exact, 'malformed-ready controller', terminate=False)
        release.write_text('release', encoding='ascii')
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertTrue(failure['reason'])
        self.expected_bridge_failure = True
        self.ended(self.controller, 'malformed nested ready releases controller')
        self.assertFalse(any(self.owned.glob('*/request.json')))
        number = self.action('release', check_send=False)
        result = self.wait_json(self.root / ('release-%03d.json' % number))
        self.assertFalse(result['attempted'])
        self.assertEqual(result['release_calls'], 1)
        self.quit_godot()

    def test_unknown_matching_poll_event_releases_controller_and_worker(self):
        self.live_worker(emit_unknown=True)
        self.action('poll', {'context': self.context})
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertIn('event', failure['reason'].lower())
        self.expected_bridge_failure = True
        self.ended(self.controller, 'unknown matching-sequence event releases controller')
        self.ended(self.worker, 'unknown event closes owned worker Job')
        number = self.action('release', check_send=False)
        result = self.wait_json(self.root / ('release-%03d.json' % number))
        self.assertFalse(result['attempted'])
        self.assertEqual(result['release_calls'], 1)
        self.quit_godot()

    def bootstrap_ready_fault(self, mutation):
        marker = self.root / 'bootstrap-owner.json'
        release = self.root / 'release-bootstrap-fault'
        body = ('old_emit=C.Transport.emit\ndef emit(self,value):\n'
                ' if value.get("event")=="ready":\n  Path(' + repr(str(marker)) + ').write_text(json.dumps(value["controller"]))\n'
                '  while not Path(' + repr(str(release)) + ').exists():time.sleep(.01)\n'
                '  ' + mutation + '\n old_emit(self,value)\nC.Transport.emit=emit\n')
        self.launch(self.wrapper(body), expect_ready=False)
        self.controller = self.observer.retain(self.wait_json(marker), 'tampered bootstrap controller')
        release.write_text('release', encoding='ascii')
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertTrue(failure['reason'], failure)
        self.expected_bridge_failure = True
        self.ended(self.controller, 'wrong bootstrap host closes controller')
        self.assertFalse(any(self.owned.glob('*/request.json')))
        self.assertFalse((self.root / 'event-001.json').exists())
        number = self.action('release', check_send=False)
        result = self.wait_json(self.root / ('release-%03d.json' % number))
        self.assertFalse(result['attempted'])
        self.assertEqual(result['release_calls'], 1)
        self.quit_godot()

    def test_ready_wrong_host_pid_is_refused_before_start(self):
        self.bootstrap_ready_fault('value["host"]["pid"]+=4')

    def test_ready_wrong_host_image_is_refused_before_start(self):
        self.bootstrap_ready_fault('value["host"]["image_path"]=' + repr(str(self.root / 'wrong-engine.exe')))

    def test_ready_missing_host_creation_is_refused_before_start(self):
        self.bootstrap_ready_fault('del value["host"]["created_100ns"]')

    def test_actual_host_image_pin_mismatch_refuses_before_ready(self):
        marker = self.root / 'bad-pin-owner.json'
        release = self.root / 'release-bad-pin'
        body = ('Path(' + repr(str(marker)) + ').write_text(json.dumps(C.WORKER.self_owner()))\n'
                'while not Path(' + repr(str(release)) + ').exists():time.sleep(.01)\n'
                'sys.argv[sys.argv.index("--parent-image-sha256")+1]="0"*64\n'
                'old_parent=C.ParentLease.__init__\ndef parent(self,*args,**kwargs):\n'
                ' try:return old_parent(self,*args,**kwargs)\n'
                ' except Exception as error:\n  Path(' + repr(str(self.root / 'host-pin-refusal.json')) + ').write_text(json.dumps({"error":str(error)}))\n  raise\n'
                'C.ParentLease.__init__=parent\n')
        self.launch(self.wrapper(body), expect_ready=False)
        self.controller = self.observer.retain(self.wait_json(marker), 'actual wrong-host-pin controller')
        release.write_text('release', encoding='ascii')
        failure = self.wait_json(self.root / 'bridge-failure.json')
        self.assertTrue(failure['reason'])
        self.expected_bridge_failure = True
        self.assertIn('fingerprint differs', self.wait_json(self.root / 'host-pin-refusal.json')['error'])
        # Node mapped cleanup can race the controller's final exit2; both its
        # observed exit and the actual ParentLease rejection remain evidence.
        self.ended(self.controller, 'retained host image fingerprint mismatch')
        self.assertFalse((self.root / 'event-001.json').exists())
        self.assertFalse(any(self.owned.glob('*/request.json')))
        self.quit_godot()

    def test_four_bad_references_refuse_then_large_file_prepares(self):
        outside = self.root / 'controller-jobs' / 'outside-request.json'
        body = ('old_dispatch=C.Controller.dispatch\ncounter=0\ndef dispatch(self,message):\n'
                ' global counter\n if message.get("op")=="start":\n  counter+=1\n  ref=message["submission"]\n'
                '  original=dict(ref)\n  label=None\n'
                '  if counter==1:label="raw-sha";ref["sha256"]="0"*64\n'
                '  elif counter==2:label="context-sha";ref["context_sha256"]="0"*64\n'
                '  elif counter==3:label="source-sha";ref["source_sha256"]="0"*64\n'
                '  elif counter==4:\n   label="owned-path"\n   target=Path(' + repr(str(outside)) + ')\n   target.write_bytes(Path(ref["path"]).read_bytes())\n   ref["path"]=str(target)\n'
                '  if label:(Path(' + repr(str(self.root)) + ')/("tamper-%03d.json"%counter)).write_text(json.dumps({"label":label,"original":original,"tampered":ref}))\n'
                ' return old_dispatch(self,message)\nC.Controller.dispatch=dispatch\n')
        self.use_large_context()
        self.launch(self.wrapper(body))
        labels = ['raw-sha', 'context-sha', 'source-sha', 'owned-path']
        reasons = ['raw bytes', 'context', 'source', 'owned']
        for number, (label, reason) in enumerate(zip(labels, reasons), 1):
            with self.subTest(reference=label):
                self.action('start', {'source': str(self.source), 'items': [request(self.glb), dict(request(self.glb), component=1)],
                                     'context': self.context, 'mode': 'included-batch'})
                refused = self.event('refused')
                self.assertIn(reason, refused['reason'].lower())
                self.assertEqual(refused['ticket'], {'generation': 0, 'nonce': None})
                marker = self.wait_json(self.root / ('tamper-%03d.json' % number))
                self.assertEqual(marker['label'], label)
                self.assertNotEqual(marker['original'], marker['tampered'])
                self.assertGreater(Path(marker['original']['path']).stat().st_size, 2048)
                self.assertFalse(any(self.owned.glob('*/request.json')))
        started = self.start()
        child = self.observer.retain(started['owner'], 'accepted large-submission worker')
        prepared = self.prepare()
        self.assert_submission_binding(started, prepared, require_large=True)
        self.ended(child, 'large-submission worker exits before prepared result')
        self.close_prepared()

    def test_cancel_rejects_stale_submission_then_fresh_large_file_prepares(self):
        body = ('old_dispatch=C.Controller.dispatch\ncounter=0\nfirst=None\ndef dispatch(self,message):\n'
                ' global counter,first\n if message.get("op")=="start":\n  counter+=1\n'
                '  if counter==1:first=dict(message["submission"])\n'
                '  elif counter==2:\n   fresh=dict(message["submission"])\n   message["submission"]=dict(first)\n'
                '   Path(' + repr(str(self.root / 'stale-reference.json')) + ').write_text(json.dumps({"fresh":fresh,"stale":first}))\n'
                ' return old_dispatch(self,message)\nC.Controller.dispatch=dispatch\n')
        self.use_large_context()
        self.launch(self.wrapper(body))
        first_started = self.start()
        first_child = self.observer.retain(first_started['owner'], 'cancelled large-submission worker')
        old_submission = self.assert_submission_binding(first_started, require_large=True)
        old_sha = sha(old_submission)
        self.action('cancel')
        cancelled = self.event('cancelled')
        self.assertIsNone(cancelled['ticket']['nonce'])
        self.ended(first_child, 'cancel closes first large-submission worker')
        self.action('start', {'source': str(self.source), 'items': [request(self.glb), dict(request(self.glb), component=1)],
                             'context': self.context, 'mode': 'included-batch'})
        refused = self.event('refused')
        self.assertIn('ticket', refused['reason'].lower())
        self.assertEqual(refused['ticket'], cancelled['ticket'])
        stale = self.wait_json(self.root / 'stale-reference.json')
        self.assertEqual(stale['stale']['sha256'], old_sha)
        self.assertNotEqual(stale['fresh']['path'], stale['stale']['path'])
        self.assertEqual(sha(old_submission), old_sha)
        started = self.start()
        fresh_child = self.observer.retain(started['owner'], 'fresh large-submission worker')
        prepared = self.prepare()
        self.assert_submission_binding(started, prepared, require_large=True)
        self.assertGreater(len(self.submission_files()), 2)
        self.ended(fresh_child, 'fresh large-submission worker exits')
        self.close_prepared()

    def cleanup(self):
        errors = []
        if self.godot is not None:
            try:
                if self.godot.poll() is None:
                    if self.observer.identity(self.godot._handle) != self.godot_owner:
                        raise AssertionError('Popen Godot identity changed')
                    self.godot.kill()
                    self.godot.wait(timeout=4)
                value = {'label': 'external Popen Godot handle', 'owner': self.godot_owner,
                         'observed': self.observer.identity(self.godot._handle),
                         'signaled': self.observer.wait(self.godot._handle, 0) == 0,
                         'returncode': self.godot.returncode, 'generic_pid_termination': False,
                         'godot_sha256': self.godot_sha256, 'headless_only': True}
            except BaseException as error:
                errors.append(type(error).__name__ + ': ' + str(error))
                value = {'label': 'external Popen Godot handle', 'cleanup_error': errors[-1]}
            finally:
                for thread in self.readers:
                    thread.join(1)
                    if thread.is_alive():
                        errors.append('Owned Godot output reader did not reach EOF')
                for pipe in (self.godot.stdout, self.godot.stderr):
                    if pipe is not None:
                        try:
                            pipe.close()
                        except OSError as error:
                            errors.append(str(error))
                self.godot._handle.Close()
                value['observer_handle_closed'] = self.godot._handle.closed
                self.observer.records.append(value)
        errors.extend(self.observer.close_all())
        errors.extend(self.drain_errors)
        (self.root / 'stdout.log').write_bytes(self.stdout)
        (self.root / 'stderr.log').write_bytes(self.stderr)
        publish(self.root / 'observer-receipts.json', {'records': self.observer.records,
                                                    'all_observer_handles_closed': all(item.get('observer_handle_closed') for item in self.observer.records),
                                                    'errors': errors, 'generic_pid_termination': False})
        self.assertFalse(errors, errors)
        self.assertEqual(P.identity(self.source), self.before)
        engine_log = (self.root / 'engine.log').read_text(encoding='utf-8', errors='replace') if (self.root / 'engine.log').exists() else ''
        combined = bytes(self.stdout).decode('utf-8', 'replace') + engine_log
        self.assertIn('4.6.stable.official.89cea1439', combined)


if __name__ == '__main__':
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GodotBridge))
    report = {'format': 'has_wind_production_bootstrap_cpu_tests_1', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'passed': result.wasSuccessful(), 'folder': str(RUN), 'real_windows_godot_headless': True,
              'godot_binary': str(GODOT), 'godot_sha256': sha(GODOT), 'python_sha256': sha(PYTHON),
              'gpu_used': False, 'main_project_launched': False, 'native_model_or_converter_started': False,
              'prior_packets_modified': False, 'normal_config_omits_host_identity': True,
              'scope': 'Isolated host bootstrap, large references and CPU lifecycle only'}
    (OUT / 'cpu-tests.log').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'cpu-tests.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue())
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
