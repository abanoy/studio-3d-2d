"""Record completed review/diagnostic and the retained isolated domain failure."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def load(n):return json.loads((ROOT/n).read_bytes())
def pin(n):return {'path':n,'sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest()}
def write(n,v):
    with (ROOT/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
review=load('output/native-hair-review-root-execution-20261116-attempt1/verification.json')
assert review['passed'] and review['checks_observed']==187 and all(review['preservation'].values())
normal=load('output/normal-boundary-20261116-attempt2/root-execution/verification.json')
comparison=load('output/normal-boundary-20261116-attempt2/BLENDER_BOUNDARY_COMPARISON.json')
assert normal['diagnostic_completed'] and normal['runtime_lease_released'] and comparison['status']=='COHERENT_BOUNDARY_MEASUREMENT'
write('docs/benchmarks/native_five_owner_review_2026-11-16.json',{'format':'has_native_five_owner_review_actual_1','status':'PASSED_187_SOFTWARE_CHECKS_MANUAL_DEFERRED','source_commit':'52f63c944ded7a651da871524d23a345b606424d','review_directory':review['review'],'checks':187,'examples':4,'preservation_gates':review['preservation'],'root_execution':pin('output/native-hair-review-root-execution-20261116-attempt1/verification.json'),'public_packet':pin('experiments/native_five_review_actual_packet_20261116/INDEX.json'),'actual_native5_On_tick_Off':True,'human_observation':'DEFERRED_NO_RESULT','old_review_preserved':True,'clean_install_or_artist_qualification_claimed':False})
write('docs/benchmarks/source_normal_boundary_2026-11-16.json',{'format':'has_actual_source_normal_boundary_1','status':'COHERENT_MEASUREMENT_ORIGINAL_FIDELITY_FAILED','execution':pin('output/normal-boundary-20261116-attempt2/root-execution/verification.json'),'public_packet':pin('experiments/normal_boundary_actual_20261116/INDEX.json'),'original_raw_gate':comparison['original_raw_gate'],'metrics':comparison['metrics'],'exporter_prediction_error':comparison['exporter_prediction_error'],'all_candidate_bounds':comparison['native_to_blender_all_candidate_bounds'],'multiple_normal_classes':comparison['multiple_exact_normal_classes'],'matched_vertices':9661,'unmatched_vertices':0,'private_capture_identical_across_attempts':True,'prior_attempt':'FAILED_DESKTOP_CONFIRMATION_COMPARISON_UNRUN','causal_limit':comparison['causal_limit'],'next':'Observe exact SourceIO setter inputs and immediate/later Blender normal readback; preserve unambiguous source vertex identity. No normal correction or tolerance change implemented.'})
domain=load('output/six-foot-domain-20261116-attempt1/Studio/output/domain/result.json')
assert domain['checks']==444 and domain['failures']==7 and domain['complete_assertion_set']
write('docs/benchmarks/six_foot_gd_initial_2026-11-16.json',{'format':'has_six_foot_initial_engine_probe_1','status':'FAILED_ISOLATED_DOMAIN_MAIN_UNCHANGED','checks':444,'failures':7,'failed_names':[k for k,v in domain['named_checks'].items() if not v],'execution':pin('output/six-foot-domain-20261116-attempt1/verification.json'),'result':pin('output/six-foot-domain-20261116-attempt1/Studio/output/domain/result.json'),'boundary':'UNRUN_AFTER_DOMAIN_FAILURE','parser_passed':True,'root_lease_released':True,'actual_import_normalization_active':False,'application_source_modified':False,'next':'Diagnose schema encode discrepancy against transported oracle; preserve first failure and all exact numeric checks.'})
p=ROOT/'docs/completion_checklist.json';d=json.loads(p.read_bytes())
stable=[(x['id'],x['implementation'],x['acceptance_status'],x['external_dependencies']) for x in d['requirements']]
for row in d['requirements']:
    if row['id'] in ('IMPORT-02','IMPORT-03'):
        row['evidence'].extend([{'kind':'test_result','path':'docs/benchmarks/native_five_owner_review_2026-11-16.json','scope':'New52f sibling review passes187actualsoftwarechecks,4examples/9preservationgates,includingrealnative5On/tick/Off; manualreviewdeferred.'},{'kind':'test_result','path':'docs/benchmarks/source_normal_boundary_2026-11-16.json','scope':'ActualcoherentBlenderboundarymeasurement9661witnesses/predictionerror0; originalraw8364failuresremain. No native-normal fidelity pass.'}])
d['next_actions'][0]={'priority':0,'requirement':'IMPORT-03','action':'Publish and remotelyverify completed full52f/187review/coherentnormalmeasurement plus source-only prototypes. Then qualify setter/Blender-storage normal probe and repair isolatedsixfoot schema-encode7failures. Keep all firstfailures/tolerances/manualdeferrals andprotectedassets; active6ft import remains unimplemented.'}
assert stable==[(x['id'],x['implementation'],x['acceptance_status'],x['external_dependencies']) for x in d['requirements']]
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
entry='''

## 2026-11-16 — Updated review187 passes; normal boundary measured

Built the fresh sibling HAS-Review-20261115-Native-Hair-52f63c9 from exactGit52f,
approveddependencies and retained four-example DATA. Final-location private
replay passes187checks(44+46+56+41),4closedjobs and9preservationgates. Junko's
ordinary Hair&clothes checkbox creates5states, advances7natural fixedticks,
then Off restoresall69worldbones/root/authoreddata/source/history exactly.
The old review remains unchanged; manual acceptance is DEFERRED/no result.
Publicpacket experiments/native_five_review_actual_packet_20261116 INDEX
766d30601f902ef7485a2cbd9827c1d52066a6aea7da9251666f9d12cf7a0043.

Background Blender attempt1 completes its read but fails wrapper placement.
Attempt2 adds a zero-size hidden disabled nonactivating STATIC placement HWND;
the unchanged outer monitor confirms the real owned private window. Sentinel
is destroyed finally. No desktop switch/show/activation or numeric body change.
Capture exits0/reaped7.942s; comparison0/reaped3.488s; job/desktop close and root
observes0ownednativecommands. The17MB privatecapture hashes EXACTLYmatch across
attempts. Originalfirst failure stays failed; raw arrays stay PRIVATEoutput.
Two additional stage preflights refuse transient ffmpeg/pythonw stamps before
writes. Strict repeat observations and unchanged whole preflight pass; cause
remainsunknown. Roottrace wrapper first misses probe_support module searchpath;
corrected path then passes without touching reader/gates. Coordinator preparation
also had shell-quoting and index-list/dict setup errors before native launch;
corrected source is retained, not represented as a product failure or pass.

All9661exported vertices match42,702capturedcorners; predicted exporter output
is EXACT (maxerror0). The raw normal gate is reproduced:8364/9661fail above2e-5,
maximum.0012165467. Native→savedBlenderbest compatiblecorners has2108failures,
max.0012586271; Blender→GLB has8249above, max8.2889e-5. Unit-length deviations
are below2.2e-7; normalization does not resolve direction error. Eight normal
classes have ambiguous compatiblecorners; allcandidatebounds are preserved.
This localizes measured differences before export plus export-rounding loss;
it does not prove the original setter/encoder cause. Next probe instruments
exact setter inputs/immediate read/validate timing, without nearest-normal repair.
Publicpacket normal_boundary_actual_20261116 INDEX240f3d33ff7e2a156731b3f637f18d6139d2bb6c31147723a4ed760d3c86fabd.

The isolated six-foot GDScript prototype now parses, but its actual444check
domain run fails7schema_encode rows (437pass). Boundary21 remains UNRUN.
Both owned headlesschildren exit/reap, sourcespreserved and nativeclosure0.
Main1019functional files stay untouched; no active normalization or score change.
Keep the sealed source-only predecessor and failed actual run. Diagnose the
encoder/oracle transport before a successor; no assertion/tolerance is waived.
Formal55/62 and52/54 unchanged. Publish completed evidence, verify remote,
then review exact disposable cleanup; continue independent implementation.
'''
for name in ('LLM.md','docs/progress_memo.md'):
    with (ROOT/name).open('a',encoding='utf-8',newline='\n') as f:f.write(entry)
print(json.dumps({'review_checks':187,'normal_status':comparison['status'],'normal_fidelity_passed':False,'six_foot_domain_failed':7,'main_source_changed':False}))
