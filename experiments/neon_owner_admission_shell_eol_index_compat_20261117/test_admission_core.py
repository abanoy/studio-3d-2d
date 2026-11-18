"""Synthetic metadata/source bytes only; no copy/native/full-output operations."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,json,unittest
import admission_core as A
HERE=Path(__file__).resolve().parent
CTX={'commit':'a'*40,'checkout':r'C:\synthetic\candidate','run_name':'synthetic-UNRUN','functional_sources':1029,'coordinator_pid':1,'coordinator_birth':'2026-11-17T01:27:35.0000000Z','python_pid':2,'python_birth':'2026-11-17T01:27:35.1000000Z','runner':'synthetic.ps1','runner_sha256':'1'*64,'python_executable':r'C:\synthetic\python.exe','python_command':'synthetic python command'}
CTX['registry_sha256']=A.digest((HERE/'reference_registry.json').read_bytes().replace(b'375ec05e925159850ff3b0abf2e8f98f9d2ce129',CTX['commit'].encode()))
# Reuse only authored synthetic metadata builders, not their validator or live context.
source=ast.parse((HERE/'reference_test_terminal.py').read_bytes())
nodes=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in {'receipt','metadata','result'}]
for node in ast.walk(ast.Module(body=nodes,type_ignores=[])):
 if isinstance(node,ast.Constant) and node.value=='RESULT_REGISTRY.json':node.value='reference_registry.json'
ns={'copy':copy,'json':json,'Path':Path,'C':SimpleNamespace(CONTEXT=CTX,HERE=HERE)}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<authored synthetic metadata>','exec'),ns)

def obs():
 return {'coordinator':{'pid':1,'expected_creation_utc':CTX['coordinator_birth'],'pid_present':False,'current_creation_utc':None,'original_absent':True},'python':{'pid':2,'expected_creation_utc':CTX['python_birth'],'pid_present':False,'current_creation_utc':None,'original_absent':True},'owned_runtime_matches':[],'owned_runtime_command_matches_absent':True,'root_observer_issued_no_termination':True,'observer_retained_Popen_reaped':True,'observed_utc':'2026-11-17T02:28:00.0000000Z'}
def bundle():
 state,birth,launch,before,after,_=ns['metadata']();full,registry=ns['result']();registry['source_commit']=CTX['commit']
 normal=ns['receipt']();cancel=ns['receipt']();cancel.update(desktop='HAS_Test_synthetic_cancel',child_pid=124,exit=2,cancelled=True,error='Owned converter cancelled')
 classes={normal['desktop']:'normal_exit0',cancel['desktop']:'registered_Krita_cancel_exit2'}
 inv={'format':'has_neon_ffcf_terminal_receipt_inventory_1','source_commit':CTX['commit'],'run_directory':state['run_folder'],'suite_status':'passed','suite_exit':0,'functional_sources':1029,'result_groups':158,'core_groups':36,'movie_groups':21,'full_suite_passed':True,'final_full_report_used':True,'all_collected_jobs_desktops_closed_private':True,'all_inline_exact_physical_matches':True,'root_observer_issued_no_termination':True,'registered_cancel_observed':True,'rows':[{'receipt':normal,'classification':'normal_exit0'},{'receipt':cancel,'classification':'registered_Krita_cancel_exit2'}],'inline_receipts':[{'receipt':copy.deepcopy(normal)},{'receipt':copy.deepcopy(cancel)}],'unique_physical_jobs':2,'unique_job_classifications':classes,'physical_receipt_files':2,'normal_exit0':1,'registered_cancel_exit2':1,'failed_partial_nonzero':0,'process_observation':obs()}
 release={'format':'has_root_neon_ffcf_graphics_lease_release_1','released':True,'release_kind':'closed_passed_full_run','source_commit':CTX['commit'],'canonical_run':CTX['run_name'],'coordinator_pid':1,'python_pid':2,'functional_sources':1029,'physical_jobs':2,'physical_receipt_files':2,'suite_exit':0,'full_suite_passed':True,'final_full_report_used':True,'all_collected_jobs_desktops_closed_private':True,'all_inline_exact_physical_matches':True,'root_observer_issued_no_termination':True,'released_utc':obs()['observed_utc'],'second_identity_and_scope_observation':obs()}
 docs={'state':state,'birth':birth,'launch':launch,'before':before,'after':after,'full_report':full,'inventory':inv,'release':release}
 return docs,registry

def arguments(docs,registry,canonical=True):
 raw={k:A.encoded(v) for k,v in docs.items() if k!='release'}
 release=copy.deepcopy(docs['release']);release['receipt_inventory_sha256']=A.digest(raw['inventory']);release['terminal_state_sha256']=A.digest(raw['state']);raw['release']=A.encoded(release)
 raw['canonical_log']=(b'PASS authored synthetic step\n'+raw['full_report']) if canonical else b'not the complete report'
 return raw,copy.deepcopy(CTX),registry,{k:A.digest(v) for k,v in raw.items()},A.REF['ns'](docs['state']['started_utc'])+1

def sources():
 work={'src/f%04d.gd'%i:('authored%d\n'%i).encode() for i in range(1029)};work['src/f0000.gd']=b'authored0\r\n'
 git={k:v.replace(b'\r\n',b'\n') for k,v in work.items()};tested={k:A.digest(v) for k,v in work.items()}
 recipe={k:{'tested_working_sha256':tested[k],'git_blob_sha256':A.digest(git[k]),'canonical_content_sha256':A.digest(A.canonical(v,k)),'source_mode':'exact_Git_and_tested_working_bytes' if v==git[k] else 'candidate_tested_raw_with_explicit_Git_CRLF_LF_bridge'} for k,v in work.items()}
 return tested,work,git,recipe,'b'*40,True

def bridge():
 old={'src/f%04d.gd'%i:{'raw_sha256':A.digest(str(i).encode()),'content_sha256':A.digest(str(i).encode())} for i in range(1019)};new=copy.deepcopy(old)
 for i in range(1019,1029):new['src/f%04d.gd'%i]={'raw_sha256':A.digest(str(i).encode()),'content_sha256':A.digest(str(i).encode())}
 for i in range(3):new['src/f%04d.gd'%i]={'raw_sha256':A.digest(('changed%d'%i).encode()),'content_sha256':A.digest(('changed%d'%i).encode())}
 rows=[]
 for name,row in new.items():
  prior=old.get(name)
  if prior is not None and prior['content_sha256']==row['content_sha256']:continue
  rows.append({'path':name,'classification':'added' if prior is None else 'modified','old_raw_sha256':prior['raw_sha256'] if prior else None,'old_content_sha256':prior['content_sha256'] if prior else None,'new_raw_sha256':row['raw_sha256'],'new_content_sha256':row['content_sha256']})
 return old,new,rows

class CandidateAdmission(unittest.TestCase):
 def test_current_activation_is_UNREADY_even_for_favorable_claims(self):
  for value in [None,b'{}',A.encoded({'passed':True,'status':'qualified'})]:
   with self.assertRaisesRegex(ValueError,'UNREADY'):A.require_activation(value)
 def test_hypothetical_actual_schema_full_and_dynamic_closure_passes_pure_check_only(self):
  d,r=bundle();out=A.check_candidate_bundle(*arguments(d,r));self.assertEqual(out['physical_jobs'],2);self.assertTrue(out['outer_actual_activation_still_required'])
 def test_failed_running_or_focused_cannot_replace_fullPASS(self):
  for status in ('failed','running','runner_error'):
   d,r=bundle();d['state'].update(status=status,suite_exit=1)
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_missing_extra_or_changed_raw_artifact_is_refused(self):
  d,r=bundle();args=list(arguments(d,r));args[0]['state']+=b' '
  with self.assertRaises(ValueError):A.check_candidate_bundle(*args)
  d,r=bundle();args=list(arguments(d,r));args[0].pop('birth')
  with self.assertRaises(ValueError):A.check_candidate_bundle(*args)
 def test_birth_parent_command_lease_and_source_mutations_refuse(self):
  changes=[('birth',lambda x:x['python'].update(parent_pid=3)),('launch',lambda x:x.update(graphics_lease='shared')),('after',lambda x:x['source_sha256'].update({'synthetic/0':'1'*64})),('state',lambda x:x.update(pid=1.0)),('state',lambda x:x.update(script_sha256='0'*64))]
  for field,change in changes:
   d,r=bundle();change(d[field])
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_all_158_36_21_and_Neon_12504_predicates_retained(self):
  for change in [lambda x:x.pop('unit'),lambda x:x['neon_workspace'].update(checks=12503),lambda x:x['neon_workspace'].update(checks=12504.0),lambda x:x.update(actual_mmd_tested=False),lambda x:x['posed_model_video_0'].update(frames=47)]:
   d,r=bundle();change(d['full_report'])
   with self.assertRaises((ValueError,KeyError)):A.check_candidate_bundle(*arguments(d,r))
 def test_fresh_log_suffix_and_report_time_required(self):
  d,r=bundle()
  with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r,False))
  args=list(arguments(d,r));args[-1]=0
  with self.assertRaises(ValueError):A.check_candidate_bundle(*args)
 def test_bad_physical_receipt_or_unregistered_cancel_refuses(self):
  for change in [lambda x:x['rows'][0]['receipt'].update(job_closed=False),lambda x:x.update(registered_cancel_observed=False),lambda x:x['rows'][1]['receipt'].update(error='unknown cancellation'),lambda x:x.update(failed_partial_nonzero=1)]:
   d,r=bundle();change(d['inventory'])
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_duplicate_identical_receipts_count_jobs_once(self):
  d,r=bundle();d['inventory']['rows'].append(copy.deepcopy(d['inventory']['rows'][0]));d['inventory']['physical_receipt_files']=3;d['release']['physical_receipt_files']=3
  out=A.check_candidate_bundle(*arguments(d,r));self.assertEqual(out['physical_jobs'],2)
 def test_inline_mismatch_or_physical_count_guess_refuses(self):
  for change in [lambda x:x['inline_receipts'][0]['receipt'].update(child_pid=999),lambda x:x.update(unique_physical_jobs=192),lambda x:x.update(normal_exit0=True)]:
   d,r=bundle();change(d['inventory'])
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_no_release_failure_release_or_wrong_birth_refuses(self):
  for change in [lambda x:x.update(released=False),lambda x:x.update(release_kind='closed_failed_partial_run'),lambda x:x.update(full_suite_passed=False),lambda x:x.update(coordinator_pid=True),lambda x:x['second_identity_and_scope_observation']['python'].update(original_absent=False)]:
   d,r=bundle();change(d['release'])
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_PID_reuse_allowed_only_when_original_identity_absent(self):
  d,r=bundle()
  for observation in [d['inventory']['process_observation'],d['release']['second_identity_and_scope_observation']]:observation['python'].update(pid_present=True,current_creation_utc='2026-11-17T02:27:59.0000000Z')
  A.check_candidate_bundle(*arguments(d,r))
  d['release']['second_identity_and_scope_observation']['python']['current_creation_utc']=CTX['python_birth']
  with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_root_scope_or_observer_or_no_termination_conditions_refuse(self):
  for key,value in [('owned_runtime_matches',[{}]),('owned_runtime_command_matches_absent',False),('root_observer_issued_no_termination',False),('observer_retained_Popen_reaped',False)]:
   d,r=bundle();d['inventory']['process_observation'][key]=value
   with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_registry_cannot_rename_a_required_core_group_or_refresh_schema(self):
  d,r=bundle();d['full_report']['unreviewed_replacement_core']=d['full_report'].pop('unit')
  for field in ['expected_result_keys','expected_core_process_keys']:r[field]=['unreviewed_replacement_core' if k=='unit' else k for k in r[field]]
  with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
  d,r=bundle();r['verifier_sha256']='0'*64
  with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_registry_commit_mismatch_refuses(self):
  d,r=bundle();r['source_commit']='f'*40
  with self.assertRaises(ValueError):A.check_candidate_bundle(*arguments(d,r))
 def test_duplicate_metadata_keys_refuse(self):
  with self.assertRaises(ValueError):A.parse(b'{"passed":true,"passed":false}')

class SourceBridge(unittest.TestCase):
 def test_exact_tested_raw_working_bytes_with_explicit_git_EOL_bridge(self):
  out=A.check_merged_sources(*sources());self.assertEqual(out['source_files'],1029);self.assertEqual(out['copy_source_mode'],'candidate_tested_raw_bytes')
 def test_EOL_optin_does_not_admit_changed_content_or_missing_file(self):
  for change in [lambda a:a[1].update({'src/f0000.gd':b'changed\n'}),lambda a:a[1].pop('src/f0000.gd'),lambda a:a[2].update({'src/f0000.gd':b'changed\n'})]:
   args=list(sources());change(args)
   with self.assertRaises(ValueError):A.check_merged_sources(*args)
 def test_no_implicit_EOL_or_wrong_source_mode_recipe(self):
  args=list(sources());args[-1]=False
  with self.assertRaises(ValueError):A.check_merged_sources(*args)
  args=list(sources());args[3]['src/f0000.gd']['source_mode']='exact_Git_and_tested_working_bytes'
  with self.assertRaises(ValueError):A.check_merged_sources(*args)
 def test_nontext_EOL_normalization_refuses(self):
  args=list(sources())
  for mapping in args[:4]:mapping['data/fake.png']=mapping.pop('src/f0000.gd')
  args[3]['data/fake.png']['canonical_content_sha256']=A.digest(args[1]['data/fake.png'])
  with self.assertRaises(ValueError):A.check_merged_sources(*args)
 def test_loneCR_or_recipe_hash_edit_cannot_hide_changed_bytes(self):
  args=list(sources());args[1]['src/f0000.gd']+=b'\r'
  with self.assertRaises(ValueError):A.check_merged_sources(*args)
  args=list(sources());args[3]['src/f0000.gd']['git_blob_sha256']='0'*64
  with self.assertRaises(ValueError):A.check_merged_sources(*args)
 def test_reviewed_second_bridge_has_no_guessed_changed_count(self):
  out=A.check_reviewed_delta(*bridge());self.assertEqual(len(out['changed_or_added_files']),13);self.assertTrue(out['historical_native_to52_bridge_still_separately_required'])
 def test_second_bridge_missing_extra_wrong_hash_or_duplicate_refuses(self):
  for change in [lambda a:a[2].pop(),lambda a:a[2].append(copy.deepcopy(a[2][0])),lambda a:a[2][0].update(new_raw_sha256='0'*64),lambda a:a[2].append({'path':'src/f0999.gd'})]:
   args=list(bridge());change(args)
   with self.assertRaises(ValueError):A.check_reviewed_delta(*args)
 def test_second_bridge_removal_or_invalid_identity_refuses(self):
  args=list(bridge());args[1]['src/added.gd']=args[1].pop('src/f1000.gd')
  with self.assertRaises(ValueError):A.check_reviewed_delta(*args)
  args=list(bridge());args[1]['src/f0000.gd']['raw_sha256']=True
  with self.assertRaises(ValueError):A.check_reviewed_delta(*args)
 def test_plan_joins_the_same_candidate_and_merged_source_map(self):
  candidate={'candidate_commit':'a'*40,'candidate_source_map_sha256':'c'*64,'outer_actual_activation_still_required':True}
  merged={'merged_revision':'b'*40,'source_files':1029,'tested_working_map_sha256':'c'*64,'tested_content_map_sha256':'e'*64,'copy_source_mode':'candidate_tested_raw_bytes','actual_activation_and_clean_Git_preflight_still_required':True}
  historical={'historical_bridge_preserved':True,'historical52_target_map_joined':True,'old52_raw_source_map_sha256':'1'*64,'old52_content_source_map_sha256':'2'*64};delta={'old_files':1019,'new_files':1029,'old_raw_source_map_sha256':'1'*64,'old_content_source_map_sha256':'2'*64,'new_raw_source_map_sha256':'c'*64,'new_content_source_map_sha256':'e'*64,'historical_native_to52_bridge_still_separately_required':True}
  plan=A.assemble_copy_proposal(candidate,merged,historical,delta);self.assertIs(plan['execution_authorized'],False)
  merged['tested_working_map_sha256']='d'*64
  with self.assertRaises(ValueError):A.assemble_copy_proposal(candidate,merged,historical,delta)
 def test_unrelated_delta_or_missing_historical52_witness_cannot_assemble_chain(self):
  candidate={'candidate_commit':'a'*40,'candidate_source_map_sha256':'c'*64,'outer_actual_activation_still_required':True}
  merged={'merged_revision':'b'*40,'source_files':1029,'tested_working_map_sha256':'c'*64,'tested_content_map_sha256':'e'*64,'copy_source_mode':'candidate_tested_raw_bytes','actual_activation_and_clean_Git_preflight_still_required':True}
  historical={'historical_bridge_preserved':True,'historical52_target_map_joined':True,'old52_raw_source_map_sha256':'1'*64,'old52_content_source_map_sha256':'2'*64}
  delta={'old_files':1019,'new_files':1029,'old_raw_source_map_sha256':'1'*64,'old_content_source_map_sha256':'2'*64,'new_raw_source_map_sha256':'c'*64,'new_content_source_map_sha256':'e'*64,'historical_native_to52_bridge_still_separately_required':True}
  for field in ['old_raw_source_map_sha256','old_content_source_map_sha256','new_raw_source_map_sha256','new_content_source_map_sha256']:
   wrong=copy.deepcopy(delta);wrong[field]='9'*64
   with self.assertRaises(ValueError):A.assemble_copy_proposal(candidate,merged,historical,wrong)
  historical['historical52_target_map_joined']=False
  with self.assertRaises(ValueError):A.assemble_copy_proposal(candidate,merged,historical,delta)
 def test_historical_native52_bridge_and_lock_are_exact_immutable_dependencies(self):
  root=HERE.parent/'native_five_review_after_full_20261116';lock=(root/'builder/input-lock.json').read_bytes();delta=(root/'source-delta.json').read_bytes()
  witness=A.check_historical_predecessors(lock,delta);self.assertTrue(witness['historical_bridge_preserved']);self.assertIs(witness['historical52_target_map_joined'],False)
  with self.assertRaises(ValueError):A.check_historical_predecessors(lock,delta,b'{}',{})
  with self.assertRaises(ValueError):A.check_historical_predecessors(lock+b' ',delta)
  with self.assertRaises(ValueError):A.check_historical_predecessors(lock,delta+b' ')

if __name__=='__main__':unittest.main()
