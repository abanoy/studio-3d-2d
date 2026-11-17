from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
note='''\n## 2026-11-17 — Second Neon full failure closed; setter boundary measured

The381 full verifier failed at animated_channels47/1 after316seconds, with
all1028functional files unchanged. All three retained MMD/GMod/SFM native
fixtures executed. Root's strict failed-terminal helper derived27physical jobs:
25exit0, one source-registered Krita cancellation2 and one animated assertion1.
Both exact coordinator6012/Python8148 identities were absent; all nested jobs
and desktops closed. Failed-only lease released2026-11-17T00:46:22.2853317Z.
Inventorybfc025aaf492ee5eb8b7b19c8cd0a581134773fa111a3c89ef452c30fdca0d92.
No stale final report or full PASS was used. Raw47/1 report8b611de2 is retained.

The remaining content-end input scrolled the requested native channel above
the compact viewport. Revealing that channel and adding a pre-click visibility
assertion passes48/0 across all three native fixtures. The414-GD source audit
found two additional older focused cases, neither directly registered in the
default verifier. Original movement shows3offscreen-channel failures and then
a stale Dictionary.image API error; its existing watchdog exits and all jobs
close. The Drawing/raster-owner code AND stale test are exactfull52sources, so
that API error is preexisting standalone fixture code, not a Neon Drawing change.
Revealed channels plus current edit_image API pass both legacy/component movement
profiles. No original predicate was removed; original failures stay preserved.

Original waveform samples were outside the image/track viewports. After reveal,
the unchanged Classic467d45 predicate passes13/0, fourbars. Approved Neon uses
another RGBA palette. A source-derived theme/bounds successor preserves13old
checks and adds one: Classic14/0, Neon14/1 withthreebars and validbounds. Keep
this failure; diagnose the unmatched sample without wideningRGB.02 tolerance,
reducing fourbars or taking expected colors from observed pixels. It is not a
new normal/physics result. Current third full run has NOT started yet.

The native setter diagnostic actually completes in24.1789978seconds, wrapper
exit0/reaped, private placement and hidden sentinel cleanup verified. All26
roles, full52source1019, original inputs and runtime/source catalogues recheck;
both owned scopes are closed. PUBLIC_SETTER SHA
86126f272e52b60323e9a49443df7d320472c61cfae2eada3f88b90c57dd262b;
placement723d2cb834c28e8602c0c5b5ca67943f4d75a257b02bdf5f52997243667ad9ed.
The15,172,535-byte private arrays remain output-only and were not published.

Incoming native setter words are exact. Immediate Blender readback differs above
2e-5 on6846/34332hair corners (max.0007408270) and2130/8370Hat corners
(max.0012586271). Before/after validate normal hashes are unchanged. Untouched
unobserved replay is bit-exact, and its saved-fixture corner comparison is zero.
Thus the first observed discrepancy is between correct setter input and immediate
API readback, before later validation/export. This does not identify a particular
C++ encoder routine. Original GLB normal fidelity remainsFAILED_UNQUALIFIED.
An isolated exact-ID carrier correction is being CPU/source-reviewed; no native
normal repair, derivative GLB, requalification or production change is claimed.

Keep main's1019functional reference and candidate worktree separate. No redesign
merge yet. Current candidate test input successors remain under focused review;
commit the final reviewed fixture state and run the complete default again.
All formal statuses/denominators remain55/62 and52/54; no owner result inferred.
'''
for name in ('LLM.md','docs/progress_memo.md'):
    p=ROOT/name
    if '## 2026-11-17 — Second Neon full failure closed; setter boundary measured' not in p.read_text(encoding='utf-8'):
        with p.open('a',encoding='utf-8',newline='\n') as f:f.write(note)
p=ROOT/'docs/NEXT_SESSION_PLAN_2026-11-17.md';body=p.read_text(encoding='utf-8')
body=body.replace('The complete corrected Windows run is ACTIVE in the separate checkout','The381 corrected Windows run FAILED at animated_channels47/1; all27private\njobs are closed and the lease released. A third complete run has NOT started.\nThe retained failed run is in the separate checkout')
body=body.replace('Do not edit that source/HEAD or launch\nother graphics/native jobs until terminal and authoritative closure are audited.','Its terminal/source/physical closure has been audited. Later test input changes\nare being qualified before a successor commit and fresh complete run.')
body=body.replace('Once the exclusive native slot is released,\nrun the sealed successor and record actual setter/control/validate boundaries.','The sealed sentinel successor now actually completed: exact native inputs,\nimmediate readback loss, unchanged validate stage and bit-exact replay/saved\ncontrol. See source_normal_setter_2026-11-17 benchmark; no repair is active.')
p.write_text(body,encoding='utf-8',newline='\n')
p=ROOT/'docs/benchmarks/neon_review_2026-11-17.json';b=json.loads(p.read_bytes())
b.update(corrected_full='FAILED_381_ANIMATED_CHANNELS47_1',corrected_full_private_jobs_closed=27,corrected_full_sources_unchanged=1028,third_full='NOT_STARTED',native_channel_fixture_successor='48/0_all3native',movement_legacy_and_component_successors='PASSED',waveform_palette_successor={'classic':'14/0','neon':'14/1_PENDING_DIAGNOSIS'})
p.write_text(json.dumps(b,indent=2)+'\n',encoding='utf-8')
public_path=ROOT/'output/normal-setter-boundary-20261116-attempt1/capture/PUBLIC_SETTER.json'
public=json.loads(public_path.read_bytes());assert hashlib.sha256(public_path.read_bytes()).hexdigest()=='86126f272e52b60323e9a49443df7d320472c61cfae2eada3f88b90c57dd262b'
record={'format':'has_native_normal_setter_actual_checkpoint_1','root_diagnostic_completed':True,'public_setter_sha256':hashlib.sha256(public_path.read_bytes()).hexdigest(),'public_placement_sha256':'723d2cb834c28e8602c0c5b5ca67943f4d75a257b02bdf5f52997243667ad9ed','source_full_context':'52f63c944ded7a651da871524d23a345b606424d','expected_staging_head':'592fe4f82ec0284adaa328228da83feb9abc7814','owned_capture_seconds':24.178997799999706,'private_job_desktop_closed':True,'all26_roles_rechecked':True,'both_owned_scopes_released':True,'normal_fidelity':'FAILED_UNQUALIFIED','measured_public_scalars':public,'private_native_arrays_uploaded':False,'repair_implemented':False}
(ROOT/'docs/benchmarks/source_normal_setter_2026-11-17.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
p=ROOT/'docs/completion_checklist.json';doc=json.loads(p.read_bytes())
before={r['id']:{k:v for k,v in r.items() if k not in ('evidence','remaining')} for r in doc['requirements']}
for row in doc['requirements']:
    if row['id']=='IMPORT-03' and not any(e.get('path')=='docs/benchmarks/source_normal_setter_2026-11-17.json' for e in row['evidence']):row['evidence'].append({'kind':'test_result','path':'docs/benchmarks/source_normal_setter_2026-11-17.json','scope':'Actualexactsetterinput/immediatereadback/validate/untouchedreplay/savedcontrol boundaries measured; firstobservedAPIboundaryloss, no normalrepairorfidelitypass. Privatearrayskeptoutputonly.'})
doc['next_actions'][0]['action']='Finish preciseNeonwaveformfixture diagnosis (Classic14pass/Neon14_1retained), commitreviewedtimelinefixtures, runfreshcomplete Windowsdefault beforemerge. Nativechannel48andbothmovementprofilespass. Setterboundarymeasured; isolateexact-IDnormalrepairprototypewithoutchangingoriginalB orclaimingqualification. Keepallfailures/manualdeferrals/protectedassets.'
assert before=={r['id']:{k:v for k,v in r.items() if k not in ('evidence','remaining')} for r in doc['requirements']}
p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Recorded closed failed381, focused successors and actual setter measurement; no merge or fidelity PASS.')
