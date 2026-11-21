"""Pure fake bootstrap regressions. No window, process, SDK or native execution."""
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_map_bootstrap_tested',HERE/'map_prepare_bootstrap.py')
B=importlib.util.module_from_spec(spec);sys.modules[spec.name]=B;spec.loader.exec_module(B)

def role(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.folder=Path(self.temp.name)
        script=self.folder/'prepare.py';script.write_text('pass\n',encoding='utf8')
        self.config={'format':'has_map_prepare_hidden_bootstrap_1','worker':role(script),'sentinel':role(script),'preparer':role(script),
                     'args':['original.bsp','--output',str(self.folder/'bundle')],'placement':str(self.folder/'placement.json'),
                     'environment':{key:'1' if key in {'PYTHONDONTWRITEBYTECODE','NO_BPY'} else str(self.folder/key) for key in B.ENV_KEYS}}
        self.policy={'format':'has_hidden_background_desktop_placement_sentinel_1','destroyed_in_finally':False}
        self.events=[];self.original_path=list(sys.path);self.original_argv=sys.argv
    def tearDown(self):
        sys.path[:]=self.original_path;sys.argv=self.original_argv;self.temp.cleanup()
    @contextmanager
    def fake_window(self):
        self.events.append('window_created')
        try:yield self.policy
        finally:self.policy['destroyed_in_finally']=True;self.events.append('window_destroyed')
    def run_fake(self,runner):
        environment={'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'safe.directory','GIT_CONFIG_VALUE_0':'','UNTREATED_EMPTY':''}
        with patch.object(B.os,'environ',environment),patch.object(B,'load_factory',return_value=self.fake_window),patch.object(B.runpy,'run_path',side_effect=runner):
            B.execute(self.config)
        return environment
    def test_success_holds_window_during_ordinary_preparer_and_closes(self):
        def runner(path,run_name):
            self.events.append('preparer')
            self.assertEqual(path,self.config['preparer']['path']);self.assertEqual(run_name,'__main__')
            self.assertEqual(sys.argv,[path,*self.config['args']]);self.assertFalse(self.policy['destroyed_in_finally'])
        self.run_fake(runner)
        self.assertEqual(self.events,['window_created','preparer','window_destroyed'])
        value=json.loads(Path(self.config['placement']).read_text())
        self.assertTrue(value['worker_verified_hidden_sentinel_closed']);self.assertTrue(value['placement_is_for_root_python_preparer'])
        self.assertFalse(value['blender_gui_or_render_claim']);self.assertIs(sys.argv,self.original_argv)
    def test_present_but_empty_git_values_are_untouched(self):
        env=self.run_fake(lambda *a,**kw:None)
        self.assertIn('GIT_CONFIG_VALUE_0',env);self.assertEqual(env['GIT_CONFIG_VALUE_0'],'')
        self.assertIn('UNTREATED_EMPTY',env);self.assertEqual(env['UNTREATED_EMPTY'],'')
        self.assertEqual(env['GIT_CONFIG_COUNT'],'1');self.assertEqual(env['GIT_CONFIG_KEY_0'],'safe.directory')
    def test_ordinary_success_exit_keeps_zero_and_still_closes(self):
        original=SystemExit(0)
        with self.assertRaises(SystemExit) as caught:self.run_fake(lambda *a,**kw:(_ for _ in ()).throw(original))
        self.assertIs(caught.exception,original);self.assertEqual(caught.exception.code,0)
        self.assertTrue(json.loads(Path(self.config['placement']).read_text())['worker_verified_hidden_sentinel_closed'])
    def test_source_failure_is_not_converted_to_success(self):
        original=RuntimeError('owned fake conversion failure')
        with self.assertRaises(RuntimeError) as caught:self.run_fake(lambda *a,**kw:(_ for _ in ()).throw(original))
        self.assertIs(caught.exception,original);self.assertTrue(self.policy['destroyed_in_finally'])
        self.assertEqual(self.events,['window_created','window_destroyed'])
    def test_preparer_pin_drift_refuses_before_window_and_environment(self):
        self.config['preparer']['sha256']='0'*64
        with patch.object(B,'load_factory') as factory,patch.object(B.os,'environ',{}) as env:
            with self.assertRaisesRegex(ValueError,'^BOOTSTRAP_SOURCE_PIN_DIFFERS$'):B.execute(self.config)
        factory.assert_not_called();self.assertEqual(env,{})
    def test_git_key_cannot_be_added_to_owned_environment(self):
        self.config['environment']['GIT_CONFIG_VALUE_0']='replacement'
        with patch.object(B,'load_factory') as factory:
            with self.assertRaisesRegex(ValueError,'^BOOTSTRAP_ENV_SCHEMA$'):B.execute(self.config)
        factory.assert_not_called()
    def test_wrong_known_factory_source_pin_refuses_without_execution(self):
        with self.assertRaisesRegex(ValueError,'^BOOTSTRAP_KNOWN_SOURCE_REQUIRED$'):B.load_factory(self.config)
        self.assertFalse(Path(self.config['placement']).exists())
    def test_parent_has_no_environment_writes_and_preserves_strict_placement(self):
        source=(HERE/'run_map_retest.py').read_text(encoding='utf8');tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Attribute):
                self.assertFalse(isinstance(node.func.value.value,ast.Name) and node.func.value.value.id=='os' and node.func.value.attr=='environ')
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                for target in node.targets if isinstance(node,ast.Assign) else [node.target]:
                    self.assertFalse(isinstance(target,ast.Subscript) and isinstance(target.value,ast.Attribute) and isinstance(target.value.value,ast.Name) and target.value.value.id=='os' and target.value.attr=='environ')
        self.assertIn("proof.get('child_desktop_confirmed') is True",source)
        self.assertIn("proof.get('private_window_seen') is True",source)
        self.assertIn("policy.get(key) is True",source);self.assertIn("policy.get(key) is False",source)
    def test_all28_qualified_light_patch_pins_stay_exact(self):
        source=(HERE/'run_map_retest.py').read_text(encoding='utf8')
        self.assertIn("8319,'284971f27040335b727c7a94639920cb6b1e37a37645ec8f553a704f1522eb5b'",source)
        self.assertIn("30697,'cc5a205772c83949bcc10f06633a73d83664c455e8daad163c06dba7a26dc60e'",source)
if __name__=='__main__':unittest.main()
