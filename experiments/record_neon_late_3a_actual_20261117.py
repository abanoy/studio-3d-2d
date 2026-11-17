"""Select scalar targeted-run outcomes; never copy native report bodies."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'has-neon-review-20261116-c2d52ff/output'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=ROOT/'experiments/neon_late_stage_cases_source_20261117'
assert sha(packet/'INDEX.json')=='790277ef5e25f78e63d46350dba0304dce6c083c84ad5e010ac478fcea865ea3'
spec=importlib.util.spec_from_file_location('root_actual_canonical_tail',packet/'late_cases.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
run=OUT/'neon-late-3a-attempt2';report=load(run/'verification.json');outer=load(run/'TARGETED-COMPLETION.json');tool=load(run/'ROOT-TOOL-TERMINATION.json')
assert sha(run/'verification.json')=='e366426598261c13674aafdd4c8fedc9cb5a350ebfcf8be08bd10906d4011167'
assert sha(run/'TARGETED-COMPLETION.json')=='2ed5edd7bed4a83b2a3245ff73da41d52d7cf5c78ba55d83eba88e5b54e0408a'
assert report['passed'] and report['all_functional_source_unchanged'] and report['host_scopes_closed'] and report['functional_source_files']==1029
assert outer['all44_completed_and_canonical_reports_passed'] and tool['tool_session_id']==20079 and tool['tool_result']['exit_code']==0 and 'session_id' not in tool['tool_result']
assert [r['label'] for r in report['rows']]==[r[0] for r in A.CASES]
rows=[]
for r in report['rows']:
 assert r['exit']==0 and r['retained_Popen_reaped'] and not r['timed_out'];A.assert_canonical_report(r['label'],r['report'])
 row={k:r[k] for k in ('label','exit','seconds','retained_Popen_reaped','timed_out')}
 for k in ('checks','failures'):
  if type(r['report'].get(k)) is int:row[k]=r['report'][k]
 if type(r['report'].get('native_tested')) is bool:row['native_tested']=r['report']['native_tested']
 rows.append(row)
first=load(OUT/'neon-late-3a-attempt1/verification.json')
assert len(first['rows'])==8 and first['rows'][-1]['exit']==1 and first['all_functional_source_unchanged'] and first['host_scopes_closed']
record={'observed_utc':datetime.now(timezone.utc).isoformat(),'candidate_commit':'3a3701ab6edfa81dc883759403c170b8555aab07','format':'has_selected_targeted_late_stage_outcomes_1',
 'result':'ALL44_TARGETED_WRAPPERS_PASS','rows':rows,'source_files_unchanged':1029,'all_wrapper_processes_reaped':True,'host_scopes_closed':True,
 'private_report_sha256':sha(run/'verification.json'),'private_tool_terminal_sha256':sha(run/'ROOT-TOOL-TERMINATION.json'),
 'before_after_map_sha256':sha(run/'source-before.json'),'canonical_additional_report_assertions_preserved':True,
 'prior_attempt':{'closed':True,'wrappers':8,'last_exit':1,'cause':'Root targeted runner omitted canonical HYBRID_NATIVE_INPUTS; component wrapper correctly refused absent native coverage.','native_acceptance_pass':False},
 'full_suite_passed':False,'product_merged':False,'new_owner_copy_or187':False,'raw_native_reports_arrays_pixels_included':False}
dest=ROOT/'experiments/neon_late_3a_actual_20261117';dest.mkdir(exist_ok=False)
(dest/'OBSERVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(dest/'README.md').write_text('All 44 canonical late-stage wrappers pass with their additional report assertions. This targeted run excludes early/core and media-aggregate qualification; a fresh full run remains required. Raw reports and native arrays remain private.\n',encoding='utf-8')
files=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.iterdir())]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_scalar_targeted_actual_packet_1','files':files},indent=2)+'\n',encoding='utf-8')
paragraph='''
### November 17, 2026 — all 44 later-stage verifiers pass on 3a

Actual targeted attempt2 completed with all44 canonical wrappers passing, including
contact/component recording, persistence/readers, multi-audio, duration, motion,
all drawing/fill tools, recovery, Home, tutorials and first-movie completion.
Canonical extra report checks were retained; source1029 remained exact and all
per-wrapper Popen handles/host scopes closed. Tool session20079 returned0 at
18:32:59UTC; its raw terminal witness is retained privately (no outer Python
Popen/birth claim). Tail report e3664265 is private because it includes native
arrays. Only source-authored labels, scalar counts and outcomes are published.

Attempt1 is retained as a closed setup failure: Root omitted the canonical raw
VRM input directory; the eighth wrapper correctly refused missing native coverage.
Attempt2 mirrors the canonical input settings, with VRM1 hash14d2 confirmed.
It does not replace the required new full158/core36/movie21 qualification.
No merge, new review or cold187 is claimed; acceptance55/62 and implementation
52/54 remain unchanged. Human observations stay deferred.

The independent PMX raw-table oracle now passes18 authored CPU methods, including
720 layouts and two manual fixtures, with source-peer review. Four owner PMX2.0
UTF16LE originals have stable read-only metadata and byte-equal owned copies
(20,781,686B). Their body/joint tables have not yet been observed. The independent
oracle/candidate harness is source-only work; no native/production/simulation
qualification follows from staging or synthetic tests.
'''
for name in ('LLM.md','docs/progress_memo.md'):
 with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
path=ROOT/'docs/benchmarks/neon_review_2026-11-17.json';bench=load(path);bench['preceding_color_focus']=bench['latest_observation'];bench['latest_observation']=record
path.write_text(json.dumps(bench,indent=2)+'\n',encoding='utf-8',newline='\n')
path=ROOT/'docs/completion_checklist.json';ledger=load(path);ledger['next_actions'][0]['action']='3a source-frozen targeted44PASS with canonical outer checks,source1029 unchanged/owned processes and host scopes closed; original color44/0 exactpixel diagnostic also passes. Run fresh full158/core36/movie21 before merge/newownerreview/cold187. While lane closed, independent readonly Bmetadata and PMX oracle observations may proceed with truthful unqualified scope. Humanchecks deferred; originals/tools/reviews protected.'
path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'targeted_wrappers':len(rows),'passed':True,'full_or_merge_claimed':False,'INDEX_sha256':sha(dest/'INDEX.json')}))
