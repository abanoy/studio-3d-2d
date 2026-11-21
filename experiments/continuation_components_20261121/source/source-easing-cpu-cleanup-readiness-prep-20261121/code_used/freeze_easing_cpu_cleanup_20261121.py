"""Freeze only prepared source/evidence. No deletion, move, process or engine use."""
from pathlib import Path
import ast,hashlib,json,stat
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';DEST=OUT/'source-easing-cpu-cleanup-readiness-prep-20261121'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def put(name,b):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b,name
 else:p.write_bytes(b)
def js(name,v):put(name,(json.dumps(v,indent=2)+'\n').encode())
assert not (DEST/'SOURCE_PINS.json').exists()
summary=json.loads(read(DEST/'AUDIT_SUMMARY.json'))
assert summary['stage_count']==7 and summary['total_files']==5640 and summary['total_logical_bytes']==47366153
assert not summary['deferred_privacy_files'] and summary['unbacked_noncache_binary_files']==5
recovery=json.loads(read(DEST/'SOURCE_RECOVERY_CHECKS.json'));assert len(recovery['files'])==5510 and not recovery['unrecoverable_source_rows']
counts={}
for row in recovery['files']:
 assert row['recovery'] is not None;counts[row['stage']]=counts.get(row['stage'],0)+1
# Remove a redundant5510-row projection: every complete row, its recovery pointer
# and native identity remain in the exact stage-inventories. This metadata was
# generated here and not frozen previously; no original stage/report is altered.
compact={'format':'has_easing_cpu_source_hash_recovery_summary_2','source_rows_checked':5510,
 'unrecoverable_source_rows':0,'source_rows_by_stage':counts,
 'detailed_records':'stage-inventories/<stage>.json files[] contains all exact paths/hashes/recovery refs and identities',
 'prior_checkpoint':'c31576d0c1d84030d51ec886f2f3976a60a70c7b','all_source_rows_recoverable_by_hash':True}
(DEST/'SOURCE_RECOVERY_CHECKS.json').write_text(json.dumps(compact,indent=2)+'\n',encoding='utf-8')
for p in (DEST/'stage-inventories').glob('*.json'):
 value=json.loads(read(p));p.write_text(json.dumps(value,separators=(',',':'))+'\n',encoding='utf-8')
icon=ROOT/'web/studio.svg';b=read(icon)
assert len(b)==720 and sha(b)=='fd9ec2eff6157f02d93e51f1f9e9e2040fe407aa13f5922ac7e2967c76b1d450'
js('ICON_RECOVERY_REFERENCE.json',{'format':'has_repository_icon_readonly_recovery_reference_1','repository_path':'web/studio.svg',
 'bytes':len(b),'sha256':sha(b),'five_stage_copies_match_existing_repo_bytes':True,
 'icon_copied_into_packet':False,'independent_Git_commit_binding_performed_by_author':False,
 'Root_Git_byte_confirmation_required_before_cleanup':True})
origins=json.loads(read(DEST/'PRESERVED_ORIGINS.json'));assert len(origins['files'])==90
for row in origins['files']:
 b=read(DEST/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
 assert b==read(Path(row['origin']))
put('evidence/prior-c315-remote-verification.json',read(OUT/'IMPORT_OFF_REMOTE_VERIFIED_20261121.json'))
for name in ('prepare_easing_cpu_cleanup_20261121.py','inspect_easing_cpu_host_dependencies_20261121.py','freeze_easing_cpu_cleanup_20261121.py'):
 put('code_used/'+name,read(OUT/name));ast.parse(read(OUT/name),filename=name)
deps=json.loads(read(DEST/'FUTURE_HOST_DEPENDENCIES.json'));assert len(deps['scanned_runtime_sources'])==33 and not deps['runtime_exact_stage_dependencies']
js('FREEZE_PROOF.json',{'format':'has_easing_cpu_cleanup_source_freeze_1','status':'PREPARATION_ONLY_NO_CLEANUP_AUTHORIZATION',
 'owned_stages':7,'actual_file_count':5640,'actual_logical_bytes':47366153,'all_inspected_files_regular_single_link':True,
 'aliases_observed':0,'source_hash_recovery_rows':5510,'unrecoverable_source_rows':0,
 'missing_text_artifacts_preserved':90,'missing_text_artifact_bytes':1460358,
 'private_array_or_text_screen_refusals':0,'unmatched_repo_icon_copies':5,
 'source_entries_checked_for_exact_stage_dependencies':33,'exact_runtime_stage_dependencies_found':0,
 'historical_process_reaped_flags_are_not_fresh_host_process_proof':True,
 'new_remote_byte_verification_required':True,'fresh_Root_process_check_required':True,
 'Root_Git_icon_binding_required':True,'delete_move_CIM_or_graphics_performed':False,
 'owner_inputs_native_models_cache_binaries_or_art_copied':False,'original_failures_and_parse_only_scope_preserved':True})
rows=[]
for p in sorted(DEST.rglob('*')):
 if not p.is_file():continue
 b=read(p);text=b.decode('utf-8-sig');assert '\0' not in text
 assert p.suffix.lower() in ('.py','.json','.gd','.md','.log','.cfg','.godot','.tscn','.gdshader')
 rows.append({'path':p.relative_to(DEST).as_posix(),'bytes':len(b),'sha256':sha(b)})
manifest={'format':'has_easing_cpu_cleanup_readiness_source_pins_1','status':'FROZEN_PREPARATION_NOT_DELETION_AUTHORIZATION',
 'files':rows,'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),
 'owned_stages':7,'logical_bytes_proposed':47366153,'root_process_and_remote_proof_still_required':True,
 'private_or_binary_payloads_copied':False,'cleanup_performed':False}
raw=(json.dumps(manifest,indent=2)+'\n').encode();put('SOURCE_PINS.json',raw)
assert {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}=={r['path'] for r in rows}|{'SOURCE_PINS.json'}
for row in rows:
 b=read(DEST/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
print(json.dumps({'folder':str(DEST),'total_files':len(rows)+1,'total_bytes':sum(r['bytes'] for r in rows)+len(raw),
 'manifest_bytes':len(raw),'manifest_sha256':sha(raw),'stages':7,'stage_files':5640,'stage_logical_bytes':47366153,
 'new_text_artifacts':90,'new_text_artifact_bytes':1460358,'cleanup_performed':False}))
