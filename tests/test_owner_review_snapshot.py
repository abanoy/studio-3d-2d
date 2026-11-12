"""A committed review must never pick up concurrent working-tree edits."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_owner_review_snapshot import freeze_source


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='review-snapshot-',dir=ROOT/'output')
        self.root=Path(self.temporary.name)
        self.git('init','-q')
        for name,data in {
            'main.tscn':b'original scene\r\n',
            'project.godot':b'original project\n',
            'run.py':b'original runner\n',
            'src/space and \u65e5\u672c.gd':b'\x00binary and exact CRLF\r\n',
            'output/private.has':b'never copy art',
            '.godot/cache':b'never copy cache',
            'tools/__pycache__/tool.pyc':b'never copy bytecode',
        }.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        self.git('add','-f','.')
        self.git('-c','user.name=Snapshot Test','-c','user.email=snapshot@example.invalid','commit','-qm','fixture')
        self.commit=self.git('rev-parse','HEAD').strip()

    def tearDown(self):
        self.temporary.cleanup()

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,text=True,encoding='utf-8',stderr=subprocess.PIPE)

    def test_revision_ignores_modified_staged_deleted_and_untracked_files(self):
        (self.root/'main.tscn').write_bytes(b'unreviewed')
        (self.root/'project.godot').write_bytes(b'unreviewed staged')
        self.git('add','project.godot')
        (self.root/'run.py').unlink()
        (self.root/'untracked.gd').write_bytes(b'unreviewed new')
        target=self.root/'snapshot'
        commit,hashes=freeze_source(self.root,target,self.commit)
        self.assertEqual(commit,self.commit)
        self.assertEqual(set(hashes),{'main.tscn','project.godot','run.py','src/space and \u65e5\u672c.gd'})
        for name,digest in hashes.items():
            expected=subprocess.check_output(['git','show',self.commit+':'+name],cwd=self.root)
            self.assertEqual((target/name).read_bytes(),expected)
            self.assertEqual(digest,hashlib.sha256(expected).hexdigest())
        self.assertFalse((target/'output').exists())
        self.assertFalse((target/'.godot').exists())
        self.assertEqual((self.root/'main.tscn').read_bytes(),b'unreviewed')
        self.assertFalse((self.root/'run.py').exists())

    def test_default_still_copies_working_files(self):
        (self.root/'main.tscn').write_bytes(b'working')
        (self.root/'untracked.gd').write_bytes(b'new working')
        target=self.root/'snapshot'
        commit,hashes=freeze_source(self.root,target)
        self.assertEqual(commit,self.commit)
        self.assertEqual((target/'main.tscn').read_bytes(),b'working')
        self.assertIn('untracked.gd',hashes)
        self.assertNotIn('output/private.has',hashes)

    def test_existing_destination_is_never_overwritten(self):
        target=self.root/'snapshot';target.mkdir();(target/'owner.txt').write_bytes(b'keep')
        with self.assertRaisesRegex(AssertionError,'Studio must not exist'):
            freeze_source(self.root,target,self.commit)
        self.assertEqual((target/'owner.txt').read_bytes(),b'keep')

    def test_bad_revision_creates_nothing(self):
        target=self.root/'snapshot'
        with self.assertRaises(subprocess.CalledProcessError):
            freeze_source(self.root,target,'missing-commit')
        self.assertFalse(target.exists())

    def test_committed_symlink_refused_before_copy(self):
        oid=self.git('rev-parse','HEAD:run.py').strip()
        self.git('update-index','--add','--cacheinfo','120000,'+oid+',linked.py')
        self.git('-c','user.name=Snapshot Test','-c','user.email=snapshot@example.invalid','commit','-qm','symlink fixture')
        target=self.root/'snapshot'
        with self.assertRaisesRegex(AssertionError,'Unsupported snapshot entry'):
            freeze_source(self.root,target,'HEAD')
        self.assertFalse(target.exists())

    def test_unsafe_windows_tree_names_refused_before_any_copy(self):
        original=subprocess.check_output
        oid=self.git('rev-parse','HEAD:run.py').strip()
        for name in ['D:outside.py','\\outside.py','nested\\escape.py','file.py:stream',
                     '../outside.py','/outside.py','con.py','a./b.py','trailing /b.py',
                     'src//b.py','src/./b.py','MAIN.TSCN']:
            with self.subTest(name=name):
                def fake_tree(args,**kwargs):
                    data=original(args,**kwargs)
                    if args[1]=='ls-tree':data+=('100644 blob '+oid+'\t'+name+'\0').encode()
                    return data
                target=self.root/'snapshot'
                with patch('tools.build_owner_review_snapshot.subprocess.check_output',side_effect=fake_tree):
                    with self.assertRaises(AssertionError):freeze_source(self.root,target,self.commit)
                self.assertFalse(target.exists())

    def test_target_created_during_git_read_is_preserved(self):
        original=subprocess.check_output;target=self.root/'snapshot'
        def concurrent_target(args,**kwargs):
            data=original(args,**kwargs)
            if args[1]=='cat-file':
                target.mkdir();(target/'owner.txt').write_bytes(b'concurrent owner data')
            return data
        with patch('tools.build_owner_review_snapshot.subprocess.check_output',side_effect=concurrent_target):
            with self.assertRaises(FileExistsError):freeze_source(self.root,target,self.commit)
        self.assertEqual(list(target.iterdir()),[target/'owner.txt'])
        self.assertEqual((target/'owner.txt').read_bytes(),b'concurrent owner data')


if __name__=='__main__':unittest.main()
