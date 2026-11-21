"""Append bounded live pickup facts, preserving all existing history bytes."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
REV='435dc02426a7cdd313e43fe674c9008520845428'
heading='2026-11-21 live continuation: Full182 running; experimental headless results'
body='''
## 2026-11-21 live continuation: Full182 running; experimental headless results

Retrieval/publication435dc02426a7cdd313e43fe674c9008520845428 is independently verified from a fresh GitHub clone: all1094 changed paths/25,775,389raw bytes/modes and1102 functional sources match exact hashes/Git blobs. The first clone was incomplete (missing index plus one long archive pathname); Root rebuilt only its index, enabled core.longpaths locally, restored the exact Git blob, then obtained a clean verification. Original failure remains in output/UI_CAMERA_FULL_LAUNCH_ROOT_20261121.json. Future Windows clones should set both core.autocrlf=false and core.longpaths=true locally before checkout; do not change owner global configuration.

Canonical Full is IN PROGRESS, not PASS: fresh isolated has-ui-camera-full-20261121-435dc02/output/windows-reference-body-1795253708684469500, verifier18456/coordinator33080, Root retained exec87359.13 declared fixture files/32,095,990bytes were staged before snapshots; originals unchanged. Exact expected182-key list and12new626-check counts are in output/FULL182_REGISTRATION_AUDIT_20261121.json; Root output/verify_full182_root_20261121.py adds explicit postflight. Early core, Neon and111 new editor controls pass; new complete report/media/private closures still pending. Do not mutate fresh source/revision/old experiments during Full. Previous170-group Full remains historical.52/54implementation and55/62formal acceptance are unchanged; human/native-artist/device/clean-offline observations are not inferred.

Separate preparation only, no product adoption: exact Godot skin-weight conversion Root171 headless controls PASS in has-miku-pure171-1795254495155816300 (40probe+27binding+26geometry+24conversion+54skin;5closed private headless jobs, all1102source/HEAD/env preserved). Child's previous desktop-creation refusal executed zero assertions and stays FAIL; host process check proved no engine/job creation, retained lock bytes were moved before exact frozen-host retry. Evidence packet output/source-miku-pure171-evidence-prep-20261121 pins02a2b531c71ccca1ae7f352cbd1ef463b646e6ff54adfb86613c4bc71d500252.13actual ArrayMesh controls,52444native weight-slot admission, palette calibration and contact remain UNRUN. Do not reuse obsolete1086 guards or count synthetic results as model contact.

Separate close-face control: source-posed-head-render-bounds-prep-20261121 pins0ab8d9e1f63e38334b4fb6de9d6ce42a893f9eee559d3a78e7317f07b5b33c68. Child and independent Root each passed the same43 synthetic controls (not additive); Root cpu-stage-1795254562029164300. First unsafe-predelete engine-error attempt is retained. Opt-in cached per-instance derived margin preserves SourceShape custom_aabb ownership, no Main hooks. Protected Youmu head has85neutral imported morph targets;5361-vertex head-margin controls are distinct from1489-vertex face-material controls. Native two-context/backoff visibility, transforms/nonuniform scale, live modifiers, export and reopen remain UNRUN.

Separate SMH-inspired camera easing preparation: Root69 pure/editor-spy controls PASS; first actual-app headless88PASS covered key-array/history Undo only. Stronger24-control fixture reproduced23PASS/1FAIL: camera position remained at baked preview after Undo, while original keys restored. Exact failure retained at has-easing435-app-cpu-1795254695259497400. Narrow successor tags only Bake history with camera_timing_bake and refreshes authored camera on tagged Undo/Redo, preserving untagged free-camera behavior. Frozen output/source-keyframe-easing435-undo-fix-prep-20261121 pins472cd37a7dd4717880fe341fa1beea942e4d58f756038a4d78b00d16451b128b. Root actual-app96PASS (24x4Classic/Neon Simple/Advanced) at has-easing435-app-cpu-1795254761995523000, and fixed69 standalone controls PASS at has-easing-headless-1795254831934151300. All children reaped/admitted inputs/env preserved. Real camera pixels/GUI/capture/movie/cold save/241-key integration remain pending; no current application files changed. These successors are proposals, not additional shipping features.

Owner review PREPARED_NOT_RUNTIME_VERIFIED: C:/a/Programming/cloudflare/HAS-Review-Editor-Camera-435dc02,1105 exact committed runtime files, unique profile, three exact private packed copies (Junko hair joints, protected close-up face, protected Miku fan). No launchers/startup/replay qualification yet; defer graphics until Full closes. Preserve earlier reviews, original projects/Steam/shared tools and this pending private deliverable; do not prompt the busy owner.

Cleanup after verified remote backup: previous three headless stages17733files/124352320logicalbytes removed; final initial prelaunch stage1095files/9020814logicalbytes now also removed after renewed377-process scan/no target matches/no unreadable runtime candidates and exact archived raw failure/driver hashes. Total18828files/133373134logicalbytes; physical allocation reclaimed unmeasured. output/HEADLESS_FIRST_VERIFIED_REMOVAL_20261121.json records actual removal. New native/private/full stages remain needed and protected.

Next: complete exact Full182 postflight and record failures honestly; then exclusive private native packing/full-slot contact and derived-face controls, owner-review startup/replay, and real easing GUI/export/cold controls. Junko split-assembly prototype is being advanced independently. Commit/push all completed source/evidence and verify remote before deleting disposable files. Goal stays active.
'''
addition=body.replace('\n','\r\n').encode('utf-8')
records=[]
for name in ('LLM.md','docs/progress_memo.md','docs/RESUME_MASTER_PLAN.md','docs/NEXT_SESSION_PLAN_2026-11-20.md'):
    path=ROOT/name;before=path.read_bytes()
    assert heading.encode() not in before
    expected=subprocess.check_output(['git','-c','core.autocrlf=false','show',REV+':'+name],cwd=ROOT)
    assert before==expected,'Concurrent history edit, refuse replacement: '+name
    with path.open('ab') as stream:assert stream.write(addition)==len(addition)
    after=path.read_bytes();assert after==before+addition
    records.append({'path':name,'old_bytes':len(before),'old_sha256':hashlib.sha256(before).hexdigest(),
      'appended_bytes':len(addition),'new_sha256':hashlib.sha256(after).hexdigest(),'original_prefix_preserved':True})
(ROOT/'output/LIVE_PICKUP_APPEND_20261121.json').write_text(json.dumps({'format':'has_live_pickup_append_1','full_status':'RUNNING_NOT_PASS','files':records},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'APPENDED_WITH_ORIGINAL_PREFIXES_PRESERVED','files':len(records),'full_status':'RUNNING_NOT_PASS'}))
