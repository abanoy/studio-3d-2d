"""Add the reviewed strict performance overlay to fresh isolated stage2 only."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/native_five_performance_candidate_20261115'
FOLDER=ROOT/'output/native-five-stage-attempt2'
TARGET=FOLDER/'Studio/src/source_secondary.gd'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(PACKET/'INDEX.json')=='80203837bd647fbad157d9ea7b1ee8e0c82014bbaa1329b0c5f2fac7e95bb441'
assert sha(PACKET/'source_secondary_strict.gd')=='064c211efbb19b829defb959b6f9d0c6aeef36aa6c2af76065fda9f2b17b21be'
assert sha(TARGET)=='dcf861f26ff7829ec25e2616e56416dd68fa4bb6a32d5340c969b9c946d84e47'
assert TARGET.resolve().is_relative_to(FOLDER.resolve()) and not TARGET.is_symlink()
before=sha(TARGET)
TARGET.write_bytes((PACKET/'source_secondary_strict.gd').read_bytes())
record={'format':'has_isolated_five_strict_overlay_1','target':str(TARGET),'before':before,'after':sha(TARGET),
        'packet_index_sha256':sha(PACKET/'INDEX.json'),'base_stage_manifest_sha256':sha(FOLDER/'STAGE-MANIFEST.json'),
        'scalar_core_sha256':sha(FOLDER/'Studio/src/source_chain_math.gd'),
        'main_original_root_modified':False,'runtime_or_qualification_claimed':False}
with (FOLDER/'STRICT-OVERLAY.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps(record))
