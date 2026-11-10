# HAS next-session plan — shutdown checkpoint, 2026-11-10

The owner explicitly requested shutdown wrap-up and this concrete pickup plan. Pause work; do not treat the product as complete.

Repository: https://github.com/abanoy/studio-3d-2d

**Verified implementation checkpoint:** `5ab8c3911e7eba294e56bb6caaeb387ae41d4fd7`.
Camera checkpoint: `c3ea9907cd2de69396e0ce2b8daea7fdef1f62ad`.
Retrieve latest `main`, including the later commit containing this plan. The repository is authoritative; historical PC caches are not the source of truth.

## 1. First actions on return

1. Read `AGENTS.md`, both complete governing specifications, `LLM.md`, `docs/progress_memo.md`, `docs/local_acceptance_handoff.md`, `docs/windows_acceptance_followup.md`, this plan and the current completion ledger.
2. Fetch/clone latest main into a new isolated checkout. Preserve the retained checkout and private review data below; do not reset or clean an owner's working tree. If reusing the retained checkout, inspect status first: generated tracked output/bytecode is dirty, while intended source has been committed.
3. Verify source and evidence against remote. Reuse approved Godot 4.6 stable standard, Python, FFmpeg and native-worker runtimes. All automated graphics must go through `run.command` on private Windows desktops; never use a visible fallback.
4. Resume owner review of the concrete runnable update before interpreting UI requests as finished human acceptance. Then complete the full aggregate and remaining acceptance exercises in the order below.

## 2. What is implemented now — do not redo it

- Timeline can compress and scroll; its divider actually enlarges the scene. World tree and buttons fill the dock's width, including after reset/reload. The owner explicitly confirmed that clipping is fixed.
- Desktop 100% means actual window pixels rather than automatic enlargement of a fixed 1400×900 canvas. Larger 125/150/175% settings remain available and persistent. The owner said this size was good.
- Recursive horizontal/vertical dock splits, tab groups, broad proportional split targets, native floating windows, remembered nested homes, persistent split sizes/selection/geometry and v1/v2 → v3 migration. The requested example—two groups across the top, with further rows inside one column—passes actual mouse-drag and cold-process tests. **The owner has not reviewed this latest nested version yet.**
- Ctrl temporarily slows WASD flight to 0.75 units/s; normal is 3 and Shift is 8. Releasing Ctrl restores the appropriate speed without ending the gesture. Additional held camera buttons preserve the original cursor position. Last release/Escape requests return through viewport coordinates; app switching suppresses the warp. **Physical cursor return still needs an owner desktop observation.**
- Fan **Aim at hair**, one Undo, scale-aware placement, selected-model targeting for **Add fan**, and visible air-reach feedback. Deterministic fixed-step gusts/crossflow keep reached loose joints moving; zero speed or missed airflow adds no flutter. **Latest fan behavior still needs owner visual feedback.**
- Exact historical `hecatia.kra` was supplied and verified; fresh Krita 32-writer + 5-cold checks pass. Current native fixtures rebuild independently of the installed Studio's output cache.

Useful source/tests:

| Area | Files |
| --- | --- |
| Nested docks | `src/workspace_layout.gd`, `src/dock_tree.gd`, `tests/verify_workspace_nested.py`, `tests/verify_workspace_docking.py` |
| Camera | `src/app.gd`, `src/world_selection.gd`, `tests/verify_orbit_navigation.py` |
| Fan | `src/airflow.gd`, `src/fan_editor.gd`, `src/secondary_live.gd`, `src/physics_editor.gd`, `tests/verify_fan_flutter.py`, `tests/verify_fan_motion.py` |
| Current native fixtures | `tests/native_fixture_root.py`, `tests/prepare_native_projects.gd`, `docs/windows_aggregate_fixtures.md` |

## 3. Features still not implemented, or deliberately limited

These distinctions matter: do not call an unobserved acceptance exercise an unwritten feature, and do not promote optional ideas into required work.

### Docking limits / possible further requested refinement

The recursive arrangement requested by the owner is implemented. Current dockable panels are **World, Properties and Timeline**. These additional capabilities are not implemented:

- Docking every other tool window, such as Layers or Tutorials, into the same tree.
- Detaching an entire multi-tab/split group as one compound native window; current floating windows contain one panel each.
- Direct tab-strip reordering and separate explicit docking-target icons. Current interaction uses panel/tab dragging with highlighted half-panel previews and proportional edge zones.
- Snapping by dragging the operating-system window title bar itself; drag the panel's internal title/tab label to redock.

Next action: show the implemented nested behavior to the owner and obtain the remaining concrete arrangement/visual complaint. Implement additional items only if requested or supported by measured usability need; they are not new mandatory completion-ledger IDs.

### Native coverage that remains partial

`IMPORT-02` and `IMPORT-03` are the only two required implementation groups still marked **partial**. Current supported Source/MMD/VRM routes have software evidence, but this does not mean every native shader, cloth/rig simulator, Source physics feature or BSP surface/lightmap is reproduced.

- Supported native geometry/material/UV/rig/expressions and dependency reporting still need artist comparison to the actual originals. Fix concrete mismatches, then rerun the relevant native/cold/movie checks.
- Preserve explicit Source lightmap/atlas/downsampling/displacement limits. The current Flatgrass case baked 29 brush faces, with one prop, 12 textures and two static lights. `temp.gma` is Transit and currently refuses the documented 64-static-light profile bound; do not claim universal map compatibility or quietly raise limits.
- Full ecosystem-native shader/physics equivalence is not implemented or promised. Distinguish required supported profiles from optional roadmap extensions.

### Fan/physics limits

The gust model is bounded relative airflow, not calibrated fluid simulation. Existing joint stiffness, drag, colliders and declared chains determine response. No automatic world floor, automatic pose reset, full mesh-cloth solver or perpetual motion with fan off was added. A 3D airflow-cone gizmo is not implemented; reach text and Aim at hair are present.

The copied owner recovery had Hips Y ≈ **−80.360916** while its fan remained near the original height. All 12 chains missed the stream at strengths 3/12/50. Do not reset that pose silently. Aim the fan or let the owner deliberately reposition/reset using ordinary controls. Keep body Physics off for a posed standing character unless an intended collision environment is present.

### Optional / OPEN work — not a required backlog by default

- Optional AI/line-art/painted in-between suggestions: deferred and opt-in only.
- Remaining advanced drawing refinements: audit existing selection/lasso/mask/palette tools first; several already exist. Do not rebuild the whole category from its historical title.
- Photorealism/ray tracing/high-end renderer: preference open, no compulsory engine rewrite.
- Blender-assisted world authoring / USD or further native-source extensions: optional deferred.
- Third collision-following recording mode and a particular compression algorithm: suggested, not required; Local/World behavior remains governed.
- OPEN decisions remain in the ledger: further clip/ripple/cross-track semantics, multi-projection 3D path inference, assist intensity, extra UX options and public-distribution licensing. Existing package contract is resolved. Do not invent answers or publish/relicense anything.

## 4. Immediate runnable owner review

Retained review folder:

`C:\a\Programming\cloudflare\has-acceptance-session-20261110\output\owner-review`

Owner-clickable launchers: `Open Avatar.bat`, `Open Flatgrass.bat`, `Open Street.bat`, `Start review.bat`.

The six latest nested/fan sources were backed up and updated in its separate `Studio` source snapshot. Camera sources were updated earlier. Normal installed Studio was not replaced. Restart this review copy to load the latest code.

Next owner checks:

1. Dock Timeline above the scene. Drag World into Timeline's right outer quarter: confirm two top columns. Split another group above/below, resize, tab, detach, close/redock and restart. Record the exact remaining roughness; do not ask the owner to repeat already confirmed clipping checks without a new failure.
2. During LMB/WASD navigation, press/release Ctrl, then release the mouse away from center. Confirm both speed and physical pointer return. Automated tests verify the requested restore target on a private desktop, not the owner's actual cursor.
3. Select the model and enable Hair & clothes with body Physics off. Select the existing fan and click Aim at hair. Confirm reach text and visible continuing motion; compare strengths 3 and 12 and then 0. Record naturalness, direction, jitter or excessive response. Record is needed to keep live motion as animation.
4. Compare Avatar shape/materials/expressions to the original VRM; then review Flatgrass and street in their separate projects. These are no longer overlapping environments. Native appearance approval is still missing.

Do not operate the owner's live window automatically. Ask them to save before closing. Preserve recovery; their current live work can differ from the original packed projects.

## 5. Complete the full aggregate — still unpassed

The aggregate was deliberately stopped several times for actionable owner UI requests, most recently before nested docking. Those interruptions are not spontaneous test failures and are not passes. Scoped new suites pass; do not substitute them for completing `tests/verify.py`.

The original KRA is now available:

`C:\a\Programming\HAS\hecatia.kra`

SHA256: `fff3599293023f41f05eb27c9d51d2af45d01493b8618c5da51067f3449ff758` (19 layers).

The 18-layer `C:\a\dump\hecatia.kra~` is a different file. Do not substitute it.

Four historical legacy source ZIPs are absent under the old installed output/checkpoints tree:

- `2026-11-04-015322-mp3-ogg-audio/development-source.zip`
- `2026-11-04-035230-joint-sound-review/development-source.zip`
- `2026-11-04-134345-media-review/development-source.zip`
- `2026-11-04-145211-project-duration/development-source.zip`

Next independent engineering task: recover the checksum-bound historical oracles used by `verify_audio_trim.py`, `verify_audio_fades.py`, `verify_project_timing.py` and `verify_current_candidate.py`. Search repository history and documented provenance first. If extracting exact historical source blobs from Git, bind them to verified commit/blob SHA and retain original reader/audio assertions. Do not fabricate a ZIP matching a new hash or weaken the old expected hashes. If exact identity cannot be established, retain that precise input blocker and ask for the actual archive.

Stage exact originals in the new owned checkout, rebuild the current native prerequisites using `docs/windows_aggregate_fixtures.md`, then run:

```powershell
$env:HYBRID_HECATIA_KRA=(Resolve-Path output/owner-fixtures/hecatia.kra).Path
$env:HYBRID_NATIVE_INPUTS='C:\a\dump'
$env:HYBRID_FFMPEG='C:\Program Files\ffmpeg\bin\ffmpeg.exe'
python -u tests/verify.py *> output/acceptance-resume.log
```

Required outcome: exit 0 and current complete aggregate report, or a precisely retained real failure/input blocker. Preserve every fail/skip/unrun case and isolation receipt. Do not rerun unrelated heavy tests after a clean result without a new reason.

Useful focused reruns:

```powershell
$env:HYBRID_WORKSPACE_PROJECT='C:\a\Programming\cloudflare\has-acceptance-session-20261110\output\owner-review\Avatar.has'
python tests/verify_workspace_nested.py
python tests/verify_workspace_docking.py
python tests/verify_workspace_resize.py
$env:HYBRID_FAN_PROJECT='C:\a\Programming\cloudflare\has-acceptance-session-20261110\output\fan-native-probe\input'
python tests/verify_fan_flutter.py
Remove-Item Env:HYBRID_FAN_PROJECT
python tests/verify_fan_flutter.py
python tests/verify_fan_motion.py
python tests/verify_orbit_navigation.py --native-project output/camera-input/native-miku.has
python tools/check_completion.py
```

The camera native wrapper requires actual Miku (>100 bones); Avatar has 91 and intentionally fails that fixture guard. Recreate the Miku packed fixture from the normal app's current 126-bone MMD project if needed; do not lower the guard.

## 6. Remaining required acceptance — actual people/devices/environment

The ledger remains **55/62 acceptance verified, 52/54 implementation groups implemented**. C/D/F stay closed. Seven open IDs are IMPORT-02, IMPORT-03, ACCEPT-A, ACCEPT-B, ACCEPT-E, ACCEPT-TABLET and ACCEPT-INSTALL.

Use `docs/windows_acceptance_followup.md` for exact exercises:

- **Native appearance (IMPORT-02/03 + ACCEPT-B):** real original-versus-imported supported appearance/posing comparison. Exact self-replay pixels are not artist approval.
- **Novice A:** a genuinely new user, timed eight-step VRM/pose/save/reopen/export exercise, plus independent environment/camera/drawing/sound story. Record elapsed time, help, real Explorer drop and confusion.
- **Learner E:** Basic practice with a genuine 10–30 second stuck interval, quiet hint, Previous, Continue/Start Fresh and completion. Record real assistance/clarity.
- **Tablet/audio:** actual tablet/pen, driver/configuration, GPU/refresh/audio output, light/heavy pressure/eraser/comfort, measured input-to-visible latency and actual listening in preview/export after seek. Synthetic packets/PCM analysis do not close this.
- **Clean offline Windows:** approved clean Windows 10/11 PC/VM with documented prerequisites, networking disconnected, original import, HAS save/reopen, playable MP4 and missing-tool diagnostics. This configured development PC is not a clean setup. New installation/replacement/deployment still needs separate authorization.

## 7. Test evidence and protected retention

Latest compact evidence:

- `docs/benchmarks/nested_docks_fan_flutter_2026-11-10.json`
- `docs/benchmarks/camera_input_refinement_2026-11-10.json`
- `docs/benchmarks/true_desktop_scale_2026-11-10.json`
- `docs/benchmarks/workspace_docking_2026-11-10.json`
- `docs/benchmarks/native_fixture_rebuild_2026-11-10.json`
- `docs/benchmarks/windows_acceptance_resume_2026-11-10.json`

New final scoped passes include native15 + original15 flutter checks; fan49 including native VRM0/1, Record/HAS/48-frame H264; nested13+5; v1/v2 migration18+4; native resize31. Timeline42+35+48+47 and camera52+2 pass with the documented scope before final isolated gain/drop-hit refinements. Thirteen relevant private receipts validate isolation/cleanup. Full aggregate and latest human review remain unpassed. Preserve intermediate failed measurements; initial prototypes had compile/test-helper errors and a too-small default gust on the original fixture, all requiring clean reruns.

**Do not delete this retained checkout yet:**

`C:\a\Programming\cloudflare\has-acceptance-session-20261110`

It contains pending private deliverables/reproduction input, especially:

- `output\owner-review` (projects, runnable separate source, backups).
- **`output\owner-review\Studio\output\recovery`** (owner live recovery, not just the roaming profile).
- `output\fan-native-probe\input` (owned read-only-staged actual fan/pose reproduction).
- Native aggregate preparation fixtures and the exact staged KRA.

Original owner inputs, `C:\a\Programming\HAS`, Downloads archives, `C:\a\dump`, `C:\a\tools`, Steam content, normal installed Studio and shared runtimes are protected. Private art must not be uploaded. Current approved disposable SourceIO is under this session's `output\dependencies`; exact pinned revision/archive hash are recorded in prior receipts and `dependencies.json`.

Earlier verified cleanup removed 17 superseded test folders (123,881,173 bytes); its exact record is committed. Do not run broad cleanup/reset on shutdown. Retain private deliverables until a safe backup/owner decision exists. At eventual assignment end: commit/push evidence, verify remote, then remove only finished session-owned disposable paths and the checkout when no pending/private unbacked deliverable remains.

For each next completed increment: update source/tests/compact findings, preserve stable IDs and optional/OPEN distinctions, append history, push without force, verify remote, then clean exact finished disposable outputs. Do not mark the goal complete merely because this shutdown handoff is saved.


## Later cloud increment: Bikini Reimu missing helpers

The owner subsequently requested the missing-rig issue specifically. Hair & clothes now opens the existing reviewed weighted-helper setup for chainless skinned models, with actual hair-ribbon generation/fan/Record/cold-HAS/movie evidence. Fetch the latest main before resuming Windows work. See docs/benchmarks/reimu_missing_helpers_2026-11-10.json and docs/secondary_motion.md. This does not close remaining human/device or full-aggregate gates, nor imply full automatic hair/cloth rigging.
