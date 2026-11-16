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


# These cases supplement SnapshotTests; Git is entirely mocked in this class.
class RuntimeScopeTests(unittest.TestCase):
    def setUp(self):
        parent=ROOT/'output';parent.mkdir(exist_ok=True)
        self.temporary=tempfile.TemporaryDirectory(prefix='runtime-snapshot-mock-',dir=parent)
        self.root=Path(self.temporary.name)
        self.assertTrue(self.root.resolve().is_relative_to(parent.resolve()))
        self.files={
            'main.tscn':b'[ext_resource path="res://src/main.gd"]\r\n',
            'project.godot':b'config/icon="res://assets/icons/app.svg"\n',
            'run.py':b'from tools.relative_module import main\n',
            'launch.pyw':b'from run import main\n',
            'src/main.gd':b'preload("res://shaders/surface.gdshader")\n',
            'tests/world_selection_teardown.gd':b'OLD SHARED TEST\n',
            'tests/negative.gd':b'"res://does-not-exist"\n"res://output/private.has"\n"res://"\n"res://catalogue/models/"\n"res://not-catalogued.gd"\n',
            'tests/web.gd':b'preload("res://web/small.gd")\n',
            'tools/relative_module.py':b'def main():return 0\n',
            'data/definition.json':b'{"value":1}\n',
            'examples/procedural.bin':b'\x00\x01synthetic fixture\r\n',
            'shaders/surface.gdshader':b'"res://textures/palette.tres"\n',
            'textures/palette.tres':b'[resource]\n',
            'assets/icons/app.svg':b'<svg/>\n',
            'catalogue/models/one.txt':b'one\n',
            'catalogue/models/two.txt':b'two\n',
            'web/small.gd':b'"res://web/palette.tres"\n',
            'web/palette.tres':b'[resource]\n',
            'THIRD_PARTY_NOTICES.md':b'notice\n',
            'docs/licenses.md':b'licenses\n',
            'docs/unrelated-audit.md':b'unrelated evidence\n',
            'experiments/old-proof.json':b'{"unrelated":true}\n',
            'output/private.has':b'never include\n',
            '.godot/cache':b'never include\n',
            'tools/__pycache__/old.pyc':b'never include\n',
        }
        for name,body in self.files.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
        (self.root/'not-catalogued.gd').write_bytes(b'not in Git candidate list\n')
        self.commit='a'*40
        self.calls=[];self.extra_rows=[];self.malformed_batch=None;self.concurrent=False

    def tearDown(self):
        # Only this checked disposable fixture tree is removed.
        self.assertTrue(self.root.resolve().is_relative_to((ROOT/'output').resolve()))
        self.temporary.cleanup()

    @staticmethod
    def oid(body):
        return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest().encode()

    def fake_git(self,args,**kwargs):
        self.calls.append((list(args),kwargs.get('input')))
        self.assertEqual(Path(kwargs['cwd']),self.root)
        verb=args[1]
        if verb=='rev-parse':
            if args[-1]=='missing^{commit}':raise subprocess.CalledProcessError(128,args)
            return self.commit+'\n'
        if verb=='ls-files':return ('\0'.join(sorted(self.files))+'\0').encode()
        if verb=='ls-tree':
            rows=[b'100644 blob '+self.oid(body)+b'\t'+name.encode()+b'\0' for name,body in sorted(self.files.items())]
            return b''.join(rows+self.extra_rows)
        if verb=='cat-file':
            if self.concurrent:
                (self.root/'snapshot').mkdir();(self.root/'snapshot/owner.txt').write_bytes(b'keep concurrent data')
                self.concurrent=False
            if self.malformed_batch is not None:return self.malformed_batch
            bodies={self.oid(body):body for body in self.files.values()}
            return b''.join(oid+b' blob '+str(len(bodies[oid])).encode()+b'\n'+bodies[oid]+b'\n' for oid in kwargs['input'].splitlines())
        raise AssertionError('Unexpected process request: '+repr(args))

    def freeze(self,revision=None,**kwargs):
        with patch('tools.build_owner_review_snapshot.subprocess.check_output',side_effect=self.fake_git):
            return freeze_source(self.root,self.root/'snapshot',revision,**kwargs)

    def test_runtime_seeds_and_transitive_literal_dependency_closure(self):
        commit,hashes=self.freeze(runtime_scope=True)
        self.assertEqual(commit,self.commit)
        expected=set(self.files)-{'docs/unrelated-audit.md','experiments/old-proof.json','output/private.has','.godot/cache','tools/__pycache__/old.pyc'}
        self.assertEqual(set(hashes),expected)
        for name in hashes:
            self.assertEqual((self.root/'snapshot'/name).read_bytes(),self.files[name])
            self.assertEqual(hashes[name],hashlib.sha256(self.files[name]).hexdigest())
        self.assertFalse((self.root/'snapshot/not-catalogued.gd').exists())
        self.assertEqual([call[0][1] for call in self.calls],['rev-parse','ls-files'])

    def test_default_working_scope_retains_unrelated_source(self):
        _,hashes=self.freeze()
        self.assertIn('experiments/old-proof.json',hashes)
        self.assertIn('docs/unrelated-audit.md',hashes)
        self.assertNotIn('output/private.has',hashes)

    def test_default_revision_scope_retains_unrelated_source(self):
        _,hashes=self.freeze(self.commit)
        self.assertIn('experiments/old-proof.json',hashes)
        self.assertIn('docs/unrelated-audit.md',hashes)
        self.assertEqual(sum(call[0][1]=='cat-file' for call in self.calls),1)

    def test_runtime_revision_uses_old_blob_closure_ignoring_working_bytes(self):
        (self.root/'main.tscn').write_bytes(b'"res://experiments/old-proof.json"\n')
        (self.root/'project.godot').write_bytes(b'working changed\n')
        (self.root/'shaders/surface.gdshader').unlink()
        _,hashes=self.freeze(self.commit,runtime_scope=True)
        self.assertEqual((self.root/'snapshot/main.tscn').read_bytes(),self.files['main.tscn'])
        self.assertEqual((self.root/'snapshot/project.godot').read_bytes(),self.files['project.godot'])
        self.assertIn('textures/palette.tres',hashes)
        self.assertNotIn('experiments/old-proof.json',hashes)
        fetched=b''.join(data for args,data in self.calls if args[1]=='cat-file')
        self.assertNotIn(self.oid(self.files['experiments/old-proof.json'])+b'\n',fetched)
        self.assertNotIn(self.oid(self.files['docs/unrelated-audit.md'])+b'\n',fetched)

    def test_old_revision_baseline_and_current_shared_test_remain_separate(self):
        name='tests/world_selection_teardown.gd';current=b'CURRENT SHARED TEST\n'
        (self.root/name).write_bytes(current)
        _,hashes=self.freeze(self.commit,runtime_scope=True);baseline=hashes.copy()
        target=self.root/'snapshot'/name;target.write_bytes((self.root/name).read_bytes())
        hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(baseline[name],hashlib.sha256(self.files[name]).hexdigest())
        self.assertEqual(hashes[name],hashlib.sha256(current).hexdigest())
        self.assertNotEqual(hashes[name],baseline[name])

    def test_existing_target_is_preserved(self):
        target=self.root/'snapshot';target.mkdir();(target/'owner.txt').write_bytes(b'keep')
        with self.assertRaisesRegex(AssertionError,'Studio must not exist'):self.freeze(runtime_scope=True)
        self.assertEqual((target/'owner.txt').read_bytes(),b'keep')
        self.assertEqual(self.calls,[])

    def test_unsafe_catalogue_names_refused_before_copy_even_outside_scope(self):
        for name in ['../escape.gd','src/../escape.gd','docs/con.py','src/a.gd:stream','src//a.gd','src/./a.gd','MAIN.TSCN']:
            with self.subTest(name=name):
                self.extra_rows=[b'100644 blob '+self.oid(b'bad')+b'\t'+name.encode()+b'\0']
                with self.assertRaises(AssertionError):self.freeze(self.commit,runtime_scope=True)
                self.assertFalse((self.root/'snapshot').exists())

    def test_unsupported_revision_entry_still_refused_outside_scope(self):
        self.extra_rows=[b'120000 blob '+self.oid(b'link')+b'\tdocs/link\0']
        with self.assertRaisesRegex(AssertionError,'Unsupported snapshot entry'):self.freeze(self.commit,runtime_scope=True)
        self.assertFalse((self.root/'snapshot').exists())

    def test_runtime_requires_all_four_entrypoints(self):
        del self.files['launch.pyw']
        with self.assertRaisesRegex(AssertionError,'Missing runtime application entry points'):self.freeze(runtime_scope=True)
        self.assertFalse((self.root/'snapshot').exists())

    def test_runtime_scope_is_keyword_only_and_explicit_bool(self):
        with self.assertRaises(TypeError):freeze_source(self.root,self.root/'snapshot',None,True)
        with self.assertRaisesRegex(AssertionError,'explicit bool'):self.freeze(runtime_scope=1)
        self.assertFalse((self.root/'snapshot').exists())

    def test_malformed_git_batch_refused_before_copy(self):
        self.malformed_batch=b'0'*40+b' blob 1\nx\n'
        with self.assertRaisesRegex(AssertionError,'Unexpected Git blob response'):self.freeze(self.commit,runtime_scope=True)
        self.assertFalse((self.root/'snapshot').exists())

    def test_concurrent_destination_is_never_replaced(self):
        self.concurrent=True
        with self.assertRaises(FileExistsError):self.freeze(self.commit,runtime_scope=True)
        self.assertEqual((self.root/'snapshot/owner.txt').read_bytes(),b'keep concurrent data')

    def test_bad_revision_creates_nothing(self):
        with self.assertRaises(subprocess.CalledProcessError):self.freeze('missing',runtime_scope=True)
        self.assertFalse((self.root/'snapshot').exists())

    def test_literal_resource_can_include_an_explicit_evidence_dependency(self):
        # Scope excludes evidence by default, not resources actually referenced.
        self.files['src/main.gd']=b'"res://experiments/old-proof.json"\n'
        (self.root/'src/main.gd').write_bytes(self.files['src/main.gd'])
        _,hashes=self.freeze(runtime_scope=True)
        self.assertIn('experiments/old-proof.json',hashes)
        self.assertNotIn('docs/unrelated-audit.md',hashes)


if __name__=='__main__':unittest.main()
