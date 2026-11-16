"""Record isolated native5 success/failure without changing the main backend."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
STAGE='output/native-five-stage-attempt1'
STATE=STAGE+'/Studio/output/source-native-five-state-20261116T032753090430'
GUI=STAGE+'/Studio/output/native-five-gui-attempt1'
def pin(name):return {'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}
def load(name):return json.loads((ROOT/name).read_bytes())
s=load(STATE+'/verification.json');sr=load(STATE+'/result.json');g=load(GUI+'/verification.json');gr=load(GUI+'/writer/result.json');c=load(GUI+'/authoritative-closure.json')
assert s['passed'] and sr['checks']==266 and sr['failures']==0
assert not g['passed'] and gr['checks']==82 and gr['failures']==1 and c['runtime_lease_released']
assert c['domain_failures']==1 and all(g['preservation'].values())
record={'format':'has_isolated_native_five_initial_results_1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'main_product_backend':'UNCHANGED_NATIVE8_ONLY','main_product_promoted':False,
        'overlay_packet':pin('experiments/source_native_five_port_candidate_v2_20261115/INDEX.json'),
        'stage_manifest':pin(STAGE+'/STAGE-MANIFEST.json'),'original_root_preservation':pin(STAGE+'/ROOT-PRESERVATION-initial-runs.json'),
        'state':{'passed':True,'checks':266,'failures':0,'verification':pin(STATE+'/verification.json'),'result':pin(STATE+'/result.json'),
                 'metrics':sr['metrics'],'source_preservation':s['preservation'],'lease_released':s['runtime_lease_released']},
        'GUI':{'passed':False,'writer_checks':82,'writer_failures':1,'readers':'UNRUN_AFTER_WRITER_FAILURE',
               'failed_gate':'fan.opposite_tip_directions','verification':pin(GUI+'/verification.json'),'writer_result':pin(GUI+'/writer/result.json'),
               'closure':pin(GUI+'/authoritative-closure.json'),'preservation':g['preservation'],'lease_released':c['runtime_lease_released'],
               'next':'Scalar-only direction diagnostic; preserve original native8 predicate and test linked-chain assumptions independently.'},
        'performance':{'native_step_mean_ms_observed':{name:gr['metrics'][name]['native_step_processing']['mean_usec']/1000 for name in ['disabled','speed3','speed12','speed50','opposite']},
                       'native_step_max_ms_observed':max(row['native_step_processing']['max_usec']/1000 for row in gr['metrics'].values()),
                       'fixed_clock_budget_ms':1000/120,'measured_only_no_FPS_pass_claim':True,
                       'next':'Strict ancestor-closure calculation candidate; retain full69 guards and actual unaffected/restoration gates.'},
        'scope':'Experimental five-rule overlay on one qualified Junko model. Not main, no Source SDK/client/artist fidelity, no same-actor active ragdoll qualification.',
        'formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED'}
target=ROOT/'docs/benchmarks/native_five_initial_2026-11-15.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2);stream.write('\n')
entry='''

## 2026-11-15 — Isolated five-rule state pass; UI directional gate still fails

Root staged sealed native5v2 only under output/native-five-stage-attempt1/Studio:
three product/five observer-driver overlays,1023sourcefiles/two copied inputs,
original main product still native8 only. Exact preparation5869b585... and
after-run preservation06e5364f... bind originalRoot/input/baseline/packet equality.

Actualheadless parse/state PASS266checks,zero failures,886successful native
steps observed across three actual Models,32invalid contexts, fresh/null/partial
baselines, constant-scale rotating roots and malformed-wrapper refusal. Both
childrenexit0/reap,noerror/kill,source/input/toolpreservationtrue,leaseclosed.
Run: .../Studio/output/source-native-five-state-20261116T032753090430.

ActualprivateUIwriter executes82checks withONEfailure:
fan.opposite_tip_directions. Other81includeweighted fan response, unaffected
regions, Off/seek/Save/LocalRecord/Undo and packed/linked save commands. Cold
readers/export remainUNRUN becausewriterfailed. Writerexit1/reaped/private
job+desktopclosed in42.972s,allfourpreservationgatestrue. Root03:33:14.6905260Z
closure confirms0ownednativecommands andnoRoottermination. Run:
.../Studio/output/native-five-gui-attempt1. PreserveFAILED/no main promotion.

The new all-five total3D-tip dot predicate and fanfixture symmetry are under
independent scalar/analytic investigation; originalnative8gate stays. Do not
waive a failure or infer actual failingjoint withouttheplanned diagnostic.
Measured successful Native.step means11.04–12.74ms(max17.723ms) exceed the
8.333ms120Hz step budget inthisdebug/test configuration. Prepare a strictly
guarded ancestor-calculation optimization and measure; no inventedFPS pass.
Benchmark: docs/benchmarks/native_five_initial_2026-11-15.json. Neither266state
PASS nor81otherUIchecksqualifiescomplete native5behavior; currentmainremains
one rule. Fullretry, SDK/artist, same-actorbody and broader49remain separate.
Formal55/62and52/54unchanged; ownerbusy, continuewithoutmanualquestions.
'''
assert sr['metrics']['completed_native_steps']==886
for name in ['LLM.md','docs/progress_memo.md']:
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(entry)
print(json.dumps({'benchmark':pin('docs/benchmarks/native_five_initial_2026-11-15.json'),'state_passed':True,'GUI_passed':False,'main_promoted':False}))
