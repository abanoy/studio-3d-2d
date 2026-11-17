"""Synthetic API fault injection only; never calls Win32 or loads Blender."""
from pathlib import Path
import argparse,ast,contextlib,ctypes,hashlib,io,json,sys,tempfile,types,unittest
from ctypes import wintypes as W
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'normal_setter_boundary_probe_20261116'
SENTINEL_OLD=HERE.parent/'normal_boundary_probe_sentinel_20261116'
HELPER_SHA='809e4f01bf5236e716df558f5ac03ab5960c2b81c4ac7d50bd369a97c1c409f6'
POLICY_SHA='8dc902af4b7b8970634593e516d75228308112220f000b1cf22ca4914d4062ba'

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

def sentinel(api,platform="win32"):
    tree=ast.parse((HERE/'setter_probe.py').read_text())
    method=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_hidden_placement_sentinel')
    unit=ast.Module(body=[method],type_ignores=[]);ast.fix_missing_locations(unit)
    namespace={'C':FakeC(api),'W':W,'sys':types.SimpleNamespace(platform=platform),'contextmanager':contextlib.contextmanager}
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
        tree=ast.parse((HERE/'setter_probe.py').read_text())
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
        original=(OLD/'setter_probe.py').read_text();current=(HERE/'setter_probe.py').read_text()
        def methods(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        before=methods(original);after=methods(current)
        self.assertTrue(all(after[n]==value for n,value in before.items()))
        original_node=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        body=''.join(original.splitlines(keepends=True)[original_node.lineno-1:original_node.end_lineno])
        self.assertEqual(current.count(body),1)
        current_node=next(n for n in ast.parse(current).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        raw_main=b''.join((HERE/'setter_probe.py').read_bytes().splitlines(keepends=True)[current_node.lineno-1:current_node.end_lineno])
        old_raw_main=b''.join((OLD/'setter_probe.py').read_bytes().splitlines(keepends=True)[original_node.lineno-1:original_node.end_lineno])
        self.assertEqual(raw_main,old_raw_main)
    def test_core_and_wrapper_unchanged(self):
        for name in ('setter_support.py','instrumentation.py','vvd_normals.py','test_setter_support.py','test_instrumentation.py','test_vvd_normals.py'):
            self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
        root=HERE.parents[1]
        proof=root/'output/windows-canonical-bone-binding-20261116T041518335/source-before.json'
        self.assertEqual(hashlib.sha256(proof.read_bytes()).hexdigest(),'4b1eb25e1da8e510106fe3dd01c4b5014c7cc719133f18e1bbccd386ec9deae7')
        expected=json.loads(proof.read_bytes())['source_sha256']['tools/private_desktop.py']
        self.assertEqual(hashlib.sha256((root/'tools/private_desktop.py').read_bytes()).hexdigest(),expected)
        self.assertEqual(expected,'9788e7fde42de7bce022589c86146eaa93deb142ef368aa37a05259ec3047628')
        support=ast.parse((HERE/'setter_support.py').read_bytes())
        roles=next(n.value for n in support.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROLES' for t in n.targets))
        self.assertEqual(len(ast.literal_eval(roles)),26)



# Only extracted pure functions are executed. Blender, WinDLL, process inventory,
# source runtime and real native arrays are never imported or invoked by this suite.
def extracted_functions(*names, namespace):
    tree=ast.parse((HERE/'setter_probe.py').read_bytes())
    methods={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    unit=ast.Module(body=[methods[name] for name in names],type_ignores=[])
    exec(compile(ast.fix_missing_locations(unit),'<synthetic-setter-wrapper-only>','exec'),namespace)
    return namespace

def decorated_bytes(path,name):
    raw=path.read_bytes();lines=raw.splitlines(keepends=True)
    method=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name)
    start=min([method.lineno]+[n.lineno for n in method.decorator_list])
    return b''.join(lines[start-1:method.end_lineno])

class HelperIntegrityTests(unittest.TestCase):
    def test_exact_sealed_prerequisite_indices(self):
        for path,pin in ((SENTINEL_OLD/'INDEX.json','a2475b28c03c6b87cc0d98d537433204b9553122a97f1197321455a491e2ef64'),(OLD/'INDEX.json','d6c4520ae2a78bc779cb227bb028c5cf2a3b166706da154bc85a1343736e0350')):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),pin)
        index=json.loads((OLD/'INDEX.json').read_bytes())
        for name in ('setter_probe.py','setter_support.py','instrumentation.py','vvd_normals.py'):
            raw=(OLD/name).read_bytes();entry=index['files'][name]
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(entry['bytes'],entry['sha256']))
    def test_decorated_helper_byte_exact_to_sealed_source(self):
        current=decorated_bytes(HERE/'setter_probe.py','_hidden_placement_sentinel')
        original=decorated_bytes(SENTINEL_OLD/'capture_blender_normals.py','_hidden_placement_sentinel')
        self.assertEqual(current,original)
        self.assertEqual(hashlib.sha256(current).hexdigest(),HELPER_SHA)
    def test_nonwindows_refuses_before_any_fake_api(self):
        api=FakeAPI()
        with self.assertRaisesRegex(RuntimeError,'requires Windows'):
            with sentinel(api,platform='linux')():self.fail('must not yield')
        self.assertEqual(api.calls,[])
    def test_get_window_rect_failure_destroys_owned_window(self):
        class Fault(FakeAPI):
            def call(self,name,*args):
                value=super().call(name,*args)
                return 0 if name=='GetWindowRect' else value
        api=Fault()
        with self.assertRaises(OSError):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active);self.assertEqual(api.destroy_calls,1)
    def test_visible_and_child_style_bits_are_rejected(self):
        for forbidden in (0x10000000,0x40000000):
            with self.subTest(style_bit=forbidden):
                class Fault(FakeAPI):
                    def call(self,name,*args):
                        value=super().call(name,*args)
                        return value|forbidden if name=='GetWindowLongW' and args[1]==-16 else value
                api=Fault()
                with self.assertRaisesRegex(RuntimeError,'top-level popup'):
                    with sentinel(api)():self.fail('must not yield')
                self.assertFalse(api.active);self.assertEqual(api.destroy_calls,1)
    def test_missing_toolwindow_style_is_rejected(self):
        class Fault(FakeAPI):
            def call(self,name,*args):
                value=super().call(name,*args)
                return value&~0x80 if name=='GetWindowLongW' and args[1]==-20 else value
        api=Fault()
        with self.assertRaisesRegex(RuntimeError,'activation/tool policy'):
            with sentinel(api)():self.fail('must not yield')
        self.assertFalse(api.active)
    def test_cleanup_owner_change_is_not_destroyed_or_accepted(self):
        api=FakeAPI()
        with self.assertRaisesRegex(RuntimeError,'ownership differs'):
            with sentinel(api)():api.bad_pid=True
        self.assertEqual(api.destroy_calls,0)
    def test_unavailable_handle_is_not_destroyed_or_accepted(self):
        class Fault(FakeAPI):
            def call(self,name,*args):
                value=super().call(name,*args)
                return 0 if name=='IsWindow' else value
        api=Fault()
        with self.assertRaisesRegex(RuntimeError,'unavailable'):
            with sentinel(api)():self.fail('must not yield')
        self.assertEqual(api.destroy_calls,0)

class WrapperTests(unittest.TestCase):
    def fixture(self,*,code=0,status='SETTER_BOUNDARIES_MEASURED',bad_private_hash=False,hook=None,main_error=None):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        target=Path(temp.name)/'capture';lease_path=Path(temp.name)/'lease.json'
        api=FakeAPI();events=[]
        lease={'private_output':str(target),'additional_metadata_policy':{'path':str(HERE/'ISOLATION_POLICY.json'),'sha256':POLICY_SHA}}
        private_raw=b'{"synthetic_setter_private":true}\n'
        public={'format':'has_sourceio_setter_boundary_probe_1','status':status,'private_sha256':'0'*64 if bad_private_hash else hashlib.sha256(private_raw).hexdigest(),'normal_fidelity':'FAILED_UNQUALIFIED'}
        public_raw=(json.dumps(public,sort_keys=True)+'\n').encode()
        state=types.SimpleNamespace(api=api,target=target,lease=lease,events=events,private_raw=private_raw,public_raw=public_raw,main_calls=0)
        def require(ok,message):
            if not ok:raise ValueError(message)
        def check_lease(path,probe):
            self.assertEqual(path,lease_path)
            self.assertEqual(Path(probe),HERE/'setter_probe.py')
            events.append(('lease',api.active))
            return lease,{}
        def main():
            self.assertTrue(api.active,'original main must run inside the sentinel lifetime')
            state.main_calls+=1;events.append(('main',api.active))
            target.mkdir()
            (target/'PRIVATE_SETTER.json').write_bytes(private_raw)
            (target/'PUBLIC_SETTER.json').write_bytes(public_raw)
            if hook:hook(state)
            if main_error:raise main_error
            return code
        namespace={'HERE':HERE,'ISOLATION_POLICY_SHA':POLICY_SHA,'Path':Path,'argparse':argparse,'json':json,
            'sha':lambda raw:hashlib.sha256(raw).hexdigest(),'require':require,'check_lease':check_lease,'main':main,
            '_hidden_placement_sentinel':sentinel(api),'bpy':types.SimpleNamespace(app=types.SimpleNamespace(background=True)),
            'sys':types.SimpleNamespace(argv=['blender','--','--lease',str(lease_path)]),'__file__':str(HERE/'setter_probe.py')}
        extracted_functions('write','_verified_isolation_policy','_main_with_placement_sentinel',namespace=namespace)
        state.namespace=namespace
        return state
    def invoke(self,state):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):result=state.namespace['_main_with_placement_sentinel']()
        return result,output.getvalue()
    def assert_original_outputs_unchanged(self,state):
        self.assertEqual((state.target/'PRIVATE_SETTER.json').read_bytes(),state.private_raw)
        self.assertEqual((state.target/'PUBLIC_SETTER.json').read_bytes(),state.public_raw)
    def test_success_sidecar_only_after_cleanup_and_binds_both_original_outputs(self):
        state=self.fixture();code,log=self.invoke(state)
        self.assertEqual(code,0);self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertEqual(state.events,[('lease',False),('main',True),('lease',False)])
        self.assert_original_outputs_unchanged(state)
        sidecar=json.loads((state.target/'PUBLIC_PLACEMENT.json').read_bytes())
        self.assertEqual(sidecar['public_setter_sha256'],hashlib.sha256(state.public_raw).hexdigest())
        self.assertEqual(sidecar['private_setter_sha256'],hashlib.sha256(state.private_raw).hexdigest())
        self.assertEqual(sidecar['metadata_policy_sha256'],POLICY_SHA)
        self.assertIs(sidecar['numeric_public_and_private_outputs_unchanged'],True)
        metadata=json.loads((HERE/'ISOLATION_POLICY.json').read_bytes())
        self.assertEqual(sidecar['format'],metadata['public_sidecar_format'])
        for key,value in metadata['public_field_required_values'].items():
            self.assertEqual(sidecar['background_isolation_sentinel'][key],value)
            self.assertIs(type(sidecar['background_isolation_sentinel'][key]),type(value))
        lines=log.splitlines();self.assertEqual(len(lines),1)
        marker=metadata['additional_stdout_marker'];self.assertTrue(lines[0].startswith(marker))
        self.assertEqual(json.loads(lines[0][len(marker):]),sidecar)
    def test_nonzero_main_preserves_failure_and_never_writes_sidecar(self):
        state=self.fixture(code=1);code,log=self.invoke(state)
        self.assertEqual(code,1);self.assertEqual(log,'');self.assertEqual(state.main_calls,1)
        self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertEqual(state.events,[('lease',False),('main',True)])
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_main_exception_destroys_and_never_writes_sidecar(self):
        state=self.fixture(main_error=ValueError('synthetic original main failure'))
        with self.assertRaisesRegex(ValueError,'synthetic original main failure'):self.invoke(state)
        self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_cleanup_failure_never_writes_sidecar(self):
        state=self.fixture();state.api.fail_destroy=True
        with self.assertRaises(OSError):self.invoke(state)
        self.assertEqual(state.api.destroy_calls,1)
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_visibility_on_cleanup_is_a_failure_after_destroy(self):
        state=self.fixture(hook=lambda s:setattr(s.api,'visible',True))
        with self.assertRaisesRegex(RuntimeError,'became visible'):self.invoke(state)
        self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
    def test_interactive_or_nonboolean_background_refuses_before_lease_and_win32(self):
        for background in (False,None,1):
            with self.subTest(background=background):
                state=self.fixture();state.namespace['bpy'].app.background=background
                with self.assertRaisesRegex(ValueError,'background mode'):self.invoke(state)
                self.assertEqual(state.events,[]);self.assertEqual(state.api.calls,[]);self.assertEqual(state.main_calls,0)
    def test_bad_policy_hash_refuses_before_win32(self):
        state=self.fixture();state.lease['additional_metadata_policy']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Pinned sentinel metadata policy'):self.invoke(state)
        self.assertEqual(state.api.calls,[]);self.assertEqual(state.main_calls,0)
        self.assertFalse(state.target.exists())
    def test_wrong_policy_path_refuses_before_win32(self):
        state=self.fixture();state.lease['additional_metadata_policy']['path']=str(HERE/'different-policy.json')
        with self.assertRaisesRegex(ValueError,'Pinned sentinel metadata policy'):self.invoke(state)
        self.assertEqual(state.api.calls,[]);self.assertEqual(state.main_calls,0)
    def test_policy_change_after_main_refuses_after_cleanup(self):
        state=self.fixture(hook=lambda s:s.lease['additional_metadata_policy'].update(sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'Pinned sentinel metadata policy'):self.invoke(state)
        self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_bad_private_hash_refuses_after_cleanup(self):
        state=self.fixture(bad_private_hash=True)
        with self.assertRaisesRegex(ValueError,'Original private setter output differs'):self.invoke(state)
        self.assertFalse(state.api.active);self.assertEqual(state.api.destroy_calls,1)
        self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_failed_public_status_is_never_qualified(self):
        state=self.fixture(status='SETTER_IMPORT_REPLAY_FAILED')
        with self.assertRaisesRegex(ValueError,'Successful original setter result'):self.invoke(state)
        self.assertFalse(state.api.active);self.assertFalse((state.target/'PUBLIC_PLACEMENT.json').exists())
        self.assert_original_outputs_unchanged(state)
    def test_existing_sidecar_is_preserved_as_failure(self):
        existing=b'{"previous_attempt":true}\n'
        state=self.fixture(hook=lambda s:(s.target/'PUBLIC_PLACEMENT.json').write_bytes(existing))
        with self.assertRaises(FileExistsError):self.invoke(state)
        self.assertFalse(state.api.active)
        self.assertEqual((state.target/'PUBLIC_PLACEMENT.json').read_bytes(),existing)
        self.assert_original_outputs_unchanged(state)


if __name__=='__main__':unittest.main()
