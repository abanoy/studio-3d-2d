"""Synthetic-only CPU checks; never writes a lease or reads native/full files."""
from copy import deepcopy
import json
import math
from pathlib import Path
import unittest
from probe_support import validate_context,CONTEXT_FILES
from normal_metrics import pair,stats,summarize,candidate_bounds,exporter_axis_stage

HERE=Path(__file__).resolve().parent
COMMIT='a'*40


def synthetic_context():
    # Explicit test dictionaries only; not written as actual evidence/lease.
    run='SYNTHETIC_FULL';folder='C:/SYNTHETIC_ONLY/'+run
    hashes={key:(str(index+1)*64)[:64] for index,key in enumerate(sorted(CONTEXT_FILES))}
    source={'tests/verify.py':'459b90eeeae9d5523654c07fcbb3de27dad0e889943f46947333e8eb5a65437a'}
    state={'format':'has_owned_canonical_run_1','status':'passed','suite_exit':0,'source_unchanged':True,'source_commit':COMMIT,'pid':10,'process_started':'SYNTHETIC_BIRTH_A','run_folder':folder,'started_utc':'SYNTHETIC_START','finished_utc':'SYNTHETIC_FINISH'}
    birth={'format':'has_root_full_child_birth_observation_1','source_commit':COMMIT,'coordinator_pid':10,'coordinator_birth':'SYNTHETIC_BIRTH_A','python_pid':11,'python_birth':'SYNTHETIC_BIRTH_B','python_parent':10,'run_folder':folder}
    launch={'source_commit':COMMIT,'pid':10,'creation_utc':'SYNTHETIC_BIRTH_A','run_folder':folder}
    before={'commit':COMMIT,'source_sha256':source};hashes['source_after']=hashes['source_before']
    host={'source_commit':COMMIT,'canonical_run':run,'coordinator_pid':10,'python_pid':11,'expected_creation_utc':'SYNTHETIC_BIRTH_A','expected_python_creation_utc':'SYNTHETIC_BIRTH_B','raw_observation_sha256':hashes['raw_host'],'coordinator_absent':True,'python_absent':True,'owned_runtime_command_matches_absent':True,'source_before_after_and_current_exact':True,'functional_source_entries':1,'coordinator_matches':[],'owned_runtime_matches':[],'observed_utc':'SYNTHETIC_OBSERVATION'}
    raw={'source_commit':COMMIT,'state_status':'passed','suite_exit':0,'checked_utc':'SYNTHETIC_OBSERVATION','root_birth_observation_sha256':hashes['birth'],'canonical_run':folder,'owned_runtime_command_matches_absent':True,'owned_runtime_matches':[],'functional_source_entries':1,'source_before_after_and_current_exact':True,'coordinator':{'pid':10,'expected_creation_utc':'SYNTHETIC_BIRTH_A','original_absent':True},'python':{'pid':11,'expected_creation_utc':'SYNTHETIC_BIRTH_B','original_absent':True}}
    release={'format':'has_root_canonical_graphics_lease_release_1','released':True,'source_commit':COMMIT,'canonical_run':run,'coordinator_pid':10,'python_pid':11,'all_private_jobs_closed':True,'owned_runtime_command_matches_absent':True,'functional_source_entries':1,'canonical_state_sha256':hashes['state'],'host_proof_sha256':hashes['host'],'full_report_sha256':hashes['report'],'normalized_log_report_suffix_equal':True}
    return {'state':state,'launch':launch,'birth':birth,'source_before':before,'source_after':deepcopy(before),'report':{str(i):None for i in range(157)},'host':host,'raw_host':raw,'release':release},hashes,run


class ProbeTests(unittest.TestCase):
    def test_complete_synthetic_context_and_no_status_substitution(self):
        data,hashes,run=synthetic_context();self.assertEqual(validate_context(data,hashes,run,COMMIT,1),data['source_before']['source_sha256'])

    def test_running_failed_scope_and_string_pass_refused(self):
        for status in ('running','failed','runner_error','PASS',True):
            with self.subTest(status=status):
                data,h,r=synthetic_context();data['state']['status']=status
                with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_boolean_or_nonzero_suite_exit_refused(self):
        for value in (False,1,'0',None):
            data,h,r=synthetic_context();data['state']['suite_exit']=value
            with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_source_commit_birth_and_parent_mismatch_refused(self):
        for key,value in [('source_commit','b'*40),('coordinator_birth','other'),('python_parent',12),('coordinator_pid',12)]:
            data,h,r=synthetic_context();data['birth'][key]=value
            with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_source_drift_and_before_after_hash_refused(self):
        data,h,r=synthetic_context();data['source_after']['source_sha256']['added']='f'*64
        with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)
        data,h,r=synthetic_context();h['source_after']='f'*64
        with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_release_file_binds_state_report_and_host(self):
        for key in ('canonical_state_sha256','host_proof_sha256','full_report_sha256'):
            data,h,r=synthetic_context();data['release'][key]='0'*64
            with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_active_process_or_private_jobs_cannot_release(self):
        for section,key in [('host','python_absent'),('raw_host','owned_runtime_command_matches_absent'),('release','all_private_jobs_closed')]:
            data,h,r=synthetic_context();data[section][key]=False
            with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_wrong_registry_count_and_source_verifier_refused(self):
        data,h,r=synthetic_context();data['report'].pop('1')
        with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)
        data,h,r=synthetic_context();data['source_before']['source_sha256']['tests/verify.py']='f'*64;data['source_after']=deepcopy(data['source_before'])
        with self.assertRaises(ValueError):validate_context(data,h,r,COMMIT,1)

    def test_raw_length_error_cannot_be_hidden_by_normalization(self):
        result=pair((2,0,0),(1,0,0));self.assertEqual(result['raw_distance'],1);self.assertEqual(result['unit_direction_distance'],0);self.assertEqual(result['left_length_deviation'],1)
        summary=summarize([result]);self.assertEqual(summary['raw_distance']['diagnostic_above_2e_5'],1)

    def test_direction_change_separate_from_lengths(self):
        result=pair((1,0,0),(0,1,0));self.assertAlmostEqual(result['raw_distance'],math.sqrt(2));self.assertEqual(result['left_length_deviation'],0);self.assertEqual(result['right_length_deviation'],0)

    def test_zero_normal_has_explicit_undefined_direction(self):
        row=pair((0,0,0),(1,0,0));self.assertIsNone(row['unit_direction_distance']);self.assertEqual(stats([None])['undefined'],1);self.assertEqual(row['raw_distance'],1)

    def test_nonfinite_and_boolean_normals_refused(self):
        for bad in ((math.nan,0,1),(math.inf,0,1),(True,0,1),(0,1)):
            with self.assertRaises(ValueError):pair(bad,(0,0,1))

    def test_all_candidate_bounds_retain_adverse_witness(self):
        bounds=candidate_bounds((1,0,0),[(1,0,0),(0,1,0)]);self.assertEqual(bounds['raw_best'],0);self.assertAlmostEqual(bounds['raw_worst'],math.sqrt(2));self.assertAlmostEqual(bounds['unit_worst'],math.sqrt(2))
        with self.assertRaises(ValueError):candidate_bounds((1,0,0),[])

    def test_predicted_zero_fallback_precedes_axis_map_and_preserves_raw(self):
        raw=(0.,0.,0.);self.assertEqual(exporter_axis_stage(raw),(0.,1.,0.));self.assertEqual(raw,(0.,0.,0.))
        self.assertEqual(exporter_axis_stage((1,0,0)),(1.,0.,0.));self.assertEqual(exporter_axis_stage((0,1,0)),(0.,0.,-1.))
        self.assertEqual(exporter_axis_stage((0,0,1)),(0.,1.,0.))


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProbeTests);result=unittest.TestResult();suite.run(result)
    report={'format':'normal_probe_synthetic_cpu_1','test_methods':result.testsRun,'passed':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),'source':'Explicit synthetic context/vector dictionaries only; no actual full/native/model/Blender inputs loaded.','actual_lease_or_stage_created':False,'engine_CIM_Git_process_executed':False}
    (HERE/'CPU_TESTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
    for test,error in result.failures+result.errors:print(str(test)+'\n'+error)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
