"""Freeze source-only replay host; never import or execute candidate/runtime."""
from pathlib import Path
import ast,hashlib,json,re,stat
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent;DEST=OUT/'source-owner-review-c315-replay-prep-20261121'
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b,name
 else:p.write_bytes(b)
assert not (DEST/'SOURCE_PINS.json').exists()
for name in ('prepare_owner_replay_c315_host_20261121.py','finish_owner_replay_c315_inputs_20261121.py','freeze_owner_replay_c315_host_20261121.py'):
 put('code_used/'+name,read(OUT/name))
inputs=json.loads(read(DEST/'HOST_INPUT_PINS.json'));assert len(inputs['files'])==9 and inputs['expected_total_checks']==69
for row in inputs['files']:
 b=read(DEST/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
ref=read(DEST/'reference/verify_owner_review.py').decode();body=ref[ref.index('def compare('):ref.index('\ndef load_runner(')]
assert body in read(DEST/'review_state_compare.py').decode()
assert read(DEST/'reference/owner_review_replay.gd')==read(ROOT/'tests/owner_review_replay.gd')
fixture=read(DEST/'reference/owner_review_replay.gd').decode()
assert len(re.findall(r'(?m)^\s*check\(',fixture))==22
assert len(re.findall(r'(?m)^\s{3}check\(',fixture))==1 # one per cel; object loop has two tabs
parsed=0
for p in DEST.rglob('*.py'):ast.parse(read(p),filename=str(p));parsed+=1
proof={'format':'has_owner_review_c315_replay_source_proof_1','status':'SOURCE_ONLY_UNRUN_FULL_FAILED_HOLD',
 'revision':inputs['revision'],'actual_review_runtime_source_files':1106,'review_original_total_files':1116,
 'exact_preparation_sha256':inputs['preparation_pin']['sha256'],'private_seal_sha256':inputs['private_seal_pin']['sha256'],
 'private_seal_copied_or_project_metadata_saved_in_source_packet':False,'expected_cases':3,'expected_node_checks':69,
 'expected_private_images':12,'expected_native_processes':3,'three_package_scope_only':True,
 'shared_Full182_1103_626_21movies_outer_current_receipt_gate_unchanged':True,
 'actual_c315_Full_status_at_freeze':'Root reported FAIL2801.1818s/contact_transform; no successful Full admitted',
 'actual_review_res_root_not_mock_copy_required':True,'external_scene_uses_exact_committed_Node':True,
 'review_override_and_owner_interactive_profile_not_overlaid':True,'launcher_only_workspace_receipts_outside_review':True,
 'all_declared_packed_and_cold_unpacked_payload_sha_crc_required':True,'legacy_saved_state_comparator_copied_byte_exact':True,
 'native_Setup_Focus_pixels_and_before_after_state_camera_exact':True,'zero_readbacks_and_source_stamp_preservation_required':True,
 'public_projection_explicit_counts_hashes_flags_only':True,'AST_parsed_python_sources':parsed,
 'candidate_imports_native_or_graphics_executions':0,'Main_Full_or_review_files_modified':False,
 'host_peer':'REQUESTED_AFTER_FREEZE; no unreceived source GO claimed','human_acceptance_or_six_package_aggregate_claimed':False}
put('STRUCTURAL_PROOF.json',(json.dumps(proof,indent=2)+'\n').encode())
rows=[]
for p in sorted(DEST.rglob('*')):
 if not p.is_file():continue
 b=read(p);text=b.decode('utf-8-sig');assert '\0' not in text
 assert p.suffix.lower() in ('.py','.gd','.json','.md')
 assert not p.name.startswith('PRIVATE_')
 rows.append({'path':p.relative_to(DEST).as_posix(),'bytes':len(b),'sha256':sha(b)})
manifest={'format':'has_owner_review_c315_replay_source_pins_1','revision':inputs['revision'],
 'status':'SOURCE_ONLY_UNRUN_SUCCESSFUL_FULL_REQUIRED_ACTUAL_C315_FAILED','files':rows,'payload_files':len(rows),
 'payload_bytes':sum(r['bytes'] for r in rows),'private_seal_or_project_metadata_images_copied':False,
 'native_or_graphics_executed':False,'Main_Full_review_or_installed_Studio_modified':False,'host_peer_pending':True}
raw=(json.dumps(manifest,indent=2)+'\n').encode();put('SOURCE_PINS.json',raw)
assert {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}=={r['path'] for r in rows}|{'SOURCE_PINS.json'}
for row in rows:
 b=read(DEST/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
host=read(DEST/'run_review_replay.py')
print(json.dumps({'folder':str(DEST),'total_files':len(rows)+1,'total_bytes':sum(r['bytes'] for r in rows)+len(raw),
 'manifest_bytes':len(raw),'manifest_sha256':sha(raw),'host_bytes':len(host),'host_sha256':sha(host),
 'expected_cases':3,'expected_checks':69,'native_or_graphics_executed':False}))
