"""Real hidden Python CPU-child lifecycle tests; no Godot/native conversion."""
from pathlib import Path
import copy
import importlib.util
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import unittest
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parents[1]; ROOT = OUT.parents[1]
sys.path[:0] = [str(OUT / 'candidate/tools'), str(ROOT / 'tools'), str(ROOT / 'tests')]
from test_secondary_helpers import two_panel_fixture, request
import wind_helper_preview as P
import wind_preview_owned as A
RUN = OUT / 'cpu-results' / uuid.uuid4().hex


@unittest.skipUnless(os.name == 'nt', 'Windows owned-child adapter')
class OwnedCPUWorker(unittest.TestCase):
    def setUp(self):
        # CreateProcess still rejects a long cwd on this host; keep owned test
        # paths short while retaining the full testcase name in its receipt.
        self.root = RUN / hashlib.sha256(self._testMethodName.encode()).hexdigest()[:12]
        self.root.mkdir(parents=True, exist_ok=False)
        (self.root / 'testcase.json').write_text(json.dumps({'test': self._testMethodName})+'\n', encoding='utf-8')
        self.source = self.root / 'authored.glb'; self.glb = two_panel_fixture(self.source)
        self.before = P.identity(self.source); owned = self.root / 'jobs'; owned.mkdir()
        self.context = {'actor_id': 'fixture', 'root_instance_id': str(2**63+1), 'revision': '8', 'frame': '12',
                        'authored_sha256': 'a'*64, 'shape_sha256': 'b'*64, 'bindings_sha256': 'c'*64}
        self.lease = P.DraftLease(owned)
        self.token = self.lease.begin(self.source, [request(self.glb), dict(request(self.glb), component=1)], self.context, 'included-batch')
        self.adapter = A.OwnedPreviewJob(self.lease, ROOT, timeout=5)
        self.addCleanup(self.adapter.close)

    def finish(self, context=None):
        until = time.monotonic()+10
        while time.monotonic()<until:
            result = self.adapter.poll(context or self.context)
            if result['state'] != 'running': return result
            time.sleep(.01)
        self.fail('CPU test watchdog')

    def wrapper(self, body):
        path = self.root / ('cpu-wrapper-' + uuid.uuid4().hex + '.py')
        header = 'import sys,time,json,subprocess\nfrom pathlib import Path\nsys.path.insert(0,' + repr(str(OUT / 'candidate/tools')) + ')\nimport wind_preview_worker as W\n'
        path.write_text(header + body, encoding='utf-8')
        original = self.adapter.command
        def command(job):
            args = original(job); args[4] = str(path); return args
        return command

    def wait_file(self, path):
        until = time.monotonic()+4
        while time.monotonic()<until:
            if path.is_file(): return
            time.sleep(.01)
        self.fail('CPU marker watchdog: '+str(path))

    def test_real_child_exit_pipe_identity_and_hidden_candidate(self):
        owner = self.adapter.start(self.token); result = self.finish()
        self.assertEqual(result['state'], 'prepared_hidden', result)
        self.assertEqual(result['receipt']['setup_members_built'], 2)
        self.assertTrue(result['job_closed']); self.assertTrue(result['process_handle_closed'])
        self.assertGreater(owner['pid'], 0); self.assertTrue(owner['created_100ns'].isdigit())
        self.assertEqual(P.identity(self.source), self.before); self.assertEqual(self.lease.phase, 'prepared_hidden')

    def test_foreign_imported_worker_is_refused_before_helper_calls(self):
        with patch.object(A.worker, '__file__', str(self.root / 'foreign_worker.py')), patch.object(A.worker, 'file_sha') as sha:
            with self.assertRaisesRegex(ValueError, 'different wind_preview_worker'):
                A.OwnedPreviewJob(self.lease, ROOT)
        sha.assert_not_called(); self.assertEqual(self.lease.phase, 'building')
        self.assertFalse((self.token['job'] / 'owned-launch.json').exists())

    def test_cancellation_uses_exact_current_owner_and_never_admits(self):
        owner = self.adapter.start(self.token)
        with self.assertRaisesRegex(ValueError, 'Stale cancellation'):
            self.adapter.cancel({**owner, 'created_100ns': str(int(owner['created_100ns'])+1)})
        self.assertEqual(self.adapter.state, 'running')
        self.assertTrue(self.adapter.cancel(owner)); self.assertEqual(self.adapter.state, 'cancelled')
        self.assertIsNone(self.adapter.receipt); self.assertEqual(self.lease.phase, 'stopped')
        self.assertTrue(self.adapter.job_closed); self.assertTrue(self.adapter.handle_closed)
        self.assertEqual(P.identity(self.source), self.before)

    def test_context_change_cancels_owned_child(self):
        self.adapter.start(self.token); result = self.finish({**self.context, 'frame': '13'})
        self.assertEqual(result['state'], 'cancelled'); self.assertIsNone(result['receipt'])
        self.assertEqual(self.lease.phase, 'stopped'); self.assertTrue(self.adapter.job_closed)

    def test_timeout_of_gated_worker_closes_job(self):
        self.adapter.timeout = .05
        with patch.object(self.adapter, '_send_start', return_value=None): self.adapter.start(self.token)
        result = self.finish(); self.assertEqual(result['state'], 'cancelled', result)
        self.assertIn('timed out', result['error']); self.assertTrue(self.adapter.job_closed)
        self.assertTrue(self.adapter.handle_closed); self.assertIsNone(self.adapter.receipt)

    def test_assignment_failure_sends_no_start_and_reaps_child(self):
        with patch.object(A.NativeJob, 'assign', side_effect=OSError('CPU controlled assignment failure')), patch.object(self.adapter, '_send_start') as send:
            with self.assertRaisesRegex(OSError, 'assignment failure'): self.adapter.start(self.token)
        send.assert_not_called(); self.assertIsNone(self.adapter.process)
        self.assertTrue(self.adapter.job_closed); self.assertTrue(self.adapter.handle_closed)
        self.assertFalse((self.token['job'] / 'candidate').exists())

    def test_valid_completion_then_nonzero_exit_cannot_admit(self):
        with patch.object(self.adapter, 'command', self.wrapper('W.main()\nraise SystemExit(7)\n')):
            self.adapter.start(self.token)
        result = self.finish(); self.assertEqual(result['state'], 'failed', result)
        self.assertIn('exited 7', result['error']); self.assertIsNone(self.adapter.receipt)
        self.assertTrue(self.adapter.job_closed); self.assertTrue(self.adapter.handle_closed)

    def test_buffered_valid_completion_then_hang_is_cancelled(self):
        body = 'W.main()\njob=Path(sys.argv[sys.argv.index("--job")+1])\n(job/"packet-sent").write_text("yes")\ntime.sleep(10)\n'
        with patch.object(self.adapter, 'command', self.wrapper(body)):
            owner = self.adapter.start(self.token)
        self.wait_file(self.token['job'] / 'packet-sent')
        self.adapter.cancel(owner, 'cancel after buffered completion')
        self.assertIsNone(self.adapter.receipt); self.assertEqual(self.lease.phase, 'stopped')
        self.assertTrue(self.adapter.readers[0].data.startswith(A.worker.PREFIX))

    def test_late_old_generation_and_stale_cancel_do_not_affect_replacement(self):
        old_owner = self.adapter.start(self.token)
        newer = self.lease.begin(self.source, [request(self.glb)], self.context)
        result = self.finish(); self.assertEqual(result['state'], 'cancelled', result)
        self.assertEqual(self.lease.pending, newer); self.assertEqual(self.lease.phase, 'building')
        self.adapter.start(newer)
        with self.assertRaisesRegex(ValueError, 'Stale cancellation'): self.adapter.cancel(old_owner)
        result = self.finish(); self.assertEqual(result['state'], 'prepared_hidden', result)
        self.assertEqual(result['receipt']['generation'], newer['generation'])

    def test_source_stamp_change_after_worker_completion_is_refused(self):
        self.adapter.start(self.token); self.wait_file(self.token['job'] / 'preview-receipt.json')
        item = self.source.stat(); os.utime(self.source, ns=(item.st_atime_ns, item.st_mtime_ns+1_000_000))
        result = self.finish(); self.assertEqual(result['state'], 'failed', result)
        self.assertIn('source changed', result['error']); self.assertIsNone(self.adapter.receipt)

    def test_receipt_change_after_worker_publication_is_refused(self):
        self.adapter.start(self.token); path = self.token['job'] / 'preview-receipt.json'; self.wait_file(path)
        value = json.loads(path.read_bytes()); value['setup_members_built'] = 99; path.write_bytes(P.encoded(value))
        result = self.finish(); self.assertEqual(result['state'], 'failed', result)
        self.assertIn('receipt changed', result['error']); self.assertIsNone(self.adapter.receipt)
        self.assertTrue(self.adapter.job_closed); self.assertTrue(self.adapter.handle_closed)

    def test_source_hash_drift_before_admission_is_refused(self):
        self.adapter.start(self.token); self.wait_file(self.token['job'] / 'preview-receipt.json')
        original = A.worker.file_sha
        def drift(path):
            return '0'*64 if Path(path).name == 'wind_helper_preview.py' else original(path)
        with patch.object(A.worker, 'file_sha', side_effect=drift): result = self.finish()
        self.assertEqual(result['state'], 'failed', result); self.assertIn('source changed', result['error'])
        self.assertIsNone(self.adapter.receipt)

    def test_python_fingerprint_drift_before_admission_is_refused(self):
        self.adapter.start(self.token); self.wait_file(self.token['job'] / 'preview-receipt.json')
        original = A.worker.file_sha
        def drift(path): return '0'*64 if Path(path) == self.adapter.python else original(path)
        with patch.object(A.worker, 'file_sha', side_effect=drift): result = self.finish()
        self.assertEqual(result['state'], 'failed', result); self.assertIn('Python fingerprint changed', result['error'])

    def test_stdout_framing_identity_and_both_pipe_caps_fail_closed(self):
        behaviors = {
            'duplicate': 'old=W.emit\nW.emit=lambda packet:(old(packet),old(packet))\nraise SystemExit(W.main())\n',
            'trailing': 'W.main()\nsys.stdout.buffer.write(b"trailing");sys.stdout.buffer.flush()\n',
            'invalid-utf8': 'W.main()\nsys.stdout.buffer.write(bytes([255]));sys.stdout.buffer.flush()\n',
            'foreign-pid': 'old=W.emit\ndef emit(packet):\n packet["owner"]["pid"]+=4\n old(packet)\nW.emit=emit\nraise SystemExit(W.main())\n',
            'foreign-created': 'old=W.emit\ndef emit(packet):\n packet["owner"]["created_100ns"]="1"\n old(packet)\nW.emit=emit\nraise SystemExit(W.main())\n',
            'foreign-generation': 'old=W.emit\ndef emit(packet):\n packet["completion"]["generation"]+=1\n old(packet)\nW.emit=emit\nraise SystemExit(W.main())\n',
            'stdout-cap': 'sys.stdout.buffer.write(b"X"*20000);sys.stdout.buffer.flush()\nraise SystemExit(W.main())\n',
            'stderr-cap': 'sys.stderr.buffer.write(b"X"*300000);sys.stderr.buffer.flush()\nraise SystemExit(W.main())\n',
            'unexpected-stderr': 'sys.stderr.write("unexpected diagnostic\\n");sys.stderr.flush()\nraise SystemExit(W.main())\n'
        }
        for label, body in behaviors.items():
            with self.subTest(case=label):
                if self.adapter.process is not None: self.adapter.close()
                self.token = self.lease.begin(self.source, [request(self.glb)], self.context)
                with patch.object(self.adapter, 'command', self.wrapper(body)): self.adapter.start(self.token)
                result = self.finish(); self.assertIn(result['state'], ('failed', 'cancelled'), result)
                self.assertIsNone(self.adapter.receipt); self.assertTrue(self.adapter.job_closed); self.assertTrue(self.adapter.handle_closed)
                self.assertLessEqual(len(self.adapter.readers[0].data), A.MAX_STDOUT)
                self.assertLessEqual(len(self.adapter.readers[1].data), A.MAX_STDERR)

    def test_job_close_failure_refuses_admission_and_can_finish_cleanup(self):
        self.adapter.start(self.token)
        original = self.adapter.native.close
        with patch.object(self.adapter.native, 'close', side_effect=OSError('CPU close failure')):
            result = self.finish()
        self.assertEqual(result['state'], 'failed'); self.assertIsNone(self.adapter.receipt)
        self.assertFalse(self.adapter.job_closed); self.adapter.close(); self.assertTrue(self.adapter.job_closed)

    def test_one_process_job_blocks_descendant_launch(self):
        body = 'job=Path(sys.argv[sys.argv.index("--job")+1])\nmarker=job/"descendant-ran"\nblocked=False\ntry:\n child=subprocess.Popen([sys.executable,"-c","from pathlib import Path;Path("+repr(str(marker))+").write_text(\\"bad\\")"],creationflags=subprocess.CREATE_NO_WINDOW)\n code=child.wait(timeout=3);child._handle.Close();blocked=code!=0\nexcept OSError:\n blocked=True\n(job/"descendant-check.json").write_text(json.dumps({"blocked":blocked,"ran":marker.exists()}))\nraise SystemExit(W.main())\n'
        with patch.object(self.adapter, 'command', self.wrapper(body)): self.adapter.start(self.token)
        result = self.finish(); self.assertEqual(result['state'], 'prepared_hidden', result)
        evidence = json.loads((self.token['job'] / 'descendant-check.json').read_bytes())
        self.assertTrue(evidence['blocked']); self.assertFalse(evidence['ran'])


if __name__ == '__main__':
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OwnedCPUWorker))
    report = {'format': 'has_wind_owned_cpu_adapter_tests_1', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'passed': result.wasSuccessful(), 'folder': str(RUN), 'real_python_children': True,
              'godot_started': False, 'gpu_used': False, 'native_converter_started': False,
              'main_or_frozen_packet_modified': False, 'scope': 'CPU owned-child/process/packet candidate only'}
    (OUT / 'cpu-tests.log').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'cpu-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(stream.getvalue()); print(json.dumps(report,indent=2)); raise SystemExit(0 if result.wasSuccessful() else 1)
