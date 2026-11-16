"""Record the actual bounded qualification and subsequent runtime-equivalent promotion."""
from pathlib import Path
import datetime,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((ROOT/n).read_bytes())
def pin(n):return {'path':n,'sha256':sha(ROOT/n)}
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
stage='output/native-five-stage-attempt3'
gui=stage+'/Studio/output/native-five-gui-attempt1'
state=stage+'/Studio/output/source-native-five-state-20261116T040011702334'
assert load(state+'/verification.json')['passed'] and load(gui+'/verification.json')['passed']
assert load(stage+'/TRANSVERSE-ROOT-EXECUTION/verification.json')['runtime_lease_released']
assert load('output/native-five-promotion-applied/verification.json')['passed']
domain='output/helper-preview-driver-domain/source-five-promotion-20261116/result.json'
d=load(domain);assert len(d['checks'])==120 and not d['failures'] and d['source_preservation']
spec=importlib.util.spec_from_file_location('qualified_five_helper_port',ROOT/'tests/verify_helper_preview.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
spec=importlib.util.spec_from_file_location('qualified_five_wind_port',ROOT/'tests/verify_wind_review.py');wind=importlib.util.module_from_spec(spec);spec.loader.exec_module(wind)
wind.ALLOW_EOL=True
ports={'helper':helper.validate_port(ROOT,allow_eol=True),'wind':wind.runtime_hashes()}
save(ROOT/'output/native-five-promotion-applied/current-port-validation.json',{'passed':True,'explicit_checkout_EOL_normalization':True,'ports':ports})
w=load(gui+'/writer/result.json');times={n:v['native_step_processing'] for n,v in w['metrics'].items() if isinstance(v,dict) and 'native_step_processing' in v}
benchmark={'format':'has_native_five_qualified_main_increment_1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'QUALIFIED_BOUNDED_RUNTIME_PROMOTED_FRESH_FULL_REQUIRED','native_rule_indices_selected':[8,17,18,26,27],'solved_rules':5,'retained_rules':49,'supported_strands':3,
    'state':{'checks':266,'failures':0,'verification':pin(state+'/verification.json')},
    'GUI':{'checks':102,'failures':0,'phases':{'writer':83,'reader-packed':11,'reader-linked':8},'verification':pin(gui+'/verification.json'),'authoritative_root_closure':pin(stage+'/TRANSVERSE-ROOT-EXECUTION/verification.json')},
    'actual_success_packet':pin('experiments/native_five_qualified_actual_20261116/INDEX.json'),
    'original_source_and_native_input_preservation':pin(stage+'/ROOT-PRESERVATION-qualified-102.json'),
    'promotion':pin('output/native-five-promotion-applied/verification.json'),
    'promotion_source_review':pin('experiments/source_native_five_promotion_review_20261116/INDEX.json'),
    'CPU_driver_controls':{'checks':120,'failures':0,'result':pin(domain)},'current_reviewed_ports':pin('output/native-five-promotion-applied/current-port-validation.json'),
    'native_step_microseconds_by_profile':times,'timing_scope':'Successful Native.step only; controlled fixture differs from earlier timing runs. No120Hz/FPS qualification.',
    'earlier_failures_preserved':'Initial82/1 and diagnostic57/2 remain failed in native_five_initial_actual_20261116; direction predicates and all numerical tolerances unchanged.',
    'main_promotion_runtime_delta':'Two source headers only differ from qualified runtime; wrapper and four test files are exact. Two user-facing physics strings and only their two manifest hash rows are updated.',
    'scope':'Exact qualified Junko GLB only; three supported strands. Other44 native rules remain inactive, same-actor ragdoll/SDK/client/artist fidelity remain unqualified.',
    'fresh_main_full_default_passed':False,'manual_hair_check':'OWNER_DEFERRED_NO_RESULT','formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED'}
target=ROOT/'docs/benchmarks/native_five_qualified_2026-11-15.json';save(target,benchmark)
ledger_path=ROOT/'docs/completion_checklist.json';ledger=json.loads(ledger_path.read_bytes())
stable=[(r['id'],json.dumps(r['implementation'],sort_keys=True),r['acceptance_status'],json.dumps(r['external_dependencies'],sort_keys=True)) for r in ledger['requirements']]
for row in ledger['requirements']:
    if row['id'] in ('IMPORT-02','IMPORT-03'):
        row['evidence'].append({'kind':'test_result','path':'docs/benchmarks/native_five_qualified_2026-11-15.json','scope':'Actual isolated266state+102GUI/cold/export checks PASS; runtime-equivalent five-rule implementation promoted.120CPU driver controls and current41port rows pass. Fresh complete default required; old failed trials/normal gate retained.'})
ledger['next_actions'][0]={'priority':0,'requirement':'IMPORT-02','action':'Five qualified native Source joints are promoted for three Junko strands. Commit/push/read back the increment, then run a fresh complete Windows default on that exact checkpoint. Preserve initial direction failures, unchanged normal-fidelity failure, all62 statuses and deferred human checks.'}
assert stable==[(r['id'],json.dumps(r['implementation'],sort_keys=True),r['acceptance_status'],json.dumps(r['external_dependencies'],sort_keys=True)) for r in ledger['requirements']]
ledger_path.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
entry='''

## 2026-11-15 — Three imported hair strands qualified and promoted

Actual isolated strict2 state verification passes266/0 across three instances;
actual editor writer83, packed cold reader/export11 and linked cold reader8
all pass(102total). The retained root wrapper exits0/reaped in62.4266seconds;
three real private jobs/desktops close without foreground activation, timeout
or termination. Original1014 functional sources, two native inputs, baseline
and sealed candidate remain exact before promotion. Success packet:
experiments/native_five_qualified_actual_20261116, INDEX429ea76d462a385cfa2d292ed9c2c12dd9fbf9e52193f63bfb0e7776324dd655.
Root separately verifies173archive checks; these are not product checks.

The new transverse fan fixture preserves the old direction predicates and all
numeric tolerances, proves fixed root/actual five-anchor centroid/opposite
fields, and keeps gust wiggle. Animated0.47radian root geometry remains tested
in the actual Record/Undo/HAS/export pipeline. Earlier82/1 and57/2 failures
remain failed and recoverable. Native.step means now7.521–9.054ms, peak13.289ms;
the camera fixture differs, so no paired speedup or120Hz/FPS pass is claimed.

Promoted exactly10 reviewed files: three product files, four exact qualified
test/driver files, two UI strings in physics_editor, and two manifest hash
successors. Two source headers change comments only; runtime code matches the
qualified Stage3. Main now solves native8,17,18,26,27 (three strands,5of49),
with all69 identity/rest/context/scale/pose guards and atomic per-instance
state. User text names three supported strands. Remaining44 rules are inert;
same-actor ragdoll, collision/SDK/client/artist parity and normals remain separate.
Current120CPU driver controls and all41 reviewed helper/wind rows pass with
explicit checkout-EOL reconstruction. Functional source count is now1019.

The first strict2 application helper refused a dictionary/list index mismatch
before any write; its correction then applied the exact reviewed source.
The first120-control invocation refused a relative output path before tests;
the required fresh absolute owned path then passes120/0. Neither is a runtime
failure or a relaxed gate. Detailed benchmark:
docs/benchmarks/native_five_qualified_2026-11-15.json. Commit/push/read back,
then run fresh full Windows verification. The earlier dbf complete run remains
FAILED; manual exercise DEFERRED/no result;55/62 and52/54 unchanged.
'''
for name in ('LLM.md','docs/progress_memo.md'):
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as f:f.write(entry)
print(json.dumps({'benchmark':pin('docs/benchmarks/native_five_qualified_2026-11-15.json'),'current_port_rows':sum(len(v) for v in ports.values()),'main_rules':5,'fresh_full_required':True}))
