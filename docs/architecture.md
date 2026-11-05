# Architecture, schema 2 (legacy schema 1 readable)

Home is an embedded `home_screen.gd` overlay over the same live document. Normal
startup finishes newest-valid recovery first; only an unrecovered clean New shows
Home. `recent_projects.gd` stores bounded local UI metadata after successful HAS
save/open, separate from project data. Managed recovery thumbnails are optional
references, never file validation. Existing New/Open/dirty confirmations and HAS
workers remain authoritative. See [Home](home.md); course/lesson integration is next.

Current recovery preview work uses `recovery_preview.gd`: main-thread viewport
readback plus independent cel snapshots, one worker for CPU image preparation and
PNG/journal I/O, nonblocking completion polling and teardown joining. Checkpoints
defer while that writer is active, with queued explicit requests. No active scene
or GPU API runs on the worker. See [recovery previews](recovery_preview.md) for
ownership, lifecycle, measured scopes and remaining synchronous work.

`main.tscn` launches a standalone application shell (`src/app.gd`), not an engine
editor plugin. `canvas_view.gd` maps window/zoom/pan coordinates to 1920×1080;
`timeline_view.gd` displays camera diamonds and cel exposures with click/drag seek.

`foot_hold.gd` captures both validated leg endpoints for opt-in body Move gestures.
The existing scratch limb IK solves ordinary FK deltas; the editor previews from
the gesture baseline, restores the last reachable candidate on failure, and commits
one automatic pose key/Undo. It has no persistent timeline contact state. See
[held-foot authoring and the continuous-contact gap](foot_hold.md).

`timeline.gd` is the time authority: integer frame, rational FPS, sorted camera keys,
position/FOV interpolation and quaternion slerp. Each key's interpolation controls
its outgoing interval. Export samples `n*fps_den/fps_num`, never wall-clock delta.
Interactive preview uses the audio playback position, compensated for time since last
mix and estimated output latency, when a clip and hardware driver exist. Otherwise it
uses monotonic time with an explicit silent fallback on Dummy audio. Visual frames
may drop under load; export duration never changes. Playback runs once and stops at
the final frame. Switching mode preserves frame and restores the sampled shot; a temporary
navigation camera transform is only committed by an explicit key operation.

`scene3d.gd` creates the original box-built fixture and imports GLB using GLTFDocument
at runtime. Only embedded resources are accepted; no external URI/network loading.
128 MiB GLB limit. The current import is static geometry/materials. Camera keys are
independent of imported cameras and file animation. Godot uses right-handed +Y up,
camera facing -Z; keys store quaternion XYZW. Model units are interpreted as meters.
No automatic re-centering or source-file modification occurs.

`renderer.gd` owns a full-HD SubViewport, independent World3D, application light and
camera. Preview displays its texture beneath a transparent ImageTexture. Export
samples the same camera and cel functions, waits for frame_post_draw and reads the
GPU texture; it composites the identical cel overlay into an RGBA PNG. Geometry and
paint never share mutable state. Lighting is deliberately simple and may combine
with imported lights; material/import compatibility is limited by Godot.

`drawing.gd` stores layers of independent Image resources. An exposure is `[start,
start+duration)`; a duplicate copies pixels while holds reuse them. Painting is
screen-space RGBA8, assumed sRGB, normal straight-alpha composition. There is no
linear-light/HDR/ICC pipeline. A distance-to-segment brush prevents gaps from sparse
mouse events. Stroke history stores before/after 64×64 touched tiles. History is
charged conservatively and trimmed to 64 MiB (a single large structural command
can exceed this); current raster data is capped at 32 cels (~253 MiB). No cold cache
yet. Full overlay composition/upload is limited to once per dirty application frame;
measured baseline precedes any GPU brush/tiled upload redesign.

`fill.gd` performs bounded four-connected seed/tolerance scanline filling over
detached RGBA bytes. `fill_editor.gd` owns one low-priority worker, guarded revision/
frame/layer installation, exact candidate composite previews and atomic cel/tile
history. Only the main thread accesses live Images/textures/nodes. An explicit
Flats insertion retains original layer dictionary/image identities so older Undo
commands remain valid. Existing layer/cel storage and final renderer stay shared;
unapplied previews are canvas-only. See drawing_fill.md for limits and references.

onion_editor.gd selects adjacent exposures of the active layer and caches two
alpha-tinted GPU rasters behind the current overlay. CanvasRaster shares its exact
float image rectangle for background/ghosts/front paint. Transient Image revision
metadata invalidates edited neighbor caches without serializing settings or
changing source pixels. The final renderer, fill sampler and recovery use committed
layers alone, never these UI items. See onion_skin.md for scope and verification.

`storage.gd` writes schema-versioned JSON and original managed assets. Schema 2 originally added
one audio clip and its checksummed WAV. Current [multi-clip audio](multiple_audio.md)
retains that layout for one clip and uses a versioned audio collection for several.
Schema 1 loads with no audio. Both integer
and JSON's numeric representations of supported schema versions are validated.
Scene names
use real SHA256; a fresh immutable cel generation is written per save. Only after
all images succeed is a flushed temporary manifest renamed over the live one.
The previous manifest is copied to project.backup.json before replacement. Loading
validates schema/types/frame bounds, sorted keys, exposure overlap, relative paths,
scene checksum and dimensions, then swaps the active document only on success.
It rejects `..`, absolute paths, URLs and Windows backslashes. Use ordinary local
directories: junction/symlink escape hardening and hostile-input fuzzing are not
complete. Saves are recoverable via backup/new PNG generations; power-loss fsync
guarantees and recovery/autosave UI are not claimed. Old generations remain for
recovery and consume disk; no automatic garbage collection deletes them.

`encoder.gd` detects libx264/AAC, passes an argument array to FFmpeg via nonblocking
pipes, drains errors, exposes cancellation and checks process exit. It never invokes
a shell. New export folders preserve PNGs/logs on failure. Encoding uses exact video
duration, pads audio if supplied, and avoids -shortest truncation. No external source
asset is overwritten. Editor export includes its deterministic WAV mix when a clip
exists, otherwise silent video. UI edits are disabled while exporting and export evaluation
uses a snapshot. Closing while busy cancels before allowing another close.

`audio_track.gd` parses bounded RIFF/WAVE PCM16 mono/stereo files. It rejects unsupported
codecs, malformed chunks and oversized sources before playback. Each clip has exact
integer start_frame/source_in_sample, gain and mute. Original WAV bytes remain intact.
A 48kHz stereo PCM16 project mix is generated from exact rational frame-to-sample
addresses, linear interpolation for resampling, and explicit int16 clipping. Preview
plays that same mix; offline export writes it unchanged before AAC encoding. A peak
waveform describes this project-time mix, including silence. Source files may be up
to 60s/32MiB; mixed sequences are bounded to 60s. Linear resampling and positive-gain
clipping are prototype limits, not mastering-quality processing. Mixing currently
runs synchronously on edit; long/high-rate cases need worker/timing measurements.
The current collection mixer sums overlapping clips before quantization/clipping,
retains16clip/64MiB decoded limits and per-clip project-time waveforms, and feeds
the same player/export mix. All project writers use the collection; the selected
clip accessor is only an editing view. See multiple_audio.md for versioning,
shared Undo/serialization and scoped actual native-scene verification.

Normal play uses Godot AudioStreamPlayer with no loop. User pause stops at the exact
displayed frame; seeking remains silent and the next play starts at that frame's
timestamp. Monotonic clamping prevents tiny backwards visual jumps in the audio clock.
Latency estimates do not establish real speaker/monitor lip sync. A captured app bus
tests actual sample generation; listening and driver/device variation remain owner tests.

Future multiple audio clips, rigs and sequences must evaluate through this same project time;
no independent ticking playback engine may redefine frame identity.

## Requested legacy asset track

The owner now requests Source/GMod and MMD maps/models, with Ragdoll Mover/SMH as
interaction references. tools/asset_audit.py inventories GMA/LZMA/PMD/PMX without
executing embedded scripts. tools/prepare_mmd.py stages native files/dependencies in
a NEW output directory and invokes a factory-started external Blender/MMD Tools
worker, tools/blender_mmd_bridge.py. It retains native files, packed editable.blend,
parameters.json and GLB. The Godot renderer remains standard-format based.

The studio has scene framing and manual FK posing of the tested prepared rigs.
The whole native preservation bundle is not yet copied by managed project save,
so retain the preparation directory. Source decoding now uses prepare_source.py /
blender_source_bridge.py and the same standard GLB loader. See legacy_compatibility.md
for concrete status, parameter preservation contract and source references.


## Workspace presentation

src/studio_theme.gd creates original vector icons and gradient nine-patch surfaces
in memory. No second framework or external artwork. app.gd keeps advanced_controls
and contextual Drawing/Camera/Audio sections. set_advanced only changes visibility;
project keys/cels/audio/renderer and playback clocks have no alternative Simple path.
No project-schema changes or preference writes. Console run.py remains diagnostic;
launch.pyw uses the windowed installed engine and captures launcher diagnostics.
Default boot splash is off; app sets its own title/icon while retaining About credits.


## Recovery

recovery.gd manages bounded discovery, process ownership, checkpoint budget and
resolved fingerprints. app.gd schedules writes between edits and owns restore UI.
New owner sidecars add the exact Windows process creation time as a decimal string.
One scoped read-only handle supplies liveness and identity; different creation
times distinguish reused PIDs. Legacy PID-only records remain readable, unknown
or malformed ownership stays protected, and the app caches its own token. The
native model/world/HAS/journal formats do not change. See startup_recovery.md.
Normal deferred startup tries candidates newest-first through the SAME Storage
and complete renderer/rig preparation used by Open. Failures preserve live state
and are retained in a startup result; success becomes an unsaved copy. Session/
revision/interaction guards prevent deferred work from replacing intervening edits.
No startup dialog or automatic manual-HAS write. Explicit recovery choices remain.
recovery_journal.gd adds a checksummed catalog and at most12 visible immutable
metadata states/session, with shared model/WAV/content-addressed PNGs. It adopts
both legacy generations before rotation. Catalog rollback references are retained
during pruning; only exact journal-owned metadata/preview names are removed.
Storage accepts an archived manifest only when its exact hash filename matches
its bytes, then runs the normal full loader. Native model/world/HAS schemas do
not change. Idle, revision/view-guarded thumbnail callbacks never evaluate the
shot or change drawing data. Advanced history includes resolved sessions; startup
and Simple pending choices do not. See recovery_history.md for remaining limits.
Storage takes optional recovery editor metadata and immutable raster hashes; normal
manual project serialization is unchanged. Backup manifest loading remains an
allowlisted path, also used by automatic fallback. Validation completes before changing the live scene; failed opens
preserve it. Recovery does not redirect Save into the cache. A restored project
requires choosing a normal save folder and keeps its source recovery until saved.


## Source-independent model / pose increment

model.gd owns studio_model_1 data validation, imported base poses, native bone identity,
root and sparse-pose sampling. renderer.gd prepares/binds before replacing the live
model, and uses the same evaluator for preview/export. pose_editor.gd handles FK
selection, local/world gizmos, gesture undo and explicit recording. Guides are canvas
UI only. Environment and model use the same GLB loader; no source-format branches in
posing. Schema3 adds one optional model, with old projects defaulting to no model.
Native report metadata is retained; full native bundle packing is still open.

## Source preparation

source_import.gd provides native model/map pickers, member selection, unit scale,
an extra content mount, asynchronous worker status and cooperative cancellation.
prepare_source.py stages resource-only GMA/legacy archives or direct MDL sidecars /
BSP copies into a new bundle. The pinned SourceIO decoder runs in isolated external
Blender, with deterministic explicit read-only mounts and no Steam autodiscovery.
Our bridge constructs simple PBR materials instead of invoking Source shader nodes.
It loads map prop geometry and records missing dependencies. Completed GLBs enter
renderer/model.gd normally; no source-format condition is present in pose evaluation.
Only the adapter and file-choice routing know about Source. Full details/limits are
in source_import.md. Existing schema3 storage and the master frame clock are reused.


## Installed Source content browser - 2026-10-29

Owner prioritized a searchable in-app library and more complete dependency discovery.
Installed navbar/source-dialog shortcut now open source_browser.gd: asynchronous
location discovery, selected-package indexing, global asset search, model/map filters,
original member/path display, dependency checkboxes, saved extra roots, cancellation
and actual import. Loose/VPK/GMA/legacy-bin members all feed the same GLB/model path.
No separate rig or scene engine. Original gradient UI is reused with a light modal
background; old modal windows hide before replacement dialogs/progress open.

source_content.py owns bounded stdlib indexes and read-only KeyValues/Steam/mount
path discovery; source_browser.py is its data-only worker. VPK import extracts only
the selected MDL/BSP and available sidecars, with CRC checks. An original bounded
GMA provider supplies cross-addon resources selectively. Native Source imports also
honor saved mount settings, not just imports from the new browser. Only selected
asset resources and enabled locations resolve dependencies; addons/SFM default off.
No game configs are edited, scripts executed or assets downloaded.

Research found GMod already includes most CS:S/episode content (Facepunch July2025
update); actual included CSS VPK indexes1361models and chair texture import works.
SFM was initially absent, but its real files/manifest appeared during this session
without an install/download/launch by this assistant. Actual gameinfo search paths
were read and installed SFM content can be explicitly enabled. The private shrine
improves from112/525to524/525props and13to34textures; one corrupt embedded material
CRC remains an explicit error. Both standard GLBs render in Godot and the improved
map saves/reopens. SFM session/DMX animation, procedural rigs/effects, exact live
GMod mount-state emulation, native shading/lightmap fidelity and thumbnails remain
unsupported. Full instructions, primary sources and bounds: installed_content.md.


## Owner-selected HAS project container - 2026-10-29

New project Save/Open use .has, inspectable ZIP v1 around existing schema3/GLB/
studio_model_1 data. Packed is default; linked references standardized local GLB/WAV
files by checksum with actual locate-file prompts. Cels and animation stay editable
and embedded. Cache-only assets externalize beside a linked HAS; relinks preserve
real source locations. Legacy directory Save/Open remains available. Native conversion
bundles remain external, while already-managed native parameter metadata is included.
Broader format adapters remain incremental work, not a new universal importer claim.

HasProject node coordinates a cancellable stdlib worker; bounded ZIP/index/path/CRC/
SHA checks precede normal full project/GLB validation. Atomic temp replacement and
previous HAS backup preserve complete saves; failed open keeps the live project.
Recovery uses HAS identity and restores an unsaved copy. Synchronous snapshot creation
and retained/unbounded global cache remain limits. Details: has_format.md.


## Owner-prioritized FBX / OBJ / glTF adapters - 2026-10-29

Add scene/model accept binaryFBX,OBJ/MTL,glTF2.0. The existing asynchronous import
coordinator dispatches prepare_generic.py and its isolated built-in Blender worker,
with scale, explicit asset root and OBJ up axis. No GMod/SourceIO/MMD dependency for
these formats. Original source/dependencies are staged and hashed, textures packed,
then one self-contained GLB and standard native report feed the existing renderer/
pose/timeline/HAS path. Raw MTL is retained while working maps are confined to
checked staged textures. Native animations are retained in editable.blend, not
automatically loaded into the Studio timeline; no physics/IK/constraints or universal
material fidelity claim. Original spec/workflow remain intact. See common_import.md.


## Voice addendum precedence and first bounded patch — 2026-10-29

Owner supplied the full voice addendum as the next instruction and clarified that it
supersedes earlier decisions. See voice_addendum_audit.md and its comparison matrix;
the preserved original specification is historical where it conflicts. OPEN and
suggested details remain distinct from confirmed requirements. Multiple objects,
world selection, clips, IK, physics and interactive tutorials remain pending.

Direct bone/root manual edits now auto-key at the current frame by default, as the
owner explicitly confirmed; camera keys stay explicit. pose_editor.commit gates this
only for authored transform/pose changes and inserts the key before the same undo
snapshot. Flag changes, import, selection, playback and render do not use that gate.
A drag commits once, Escape restores its original data. Advanced can disable Auto-key
for the existing draft workflow; no project schema or existing key migration occurs.
The preference resets on launch. Existing explicit Record remains useful for holds.
Keys still contain full sparse poses/root; per-channel clips and physics recording
are separate future work. No automatic initial rest key is fabricated.

Main Export defaults beside saved HAS, in a newly created render folder. Unsaved,
recovered and legacy-directory documents choose a destination. Advanced offers a
one-off alternate folder. Picker hides before action. A missing parent reports an
error rather than recreating unavailable paths; successful mkdir must own a fresh
folder before writing. Existing movie, project, PNG, cancel and encoder paths remain.
Godot4.6 DirAccess/FileDialog primary APIs were checked. No new dependency or external
format exporter, native source write, original art change or deployment.


## Continuous goal — empty New world foundation — 2026-10-29

Owner explicitly requested a continuous completion goal; it is active over the full
addendum, not narrowed to this checkpoint. Normal startup now opens a clean black
empty world in Simple Scene/camera mode, no selected object and one stationary
camera key. New icon protects dirty work with confirmation. Original room remains
Advanced > Sample room (also explicit --demo-room for existing film regression
fixtures). Both actions start unsaved projects; clear prior assets, cels, audio,
history, save/link identity and canvas navigation while retaining UI preferences.
File import failure validates before discarding the current document.

No schema migration: scene3d.make_empty authors a small standard GLB with no mesh.
Godot4.6's exporter produced a length header eight bytes longer than its mesh-free
file; direct bounded original GLB authoring avoids this without relaxing validation.
A tiny unused4byte BIN avoids the engine's JSON-only reader warnings. Normal HAS
packing includes this asset and reopens with the original template absent.

Renderer owns a separate editor-only horizontal256x256 plane, recentered near camera
XZ, white unshaded shader with distance8–80unit fade and derivative-based subpixel
fade. It is visible for empty environments, not imported nonempty maps, and never
written into imported geometry. Final capture hides it through the awaited GPU frame,
then restores it. New projects persist optional video.world_background=black; older
projects without this field retain legacy_blue so their output does not silently change.
The optional enum is validated; no general lighting/settings UI exists yet. Shader uses current Godot4.6 documented spatial built-ins:
https://docs.godotengine.org/en/4.6/tutorials/shaders/shader_reference/spatial_shader.html

New tests/new_scene_smoke.gd exercises actual default startup, no selection, stationary
keys, bounded visible grid/black final, free-camera release, independent drawing,
New cancel/confirm, packed HAS portability, exact export PNG and preserved manual
HAS bytes, plus explicit sample-room loading. Full verify.py includes it and probes
its movie. Existing film/UI/recovery fixtures explicitly select --demo-room, while
the new test never does; they are not evidence of default startup by themselves.

Limits: Home/tutorial/recents and world hierarchy/mesh selection are next; still one
environment plus one model. Grid is a visual reference, not a collision floor. Empty
assets are retained as tiny files in output/templates; automatic cache cleanup and
concurrent template naming remain open. No physics, multiple instances or clips
claimed. Existing schema3, .has, cels and native adapter contracts are unchanged.


## World hierarchy, selection and Alt hold — 2026-10-29

Added functional left World tree for current environment/model, selection/framing,
GPU-ID viewport picking, green skinned outline and editor-only hidden ghost. Source
meshes/skins are shared by isolated layer20 selection instances; original layers and
materials stay untouched. Actual World3D comes from find_world_3d() (own_world_3d has
no explicit base world_3d property). Mask camera/helper is not an animated camera.
Mask960x540 updates when selected/picking; click alone reads pixels after render.
Original ID/outline/ghost shaders retain standard albedo alpha cutouts but do not
promise complex native shader semantics. Hidden selected ghost renders through map
occlusion; ordinary hidden child variants stay absent when parent remains visible.

Short LMB selects directly into posing while preserving the view; RMB entity context
and empty-space deselect coexist with4pixel drag navigation. Ctrl+LMB immediate free
camera has priority over handles; combined buttons/middle/WASD remain. New gestures
or asset changes invalidate stale asynchronous picks. Focus/Escape cancels pending
capture. Owner explicitly answered: HOLD Alt reveals all bones, RELEASE hides them.
Selected bone/handles remain. Right-click Reset pose restores imported bone offsets,
preserves root placement and auto-keys as an authored change; not generic humanoid
T-pose inference or physics capture. Show/Hide still static, not visibility keys.

Saved projects open at their sampled shot frame in Scene/camera with nothing selected.
New/Open clear old selection state. Selection is UI-only and changes no schema or
source-format contract. World tree currently lists one environment and one actor;
map roots can select/frame, but transforms/groups/multiple assets are next. See
world_selection.md for controls, primary API sources, limits and measured comparison.
Full verify.py includes41new actual selection checks, prepared native MMD/GMod/SFM,
and now rejects shader errors. Early parse/shader/shared-world issues were fixed.
An authored final comparison differs only at one mesh-edge pixel (3channels,
mean0.00002424/255) after mode reselection; uses existing bounded edge criterion,
not claimed universal pixel identity. Main shot excludes the helper layer explicitly.


## Multi-object persistence foundation — schema4 staged — 2026-10-29

`world_document.gd` defines `studio_world_1`: at most64 `studio_model_1` records,
each with a stable instance ID, kind, parent ID and first presence frame. Maps,
actors and empty groups share the existing local root/pose/native metadata contract.
Validation rejects duplicate IDs, missing/cyclic parents, invalid transforms/poses,
fractional presence frames and noncanonical portable asset paths.

Storage's optional final world argument writes schema4 with one `world.objects`
list, removing old scene/model slots. It validates and hashes every unique source
before writes, copies shared geometry once by SHA256, and resolves all managed
sources on load. Existing video, camera, editable RGBA layers, audio and editor frame
remain separate. Zero-object/zero-layer worlds are valid; earlier schemas retain
their existing constraints. Schema1–3 normalization preserves metadata and legacy IDs.

HAS ZIPv1 is unchanged. Its inventory worker handles schema3/4, unique asset links,
empty worlds and parent-graph checks. Current editor still uses schema3 and safely
refuses schema4 before live-state replacement. The runtime registry, stable-ID Undo,
hierarchical transform/presence evaluation, multi-object selection and all-object
save/recovery/export integration must land before that guard is removed. See
[world_format.md](world_format.md) for fields, bounds and the integration gate.

`verify_world_document.py` verifies package persistence plus actual GLB decoding and
pose bindings in separate reader processes. It does not yet demonstrate simultaneous
multi-object rendering. Final Windows results are in progress_memo.md.


## Multi-object renderer — 2026-10-29

world_runtime.gd now owns detached, fully validated world instances, stable ID lookup,
a topological parent graph and common-frame evaluation. Inventory precedes hierarchy
attachment, keeping child rigs independent. Renderer prepares without altering the
live world, then installs one complete graph and emits one assets_changed signal.
Bad source hashes, GLBs, bone bindings or graph values preserve the previous world.

Each Model instance applies the existing root/pose contract. Its root is attached to
its parent's imported root, so local transforms include that parent's base transform.
Presence gates visibility independently from pose interpolation; parent visibility
propagates through Node3D without changing child data. Final capture evaluates all
instances, excludes reference-only content, reads the GPU and restores preview flags.
The same independent RGBA compositor and encoder render the combined world.

This kernel is connected to renderer.gd, not yet to normal app Open/Save or selection.
Legacy single-slot APIs refuse to partially replace an installed multi-object world.
Existing single-slot app workflows remain valid; schema4 Open guard remains until
stable-ID editor selection/Undo, append importing and all-object recovery are wired.
See world_format.md and verify_world_runtime.py for actual combined-world checks.


## Multi-object editor target and save paths — 2026-10-29

Renderer.active_model resolves a selected stable instance ID without aliasing the
legacy renderer.model slot. PoseEditor uses that resolver for every control. Its
world_object history commands carry object_id and full before/after data; restoration
validates the record/bindings and targets that ID regardless of current selection.
Runtime.snapshot collects current instance dictionaries, including replacements from
Undo. World-axis root manipulation converts through parent rotation/uniform scale.

WorldSelection now builds nested instance rows, stops mesh collection at instance
boundaries and assigns distinct colors for64GPU IDs. Color-distance outline matching
replaces the old two-primary-color dot product. Group outlines cover descendants;
picking still uses each original instance ID. Layer20 helpers remain editor-only.

HAS and directory Save now pass world_state when present. Linked inventories gather
all instance sources, and recovery preflight deduplicates source paths before saving
the complete world. Existing legacy documents still write schema3. Normal schema4
Open remains gated until append imports and atomic New/Open/recovery transitions land.
Editor-control tests install prepared worlds directly, not through a fake product menu.


## Ordinary multi-object workflow — 2026-10-29

Normal Add scene/model appends independent standard records, preserving every prior
map/model/pose/cel/audio/camera key. Managed SHA revisions survive changed originals.
Structural Add/Remove Undo restores whole worlds and descendants. New creates a true
zero-asset schema4 world. Normal schema4 Open/recovery validates every asset and rig
before complete replacement; selection clears. Schema1–3 remain readable with their
original background/render defaults; a later Add promotes and appends existing content.
Empty drawing-less worlds receive empty Rough/Ink templates. Linked cache revisions
externalize to persistent adjacent HAS sidecars; matching originals remain linked.
One JSON numeric-version comparison bug in World.from_project was fixed without
weakening schema validation. Timeline clips, drop/spawn and visibility UI remain next.

Worktree full verify.py exit0: unit24,spikes,editor39,encoder failures,audio24/Dummy,
UI23,recovery14+13,pose45actualMiku,autokey29actualMMD/GMod/SFM,newscene20,selection41,
worlddocument36,runtime43,worldedit37,normalworkflow24. Movies H2641080p24/48frames/2s;
core AAC onset1.000s/RMS5658.30. World/HAS Python combined22, separate world readers,
HAS13+32, actual generic9+41, Source8+6+32 and browser14+28 passed in worktree.
Final canonical verification will be recorded separately; these are worktree results.

New owner scope: Koikatsu/KKS/AI cards and maps, AA2, VRoid2.1.3 .vroid and VRM0/1.
Read-only Illusion card-index tool plus9authored corruption/layout tests pass; all6
supplied cards recognized (Keine is KKS). No direct card/map assembly claimed. Existing
PMX texture completeness and installed tools inspected; originals untouched. See
illusion_import.md. Both VRM files have glTF2 geometry/skins/textures/morphs and version
specific extensions; .vroid is a distinct4entry archive. VRoid installation found at
owner-specified Local/Programs/VRoidStudio/2.1.3. Conversion/render tests are next.


## Direct native MMD and VRM import — 2026-10-29

Add model now accepts PMD/PMX/VRM; Add scene accepts PMD/PMX. Native MMD starts the
installed Blender/MMD Tools worker asynchronously with default scale.08, no manual
conversion step or Source-game dependency. Worker status/cancel and explicit owned
Blender termination preserve current content on failure/cancel. Source originals and
textures are copied/hashed, external native bundles remain. Existing material/IK/
physics and512rig-bone/report limits remain explicit. No converter/tool installed.
VRM0/1 uses new stdlib prepare_vrm.py, preserving embedded geometry/skins/morphs/BIN,
adding facing/scale wrappers without changing source indices, retaining humanoid
maps and native parameters/provenance. VRM0 rotates180Y to canonical+Z. .vroid offers
VRM guidance; its project parser, MToon, springs, gaze, IK and expression controls
remain unimplemented. Each supported import enters the same native HAS world and
pose/Undo/key/HAS/render path. No external-format exporter or separate pose engine.

Worktree native integration passes43checks: actual picker filters/callback, native
Miku PMD/street PMX/both owner VRMs,4independent instances, source metadata/SHA/mtime,
pose deformation/auto-key/Undo/Redo, map root key, packed HAS/exact reopen, separate
RGBA and H2641080p24/48frame/2s export, bad input/.vroid guidance and owned Blender
cancellation. Eight authored VRM tests pass (bounds/resources/version/humanoid indices,
normalization/index preservation/cancel/no overwrite). Full worktree verify.py passes
all existing checks including native rigs, audio/recovery and normal world workflow.
Final canonical commands/results will be appended after saving and verification.

Owner supplied same-character Misaki exports/card. Read-only comparison in
koikatsu_comparison.md: KKBP root30550verts/1637bones/572vertex morphs/no PMX textures,
7separate outfit PMXs and JSON shader/parameter resources; second40852verts/908bones,
426mixed morphs,85rigid bodies/122joints,29textures/one missing. Skeleton identities,
units, outfit assembly and material translation differ. First has52face/44body shape
values in CharacterInfo; its CustomBody/Face shape fields are string placeholders.
Second companion JSON fails strict decoding due trailing comma. Neither is claimed
as a successful native HAS import. Current MMD preflight explicitly reports missing
cf_m_eyeline_kage@330500.png before staging/Blender. Both exceed512bones; a dedicated
KKBP adapter and large-rig work are subsequent tasks. Original PMXs/card SHA/mtime
unchanged after inventory; JSON files read only. No game/exporter launch or mutation.

Native test iterations fixed an inferred type and a picker-title assumption; the
picker now exercises its real selection callback, hides before worker UI and passes
without exclusive-window conflicts. One live test observation handle was lost across
a host interruption: process inventory confirmed no owned jobs remained before rerun.
No duplicate worker launched merely due observation timeout. Known restricted worktree
shader-cache warning remains; physical/tablet/audible/native-fidelity/clean-machine
acceptance remains unclaimed. Continuous full goal stays active.


## File drop and import-at-frame — 2026-10-29

New import_actions.gd connects native Window.files_dropped to viewport hit testing.
Drop one supported3D file over viewport: model-only types route directly, BSP routes
as map; ambiguous GLB/glTF/FBX/OBJ/PMX/archive files offer Model/prop or Environment/map.
Drops start at0 regardless of current playhead. Playback pauses and active edits finish.
Multiple-file drops reject the whole request with guidance (no silently skipped files).
Unsupported/outside/busy drops preserve the world. Physical Explorer drag is not yet
verified; automated tests exercise the actual viewport handler and check signal wiring.
An attempted synthetic Window signal had stale OS cursor coordinates; it is not treated
as a successful OS test. No production hit-testing requirement was weakened.

Right-click timeline opens Add model/prop here and Add environment/map here. Right-click
alone does not scrub; choosing action seeks the clicked frame and opens the ordinary
native picker. Start frame is a per-request value through Source/generic/native dialogs
and async workers, never derived from the eventual completion playhead. Direct Add
keeps default0. Existing schema4 first presence is reused, no migration/new format.
Active object's timeline lane shows a presence band, still not a draggable animation clip.

Worktree import_timing_smoke.gd18checks pass: handler/OS wiring, playback pause/role
chooser, drop0 fromframe32, multiple/outside/unsupported rejection, timeline context/
realpicker callback, frame24 absence/presence, structural Undo/Redo, real VRM worker
keepsframe40 after playhead moves5, packed HAS/fresh New/Open, actual rendered boundary
and exact exported PNG frames23/24. Original GLB bytes unchanged. Optional VRM portion
skips when owner sample absent. Full core regression is being verified separately.
Grounded near-camera spawn, multi-file queue, all-object timeline lanes and structural
animation clips/visibility fades remain next. This is a bounded timing/input increment.

Primary API: https://docs.godotengine.org/en/4.6/classes/class_window.html#signals
Window.files_dropped is the native OS drop signal; no extra UI framework or package.


## Near-camera import placement — 2026-10-29

UI Add model, viewport drop/timeline model actions and Installed browser model imports
now capture the camera view with the import request. The same context crosses native,
common-format and Source preparation. New models receive static root placement near
that view, preserving source geometry, existing objects and explicit camera keys.
Map imports retain native/root placement. Low-level add_model API retains explicit
opt-out for fixtures/prepared-document operations; normal UI uses placement.

Original import_placement.gd computes neutral bounds, queries nearby visible environment
triangles, tries up to9candidate positions, aligns bottom to support where practical
and checks model/prop bounds plus wall-triangle bounds for overlap. Source geometry
and rigs are untouched. Surface budget50000triangles, oversized surfaces skipped and
reported; mesh/material transparency, skinned contact and physical collision semantics
are not emulated. Empty grid uses reference y0 only if in view; high aerial/no-support
views keep visible fallback. If all candidates overlap, import still succeeds with
status/metadata explaining fallback. No physics simulation or invented animation keys.

Initial worktree placement tests15authored checks pass: distant camera, translated
floor, full bounds inside view, independent map/camera/actor data, no implicit key,
second actor avoids overlap, Undo/Redo,9blocked candidates with visible fallback,
aerial fallback, presence24/HAS/export and original SHA. Expanded run18checks also
passes actual prepared gm_construct map query/native floor support and actor pixels
without reframing. Query measured29.483ms, authored import11.516ms in that run; not
a universal latency/complex-scene claim. Native MMD/VRM43integration tests also pass
in worktree after high-level placement wiring. Broader regressions/canonical checks
are recorded after verification. Existing root JSON precision uses Vector3 tolerance
and canonical JSON metadata comparison; initial test had not keyed its aerial camera.

Still missing: physics/IK foot planting, exact collision/mesh silhouette, huge-rig /
huge-scene performance and native material/physics fidelity. Ground query can choose
visible triangles with no native collision flags; budget fallback stays explicit.
No gameplay scripts, asset writes, converters installed or export-back feature.
Primary APIs: Geometry3D.ray_intersects_triangle and Mesh surface access in pinned
Godot4.6 docs; original logic, no engine/third-party code copied.


## Whole-object timeline retiming

object_timing.gd provides source-independent authored-span and bounded-delta helpers.
TimelineView receives stable-ID runtime records, shows collapsed map/model/group rows,
and previews a move without mutation. Release emits the original object snapshot and
delta. app.retime_object compares that snapshot to live data, restores through existing
PoseEditor validation, and records one world_object command. Runtime replacement cancels
gestures by instance token. Active timeline drags defer recovery. Existing Model sampler,
world presence, schema4/HAS and independent camera/cel/audio tracks remain authoritative.
Multiple independently owned animation pieces and gap bridging are the next domain step;
whole-take movement does not pretend to provide split/clipboard operations.


## Independent animation source curves

animation_clips.gd provides pure version2 promotion/split/move/remove/paste/key/range
operations. Model validates both versions and maps project frames to owned source
curves; gaps blend endpoint states under hold/linear/ease. Source keys outside a
piece remain interpolation controls. PoseEditor writes/deletes keys through Model
methods, extending introduction on explicit earlier edits. ClipEditor owns local
clipboard/context operations and restores through the existing stable-ID Undo path.
TimelineView draws/drag-previews individual pieces; Shift-drag delegates complete-
object movement to ObjectTiming, leaving source addresses unchanged. Source GLBs,
master camera, RGBA cels/audio and world hierarchy remain independent.


VisibilityTrack evaluates persistent on/off state and linear rational-time opacity independently of motion. ModelOpacity owns temporary instance-local Standard/ORM material copies for actual Compatibility fades. WorldRuntime propagates parent opacity once; Model/renderer use the same evaluator for preview and export. User controls promote only edited objects to studio_model_3; old record readers remain. See visibility.md.


AnimatedChannels derives a bounded view index over existing pose-piece source curves and independent visibility keys. TimelineView caches expanded descriptors, separates visual row addresses from domain object indexes and clips drawing to visible rows; the pinned ruler shares the same label width. App selects the original rig/bone/frame without changing the view. Optional authored channel hints are stored on ordinary pose keys; animation evaluation remains unchanged.


LimbIK validates native-role/known-name three-joint chains, solves a disposable
Godot4.6 TwoBoneIK3D scratch rig, and returns ordinary pose offsets. PoseEditor
commits a completed gesture through the existing auto-key/Undo path. No solver
remains on the live imported skeleton. BoneLabels uses local exact aliases and
declared humanoid roles; Simple/Advanced label refresh never renames rig identities.


PhysicsRig builds bounded source-independent physical skeleton proxies and captures
engine modifier output into ordinary FK offsets without writing live keys. Jolt120Hz,
CCD, limb-aligned cone/hinge profiles and neighbor exclusions support actual falls/contact. Weighted skin
bounds fit structural boxes, with capsule/sphere fallbacks. PhysicsEditor owns live rigs/map triangle colliders,
temporary pin/kinematic grab anchors and selected-object freeze commands. Model's
unrecorded preview override is transient; ordinary static poses/HAS schema remain.
Physics stops on seek/play/save/export, recovery defers while live, and asset changes
dispose old solver/collider nodes. No implicit live-motion animation bake.

PhysicsSelfCollision compares activation-time oriented box/sphere/capsule proxies
within a bounded connected neighborhood. Local overlaps receive session exceptions,
preventing adjacent fitted volumes from stretching joints against one another.
Body fitting excludes loose/unknown descendants while retaining recognized body
helpers. Original geometry/weights are unchanged; this is collision fitting, not
hair/cloth simulation. Jolt uses four position iterations; see physics.md and
secondary_motion.md for observed limitations and the owner's wind/helper scope.

PhysicsProp adapts unrigged/single-bone models into world-space RigidBody3D proxies.
Bounded mesh convex hulls (dense-mesh box fallback) include the actual current skin
pose. Model's transient live-world root prevents timeline evaluation from resetting
the visual, while source data remains unchanged. Freeze converts proxy world motion
through parent and base_root into the existing model transform; no schema change.
Same-frame preview_transform complements the existing pose draft for animated roots.
PhysicsEditor shares picking/pin-grabbing, validation, stopping and Undo across both
proxy kinds. Nested simultaneously live instances are explicitly unsupported.


PhysicsRecording owns explicit Local/World capture, starts on the next fixed tick,
uses integer tick/frame phase with bracket interpolation, and stages sparse physical
bone/root samples without editing live authored data. Recorded ranges become
ordinary owned animation pieces; atomic multi-instance restore gives one Undo.
Model live pose/root overrides isolate simulation from authored track evaluation.
Normal ticks count only new encoded samples; full candidate validation runs on
Stop or a possible budget boundary. Compact JSON writing preserves existing schemas
and the1MiB read bound. Recovery defers live physics, while pending recording marks
the project dirty and cancellation restores clean state only without other edits.


SecondaryRig derives a bounded source-independent secondary-chain descriptor at
GLB load using exact generated GLTFNode bone bindings, retained node endpoints,
centers and sphere/capsule groups. Existing native GLBs reconstruct it on reopen;
no scene/model/HAS schema changes. SecondarySpring is an explicit experimental
unit-world scratch-skeleton runner producing ordinary FK offsets; it is not
installed on imported rigs or wired to Simple controls. Its initialization waits
for deferred engine configuration before authoritative fixed tick zero. Existing
range-piece/Undo/HAS/movie paths carry experiment-only baked results. See
secondary_motion.md for real-asset evidence, initial transients and next fan/UI/
recording/helper integration gates.


Current fan integration: SecondaryLive wraps optional body simulation and the
scratch spring runner behind the same pose/root/capture/dispose contract. The
PhysicsEditor fixed callback runs before Recording, so secondary output shares
the established rational capture phase. Hair-only capture samples authored model/
parent transforms at fractional frame time; authored storage remains integer.
Airflow collects local directional fields from standard models with validated
studio_airflow_1 metadata. FanEditor uses normal Add/selection/pose/Undo/HAS paths.
The simulation toolbar wraps; no new UI framework or source-specific pose branch.
Activation ramp, force smoothing and capped secondary offsets reduce startup jumps;
these are approximations, not full cloth/contact fidelity. See secondary_motion.md.


Reviewed helper authoring: SecondaryHelperEditor owns a bounded local Python worker,
correctable source-index/skin preview and one atomic world revision. The stdlib
secondary_helpers backend appends weighted joints/inverse binds/VRMC_springBone to
an immutable GLB, retaining old buffer data and native indices. The existing loader
resolves exact engine-generated bone identities; discarded GLTF scene-node references
are skipped safely. Canvas review lines are editor-only. No new project schema or
format-specific pose engine. See secondary_motion.md for limits.


Multi-part additions now use extras.has_secondary_helpers_1 rather than inserting
another native source extension. SecondaryRig parses native data first, then HAS
additions into the same descriptor/ownership limits. Existing VRMC-generated assets
remain supported; VRM0 native chains cannot be shadowed. Worker assessment protects
regions with existing spring-weighted joints; UI offers only unrigged components.
Each immutable revision retains earlier bone IDs/keys and ordered source history.


Manual patch review extends the helper request with a bounded source vertex_mask.
The worker expands UV-seam equivalents, validates one connected triangle patch,
pins every induced cut boundary and traverses only the selected graph. Preview
retains the whole bounded component for accurate source-index box selection while
drawing only selected edges. CanvasView delegates explicitly armed LMB input to
SecondaryHelperEditor; App forwards captured motion/release/Escape and focus
cancellation. Close/New clear the callback. Camera/paint/data paths otherwise stay
shared; no duplicate renderer or native format branch.

SourceShape captures per-source-node mesh bindings/default weights after GLTF scene
generation, using explicit importer tags and exact mesh resources. Model's optional
saved source_shape setting defaults false when absent, true for fresh UI imports.
Prepare validates weights and bounded CPU POSITION mixes without changing live
instances; Model.apply changes per-instance GPU values and cached bounds/positions
only when the setting changes. Shared mesh resources remain immutable. Placement,
map colliders, prop hulls and weighted ragdoll fits read those effective vertices.
SecondaryHelperEditor snapshots actual weights and preserves them across worker
selection/preview/build. Existing whole-world asset Undo and portable storage remain.

BaseShapeEditor is an Advanced-only static setup panel inside PoseEditor. SourceShape
version2 merges sparse absolute overrides with imported defaults or a neutral base.
Validation computes a complete candidate list locally, publishing geometry caches
only on success; apply then updates each bound mesh instance. Existing model
history/restore, world preparation, placement, physics fitting, helper snapshots
and HAS storage all consume that same configuration. No separate expression engine
or per-frame recalculation is introduced. Animated expression channels remain next.

ShapeAnimation now extends that setup into model version4 source-time snapshots.
Root/bone sampling remains shared with shape amounts through the same animation
piece location/gap mapping. Simple opens a small scrolling shape editor; Advanced
base controls still affect static setup. Copy resolves source baselines before
paste, visibility edits preserve version4, bone edits include sampled shapes and
physics capture retains/counts authored shape data. SourceShape caches needed
target arrays/extents, updates GPU weights/conservative bounds per frame, and
computes exact CPU geometry only when requested. This supersedes the earlier
static-only animation gate; see shape_animation.md for versions and bounds.

Model5 supersedes shared expression snapshots for new edits: ShapeAnimation reads
per-piece shape_keys separately from body keys while retaining the same source
time/split/move/clipboard contract. Only pieces containing a target's controls
participate in that target's curve. Expression-only pieces are excluded from body
sampling. Per-target introduction/interpolation and separate draft addresses prevent
unrelated edits changing a curve. Legacy model4 reading stays unchanged; explicit
promotion extracts its old expression snapshots before a new edit. Recording
separates body/shape samples and charges both against existing capture budgets.

Model6 now extends the existing complete Model/piece dictionaries with per-part body
ownership. BodyAnimation is a bridge to BodyCurves, preserving unknown clip fields,
expressions, geometry references and native metadata. BodyCurveRuntime compiles
shared source-frame arrays and sparse overrides once per replaced data dictionary;
Model caches frame samples and derives inspection keys separately. Auto-key uses
the pre-edit baseline and changed IDs; Record includes shared rest controls.
Per-part ranges on growing takes prevent another part changing gap interpolation;
deliberate split/capture fragments retain fixed slice boundaries. Preview/render,
history, clipboard and portable storage all use the same fields. Readers preserve
model1–5 output; body edits explicitly promote. See body_animation.md and progress
memo for actual tested gates, pending scope and canonical installation status.

Lighting is an optional validated video setting, absent=legacy studio illumination.
New empty projects choose unshaded; sample-room fixtures retain studio. Renderer
controls its existing lamp/ambient separately from imported lights. ModelOpacity's
instance-local material layer composes fade and unshaded copies, retaining original
overrides for exact restoration. Registry ownership is still captured before
parenting. Legacy environments receive the same adapter. The normal evaluator,
capture and project-setting Undo share video state; no lighting key/pose mutation
or source-format branch is introduced. See lighting.md for actual scope and gates.

Interactive placement requests also carry transient physics-on intent. App append
captures existing live modes, freezes/rebuilds the standard world and restores
deferred body/secondary starts without stealing selection. PhysicsEditor checks
exact instance root/data/frame and waits for conversion/modal completion. Normal
Save/seek/Undo/New/Open clear requests; saved scenes never rearm simulation. The
same body/secondary solvers handle explicit toggles and import defaults. No live
flag is added to the project or native source. See import_physics.md for scope.

PoseBounds is a separate on-demand view query, combining shared current morph
geometry with native skin binds. PhysicsRig publishes its already captured final
modifier globals through a weak-owner transient skeleton cache; stop/dispose clear
it. Static edits force fresh skeleton globals. Renderer framing uses these bounds,
while import-placement bind queries remain unchanged. No project field, authored
key, source asset mutation or simulation pause is needed. See pose_framing.md.

Camera sampling owns optional per-key near/far distances alongside pose/FOV; old
keys supply the established0.05/2000 defaults. Renderer.view_state/restore_view
captures all four mutable view properties for editor-preserving operations.
Explicit key insertion reads the actual camera projection; temporary framing is
not shot data. Storage validates the optional ranges before writes and before live
Open. A view-changed signal refreshes the hidden Advanced controls without value
callbacks or implicit keys. See camera_projection.md for limits and test evidence.


Tutorials: Home catalog and state-observing first chapters use the ordinary HAS
worker, native world and Storage. Personal lesson checkpoints atomically include
validated editor view/selection as optional editor.lesson_ui, alongside the scene.
Ordinary project opens ignore that field; personal HAS saves do not carry teacher
progress. Previous/Continue restore whole scene then editor state. See tutorials.md.


First-movie lesson v1 adds eleven tasks without shifting either older course.
LessonStore bounds/checkpoint addresses follow immutable per-course counts. Three
boolean observations live inside the same atomic lesson_ui scene snapshot, not
model motion or project schemas. Normal successful export emits a terminal signal;
cancel/failure cannot qualify through stale files. Hints are mouse-ignoring root UI,
excluded from final render, with corner selection and transient collapse.


LayerEditor owns a compact Simple layer dialog and two existing-history command
paths: layers retains shallow order arrays; layer_properties retains name/visible
values plus the original dictionary. Final Drawing.composite remains authoritative
for bottom-to-top order. No model/world/HAS schema change or new rendering path.
Layer edits cancel pending fills; removal charges retained Images. See drawing_layers.md.


Drawing.layer_image caches up to four weak-source derived opacity Images, keyed by
revision/amount. Drawing.touch accumulates dirty bounds, with a whole-image flag
for fill/replacement. Brush and tile Undo pass actual bounds. Existing compositor
remains shared across preview/fill/capture. The separate recovery CPU worker uses
the pure faded operation after resize, never global caches. See layer_opacity.md.


ColorSampler routes Draw tool3/I before painting. Its shared-world SubViewport is
allocated lazily, updated once, read at one-shot post-draw and then disabled. Camera
transform/projection copy is read-only; grid uses editor layer19, selection20 stays
separate. Only one native RGBA8 pixel is composited from current cels. State guards
protect frame/revision/session/view/source/layer/color, dialogs and physics. Node
delete disconnects the pending method and releases its shared world. See color_picker.md.
