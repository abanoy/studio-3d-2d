"""Owned bounded metadata sync/replacement faults; no physical power-loss claim."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from tools import metadata_commit as mc

ROOT = Path(__file__).resolve().parents[1]


class MetadataCommitTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)
        target = root / 'progress.json'
        temporary = root / 'progress.json.prepared.tmp'
        before = b'{"old":1}'
        data = b'{"new":2}'
        target.write_bytes(before); temporary.write_bytes(data)
        args = (root, target, temporary, hashlib.sha256(data).hexdigest(), root)
        return root, args, before, data

    def test_exact_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, data = self.fixture(directory)
            self.assertTrue(mc.commit(*args)['ok'])
            self.assertEqual(args[1].read_bytes(), data)
            self.assertFalse(args[2].exists())

    def test_changed_or_oversized_temporary_preserves_prior_state(self):
        for data in [b'changed', b'x' * (mc.MAX_META + 1)]:
            with self.subTest(bytes=len(data)), tempfile.TemporaryDirectory() as directory:
                root, args, before, _ = self.fixture(directory)
                args[2].write_bytes(data)
                with self.assertRaises(mc.HasError): mc.commit(*args)
                self.assertEqual(args[1].read_bytes(), before)

    def test_failed_file_sync_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _ = self.fixture(directory)
            with mock.patch.object(mc.os, 'fsync', side_effect=OSError('injected sync failure')):
                with self.assertRaises(OSError): mc.commit(*args)
            self.assertEqual(args[1].read_bytes(), before)

    def test_changed_after_sync_refuses_before_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _ = self.fixture(directory)
            original = mc.os.fsync
            def corrupt(handle):
                original(handle); args[2].write_bytes(b'corrupt')
            with mock.patch.object(mc.os, 'fsync', side_effect=corrupt):
                with self.assertRaises(mc.HasError): mc.commit(*args)
            self.assertEqual(args[1].read_bytes(), before)

    def test_replace_failure_preserves_prior_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _ = self.fixture(directory)
            with mock.patch.object(mc.os, 'replace', side_effect=PermissionError('injected replace denial')):
                with self.assertRaises(PermissionError): mc.commit(*args)
            self.assertEqual(args[1].read_bytes(), before)

    def test_post_commit_sync_failure_reports_new_file_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, data = self.fixture(directory)
            with mock.patch.object(mc, 'sync_directory', side_effect=[True, OSError('injected final sync failure')]):
                result = mc.commit(*args)
            self.assertFalse(result['ok']); self.assertTrue(result['committed'])
            self.assertIn('file was written', result['error']); self.assertEqual(args[1].read_bytes(), data)

    @unittest.skipUnless(os.name == 'posix', 'Owned symlink fixture; native Windows gate remains')
    def test_linked_final_temporary_or_legacy_temp_preserves_original(self):
        for which in [1, 2, 'legacy']:
            with self.subTest(which=which), tempfile.TemporaryDirectory() as directory:
                root, args, _, _ = self.fixture(directory)
                original = root / 'source-original'; original.write_bytes(b'ORIGINAL')
                target = Path(str(args[1])+'.tmp') if which=='legacy' else args[which]
                if target.exists(): target.unlink()
                target.symlink_to(original)
                with self.assertRaises(mc.HasError): mc.commit(*args)
                self.assertEqual(original.read_bytes(), b'ORIGINAL'); self.assertTrue(target.is_symlink())

    @unittest.skipUnless(os.name == 'posix', 'Owned hard-link fixture; native Windows gate remains')
    def test_hardlinked_final_preserves_external_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, data = self.fixture(directory)
            original = root / 'source-original'; original.write_bytes(before)
            args[1].unlink(); os.link(original, args[1]); stamp = original.stat().st_mtime_ns
            self.assertTrue(mc.commit(*args)['ok']); self.assertEqual(args[1].read_bytes(), data)
            self.assertEqual(original.read_bytes(), before); self.assertEqual(original.stat().st_mtime_ns, stamp)

    @unittest.skipUnless(os.name == 'posix', 'Owned hard-link fixture; native Windows gate remains')
    def test_hardlinked_temporary_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, data = self.fixture(directory)
            original = root / 'source-original'; original.write_bytes(data)
            args[2].unlink(); os.link(original, args[2])
            with self.assertRaises(mc.HasError): mc.commit(*args)
            self.assertEqual(args[1].read_bytes(), before); self.assertEqual(original.read_bytes(), data)

    def test_outside_root_or_unowned_temporary_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _ = self.fixture(directory)
            for target, temporary in [(root.parent / 'outside.json', args[2]),
                                      (args[1], root / 'unowned.tmp')]:
                with self.subTest(target=target), self.assertRaises(ValueError):
                    mc.commit(root, target, temporary, args[3], root)
            self.assertEqual(args[1].read_bytes(), before)

    @unittest.skipUnless(os.name == 'posix', 'POSIX parent fd sync fixture; Windows gate remains')
    def test_all_created_private_parents_are_synced(self):
        with tempfile.TemporaryDirectory() as directory:
            boundary = Path(directory)
            root = boundary / 'created' / 'private'
            target = root / 'course' / 'session' / 'progress.json'
            target.parent.mkdir(parents=True)
            temporary = Path(str(target)+'.prepared.tmp'); data = b'new progress'; temporary.write_bytes(data)
            observed=[]; original=mc.os.fsync
            def sync(handle):
                info=os.fstat(handle);observed.append((info.st_dev,info.st_ino));return original(handle)
            with mock.patch.object(mc.os,'fsync',side_effect=sync):
                result=mc.commit(root,target,temporary,hashlib.sha256(data).hexdigest(),boundary)
            self.assertTrue(result['ok']);self.assertTrue(result['directory_synced'])
            directories=mc.parents([target.parent,root],boundary)
            for path in directories:
                info=path.stat();self.assertIn((info.st_dev,info.st_ino),observed)
            self.assertEqual(result['directories_synced'],len(directories))

    def test_cli_unicode_path_is_data_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'private ✓';root.mkdir();root,args,_,data=self.fixture(root)
            result=subprocess.run([sys.executable,str(ROOT/'tools/metadata_commit.py'),*map(str,args)],capture_output=True,text=True,encoding='utf-8',timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok']);self.assertEqual(args[1].read_bytes(),data)


if __name__=='__main__':unittest.main()
