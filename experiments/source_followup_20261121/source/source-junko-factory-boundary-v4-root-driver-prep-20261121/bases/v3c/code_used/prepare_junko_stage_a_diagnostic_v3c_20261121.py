"""Manifest-closure-only successor: retain every nested predecessor SOURCE_PINS."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-stage-a-rest-diagnostic-v3b-root-driver-prep-20261121'
D=R/'output/source-junko-stage-a-rest-diagnostic-v3c-root-driver-prep-20261121'
def pin(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
old=(S/'SOURCE_PINS.json').read_bytes();assert pin(old)['sha256']=='e66a8204de7be7436f37b7f712c961669c59f0af991b30d178447d68bc06e175'
assert not D.exists();D.mkdir()
for p in S.rglob('*'):
 if p.is_file():
  target=D/p.relative_to(S);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
(D/'BASES_V3B_SOURCE_PINS.json').write_bytes(old)
shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'MANIFEST_CORRECTION.json').write_text(json.dumps({'status':'SOURCE_ONLY_UNRUN_PENDING_PEER','previous_source_pins_sha256':pin(old)['sha256'],'source_authoring_issue':'v3b file enumeration excluded nested SOURCE_PINS names; exact ownpacket closure would refuse before jobs. No runtime or native failure occurred.','change':'Include every actual nested predecessor SOURCE_PINS and exclude only the one new top-level manifest.','all_executable_source_bytes_unchanged':True,'v3b_folder_preserved':True},indent=2)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and p!=D/'SOURCE_PINS.json']
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_stage_a_body_refusal_v3c_driver_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':files},indent=2)+'\n',encoding='utf-8')
assert set(r['path'] for r in files)|{'SOURCE_PINS.json'}=={p.relative_to(D).as_posix() for p in D.rglob('*') if p.is_file()}
for row in files:assert pin((D/row['path']).read_bytes())=={'bytes':row['bytes'],'sha256':row['sha256']}
assert (D/'run_stage_a.py').read_bytes()==(S/'run_stage_a.py').read_bytes()
print(json.dumps({'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin((D/'run_stage_a.py').read_bytes()),'worker':pin((D/'gated_converter_worker.py').read_bytes()),'exact_own_source_closure_CPU_audit':'PASS'},indent=2))
