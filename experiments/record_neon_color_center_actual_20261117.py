"""Record exact scalar outcomes only; keep native coordinates, pixels and reports private."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'has-neon-review-20261116-c2d52ff/output'
load=lambda p:json.loads(p.read_bytes())
focus=load(OUT/'neon-color-center-3a3701a-attempt1/verification.json')
assert focus['passed'] and focus['all_functional_source_unchanged'] and focus['host_scopes_closed'] and focus['functional_source_files']==1029
case,=focus['rows'];assert case['exit']==0 and case['retained_Popen_reaped'] and case['report']['checks']==44 and case['report']['failures']==0
old=load(OUT/'neon-color-diagnostic-696-attempt1/PRIVATE-native-diagnostics.json')
new=load(OUT/'neon-color-diagnostic-center-attempt1/PRIVATE-native-diagnostics.json')
old_record=load(OUT/'neon-color-diagnostic-696-attempt1/DIAGNOSTIC-RECORD.json')
new_record=load(OUT/'neon-color-diagnostic-center-attempt1/DIAGNOSTIC-RECORD.json')
assert len(old)==len(new)==3 and old_record['child_exit']==1 and new_record['child_exit']==0
for record in (old_record,new_record):
 assert record['reaped'] and record['private_job_and_desktop_closed'] and record['host_scope_closed'] and record['functional_sources_unchanged']==1029 and record['native_input_files_unchanged']==36
assert all(row['got_RGBA']==row['reference_at_last_result_RGBA'] for row in old)
assert sum(not row['operands']['picked_color_exact'] for row in old)==1
assert all(all(row['operands'].values()) and row['last_result_pixel']==row['native_intended_pixel'] and row['got_RGBA']==row['wanted_RGBA'] for row in new)
record={'observed_utc':datetime.now(timezone.utc).isoformat(),'candidate_commit':'3a3701ab6edfa81dc883759403c170b8555aab07',
 'fixture_test_sha256':'102ec02e262644a641f6ecc43020940c33834a59b695cfdc0d2d889cc8cae781','application_code_changed':False,
 'original_verifier':{'checks':44,'failures':0,'native_cases':3,'seconds':case['seconds'],'reaped':True,'scope_closed':True,'functional_sources_unchanged':1029},
 'before_diagnostic':{'native_cases':3,'exact_color_failures':1,'other_four_operands_all_passed':all(all(v for k,v in row['operands'].items() if k!='picked_color_exact') for row in old),'sample_matches_actual_neighbor_pixel':True,'closed':True,'source_and_36_native_files_unchanged':True},
 'corrected_diagnostic':{'native_cases':3,'all_five_operands_passed':True,'all_intended_pixels_sampled':True,'all_exact_reference_colors':True,'closed':True,'source_and_36_native_files_unchanged':True},
 'correction':'Aim half a pixel inside the same expected output pixel; preserve all expected colors/checks/thresholds/cases.',
 'full_suite_passed':False,'merged':False,'new_owner_copy_or187':False,'raw_native_coordinates_colors_and_reports_included':False}
dest=ROOT/'experiments/neon_color_center_actual_20261117';dest.mkdir(exist_ok=False)
(dest/'OBSERVATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
(dest/'README.md').write_text('The original 44-check verifier and passive three-case diagnostic pass after a one-line test-input correction. Application sampling code is unchanged. Full qualification and merge remain outstanding. Raw native pixels, coordinates and reports are private.\n',encoding='utf-8')
rows=[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(dest.iterdir())]
(dest/'INDEX.json').write_text(json.dumps({'format':'has_scalar_focused_actual_packet_1','files':rows},indent=2)+'\n',encoding='utf-8')
paragraph='''
### November 17, 2026 — exact native color checks pass after input correction

The passive diagnostic reproduced the Miku color failure while the other four
preservation operands passed. Canvas floating-point mapping put the integer-edge
test click one row above its intended pixel; the picker returned the exact color
at that actual pixel. A second fixture had the same shift masked by equal neighbor
colors. Application sampling code is unchanged.

Candidate 3a3701ab6edfa81dc883759403c170b8555aab07 changes only the native test
click to the center of the SAME expected pixel. All original expected colors,
44 assertions, thresholds and three native cases remain. The original verifier
now passes 44/0 in 19.8323144 seconds. A separate passive diagnostic also passes:
all three intended pixels, exact colors and five preservation operands match.
All private jobs/host scopes closed; source 1029 and 36 native files unchanged.
This is focused evidence; later-stage preflight and a new full run remain required.

Main 855d67fe44868793a29d6c6c75c61c0ba86236d2 is pushed and independently
retrieved: 67 exact files, 3,170,298 Git bytes, three EOL recipes preserving
3,191,634 working bytes. Proof 1b109da3 is retained for the next checkpoint.
No cleanup, full PASS, merge, fresh review copy or cold187 is claimed.
'''
for name in ('LLM.md','docs/progress_memo.md'):
 with (ROOT/name).open('a',encoding='utf-8',newline='\n') as stream:stream.write(paragraph)
path=ROOT/'docs/benchmarks/neon_review_2026-11-17.json';bench=load(path);bench['preceding_696_closed_failure']=bench['latest_observation'];bench['latest_observation']=record
path.write_text(json.dumps(bench,indent=2)+'\n',encoding='utf-8',newline='\n')
path=ROOT/'docs/completion_checklist.json';ledger=load(path);ledger['next_actions'][0]['action']='3a3701a corrects only native test click to same-pixel center; original color44/0 and independent3case passive diagnostic pass with source1029/native36 unchanged and private scopes closed. Run source-exact later-stage preflight, then fresh full158 before merge/newreview/cold187. Main855 checkpoint independently retrieved67files. Acceptance55/62,implementation52/54 unchanged; human checks deferred.'
path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'original_checks':44,'failures':0,'exact_native_pixels':3,'full_or_merge_claimed':False,'INDEX_sha256':hashlib.sha256((dest/'INDEX.json').read_bytes()).hexdigest()}))
