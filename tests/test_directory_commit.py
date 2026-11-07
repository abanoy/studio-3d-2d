"""Owned directory-commit faults and real cooperating-process overlap/termination."""
from pathlib import Path
import errno
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from tools import directory_commit as dc

ROOT = Path(__file__).resolve().parents[1]


class DirectoryCommitTests(unittest.TestCase):
    def fixture(self, directory):
        root = Path(directory)
        before = b'{"schema_version":4,"generation":"before"}'
        backup = b'{"schema_version":4,"generation":"older"}'
        candidate = b'{"schema_version":4,"generation":"new"}'
        (root / 'project.json').write_bytes(before)
        (root / 'project.backup.json').write_bytes(backup)
        name = 'project.json.prepared.tmp'
        (root / name).write_bytes(candidate)
        args = (root, name, dc.sha(root / 'project.json'), dc.sha(root / name), True)
        return root, args, before, backup, candidate

    def intact(self, root, before, backup):
        self.assertEqual((root / 'project.json').read_bytes(), before)
        self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    def test_valid_commit_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _, candidate = self.fixture(directory)
            result = dc.commit(*args)
            self.assertTrue(result['ok'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)
            self.assertEqual((root / 'project.backup.json').read_bytes(), before)
            self.assertFalse((root / args[1]).exists())

    def test_first_save_without_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, candidate = self.fixture(directory)
            (root / 'project.json').unlink()
            (root / 'project.backup.json').unlink()
            self.assertTrue(dc.commit(root, args[1], '', args[3], False)['ok'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)
            self.assertFalse((root / 'project.backup.json').exists())

    def test_conflicting_generation_preserves_committed_save_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, backup, _ = self.fixture(directory)
            changed = b'{"schema_version":4,"generation":"another writer"}'
            (root / 'project.json').write_bytes(changed)
            with self.assertRaisesRegex(dc.HasError, 'Another save changed'):
                dc.commit(*args)
            self.intact(root, changed, backup)
            self.assertTrue((root / args[1]).exists())

    def test_candidate_damage_refuses_before_rotation(self):
        for data, recompute in [(b'{', True), (b'[]', True), (b'{"schema_version":true}', True),
                                (b'{"schema_version":4,"bad":NaN}', True),
                                (b'x' * (dc.MAX_META + 1), True), (b'changed', False)]:
            with self.subTest(data=data[:30]), tempfile.TemporaryDirectory() as directory:
                root, args, before, backup, _ = self.fixture(directory)
                (root / args[1]).write_bytes(data)
                digest = dc.sha(root / args[1]) if recompute else args[3]
                with self.assertRaises((ValueError, dc.HasError)):
                    dc.commit(root, args[1], args[2], digest, True)
                self.intact(root, before, backup)

    def test_invalid_candidate_address_cannot_promote_other_files(self):
        for name in ['../source.json', 'assets/source.glb', 'project.json', '/tmp/source.json']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root, args, before, backup, _ = self.fixture(directory)
                with self.assertRaises(dc.HasError):
                    dc.commit(root, name, args[2], args[3], True)
                self.intact(root, before, backup)

    @unittest.skipUnless(os.name == 'posix', 'Owned link fixture; native Windows gate remains')
    def test_symlinked_destinations_never_change_original(self):
        for name in ['project.json', 'project.backup.json', 'project.json.prepared.tmp',
                     'project.json.tmp', 'project.backup.json.tmp', 'project.json.lock']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root, args, _, _, _ = self.fixture(directory)
                original = root / 'source-original'
                original.write_bytes(b'ORIGINAL')
                path = root / name
                if path.exists(): path.unlink()
                path.symlink_to(original)
                with self.assertRaises(dc.HasError): dc.commit(*args)
                self.assertEqual(original.read_bytes(), b'ORIGINAL')
                self.assertTrue(path.is_symlink())

    @unittest.skipUnless(os.name == 'posix', 'Owned hard-link fixture; native Windows gate remains')
    def test_hardlinked_backup_replacement_preserves_original_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, _ = self.fixture(directory)
            original = root / 'source-original'
            original.write_bytes(backup)
            (root / 'project.backup.json').unlink()
            os.link(original, root / 'project.backup.json')
            self.assertTrue(dc.commit(*args)['ok'])
            self.assertEqual(original.read_bytes(), backup)
            self.assertEqual((root / 'project.backup.json').read_bytes(), before)

    @unittest.skipUnless(os.name == 'posix', 'Owned hard-link fixture; native Windows gate remains')
    def test_hardlinked_candidate_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, candidate = self.fixture(directory)
            original = root / 'source-original'
            original.write_bytes(candidate)
            (root / args[1]).unlink()
            os.link(original, root / args[1])
            with self.assertRaises(dc.HasError): dc.commit(*args)
            self.intact(root, before, backup)
            self.assertEqual(original.read_bytes(), candidate)

    def test_sync_failure_before_promotion_preserves_both_saved_generations(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, _ = self.fixture(directory)
            with mock.patch.object(dc.os, 'fsync', side_effect=OSError(errno.ENOSPC, 'injected sync failure')):
                with self.assertRaises(OSError): dc.commit(*args)
            self.intact(root, before, backup)

    def test_corruption_after_sync_is_detected_before_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, _ = self.fixture(directory)
            original = dc.os.fsync
            def corrupt(handle):
                original(handle)
                (root / args[1]).write_bytes(b'corrupt')
            with mock.patch.object(dc.os, 'fsync', side_effect=corrupt):
                with self.assertRaises(dc.HasError): dc.commit(*args)
            self.intact(root, before, backup)

    def test_failed_backup_replace_preserves_both_generations(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, _ = self.fixture(directory)
            original = dc.os.replace
            def replace(source, target):
                if Path(target).name == 'project.backup.json': raise PermissionError('injected backup replace denial')
                return original(source, target)
            with mock.patch.object(dc.os, 'replace', side_effect=replace):
                with self.assertRaises(PermissionError): dc.commit(*args)
            self.intact(root, before, backup)

    def test_failed_primary_replace_preserves_current_and_verified_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _, _ = self.fixture(directory)
            original = dc.os.replace
            def replace(source, target):
                if Path(target).name == 'project.json': raise PermissionError('injected primary replace denial')
                return original(source, target)
            with mock.patch.object(dc.os, 'replace', side_effect=replace):
                with self.assertRaises(PermissionError): dc.commit(*args)
            self.intact(root, before, before)

    def test_final_sync_failure_reports_that_new_generation_was_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _, candidate = self.fixture(directory)
            with mock.patch.object(dc, 'sync_directory', side_effect=[True, OSError('injected final sync failure')]):
                result = dc.commit(*args)
            self.assertFalse(result['ok']); self.assertTrue(result['committed'])
            self.assertIn('Project was written', result['error'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)
            self.assertEqual((root / 'project.backup.json').read_bytes(), before)

    def test_invalid_previous_manifest_keeps_existing_good_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, backup, candidate = self.fixture(directory)
            (root / 'project.json').write_bytes(b'{')
            self.assertTrue(dc.commit(root, args[1], dc.sha(root / 'project.json'), args[3], False)['ok'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)
            self.assertEqual((root / 'project.backup.json').read_bytes(), backup)

    @unittest.skipUnless(os.name == 'posix', 'Actual process overlap and SIGKILL fixture; Windows gate remains')
    def test_real_competing_process_refuses_then_retries_after_sigkill(self):
        script = """import sys
from pathlib import Path
from tools.has_project import save_lock
with save_lock(Path(sys.argv[1])):
 print('LOCKED',flush=True)
 sys.stdin.readline()
"""
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, backup, candidate = self.fixture(directory)
            child = subprocess.Popen([sys.executable, '-c', script, str(root / 'project.json')], cwd=ROOT,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'LOCKED')
                with self.assertRaisesRegex(dc.HasError, 'Another save'): dc.commit(*args)
                self.intact(root, before, backup)
                child.kill(); child.wait(timeout=10)
                self.assertEqual(child.returncode, -signal.SIGKILL)
                self.assertTrue(dc.commit(*args)['ok'])
                self.assertEqual((root / 'project.json').read_bytes(), candidate)
            finally:
                if child.poll() is None: child.kill(); child.wait(timeout=10)
                child.stdin.close(); child.stdout.close(); child.stderr.close()

    @unittest.skipUnless(os.name == 'posix', 'POSIX directory-sync fixture; native Windows gate remains')
    def test_unsupported_directory_sync_is_explicit_and_does_not_break_save(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, candidate = self.fixture(directory)
            original = dc.os.fsync
            import stat
            def sync(handle):
                if stat.S_ISDIR(os.fstat(handle).st_mode): raise OSError(errno.EINVAL, 'injected unsupported directory sync')
                return original(handle)
            with mock.patch.object(dc.os, 'fsync', side_effect=sync):
                result = dc.commit(*args)
            self.assertTrue(result['ok']); self.assertFalse(result['directory_synced'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)

    @unittest.skipUnless(os.name == 'posix', 'Actual worker SIGKILL boundaries; native Windows gate remains')
    def test_actual_worker_kill_preserves_a_valid_committed_generation(self):
        script = """import json,os,signal,sys
from pathlib import Path
from unittest import mock
from tools import directory_commit as dc
args=json.loads(sys.argv[1]);stage=sys.argv[2];original=dc.os.replace
boundary=Path(args[0])/('project.backup.json' if stage=='backup' else 'project.json')
def replace(source,target):
 if Path(target)==boundary:
  if stage=='after':original(source,target)
  os.kill(os.getpid(),signal.SIGKILL)
 return original(source,target)
with mock.patch.object(dc.os,'replace',side_effect=replace):dc.commit(*args)
"""
        for stage in ('backup', 'primary', 'after'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                root, args, before, backup, candidate = self.fixture(directory)
                job = (str(root), *args[1:])
                result = subprocess.run([sys.executable, '-c', script, json.dumps(job), stage], cwd=ROOT,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, -signal.SIGKILL, result.stdout + result.stderr)
                self.assertEqual((root / 'project.json').read_bytes(), candidate if stage=='after' else before)
                self.assertEqual((root / 'project.backup.json').read_bytes(), backup if stage=='backup' else before)
                json.loads((root / 'project.json').read_bytes())
                if stage!='after': self.assertTrue(dc.commit(*args)['ok'])

    def test_whole_valued_json_schema_versions_remain_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, _ = self.fixture(directory)
            old = b'{"schema_version":4.0,"generation":"old"}'
            candidate = b'{"schema_version":4.0,"generation":"new"}'
            (root / 'project.json').write_bytes(old)
            (root / args[1]).write_bytes(candidate)
            self.assertTrue(dc.commit(root, args[1], dc.sha(root / 'project.json'), dc.sha(root / args[1]), True)['ok'])
            self.assertEqual((root / 'project.backup.json').read_bytes(), old)
            self.assertEqual((root / 'project.json').read_bytes(), candidate)

    @unittest.skipUnless(os.name == 'posix', 'Actual two-worker fixture; native Windows gate remains')
    def test_two_real_prepared_writers_commit_only_one_starting_generation(self):
        script = """import json,sys
from tools.directory_commit import commit
args=json.loads(sys.argv[1]);print('READY',flush=True);sys.stdin.readline()
try:print(json.dumps(commit(*args)),flush=True)
except (ValueError,OSError,RuntimeError) as error:print(json.dumps({'ok':False,'error':str(error)}),flush=True)
"""
        with tempfile.TemporaryDirectory() as directory:
            root, args, before, _, candidate = self.fixture(directory)
            second_name = 'project.json.second.tmp'
            second = b'{"schema_version":4,"generation":"second"}'
            (root / second_name).write_bytes(second)
            jobs = [(str(root), args[1], args[2], args[3], True),
                    (str(root), second_name, args[2], dc.sha(root / second_name), True)]
            children = []
            try:
                for job in jobs:
                    child = subprocess.Popen([sys.executable, '-c', script, json.dumps(job)], cwd=ROOT,
                                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    children.append(child)
                    self.assertEqual(child.stdout.readline().strip(), 'READY')
                for child in children: child.stdin.write('commit\n'); child.stdin.flush()
                results = []
                for child in children:
                    child.wait(timeout=10); self.assertEqual(child.returncode, 0)
                    results.append(json.loads(child.stdout.read()))
                self.assertEqual(sum(result['ok'] for result in results), 1, results)
                self.assertEqual((root / 'project.backup.json').read_bytes(), before)
                self.assertIn((root / 'project.json').read_bytes(), (candidate, second))
                self.assertEqual(sum((root / job[1]).exists() for job in jobs), 1)
            finally:
                for child in children:
                    if child.poll() is None: child.kill(); child.wait(timeout=10)
                    child.stdin.close(); child.stdout.close(); child.stderr.close()

    def test_cli_new_project_uses_explicit_missing_token(self):
        with tempfile.TemporaryDirectory() as directory:
            root, args, _, _, candidate = self.fixture(directory)
            (root / 'project.json').unlink()
            result = subprocess.run([sys.executable, str(ROOT / 'tools/directory_commit.py'), str(root), args[1],
                                     'missing', args[3], 'no'], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)['ok'])
            self.assertEqual((root / 'project.json').read_bytes(), candidate)


if __name__ == '__main__':
    unittest.main()
