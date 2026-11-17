"""Root-owned final-location review validation; use the unchanged private launcher."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
PACKET=ROOT/'experiments/native_five_review_after_full_20261116'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
assert sha(PACKET/'INDEX.json')=='cf7555d6186ba96c845eb919471d068805b057e19b171280283843bb2c2ea974'
assert sha(PACKET/'replay/validate_after_full.py')=='f6e87e8eb239bc08843ef1b3f369b449509bae98128db770b3835639185f8514'
helper=ROOT/'experiments/normal_boundary_probe_actual_20261116/run_owned.py'
spec=importlib.util.spec_from_file_location('root_private_execution_observer',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
folder=ROOT/'output/native-hair-review-root-execution-20261116-attempt1';folder.mkdir()
module.save(folder/'source-context.json',{'observer_sha256':sha(helper),'review_packet_index_sha256':sha(PACKET/'INDEX.json'),'driver_sha256':sha(Path(__file__))})
module.closure(folder,'before')
command=load(PACKET/'replay/command.json')['command']
process,_=module.invoke(folder,'review',command,2000)
path=ROOT/'output/native-hair-final-validation-52f63c9-20261116-attempt1/verification.json'
v=load(path) if path.exists() else {}
after=module.closure(folder,'after')
checks=sum(x.get('observed_checks',0) for x in v.get('results',[]))
record={'format':'has_root_final_native_five_review_execution_1','passed':process['exit']==0 and not process['timed_out'] and v.get('passed') is True and checks==187 and after['owned_count']==0,
    'process':process,'checks_observed':checks,'examples':len(v.get('results',[])),'preservation':v.get('preservation'),
    'verification_sha256':sha(path) if path.exists() else None,'runtime_lease_released':True,
    'review':v.get('review'),'human_observation':'OWNER_DEFERRED_NO_RESULT'}
module.save(folder/'verification.json',record);print(json.dumps(record));raise SystemExit(0 if record['passed'] else 1)
