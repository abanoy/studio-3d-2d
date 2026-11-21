"""Freeze source-only successor after independent source peer; no execution."""
from pathlib import Path
import ast,hashlib,json,stat
OUT=Path(__file__).resolve().parent;NEW=OUT/'source-miku-contact-c315-1103-successor-prep-20261121'
OLD=OUT/'source-miku-contact-1102-successor-prep-20261121'
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b,str(p)
 else:p.write_bytes(b)
assert not (NEW/'SOURCE_PINS.json').exists(),'Frozen packet must never be rewritten'
# This is a predecessor-reference manifest, not a claim that this small base
# folder contains its full historical closure. Original bytes remain untouched.
p=NEW/'bases/435/SOURCE_PINS.json';q=p.with_name('PREDECESSOR_SOURCE_PINS.json')
assert p.resolve().parent==q.resolve().parent==(NEW/'bases/435').resolve()
assert read(p)==read(OLD/'SOURCE_PINS.json') and not q.exists();p.rename(q)
for name in ('prepare_miku_c315_successor_20261121.py','finish_miku_c315_successor_20261121.py',
 'extend_miku_c315_contracts_20261121.py','freeze_miku_c315_successor_20261121.py'):
 write(NEW/'code_used'/name,read(OUT/name))
review='''# Source review and execution boundary

Independent face_gizmo source/API GO received after reading shared source1103.py
17,881 bytes / e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3
and all60 authored synthetic controls, against actual run_full,
receipt_provenance and the c315 isolated outer launch schema. No concrete blocker
was found. Source admission certifies explicit retained Root evidence, not the
existence of a successful Full at authoring time. No candidate import, policy
control, native/ArrayMesh/GPU execution or reserved checkout edit was performed
by author or peer. Python AST parsing is source inspection only.

All13 old GDScript payloads, both ownership helpers, four private data hashes and
the exact private-manifest size/hash remain unchanged. The60 policy controls are
separate authored/unrun checks; the native268/13-job expectation is unchanged.
Historical435 native hosts and its failed Full remain preserved. This is an
explicit c315/1103 source successor, not a relaxed old-host revision check.

bases/435/PREDECESSOR_SOURCE_PINS.json preserves the exact old manifest as a
reference; the complete old closure is preserved at its original packet path.
AUTHORING_INPUTS.json describes the earlier authoring phase, before the shared
guard extension; the completed source is source1103.py and pinned by the final
INPUT_PINS and SOURCE_PINS manifests. No runtime facts are inferred from it.
'''
write(NEW/'SOURCE_REVIEW.md',review.encode())
oldinputs=json.loads(read(OLD/'INPUT_PINS.json'));inputs=json.loads(read(NEW/'INPUT_PINS.json'))
assert inputs['targets']==oldinputs['targets'] and len(inputs['targets'])==13
for row in inputs['files']:
 b=read(NEW/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
for row in inputs['targets']:assert read(NEW/'payload'/row['path'])==read(OLD/'payload'/row['path'])
for name in ('qualified_helpers.py','qualified_ui_host.py'):assert read(NEW/name)==read(OLD/name)
old=read(OLD/'run_miku_contact_qualification.py').decode();new=read(NEW/'run_miku_contact_qualification.py').decode()
for token in ('PRIVATE_MANIFEST_PIN =','PROJECT_SHA =','ASSET_SHA =','COLLIDER_SHA =','ALIGNMENT_SHA ='):
 assert next(x for x in old.splitlines() if x.startswith(token))==next(x for x in new.splitlines() if x.startswith(token))
assert old[old.index('def private_inputs('):old.index('def main():')]==new[new.index('def private_inputs('):new.index('def main():')]
count=0
for p in NEW.rglob('*.py'):ast.parse(read(p),filename=str(p));count+=1
proof={'format':'has_miku_c315_source_structural_proof_1','status':'SOURCE_ONLY_UNRUN',
 'revision':'c31576d0c1d84030d51ec886f2f3976a60a70c7b','functional_baseline':1103,
 'all13_payloads_byte_identical_to_frozen435_successor':True,'both_ownership_helpers_byte_identical':True,
 'private_manifest_and_project_asset_collider_alignment_pins_unchanged':True,
 'private_inputs_and_public_projection_functions_byte_identical':True,
 'python_sources_AST_parsed':count,'candidate_code_imported_or_executed':False,
 'actual_successful_Full182_required':True,'exact_new626_and21_movie_identities_required':True,
 'isolated_outer_completion_and_actual_current_receipts_required':True,
 'policy_controls_authored':60,'policy_controls_executed':0,'expected_native_workflow_checks':268,
 'expected_native_workflow_jobs':13,'native_or_ArrayMesh_checks_executed':0,
 'private_arrays_or_native_art_copied':False,'Main_or_Full_checkout_modified':False,
 'source_peer':'face_gizmo: SOURCE/API GO only'}
write(NEW/'STRUCTURAL_PROOF.json',(json.dumps(proof,indent=2)+'\n').encode())
rows=[]
for p in sorted(NEW.rglob('*')):
 if not p.is_file():continue
 b=read(p);b.decode('utf-8-sig')
 assert p.suffix.lower() in ('.py','.gd','.json','.md')
 rows.append({'path':p.relative_to(NEW).as_posix(),'bytes':len(b),'sha256':sha(b)})
manifest={'format':'has_miku_c315_successor_source_pins_1','status':'SOURCE_API_GO_UNRUN_FULL_GATED',
 'revision':proof['revision'],'functional_source_count':1103,'files':rows,'payload_files':len(rows),
 'payload_bytes':sum(r['bytes'] for r in rows),'source_peer':'face_gizmo','policy_checks_executed':0,
 'native_or_ArrayMesh_checks_executed':0,'actual_successful_Full_required':True,'application_adopted':False,
 'private_arrays_published':False,'Main_or_Full_checkout_modified':False}
raw=(json.dumps(manifest,indent=2)+'\n').encode();write(NEW/'SOURCE_PINS.json',raw)
for row in rows:
 b=read(NEW/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert {p.relative_to(NEW).as_posix() for p in NEW.rglob('*') if p.is_file()}=={r['path'] for r in rows}|{'SOURCE_PINS.json'}
print(json.dumps({'folder':str(NEW),'total_files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),
 'total_bytes':sum(r['bytes'] for r in rows)+len(raw),'manifest_bytes':len(raw),'manifest_sha256':sha(raw),
 'helper_bytes':len(read(NEW/'source1103.py')),'helper_sha256':sha(read(NEW/'source1103.py')),
 'driver_bytes':len(read(NEW/'run_miku_contact_qualification.py')),'driver_sha256':sha(read(NEW/'run_miku_contact_qualification.py'))}))
