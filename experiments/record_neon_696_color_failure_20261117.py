"""Record selected scalar facts from the closed failed 696 run; keep raw data private."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT.parent/'has-neon-review-20261116-c2d52ff'
RUN=REVIEW/'output/windows-neon-696ca7f-20261117T170720480423'
load=lambda p:json.loads(p.read_bytes())
state=load(RUN/'state.json');release=load(RUN/'graphics-lease-closed.json')
invpath=RUN/'terminal-audit-attempt1/receipt-inventory.json';inv=load(invpath)
assert hashlib.sha256(invpath.read_bytes()).hexdigest()==release['receipt_inventory_sha256']=='c11d074afa51f2144cce34eb4605280aea39f789904cf327e4fc30cbcfa96e97'
assert state['status']=='failed' and state['suite_exit']==1 and state['source_unchanged'] is True
assert state['source_commit']=='696ca7f1491a43b1a2267a53f8ca0f62b7c211a9' and release['released'] is True
assert inv['unique_physical_jobs']==inv['physical_receipt_files']==93 and inv['normal_exit0']==91
assert inv['registered_cancel_exit2']==inv['failed_partial_nonzero']==1
assert len(inv['inline_receipts'])==11 and len(inv['phase_documents'])==66
assert inv['all_collected_jobs_desktops_closed_private'] and inv['all_inline_exact_physical_matches']
camera=load(REVIEW/'output/camera-range-verification.json')
assert camera['checks']==60 and camera['failures']==0 and camera['native_fixture_count']==5
assert hashlib.sha256((REVIEW/'output/camera-range-verification.json').read_bytes()).hexdigest()==inv['phase_documents'][str(REVIEW/'output/camera-range-verification.json')]['sha256']
log=(RUN/'canonical.log').read_text(encoding='utf-8')
assert 'COLOR_SAMPLER_SMOKE ' in log and '"checks":44,"failures":1' in log
failure='native color excludes selection helpers while preserving rig/source/view: pose-smoke/miku-project'
assert 'FAIL '+failure in log
record={'observed_utc':datetime.now(timezone.utc).isoformat(),'state':state,'result':'FAILED_NATIVE_COLOR_SAMPLER_CONJUNCTION',
 'camera':{'checks':60,'failures':0,'native_fixtures':5},'color_sampler':{'checks':44,'failures':1,'native_fixtures':3},
 'failure_label':failure,'cause':'NOT_YET_DIAGNOSED','physical_jobs':93,'normal_exit0':91,'registered_Krita_cancel_exit2':1,'failed_partial_nonzero':1,
 'inline_exact_matches':11,'phase_documents':66,'functional_sources_unchanged':1029,'released_utc':release['released_utc'],
 'inventory_sha256':release['receipt_inventory_sha256'],'raw_report_logs_phase_native_arrays_included':False,
 'full_pass_claimed':False,'product_merged':False,'actual_cold187_started':False}
dest=ROOT/'experiments/neon_696_color_failure_20261117';dest.mkdir(exist_ok=False)
(dest/'OBSERVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
(dest/'README.md').write_text('The camera regression passed in the full run. A later native color-picker conjunction failed for one of three retained cases. The cause remains undiagnosed. This packet contains selected scalar metadata only; raw reports and logs remain private.\n',encoding='utf-8')
rows=[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.iterdir())]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_selected_actual_failure_1','files':rows},indent=2)+'\n',encoding='utf-8')
paragraph='''
### November 17, 2026 — camera passed; native color-picker failure closed

The frozen 696 full run passed the original camera check (60/0, five native
fixtures), then failed at color sampling (44/1). One retained Miku fixture failed
the conjunction covering capture, exact color and view/world/source preservation;
the two Source fixtures passed. The failing condition is not yet identified.
No assertion or tolerance has been changed. Root will split the diagnostic before
proposing a fix. The run finished at 17:41:03.6301734Z with source 1029 unchanged.

Root's strict audit closed 93 private jobs: 91 exit 0, one registered Krita cancel
and one failed color test. All 11 inline receipts match; 66 phase documents are
retained privately. Release was observed at 17:42:05.1961829Z, inventory c11d074a.
The native lane is free and root-owned. No full PASS, merge, owner copy or cold187
is claimed. Acceptance remains 55/62 and implementation 52/54; human review stays
deferred. Raw full/phase/native reports and logs remain private.

The separate PMX archive prototype now passes 49 synthetic methods (16 archive
and 33 retained reader methods), with source-peer review. It preserves an inert,
versioned physics-declaration capsule and small descriptor through a GLB in RAM,
with integrity, provenance, unsupported-profile and capacity checks. It has not
qualified native artist PMX input, changed importing, or enabled PMX simulation.
'''
for name in ('LLM.md','docs/progress_memo.md'):
 with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
bp=ROOT/'docs/benchmarks/neon_review_2026-11-17.json';bench=load(bp)
bench['preceding_696_running']=bench['latest_observation'];bench['latest_observation']=record
bp.write_text(json.dumps(bench,indent=2)+'\n',encoding='utf-8',newline='\n')
lp=ROOT/'docs/completion_checklist.json';ledger=load(lp)
ledger['next_actions'][0]['action']='Closed 696 failed full: camera60/0 passed; color44/1 failed for one retained Miku conjunction. Diagnose the exact failed condition without weakening assertions; run appropriate focused checks then a new frozen full before merge/copy/cold187. Source1029 unchanged;93 private jobs closed, release c11d074a. Human checks deferred; native originals/reviews/tools protected.'
lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'result':record['result'],'closed_jobs':93,'raw_data_copied':False,'packet_INDEX_sha256':hashlib.sha256((dest/'INDEX.json').read_bytes()).hexdigest()}))
