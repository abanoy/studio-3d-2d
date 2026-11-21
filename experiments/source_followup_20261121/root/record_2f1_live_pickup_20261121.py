from pathlib import Path
import json,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
remote=json.loads((OUT/'IMPORT_INFO_REMOTE_VERIFIED_20261121.json').read_bytes());assert remote['status']=='PASS'
cleanup=json.loads((OUT/'EASING_CLEANUP_REMOVED_20261121.json').read_text(encoding='utf-8-sig'));assert cleanup['status']=='PASS' and cleanup['exact_named_roots']==7
native=ROOT.parent/'has-junko-native-stage-a-1795270452664135900/PUBLIC_RESULT.json';n=json.loads(native.read_bytes());assert n['status']=='FAIL' and n['checks']==16 and n['conversions']=={} and n['all_jobs_closed']
outer=ROOT.parent/'has-import-info-full-20261121-2f1acbd/output/root-full-launch-1795270518224140000';assert not (outer/'completion.json').exists()
record={'format':'has_2f1_live_pickup_1','status':'FULL183_RUNNING_NATIVE_REST_FAILURE_UNDER_INVESTIGATION','published_retrieved_revision':remote['revision'],'tree':remote['tree'],'selected_paths':1150,'selected_bytes':18261896,'functional_sources':1109,'canonical_groups':183,'root_full_session':56699,'outer':str(outer),'coordinator_pid':9228,'verifier_pid':13748,'Full_completed':False,'native_stage_a':'FAIL16: pure controls pass; Body rest mismatch; Dress not started; all attempted jobs closed and2859 inputs preserved','new_cleanup':{'directories':7,'files':5640,'logical_bytes':47366153,'allocated_disk_bytes_claimed':False},'formal_scores':'52/54 implementation;55/62 acceptance','recorded_ns':time.time_ns()}
(OUT/'2F1_LIVE_PICKUP_20261121.json').write_text(json.dumps(record,indent=2)+'\n')
section='''
## 2026-11-21 — 2f1 retrieved; Full183 running; verified CPU cleanup done

Published/retrieved2f1acbd7867087d9f18cfbc1122cc0c883c5f788, tree
560a8262ea392963bdf9fa55441b79774a534751. A fresh remote clone independently
matched all1,150 selected paths/18,261,896 bytes, raw SHA/Git blobs/modes and all
1109 functional sources; it was clean before staging13 legacy inputs/32,095,990
bytes, whose originals stayed unchanged. Component archive inventory7c55df06 has
1108 payloads/14,700,087 bytes plus inventory,35 complete source manifests and a
separate stronger independent read-only privacy/hash audit. No private art/assets.

Fresh Full183 is RUNNING, not passed: Rootexec56699 owns retained coordinator9228
and verifier13748. Checkout has-import-info-full-20261121-2f1acbd; outer folder
output/root-full-launch-1795270518224140000; inner
output/windows-reference-body-1795270518404649600. Do not edit that checkout or
launch competing graphics. Read actual completion before any postflight; the
strengthened independently reviewed postflight source b91c63c0 is still UNRUN.
Old c315 Full remains failed, and all old c315 successful-Full gates stay closed.

The independent actual Junko Body/Dress StageA run FAIL16 is retained at
has-junko-native-stage-a-1795270452664135900. The16 pure guards passed. Body's
real background conversion refused native_Blender_rest_matrix_mismatch inside
the strict native-to-Blender proof; Dress was never started and zero conversions
qualified. Both attempted owned jobs closed/reaped/active0; all2859 admitted
inputs, Main and environment stayed unchanged; lock removed. Evidence packet
a6a9ae50 retains public result, safe raw guard/ownership logs and an exact bounded
traceback slice with whole-log hash/offset. Models, raw matrices and full logs
remain private. Hair is preparing a diagnostic that records the first mismatched
bone index/scalar error while preserving the original refusal/tolerance. This is
an actual conversion finding, not proof that native54 follow or physics works.

Cleanup is now ACTUAL: after remote byte verification, Root rechecked all seven
explicit old Easing CPU stages, exact native64 identities/membership/raw hashes,
90 new preserved copies,92 prior archive files,5453 source references/1094 unique
c315 Git blobs and five committed icon copies. A fresh host scan saw368 processes,
zero target users and zero unreadable relevant Python/Blender/Godot commands.
Root removed only the seven literal directories listed in the published cleanup
plan:5640 files/47,366,153 logical bytes. Allocated disk space freed is not measured.
No processes were terminated. Current Full, native stages, reviews, original
assets and installed tools were not removed. Receipts: EASING_CLEANUP_REMOVED,
PROCESS_CHECK and EXACT_PREFLIGHT_20261121.json. Initial PowerShell boundary API
and creator quoting refusals happened before any removal and remain recorded.
Old authoring collectors may need exact evidence restored from Git; current
future runtime hosts have copied proof and no dependency on these deleted stages.

Continue the running Full and bounded CPU native diagnostic independently. Face
is explicitly porting the face-bounds114 host to2f1/1109/183 and the future actual
Root postflight; no GPU/native qualification or face fix is inferred from that
source work. Preserve all failed/skipped/unrun results and publish this ongoing
follow-up's source/evidence before ending. Formal52/54 and55/62 remain unchanged;
no new owner/human/device exercise and no prompt to a busy owner.
'''
for name in ('LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md'):
 p=ROOT/name;raw=p.read_bytes();assert section.splitlines()[1].encode() not in raw;p.write_bytes(raw+section.encode())
print(json.dumps(record))
