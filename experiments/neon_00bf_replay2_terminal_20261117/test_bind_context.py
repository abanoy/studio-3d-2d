"""Synthetic binding metadata only; no active-run read or process query."""
import copy
import unittest
from unittest.mock import patch

import bind_context as B


def metadata():
    digest='d'*64
    before={'commit':B.COMMIT,'source_sha256':{'synthetic/'+str(i):'0'*64 for i in range(1028)}}
    before['source_sha256']['tests/verify.py']=digest
    launch={'format':'has_root_neon_full_launch_1','source_commit':B.COMMIT,
            'coordinator_pid':B.COORDINATOR['pid'],'coordinator_creation_utc':B.COORDINATOR['creation_utc'],
            'run_folder':str(B.RUN),'functional_source_files':1029,'runner':str(B.RUNNER),
            'runner_sha256':B.RUNNER_SHA,'graphics_lease':'root-exclusive'}
    birth={'format':'has_root_neon_corrected_birth_observation_1',
           'coordinator':copy.deepcopy(B.COORDINATOR),'python':copy.deepcopy(B.PYTHON)}
    api={'format':'has_root_python_birth_api_observation_1','pid':B.PYTHON['pid'],
         'get_process_start_time_utc':B.PYTHON['creation_utc'],
         'cim_creation_utc':'2026-11-17T15:58:55.9596268Z',
         'terminal_identity_api':'Get-Process.StartTime, same as pinned creation_utc'}
    return before,launch,birth,api,digest


class BindTests(unittest.TestCase):
    def test_exact_synthetic_bindings_accept(self):
        B.validate(*metadata())

    def test_wrong_commit_count_digest_or_traversal_refuses(self):
        for action in [lambda v:v[0].update(commit='0'*40),
                       lambda v:v[0]['source_sha256'].pop('synthetic/0'),
                       lambda v:v[0]['source_sha256'].update({'synthetic/0':True}),
                       lambda v:v[0]['source_sha256'].update({'synthetic/0':'not-a-digest'}),
                       lambda v:v[0]['source_sha256'].update({'tests/verify.py':'0'*64}),
                       lambda v:v[0]['source_sha256'].update({'../escape':v[0]['source_sha256'].pop('synthetic/0')})]:
            values=list(metadata());action(values)
            with self.assertRaises(ValueError):B.validate(*values)

    def test_birth_parent_command_and_numeric_alias_refuse(self):
        for section,key,value in [('coordinator','pid',float(B.COORDINATOR['pid'])),
                                  ('python','pid',float(B.PYTHON['pid'])),
                                  ('python','parent_pid',1),('python','command_line','python wrong.py'),
                                  ('python','creation_utc','2026-11-17T15:58:55.9596268Z')]:
            values=list(metadata());values[2][section][key]=value
            with self.assertRaises(ValueError):B.validate(*values)

    def test_run_scope_runner_lease_and_exact_count_refuse(self):
        for key,value in [('run_folder',str(B.REVIEW/'output/other')),('runner','C:\\wrong.ps1'),
                          ('runner_sha256','0'*64),('graphics_lease','shared'),
                          ('functional_source_files',1029.0),('coordinator_pid',True),
                          ('coordinator_creation_utc','2026-11-17T15:58:55.2656635Z')]:
            values=list(metadata());values[1][key]=value
            with self.assertRaises(ValueError):B.validate(*values)

    def test_GetProcess_identity_not_CIM_precision_alias(self):
        values=list(metadata());B.validate(*values)
        self.assertEqual(B.ns(values[3]['get_process_start_time_utc'])-B.ns(values[3]['cim_creation_utc']),100)
        values[3]['get_process_start_time_utc']=values[3]['cim_creation_utc']
        with self.assertRaises(ValueError):B.validate(*values)

    def test_API_pid_type_or_identity_source_mutation_refuses(self):
        for key,value in [('pid',float(B.PYTHON['pid'])),('format','wrong'),
                          ('terminal_identity_api','CIM'),('cim_creation_utc','not-UTC')]:
            values=list(metadata());values[3][key]=value
            with self.assertRaises(ValueError):B.validate(*values)

    def test_nonimmutable_names_refuse_before_any_path_access(self):
        with patch.object(B,'safe',side_effect=AssertionError('No filesystem access allowed')):
            for name in ['state.json','source-after.json','canonical.log','verification.json','../launch.json']:
                with self.assertRaises(ValueError):B.read_input(name)

    def test_exact_four_input_policy_and_numeric_types(self):
        self.assertEqual(B.INPUTS,('source-before.json','launch.json','root-birth-observation.json','root-birth-api-detail.json'))
        self.assertTrue(B.typed_same(B.COORDINATOR,copy.deepcopy(B.COORDINATOR)))
        self.assertFalse(B.typed_same(B.COORDINATOR,{'pid':float(B.COORDINATOR['pid']),'creation_utc':B.COORDINATOR['creation_utc']}))


if __name__=='__main__':unittest.main()
