"""Actual owned worker receipt, cancellation and exact seed/source identity."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,unittest
from test_helper_morphs import shape_fixture


class StudyWorker(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.source=self.folder/'shape.glb';shape_fixture(self.source);self.before=(self.source.read_bytes(),self.source.stat().st_mtime_ns)
        self.worker=Path(__file__).resolve().parents[1]/'tools/shape_study_worker.py'
        self.request={'format':'studio_shape_study_request_1','job_id':'1234','seeds':{'format':'studio_deform_seeds_1','source_sha256':hashlib.sha256(self.before[0]).hexdigest(),'controls':[{'node':3,'target':0,'native_name':'Loose part shape','area':'Hair','provenance':'Manual choice'}]}}

    def run_worker(self):
        (self.folder/'request.json').write_text(json.dumps(self.request),encoding='utf-8')
        p=subprocess.run([sys.executable,str(self.worker),str(self.source),str(self.folder)],capture_output=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse((self.folder/'result.json.tmp').exists())
        self.assertEqual((self.source.read_bytes(),self.source.stat().st_mtime_ns),self.before)
        return json.loads((self.folder/'result.json').read_text())

    def test_actual_worker_observes_without_touching_source(self):
        result=self.run_worker();self.assertTrue(result['ok']);self.assertEqual(result['job_id'],'1234')
        self.assertEqual(result['value']['target_count'],2)
        self.assertEqual(result['value']['rows'][1]['region_estimate']['area'],'Hair')

    def test_cancelled_request_never_publishes_observations(self):
        (self.folder/'cancel').write_text('cancel');result=self.run_worker()
        self.assertFalse(result['ok']);self.assertIn('cancelled',result['error']);self.assertNotIn('value',result)

    def test_stale_source_fails_with_structured_receipt(self):
        self.request['seeds']['source_sha256']='0'*64;result=self.run_worker()
        self.assertFalse(result['ok']);self.assertIn('source changed',result['error'])

    def test_invalid_job_identity_is_rejected(self):
        self.request['job_id']='../other';self.assertFalse(self.run_worker()['ok'])

    def test_existing_receipt_is_not_replaced(self):
        self.run_worker();before=(self.folder/'result.json').read_bytes()
        p=subprocess.run([sys.executable,str(self.worker),str(self.source),str(self.folder)],capture_output=True,timeout=20)
        self.assertNotEqual(p.returncode,0);self.assertEqual((self.folder/'result.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
