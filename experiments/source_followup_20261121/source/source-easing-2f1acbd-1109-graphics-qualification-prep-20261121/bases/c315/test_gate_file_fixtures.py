"""Three authored UNRUN pure file-fixture controls; cannot start native jobs."""
from pathlib import Path
import copy,hashlib,importlib.util,json,tempfile,unittest
spec=importlib.util.spec_from_file_location('_easing_c315_fixture_policy',Path(__file__).with_name('source1103.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)

class GateFiles(unittest.TestCase):
    def setUp(self):self.snapshots=[]

    def fixture(self,folder,name,value):
        p=folder/name;p.write_text(json.dumps(value,allow_nan=False),encoding='utf-8')
        before=p.read_bytes();parsed=json.loads(before)
        self.snapshots.append((p,before,hashlib.sha256(before).hexdigest()))
        return parsed

    def unchanged(self):
        for p,before,digest in self.snapshots:
            self.assertEqual(p.read_bytes(),before)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)

    def test_failed_full_file_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            good={'format':'has_reference_body_full_coordinator_1','revision':S.REVISION,'exit':0,
                  'functional_source_count':1103,'result_groups':182,**{k:True for k in S.FLAGS}}
            S.completion_contract(self.fixture(root,'good.json',good))
            bad=copy.deepcopy(good);bad['whole_verifier_pass']=False
            with self.assertRaises(ValueError):S.completion_contract(self.fixture(root,'failed.json',bad))
            self.unchanged()
            self.assertEqual(json.loads((root/'good.json').read_bytes()),good)
            self.assertEqual(json.loads((root/'failed.json').read_bytes()),bad)

    def test_unreaped_outer_file_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);clone=root/S.FULL_CLONE;outer=clone/'output/root-full-launch-fixture'
            launch={'format':'has_import_off_full_outer_launch_1','revision':S.REVISION,'checkout':str(clone),
                'pid':1,'started_ns':1,'coordinator_sha256':'a'*64,'parent_environment_changed':False,
                'hidden_console':True,'graphical_tests_must_use_private_desktops':True,
                'child_environment':{k:str(outer/'User'/v) for k,v in
                    [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]}}
            launch['child_environment']['PYTHONDONTWRITEBYTECODE']='1'
            good={'format':'has_import_off_full_outer_completion_1','exit':0,'pid':1,'launch':launch,
                **{k:True for k in ('child_reaped','parent_environment_unchanged','coordinator_source_unchanged','revision_unchanged')}}
            S.outer_contract(launch,self.fixture(root,'good.json',good),clone,outer,'a'*64)
            bad=copy.deepcopy(good);bad['child_reaped']=False
            with self.assertRaises(ValueError):S.outer_contract(launch,self.fixture(root,'failed.json',bad),clone,outer,'a'*64)
            self.unchanged()
            self.assertEqual(json.loads((root/'good.json').read_bytes()),good)
            self.assertEqual(json.loads((root/'failed.json').read_bytes()),bad)

    def test_foreground_receipt_file_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            good={'format':'studio_private_desktop_1','desktop':'HAS_SYNTHETIC','child_pid':1,'exit':0,
                'job_closed':True,'desktop_closed':True,'child_desktop_confirmed':True,
                'foreground_child_observed':False,'desktop_switch_requested':False}
            S.physical_receipt_contract(self.fixture(root,'good.json',good))
            bad=copy.deepcopy(good);bad['foreground_child_observed']=True
            with self.assertRaises(ValueError):S.physical_receipt_contract(self.fixture(root,'failed.json',bad))
            self.unchanged()
            self.assertEqual(json.loads((root/'good.json').read_bytes()),good)
            self.assertEqual(json.loads((root/'failed.json').read_bytes()),bad)

if __name__=='__main__':unittest.main()
