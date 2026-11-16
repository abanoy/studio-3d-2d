"""Record measured scopes without reclassifying the earlier full-default run."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(relative):
    return {'path': relative, 'sha256': sha(ROOT / relative)}


def save(relative, value):
    with (ROOT / relative).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    state = 'output/source-native-state-20261116T020227823185'
    state_result = json.loads((ROOT / state / 'result.json').read_bytes())
    state_verification = json.loads((ROOT / state / 'verification.json').read_bytes())
    gui = 'experiments/source_native_live_actual_20261115/BENCHMARK.json'
    gui_result = json.loads((ROOT / gui).read_bytes())
    assert state_verification['passed'] and state_result['checks'] == 180 and state_result['failures'] == 0
    assert gui_result['passed'] and gui_result['checks'] == 96
    observed = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save('output/source-native-state-20261116T020126056307/PRECHECK_REFUSAL.json', {
        'format':'has_native_state_preflight_refusal_1','recorded_utc':observed,
        'status':'REFUSED_BEFORE_ENGINE_LAUNCH','reason':'Restricted context denied read-only CIM process inventory.',
        'evidence_basis':'Root observed run_state_owned.py assertion at before-runtime inventory and separate native PowerShell Get-CimInstance access-denied diagnostic; this initial directory was empty.',
        'raw_child_inventory_output_retained':False,'engine_launched':False,
        'successor':'output/source-native-state-20261116T020159138961',
        'successor_status':'HEADLESS_PARSE_FAILED_TYPE_INFERENCE',
        'not_an_automatic_approval_rejection':True})
    manifest = json.loads((ROOT / state / 'SOURCE.json').read_bytes())
    production = [p for p in manifest['files'] if p['path'] in ['src/source_jiggle_math.gd','src/source_secondary.gd','src/secondary_live.gd','src/physics_editor.gd','src/fan_editor.gd']]
    assert len(production) == 5
    save('docs/benchmarks/native_source_live_2026-11-15.json', {
        'format':'has_native8_product_increment_1','owner_date':'2026-11-15','recorded_utc':observed,
        'source_base_HEAD':manifest['source_HEAD'],'status':'PASSED_SCOPED_GUI_96_AND_LATER_HEADLESS_STATE_180',
        'current_complete_Windows_default':'PENDING_AFTER_PRODUCT_CHANGES',
        'native_rules_active':1,'native_rules_retained':49,'native_rule_index':8,'native_parent_index':7,
        'qualified_profile':'Exact original Junko hair GLB; Source0x31 at conversion0.01905, no generic chains, same-actor body physics off',
        'raw_source_report_activation_changed':False,'current_review':'Earlier f0dd57a review; new backend not packaged there',
        'gui':{'benchmark':pin(gui),'packet_index':pin('experiments/source_native_live_actual_20261115/INDEX.json'),
               'checks':96,'writer':77,'packed':11,'linked':8,'closed_private_jobs':3,
               'coverage':gui_result['ordinary_editor_acceptance'],'native_fan_policy':gui_result['native_fan_policy'],
               'later_header_guard_covered_by_this_GUI_run':False,'first_attempt':'FAILED_74_CHECKS_TWO_FALSE_RAGDOLL_EXPECTATIONS_RETAINED'},
        'state':{'verification':pin(state+'/verification.json'),'result':pin(state+'/result.json'),
                 'source':pin(state+'/SOURCE.json'),'closure':pin(state+'/after-runtime-closure.json'),
                 'checks':180,'metrics':state_result['metrics'],'scope':state_result['scope'],
                 'cleanup':state_result['cleanup'],'production_source':production,
                 'first_parse_failure':pin('output/source-native-state-20261116T020159138961/verification.json'),
                 'parse_fix':'Only annotate test complete as bool; predicates unchanged'},
        'unqualified':['Other48 native rules','Same-actor active ragdoll/native coexistence','Full Source SDK/client or artist fidelity','Current complete Windows default','Current owner review of native motion'],
        'formal_acceptance':'55/62_UNCHANGED','implementation_coverage':'52/54_UNCHANGED'})
    entry = '''

## 2026-11-15 — First bounded native joint integrated with ordinary controls

Working source based on9de4e6c now adds scalar64 Source0x31 mathematics and a
qualified native8 FrontHair1 backend, selected explicitly by Hair & clothes on
the original exact Junko GLB. One of49 retained rules runs; metadata remains
inert import provenance and full-layout flags are unchanged. Helper-derived
assets and declared generic chains retain the existing generic backend.

Actual private ordinary-control verification passes96checks(77writer/11packed/
8linked), three closed jobs, four preservation gates. Seven actual fan profiles
measure disabled/zero/miss/opposite and speeds3/12/50;152weighted vertices move,
9509unaffected vertices and68other world bones remain exact. Off/seek/unrecorded
Save restore authored state, actual Local Record/Stop/Escape/Undo/Redo works,
packed+linked cold states/frames and packed PNG-export frames agree. A separate
fan's actual rigid body/RID persists through native On/Off. The first74-check
run retains two FAILED fixture expectations: this hair-only rig correctly lacks
the arm/leg chains required for automatic ragdoll. Correction preserves all
numeric gates and tests the real refusal plus independent body ownership.

Subsequent header/binding-staleness changes pass180headless lifecycle checks,
three actual Model instances,506completed native steps and23negative cases.
Header/length/mtime mutations each meet their required isolated observation.
All owned GLBs restore; passed inputs, authored69-bone state/keys/raw49 report,
source and runtimes remain exact. Parse/state children exit0/reap, no engine
errors or kills; after-runtime inventory owns0processes. First preflight was
refused by unavailable CIM access before any engine launch. First actual parse
failure is preserved; sole test fix annotates complete as bool, with unchanged
180predicates. Continuous header/length/mtime checks do not promise to detect
body-only edits preserving those fields; full source hashing is at create/reload.

Evidence: experiments/source_native_live_actual_20261115 and
output/source-native-state-20261116T020227823185; benchmark
docs/benchmarks/native_source_live_2026-11-15.json. The96GUI run precedes the
later header guard, separately covered by180state checks. Same-actor active
ragdoll, other48rules, SDK/artist fidelity and current complete-default remain
unqualified. Parent-chain proof and fresh full-default are next. The owner's
volunteered click-selection test uses the earlier f0dd57a review, which does
not contain this new native-motion backend. Formal55/62and52/54stay unchanged.
Continue independent work; no checkpoint implies a new owner pause.
'''
    for relative in ['LLM.md','docs/progress_memo.md']:
        path = ROOT / relative
        assert '## 2026-11-15 — First bounded native joint integrated with ordinary controls' not in path.read_text(encoding='utf-8')
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(entry)
    print(json.dumps({'recorded_utc':observed,'benchmark':pin('docs/benchmarks/native_source_live_2026-11-15.json')}))


if __name__ == '__main__':
    main()
