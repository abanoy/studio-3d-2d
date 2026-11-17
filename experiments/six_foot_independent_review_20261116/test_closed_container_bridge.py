"""Actual closed-v2 container worker on disposable synthetic fixtures only."""
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
V1=ROOT/'experiments/six_foot_import_basis_candidate_20261116'
CANDIDATE=ROOT/'experiments/six_foot_import_basis_gd_candidate_20261116'
sys.path.insert(0,str(ROOT))
original=importlib.import_module('tools.has_project')
directory=importlib.import_module('tools.directory_commit')

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

old_basis=load('tools.import_basis',V1/'draft/tools/import_basis.py')
archive_creator=load('tools._synthetic_schema9_creator',V1/'draft/tools/has_project.py')
basis=load('tools.import_basis',CANDIDATE/'draft/tools/import_basis.py')
candidate=load('tools._closed_basis_v2_reader',CANDIDATE/'draft/tools/has_project.py')
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


class ClosedBridge(unittest.TestCase):
    def owned_temp(self):
        temp=tempfile.TemporaryDirectory(prefix='owned-synthetic-',dir=HERE)
        path=Path(temp.name).resolve();self.assertTrue(path.is_relative_to(HERE.resolve()))
        def cleanup():
            self.assertTrue(path.resolve().is_relative_to(HERE.resolve()));temp.cleanup()
        self.addCleanup(cleanup);return path

    def test_active9_pack_refuses_before_new_container_for4_and7(self):
        for version in (4,7):
            for storage in ('packed','linked'):
                folder=self.owned_temp();request,_=setup(folder,manifest(version,wrapped=True),storage)
                with self.assertRaises(basis.BasisError):candidate.pack(request)
                self.assertFalse(Path(request['path']).exists())

    def test_active9_unpack_refuses_before_extraction_for4_and7(self):
        for version in (4,7):
            for storage in ('packed','linked'):
                folder=self.owned_temp();request,_=setup(folder,manifest(version,wrapped=True),storage);archive_creator.pack(request)
                out=folder/'never-created'
                with self.assertRaises(basis.BasisError):candidate.unpack({'path':request['path'],'folder':str(out)})
                self.assertFalse(out.exists())

    def test_legacy4_and7_active_fields_refuse_before_target_replace(self):
        for version in (4,7):
            folder=self.owned_temp();request,_=setup(folder,manifest(version,active=False));candidate.pack(request);before=Path(request['path']).read_bytes()
            (Path(request['folder'])/'project.json').write_bytes(candidate.json_bytes(manifest(version,active=True)))
            with self.assertRaises(basis.BasisError):candidate.pack(request)
            self.assertEqual(Path(request['path']).read_bytes(),before)

    def test_legacy4_and7_active_fields_refuse_before_extraction(self):
        for version in (4,7):
            folder=self.owned_temp();request,_=setup(folder,manifest(version,active=True));original.pack(request)
            out=folder/'never-created'
            with self.assertRaises(basis.BasisError):candidate.unpack({'path':request['path'],'folder':str(out)})
            self.assertFalse(out.exists())

    def test_ordinary4_and7_packed_and_linked_preserve_manifest_bytes(self):
        for version in (4,7):
            for storage in ('packed','linked'):
                folder=self.owned_temp();request,blob=setup(folder,manifest(version,active=False),storage)
                result=candidate.pack(request);self.assertTrue(result['ok'])
                out=candidate.unpack({'path':request['path'],'folder':str(folder/'opened')})
                self.assertTrue(out['ok']);self.assertEqual((Path(out['folder'])/'project.json').read_bytes(),blob)
                BOUNDARY_CASES.append({'underlying_version':version,'storage':storage,'legacy_manifest_bytes_preserved':True})

    def test_ordinary_asset_package_remains_supported(self):
        folder=self.owned_temp();request,blob=setup(folder,manifest(active=False),package=True);candidate.pack(request)
        out=candidate.unpack({'path':request['path'],'folder':str(folder/'opened'),'import_asset':True,'asset_kind':'model','asset_frame':0})
        self.assertTrue(out['ok']);self.assertEqual(out['asset_package'],request['asset_package']);self.assertEqual((Path(out['folder'])/'project.json').read_bytes(),blob)

    def test_active_asset_package_refuses_on_both_worker_sides(self):
        folder=self.owned_temp();request,_=setup(folder,manifest(wrapped=True),package=True)
        with self.assertRaises(basis.BasisError):candidate.pack(request)
        archive_creator.pack(request);out=folder/'never-created'
        with self.assertRaises(basis.BasisError):candidate.unpack({'path':request['path'],'folder':str(out),'import_asset':True,'asset_kind':'model','asset_frame':0})
        self.assertFalse(out.exists())

    def test_request_ready_field_cannot_enable_worker(self):
        folder=self.owned_temp();request,_=setup(folder,manifest(wrapped=True));request['runtime_basis_ready']=True
        with self.assertRaises(basis.BasisError):candidate.pack(request)
        self.assertFalse(Path(request['path']).exists())


def main():
    watched=[ROOT/'tools/has_project.py',ROOT/'tools/directory_commit.py',CANDIDATE/'draft/tools/has_project.py',CANDIDATE/'draft/tools/import_basis.py']
    def identities():return {str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mtime_ns':p.stat().st_mtime_ns} for p in watched}
    before=identities();suite=unittest.defaultTestLoader.loadTestsFromTestCase(ClosedBridge);names=[case.id().split('.')[-1] for case in suite];result=unittest.TestResult()
    with mock.patch('subprocess.Popen',side_effect=AssertionError('No subprocess allowed in synthetic worker proof')) as guard:suite.run(result);attempts=guard.call_count
    after=identities();report={'format':'has_six_foot_closed_v2_actual_container_cpu_1','passed':result.wasSuccessful(),'test_methods':result.testsRun,'named_tests':names,'legacy_positive_cases':BOUNDARY_CASES,'failures':[{'test':str(t),'trace':trace} for t,trace in result.failures],'errors':[{'test':str(t),'trace':trace} for t,trace in result.errors],'subprocess_attempts':attempts,'source_identity_before':before,'source_identity_preserved':before==after,'actual_container_workers_used':True,'synthetic_assets_only':True,'Godot_classifier_Model_or_activation_runs':0,'sealed_candidates_modified':False}
    (HERE/'CLOSED_WORKER_CPU_RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k in ('passed','test_methods','subprocess_attempts','source_identity_preserved','Godot_classifier_Model_or_activation_runs')}))
    for test,trace in result.failures+result.errors:print(str(test)+'\n'+trace)
    return 0 if result.wasSuccessful() and before==after and attempts==0 else 1


if __name__=='__main__':raise SystemExit(main())
