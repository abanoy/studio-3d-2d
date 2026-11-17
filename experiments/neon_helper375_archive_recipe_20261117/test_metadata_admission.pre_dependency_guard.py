"""Meaningful in-memory tamper checks on the exact closed scalar/source corpus."""
from pathlib import Path
import copy,hashlib,json,unittest
from archive_checks import ROOT_RUN,check,load
HERE=Path(__file__).resolve().parent
class MetadataAdmission(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  raw=(HERE/'INPUTS.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='f793f505db95097a27e2f9dac845e5bec6d012b7a4ae4610140ad4f64e927af1'
  cls.spec=load(raw);cls.original={};cls.bindings={}
  for row in cls.spec['inputs']:
   data=(Path(cls.spec['roots'][row['root']])/row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
   key=row['root']+':'+row['path'];cls.original[key]=data;cls.bindings[key]=row
  cls.result_key='REVIEW:'+ROOT_RUN+'verification.json'
  cls.results=[key for key in cls.original if key.endswith('/result.json')]
  cls.receipts=[key for key in cls.original if key.endswith('/private-receipt.json')]
  cls.launches=[key for key in cls.original if key.endswith('/owned-launch.json')]
  cls.outcomes=[key for key in cls.original if key.endswith('/owned-outcome.json')]
 def setUp(self):self.raw=self.original.copy()
 def change(self,key,action):
  value=load(self.raw[key]);action(value);self.raw[key]=json.dumps(value,allow_nan=False).encode();load(self.raw[key])
 def refuse(self):
  with self.assertRaises((ValueError,KeyError,StopIteration)):check(self.raw,self.bindings,self.spec['roots']['REVIEW'])
 def test_exact_closed_corpus_accepts(self):self.assertEqual(check(self.raw,self.bindings,self.spec['roots']['REVIEW']),self.spec['expected_summary'])
 def test_root_failed_status_refuses(self):self.change(self.result_key,lambda v:v.update(passed=False));self.refuse()
 def test_root_full_success_claim_refuses(self):self.change(self.result_key,lambda v:v.update(full_suite_pass_claimed=True));self.refuse()
 def test_root_assertions_not_completed_refuse(self):self.change(self.result_key,lambda v:v['rows'][1].update(root_exact_suite_assertions_passed=False));self.refuse()
 def test_source_after_byte_identity_change_refuses(self):
  key='REVIEW:'+ROOT_RUN+'source-after.json';self.change(key,lambda v:v.update({'src/app.gd':'0'*64}));self.refuse()
 def test_raw_graphical_float_count_alias_refuses(self):
  key=next(k for k in self.results if '/focused/' in k);self.change(key,lambda v:v.update(checks=221.0));self.refuse()
 def test_raw_CPU_check_omission_refuses(self):
  key=next(k for k in self.results if '/adapter/' in k);self.change(key,lambda v:v['checks'].pop());self.refuse()
 def test_raw_context_revision_change_refuses(self):
  key=next(k for k in self.results if '/focused/' in k);self.change(key,lambda v:v['metrics'].update(main_revision='0'*40));self.refuse()
 def test_private_receipt_foreground_refuses(self):self.change(self.receipts[0],lambda v:v.update(foreground_child_observed=True));self.refuse()
 def test_private_receipt_job_not_closed_refuses(self):self.change(self.receipts[0],lambda v:v.update(job_closed=False));self.refuse()
 def test_private_command_stale_receipt_path_refuses(self):
  key=self.receipts[0].removesuffix('private-receipt.json')+'command.json';self.change(key,lambda v:v.__setitem__(v.index('--receipt')+1,'C:\\wrong\\old.json'));self.refuse()
 def test_CPU_receipt_invention_refuses(self):
  key=next(k for k in self.original if '/adapter/command.json' in k);self.change(key,lambda v:v.extend(['--receipt','C:\\invented.json']));self.refuse()
 def test_worker_launch_without_job_assignment_refuses(self):self.change(self.launches[0],lambda v:v.update(job_assigned=False));self.refuse()
 def test_worker_outcome_owner_mismatch_refuses(self):self.change(self.outcomes[0],lambda v:v['owner'].update(created_100ns='1'));self.refuse()
 def test_worker_outcome_unclosed_handle_refuses(self):self.change(self.outcomes[0],lambda v:v.update(process_handle_closed=False));self.refuse()
 def test_missing_outcome_is_not_silently_counted_completed(self):self.raw.pop(self.outcomes[0]);self.refuse()
 def test_recorded_worker_scope_nonzero_refuses(self):self.change('REVIEW:'+ROOT_RUN+'after-worker-closure.json',lambda v:v.update(owned_count=1));self.refuse()
if __name__=='__main__':unittest.main()
