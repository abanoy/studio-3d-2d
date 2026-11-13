# HAS completion checklist

The exact active cloud goal is kept in [complete-has.md](goals/complete-has.md). The machine-readable ledger is [completion_checklist.json](completion_checklist.json). This is a finite engineering decomposition of the two governing documents, not a claim of product completion.

Baseline: `daa063c645182ba9af6d70fc4a87142bb2cfb727`; 2026-11-06. The addendum governs conflicts. Later established hold-Alt/MMB/auto-key choices remain resolved.

There are 54 required capability groups and 8 required acceptance gates. Optional/conditional refinements and unresolved decisions are recorded separately. The JSON source-section and acceptance-scenario indexes provide the reverse mapping to both documents.

## Reading the statuses

`implemented` describes code coverage. `partial` and `missing` identify engineering work. `scoped_evidence` cites documented profile-specific tests; `historical_only` needs current closure. Neither means these tests were executed during this checklist audit. Whole-item acceptance closes only after its condition and supporting evidence have been audited.

Recorded reports can contain narrower passes alongside native/device skips. Do not infer native fidelity, physical comfort or clean Windows readiness from procedural cloud tests. The earlier informal 70% estimate is not a measurement against this ledger.

## Next required work

- **P1 · IMPORT-02** — Native inputs are now available and the combined Windows supported-profile route passes. Remaining external prerequisite: artist/source-appearance comparison against the actual native originals using docs/windows_acceptance_followup.md. Roadmap formats/full native shader-simulator reproduction remain optional or explicit unsupported limits; no known independent software defect is being handed off.
- **P1 · IMPORT-03** — Native dependencies, original preservation, bounded materials/props/lightmaps and exact portable cold replay now have Windows evidence. Obtain actual source-appearance/artist comparison for supported geometry/material/rig behavior. Preserve the explicitly reported partial lightmap/native-shader/physics limits; do not infer original visual fidelity solely from self-replay hashes.
- **P2 · ACCEPT-A** — Windows native21+6 software and core drawing/audio checks now pass. A real novice still must perform the eight-step timed exercise, actual Explorer drop/input and original independent drawing/sound workflow; record time, assistance, confusing controls and audible synchronization. Automation is not novice evidence.
- **P2 · ACCEPT-B** — The combined Windows native software route now passes19+5checks, cold exact Lit/Unshaded replay and actual MP4 with all five original street atlases. Actual artist comparison to supported original source appearance remains required. The automated overlapping large-environment fixture is not a composed or approved artistic scene.
- **P2 · ACCEPT-E** — Windows software course/first-movie cases now pass. A real learner still needs to observe grading, clarity, a genuine10-30second stuck hint, full Previous/Continue-Fresh and optional normal Save. Record actual observations using docs/windows_acceptance_followup.md.
- **P2 · ACCEPT-TABLET** — Actual target tablet/driver/GPU1080p latency/pressure/comfort and audible sync observation; use the exact exercise in docs/windows_acceptance_followup.md.
- **P2 · ACCEPT-INSTALL** — Provide an approved clean supported Windows10/11 offline setup with documented prerequisites; do not replace owner tools or call this configured PC a clean installation.

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
| IMPORT-02 | Native ecosystem coverage | partial / external_required · [report](native_test_inputs.md) | Source model/map containers, MMD model/motion/pose and VRM profiles have documented supported features, safe adapters and representative native acceptance evidence. |
| IMPORT-03 | Native fidelity and dependency reporting | partial / external_required · [report](source_import.md) | Imported data uses the canonical HAS representation and cached preparations. For each supported profile verify geometry, materials, hierarchy, rig/morph/animation and supported physics/lightmaps; unsupported properties get actionable diagnostics. |
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
| TIME-01 | One rational frame domain | implemented / verified · [report](project_timing.md) | Camera, poses, drawings, media and sound use integer frames and rational rates; seek/preview/export agree and timing edits protect existing content. |
| TIME-02 | Collapsed tracks and animated subtracks | implemented / verified · [report](motion_animation.md) | Objects begin collapsed, expansion shows animated parts, and selecting parts focuses their channels without exposing inactive rig clutter by default. |
| TIME-03 | Structural clip and drawing edits | implemented / verified · [report](drawing_clipboard.md) | Move/cut/copy/paste/split retain relative animation or independent cel pixels and have correct Undo; frame3000-to0 is supported. |
| TIME-04 | Timeline navigation and waveforms | implemented / verified · [report](sparse_audio.md) | Zoom/pan/seek share a ruler and frame mapping, labels stay fixed, scroll-to-playhead works and sound waveforms remain aligned. |
| VIS-01 | Presence, persistent visibility and gaps | implemented / verified · [report](visibility.md) | Late introduction is absent beforehand; later clips do not override an explicit OFF; parent visibility, held/bridged gaps and global300ms/zero fades remain deterministic. |
| DRAW-01 | Independent RGBA layers | implemented / verified · [report](drawing_layers.md) | Rough/Ink/Flats/Effects, order/visibility/opacity and painting remain independent from the world/camera and reproduce after saving and export. |
| DRAW-02 | Editable held cels | implemented / verified · [report](drawing_clipboard.md) | Blank/copy/delete/move/resize/split exposures obey end-exclusive boundaries and preserve independent editable pixels, Undo and persistence. |
| DRAW-03 | Brush, eraser and pressure | implemented / verified · [report](brush_pressure.md) | Output-coordinate strokes, opacity, erasing and supported pressure events remain correct under zoom/pan and Undo. |
| DRAW-04 | Safe fill and line-edge handling | implemented / verified · [report](fill_connections.md) | Iterative fill supports tolerance, connectivity, visible-ink sampling, gap preview and border growth; application is undoable and never edits invisible peers or the scene. |
| DRAW-05 | Palette and color sampling | implemented / verified · [report](project_palette.md) | The artist can keep/select project colors and sample the intended drawing/composite without modifying reference media. |
| DRAW-06 | Onion skin and comparison guides | implemented / verified · [report](onion_skin.md) | Previous/next drawings can be compared with editor-only ghosts; guides never leak into stored art or final output. |
| MEM-01 | Bounded usable drawing history | implemented / verified · [report](drawing_history.md) | Meaningful pixel/cel edits have measured bounded useful Undo/Redo without full-frame snapshots for every stroke or resetting independent live physics. |
| MEM-02 | Cold-cel storage and larger projects | implemented / verified · [report](cel_raster_reuse.md) | Cold unique drawings can be compressed/lazily loaded with measured bounded active/history caches, source integrity and reliable large-project seek/save/export. |
| AUDIO-01 | Sound import and editing | implemented / verified · [report](multiple_audio.md) | WAV and supported MP3/Ogg clips have independent timing, trim/gain/fades/mute/solo and survive packed/linked saves without source mutation. |
| AUDIO-02 | Preview clock and exact audio export | implemented / verified · [report](sparse_audio.md) | Playback uses the shared time authority and exported mixed sound has verified offsets and duration at rational rates, including nested sound without duplication and silent projects. |
| PHYS-01 | Live physics, freeze and reset | implemented / verified · [report](physics_recording.md) | Compatible bodies default to enabled physics when supported, simulate/grab/throw, freeze in the current pose when disabled and offer reset; simulation alone authors no take. |
| PHYS-02 | Explicit Local and World capture | implemented / verified · [report](physics_recording.md) | Visible explicit recording captures only selected Local bodies or all relevant World bodies; committed motion reproduces in seek/save/export and cancellation is safe. |
| LIGHT-01 | Unshaded and lit presentation | implemented / verified · [report](tutorials.md) | Unshaded is usable for posing; Lit uses supported scene lighting and retained compatible map lighting, with safe navigation and persisted output settings. |
| SEQ-01 | Editable nested sequence assets | implemented / verified · [report](editable_sequences.md) | Shared editable child scenes support local/parent mapping, offset/loop/placement/opacity, recursive audio and cache invalidation; cycles are rejected and parents update. |
| COMP-01 | Alpha media and chroma compositing | implemented / verified · [report](video_import.md) | Bounded imported alpha/Krita/video artwork becomes editable transparent holds; chroma tolerance/softness/spill and originals are preserved through preview/save/export. |
| COMP-02 | Placed overlays and simple2D effects | implemented / verified · [report](sequence_shadows.md) | Multiple editable character/clip overlays support keyed transform/opacity placement and a simple2D shadow or glow without modifying the background. |
| STORE-01 | Portable HAS and optional linked assets | implemented / verified · [report](cloud_source_recovery.md) | Default packed HAS retains editable world/rig/camera/cels/audio/settings and reopens with sources unavailable; linked saves offer actionable missing-file location. |
| STORE-02 | Independent native model/map sharing | implemented / verified · [report](requirements_cloud_2026-11-05.md) | An individual native model or map can be packaged, imported and reused independently with dependencies/provenance preserved, without external-format exporting. |
| STORE-03 | Project content versus personal preferences | implemented / verified · [report](keyboard_shortcuts.md) | Project content/settings reproduce the scene while personal input/UI preferences stay personal; loading introduces no tentative disruptive settings prompt. |
| STORE-04 | Validated atomic save and fault safety | implemented / verified · [report](cel_file_paths.md) | Corrupt/unsafe/missing assets and failed/interrupted writes cannot replace the sole valid project or escape its folder; backup/readback/integrity faults are exercised. |
| REC-01 | Quiet time/action autosave | implemented / verified · [report](recovery_schedule.md) | Default minute or meaningful-action protection waits for safe interaction state, retains failed work for retry, and protects active lesson-only changes without dirtying saved scene content. |
| REC-02 | Bounded journal and Advanced history | implemented / verified · [report](recovery_history.md) | Bounded recoverable states expose timestamps and low-resolution viewport thumbnails in Advanced without endless full-project copies. |
| REC-03 | Automatic newest-valid recovery | implemented / verified · [report](startup_recovery.md) | An actual abruptly terminated session restores the newest completely valid state, falls back through corrupt entries and never overwrites the last manual HAS. |
| COURSE-01 | Basic and Advanced topic browser | implemented / verified · [report](tutorials.md) | Offline bundled original HAS practices provide a logical Basic route and accessible Advanced sections/subsections with topic entry points. |
| COURSE-02 | Interactive teacher and quiet hints | implemented / verified · [report](tutorials.md) | Real scene-state grading advances completed tasks, rejects unrelated actions and quietly offers a useful visual hint after10–30seconds without taking over. |
| COURSE-03 | Whole-scene Previous and resumed practice | implemented / verified · [report](lesson_recovery.md) | Previous restores the complete step scene; Continue/Fresh preserve separate sessions and observations; optional personal Save and crash reattachment keep newer protected practice state. |
| OUTPUT-01 | Simple MP4 and image output | implemented / verified · [report](png_export.md) | Default output is playable H264/AAC1080p24 beside the saved HAS, with exact frame count, silent-video support and complete/transparent PNG alternatives. |
| OUTPUT-02 | Configurable output dimensions and timing | implemented / verified · [report](project_timing.md) | The user can change supported resolution/rational rate/duration with accurate media alignment and documented canvas/output behavior, while default1080p24 remains effortless. |
| OUTPUT-03 | Export progress, cancellation and recovery | implemented / verified · [report](export_failures.md) | Missing codecs/tools, failures and cancellation report truthfully, preserve recoverable frames/logs and never claim success or overwrite project assets. |
| NOTICES-01 | Notices and honest provenance | implemented / verified · [report](../THIRD_PARTY_NOTICES.md) | Dependency notices and source attribution remain available, unknown asset rights are not fabricated, and no downloaded art or unauthorized distribution is introduced. |

Detailed remaining work, implementation paths and source-section references are in the JSON ledger. A group is not closed merely because its menu exists or one fixture passes.

## Required external acceptance

| ID | Acceptance | Prerequisites |
|---|---|---|
| ACCEPT-A | A novice completes import/pose/camera/drawing/sound/save/reopen/MP4 in Simple using actual target controls. | B-ARTIST |
| ACCEPT-B | Approved Source map with available dependencies, VRM character and PMX prop coexist, pose and reopen portably with verified supported fidelity and truthful diagnostics. | B-NATIVE |
| ACCEPT-C | The complete decided scenarioC passes routed interaction and final rendering, including late presence, relative clip moves, split gaps, persistent OFF, hidden selection and adjacent cuts. |  |
| ACCEPT-D | A compatible ragdoll freezes/resets and explicit Local/World captures reproduce selected/impacted-body motion through preview, persistence and MP4, with measured ordinary-take responsiveness. |  |
| ACCEPT-E | A learner uses real practice assets, receives correct grading/quiet hints, restores whole Previous states and resumes/freshens/saves without losing practice. | B-ARTIST |
| ACCEPT-F | Abrupt native target-platform exits recover newest valid state/older fallback with timestamps/thumbnails and unchanged manual HAS; interrupted and storage-failure cases are exercised. |  |
| ACCEPT-TABLET | Record actual1080p stroke/pressure latency and comfort with the owner target tablet/driver/GPU, plus audible synchronization, without claiming universal hardware support. | B-TABLET, B-WINDOWS, B-ARTIST |
| ACCEPT-INSTALL | A clean supported Windows machine installs/launches offline, imports an original sample, saves/reopens and exports a playable movie with detected compatible encoder. | B-WINDOWS |

### Exact missing prerequisites

- **B-WINDOWS**: An approved clean supported Windows10/11 offline PC/VM setup, distinct from the now-tested configured development PC. Independent work: Fresh configured-Windows full default at9897f86 passes all36core groups, every laterregisteredwrapper,21finalmoviechecks andbothdecoded1.0secondaudioonsets, with947functionalhashes/HEADexact. Exact19-layerhecatia is suppliedandpasses32writer+5cold; notmissing. Thisisnotcleanofflineinstallationorhuman/deviceacceptance. Historicalchecksum-boundreaderbackups remainunavailable byownerreport; do notsubstitute orrequestagain. Evidence:docs/benchmarks/windows_canonical_full_2026-11-13.json. Latest integration1236fullfailedatVRM0linkedSave childcreation afterbothwindmatricespass;post-ordering scopedbackground/body checks pass. That1236failureprecededthefresh12071fecompletefullpass; see docs/benchmarks/windows_snapshot_launch_order_2026-11-13.json. Fresh post-save-order default at12071fe passes36core,154resultentries,21movies,both1.0saudioonsets and968sourcehashes/HEADexact; new external private review passes129replays with8closedjobs andprotectedpackages/runtimes unchanged. See docs/benchmarks/windows_canonical_post_save_order_2026-11-13.json. Configured-PC evidence does not certify clean offline installation.
- **B-NATIVE**: Actual artist/source-appearance comparison against approved native originals for supported geometry/material/rig/lighting behavior. Native BSPs, installed Steam dependencies, VRMs and all five street atlas PNGs are now available and have scoped Windows software evidence. Independent work: Combined native Windows19writer+5cold checks, real MP4,1of1native prop,12textures,two lights,29bounded baked faces and exact portable Lit/Unshaded replay pass. Transit CRC/index and5actual named-refusal/preservation checks pass. No missing-map/atlas or untested-Windows blanket blocker remains; unsupported bounds and self-replay versus original-fidelity distinction are explicit.
- **B-TABLET**: Owner target physical tablet/input driver, GPU and audio output device with actual measured sessions. Independent work: ConfiguredWindows software nowchecks syntheticpressure/coordinate mapping, independent raster references anddecodedWASAPI-exportaudioalignment in thefull default. Actualphysicaltablet latency/comfort andaudibledevice synchronization remainunobserved.
- **B-ARTIST**: Owner/novice observation and artistic feedback on an actual completed short animation. Independent work: Windows software routes and media have scoped passes; actual novice/learner/artistic observations remain pending. Owner explicitly requests no further review interruptions unless they grant otherwise (2026-11-11). Keep docs/windows_acceptance_followup.md ready without repeated prompts. Automated timing and scripted events are not substitutes.

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

Independent native packaging is resolved within the existing HAS container. The other open details do not suspend work on the already decided core behavior. No new extension, third-party exporter, mandatory AI, public release or settings prompt is authorized by this checklist.

## Scoring and closure

Implementation coverage = implemented required_implementation groups / all54required implementation groups. Acceptance closure = verified required groups / all62required implementation+verification groups. No partial credit; external blockers stay in the acceptance denominator. Exclude optional/decision/control records. Equal checklist groups are not effort, reliability or release-readiness weights; do not combine the two scores.

Audited implementation coverage: **96.30% (52/54 groups)**. Formal acceptance closure: **88.71% (55/62 groups)**. See the [per-item source/evidence audit](benchmarks/completion_baseline_audit_2026-11-07.json). These are separate checklist counts, not an overall release-readiness or remaining-time estimate. Keep stable IDs; split or add requirements only through an explicit documented ledger revision. Blocked required items remain incomplete and in the acceptance denominator.

To close an item, record `acceptance_status: verified`, `verification: verified` and a `test_result` reference with its commit and exact scope. Preserve failed/skipped/unrun and historical evidence. Keep a small curated closure receipt in the repository rather than committing incidental render/cache outputs. Do not close a broad requirement using a narrower procedural test. This tool checks ledger structure and file references; it does not certify the prose fully implements the source requirements.

Validate and regenerate this overview with:

```sh
python tools/check_completion.py --write
python tools/check_completion.py
```

An incremental commit is not full completion. Continue with the next actionable required item. Finish only when required items are verified or explicitly externally blocked and all independent work is complete. Full product completion still requires all required acceptance conditions to pass.
