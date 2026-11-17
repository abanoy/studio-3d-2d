import copy,importlib.util,unittest
from pathlib import Path
path=Path(__file__).with_name('bind_context.py')
spec=importlib.util.spec_from_file_location('neon375_api_source_test',path);B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
def raw():
 return {'format':'has_root_birth_api_detail_1','identity_api':'Get-Process.StartTime','precision':'100ns','python_pid':B.PYTHON['pid'],'python_get_process_birth':B.PYTHON['creation_utc'],'python_CIM_birth':'2026-11-17T15:58:55.9596260Z','CIM_birth_not_used_for_identity':True}
class ActualSchema(unittest.TestCase):
 def test_exact_new_raw_schema_projection_preserves_GetProcess_and_CIM_separation(self):
  x=raw();before=copy.deepcopy(x);out=B.adapt_actual_api_detail(x)
  self.assertEqual(x,before);self.assertEqual(out['get_process_start_time_utc'],B.PYTHON['creation_utc']);self.assertEqual(out['cim_creation_utc'],x['python_CIM_birth']);self.assertNotEqual(out['get_process_start_time_utc'],out['cim_creation_utc'])
 def test_missing_extra_or_old_schema_is_refused(self):
  for value in [{k:v for k,v in raw().items() if k!='precision'},{**raw(),'unreviewed':True},{'format':'has_root_python_birth_api_observation_1','pid':B.PYTHON['pid']}]:
   with self.assertRaises(ValueError):B.adapt_actual_api_detail(value)
 def test_wrong_schema_API_precision_and_identity_types_refuse(self):
  for key,value in [('format','old'),('identity_api','CIM'),('precision',100),('python_pid',float(B.PYTHON['pid'])),('python_pid',True),('python_pid',1),('python_get_process_birth','2026-11-17T15:58:55.9596260Z')]:
   x=raw();x[key]=value
   with self.assertRaises(ValueError):B.adapt_actual_api_detail(x)
 def test_CIM_metadata_cannot_claim_identity_or_invalid_timestamp(self):
  for key,value in [('CIM_birth_not_used_for_identity',False),('CIM_birth_not_used_for_identity',1),('python_CIM_birth',None),('python_CIM_birth','not UTC')]:
   x=raw();x[key]=value
   with self.assertRaises(ValueError):B.adapt_actual_api_detail(x)
if __name__=='__main__':unittest.main()
