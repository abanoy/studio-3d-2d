"""Real hidden Windows CPU controller/child lifetime observations, no renderer."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib
import io
import json
import os
import queue
import subprocess
import sys
import threading
import time
import unittest
import uuid

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parents[1]; ROOT = OUT.parents[1]; TOOLS = OUT/'candidate/tools'
sys.path[:0] = [str(TOOLS), str(ROOT/'tools'), str(ROOT/'tests')]
from test_secondary_helpers import two_panel_fixture, request
import wind_preview_controller as CONTROLLER
CONTROLLER.load(ROOT)
P = CONTROLLER.P; A = CONTROLLER.A
RUN = OUT/'cpu-results'/uuid.uuid4().hex


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class NativeObserver:
    def __init__(self):
        self.k = C.WinDLL('kernel32', use_last_error=True)
        def api(name, result, *args):
            fn = getattr(self.k, name); fn.restype = result; fn.argtypes = args; return fn
        self.open = api('OpenProcess', W.HANDLE, W.DWORD, W.BOOL, W.DWORD)
        self.current = api('GetCurrentProcess', W.HANDLE)
        self.getpid = api('GetProcessId', W.DWORD, W.HANDLE)
        self.times = api('GetProcessTimes', W.BOOL, W.HANDLE, *([C.POINTER(W.FILETIME)]*4))
        self.wait = api('WaitForSingleObject', W.DWORD, W.HANDLE, W.DWORD)
        self.exit_native = api('GetExitCodeProcess', W.BOOL, W.HANDLE, C.POINTER(W.DWORD))
        self.close_native = api('CloseHandle', W.BOOL, W.HANDLE)
        self.records = []; self.handles = {}

    def identity(self, handle):
        values = [W.FILETIME() for _ in range(4)]
        if not self.times(handle, *(C.byref(v) for v in values)): raise OSError(C.get_last_error())
        return {'pid': int(self.getpid(handle)), 'created_100ns': str((values[0].dwHighDateTime<<32)|values[0].dwLowDateTime)}

    def watch(self, owner):
        handle = self.open(0x100000|0x1000, False, owner['pid'])
        if not handle: raise OSError(C.get_last_error(), 'Observe exact known child')
        self.handles[int(handle)] = owner
        try:
            if self.identity(handle) != owner: raise AssertionError('Known child incarnation differs')
        except BaseException:
            if self.close_native(handle):self.handles.pop(int(handle),None)
            raise
        return handle

    def finish_watch(self, handle, expected, label, timeout=4000):
        record = {'label':label,'owner':expected,'observer':self.identity(self.current()),'generic_pid_termination':False}
        try:
            record['signaled'] = self.wait(handle, timeout) == 0
            record['observed'] = self.identity(handle); code = W.DWORD()
            if not self.exit_native(handle, C.byref(code)): raise OSError(C.get_last_error())
            record['exit_code_u32'] = int(code.value)
        finally:
            record['observer_handle_closed'] = bool(self.close_native(handle))
            if record['observer_handle_closed']:self.handles.pop(int(handle),None)
            self.records.append(record)
        return record


@unittest.skipUnless(os.name == 'nt', 'Windows CPU process ownership')
class Controllers(unittest.TestCase):
    def setUp(self):
        self.root = RUN/hashlib.sha256(self._testMethodName.encode()).hexdigest()[:10]
        self.root.mkdir(parents=True); (self.root/'testcase.json').write_text(json.dumps({'test':self._testMethodName})+'\n')
        self.source = self.root/'source.glb'; self.glb = two_panel_fixture(self.source); self.before = P.identity(self.source)
        self.context = {'actor_id':'synthetic','root_instance_id':str(2**63+1),'revision':'8','frame':'12',
            'authored_sha256':'a'*64,'shape_sha256':'b'*64,'bindings_sha256':'c'*64}
        self.observer = NativeObserver(); self.processes = []; self.seq = 0; self.ticket = {'generation':0,'nonce':None}
        self.addCleanup(self.cleanup)

    def cleanup(self):
        errors=[]
        for process in self.processes:
            if process.poll() is None:
                # Exact created Popen handle only; never look up/kill a PID.
                process.kill(); process.wait(timeout=4)
            observed=self.observer.identity(process._handle)
            code=W.DWORD();self.observer.exit_native(process._handle,C.byref(code))
            record={'label':getattr(process,'_observer_label','owned CPU process'),'owner':process._observer_owner,
                    'observed':observed,'signaled':self.observer.wait(process._handle,0)==0,
                    'exit_code_u32':int(code.value),'observer':self.observer.identity(self.observer.current()),
                    'generic_pid_termination':False}
            if observed!=process._observer_owner:errors.append('Owned Popen incarnation differs')
            close_errors=[]
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe and not pipe.closed:
                    try:pipe.close()
                    except OSError as error:close_errors.append(str(error))
                    if not pipe.closed:errors.append('Owned process pipe remained open')
            if not process._handle.closed: process._handle.Close()
            record['observer_handle_closed']=process._handle.closed;record['pipe_close_diagnostics']=close_errors;self.observer.records.append(record)
        for handle,owner in list(self.observer.handles.items()):
            record=self.observer.finish_watch(handle,owner,'finally cleanup of retained observation handle',timeout=0)
            if not record['observer_handle_closed']:errors.append('Observation handle close failed and remains tracked')
        (self.root/'observer-receipts.json').write_text(json.dumps(self.observer.records,indent=2)+'\n')
        self.assertFalse(errors,errors)
        self.assertEqual(P.identity(self.source), self.before)

    def launch(self, wrapper=None, parent=None, read_events_limit=None, **overrides):
        self.session = uuid.uuid4().hex; self.owned = self.root/('host-'+uuid.uuid4().hex[:6])
        owner = parent or self.observer.identity(self.observer.current())
        params = {'main-root':str(ROOT),'owned-root':str(self.owned),'parent-pid':str(owner['pid']),
                  'parent-created-100ns':owner['created_100ns'],'session':self.session,
                  'controller-sha256':sha(TOOLS/'wind_preview_controller.py'),'python-sha256':sha(sys.executable),
                  'idle-timeout':'8'}
        params.update(overrides)
        script = wrapper or TOOLS/'wind_preview_controller.py'
        args = [sys.executable,'-I','-B','-u',str(script)]
        for key,value in params.items(): args += ['--'+key,str(value)]
        process = subprocess.Popen(args, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                   close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
        self.processes.append(process); self.process=process
        self.controller_owner = self.observer.identity(process._handle)
        process._observer_owner=self.controller_owner;process._observer_label='controller'
        self.events=queue.Queue(256); self.stderr=bytearray()
        def read_events():
            try:
                read_count=0
                while True:
                    raw=process.stdout.readline(CONTROLLER.MAX_EVENT+1)
                    if not raw: self.events.put(None); return
                    self.events.put(CONTROLLER.strict_json(raw))
                    read_count+=1
                    if read_events_limit is not None and read_count>=read_events_limit:return
            except BaseException as e: self.events.put({'reader_error':str(e)})
        def read_errors():
            while True:
                raw=process.stderr.read1(4096)
                if not raw:return
                self.stderr.extend(raw[:max(0,16384-len(self.stderr))])
        threading.Thread(target=read_events,daemon=True).start(); threading.Thread(target=read_errors,daemon=True).start()
        return process

    def event(self, expected=None):
        value=self.events.get(timeout=5)
        self.assertIsNotNone(value, bytes(self.stderr)); self.assertIn('event',value,value)
        if expected:self.assertEqual(value['event'],expected,value)
        self.ticket=value['ticket']; return value

    def send(self, op, **fields):
        self.seq+=1
        value={'format':CONTROLLER.COMMAND,'session':self.session,'seq':self.seq,'op':op,**self.ticket,**fields}
        self.process.stdin.write(P.encoded(value)); self.process.stdin.flush(); return value

    def start(self):
        self.send('start',source=str(self.source),items=[request(self.glb),dict(request(self.glb),component=1)],context=self.context,mode='included-batch')
        return self.event('started')

    def prepare(self):
        until=time.monotonic()+5
        while time.monotonic()<until:
            self.send('poll',context=self.context); value=self.event()
            if value['event']!='running':self.assertEqual(value['event'],'prepared',value);return value
            time.sleep(.01)
        self.fail('Controller prepare watchdog')

    def close(self):
        self.send('close'); self.event('closed'); self.process.wait(timeout=4)
        self.assertEqual(self.process.returncode,0,bytes(self.stderr))
        return json.loads((self.owned/'controller-outcome.json').read_bytes())

    def marker(self,path):
        until=time.monotonic()+5
        while time.monotonic()<until:
            if path.is_file():
                try:return json.loads(path.read_bytes())
                except json.JSONDecodeError: pass
            time.sleep(.01)
        self.fail('Owned observation marker watchdog')

    def wrapper(self, body):
        path=self.root/('wrap-'+uuid.uuid4().hex[:6]+'.py')
        header='from pathlib import Path\nimport sys,time,json,ctypes as ctypes\nfrom ctypes import wintypes\nsys.path.insert(0,'+repr(str(TOOLS))+')\nimport wind_preview_controller as C\nC.load(Path('+repr(str(ROOT))+'))\n'
        path.write_text(header+body+'\nraise SystemExit(C.main())\n',encoding='utf-8');return path

    def postassignment_wrapper(self):
        child=self.root/'sleeping-worker.py'
        body='import sys,time,json\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(TOOLS))+')\nimport wind_preview_worker as W\ncode=W.main()\nif code:raise SystemExit(code)\nsys.stdin.close()\njob=Path(sys.argv[sys.argv.index("--job")+1])\n(job/"awake.json").write_text(json.dumps({"no_more_stdin_reads":True}))\ntime.sleep(30)\n'
        child.write_text(body,encoding='utf-8')
        marker=self.root/'assigned.json'
        code='old_command=C.A.OwnedPreviewJob.command\ndef command(self,job):\n args=old_command(self,job);args[4]='+repr(str(child))+';return args\nC.A.OwnedPreviewJob.command=command\nold_assign=C.A.NativeJob.assign\ndef assign(self,process):\n old_assign(self,process)\n fn=self.kernel.IsProcessInJob;fn.restype=wintypes.BOOL;fn.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]\n inside=wintypes.BOOL()\n if not fn(process._handle,self.handle,ctypes.byref(inside)):raise OSError(ctypes.get_last_error())\n job=process.args[process.args.index("--job")+1]\n Path('+repr(str(marker))+').write_text(json.dumps({"child":self.identity(process),"assigned":self.assigned,"inside_exact_job":bool(inside.value),"job":job}))\nC.A.NativeJob.assign=assign\n'
        return self.wrapper(code),marker

    def test_start_poll_prepared_and_close_invalidates_without_apply(self):
        self.launch(); self.event('ready'); self.assertFalse(any(self.owned.glob('*/request.json')))
        started=self.start(); prepared=self.prepare()
        self.assertEqual(started['ticket'],prepared['ticket']);self.assertTrue(prepared['job_closed']);self.assertTrue(prepared['process_handle_closed'])
        self.send('poll',context=self.context);self.event('prepared')
        outcome=self.close();self.assertEqual(outcome['phase'],'stopped');self.assertIsNone(outcome['ticket']['nonce'])
        self.assertTrue(outcome['host_handle_closed']);self.assertTrue(outcome['prepared_exposed'])

    def test_poll_cancel_invalid_start_before_start_create_no_job(self):
        self.launch();self.event('ready')
        for op,extra in [('poll',{'context':self.context}),('cancel',{}),('start',{'source':str(self.source),'items':[],'context':self.context})]:
            self.send(op,**extra);self.event('refused')
        self.assertFalse(any(self.owned.glob('*/request.json')))
        self.assertFalse(self.close()['worker_started'])

    def test_replay_and_stale_cancel_do_not_affect_new_generation(self):
        self.launch();self.event('ready');old=self.start()['ticket'];self.send('cancel');self.event('cancelled');self.start()
        current=dict(self.ticket)
        self.send('cancel',**old);refused=self.event('refused');self.assertEqual(refused['ticket'],current)
        replay={'format':CONTROLLER.COMMAND,'session':self.session,'seq':self.seq,'op':'cancel',**current}
        self.process.stdin.write(P.encoded(replay));self.process.stdin.flush();self.event('refused')
        self.prepare();self.close()

    def test_changed_context_after_prepared_invalidates_cached_result(self):
        self.launch();self.event('ready');self.start();self.prepare()
        self.send('poll',context={**self.context,'frame':'13'});self.event('invalidated')
        self.assertIsNone(self.ticket['nonce']);self.close()

    def test_changed_receipt_after_prepared_is_refused(self):
        self.launch();self.event('ready');self.start();value=self.prepare()
        path=Path(value['job'])/'preview-receipt.json';receipt=json.loads(path.read_bytes());receipt['setup_members_built']=99;path.write_bytes(P.encoded(receipt))
        self.send('poll',context=self.context);self.event('refused');self.assertIsNone(self.ticket['nonce']);self.close()

    def test_eof_after_prepared_synchronously_invalidates_and_closes(self):
        self.launch();self.event('ready');self.start();self.prepare();self.process.stdin.close();self.process.wait(timeout=4)
        outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['reason'],'host input EOF');self.assertEqual(outcome['phase'],'stopped');self.assertIsNone(outcome['ticket']['nonce'])
        self.assertTrue(outcome['host_handle_closed']);self.assertTrue(outcome['job_closed']);self.assertTrue(outcome['process_handle_closed'])

    def test_strict_framing_types_and_foreign_session_cannot_start(self):
        self.launch();self.event('ready')
        frames=[b'{"seq":1,"seq":2}',b'{"value":NaN}',bytes([255]),P.encoded({'format':CONTROLLER.COMMAND,'session':self.session,'seq':True,'op':'start',**self.ticket}),P.encoded({'format':CONTROLLER.COMMAND,'session':'f'*32,'seq':1,'op':'start',**self.ticket})]
        for raw in frames:
            self.process.stdin.write(raw.rstrip(b'\n')+b'\n');self.process.stdin.flush();self.event('refused')
        self.assertEqual(self.ticket,{'generation':0,'nonce':None});self.assertFalse(any(self.owned.glob('*/request.json')));self.close()

    def test_oversized_unterminated_frame_closes_without_start(self):
        self.launch();self.event('ready');self.process.stdin.write(b'X'*(CONTROLLER.MAX_COMMAND+1));self.process.stdin.flush();self.process.wait(timeout=4)
        outcome=json.loads((self.owned/'controller-outcome.json').read_bytes());self.assertFalse(outcome['worker_started']);self.assertEqual(outcome['exit'],2)
        self.assertIn('transport error',outcome['reason'])

    def test_wrong_parent_incarnation_refuses_before_ready_or_child(self):
        parent=self.observer.identity(self.observer.current());parent['created_100ns']=str(int(parent['created_100ns'])+1)
        self.launch(parent=parent);self.process.wait(timeout=4);self.assertEqual(self.process.returncode,2)
        self.assertIsNone(self.events.get(timeout=3));self.assertFalse(any(self.owned.glob('*/request.json')))

    def test_abrupt_controller_death_before_assignment_gives_worker_eof(self):
        marker=self.root/'gated.json'
        code='def assign(self,process):\n job=process.args[process.args.index("--job")+1]\n Path('+repr(str(marker))+').write_text(json.dumps({"child":self.identity(process),"assigned":False,"gate_sent":False,"job":job}))\n while True:time.sleep(.05)\nC.A.NativeJob.assign=assign\n'
        self.launch(self.wrapper(code));self.event('ready')
        self.send('start',source=str(self.source),items=[request(self.glb)],context=self.context)
        evidence=self.marker(marker);child=self.observer.watch(evidence['child'])
        self.assertFalse(evidence['assigned']);self.assertFalse(evidence['gate_sent'])
        self.assertEqual(self.observer.identity(self.process._handle),self.controller_owner)
        self.process.kill();self.process.wait(timeout=4)
        result=self.observer.finish_watch(child,evidence['child'],'preassignment EOF after exact controller termination')
        self.assertTrue(result['signaled'],result);self.assertEqual(result['observed'],evidence['child'])
        self.assertFalse((Path(evidence['job'])/'candidate').exists())

    def test_abrupt_controller_death_after_assignment_kills_nonreading_worker(self):
        wrapper,marker=self.postassignment_wrapper();self.launch(wrapper);self.event('ready');self.start()
        evidence=self.marker(marker);self.assertTrue(evidence['assigned']);self.assertTrue(evidence['inside_exact_job'])
        self.marker(Path(evidence['job'])/'awake.json');child=self.observer.watch(evidence['child'])
        self.assertEqual(self.observer.wait(child,0),258)
        self.assertEqual(self.observer.identity(self.process._handle),self.controller_owner)
        self.process.kill();self.process.wait(timeout=4)
        result=self.observer.finish_watch(child,evidence['child'],'kill-on-last-Job-close after exact controller termination')
        self.assertTrue(result['signaled'],result);self.assertTrue(result['observer_handle_closed'])

    def test_declared_host_death_closes_live_job_without_poll(self):
        host=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(30)'],close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
        self.processes.append(host);owner=self.observer.identity(host._handle)
        host._observer_owner=owner;host._observer_label='declared host'
        wrapper,marker=self.postassignment_wrapper();self.launch(wrapper,parent=owner);self.event('ready');self.start()
        evidence=self.marker(marker);self.marker(Path(evidence['job'])/'awake.json');child=self.observer.watch(evidence['child'])
        self.assertEqual(self.observer.identity(host._handle),owner);host.kill();host.wait(timeout=4)
        self.process.wait(timeout=4);result=self.observer.finish_watch(child,evidence['child'],'declared host lease ended')
        self.assertTrue(result['signaled']);outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['reason'],'host process ended');self.assertTrue(outcome['host_handle_closed']);self.assertTrue(outcome['job_closed']);self.assertTrue(outcome['process_handle_closed'])

    def test_unread_output_backpressure_still_closes_owned_child(self):
        wrapper,marker=self.postassignment_wrapper();self.launch(wrapper,read_events_limit=2);self.event('ready');self.start()
        evidence=self.marker(marker);self.marker(Path(evidence['job'])/'awake.json');child=self.observer.watch(evidence['child'])
        for _ in range(50):
            try:self.send('poll',context=self.context)
            except (BrokenPipeError,OSError):break
            if self.process.poll() is not None:break
            time.sleep(.025)
        self.process.wait(timeout=4)
        observed=self.observer.finish_watch(child,evidence['child'],'output backpressure closes owned Job')
        self.assertTrue(observed['signaled']);outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['exit'],2);self.assertTrue(outcome['job_closed']);self.assertTrue(outcome['process_handle_closed'])
        self.assertFalse(outcome['prepared_exposed'])

    def test_eof_while_worker_not_reading_stdin_closes_job(self):
        wrapper,marker=self.postassignment_wrapper();self.launch(wrapper);self.event('ready');self.start()
        evidence=self.marker(marker);self.marker(Path(evidence['job'])/'awake.json');child=self.observer.watch(evidence['child'])
        self.process.stdin.close();self.process.wait(timeout=4)
        self.assertTrue(self.observer.finish_watch(child,evidence['child'],'controller command EOF closes Job')['signaled'])
        outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['reason'],'host input EOF');self.assertTrue(outcome['job_closed']);self.assertTrue(outcome['process_handle_closed'])

    def test_controller_and_python_pin_mismatch_refuse_before_start(self):
        for key in ('controller-sha256','python-sha256'):
            with self.subTest(pin=key):
                self.launch(**{key:'0'*64});self.process.wait(timeout=4)
                self.assertEqual(self.process.returncode,2);self.assertIsNone(self.events.get(timeout=3))
                self.assertFalse(any(self.owned.glob('*/request.json')))

    def host_process(self):
        host=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(30)'],close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
        self.processes.append(host);owner=self.observer.identity(host._handle)
        host._observer_owner=owner;host._observer_label='declared host';return host,owner

    def test_host_loss_during_start_prevalidation_never_launches_worker(self):
        host,owner=self.host_process();marker=self.root/'hash-block.json';release=self.root/'release'
        body='old=C.P.make_envelope\ndef make(*args,**kwargs):\n result=old(*args,**kwargs)\n Path('+repr(str(marker))+').write_text(json.dumps({"blocked":True}))\n while not Path('+repr(str(release))+').exists():time.sleep(.01)\n return result\nC.P.make_envelope=make\n'
        self.launch(self.wrapper(body),parent=owner);self.event('ready')
        self.send('start',source=str(self.source),items=[request(self.glb)],context=self.context);self.marker(marker)
        host.kill();host.wait(timeout=4);release.write_text('release');self.process.wait(timeout=4)
        outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['reason'],'host process ended');self.assertFalse(outcome['worker_started'])
        self.assertFalse(any(self.owned.glob('*/request.json')))

    def test_host_loss_during_receipt_check_never_exposes_prepared(self):
        host,owner=self.host_process();marker=self.root/'receipt-block.json';release=self.root/'release'
        body='old=C.P.check_receipt\ndef check(*args,**kwargs):\n result=old(*args,**kwargs)\n Path('+repr(str(marker))+').write_text(json.dumps({"blocked":True}))\n while not Path('+repr(str(release))+').exists():time.sleep(.01)\n return result\nC.P.check_receipt=check\n'
        self.launch(self.wrapper(body),parent=owner);self.event('ready');self.start()
        self.send('poll',context=self.context)
        # The first poll can still observe a running child. Keep polling only
        # until the controlled receipt gate is reached.
        until=time.monotonic()+4
        while not marker.exists() and time.monotonic()<until:
            try:
                event=self.events.get(timeout=.05)
                if event and event.get('event')=='running':
                    time.sleep(.015);self.send('poll',context=self.context)
            except queue.Empty:pass
        self.marker(marker);host.kill();host.wait(timeout=4);release.write_text('release');self.process.wait(timeout=4)
        outcome=json.loads((self.owned/'controller-outcome.json').read_bytes())
        self.assertEqual(outcome['reason'],'host process ended');self.assertFalse(outcome['prepared_exposed'])
        self.assertTrue(outcome['job_closed']);self.assertTrue(outcome['process_handle_closed']);self.assertEqual(outcome['phase'],'stopped')


if __name__=='__main__':
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controllers))
    report={'format':'has_wind_preview_controller_cpu_tests_1','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'skipped':len(result.skipped),'passed':result.wasSuccessful(),'folder':str(RUN),'real_hidden_windows_python_processes':True,
            'godot_started':False,'gpu_used':False,'native_converter_started':False,'main_or_prior_packet_modified':False}
    (OUT/'cpu-tests.log').write_text(stream.getvalue(),encoding='utf-8');(OUT/'cpu-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(stream.getvalue());print(json.dumps(report,indent=2));raise SystemExit(0 if result.wasSuccessful() else 1)
