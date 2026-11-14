from pathlib import Path
import hashlib,gzip,json,shutil,datetime
root=Path(__file__).resolve().parents[1]
run=root/'output/windows-canonical-inert-20261114T014831592'
dest=root/'output/canonical-inert-failure-20261114'
assert not dest.exists();dest.mkdir()
state=json.loads((run/'state.json').read_bytes())
assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] is True
before=json.loads((run/'source-before.json').read_bytes());after=json.loads((run/'source-after.json').read_bytes())
assert before==after and len(before['source_sha256'])==996
host=json.loads((run/'authoritative-host-termination.json').read_bytes())
assert host['coordinator_absent'] and host['python_absent'] and host['owned_runtime_command_matches_absent'] and host['no_process_killed']
for name in ['state.json','launch.json','source-before.json','source-after.json','coordinator-children-observed.json','authoritative-host-terminal.json','authoritative-host-termination.json','coordinator.stdout.log','coordinator.stderr.log']:
 shutil.copy2(run/name,dest/name)
raw=(run/'canonical.log').read_bytes();(dest/'canonical.log.gz').write_bytes(gzip.compress(raw,mtime=0))
assert gzip.decompress((dest/'canonical.log.gz').read_bytes())==raw
case=root/'output/contact-selection/1794622745880357700'
failed=json.loads((case/'result.json').read_bytes())
assert failed['checks']==67 and failed['failures']==0 and len(failed['native_reports'])==5
(dest/'selection').mkdir()
for name in ['engine.log','result.json']:shutil.copy2(case/name,dest/'selection'/name)
receipts=[]
start=datetime.datetime.fromisoformat(state['started_utc'].replace('Z','+00:00')).timestamp()
finish=datetime.datetime.fromisoformat(state['finished_utc'].replace('Z','+00:00')).timestamp()
for p in (root/'output/private-desktop').glob('contact_selection_smoke_*.json'):
 if start<=p.stat().st_mtime<=finish:
  r=json.loads(p.read_bytes());assert r['exit']==0 and r['job_closed'] and r['desktop_closed'] and r['child_desktop_confirmed'] and not r['foreground_child_observed']
  shutil.copy2(p,dest/'selection'/p.name);receipts.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert len(receipts)==1
summary={'format':'has_canonical_inert_failed_audio_device_1','status':'FAILED_FULL_DEFAULT','source_commit':before['commit'],
 'source_and_head_unchanged':True,'functional_sources':996,'started_utc':state['started_utc'],'finished_utc':state['finished_utc'],
 'failed_command':'tests/verify_contact_selection.py','domain_checks':67,'domain_failures':0,'native_models':5,'engine_exit':0,
 'failure':'Strict engine-log gate rejected WASAPI GetBufferSize error and current output_device invalidation.',
 'cause':'Not yet established; no device-change or new-code cause inferred.',
 'private_receipts':receipts,'exact_host_identities_absent':True,'no_process_killed':True,
 'canonical_log_sha256':hashlib.sha256(raw).hexdigest(),
 'stale_full_verification':'output/verification.json predates this failed run; not admitted as its result.',
 'next':'Repeat affected test on unchanged source with original WASAPI; inspect audio scope before changing driver.',
 'closure_script_note':'First helper guard refused because PowerShell7.6 auto-parsed JSON timestamps as DateTime. No proof written then. Explicit -DateKind String preserved exact strings before successful host observation.'}
(dest/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
for name in ['start_canonical_inert_owned.ps1','close_canonical_inert_owned.ps1','capture_canonical_inert_failure.py']:
 shutil.copy2(root/'output'/name,dest/name)
rows=[{'path':p.relative_to(dest).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.rglob('*')) if p.is_file()]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_metadata_source_packet_index_1','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'failed_packet':str(dest),'files':len(rows),'index_sha256':hashlib.sha256((dest/'INDEX.json').read_bytes()).hexdigest(),'source_unchanged':True,'selection_private_job_exit':0}))
