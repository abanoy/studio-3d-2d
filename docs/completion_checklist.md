# HAS completion checklist

The exact active cloud goal is kept in [complete-has.md](goals/complete-has.md). The machine-readable ledger is [completion_checklist.json](completion_checklist.json). This is a finite engineering decomposition of the two governing documents, not a claim of product completion.

Baseline: `daa063c645182ba9af6d70fc4a87142bb2cfb727`; 2026-11-06. The addendum governs conflicts. Later established hold-Alt/MMB/auto-key choices remain resolved.

There are 54 required capability groups and 8 required acceptance gates. Optional/conditional refinements and unresolved decisions are recorded separately. The JSON source-section and acceptance-scenario indexes provide the reverse mapping to both documents.

## Reading the statuses

`implemented` describes code coverage. `partial` and `missing` identify engineering work. `scoped_evidence` cites documented profile-specific tests; `historical_only` needs current closure. Neither means these tests were executed during this checklist audit. Whole-item acceptance closes only after its condition and supporting evidence have been audited.

Recorded reports can contain narrower passes alongside native/device skips. Do not infer native fidelity, physical comfort or clean Windows readiness from procedural cloud tests. The earlier informal 70% estimate is not a measurement against this ledger.

## Next required work

- **P2 · ACCEPT-C** — Complete seven-step cloud case is recorded; finalWindows target gate remains. Do not repeat completed cloud case while independent engineering remains.
- **P2 · ACCEPT-D** — Complete mechanical cloud case is recorded; finalWindows target gate remains. Do not repeat completed cloud case while independent engineering remains.
- **P1 · REC-01** — Cold raster/history and background HAS/recovery paths, proven-owned blob retirement and shared512MiB quota reservations have scoped evidence. Prioritize remaining native/required feature gaps. Whole-process/GPU/device measurement and arbitrary orphan cleanup remain separate; do not repeat passed bounded worker/quota checks without a new change.
- **P1 · MEM-02** — Cold raster/history and background HAS/recovery paths, proven-owned blob retirement and shared512MiB quota reservations have scoped evidence. Prioritize remaining native/required feature gaps. Whole-process/GPU/device measurement and arbitrary orphan cleanup remain separate; do not repeat passed bounded worker/quota checks without a new change.
- **P1 · MEM-01** — Cold raster/history and background HAS/recovery paths, proven-owned blob retirement and shared512MiB quota reservations have scoped evidence. Prioritize remaining native/required feature gaps. Whole-process/GPU/device measurement and arbitrary orphan cleanup remain separate; do not repeat passed bounded worker/quota checks without a new change.
- **P1 · STORE-04** — Supporting POSIX sync and rollback payload validity are verified in scoped fixtures. Retain explicit native Windows and physical power-loss gates; audit the next independently actionable requirement.
- **P2 · MOTION-03** — Required bounded reusable path/clip and reversible locomotion workflow verified by current committed receipts. Native fidelity, unsupported moving parents and artist observations remain separate; general terrain and multi-view inference are not additional decided mandatory gates.
- **P2 · IMPORT-03** — Define per-profile native fidelity acceptance and use approved fixtures when available; report unsupported capabilities honestly.

Prioritize these required gaps over optional UI/effect polishing. Resolve true owner decisions when needed, continue independent work while waiting, and do not declare the whole goal blocked merely because one gate is external.

## Required implementation

| ID | Capability | Implementation / evidence | Acceptance condition |
|---|---|---|---|
| ENV-01 | Pinned offline development workflow | implemented / verified · [report](cloud_source_recovery.md) | A clean supported setup launches pinned Godot and detects Python/FFmpeg without a cloud application dependency. |
| UI-01 | Simple and Advanced share one document | implemented / verified · [report](voice_addendum_audit.md) | Switching UI detail preserves scene, timeline, camera, effective parameters and output; common tasks remain usable in Simple. |
| UI-02 | Home, recent projects and tutorials | implemented / verified · [report](home.md) | Home opens New, Tutorials and real recent projects with available thumbnails and actionable missing-file feedback. |
| WORLD-01 | Empty world and editor grid | implemented / verified · [report](voice_addendum_audit.md) | New starts black with a fading white floor grid, no selected object, bottom timeline and hierarchy; the grid is excluded from final output. |
| NAV-01 | Navigation, focus and shortcut routing | implemented / verified · [report](keyboard_shortcuts.md) | Fly controls, stepping, Space and remapped shortcuts respect text focus/drawing mode and release capture on Escape/focus loss; alternate navigation stays optional. |
| IMPORT-01 | Common-format import and immutable sources | implemented / verified · [report](common_import.md) | Supported common files import into editable HAS world objects with dependency errors; drop uses frame0 and timeline import uses its chosen frame without modifying originals. |
| IMPORT-02 | Native ecosystem coverage | partial / incomplete · [report](native_test_inputs.md) | Source model/map containers, MMD model/motion/pose and VRM profiles have documented supported features, safe adapters and representative native acceptance evidence. |
| IMPORT-03 | Native fidelity and dependency reporting | partial / incomplete · [report](source_import.md) | Imported data uses the canonical HAS representation and cached preparations. For each supported profile verify geometry, materials, hierarchy, rig/morph/animation and supported physics/lightmaps; unsupported properties get actionable diagnostics. |
| IMPORT-04 | Visible spawn and bounded grounding | implemented / verified · [report](height_import.md) | Models spawn visibly near the captured view, attempt support/overlap avoidance with bounded candidates, and remain findable on fallback; maps are not treated as tiny humanoids. |
| WORLD-02 | Multiple maps, parenting and hierarchy | implemented / verified · [report](architecture.md) | Several maps/models/groups coexist, roots move whole maps, hierarchy finds distant objects, and parenting/saving preserve transforms. |
| POSE-01 | Selection, bones and hidden-object editing | implemented / verified · [report](visibility.md) | Selection shows an editor-only green outline, accessible bones and decided hold-Alt reveal; hidden-parent selection remains editable without changing output visibility. |
| POSE-02 | Direct posing and automatic manual keys | implemented / verified · [report](body_pose_library.md) | Root and bone edits key the intended object/part at the exact playhead, Undo restores them, and unrigged assets degrade gracefully. |
| POSE-03 | Rig-aware IK and foot constraints | implemented / verified · [report](foot_contacts.md) | Supported hand/limb IK and planted-foot/root edits preserve reachable targets; unusual or missing rigs refuse safely. |
| POSE-04 | Reference-only posed characters | implemented / verified · [report](body_pose_library.md) | Poseable references can be shown/hidden independently for preview versus final render, with saved pose interpolation and usable three-quarter inspection. |
| POSE-05 | Reusable body poses | implemented / verified · [report](body_pose_library.md) | Named thumbnail poses support use, rename, duplicate, removal and compatible native pose sharing without overwriting source rigs. |
| MOTION-01 | Sparse interpolation and per-channel editing | implemented / verified · [report](motion_animation.md) | Hold/linear/ease and supported Advanced curves preserve authored endpoints, independent parameters and camera cuts during seek/save/export. |
| MOTION-02 | Reversible Motion Assist | implemented / verified · [report](motion_assistance.md) | A simple assist control offers editable, disableable corrections without silently replacing authored poses; supported parts/helpers have explicit bounds. |
| MOTION-03 | Reusable paths with locomotion assistance | implemented / verified · [report](movement_path_presets.md) | Reusable editable paths/clips can drive a character, with a visible reversible locomotion suggestion and correction workflow. |
| CAMERA-01 | Shot camera authoring and cuts | implemented / verified · [report](numeric_camera.md) | Temporary navigation is separate from explicit shot keys; numeric transforms/FOV, interpolation and adjacent-frame cuts persist and render at exact frames. |
| TIME-01 | One rational frame domain | implemented / scoped_evidence · [report](project_timing.md) | Camera, poses, drawings, media and sound use integer frames and rational rates; seek/preview/export agree and timing edits protect existing content. |
| TIME-02 | Collapsed tracks and animated subtracks | implemented / historical_only · [report](motion_animation.md) | Objects begin collapsed, expansion shows animated parts, and selecting parts focuses their channels without exposing inactive rig clutter by default. |
| TIME-03 | Structural clip and drawing edits | implemented / scoped_evidence · [report](drawing_clipboard.md) | Move/cut/copy/paste/split retain relative animation or independent cel pixels and have correct Undo; frame3000-to0 is supported. |
| TIME-04 | Timeline navigation and waveforms | implemented / verified · [report](sparse_audio.md) | Zoom/pan/seek share a ruler and frame mapping, labels stay fixed, scroll-to-playhead works and sound waveforms remain aligned. |
| VIS-01 | Presence, persistent visibility and gaps | implemented / verified · [report](visibility.md) | Late introduction is absent beforehand; later clips do not override an explicit OFF; parent visibility, held/bridged gaps and global300ms/zero fades remain deterministic. |
| DRAW-01 | Independent RGBA layers | implemented / verified · [report](drawing_layers.md) | Rough/Ink/Flats/Effects, order/visibility/opacity and painting remain independent from the world/camera and reproduce after saving and export. |
| DRAW-02 | Editable held cels | implemented / verified · [report](drawing_clipboard.md) | Blank/copy/delete/move/resize/split exposures obey end-exclusive boundaries and preserve independent editable pixels, Undo and persistence. |
| DRAW-03 | Brush, eraser and pressure | implemented / verified · [report](brush_pressure.md) | Output-coordinate strokes, opacity, erasing and supported pressure events remain correct under zoom/pan and Undo. |
| DRAW-04 | Safe fill and line-edge handling | implemented / verified · [report](fill_connections.md) | Iterative fill supports tolerance, connectivity, visible-ink sampling, gap preview and border growth; application is undoable and never edits invisible peers or the scene. |
| DRAW-05 | Palette and color sampling | implemented / verified · [report](project_palette.md) | The artist can keep/select project colors and sample the intended drawing/composite without modifying reference media. |
| DRAW-06 | Onion skin and comparison guides | implemented / verified · [report](onion_skin.md) | Previous/next drawings can be compared with editor-only ghosts; guides never leak into stored art or final output. |
| MEM-01 | Bounded usable drawing history | implemented / verified · [report](drawing_history.md) | Meaningful pixel/cel edits have measured bounded useful Undo/Redo without full-frame snapshots for every stroke or resetting independent live physics. |
| MEM-02 | Cold-cel storage and larger projects | implemented / scoped_evidence · [report](cel_raster_reuse.md) | Cold unique drawings can be compressed/lazily loaded with measured bounded active/history caches, source integrity and reliable large-project seek/save/export. |
| AUDIO-01 | Sound import and editing | implemented / verified · [report](multiple_audio.md) | WAV and supported MP3/Ogg clips have independent timing, trim/gain/fades/mute/solo and survive packed/linked saves without source mutation. |
| AUDIO-02 | Preview clock and exact audio export | implemented / verified · [report](sparse_audio.md) | Playback uses the shared time authority and exported mixed sound has verified offsets and duration at rational rates, including nested sound without duplication and silent projects. |
| PHYS-01 | Live physics, freeze and reset | implemented / verified · [report](physics_recording.md) | Compatible bodies default to enabled physics when supported, simulate/grab/throw, freeze in the current pose when disabled and offer reset; simulation alone authors no take. |
| PHYS-02 | Explicit Local and World capture | implemented / verified · [report](physics_recording.md) | Visible explicit recording captures only selected Local bodies or all relevant World bodies; committed motion reproduces in seek/save/export and cancellation is safe. |
| LIGHT-01 | Unshaded and lit presentation | implemented / historical_only · [report](tutorials.md) | Unshaded is usable for posing; Lit uses supported scene lighting and retained compatible map lighting, with safe navigation and persisted output settings. |
| SEQ-01 | Editable nested sequence assets | implemented / verified · [report](editable_sequences.md) | Shared editable child scenes support local/parent mapping, offset/loop/placement/opacity, recursive audio and cache invalidation; cycles are rejected and parents update. |
| COMP-01 | Alpha media and chroma compositing | implemented / scoped_evidence · [report](video_import.md) | Bounded imported alpha/Krita/video artwork becomes editable transparent holds; chroma tolerance/softness/spill and originals are preserved through preview/save/export. |
| COMP-02 | Placed overlays and simple2D effects | implemented / verified · [report](sequence_shadows.md) | Multiple editable character/clip overlays support keyed transform/opacity placement and a simple2D shadow or glow without modifying the background. |
| STORE-01 | Portable HAS and optional linked assets | implemented / scoped_evidence · [report](cloud_source_recovery.md) | Default packed HAS retains editable world/rig/camera/cels/audio/settings and reopens with sources unavailable; linked saves offer actionable missing-file location. |
| STORE-02 | Independent native model/map sharing | implemented / verified · [report](requirements_cloud_2026-11-05.md) | An individual native model or map can be packaged, imported and reused independently with dependencies/provenance preserved, without external-format exporting. |
| STORE-03 | Project content versus personal preferences | implemented / verified · [report](keyboard_shortcuts.md) | Project content/settings reproduce the scene while personal input/UI preferences stay personal; loading introduces no tentative disruptive settings prompt. |
| STORE-04 | Validated atomic save and fault safety | partial / incomplete · [report](cel_file_paths.md) | Corrupt/unsafe/missing assets and failed/interrupted writes cannot replace the sole valid project or escape its folder; backup/readback/integrity faults are exercised. |
| REC-01 | Quiet time/action autosave | implemented / scoped_evidence · [report](recovery_schedule.md) | Default minute or meaningful-action protection waits for safe interaction state, retains failed work for retry, and protects active lesson-only changes without dirtying saved scene content. |
| REC-02 | Bounded journal and Advanced history | implemented / scoped_evidence · [report](recovery_history.md) | Bounded recoverable states expose timestamps and low-resolution viewport thumbnails in Advanced without endless full-project copies. |
| REC-03 | Automatic newest-valid recovery | implemented / scoped_evidence · [report](startup_recovery.md) | An actual abruptly terminated session restores the newest completely valid state, falls back through corrupt entries and never overwrites the last manual HAS. |
| COURSE-01 | Basic and Advanced topic browser | implemented / verified · [report](tutorials.md) | Offline bundled original HAS practices provide a logical Basic route and accessible Advanced sections/subsections with topic entry points. |
| COURSE-02 | Interactive teacher and quiet hints | implemented / scoped_evidence · [report](tutorials.md) | Real scene-state grading advances completed tasks, rejects unrelated actions and quietly offers a useful visual hint after10–30seconds without taking over. |
| COURSE-03 | Whole-scene Previous and resumed practice | implemented / scoped_evidence · [report](lesson_recovery.md) | Previous restores the complete step scene; Continue/Fresh preserve separate sessions and observations; optional personal Save and crash reattachment keep newer protected practice state. |
| OUTPUT-01 | Simple MP4 and image output | implemented / scoped_evidence · [report](png_export.md) | Default output is playable H264/AAC1080p24 beside the saved HAS, with exact frame count, silent-video support and complete/transparent PNG alternatives. |
| OUTPUT-02 | Configurable output dimensions and timing | implemented / verified · [report](project_timing.md) | The user can change supported resolution/rational rate/duration with accurate media alignment and documented canvas/output behavior, while default1080p24 remains effortless. |
| OUTPUT-03 | Export progress, cancellation and recovery | implemented / scoped_evidence · [report](export_failures.md) | Missing codecs/tools, failures and cancellation report truthfully, preserve recoverable frames/logs and never claim success or overwrite project assets. |
| NOTICES-01 | Notices and honest provenance | implemented / verified · [report](../THIRD_PARTY_NOTICES.md) | Dependency notices and source attribution remain available, unknown asset rights are not fabricated, and no downloaded art or unauthorized distribution is introduced. |

Detailed remaining work, implementation paths and source-section references are in the JSON ledger. A group is not closed merely because its menu exists or one fixture passes.

## Required external acceptance

| ID | Acceptance | Prerequisites |
|---|---|---|
| ACCEPT-A | A novice completes import/pose/camera/drawing/sound/save/reopen/MP4 in Simple using actual target controls. | B-WINDOWS, B-ARTIST |
| ACCEPT-B | Approved Source map with available dependencies, VRM character and PMX prop coexist, pose and reopen portably with verified supported fidelity and truthful diagnostics. | B-NATIVE, B-WINDOWS |
| ACCEPT-C | The complete decided scenarioC passes routed interaction and final rendering, including late presence, relative clip moves, split gaps, persistent OFF, hidden selection and adjacent cuts. | B-WINDOWS |
| ACCEPT-D | A compatible ragdoll freezes/resets and explicit Local/World captures reproduce selected/impacted-body motion through preview, persistence and MP4, with measured ordinary-take responsiveness. | B-WINDOWS |
| ACCEPT-E | A learner uses real practice assets, receives correct grading/quiet hints, restores whole Previous states and resumes/freshens/saves without losing practice. | B-ARTIST, B-WINDOWS |
| ACCEPT-F | Abrupt native target-platform exits recover newest valid state/older fallback with timestamps/thumbnails and unchanged manual HAS; interrupted and storage-failure cases are exercised. | B-WINDOWS |
| ACCEPT-TABLET | Record actual1080p stroke/pressure latency and comfort with the owner target tablet/driver/GPU, plus audible synchronization, without claiming universal hardware support. | B-TABLET, B-WINDOWS, B-ARTIST |
| ACCEPT-INSTALL | A clean supported Windows machine installs/launches offline, imports an original sample, saves/reopens and exports a playable movie with detected compatible encoder. | B-WINDOWS |

### Exact missing prerequisites

- **B-WINDOWS**: A usable approved Windows10/11 execution environment with the pinned engine and compatible encoder/GPU context. Independent work: Portable implementation, procedural GUI/export/recovery tests and owned-directory fault tests remain actionable.
- **B-NATIVE**: SFM fixtures are now owner-approved and available (22archives/82MDLs). Full native app tests still require a recognized cloud-accessible installed SFM/GMod host and compatible full conversion worker. Approved complete BSP/map/prop/lightmap, VRM and MMD model/pose/motion fixtures and dependencies remain needed for their separate profiles. Independent work: SFM metadata/texture decoding, original-hash checks, loose-case fix and78Source unit checks completed. Offline compatible-libc metadata container preserves the host and game preflight. Full app/rig/cloth/render fidelity remains unrun until its host/fixtures are available.
- **B-TABLET**: Owner target physical tablet/input driver, GPU and audio output device with actual measured sessions. Independent work: Synthetic pressure packets, coordinate mapping, deterministic pixels and decoded audio alignment can be tested in cloud.
- **B-ARTIST**: Owner/novice observation and artistic feedback on an actual completed short animation. Independent work: Implement missing required capabilities and run objective automation first.

## Optional and conditional scope

- **O-AI · Optional AI/line-art/painted in-between suggestions** (optional_deferred): Not a prerequisite for ordinary animation. If pursued, opt-in, reversible review/accept/reject, provenance and measured owner need are required.
- **O-DRAW-POLISH · Advanced selection, lasso/painted masks, glow, multiple palettes and proportion tools** (conditional_refinement): Some are already implemented; pursue remaining refinements after stages1–4 acceptance and measured owner pain. Shadow-or-glow is already satisfied by shadow; do not count both as mandatory.
- **O-RENDER · Photorealism/ray tracing/high-end renderer** (preference_open): No compulsory engine rewrite or promised path tracing.
- **O-AUTHOR · Blender-assisted world authoring and possible USD/native-source extensions** (optional_deferred): Do not turn HAS into a modeling tool or require every possible extension.
- **O-CAPTURE · Third collision-following record mode and particular sample compression** (suggested_deferred): Local/World determinism remains required; third mode and exact thinning/delta algorithm are not decided requirements.

Stage5 refinement is conditional on demonstrated stages1–4 and owner pain. Simple shadows already satisfy the Stage4 shadow-or-glow choice; optional glow is not a second mandatory acceptance gate. Native Source/MMD/VRM support is required by the governing addendum even though the earlier MD deferred some importers.

## Unresolved decisions

- **D-PACKAGING · Independent native package contract** (resolved): Owner explicitly chose: Reuse the existing .has container (2026-11-07). Implemented as a validated independent model/map variation of portable HAS.
- **D-CLIPS · Further trim/key ownership, ripple and cross-track semantics** (open): Reconcile exact boundary/key ownership, duplicate/ripple/cross-track behavior before expanding current working clip contracts. These details do not erase decided structural move/split/clipboard requirements.
- **D-PATH · Multi-projection3D path inference** (open): Accuracy, depth inference, additional-view request and correction rules remain undecided. Authored paths and reversible locomotion assistance can proceed independently.
- **D-ASSIST · Assist intensity preference** (preference_test): Test intensity/settling with the owner; preserve exact poses and obvious disable/edit controls.
- **D-UX · Extra per-key fades, load-settings prompt and tutorial Skip** (open): Do not introduce these as mandatory features or disruptive dialogs without a decision.
- **D-LICENSE · Application/public-distribution license** (open): Owner chooses distribution/license terms before publishing; no publishing or native-art redistribution is authorized by this development goal.

Only independent native packaging currently has an explicit requirement-level owner-decision dependency. The other open details do not suspend work on the already decided core behavior. No new extension, third-party exporter, mandatory AI, public release or settings prompt is authorized by this checklist.

## Scoring and closure

Implementation coverage = implemented required_implementation groups / all54required implementation groups. Acceptance closure = verified required groups / all62required implementation+verification groups. No partial credit; external blockers stay in the acceptance denominator. Exclude optional/decision/control records. Equal checklist groups are not effort, reliability or release-readiness weights; do not combine the two scores.

Audited implementation coverage: **94.44% (51/54 groups)**. Formal acceptance closure: **59.68% (37/62 groups)**. See the [per-item source/evidence audit](benchmarks/completion_baseline_audit_2026-11-07.json). These are separate checklist counts, not an overall release-readiness or remaining-time estimate. Keep stable IDs; split or add requirements only through an explicit documented ledger revision. Blocked required items remain incomplete and in the acceptance denominator.

To close an item, record `acceptance_status: verified`, `verification: verified` and a `test_result` reference with its commit and exact scope. Preserve failed/skipped/unrun and historical evidence. Keep a small curated closure receipt in the repository rather than committing incidental render/cache outputs. Do not close a broad requirement using a narrower procedural test. This tool checks ledger structure and file references; it does not certify the prose fully implements the source requirements.

Validate and regenerate this overview with:

```sh
python tools/check_completion.py --write
python tools/check_completion.py
```

An incremental commit is not full completion. Continue with the next actionable required item. Finish only when required items are verified or explicitly externally blocked and all independent work is complete. Full product completion still requires all required acceptance conditions to pass.
