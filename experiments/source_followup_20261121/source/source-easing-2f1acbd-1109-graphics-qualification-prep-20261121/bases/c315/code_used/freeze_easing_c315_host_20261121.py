"""Freeze source-only host and review inputs, without importing/executing them."""
from pathlib import Path
import ast,hashlib,json,stat
OUT=Path(__file__).resolve().parent;DEST=OUT/'source-easing-c315-graphics-qualification-prep-20261121'
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not getattr(s,'st_file_attributes',0)&0x400
 b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns)
 return b
def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,b):
 p=DEST/name;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert read(p)==b
 else:p.write_bytes(b)
assert not (DEST/'SOURCE_PINS.json').exists()
for name in ('prepare_easing_c315_host_20261121.py','freeze_easing_c315_host_20261121.py'):put('code_used/'+name,read(OUT/name))
parse=OUT.parent.parent/'has-easing-c315-graphics-parse-1795260866931895900/RESULT.json'
put('evidence/c315-parse-only-zero-assertions.json',read(parse))
put('evidence/source-candidate-child-peer.json',read(OUT/'EASING_C315_GRAPHICS_SOURCE_CHILD_PEER_20261121.json'))
inputs=json.loads(read(DEST/'INPUT_PINS.json'))
for row in inputs['files']:
 b=read(DEST/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
candidate=json.loads(read(DEST/'candidate/SOURCE_PINS.json'))
assert len(candidate['files'])==18
for row in candidate['files']:
 b=read(DEST/'candidate'/row['path']);assert len(b)==row['bytes'] and sha(b)==row['sha256']
assert {p.relative_to(DEST/'candidate').as_posix() for p in (DEST/'candidate').rglob('*') if p.is_file()}=={r['path'] for r in candidate['files']}|{'SOURCE_PINS.json'}
fixture=read(DEST/'candidate/payload/tests/easing_c315_graphical_smoke.gd').decode()
# No GDScript execution: independently count the explicit assertion call sites.
import re
labels=re.findall(r'check\([^\r\n]*,"([^"\r\n]+)"\)',fixture)
assert len(labels)==37
reading=fixture[fixture.index('\tif reading:'):fixture.index('\tcheck(app.load_demo_room()')]
assert len(re.findall(r'\bcheck\(',reading))==8
movie_checks=[]
for branch in re.findall(r'(?ms)^\tif movies:\r?\n(.*?)(?=^\t[^\t\r\n])',fixture):movie_checks+=re.findall(r'\bcheck\(',branch)
assert len(movie_checks)==6
assert (len(labels)-8-6)*7+(len(labels)-8)==190 and 8*8==64
count=0
for p in DEST.rglob('*.py'):ast.parse(read(p),filename=str(p));count+=1
proof={'format':'has_easing_c315_graphics_source_structural_proof_1','status':'FROZEN_SOURCE_ONLY_PENDING_HOST_PEER',
 'revision':inputs['revision'],'candidate_manifest_sha256':inputs['candidate_manifest_sha256'],
 'candidate_payload_files_verified':18,'candidate_total_files':19,'targets':7,'modified_production_bases':2,'new_source_targets':5,
 'AST_parsed_python_sources':count,'candidate_imports_or_executions':0,'private_jobs_executed':0,
 'writer_assertions_without_movies':23,'writer_assertions_with_movies':29,'writer_variants':8,'writer_checks':190,
 'reader_assertions':8,'fresh_reader_variants':8,'reader_checks':64,'expected_graphical_checks':254,
 'expected_private_jobs':16,'expected_additional_hidden_ffprobe_children':2,'pure_gate_file_tests_authored':3,'pure_gate_file_tests_executed':0,
 'successful_exact_Full182_1103_626_21movies_and_outer_receipts_required':True,
 'writer_source_data_cache_and_profile_offline_for_reader':True,'only_five_exact_reader_inputs_copied':True,
 'all_source_and_generated_reader_inputs_identity_hash_preservation_required':True,
 'Main_or_Full_checkout_modified':False,'host_source_peer':'REQUESTED_AFTER_FREEZE; no unreceived GO claimed',
 'application_adopted':False}
put('STRUCTURAL_PROOF.json',(json.dumps(proof,indent=2)+'\n').encode())
review='''# Source and execution scope

Frozen for independent host source/API peer, not yet received at this freeze.
The candidate itself has source/API GO and an actual Root c315 headless parse-only
result with zero graphical assertions. These are preserved as distinct evidence.
All254 proposed graphical assertions, the two ffprobe metadata checks and three
pure gate-file tests are authored and UNRUN. No candidate or host module was
imported during authoring; Python AST parsing and literal/hash/count readback
are the only checks performed by the author. No Main/Full edits or native jobs.

Shared source1103.py is exact17,881/e32e8b70696fb355eb624424cab0222a51f80041ac14563df9328557b7e387c3,
independently source/API reviewed for the Miku successor. It is reused unchanged
with its exact baseline/group contract. It does not assert a successful Full exists.
'''
put('SOURCE_REVIEW.md',review.encode())
rows=[]
for p in sorted(DEST.rglob('*')):
 if not p.is_file():continue
 b=read(p);b.decode('utf-8-sig');assert p.suffix.lower() in ('.py','.json','.gd','.md')
 rows.append({'path':p.relative_to(DEST).as_posix(),'bytes':len(b),'sha256':sha(b)})
manifest={'format':'has_easing_c315_graphics_qualification_source_pins_1','revision':inputs['revision'],
 'status':'SOURCE_ONLY_UNRUN_FULL_GATED_PENDING_HOST_PEER','files':rows,
 'payload_files':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),
 'actual_graphical_or_gate_test_executions':0,'application_adopted':False,'Main_or_Full_modified':False}
raw=(json.dumps(manifest,indent=2)+'\n').encode();put('SOURCE_PINS.json',raw)
assert {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}=={r['path'] for r in rows}|{'SOURCE_PINS.json'}
for row in rows:
 b=read(DEST/row['path']);assert (len(b),sha(b))==(row['bytes'],row['sha256'])
driver=read(DEST/'run_easing_graphics.py')
print(json.dumps({'folder':str(DEST),'total_files':len(rows)+1,'total_bytes':sum(r['bytes'] for r in rows)+len(raw),
 'manifest_bytes':len(raw),'manifest_sha256':sha(raw),'driver_bytes':len(driver),'driver_sha256':sha(driver),
 'expected_graphical_checks':254,'expected_private_jobs':16,'gate_file_tests_executed':0}))
