from pathlib import Path
import datetime,gzip,hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
run=root/'output/windows-canonical-bone-binding-20261114T040946652'
dest=root/'experiments/owner_pause_20261114'
assert not dest.exists();dest.mkdir()
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=read(run/'state.json');pause=read(run/'user-pause-request.json');host=read(run/'user-pause-host-terminal.json')
before=read(run/'source-before.json');after=read(run/'source-after.json')
assert before==after and len(before['source_sha256'])==1008 and state['source_unchanged']
assert state['status']=='failed' and state['suite_exit']==-1 and host['owner_pause_requested'] and host['owned_runtime_command_matches_absent']
assert host['full_verification']=='USER_CANCELLED_INCOMPLETE_NOT_PASS' and host['no_process_killed'] is False
for name in ['state.json','launch.json','source-before.json','source-after.json','coordinator-children-observed.json','user-pause-request.json','user-pause-host-terminal.json','coordinator.stdout.log','coordinator.stderr.log']:
 raw=(run/name).read_bytes();path=dest/(name+'.gz' if len(raw)>65536 else name)
 path.write_bytes(gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw)
 if path.suffix=='.gz':assert gzip.decompress(path.read_bytes())==raw
raw=(run/'canonical.log').read_bytes();(dest/'partial-canonical.log.gz').write_bytes(gzip.compress(raw,mtime=0))
preps=[
 ('windows-canonical-bone-binding-retry-publication-prep-20261114','*.json'),
 ('sfm-joints-review-builder-amendment-20261114','*.json'),
 ('sfm-joints-final-validator-amendment-20261114','*.json'),
 ('sfm-joints-review-independent-audit-20261114','*.json'),
 ('native-jiggle-headless-transport-prep-20261114','*.json'),
 ('native-jiggle-headless-independent-audit-20261114','*.json'),
 ('old-native-exclusive-read-prep-20261114','*.json'),
]
prep_info=[]
for folder,_ in preps:
 source=root/'output'/folder;assert source.is_dir(),folder
 target=dest/'prepared-unrun'/folder
 rows=[]
 for path in sorted(source.iterdir()):
  if not path.is_file() or path.suffix.lower() not in {'.json','.py','.gd','.md'}:continue
  # Only top-level public code/metadata. Never descend into private-oracle folders.
  assert path.stat().st_size<1024*1024,str(path)
  out=target/path.name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
  rows.append({'name':path.name,'sha256':sha(path),'bytes':path.stat().st_size})
 prep_info.append({'folder':folder,'files':rows,'execution':'UNRUN and pinned prior-full context is INELIGIBLE after owner cancellation'})
for name in ['start_canonical_bone_binding_owned.ps1','close_canonical_bone_binding_retry_owned.ps1','save_owner_pause_20261114.py']:
 shutil.copyfile(root/'output'/name,dest/name)
dt=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
summary={'format':'has_owner_requested_pause_20261114_1','status':'PAUSED_BY_OWNER','source_commit':state['source_commit'],
 'full_verification':'USER_CANCELLED_INCOMPLETE_NOT_PASS','raw_runner_status':state['status'],'raw_runner_exit':state['suite_exit'],
 'elapsed_seconds':(dt(state['finished_utc'])-dt(state['started_utc'])).total_seconds(),
 'functional_sources':1008,'source_and_head_unchanged':True,'owned_coordinator_and_python_absent':True,
 'owned_runtime_commands_absent':True,'owned_test_tree_terminated_on_owner_request':True,'computer_shutdown':False,
 'new_full_software_failure_observed':False,'partial_log_sha256':hashlib.sha256(raw).hexdigest(),
 'partial_progress':'Fresh run passed prior helper guard208CPU/266GPU and later contact/selection/transform/viewport/motion/drawing checks before owner pause; final audio/media/recovery completion not certified.',
 'preserve_failures':'Earlier EE audio full and c4d review-guard full remain FAILED.',
 'unrun_preparations':prep_info,
 'review_package_built':False,'proposed_final_review_checks':168,'proposed_headless_transport_checks':41588,
 'native_Source_solver_implemented':False,'formal_acceptance':'55/62 unchanged','implementation':'52/54 unchanged',
 'cleanup':'NONE; all originals/stages/shared tools/current useful runs/reviews/recovery/private oracles retained',
 'private_storage':'Full native artwork, GLB/HAS/media, full rest/fingerprints, native oracle/private-preparation INPUT_LOCK and complete SDK source remain local; no private data copied into this packet.',
 'resume':'Owner must resume. Fetch latest main/read master+history. Start fresh complete Windows run with current exact context; do not admit paused f380 run or execute its PASS-gated recipes. Regenerate/review successors for actual future commit/run/host proof, then build/replay review and optionally run headless transport.'}
(dest/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(dest).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_metadata_source_packet_index_1','files':rows},indent=2)+'\n',encoding='utf-8')
benchmark={k:v for k,v in summary.items() if k!='unrun_preparations'}
benchmark.update(evidence=dest.relative_to(root).as_posix(),evidence_index_sha256=sha(dest/'INDEX.json'))
path=root/'docs/benchmarks/windows_owner_pause_2026-11-13.json';assert not path.exists();path.write_text(json.dumps(benchmark,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'index_sha256':sha(dest/'INDEX.json'),'elapsed_seconds':summary['elapsed_seconds']}))
