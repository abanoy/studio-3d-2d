"""Diagnostic CPU proof of the sealed v1 container boundary, not activation."""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CANDIDATE=ROOT/'experiments/six_foot_import_basis_candidate_20261116'
sys.path.insert(0,str(ROOT))
original=importlib.import_module('tools.has_project')
directory=importlib.import_module('tools.directory_commit')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

basis=load('tools.import_basis',CANDIDATE/'draft/tools/import_basis.py')
candidate=load('tools._six_foot_bridge_v1',CANDIDATE/'draft/tools/has_project.py')
PAYLOAD=b'Synthetic contract boundary bytes: deliberately not a GLB.'
REFERENCE=b'Synthetic resource inventory bytes: deliberately not a PNG.'
SHA=hashlib.sha256(PAYLOAD).hexdigest()
REF_SHA=hashlib.sha256(REFERENCE).hexdigest()
BOUNDARY_CASES=[]

def model(active=True):
    row={'format':'studio_model_1','id':'synthetic_boundary','name':'Synthetic boundary',
         'kind':'model','parent_id':'','start_frame':0,'sha256':SHA,'path':'assets/'+SHA+'.glb',
         'scale':1,'position':[0,0,0],'rotation_xyzw':[0,0,0,1],'visible':True,
         'reference_only':False,'pose':{},'pose_keys':[],'draft_frame':0,'metadata':{}}
    if active:row['asset_basis']=basis.make_basis(SHA,'2')
    return row

def manifest(version=4,wrapped=False,active=True):
    data={'schema_version':4,'video':{'width':1920,'height':1080,'fps_num':24,'fps_den':1,'duration_frames':48},
          'camera_keys':[],'layers':[],'audio':{},'editor':{'frame':0},
          'world':{'format':'studio_world_1','objects':[model(active)]}}
    if version==7:
        data.update(schema_version=7,content_schema_version=4,
            reference_sheet={'format':'studio_reference_sheet_1','name':'Synthetic reference',
                             'sha256':REF_SHA,'path':'references/'+REF_SHA+'.png'})
    return basis.encode_capability(data) if wrapped else data

def setup(folder,data,storage='packed',package=False):
    snapshot=folder/'snapshot';snapshot.mkdir()
    name='assets/'+SHA+'.glb';source=folder/'external-model.glb';source.write_bytes(PAYLOAD)
    (snapshot/'assets').mkdir();(snapshot/name).write_bytes(PAYLOAD)
    references={name:str(source)}
    if 'reference_sheet' in data:
        path=data['reference_sheet']['path'];ref=folder/'external-reference.png';ref.write_bytes(REFERENCE)
        (snapshot/'references').mkdir();(snapshot/path).write_bytes(REFERENCE);references[path]=str(ref)
    blob=candidate.json_bytes(data);(snapshot/'project.json').write_bytes(blob)
    request={'action':'pack','folder':str(snapshot),'path':str(folder/'synthetic.has'),
             'storage':storage,'references':references,'cache_root':str(folder/'cache')}
    if package:request['asset_package']={'format':'studio_asset_package_1','kind':'model','name':'Synthetic boundary'}
    return request,blob

class ActualBridge(unittest.TestCase):
    def owned_temp(self):
        temp=tempfile.TemporaryDirectory(prefix='owned-cpu-',dir=HERE)
        path=Path(temp.name).resolve();self.assertTrue(path.is_relative_to(HERE.resolve()))
        self.addCleanup(temp.cleanup);return path

    def test_v1_packed_and_linked_keep_original9_for_world4_and_reference7(self):
        for storage in ('packed','linked'):
            for version in (4,7):
                with self.subTest(storage=storage,version=version):
                    folder=self.owned_temp();data=manifest(version,wrapped=True);request,blob=setup(folder,data,storage)
                    candidate.pack(request)
                    with zipfile.ZipFile(request['path']) as archive:self.assertEqual(archive.read('project.json'),blob)
                    out=candidate.unpack({'path':request['path'],'folder':str(folder/'opened')})
                    self.assertTrue(out['ok']);actual=(Path(out['folder'])/'project.json').read_bytes()
                    self.assertEqual(actual,blob);self.assertEqual(json.loads(actual),data)
                    self.assertEqual(json.loads(actual)['schema_version'],9)
                    BOUNDARY_CASES.append({'storage':storage,'underlying_version':version,
                        'original_manifest_bytes_preserved':True,'extracted_schema':9,'Godot_executed':False})

    def test_actual_asset_package_worker_also_keeps9(self):
        folder=self.owned_temp();data=manifest(wrapped=True);request,blob=setup(folder,data,package=True)
        candidate.pack(request)
        out=candidate.unpack({'path':request['path'],'folder':str(folder/'opened'),
            'import_asset':True,'asset_kind':'model','asset_frame':0})
        self.assertTrue(out['ok']);self.assertEqual(out['asset_package'],request['asset_package'])
        self.assertEqual((Path(out['folder'])/'project.json').read_bytes(),blob)

    def test_actual_original_unpack_rejects9_before_extraction(self):
        folder=self.owned_temp();request,_=setup(folder,manifest(wrapped=True));candidate.pack(request)
        target=folder/'old-open'
        with self.assertRaises(original.HasError):original.unpack({'path':request['path'],'folder':str(target)})
        self.assertFalse(target.exists())

    def test_v1_rejects_unwrapped_active4_and7_before_creating_container(self):
        for version in (4,7):
            folder=self.owned_temp();request,_=setup(folder,manifest(version))
            with self.assertRaises(basis.BasisError):candidate.pack(request)
            self.assertFalse(Path(request['path']).exists())

    def test_actual_old_pack_and_unpack_accept_legacy4_and7_extra_basis(self):
        for version in (4,7):
            folder=self.owned_temp();data=manifest(version);request,blob=setup(folder,data)
            original.pack(request);out=original.unpack({'path':request['path'],'folder':str(folder/'opened')})
            self.assertTrue(out['ok']);self.assertEqual((Path(out['folder'])/'project.json').read_bytes(),blob)
            self.assertIn('asset_basis',json.loads(blob)['world']['objects'][0])

    def test_actual_directory_commit_reader_rejects9(self):
        folder=self.owned_temp();request,_=setup(folder,manifest(wrapped=True))
        with self.assertRaises(original.HasError):directory.read_manifest(Path(request['folder'])/'project.json')

    def test_actual_directory_commit_reader_accepts_legacy7_extra_basis(self):
        folder=self.owned_temp();data=manifest(7);request,blob=setup(folder,data)
        self.assertEqual(directory.read_manifest(Path(request['folder'])/'project.json'),blob)

    def test_actual_old_pack_refusal_preserves_prior_valid_container(self):
        folder=self.owned_temp();plain=manifest(active=False);request,_=setup(folder,plain)
        original.pack(request);before=Path(request['path']).read_bytes()
        (Path(request['folder'])/'project.json').write_bytes(candidate.json_bytes(manifest(wrapped=True)))
        with self.assertRaises(original.HasError):original.pack(request)
        self.assertEqual(Path(request['path']).read_bytes(),before)

def main():
    watched=[ROOT/'tools/has_project.py',ROOT/'tools/directory_commit.py',
             CANDIDATE/'draft/tools/has_project.py',CANDIDATE/'draft/tools/import_basis.py']
    before={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mtime_ns':p.stat().st_mtime_ns} for p in watched}
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ActualBridge);names=[case.id().split('.')[-1] for case in suite]
    result=unittest.TestResult()
    with mock.patch('subprocess.Popen',side_effect=AssertionError('No subprocess permitted in this CPU boundary proof')) as guard:
        suite.run(result);attempts=guard.call_count
    after={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mtime_ns':p.stat().st_mtime_ns} for p in watched}
    report={'format':'has_six_foot_actual_container_bridge_diagnostic_1','passed':result.wasSuccessful(),
        'test_methods':result.testsRun,'named_tests':names,'actual_container_boundary_cases':BOUNDARY_CASES,
        'failures':[{'test':str(t),'trace':trace} for t,trace in result.failures],
        'errors':[{'test':str(t),'trace':trace} for t,trace in result.errors],
        'subprocess_attempts':attempts,'source_identity_before':before,'source_identity_preserved':before==after,
        'diagnostic_not_product_acceptance':True,'Godot_model_render_or_activation_runs':0,
        'finding':'V1 accepts/writes original schema9 bytes, not an unversioned bridge. Current Godot reader must still refuse9. Production default needs fail-closed readiness policy.'}
    with (HERE/'ACTUAL_BRIDGE_CPU_RESULT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k in ('passed','test_methods','subprocess_attempts','source_identity_preserved','Godot_model_render_or_activation_runs')}))
    for test,trace in result.failures+result.errors:print(str(test)+'\n'+trace)
    return 0 if result.wasSuccessful() and before==after and attempts==0 else 1
if __name__=='__main__':raise SystemExit(main())
