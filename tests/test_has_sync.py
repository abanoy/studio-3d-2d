"""HAS parent/owned-sidecar syncing and post-promotion outcome faults."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest import mock
from tests import test_has_project as fixtures
has=fixtures.has


class HasSyncTests(unittest.TestCase):
    def fixture(self,directory):
        root=Path(directory);request,name,source=fixtures.HasTests().fixture(root)
        return root,request,name,source

    @unittest.skipUnless(os.name=='posix','POSIX directory fd sync; native Windows gate remains')
    def test_new_archive_parents_are_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            root,request,_,_=self.fixture(directory);target=root/'created'/'projects'/'Film.has';request['path']=str(target)
            observed=[];original=has.os.fsync
            def sync(handle):
                info=os.fstat(handle);observed.append((info.st_dev,info.st_ino));return original(handle)
            with mock.patch.object(has.os,'fsync',side_effect=sync):result=has.pack(request)
            self.assertTrue(result['ok']);self.assertTrue(result['directory_synced'])
            for path in [target.parent,target.parent.parent,root]:
                info=path.stat();self.assertIn((info.st_dev,info.st_ino),observed)

    @unittest.skipUnless(os.name=='posix','POSIX sidecar fd sync; native Windows gate remains')
    def test_owned_externalized_sidecar_and_directory_are_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            root,request,name,source=self.fixture(directory);cache=Path(request['cache_root']);cache.mkdir();cached=cache/'model.glb';cached.write_bytes(source.read_bytes());request['references'][name]=str(cached);request['storage']='linked'
            observed=[];original=has.os.fsync
            def sync(handle):
                info=os.fstat(handle);observed.append((info.st_dev,info.st_ino));return original(handle)
            with mock.patch.object(has.os,'fsync',side_effect=sync):result=has.pack(request)
            sidecar=Path(request['path']).with_suffix('.assets')
            self.assertTrue(result['ok']);self.assertTrue(result['owned_sidecars_synced'])
            for path in [sidecar,sidecar/Path(name).name]:
                info=path.stat();self.assertIn((info.st_dev,info.st_ino),observed)

    def test_pre_promotion_directory_sync_failure_keeps_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root,request,_,_=self.fixture(directory);has.pack(request);target=Path(request['path']);before=target.read_bytes()
            with mock.patch.object(has,'sync_directory',side_effect=OSError('injected directory sync failure')):
                with self.assertRaises(OSError):has.pack(request)
            self.assertEqual(target.read_bytes(),before)

    def test_post_promotion_sync_failure_reports_written_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root,request,_,_=self.fixture(directory)
            with mock.patch.object(has,'sync_directory',side_effect=[True,OSError('injected final sync failure')]):result=has.pack(request)
            self.assertFalse(result['ok']);self.assertTrue(result['committed']);self.assertIn('HAS file was written',result['error'])
            self.assertTrue(has.unpack({'path':request['path'],'folder':str(root/'reopened')})['ok'])

    @unittest.skipUnless(os.name=='posix','Owned sidecar link fixture; native Windows gate remains')
    def test_linked_managed_sidecar_folder_refuses_before_emitting_external_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root,request,name,source=self.fixture(directory);cache=Path(request['cache_root']);cache.mkdir();cached=cache/'model.glb';cached.write_bytes(source.read_bytes());request['references'][name]=str(cached);request['storage']='linked'
            outside=root/'outside-originals';outside.mkdir();(outside/'keep.txt').write_bytes(b'ORIGINAL')
            Path(request['path']).with_suffix('.assets').symlink_to(outside,target_is_directory=True)
            with self.assertRaisesRegex(has.HasError,'Linked managed sidecar'):has.pack(request)
            self.assertEqual(sorted(p.name for p in outside.iterdir()),['keep.txt']);self.assertEqual((outside/'keep.txt').read_bytes(),b'ORIGINAL')
            self.assertFalse(Path(request['path']).exists())


if __name__=='__main__':unittest.main()
