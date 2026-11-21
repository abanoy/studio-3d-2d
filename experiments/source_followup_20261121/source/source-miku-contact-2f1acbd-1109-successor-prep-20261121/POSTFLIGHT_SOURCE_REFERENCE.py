"""Fresh1109/183 postflight, including exact headless vs graphical receipts."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,stat,subprocess,time
CONTROL=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--checkout',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--outer',type=Path,required=True);p.add_argument('--revision',required=True);p.add_argument('--root-exec-reaped-confirmed',action='store_true',required=True);a=p.parse_args()
ROOT=a.checkout.resolve(strict=True);RUN=a.run.resolve(strict=True);OUTER=a.outer.resolve(strict=True)
assert RUN.parent==OUTER.parent==ROOT/'output' and ROOT.name.startswith('has-import-info-full-20261121-')
def raw(path):
 for parent in (path,*path.parents):
  s=parent.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
 s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 data=path.read_bytes();t=path.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns);return data
def strict_json(data):
 def pairs(items):
  result={}
  for k,v in items:assert k not in result;result[k]=v
  return result
 return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
def value(path):return strict_json(raw(path))
def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.autocrlf=false','-c','core.longpaths=true',*args],cwd=ROOT).decode().strip()
completion=value(RUN/'completion.json');report=value(ROOT/'output/verification.json');before=value(RUN/'source-before.json');after=value(RUN/'source-after.json')
launch=value(RUN/'launch.json');outer=value(OUTER/'launch.json');done=value(OUTER/'completion.json');provenance=value(RUN/'receipt-provenance.json')
remote=value(CONTROL/'IMPORT_INFO_REMOTE_VERIFIED_20261121.json')
contract_raw=raw(CONTROL/'FULL183_GROUP_CONTRACT_20261121.json')
assert len(contract_raw)==6076 and sha(contract_raw)=='d7bd9c53add4088d88a05d575a34752ed9ac15e802755f0ff8cb13142f5da0f4'
contract=strict_json(contract_raw)
assert contract['format']=='has_exact_full183_group_contract_1' and contract['functional_sources']==1109 and contract['new_import_info_checks']==267
assert len(contract['expected_group_keys'])==len(set(contract['expected_group_keys']))==183
assert len(contract['new_groups'])==12 and sum(contract['new_groups'].values())==626 and len(set(contract['movie_groups']))==21
assert git('rev-parse','HEAD')==a.revision==completion['revision']==launch['revision']==outer['revision']==remote['revision']
assert remote['format']=='has_import_info_remote_verification_1' and remote['status']=='PASS' and remote['functional_source_count']==1109
assert remote['remote_main_before_after']==a.revision and Path(remote['fresh_checkout'])==ROOT
assert all(remote[k] is True for k in ('all_selected_raw_sha256_git_blobs_modes_exact','functional_raw_bytes_and_membership_exact','clean_before_fixtures'))
assert completion['format']=='has_reference_body_full_coordinator_1' and outer['format']=='has_import_info_full_outer_launch_1' and done['format']=='has_import_info_full_outer_completion_1'
assert completion['exit']==done['exit']==0 and completion['whole_verifier_pass'] is True
assert all(completion[k] is True for k in ('child_reaped','functional_sources_unchanged','revision_unchanged','fresh_final_report','all_private_jobs_isolated_closed','nonzero_jobs_are_expected_cancellations','receipt_provenance_verified'))
assert all(done[k] is True for k in ('child_reaped','parent_environment_unchanged','coordinator_source_unchanged','revision_unchanged'))
assert before==after and len(before)==1109 and completion['functional_source_count']==1109
assert set(report)==set(contract['expected_group_keys']) and len(report)==completion['result_groups']==183
for name,count in contract['new_groups'].items():
 group=report[name]
 assert group['status']=='PASS' and type(group['checks']) is int and group['checks']==count and group['all_admitted_sources_unchanged'] is True and group['source_preservation_failures']==[]
 if name.startswith('editor_controls_'):
  label=name.removeprefix('editor_controls_');expected_cases={label:count}
  assert group['scope']==label and group['generated_fixture_preserved'] is True
 elif name=='camera_interactions_pure':expected_cases={'cold-wire':29,'key-edits':26,'lens-plan':12};assert group['scope']=='pure'
 else:
  label=name.removeprefix('camera_interactions_');expected_cases={'timeline-'+label:34,'lens-'+label:22};assert group['scope']=='variant'
 assert len(group['cases'])==len(expected_cases) and {r['name'] for r in group['cases']}==set(expected_cases)
 for case in group['cases']:
  expected_count=expected_cases[case['name']];marker=case['report']
  assert type(case['checks']) is int and case['checks']==expected_count and type(marker['checks']) is int and marker['checks']==expected_count and type(marker['failures']) is int and marker['failures']==0
assert sum(report[k]['checks'] for k in contract['new_groups'])==626
actual_movies=sorted(k for k in report if k.endswith('_video') or k.startswith('posed_model_video_'))
assert actual_movies==sorted(completion['movie_groups'])==sorted(contract['movie_groups']) and len(actual_movies)==21
info=report['import_capability'];assert info['status']=='PASS' and info['scope']=='all' and info['checks']==267 and len(info['cases'])==21 and len(info['pairs'])==8
info_case_counts={'legacy43':43,**{'app-'+theme+'-'+mode:30 for theme in ('classic','neon') for mode in ('simple','advanced')}}
info_pair_names={theme+'-'+str(scale)+'-'+mode for theme in ('classic','neon') for scale in (100,150) for mode in ('simple','advanced')}
for label in info_pair_names:info_case_counts['writer-'+label]=7;info_case_counts['reader-'+label]=6
assert len({r['name'] for r in info['cases']})==21 and {r['name'] for r in info['cases']}==set(info_case_counts)
assert {r['name'] for r in info['pairs']}==info_pair_names and all(r['writer_offline'] is True and r['writer_restored'] is True for r in info['pairs'])
for case in info['cases']:
 count=info_case_counts[case['name']];marker=case['report']
 assert case['status']=='PASS' and type(case['checks']) is int and case['checks']==count and type(marker['checks']) is int and marker['checks']==count and type(marker['failures']) is int and marker['failures']==0
 assert all(case[k] is True for k in ('launcher_reaped','launcher_handle_closed','private_resources_closed')) and type(case['launcher_exit']) is int and case['launcher_exit']==0
assert sum(r['checks'] for r in info['cases'])==267
assert outer['pid']==launch['coordinator_pid']==done['pid'] and all(type(v) is int and v>0 for v in (outer['pid'],launch['pid']))
assert done['launch']==outer and Path(outer['checkout'])==ROOT and outer['parent_environment_changed'] is False and outer['hidden_console'] is True and outer['graphical_tests_must_use_private_desktops'] is True
assert launch['args'][1:]==['-B','-u','tests/verify.py'] and len(launch['args'])==4
expected_environment={'APPDATA':str(OUTER/'User/Roaming'),'LOCALAPPDATA':str(OUTER/'User/Local'),'TEMP':str(OUTER/'User/Temp'),'TMP':str(OUTER/'User/Temp'),'PYTHONDONTWRITEBYTECODE':'1'}
assert outer['child_environment']==expected_environment and launch['environment']['PYTHONDONTWRITEBYTECODE']=='1'
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):
 path=Path(expected_environment[key]);assert path.is_relative_to(OUTER/'User') and path.is_dir()
 for ancestor in (path,*path.parents):
  s=ancestor.lstat();assert not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400
  if ancestor==OUTER:break
assert outer['started_ns']<=launch['started_ns']<=(ROOT/'output/verification.json').stat().st_mtime_ns<=(RUN/'completion.json').stat().st_mtime_ns<=(OUTER/'completion.json').stat().st_mtime_ns
assert sha(raw(ROOT/'experiments/reference_body_20261120/run_full.py'))==outer['coordinator_sha256']
assert provenance['conflicts']==[] and provenance['changed_original_archives']==[]
spec=importlib.util.spec_from_file_location('_actual_full183_policy',ROOT/'experiments/reference_body_20261120/run_full.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
reclassified=F.classify(value(RUN/'prior-receipts.json'),F.receipts())
assert reclassified==provenance and not reclassified['conflicts'] and not reclassified['changed_original_archives']
admitted=F.import_info_headless_receipts(ROOT,report,provenance['current'],launch['started_ns'],(RUN/'completion.json').stat().st_mtime_ns,before)
assert len(admitted)==5 and admitted==completion['import_info_headless_receipts'] and completion['import_info_headless_admission_error'] is None
headless={row['path'] for row in admitted};desktops={}
for case in info['cases']:
 if case['headless'] is True:continue
 assert case['headless'] is False and case['graphical_placement_proven'] is True and case['private_receipt_mode']=='graphical_private_window'
 path=Path(case['private_receipt']);assert path.is_relative_to(ROOT)
 data=raw(path);proof=strict_json(data);relative=path.relative_to(ROOT).as_posix()
 assert sha(data)==case['private_receipt_sha256'] and type(case['private_child_pid']) is int and proof['child_pid']==case['private_child_pid']
 assert proof['child_desktop_confirmed'] is True and proof['private_window_seen'] is True and proof['maximum_owned_windows']>0
 matches=[r for r in provenance['current'] if r['path']==relative]
 assert len(matches)==1 and matches[0]['sha256']==sha(data) and matches[0]['value']==proof

for row in provenance['current']:
 path=ROOT/row['path'];assert path.resolve(strict=True).is_relative_to(ROOT)
 data=raw(path);assert sha(data)==row['sha256'] and json.loads(data)==row['value']
 proof=row['value'];assert proof['format']=='studio_private_desktop_1' and type(proof['exit']) is int and type(proof['child_pid']) is int and proof['child_pid']>0
 assert proof['job_closed'] is True and proof['desktop_closed'] is True and proof['foreground_child_observed'] is False and proof['desktop_switch_requested'] is False
 if row['path'] not in headless:assert proof['child_desktop_confirmed'] is True
 if proof['exit']!=0:assert proof['exit']==2 and proof.get('cancelled') is True and proof.get('error')=='Owned converter cancelled'
 key=proof['desktop']
 if key in desktops:assert desktops[key]['value']==proof
 else:desktops[key]=row
assert len(desktops)==completion['unique_current_private_jobs'] and len(provenance['current'])==completion['new_receipt_paths']
actual_nonzero=[r for r in desktops.values() if r['value']['exit']!=0]
assert len(actual_nonzero)==1 and actual_nonzero==completion['nonzero_private_jobs']
assert len(completion['current_jobs'])==len(desktops) and {r['value']['desktop']:r for r in completion['current_jobs']}==desktops
assert F.snapshot()==before and {k:v['git_sha1'] for k,v in before.items()}==F.committed_sources(a.revision)
expected=value(CONTROL/'IMPORT_INFO_FINAL_FUNCTIONAL_CATALOGUE_20261121.json');assert set(expected)==set(before)
for name,row in before.items():
 data=raw(ROOT/name);assert len(data)==row['bytes'] and sha(data)==row['sha256']==expected[name]['sha256']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_sha1']==expected[name]['git_sha1']
assert git('rev-parse','HEAD')==a.revision
result={'format':'has_import_info_full183_root_postflight_1','status':'PASS','revision':a.revision,'functional_sources':1109,'canonical_groups':183,'import_info_checks':267,'editor_camera_checks':626,'movie_groups':21,'current_private_jobs':len(desktops),'headless_lifecycle_jobs':5,'all_other_jobs_graphically_isolated':True,'all_jobs_closed_and_receipts_persisted':True,'source_raw_before_after_commit_exact':True,'retained_outer_process_reaped_environment_preserved':True,'seconds':completion['seconds'],'formal_acceptance':'55/62','human_device_observations_substituted':False,'recorded_ns':time.time_ns()}
target=CONTROL/'IMPORT_INFO_FULL183_ROOT_POSTFLIGHT_20261121.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
