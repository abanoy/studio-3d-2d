from pathlib import Path
import datetime,gzip,hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
run=root/'output/windows-canonical-bone-binding-20261114T033923681'
case=root/'output/helper-preview/cpu-1794628403016259600-7aa63609'
dest=root/'output/canonical-binding-guard-failure-20261114'
assert not dest.exists();dest.mkdir()
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=read(run/'state.json');before=read(run/'source-before.json');after=read(run/'source-after.json')
assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] and before==after
assert before['commit']=='c4d767489a43a7e8e38c5251be07814b1795d1a9' and len(before['source_sha256'])==1008
host=read(run/'authoritative-host-termination.json')
assert host['coordinator_absent'] and host['python_absent'] and host['owned_runtime_command_matches_absent'] and host['no_process_killed']
failed=read(case/'verification.json')
assert failed['checks']==0 and not failed['passed'] and not failed['graphical_process_attempted'] and failed['actual_res_root'] is None
assert failed['error']=='RuntimeError: Unreviewed helper main bytes: src/secondary_helper_editor.gd' and all(failed['preservation'].values())
for name in ['state.json','launch.json','source-before.json','source-after.json','coordinator-children-observed.json','authoritative-host-terminal.json','authoritative-host-termination.json','coordinator.stdout.log','coordinator.stderr.log']:
 shutil.copyfile(run/name,dest/name)
raw=(run/'canonical.log').read_bytes();(dest/'canonical.log.gz').write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress((dest/'canonical.log.gz').read_bytes())==raw
(dest/'failed-helper').mkdir();shutil.copyfile(case/'verification.json',dest/'failed-helper/verification.json')
for name in ['tests/helper_preview_port_files.json','tests/verify_helper_preview.py']:
 out=dest/'reviewed-source-before'/name;out.parent.mkdir(parents=True,exist_ok=True)
 # This failed run's exact committed guard input, regardless of subsequent fixes.
 import subprocess
 out.write_bytes(subprocess.check_output(['git','show',before['commit']+':'+name],cwd=root))
for name in ['start_canonical_bone_binding_owned.ps1','close_canonical_bone_binding_owned.ps1','capture_canonical_binding_guard_failure.py']:
 shutil.copyfile(root/'output'/name,dest/name)
dt=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
start=dt(state['started_utc']).timestamp();finish=dt(state['finished_utc']).timestamp()
receipts=[]
for path in (root/'output/private-desktop').glob('*.json'):
 if start<=path.stat().st_mtime<=finish:
  value=read(path);assert value.get('job_closed') and value.get('desktop_closed') and not value.get('foreground_child_observed') and not value.get('desktop_switch_requested')
  target=dest/'root-private-receipts'/path.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(path,target)
  receipts.append({'path':str(path),'sha256':sha(path),'exit':value.get('exit')})
summary={'format':'has_canonical_binding_guard_failure_1','status':'FAILED_FULL_DEFAULT',
 'source_commit':before['commit'],'started_utc':state['started_utc'],'finished_utc':state['finished_utc'],
 'elapsed_seconds':(dt(state['finished_utc'])-dt(state['started_utc'])).total_seconds(),
 'functional_sources':1008,'source_and_head_unchanged':True,'failed_command':'tests/verify_helper_preview.py --mode cpu --allow-checkout-eol',
 'failure':failed['error'],'checks':0,'graphics_attempted_by_failed_wrapper':False,'snapshot_created_by_failed_wrapper':False,
 'cause':'Intentional reviewed-source guard still pins the prior helper-editor bytes. Snapshot copying includes all functional sources; the dependency was present in main.',
 'next':'Independently review current optional native-joint consumer and explicit resolver dependency, update affected provenance manifests without weakening checks, rerun208CPU/266GPU, then a fresh full default.',
 'root_private_receipts_in_time_window':receipts,'receipt_scope':'Root output/private-desktop only; not presented as the total including nested test snapshots.',
 'host_closed':True,'processes_killed':False,'canonical_log_sha256':hashlib.sha256(raw).hexdigest(),
 'stale_full_verification':'output/verification.json predates this run; not admitted as its full result.',
 'native_scope':'The separate fourcase native workflow passed; it does not substitute for this failed complete run.',
 'limits':'No full PASS, native solver, artist/human/device/install completion or cleanup authorization inferred.'}
(dest/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(dest).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_metadata_source_packet_index_1','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(dest),'payloads':len(rows),'bytes':sum(v['bytes'] for v in rows),'elapsed_seconds':summary['elapsed_seconds'],'index_sha256':sha(dest/'INDEX.json')}))
