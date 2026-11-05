# Voice addendum implementation audit — 2026-10-29

## Owner-approved normal installation — 2026-11-02 at 1946 EST

The owner explicitly approved applying the tested workspace review copy with a
backup. Normal `C:/a/Programming/cloudflare/prototypes/studio-3d-2d` now contains
that update: Model8 motion feeling, multiple sound clips, deform catalogue/study/
comparison/presets, optional character height/static map sizing, and the four UI
changes. Older Model7 scenes remain readable. The frozen web preview is unchanged.

Exact approved source archive SHA256:
`4f55fa0ae06955bad3a8cf6ccad258186892ee433f5c981b51019720c805425a`. Every replaced source was backed up at
`C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\source-backups\2026-11-02-190733-before-approved-workspace`; new source paths are recorded as previously absent.
No source files were deleted. Projects, original assets, caches and the existing
append-only progress memo were preserved; no open owner window was controlled.

Fresh normal-path verification completed19 groups/21 command invocations with exit0 and
42 accepted private graphical receipts. It covers workspace/UI/layers,
beginner course, comparison, installed Source browser, native contact viewport,
multiple audio, tutorials/recovery history, motion feeling, HAS, native/common
imports, height, map sizing, MMD groups and expression presets. Functional source
hashes remained exact throughout; original assertions and own MP4/AAC checks pass.
Evidence: `C:\a\Programming\cloudflare\prototypes\studio-3d-2d\output\approved-workspace-checks\1793664473316133500` and `output/normal-source-state.json`.
Initial height/preset wrappers lacked their local catalogue references and covered
only their authored cases (height also ran one real raw VRM import). Those initial
reports are retained. A native followup staged verified data-only reference JSON,
ran the catalogue on six native preparations, then reran height on all six and
expression presets on both VRMs. No app code, original input or assertion changed.
Documentation was updated after checks; executable source remains byte-identical
to the approved archive. Earlier full116/audio and10+5 review checks retain their
own scopes; these19 groups are not a new complete full-verifier run.

Restart Studio to load updated files if an older session is still open. Physical
input/tablet feel, artist quality, all native fidelity, clean-PC and power-loss
acceptance remain open. The full MD/addendum goal and remaining product scope are
unfinished; this is a verified local update, not a public release or deployment.


2026-11-02 continuation: [multiple audio clips](multiple_audio.md) uses the same
master clock/native project with independent timing, mute, trim/gain and draggable
sound rows. Packed/linked/recovery/lesson and movie checks cover all clips. Audio
editing remains partial: compressed sources, split/end trim/fades/buses/video/VFX/
nesting and responsiveness work remain. Normal Model7/review copy/web stay separate.

2026-11-02 continuation: [cache-free review candidate](portable_candidate.md)
verifies ordinary Home/New, native Model7/8 Open/edit/Save and synchronized movies
in fresh moved source copies, plus the included beginner course. Normal app/web
remain separate; same-machine relocation does not prove clean-PC/artist acceptance.

The owner supplied the [complete interview addendum](design/HAS_2026-10-29_Voice_Design_Addendum_for_Codex.md)
as the next instruction, then explicitly clarified: **“Addendum overwrites all decisions.”**
That clarification supersedes the addendum's older conflict-approval rule and earlier
incompatible product decisions. The original specification remains an unchanged historical
document. Its core independent 3D → camera → RGBA cels → timeline/audio → MP4 workflow survives.
Items labelled OPEN, SUGGESTED or PREFERENCE/TEST in the addendum retain those distinctions.

Addendum copy SHA256: `85c5628cb51bd8acb3abd66052bd638530e60fd2f71ea550cff773d643a4bbf7`.
Audit baseline: local checkpoint `92991b788`; all 90 tracked component files in the
canonical folder matched that checkpoint before editing (line endings normalized).
Code inspected: app, renderer, model/pose editor, timeline view, HAS save/open, import
coordinator and guides, recovery/storage, existing verification scripts and reports.

## Comparison matrix

“Present/tested” means source exists with recorded Windows test evidence, **not**
that every old suite was rerun for this audit. “Partial” identifies the tested subset.
Current-increment verification is recorded separately below and in progress_memo.md.
“Blocked” is reserved for an actual prerequisite or unsettled choice, not a large backlog.

| Addendum requirement | Status | Actual state / next piece |
|---|---|---|
| §1 Simple and Advanced use the same state | Present/tested | app.gd visibility-only controls, UI23 regression; full novice feature set still incomplete. |
| §1 Simple animation to MP4 | Partial | Import, limb posing, animation pieces, drawing, one WAV, live ragdolls and movie work; full motion capture/tutorial scope remains. |
| §2 Home / New / Tutorials / Recent thumbnails | Partial; see actual run/save status | Home follows automatic recovery, with real New/Open/Return and12 recent successful HAS saves/opens, matching managed thumbnails when available, missing-file feedback and list-only removal. Empty New/free camera remain. Tutorials opens an eleven-task beginner import-to-MP4 path and two focused chapters, using included original assets; advanced course sections remain required. See home.md and tutorials.md. |
| §2 Black empty world, fading white 3D grid, nothing selected | Present/tested | Normal startup/New are black, grid is bounded 3D with distance/subpixel fade, no actor/selection. Grid excluded from final frames and saved GLB. |
| §2 Bottom timeline / vertical scene hierarchy | Partial | Bottom pinned camera ruler plus scrollable per-object/cel/audio rows and functional left World tree; multiple maps/models/groups editable. |
| §2 GMod flight, optional orbit scheme | Partial | Ctrl+LMB look plus WASD/QE, focus/Escape release; orbit/remapping missing. |
| §3 Explorer drop at frame0 / timeline context import at chosen frame | Partial | Native window drop wired, viewport handler tested; right-click timeline/native picker and async chosen presence work. Physical Explorer drag remains unverified; single-file drops only. |
| §3 Visible grounded spawn / bounded overlap search | Partial | UI model imports use captured view, visible surface queries,9candidate overlap search and explicit visible fallback. Actual translated floor/native GMod map tested; physical/transparent/skinned collision semantics and large-scene guarantees remain absent. |
| §3 Multiple maps / actors / group transforms | Partial | Prepared schema4 worlds render/select/edit several maps/models/groups with independent transforms/poses/presence and stable-ID Undo. Normal append imports, empty New, atomic all-object Open/recovery and structural Add/Remove Undo work. |
| §3 Source MDL/BSP/GMA / installed GMod/SFM library | Partial | Tested native imports, dependencies and searchable mounts; shader/lightmap/physics fidelity incomplete. SFM Workshop files absent in last local inventory. |
| §3 MMD PMD/PMX, VMD/VPD | Partial | Direct native PMD/PMX file routing uses the installed converter and shared model controls; VMD/VPD and richer native semantics missing. |
| §3 FBX / OBJ / glTF / GLB | Present/tested, bounded | Binary FBX, OBJ/MTL, glTF2.0 sidecars/data URI, embedded GLB. Native clips retained externally, not mapped to timeline. |
| §3 VRM / SMD / DMX / Blend / USD | Partial | Direct VRM0/1 geometry/rig import, humanoid metadata and facing normalization; native VRM behavior and other listed formats remain missing. |
| §3 One standard native representation / provenance | Partial | Embedded GLB + versioned studio_model_1/2/3 + native reports shared across adapters; original native/blend conversion bundles external. |
| §3 Asset-browser thumbnails | Missing | Text search/browser works; lazy thumbnails are suggested engineering work. |
| §4 Model click / green outline / visible bone selection | Present/tested, bounded | GPU mesh picking, green skinned outline, bone tree/joints and FK handles; click selects directly into posing without camera movement. Draw still paints. |
| §4 Alt skeleton reveal | Present/tested; owner resolved | Owner explicitly chose hold Alt to reveal, release to hide. Selected handles remain; focus/Escape clears reveal. |
| §4 RMB deselect / entity context menu | Present/tested, bounded | Short empty click deselects; entity context offers Frame, Reset imported pose and Hide/Show. Drag beyond4pixels remains POV; Ctrl+LMB free camera. |
| §4 Hidden selected child green ghost | Partial | Hidden selected objects under parent groups get editor-only ghosts; group selection outlines descendants. Existing whole-model x-ray and source/visibility isolation retained. |
| §5 Direct model/bone auto-key | Present/tested in this increment | Owner specifically confirmed auto-key models/bones, camera keys explicit. Completed edits key current frame in one undo group. Advanced opt-out retains draft editing. |
| §5 Smooth easing / detailed curves | Partial | ease, linear and hold; easing default. No custom curve editor. |
| §5 Default IK / feet planted | Present/tested, bounded; installation gate separate | Default hand/foot authoring plus Model7 persistent ranges, direct foot/knee correction, inherited-transform reach guards, clip reanchoring and explicit physics ownership. Full frozen-source regression passed93processes. Installed-copy status is in the current memo/normal-source-state marker. Sparse Hold feet alone still slides between FK keys; automatic ground/walking/full-body inference remains unfinished. See foot_contacts.md and contact_animation.md. |
| §5 Motion Assist / overshoot / reusable walks / multi-view paths | Missing; some design OPEN | No compulsory AI or generated motion. Bounce intensity and path inference remain preferences/experiments. |
| §6 One animated camera / instant cuts | Partial | One shot Camera3D, hold/linear/ease keys; adjacent-frame positions sample exact values. No Simple Cut action. Temporary inspection transform still requires explicit shot key, as owner confirmed. |
| §7 Expand animated channels / draggable clips / split/copy/paste | Partial | Every object has a collapsed row; independently owned split/copy/cut/paste/delete pieces and Shift-drag whole-object timing use stable-ID Undo. Animated part rows now expand for selection/key inspection; independent per-channel curves, stretching/ripple and cross-rig retargeting remain missing. |
| §7 Object lifetime / gap hold versus bridge | Partial; owner clarified bridge intent | Version2 pieces connect gaps under existing interpolation, preserve held final state and absence before introduction; explicit earlier manual keys extend introduction. Persistent visibility keys and parent state remain authoritative independently of motion. |
| §8 Persistent visibility keys / global 300ms fade | Present/tested, bounded | Simple Show/Hide keys persist independently of motion; project Options defaults300ms/0cut; version3, parent opacity, ghost, HAS/recovery/export. Native partial alpha may reveal inner surfaces; see visibility.md. |
| §9 Physics ON / grab/throw / freeze / T-pose | Partial | Simple Physics, approximate ragdolls/map collision, dynamic props, grab/release and freeze work. Interactive compatible ragdoll imports now default ON, waiting for modal completion and preserving earlier live body/hair modes through import rebuilds. Native collision/joint fidelity and inferred T-pose remain incomplete. See import_physics.md/current progress for verification and saved-copy status. |
| §9 Explicit Local / World Record | Present/tested, bounded | Explicit Simple Local/World captures staged fixed-tick sparse poses/roots into ordinary pieces; atomic Undo, saved replay and MP4. Local excludes peer motion; World captures all live targets. Live audio preview and long/dense scaling remain limited. See physics_recording.md. |
| §10 Unshaded default / Lit toggle / BSP baked lights | Partial | New projects use Unshaded; Simple offers Lit and compatible Studio light, saved with Undo/HAS/recovery/export. Actual imported GLB lights work; native BSP lightmaps and detailed light authoring remain missing. See lighting.md/current progress for saved-copy verification. |
| §10 Optional photorealistic renderer | Missing; aspiration OPEN | No ray-tracing promise; keep responsive basic pipeline first. |
| §11 Packed HAS default / linked opt-out / locate missing | Present/tested | ZIPv1 around schema3/4, checksums and bounded validation; GLB/PNG/WAV/poses/camera/native reports embedded. No need to replace format. |
| §11 Independent native model/map distribution | Missing; packaging choice OPEN | No dedicated asset package or extension. Do not invent one in this increment. |
| §11 Project settings versus personal preferences | Partial; tentative | Frame/rate/assets saved; interface visibility and local mounts separate. Global visibility fade now saved; render/lighting settings still needed; no settings-load prompt. |
| §12 Interactive courses / whole-scene Previous / resume | Partial; see current run/save status | Basic first-movie course covers actual map/model imports, live/unrecorded physics/freeze, selection/reset, camera, auto-keyed arm, Ink, preview, clip split/drag and optional personal Save/actual MP4. Existing pose/draw and camera chapters remain. Quiet15s offer/requested control-joint highlights, clear/collapsible guide, full Previous and Continue/Fresh retain versioned observations. Advanced sections, topic/subsection entry points and richer demonstrations remain required. Skip OPEN. See tutorials.md. |
| §13 Quiet default autosave / action schedule | Present in current source, bounded; see actual run/save status | Default1min; Advanced0.5–10min or1–1000 completed edits (initial25). Counts completed changed commands/Undo/Redo/layer visibility, not stroke segments/navigation/no-ops. Busy deferral, commit-only count reset, failed-write backoff and exact-revision Save protection. Preview/write responsiveness remains partial. See recovery_schedule.md. |
| §13 Bounded journal / thumbnails / Advanced history | Present in current source, bounded; see actual run/save status | Checksummed catalog,12 immutable metadata states/session/shared assets, rollback, idle256x144 previews and Advanced timestamp selection/restore; saved/dismissed history stays browsable. One CPU-image worker resizes/blends/encodes/writes, checkpoint writers serialize and explicit requests queue. Main GPU readback/copies/checkpoint writes, shared-asset cleanup and large-cache latency remain incomplete. See recovery_preview.md and recovery_history.md. |
| §13 Automatic newest-valid recovery / fallback | Implemented in current source; see latest verification/save status | Normal startup tries newest candidates through complete asset/rig validation, including retained journal states, skips bad generations and restores an unsaved copy without touching manual HAS. No valid candidate keeps clean New. Explicit history remains; cache/latency refinement is incomplete. See startup_recovery.md. |
| §14 Independent 2D / audio / VFX / chroma | Partial | Rough/Ink, optional Flats/Effects and general four-layer add/name/order/removal/visibility/opacity with Undo; holds, pen/eraser/fill with spill preview, guide-free view/drawing/original color picker, previous/next onion guides and one PCM16 WAV + AAC. Gap closing, pressure, persistent palettes, richer onion ranges, native KRA, multi-audio, VFX stack and chroma remain. See color_picker.md/drawing_layers.md/layer_opacity.md/drawing_fill.md/onion_skin.md/current progress for actual verification/save status. |
| §14 1080p24 MP4 beside saved HAS | Present/tested in this increment | Main navbar Export writes fresh render folder beside current HAS; unsaved/recovered/legacy asks destination; Advanced one-off override. |
| §14 Configurable resolution/rate / independent PNG export | Partial | Rational frame engine,1080p24 defaults, retained PNGs accompanying every movie; no general settings UI or PNG-only action. |
| §17 Full novice / cross-ecosystem / physics / tutorial acceptance | Not met | End-to-end limited camera/pose/cel/audio/HAS/movie works; this audit does not certify all six scenarios. |

## Decisions and bounded implementation order

**User-confirmed:** this addendum governs earlier conflicting decisions; direct bone and
model edits auto-key, while camera keys stay explicit. That resolves the previous manual
pose-key conflict. No additional conflict approval is needed for changes already decided
by the addendum. Its unresolved details still require assessment at the relevant step.

**This patch:** auto-key manual FK/root edits and the saved-HAS export destination.
No storage migration, imported clip playback, generated locomotion or physics recording.
Auto-key is an authoring preference, default ON each launch; old files open without
changing keys. Advanced can turn it off; explicit Record still works. No implicit rest
key is invented: pose the initial frame before the later pose when you want a transition.
Current keys store whole sparse poses/root, rather than new per-channel tracks.

**Next proposed patch:** default rig-aware IK/physics/capture, retaining independent channel-curve controls as open timeline depth. Animated part inspection is now implemented.
Persistent visibility keys and global fades now have a first implemented increment. Independent split/clipboard pieces now connect gaps and retain
source curves. Time stretching/ripple/looping and cross-rig motion transfer remain
future features. IK, physics/capture and interactive lessons remain required later
increments. The proposed order follows dependencies; it does not shrink full scope.

**Engineering choices:** exports remain a fresh `render_*` folder next to the HAS rather
than overwriting `<project>.mp4`. This retains PNGs/logs and old movies. A chosen alternate
folder applies to one run and does not change project data or its default destination.
Godot4.6 [DirAccess](https://docs.godotengine.org/en/4.6/classes/class_diraccess.html) and
[FileDialog](https://docs.godotengine.org/en/4.6/classes/class_filedialog.html) APIs were
checked; directories are newly created, and the picker hides before starting export.

## Verification for this increment

See the appended progress checkpoint for final canonical commands, exit codes and counts.
New checks exercise automatic edit keys/overwrite/undo, cancelled gestures, draft opt-out,
HAS reopen, preview/export frame agreement, Simple default destination, Advanced override,
unsaved cancellation, unchanged manual HAS and previous-movie preservation. Physical mouse,
tablet, clean-machine portability and subjective rendering/audio acceptance remain untested.

Final canonical result: verify.py exit0 (including automatic-key29 and actual MMD/GMod/SFM), verify_has.py exit0 (12 container fixtures +32 app checks). See progress_memo.md for test scope and intermediate failures.

Empty-world checkpoint: canonical verify.py exit0 including new-scene20; verify_has.py exit0 (12+32). New/startup, editor-only fading grid and portable empty HAS work. Home/world tree/selection and other matrix gaps remain pending.

Selection checkpoint: canonical verify.py exit0 with selection41 and actual MMD/GMod/SFM; verify_has.py exit0 (12+32), verify_generic.py exit0 (9+41). Owner resolved Alt to hold/release. Top-level selection/hierarchy works; multi-instance transforms/groups/lifetimes/clips remain incomplete.

World-format foundation checkpoint: canonical verify_world_document.py exit0 (21Python+36Godot+four readers, actual native rigs); verify.py exit0 including world-document36; verify_has.py exit0 (12+32). Multi-object runtime/UI remains pending; safe schema4 Open guard remains. See world_format.md and progress_memo.md.

Multi-object renderer checkpoint: canonical verify_world_runtime.py exit0 (43actual checks, real MMD/GMod/SFM side-by-side deformation, packed reopen, H2641080p24); full verify.py exit0 including runtime43; verify_has.py exit0 (12+32). Registry/rendering is implemented; normal multi-object editor selection/Undo/import/recovery remains the next gate.

Multi-object editor checkpoint: canonical final verify_world_edit.py37 checks, all64IDs, actual MMD/GMod/SFM controls/Undo, packed/linked/directory/recovery saves, three separate package readers and H2641080p24 movie pass. Full suite passed before the final mask-filtering visual fix; affected editor37 and original selection41 reran afterward. HAS12+32 passed. Normal append import and schema4 New/Open/recovery restore remain the next required gate.

Normal-workflow checkpoint: Add/New/Open/recovery transitions are now connected and tested in the real app. Timeline clips/presence UI, visibility fades, IK, physics and tutorials remain missing. Koikatsu/KKS/AI card inventory is implemented; character assembly, Unity maps and AA2 import remain investigations. VRoid/VRM owner samples are now available for the next adapter test.

Final normal-workflow checkpoint: canonical full verify.py passes including37world-edit/24ordinary-workflow checks; HAS13+32, world22+36/four readers, normal-workflow24 with AAC onset1.0000417s, VRM samples19 and Illusion inventory9 all pass. Native VRM semantics, Illusion assembly, clips/visibility/IK/physics/tutorial gaps remain explicit.

Direct native importer checkpoint: canonical8VRM fixtures+43real PMD/PMX/VRM tests pass, full core suite passes, common9+41 and Source8+6+32 regressions pass. Direct picker/worker import, VRM forward normalization and native humanoid metadata now work; IK/physics/morph UI/native material fidelity, oversized rigs and KKBP companion-bundle assembly remain missing. Misaki comparison is structural evidence, not a successful import claim.

Import timing checkpoint: canonical20handler/picker/async/presence/HAS/render checks pass; native8+43, common9+41 and Source8+6+32 regressions pass. Full core suite passed before final OS-coordinate correction, affected timing20 reran afterward. Physical Explorer drag remains unverified; grounded spawning, batch queues and draggable clips are still missing.

Near-camera placement checkpoint: canonical21checks including real GMod geometry, HAS/movie and passive-tooltip recovery pass. Full core suite, timing20, native8+43, common9+41, browser14+28 and Source8+6+32 all exit0. Nine-candidate placement remains approximate, not physics; timeline clips/fades/IK/physics/tutorial and large-rig/KKBP gaps remain.

Owner follow-up: known Japanese humanoid bone names use a small local dictionary of English estimates, marked ≈, with original-name/ID tooltips and English/native search. Presentation only; original rigs and HAS bindings remain unchanged.

Whole-take timeline/dictionary checkpoint: canonical full core passes including36timeline/16labels; timing20,HAS13+32,native8+43,common9+41 pass. Actual MMD/GMod/SFM retiming/HAS, pinned64rows and Miku English search tested. Multiple pieces/splitting/clipboard/channel expansion, gap evaluation and visibility/fades remain required.

Independent-piece checkpoint: final canonical domain32/app50/full core/cel probe38
all exit0. Exact source sampling, independent edits/growth, gap bridges,
packed/linked/recovery, actual MMD/GMod/SFM and H264/AAC1080p24 tested. Visibility
keys/fades and channel expansion remain next; see progress memo for phase-specific
evidence and limitations.


Visibility checkpoint: canonical full core including49visibility, HAS13+32, native8+43, common9+41 all exit0. Final legacy-only promotion guard reran visibility53 and clip-domain32, both0. Persistent visibility/global fades now work; animated-channel expansion, IK/physics/capture and the remaining full scope stay open. Native per-surface alpha appearance is limited; no whole-object silhouette-fade fidelity claim.


Animated-part checkpoint: canonical46checks/full core/HAS13+32/native8+43/common9+41 all exit0. Expand/collapse, source-time key inspection, actual MMD/GMod/SFM selection, Miku many-row scrolling, metadata/HAS/recovery and H264/AAC tested. This is shared-snapshot part inspection, with independent curves, channel hierarchy and legacy-lane expansion still open. Default IK and2D adapter integration remain next.


Owner naming follow-up: Simple uses generalized body-part names in tree and timeline; Advanced reveals exact internal names and full-ID tooltips. Native identities and saved data unchanged. Owner reiterated visible Simple Physics and less clipping/controlled chaos; full physics/capture remains required and missing. See current progress checkpoint for actual test evidence.


Final limb/name checkpoint: canonical full core (limb58/labels25), focused limb58 and HAS13+32 all exit0. H264/AAC1080p24/48frames/2s and decoded onset1.0000417s; no physics or persistent foot-planting completion claim. See progress memo for actual scope.


Live physics foundation: manually activated Simple toggle, actual Jolt120Hz ragdolls, map contacts, grab/lift/release and freeze. Explicit Local/World capture and automatic-on compatible imports remain required, not replaced by existing Record pose key. See current progress memo for evidence and draft/static-save limits.


Final live physics checkpoint: canonical physics51/full core/HAS13+32 all exit0 after degree-range, collider/contact, invalid-save and synchronous-toggle fixes. Simple grab/release/freeze is implemented; automatic-on imports, dynamic props and Local/World recording remain required. See physics.md/progress memo for scope and evidence.


Dynamic-prop checkpoint: canonical props41/full core/HAS13+32 all exit0. Real ragdoll impacts displace settled boxes; prop freeze/root Undo, packed HAS, RGBA/WAV and MP4 pass, including prepared CSS-chair/OBJ. Automatic import activation and explicit Local/World recording remain required. See physics.md and progress memo for limits.


Final explicit-recording checkpoint: canonical11domain+56actual/full core/HAS13+32 all exit0. Local/World real ragdoll-box capture, MMD/GMod/SFM/VRM0/1, saved replay and H264/AAC pass. Native automatic activation, collision fidelity and long dense scaling remain open. See physics_recording.md/progress memo for phase-specific evidence and limits.

Owner physics-quality steering: prioritize stiff VRM/Scout upper limbs before
automatic import activation. Limb-aligned joint profiles and elbow/knee hinges
are the current bounded refinement; final evidence belongs in the progress memo.
Native constraints and all-rig anatomical fidelity remain incomplete.

Owner secondary-motion steering,2026-10-30: add smooth hair/skirt motion and a
movable adjustable-speed fan; reuse existing VRM spring joints, infer correctable
loose regions and generate HAS helper bones/skin weights when missing. Confirmed
actual samples retain VRM1 twelve springs/22colliders and VRM0 ten bone/collider
groups. Runtime wind and generated helpers remain missing; see secondary_motion.md.


Secondary-motion foundation: GLB loading now derives a shared bounded descriptor
from VRM0/1 authored chains. Explicit experimental fixed-step spring runner tests
wind, centers/colliders, positive uniform scale, skipped intermediates and ordinary
FK take/Undo/packed HAS/MP4 reuse. No automatic hair activation, Simple fan controls,
normal Local/World secondary recording or missing-bone generation yet. Native
initial transients remain a quality gate; see secondary_motion.md/progress memo.


Current secondary product increment: Simple Hair & clothes, ordinary Add fan with
contextual blowing speed, smoothing, optional simultaneous body ragdoll, normal
Local/World Record, packed native provenance and recorded MP4 are implemented.
This supersedes the prior experiment-only gate above. Existing-chain VRM support
remains bounded; generated helper bones/skin weights and native MMD secondary
constraints remain missing. Full acceptance is not met. See secondary_motion.md
and the current progress checkpoint for tests actually run.


Current missing-rig increment: reviewed connected skinned regions, weighted anchor
choices, correctable proposed joints, pinned root seam, immutable weighted helpers,
ordinary posing/Undo/fan/Record and packed/linked HAS now have implementation and
focused tests. This supersedes the earlier entirely-missing helper statement.
Full acceptance remains open: unskinned assets, manual garment masks/attachment seams,
multiple authored chains, stiffness inference and native cloth constraints still
need work. Native structural evidence is not automatic clothing classification.


Multi-part refinement supersedes the single-chain limit above: repeat reviewed
setup for additional unrigged components on the same skinned model, including beside
valid VRM0/1 chains. Already spring-weighted regions are protected. Native chains,
colliders and existing helper motion stay intact; generated additions use HAS asset
extras and ordinary Record/HAS playback. Unskinned assets, editable region/seam masks
and authored contact groups remain incomplete; this is not full cloth acceptance.


Manual garment-patch increment: choose a smaller connected patch by view box,
Add/Remove/Whole part, review exact skinned wires and preserve the cut boundary.
Partly rigged whole components can be inspected; overlapping spring weights remain
protected. New helpers affect only the selected patch and use ordinary Undo/Record/
HAS/MP4. Front/back inclusion,5000vertex component bound, no-free-span refusals,
unskinned assets/full cloth/custom pin painting remain explicit limits. The earlier
entirely-missing garment-mask statement is superseded by this bounded implementation.

Shape-fidelity foundation: the helper worker can now evaluate explicit morph
snapshots or requested source defaults, including sparse POSITION targets, before
assessment/preview/derivation. Authored real-GPU comparison and source preservation
are tested. Normal UI remains neutral; runtime default-weight restoration, exact
mesh bindings, saved compatibility settings and expression authoring remain missing.
This is partial progress on importer fidelity, not completion of native morph support.

Normal imported-shape integration now supersedes the experiment-only gate: new UI
imports use node/mesh defaults, old records remain neutral, Advanced opt-in has Undo,
normal helper review snapshots actual morph weights, and packed HAS/MP4 retain it.
Shared/reparented/root mesh identities and shaped prop hulls are covered by focused
Windows tests. General expression editing/keys and native nonvertex morphs remain
missing; see the latest progress entry for final regression scope.

Static setup refinement: Advanced **Base shape · whole project** now edits imported
positional channels by native mesh part/name, with Apply/reset/Undo. Version2 sparse
absolute amounts survive defaults on/off, helper revisions, packed/linked HAS and
MP4. Actual MMD/GMod/SFM deformation and Scout channel519 are covered by focused
tests. This narrows the importer-fidelity gap but does not complete auto-keyed facial
expressions, VRM expression presets or native material/bone morphs. All matrix gaps
and full acceptance requirements remain; final evidence is in progress_memo.md.

Per-frame expression increment now supersedes the static-only gate: Simple
Shapes / expressions provides auto-keyed positional target amounts in model4,
with named timeline rows, ordinary block split/retime/gaps/clipboard, Undo,
packed/linked/recovery, helper revisions and recorded MP4. Actual MMD/GMod/SFM and
VRM0/1 positional channels have focused Windows evidence. Native expression-group
presets/material/bone morphs and independent curves remain partial/missing; this
does not satisfy full importer fidelity or all addendum acceptance scenarios.

The model4 shared-snapshot gate is addressed by dedicated model5 expression
controls: new expression edits preserve existing body control values and easing.
Legacy model4 reading preserves its historical curves, and explicit promotion
extracts expressions without silently rewriting body motion. Separate expression
drafts, per-target control frames and removal/Undo complement source-time block
editing. Root/bone per-axis independence and native expression-group semantics
remain open; see shape_animation.md and current progress evidence.

Independent body-curve foundation: the remaining bone/root snapshot coupling has
an explicit reproducer. A separate bounded per-part override/deletion contract
preserves old snapshots, source slices/gaps and peer interpolation, with native GPU
and physics-take comparisons. It is not connected to normal editing, history or
native HAS storage yet; those acceptance gates remain OPEN. Sampled diagnostic
movies/projects do not close them. See body_curves.md for the integration gates.

Normal body integration supersedes the experiment-only gate above: model6 connects
independent root/bone keys to auto-key, default limb IK, explicit Record, selected-
part deletion/Undo, source slices/clipboard and native editable HAS/recovery/render.
Per-part ranges preserve peer easing while an unsliced take grows. Models1–5 keep
their historical reads until edited. See body_animation.md and the latest progress
memo for actual final test/canonical-save evidence. Per-axis curves, detailed curve
editing and all remaining full-goal gaps are still OPEN; this is not full completion.

Lighting increment: Simple Unshaded/Lit/legacy Studio light now shares saved project
video settings, preview/export and Undo. New empty scenes default Unshaded; old
records retain their original appearance. Instance-owned material copies compose
fades and preserve authored material/texture resources. Actual GLB scene-light and
native rig checks are in verify_lighting.py. Native BSP baked lights/lightmaps,
shader fidelity and light-authoring UI remain OPEN; this narrows §10 without
claiming complete native lighting/render quality. See lighting.md/current progress.

Current-pose framing refinement: Frame model/selected/scene now query the current
skinned and shaped geometry instead of shaped bind boxes. Physical final poses
are read from the existing modifier callback, without freezing or recording.
Hidden reference framing and explicit shot keys stay separate. This improves
scene usability but does not complete remaining camera tools, native physics,
cloth/assist or any other OPEN requirement. See pose_framing.md and the latest
progress memo for actual verification and canonical installation status.

Shot/editor isolation refinement: explicit camera keys now retain optional near/
far visibility distances; reference framing no longer changes distant shot output.
Old keys retain cold-start defaults; packed/linked/recovery use the same fields.
This strengthens the core animated-camera/independent-drawing contract without
claiming finished independent curves, physical cameras or full render fidelity.
See camera_projection.md and the latest memo for actual run/save status.

Recovery ownership refinement: new session sidecars retain exact Windows creation
time with the PID, distinguishing an expired writer from a reused live process
number. Matching live or uncertain owners remain protected; legacy PID-only data
keep their old conservative behavior. Native project/HAS/journal formats stay
unchanged. The focused identity/startup checks do not close shared-asset cleanup,
concurrent quota, large-cache latency or real power-loss/full-disk acceptance.
See startup_recovery.md and the latest memo for actual run/save status.

Continuous-contact foundation: a separate versioned source-time descriptor and
read-only world-space two-leg solver now have actual native-rig half-frame/seek,
release/rollback and visible-GPU experiments. This is NOT normal model7 acceptance,
contact UI, HAS persistence, physics recording or final-render integration. Those
remain required gates; the existing direct-authoring option still has its playback
sliding limitation. See foot_contacts.md and the current progress memo.

Live appearance correction: ordinary Hair & clothes updates and imported-peer
restarts now retain project Unshaded/Lit/Studio settings and inherited parent fade.
The actual UI reproducer previously lost Unshaded and replaced half opacity with1;
the focused regression checks both owner VRMs and original visible geometry.
No native shader/cloth fidelity or continuous-contact completion is implied.

Separate Model7 WIP now includes ordinary contact sampling/persistence/rendering
and Simple Plant/Release range controls, root correction and Undo. Native MMD,
GMod, SFM and VRM evaluator tests plus actual control/HAS/paint/movie tests exist.
The normal canonical application uses533d71d37 plus the compatible two-file outline
fade repair documented below. The development WIP now has
actual cross-instance/project clipboard reanchoring and focused Body/Hair/OFF/
Local/World contact interval tests. The remaining correction, inherited-parent,
reopening and performance gates still precede normal promotion. The development
worktree now also validates complete frozen-pose metadata before stopping physics
and gives descendant-aware feedback for nested-group Move, drafts and timing edits.
Read-only sampling retains authored ancestors; no child keys are invented.
Dedicated development correction controls now provide Simple view-relative foot
nudges/knee reversal and Advanced exact pin/orientation/world-knee targets, with
range validation/Undo and preserved other-foot/release/body data. Nested contact
version2 prevents older experimental readers from silently ignoring knee settings.
Viewport pin/pole gizmos, wider acceptance and remaining normal-activation gates
stay open; this does not change the matrix's shipped foot-planting status.
See contact_animation.md and the newest progress entry; this
does not change the matrix's shipped foot-planting status or claim full acceptance.

Further development acceptance: compiled native leg bindings retain485 reference
poses and a bounded five-native/32-block scene. Fresh packed/linked/recovery/lesson
store checks preserve the native combined world, editable paint and audio/movie;
teacher crash context is still separate. Newly captured channels now retain their
pre-take baseline instead of leaking a fallen pose backwards. Reused Cut clipboard
and Undo restore independent contact identities, with prepared MMD/GMod/SFM/VRM
checks and a cold reopened VRM pair retaining194 poses exactly. These remain WIP
checkpoints; hidden green geometry/current framing, wider inherited transforms and
viewport pin/pole usability still precede normal promotion. Keep all six gates in
foot_contacts.md and the full MD scope. See contact_animation.md/progress_memo.md.

Dedicated hidden-geometry acceptance now passes67 Model7 checks on five native
rigs, comparing actual posed masks against independent engine bakes, visible green
ghosts and hidden/group framing through inherited fades and reverse seeks. It
found and repaired masks retaining temporary faded materials. The same compatible
two-file repair is installed/tested in the normal app:67 Model6 checks plus five
existing suites pass; its reader still rejects7. This improves normal selection
without promoting development contact data. Wider inherited transforms/lifecycle
and viewport pin/pole controls remain before Model7 activation; shipped foot-
planting status remains Partial. No full-MD or whole-suite completion is claimed.

Further Model7 development acceptance covers nested numeric/ring rotation and
uniform scale on five native rigs with fixed feet/knee targets, complete-range
reach refusal and exact Undo/Redo. Apply scale now defers before consuming pending
physics, freezing a live body or ending Local Record; returning a drag to a valid
pose clears stale reach feedback. Supplied native baseline rotation/scale is
preserved in the test fixture. Reparenting currently has parent-ID data validation
but no editor operation; it is not implemented merely because scene trees load.
Viewport foot/pole controls and wider lifecycle/full-gate acceptance remain.

## 2026-11-01 continuation: current installed and development states

The historical matrix and entries above describe earlier checkpoints. Normal
Studio now contains the owner-approved Model7 update with its source backup and
nine normal-path groups/619checks/14private receipts verified at installation.
Its reader accepts Model7. Development Model8 adds saved reversible motion
feeling with exact authored main keys; its frozen source completed all98original
full-verifier processes under fingerprint
`506de8ee22205f4863d8425611bea56c85984d2295dd7af5e282243d8d8a0135`.
That complete source/evidence is retained in `output/model8-full-frozen.json`.
Known earlier failed camera-watchdog/controller-I/O attempts remain recorded.

A later development-only deform catalogue increment adds Simple area filters and
Advanced persistent manual names/areas, with21unit/109app/5cold checks and four
affected existing groups passing. A final original-name caption was visually
verified. It is newer than the completed98-process source, so that old full result
does not certify every current file. The new catalogue suite is wired into the
normal verifier. No newer source was installed over normal Model7 by these steps.

The supplied SFM corpus now has66native definitions, nine native raw-delta probes,
and one actual Mima-head case with three controls verified through native geometry,
GLB, normal controls, HAS/cold Open and MP4; a relocated example opens in normal
Model7. See `docs/sfm_sample_corpus.md`. Name-area guesses/manual grouping are not
the requested geometric estimator or complete native expression preset support.
Optional stature/map fitting and native particles have research evidence but no
new product UI/playback yet. These supplement the full original goal; complete
novice/cross-ecosystem/physics/tutorial/clean-machine acceptance remains open.

## 2026-11-01 continuation: observed deform regions

Development now includes a read-only positional observation backend across844
targets on six actual prepared assets, with1688signed neutral comparisons and
tentative same-model region matching from explicit weak seeds. It found/fixed a
real Source CamelCase/mixed-name categorization issue; current catalogue regression
is29unit/112app/5cold, all0. The geometry estimates are not automatically applied
in the editor, not emote/native controller evaluation or a cross-model learner.
See [deform_observations.md](deform_observations.md) for evidence and open gates.
Normal Studio remains approved Model7; frozen earlier review/web artifacts stay
unchanged. No broader full-MD or current full-suite completion claim.

## 2026-11-01 continuation: usable Advanced deform study

Advanced Shapes can run the local positional study, inspect matching-example
provenance/uncertainty and explicitly adopt an area through ordinary manual
catalogue Undo. Actual workers on six native preparations retain all844bindings;
current47app/cold/teardown checks and17Python tests pass, plus affected regressions
recorded separately. No automatic category installation or new project format.
Full native controller/emote/material/bone/UV semantics, visual study comparison,
broader supervised labels and all prior full-goal gates remain unfinished.
See shape_study.md. Normal Model7 and the frozen web handoff are unchanged.

## 2026-11-01 continuation: visual neutral comparison

Development Advanced Shapes now offers Compare without recording: a focused
neutral/test pair for one exact source target, adjustable mathematical amount and
shared turn controls. It uses the standard renderer on an isolated temporary copy,
leaving the document, pending amount, view, drawings and animation unchanged.
See shape_comparison.md for actual tests and synchronous-import/memory limitations.
This supplies bounded positional visual review; it does not finish native presets,
compound rules, non-position deforms, calibrated semantic learning or artist-first-
use acceptance. Normal Model7 and the frozen web artifact remain unchanged.

## 2026-11-01 continuation: declared VRM expression poses

Development now exposes source-declared Expressions / emotes separately from raw
area-labelled deforms. VRM0/1 resolve exact compound bindings into one standard
pose/key/Undo operation; Simple labels, Advanced native bindings, unsupported
material-only guidance and side-window placement are tested. No saved format
change. Full native animated expression semantics, material/texture/bone effects,
Source rules and MMD groups remain unfinished. See expression_presets.md for
actual native/HAS/cold-reader/MP4 proof, metadata protection and limitations.
The normal Model7 app and frozen web handoff remain unchanged.

## 2026-11-02 continuation: full current workflow review

The full existing Windows verifier plus nine native/common/Source/SFM/browser/
HAS/placement/timing/joint wrappers completed115 top-level commands, all0, with126
private graphical receipts and unchanged functional input hashes. Native test
paths now use verified retained raw VRMs, correcting the first run's missing-file
failure and optional skips. See current_review_2026-11-02.md for exact scope and
remaining gates. This supersedes older "full verifier not rerun" statements only
for this tested snapshot; it does not complete the full addendum, certify every
asset/physical-input/clean-machine behavior, or update normal Model7/frozen web.

## 2026-11-01 continuation: known-distance static map calibration

Simple World > Size map now offers two surface marks, editable door/ceiling/span
examples and an isolated preview against a six-foot guide. Apply anchors the
first point, uniformly scales only the selected static map and records one Undo.
Actual gm_construct geometry participates through the same standard model path;
HAS/cold Open and ordinary MP4 are covered. See map_calibration.md. Animated,
attached or skinned maps, existing foot-contact reanchoring and broader artist
acceptance remain open. This supplements the full goal without changing normal
Model7 or the frozen web preview.

## 2026-11-02 continuation: MMD source-declared expression groups

Fresh MMD preparation now retains nested group membership and weights, resolves
exported vertex targets and feeds the same expression catalogue/standard keys as
VRM. Simple prefers source English names; Advanced shows originals/bindings.
Mixed unsupported effects and invalid graphs refuse as a whole. Original authored
PMX fixtures cover actual worker/UI/Undo/HAS/cold/MP4, separately from supplied
samples lacking groups. Continuous native group-weight animation, nonvertex effects
and broader corpus acceptance remain unfinished. See expression_presets.md. No
normal Model7 replacement or frozen web rebuild/deploy.

## 2026-11-01 continuation: opt-in character height review

Development Options can offer a six-foot height review before new model placement
and default Physics. Off performs no extra analysis or adjustment. One standard
model path handles MMD/GMod/SFM/VRM; validated legs/head plus real mesh coverage
exclude separate heads, including those retaining a whole skeleton. Complete
unusual proportions start unchecked. Explicit Add, Cancel, timing, one Undo,
source preservation, packed/linked/cold Open, independent drawing and ordinary
MP4 are covered by 117 new checks. See height_import.md for exact evidence and
synchronous-import limitations. This is an owner-requested supplementary feature,
not full native fidelity or completion of map calibration/existing animated scale.
The normal Model7 app and frozen web handoff remain unchanged.
