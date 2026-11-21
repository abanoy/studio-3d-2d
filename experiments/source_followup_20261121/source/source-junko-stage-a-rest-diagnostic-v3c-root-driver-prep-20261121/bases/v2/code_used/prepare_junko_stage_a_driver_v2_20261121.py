"""Preserve frozen v1; normalize only exact Windows unittest newline transport."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-stage-a-root-driver-prep-20261121'
D=R/'output/source-junko-stage-a-root-driver-v2-prep-20261121'
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert pin((S/'SOURCE_PINS.json').read_bytes())['sha256']=='68c854dcfb59ce996d0b2f7741229e6c81d36d68fef14cbb00e6e46b7ca6306d'
assert not D.exists();D.mkdir()
for path in S.rglob('*'):
 if path.is_file():
  rel=path.relative_to(S);dest=D/'bases/v1'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
  if rel.as_posix()!='SOURCE_PINS.json':
   dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
source=(D/'run_stage_a.py').read_bytes()
old=b"decode('utf-8','replace')\n        need(re.search(r'Ran 16"
newline=b'\n'
if old not in source:old=old.replace(b'\n',b'\r\n');newline=b'\r\n'
new=b"decode('utf-8','replace').replace('\\r\\n','\\n')"+newline+b"        need(re.search(r'Ran 16"
assert source.count(old)==1
changed=source.replace(old,new);assert changed.replace(new,old)==source
(D/'run_stage_a.py').write_bytes(changed);ast.parse(changed)
shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'SOURCE_CORRECTION.json').write_text(json.dumps({'status':'SOURCE_ONLY_UNRUN_PENDING_PEER','previous':'68c854dcfb59ce996d0b2f7741229e6c81d36d68fef14cbb00e6e46b7ca6306d','reason':'Python unittest raw Windows stderr may use CRLF. Normalize CRLF toLF before exact16 case lines/OK/noerror checks; no assertions,commands,gates orconversion logic changed.','original_v1_unchanged':True,'actual_runtime_failure_observed':False,'worker_and_all_other_executable_sources_byte_exact':True},indent=2)+'\n',encoding='utf-8')
rows=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file()]
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_stage_a_root_source_pins_2','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows)+1,'payload_bytes':sum(r['bytes'] for r in rows),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin(changed),'worker':pin((D/'gated_converter_worker.py').read_bytes())},indent=2))
