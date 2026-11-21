from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
path=ROOT.parent/'has-character-parts-headless-435-1795255808748/RootRun-1795259996694407600/PUBLIC_RESULT.json'
raw=path.read_bytes();result=json.loads(raw)
assert result['status']=='FAIL' and result['checks']==96 and result['error']=='ONLY_SYNTHETIC_PROJECT_INPUT_TYPES'
assert len(result['jobs'])==2 and all(r['status']=='PASS' and r['job_closed'] and r['wrapper_reaped'] for r in result['jobs'])
assert result['all_admitted_inputs_preserved'] and result['owned_lock_removed']
benchmark={'format':'has_character_parts_headless_partial_1','status':'96_PASS_READER_NOT_LAUNCHED_HANDOFF_REFUSED',
 'historical_revision':result['historical_revision'],'unit_checks':58,'editor_control_checks':38,'fresh_reader_checks':0,
 'failure':result['error'],'cause':'Persistent zero-byte project.json.lock refused by bounded reader-copy input filter.',
 'all_attempted_jobs_closed':True,'source_and_native_identity_preserved':True,
 'prototype_adopted':False,'real_six_part_alignment_qualified':False,'Full_qualification_claimed':False,
 'public_result_sha256':hashlib.sha256(raw).hexdigest(),'prior_identity_preflight_refusal_preserved':True,
 'bridge_controls':{'checks':32,'status':'PASS','synthetic_only':True,'native_inputs_read':False},
 'next':'Versioned reader-only successor must strictly admit the prior96 and check a fresh reader separately.'}
dest=ROOT/'docs/benchmarks/character_parts_headless_2026-11-21.json';assert not dest.exists()
dest.write_text(json.dumps(benchmark,indent=2)+'\n',encoding='utf-8')
ledger=ROOT/'docs/completion_checklist.json';old=ledger.read_bytes()
needle=b'Junko105 preflight refused before execution; old native435hosts gated.'
replacement=b'Junko105 original preflight refused; v2 unit58/editor38 pass, reader not launched due zero-byte save-lock handoff refusal. Not adopted/native-qualified; old native435hosts gated.'
assert old.count(needle)==1;new=old.replace(needle,replacement,1)
assert json.loads(old)['requirements']==json.loads(new)['requirements']
ledger.write_bytes(new)
section=('\r\n## 2026-11-21 Junko assembly partial run retained\r\n\r\n'
 'Root ran32 synthetic identity-bridge controls: PASS, no native inputs read. '
 'Versioned Junko v2 then passed58 domain and38 actual headless editor/control checks (96 total). '
 'The fresh reader was NOT launched: bounded handoff correctly refused a persistent zero-byte project.json.lock alongside the expected project and two synthetic GLBs. '
 'Both attempted jobs were reaped/closed; all4526 admitted native identities and sources were preserved, and the owned lock removed. '
 'This is a partial failed batch, not105passes. Original identity refusal and frozen seals remain. '
 'A versioned reader-only successor is in preparation; no Main adoption, real six-MDL alignment, GPU appearance or Full qualification is claimed. '
 'See docs/benchmarks/character_parts_headless_2026-11-21.json and archived public results.\r\n').encode()
for name in ('LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md'):
 p=ROOT/name;prefix=p.read_bytes();assert b'Junko assembly partial run retained' not in prefix
 with p.open('ab') as stream:stream.write(section)
 assert p.read_bytes()==prefix+section
print(json.dumps(benchmark))
