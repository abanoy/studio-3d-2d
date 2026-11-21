"""Raw-log identity-only successor; no runtime or Main operations."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[1]
S=R/'output/source-junko-stage-a-rest-diagnostic-v3-root-driver-prep-20261121'
D=R/'output/source-junko-stage-a-rest-diagnostic-v3b-root-driver-prep-20261121'
def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert pin((S/'SOURCE_PINS.json').read_bytes())['sha256']=='421e73e795d9f66687825609d4daa71c68f37fdba11b666ceb7356b35e16d708'
assert not D.exists();D.mkdir()
for path in S.rglob('*'):
 if path.is_file():
  dest=D/path.relative_to(S);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
source=(D/'run_stage_a.py').read_bytes();nl=b'\r\n' if b'\r\n' in source else b'\n'
old=b"    log=G.read(folder/'conversion.log',64*1024*1024).decode('utf-8','replace');prefix='JUNKO_PART_REST_DIAGNOSTIC '"
new=b"    log_raw=G.read(folder/'conversion.log',64*1024*1024);log=log_raw.decode('utf-8','replace');prefix='JUNKO_PART_REST_DIAGNOSTIC '"
assert source.count(old)==1 and source.count(b"sha(log.encode('utf-8'))")==1
changed=source.replace(old,new).replace(b"sha(log.encode('utf-8'))",b'sha(log_raw)');ast.parse(changed)
assert changed.replace(new,old).replace(b"'conversion_log_sha256':sha(log_raw)",b"'conversion_log_sha256':sha(log.encode('utf-8'))")==source
(D/'run_stage_a.py').write_bytes(changed)
(D/'BASES_V3_SOURCE_PINS.json').write_bytes((S/'SOURCE_PINS.json').read_bytes())
(D/'BASES_V3_DRIVER.py').write_bytes(source)
shutil.copyfile(__file__,D/'code_used'/Path(__file__).name)
(D/'SOURCE_CORRECTION.json').write_text(json.dumps({'status':'SOURCE_ONLY_UNRUN_PENDING_PEER','v3_source_manifest_sha256':'421e73e795d9f66687825609d4daa71c68f37fdba11b666ceb7356b35e16d708','change':'Hash raw conversion.log bytes directly, including any non-UTF8 bytes, while marker/error inspection uses unchanged decoded text.','worker_process_guards_and_all_25_pure_and_diagnostic_predicates_unchanged':True,'actual_prior_runtime_failure':False,'old_v3_untouched':True},indent=2)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(D).as_posix(),**pin(p.read_bytes())} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='SOURCE_PINS.json']
(D/'SOURCE_PINS.json').write_text(json.dumps({'format':'has_junko_stage_a_body_refusal_v3b_driver_pins_1','status':'SOURCE_ONLY_UNRUN_PENDING_PEER','files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files)+1,'payload_bytes':sum(r['bytes'] for r in files),'manifest':pin((D/'SOURCE_PINS.json').read_bytes()),'driver':pin(changed),'worker':pin((D/'gated_converter_worker.py').read_bytes())},indent=2))
