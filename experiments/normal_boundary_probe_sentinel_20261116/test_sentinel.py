"""Synthetic API fault injection only; never calls Win32 or loads Blender."""
from pathlib import Path
import ast,contextlib,ctypes,hashlib,json,sys,types,unittest
from ctypes import wintypes as W
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'normal_boundary_probe_20261116'

class Function:
    def __init__(self,api,name):self.api=api;self.name=name
    def __call__(self,*args):return self.api.call(self.name,*args)
class Library:
    def __init__(self,api):self.api=api
    def __getattr__(self,name):return Function(self.api,name)
class FakeC:
    c_int=ctypes.c_int;c_void_p=ctypes.c_void_p
    POINTER=staticmethod(ctypes.POINTER);byref=staticmethod(ctypes.byref)
    def __init__(self,api):self.api=api
    def WinDLL(self,*args,**kwargs):return Library(self.api)
    @staticmethod
    def get_last_error():return 5
class FakeAPI:
    def __init__(self):
        self.calls=[];self.active=False;self.visible=False;self.enabled=False
        self.bad_pid=False;self.bad_tid=False;self.bad_rect=False;self.bad_style=False;self.bad_exstyle=False
        self.fail_create=False;self.fail_destroy=False;self.destroy_calls=0
    def call(self,name,*args):
        self.calls.append((name,args))
        if name=='GetCurrentProcessId':return 44
        if name=='GetCurrentThreadId':return 55
        if name=='CreateWindowExW':
            if self.fail_create:return 0
            self.active=True;return 137
        if name=='IsWindow':return int(self.active)
        if name=='IsWindowVisible':return int(self.visible)
        if name=='IsWindowEnabled':return int(self.enabled)
        if name=='GetWindowThreadProcessId':
            args[1]._obj.value=45 if self.bad_pid else 44
            return 56 if self.bad_tid else 55
        if name=='GetWindowLongW':
            return (0 if self.bad_style else 0x88000000) if args[1]==-16 else (0 if self.bad_exstyle else 0x08000080)
        if name=='GetWindowRect':
            area=args[1]._obj;area.left=area.top=area.bottom=0;area.right=1 if self.bad_rect else 0;return 1
        if name=='DestroyWindow':
            self.destroy_calls+=1
            if self.fail_destroy:return 0
            self.active=False;return 1
        raise AssertionError('Unexpected API, including any show/activation/desktop switch: '+name)

def sentinel(api):
    tree=ast.parse((HERE/'capture_blender_normals.py').read_text())
    method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_hidden_placement_sentinel')
    unit=ast.Module(body=[method],type_ignores=[]);ast.fix_missing_locations(unit)
    namespace={'C':FakeC(api),'W':W,'sys':types.SimpleNamespace(platform='win32'),'contextmanager':contextlib.contextmanager}
    exec(compile(unit,'<synthetic-sentinel-only>','exec'),namespace)
    return namespace['_hidden_placement_sentinel']

class SentinelTests(unittest.TestCase):
    def test_success_policy_and_exact_creation(self):
        api=FakeAPI()
        with sentinel(api)() as policy:self.assertFalse(policy['destroyed_in_finally'])
        self.assertTrue(policy['destroyed_in_finally']);self.assertFalse(api.active)
        self.assertFalse(policy['visible_at_creation']);self.assertFalse(policy['visible_before_destruction'])
        call=next(args for name,args in api.calls if name=='CreateWindowExW')
        self.assertEqual(call[:8],(0x08000080,'STATIC','HAS background capture placement',0x88000000,0,0,0,0))
        self.assertEqual(call[8:],(None,None,None,None));self.assertEqual(api.destroy_calls,1)
    def test_body_error_still_destroys(self):
        api=FakeAPI()
        with self.assertRaisesRegex(ValueError,'capture failed'):
            with sentinel(api)() as policy:raise ValueError('capture failed')
        self.assertFalse(api.active);self.assertTrue(policy['destroyed_in_finally'])
    def test_failed_creation_no_handle_action(self):
        api=FakeAPI();api.fail_create=True
        with self.assertRaises(OSError):
            with sentinel(api)():self.fail('must not yield')
        self.assertEqual(api.destroy_calls,0)
    def test_visible_initial_window_refuses_and_destroys(self):
        api=FakeAPI();api.visible=True
        with self.assertRaises(RuntimeError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active);self.assertEqual(api.destroy_calls,1)
    def test_visible_on_cleanup_destroys_before_refusal(self):
        api=FakeAPI()
        with self.assertRaisesRegex(RuntimeError,'became visible'):
            with sentinel(api)():api.visible=True
        self.assertFalse(api.active);self.assertEqual(api.destroy_calls,1)
    def test_enabled_window_refuses_and_destroys(self):
        api=FakeAPI();api.enabled=True
        with self.assertRaises(RuntimeError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active)
    def test_nonzero_area_refuses_and_destroys(self):
        api=FakeAPI();api.bad_rect=True
        with self.assertRaises(RuntimeError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active)
    def test_style_missing_refuses_and_destroys(self):
        api=FakeAPI();api.bad_style=True
        with self.assertRaises(RuntimeError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active)
    def test_noactivate_policy_missing_refuses_and_destroys(self):
        api=FakeAPI();api.bad_exstyle=True
        with self.assertRaises(RuntimeError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active)
    def test_wrong_owner_is_not_destroyed_or_accepted(self):
        api=FakeAPI();api.bad_pid=True
        with self.assertRaisesRegex(RuntimeError,'ownership differs'):
            with sentinel(api)():self.fail('must not yield')
        self.assertEqual(api.destroy_calls,0)
    def test_wrong_thread_is_not_destroyed_or_accepted(self):
        api=FakeAPI();api.bad_tid=True
        with self.assertRaisesRegex(RuntimeError,'ownership differs'):
            with sentinel(api)():self.fail('must not yield')
        self.assertEqual(api.destroy_calls,0)
    def test_destroy_failure_is_failure(self):
        api=FakeAPI();api.fail_destroy=True
        with self.assertRaises(OSError):
            with sentinel(api)():pass
        self.assertEqual(api.destroy_calls,1)
    def test_interactive_blender_refuses_before_any_window(self):
        tree=ast.parse((HERE/'capture_blender_normals.py').read_text())
        method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_main_with_placement_sentinel')
        def require(ok,message):
            if not ok:raise ValueError(message)
        def forbidden():raise AssertionError('Window creation or capture must not be reached')
        namespace={'bpy':types.SimpleNamespace(app=types.SimpleNamespace(background=False)),
            'require':require,'_hidden_placement_sentinel':forbidden,'main':forbidden}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<synthetic-background-guard>','exec'),namespace)
        with self.assertRaisesRegex(ValueError,'background mode'):
            namespace['_main_with_placement_sentinel']()
    def test_original_functions_and_main_exact(self):
        original=(OLD/'capture_blender_normals.py').read_text();current=(HERE/'capture_blender_normals.py').read_text()
        def methods(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        before=methods(original);after=methods(current)
        self.assertTrue(all(after[n]==value for n,value in before.items()))
        body=original[original.index('def main():'):original.index('\n\nif __name__ == "__main__":')]
        self.assertEqual(current.count(body),1)
    def test_core_and_wrapper_unchanged(self):
        for name in ('probe_support.py','normal_metrics.py','compare_private_normals.py','stage_after_full_pass.py','test_probe_support.py'):
            self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
        root=HERE.parents[1]
        proof=root/'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
        self.assertEqual(hashlib.sha256(proof.read_bytes()).hexdigest(),'4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7')
        expected=json.loads(proof.read_bytes())['source_sha256']['tools/private_desktop.py']
        self.assertEqual(hashlib.sha256((root/'tools/private_desktop.py').read_bytes()).hexdigest(),expected)

if __name__=='__main__':unittest.main()
