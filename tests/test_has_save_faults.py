"""Owned archive fault injection; no native assets or physical disk exhaustion."""
from pathlib import Path
import errno,io,json,os,signal,subprocess,sys,tempfile,unittest,zipfile
from contextlib import contextmanager
from unittest import mock
from tests import test_has_project as fixtures
has=fixtures.has

class SaveFaultTests(unittest.TestCase):
    def setup_save(self,root):
        request,_,_=fixtures.HasTests().fixture(root);has.pack(request);target=Path(request['path']);before=target.read_bytes()
        return request,target,before

    def damage_after_sync(self,request,kind):
        original=has.os.fsync
        def corrupt(fd):
            original(fd);target=Path(request['path']);candidates=list(target.parent.glob(target.name+'.*.tmp'));self.assertEqual(len(candidates),1);path=candidates[0]
            if kind=='truncate':path.write_bytes(path.read_bytes()[:40]);return
            with zipfile.ZipFile(path) as archive:rows={name:archive.read(name) for name in archive.namelist()}
            if kind=='pixels':
                name=next(name for name in rows if name.startswith('cels/'));data=rows[name];rows[name]=bytes([data[0]^1])+data[1:]
            else:
                header=json.loads(rows['has.json']);header['storage']='broken';rows['has.json']=has.json_bytes(header)
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for name,data in rows.items():archive.writestr(name,data)
            path.write_bytes(buffer.getvalue())
        return corrupt

    def test_corrupted_completed_payload_preserves_previous_save(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory))
            with mock.patch.object(has.os,'fsync',side_effect=self.damage_after_sync(request,'pixels')):
                with self.assertRaises((has.HasError,zipfile.BadZipFile)):has.pack(request)
            self.assertEqual(target.read_bytes(),before)
            self.assertFalse(Path(str(target)+'.backup').exists())

    def test_truncated_completed_archive_preserves_previous_save(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory))
            with mock.patch.object(has.os,'fsync',side_effect=self.damage_after_sync(request,'truncate')):
                with self.assertRaises((has.HasError,zipfile.BadZipFile)):has.pack(request)
            self.assertEqual(target.read_bytes(),before)

    def test_changed_completed_header_preserves_previous_save(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory))
            with mock.patch.object(has.os,'fsync',side_effect=self.damage_after_sync(request,'header')):
                with self.assertRaises((has.HasError,zipfile.BadZipFile)):has.pack(request)
            self.assertEqual(target.read_bytes(),before)

    def test_bad_previous_payload_cannot_replace_valid_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,target,before=self.setup_save(root);backup=Path(str(target)+'.backup');backup.write_bytes(before)
            with zipfile.ZipFile(target) as archive:rows={name:archive.read(name) for name in archive.namelist()}
            name=next(name for name in rows if name.startswith('cels/'));data=rows[name];rows[name]=bytes([data[0]^1])+data[1:]
            with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for name,data in rows.items():archive.writestr(name,data)
            with zipfile.ZipFile(target) as archive:self.assertIsNone(archive.testzip())
            has.pack(request);self.assertEqual(backup.read_bytes(),before)
            self.assertTrue(has.unpack({'path':str(target),'folder':str(root/'repaired')})['ok'])

    def test_disk_full_during_payload_write_preserves_save_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory));backup=Path(str(target)+'.backup');backup.write_bytes(before);original=has.zipfile.ZipFile.open
            @contextmanager
            def faulty(archive,name,mode='r',*args,**kwargs):
                with original(archive,name,mode,*args,**kwargs) as stream:
                    if mode=='w' and str(name).startswith('cels/'):
                        class Writer:
                            def write(self,data):
                                stream.write(data[:max(1,len(data)//2)]);raise OSError(errno.ENOSPC,'injected disk full during payload write')
                        yield Writer()
                    else:yield stream
            with mock.patch.object(has.zipfile.ZipFile,'open',faulty):
                with self.assertRaises(OSError):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    def test_disk_full_at_sync_preserves_save_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory));backup=Path(str(target)+'.backup');backup.write_bytes(before)
            with mock.patch.object(has.os,'fsync',side_effect=OSError(errno.ENOSPC,'injected sync disk full')):
                with self.assertRaises(OSError):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    @unittest.skipUnless(os.name=='posix','Owned symbolic-link fixture; Windows reparse gate remains')
    def test_linked_save_destinations_preserve_original_and_saved_files(self):
        for suffix in ('', '.backup', '.backup.tmp'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,target,before=self.setup_save(root)
                original=root/'original.bin';original.write_bytes(b'ORIGINAL')
                destination=Path(str(target)+suffix)
                if destination.exists():destination.unlink()
                destination.symlink_to(original)
                with self.assertRaisesRegex(has.HasError,'Linked save destination'):has.pack(request)
                self.assertEqual(original.read_bytes(),b'ORIGINAL');self.assertTrue(destination.is_symlink())
                if suffix:self.assertEqual(target.read_bytes(),before)

    @unittest.skipUnless(os.name=='posix','Owned hard-link fixture; Windows native gate remains')
    def test_hard_linked_legacy_backup_temporary_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,target,before=self.setup_save(root)
            original=root/'original.bin';original.write_bytes(b'ORIGINAL')
            legacy=Path(str(target)+'.backup.tmp');os.link(original,legacy)
            has.pack(request)
            self.assertEqual(original.read_bytes(),b'ORIGINAL');self.assertEqual(legacy.read_bytes(),b'ORIGINAL')
            self.assertEqual(Path(str(target)+'.backup').read_bytes(),before)

    def test_corrupted_backup_readback_preserves_both_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,target,before=self.setup_save(root)
            backup=Path(str(target)+'.backup');backup.write_bytes(before);original=has.os.fsync
            def corrupt(fd):
                original(fd)
                for path in root.glob(target.name+'.backup.*.tmp'):path.write_bytes(b'corrupt backup')
            with mock.patch.object(has.os,'fsync',side_effect=corrupt):
                with self.assertRaisesRegex(has.HasError,'changed during copying'):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    @unittest.skipUnless(os.name=='posix','Actual process lock/kill fixture; native Windows gate remains')
    def test_live_writer_refuses_overlap_and_os_releases_after_exit_or_sigkill(self):
        script="""import sys
from pathlib import Path
from tools import has_project as has
with has.save_lock(Path(sys.argv[1])):
    print('LOCKED',flush=True)
    sys.stdin.readline()
"""
        for killed in (False,True):
            with self.subTest(killed=killed),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,target,before=self.setup_save(root);backup=Path(str(target)+'.backup');backup.write_bytes(before)
                child=subprocess.Popen([sys.executable,'-c',script,str(target)],cwd=Path(__file__).resolve().parents[1],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                try:
                    self.assertEqual(child.stdout.readline().strip(),'LOCKED')
                    with self.assertRaisesRegex(has.HasError,'Another save'):has.pack(request)
                    self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)
                    self.assertEqual(list(root.glob(target.name+'.*.tmp')),[])
                    if killed:child.kill()
                    else:child.stdin.write('release\n');child.stdin.flush()
                    child.wait(timeout=10)
                    self.assertEqual(child.returncode,-signal.SIGKILL if killed else 0)
                    has.pack(request)
                    self.assertEqual(backup.read_bytes(),before)
                    self.assertTrue(has.unpack({'path':str(target),'folder':str(root/'reopened')})['ok'])
                finally:
                    if child.poll() is None:child.kill();child.wait(timeout=10)
                    child.stdin.close();child.stdout.close();child.stderr.close()

    @unittest.skipUnless(os.name=='posix','Owned lock-link fixtures; native Windows gate remains')
    def test_linked_or_hardlinked_lock_cannot_modify_original(self):
        for hard in (False,True):
            with self.subTest(hard=hard),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,target,before=self.setup_save(root);lock=Path(str(target)+'.lock');lock.unlink()
                original=root/'original';original.write_bytes(b'ORIGINAL')
                if hard:os.link(original,lock)
                else:lock.symlink_to(original)
                with self.assertRaises(has.HasError):has.pack(request)
                self.assertEqual(original.read_bytes(),b'ORIGINAL');self.assertEqual(target.read_bytes(),before)

    def test_backup_copy_failure_preserves_both_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory));backup=Path(str(target)+'.backup');backup.write_bytes(before)
            with mock.patch.object(has,'checked_copy',side_effect=OSError(errno.ENOSPC,'injected backup disk full')):
                with self.assertRaises(OSError):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    def test_backup_replace_failure_preserves_both_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory));backup=Path(str(target)+'.backup');backup.write_bytes(before);original=has.os.replace
            def replace(source,destination):
                if Path(destination)==backup:raise PermissionError('injected backup replace denial')
                return original(source,destination)
            with mock.patch.object(has.os,'replace',side_effect=replace):
                with self.assertRaises(PermissionError):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    def test_final_replace_failure_preserves_current_and_verified_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            request,target,before=self.setup_save(Path(directory));original=has.os.replace
            def replace(source,destination):
                if Path(destination)==target:raise PermissionError('injected final replace denial')
                return original(source,destination)
            with mock.patch.object(has.os,'replace',side_effect=replace):
                with self.assertRaises(PermissionError):has.pack(request)
            self.assertEqual(target.read_bytes(),before);self.assertEqual(Path(str(target)+'.backup').read_bytes(),before)

    def test_cancellation_during_readback_preserves_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);request,target,before=self.setup_save(root);backup=Path(str(target)+'.backup');backup.write_bytes(before);cancel=root/'cancel';request['cancel']=str(cancel);verify=has.verify_written_archive;check=has.check_cancel;calls=0
            def validate(*args):
                def cancel_after_first_payload(request):
                    nonlocal calls
                    calls+=1
                    if calls==3:cancel.write_text('cancel')
                    return check(request)
                with mock.patch.object(has,'check_cancel',side_effect=cancel_after_first_payload):return verify(*args)
            with mock.patch.object(has,'verify_written_archive',side_effect=validate):
                with self.assertRaisesRegex(has.HasError,'cancelled'):has.pack(request)
            self.assertGreaterEqual(calls,3);self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)

    @unittest.skipUnless(os.name=='posix','Actual SIGKILL boundary requires POSIX; Windows termination remains an external platform gate')
    def test_actual_sigkill_before_backup_and_final_replace_preserves_saves(self):
        script="""import json,os,signal,sys
from pathlib import Path
from unittest import mock
from tools import has_project as has
request=json.loads(sys.argv[1]);target=Path(request['path']);stage=sys.argv[2];original=has.os.replace
boundary=Path(str(target)+'.backup') if stage=='backup' else target
def replace(source,destination):
    if Path(destination)==boundary:os.kill(os.getpid(),signal.SIGKILL)
    return original(source,destination)
with mock.patch.object(has.os,'replace',side_effect=replace):has.pack(request)
"""
        for stage in ('backup','target'):
            with self.subTest(stage=stage),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);request,target,before=self.setup_save(root);backup=Path(str(target)+'.backup');backup.write_bytes(before)
                result=subprocess.run([sys.executable,'-c',script,json.dumps(request),stage],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,-signal.SIGKILL,result.stdout+result.stderr);self.assertEqual(target.read_bytes(),before);self.assertEqual(backup.read_bytes(),before)
                self.assertTrue(has.unpack({'path':str(target),'folder':str(root/'reopened')})['ok'])
                pending=[p for p in root.glob(target.name+'.*.tmp') if not p.name.startswith(target.name+'.backup.')];self.assertEqual(len(pending),1)
                if stage=='backup':
                    backups=list(root.glob(target.name+'.backup.*.tmp'));self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),before)
                self.assertTrue(has.unpack({'path':str(pending[0]),'folder':str(root/'verified-pending')})['ok'])

if __name__=='__main__':unittest.main()
