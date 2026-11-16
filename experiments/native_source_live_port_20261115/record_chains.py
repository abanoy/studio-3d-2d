"""Record executed experimental chain scope; never promote it to product parity."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
RUN='output/source-0x31-native-chains-20261115-attempt1'
def pin(relative):
    return {'path':relative,'sha256':hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()}
def load(relative): return json.loads((ROOT/relative).read_bytes())

v=load(RUN+'/verification.json'); r=load(RUN+'/result.json'); c=load(RUN+'/authoritative-closure.json')
assert v['passed'] and v['math_passed'] and v['native_passed'] and all(v['preservation'].values())
assert r['checks']==21087 and r['failures']==0 and len(r['cases'])==12 and r['dynamic_ticks']==1440 and r['rule_evaluations']==5760
assert c['runtime_lease_released'] and c['no_process_killed'] and c['all_retained_children_reaped']
benchmark={'format':'has_native_source_two_pair_actual_1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'PASSED_EXPERIMENTAL_TWO_PAIR_READINESS_ONLY','verification':pin(RUN+'/verification.json'),'result':pin(RUN+'/result.json'),
    'closure':pin(RUN+'/authoritative-closure.json'),'math_result':pin(RUN+'/math-result.json'),'source_lock':pin(RUN+'/CURRENT-SOURCE-LOCK.json'),
    'provenance_drift_acknowledgment':pin(RUN+'/PROVENANCE-DRIFT-ACKNOWLEDGMENT.json'),
    'math_checks':4012,'native_checks':21087,'native_pairs':[[17,18],[26,27]],'native25_has_retained_rule':False,
    'native25_policy':'Authored unsimulated ancestor of26; no invented rule',
    'cases':12,'ticks':1440,'rule_evaluations':5760,'root_uniform_scales':[1,2],
    'weighted_vertices':542,'shared_with_other_bones':340,'unaffected_vertices_exact':9119,'unselected_world_bones_exact':65,
    'maximum_basis_error':max(row['basis_error_max'] for row in r['cases']),
    'maximum_native_Z_tip_error':max(row['tip_error_max'] for row in r['cases']),
    'same_tick_parent_policy':'Fresh authored absolute-local poses recomposed under same-tick solved parents, including authored unsimulated intermediates',
    'Off_and_repeated_weighted_result':'EXACT','source_and_original_and_runtime_preservation':v['preservation'],
    'scope':r['scope'],'current_product_native_rules':1,'current_complete_default':'PENDING_AFTER_COMMIT',
    'formal_acceptance':'55/62_UNCHANGED','implementation':'52/54_UNCHANGED'}
destination=ROOT/'docs/benchmarks/native_source_chains_2026-11-15.json'
with destination.open('x',encoding='utf-8',newline='\n') as stream: json.dump(benchmark,stream,ensure_ascii=False,indent=2);stream.write('\n')
entry='''

## 2026-11-15 — Actual connected native joints and reviewed generic preflights

The separately staged scalar64 parent-chain runner passes4012synthetic math
checks(maxerror8.88e-16), then21087actual native checks/12cases/1440ticks/
5760ruleevaluations for17→18 and26→27 at roots1/2. Actual Model/weighted CPU
queries preserve9119unaffected points and65unselected bones exactly;542weighted
vertices(340shared) respond distinctly to temporary signed/strong inputs. Off
at authored12/24 and repeated12-input weighted results are exact. Maximum basis
error1.00774e-6 and native-Z tip error7.63312e-7 stay inside unchanged2e-5 gates.
All fourheadless childrenexit0/reap, ninepreservation groupspass, noengineerror
or kill; authoritativeclosure02:13:54.990457Z releasesruntimelease. Native25
has NO retained jiggle rule; its authored intermediate transform is preserved.
An incorrect frozen README sentence is corrected in a separate erratum.

Evidence: output/source-0x31-native-chains-20261115-attempt1 and
docs/benchmarks/native_source_chains_2026-11-15.json. This remains experimental
four-rule CPU orchestration, not product parent-chain/fan/body/Record/GPU/SDK
qualification. Production still runs the separately qualified native8 only.
Historicalfullf0dd receipt is explicitly acknowledged as an earlier source;
current sources are independently frozen and current full-default is pending.

Default preflight review found two old physics_editor hashes. Exact old wind/
helper manifests and observed metadata refusals are preserved. Reviewed
successors change only that row's raw/LF hashes plus a provenance pointer;
16/25pathsets, otherrows and strict driver gates stay exact. Actual metadata
functions accept41rows, existing helper-driver CPU suite passes120checks with
zero subprocess/runtime attempts, and every other1014-file catalogue identity
stays exact. Evidence: experiments/source_native_live_independent_review_20261115/
manifest-successor-20261116. A clean committed functional source is required
before the fresh full-default run; no allow-working or hash bypass is added.
All broad acceptance statuses remain unchanged. Continue independent work.
'''
for name in ['LLM.md','docs/progress_memo.md']:
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream: stream.write(entry)
print(json.dumps({'benchmark':pin('docs/benchmarks/native_source_chains_2026-11-15.json'),'checks':r['checks']}))
