"""Apply only the independently reviewed strict2 file to fresh isolated stage3."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/native_five_performance_followup_20261115'
FOLDER=ROOT/'output/native-five-stage-attempt3'
TARGET=FOLDER/'Studio/src/source_secondary.gd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(PACKET/'INDEX.json')=='cae9f2b9cb550446897ebdec0a567e5b2ffb505184effac307b17d3042d1abd5'
index=json.loads((PACKET/'INDEX.json').read_bytes())
for name,row in index['files'].items():
    p=PACKET/name;assert p.resolve().is_relative_to(PACKET.resolve()) and not p.is_symlink()
    assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
source=PACKET/'source_secondary_strict2.gd'
assert sha(source)=='3b2c29dc11b60e68306f858a32d03271e30a039b8451916df2ff9324e7da4f84'
assert sha(TARGET)=='dcf861f26ff7829ec25e2616e56416dd68fa4bb6a32d5340c969b9c946d84e47'
assert TARGET.resolve().is_relative_to(FOLDER.resolve()) and not TARGET.is_symlink()
before=sha(TARGET);TARGET.write_bytes(source.read_bytes())
record={'format':'has_isolated_five_strict2_overlay_1','target':str(TARGET),'before':before,'after':sha(TARGET),
    'packet_index_sha256':sha(PACKET/'INDEX.json'),'base_stage_manifest_sha256':sha(FOLDER/'STAGE-MANIFEST.json'),
    'main_original_root_modified':False,'runtime_qualification_claimed':False}
with (FOLDER/'STRICT2-OVERLAY.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
