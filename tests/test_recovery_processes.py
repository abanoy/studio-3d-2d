import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import recovery_processes as recovery

BOOT='12345678-abcd-1234-abcd-123456789abc'


class LinuxProcParsingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.proc=Path(self.temp.name)
        boot=self.proc/'sys/kernel/random/boot_id';boot.parent.mkdir(parents=True);boot.write_text(BOOT+'\n')
        (self.proc/'self').mkdir();(self.proc/'self/stat').write_text('present')

    def stat(self,state='S',ticks='123456',comm='artist ) animation'):
        folder=self.proc/'42';folder.mkdir(exist_ok=True)
        (folder/'stat').write_text('42 ('+comm+') '+state+' '+' '.join(['0']*18+[ticks])+ '\n')

    def test_parentheses_and_exact_start_ticks(self):
        self.stat(ticks='123456789012345678')
        result=recovery.linux_details([42],self.proc)
        self.assertEqual(result['owners'],{'42':'alive'})
        self.assertEqual(result['linux_start'],{'42':BOOT+':123456789012345678'})
        self.assertEqual(result['created_100ns'],{})

    def test_zombie_is_exited_and_has_no_live_identity(self):
        for state in ['Z','X','x']:
            self.stat(state=state);result=recovery.linux_details([42],self.proc)
            self.assertEqual(result['owners']['42'],'exited');self.assertEqual(result['linux_start'],{})

    def test_missing_or_hidden_pid_needs_positive_exited_query(self):
        for error,wanted in [(ProcessLookupError(),'exited'),(PermissionError(),'unknown'),(None,'unknown')]:
            with self.subTest(error=error),patch.object(recovery.os,'kill',side_effect=error) as probe:
                result=recovery.linux_details([42],self.proc)
                self.assertEqual(result['owners']['42'],wanted);probe.assert_called_once_with(42,0)

    def test_missing_proc_mount_is_unknown(self):
        with patch.object(recovery.os,'kill') as probe:
            result=recovery.linux_details([42],self.proc/'missing')
            self.assertEqual(result['owners']['42'],'unknown');probe.assert_not_called()

    def test_bad_stat_is_unknown(self):
        for state,ticks in [('?', '42'),('S','0'),('S','1.0'),('S','-1'),('S','a'),('S','9'*21)]:
            self.stat(state,ticks)
            with self.subTest(state=state,ticks=ticks):self.assertEqual(recovery.linux_details([42],self.proc)['owners']['42'],'unknown')

    def test_missing_boot_preserves_liveness_without_inventing_identity(self):
        self.stat();(self.proc/'sys/kernel/random/boot_id').unlink()
        result=recovery.linux_details([42],self.proc)
        self.assertEqual(result['owners']['42'],'alive');self.assertEqual(result['linux_start'],{})

    def test_invalid_pid_never_issues_a_probe(self):
        with patch.object(recovery.os,'kill') as probe:
            for pid in [0,-1,True,'42',2147483648]:
                with self.subTest(pid=pid),self.assertRaises(ValueError):recovery.linux_details([pid],self.proc)
            probe.assert_not_called()

    @unittest.skipUnless(sys.platform=='linux','Linux /proc integration')
    def test_real_owned_child_alive_then_exited(self):
        child=subprocess.Popen([sys.executable,'-c','import sys;sys.stdin.buffer.read()'],stdin=subprocess.PIPE)
        try:
            live=recovery.details([os.getpid(),child.pid]);key=str(child.pid)
            self.assertEqual(live['owners'][key],'alive')
            self.assertRegex(live['linux_start'][key],r'^[0-9a-f-]{36}:[1-9][0-9]*$')
            self.assertEqual(recovery.details([child.pid])['linux_start'][key],live['linux_start'][key])
            child.stdin.close();child.wait(timeout=5)
            self.assertEqual(recovery.details([child.pid])['owners'][key],'exited')
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=5)


if __name__=='__main__':unittest.main()
