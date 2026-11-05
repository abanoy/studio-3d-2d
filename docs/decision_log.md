# Decisions — 2026-10-29

## 2026-11-02 — native iris data baked into a common neutral eye

Use a validated unambiguous native eye frame/iris radius/offset and the installed
iris texture to produce ordinary GLB UVs and opaque PBR color. Stage changes and
touch only matching eye loops. Preserve native eye fields in reports and tell the
user this is a neutral approximation; no implicit gaze/refraction/dilation or
Source shader execution. Missing/ambiguous bindings retain gray fallback with a
reason. Existing saved assets stay unchanged. Source_eyes.md separates actual
native/GLB evidence from the running remaining regression and unfinished fidelity.

## 2026-11-02 — explicit Source texture row boundary

Decode VTF data as before, then reverse image rows once at the Blender pixel
boundary. The codec returns top-down rows; Blender Image.pixels expects bottom-up.
Do not flip mesh UVs or silently rewrite previously saved GLBs/HAS. Actual native
codec/asymmetric PNG controls and an isolated Scout before/after prove the
boundary error. Existing source-family/model contracts and particle PNG path are
unchanged. Eye shaders and broader native material behavior remain separate gaps.
See source_textures.md for proof and affected-regression status.

## 2026-11-02 — installed SFM host independent of GMod

Admit recognized SFM content using a validated installed SFM host rather than
requiring an unrelated GMod installation. Preserve the owner-required GMod check
for GMod assets. Attribute SFM providers to their declaring installation; remove
unavailable GMod fallback paths when using SFM alone. Browser inventory and native
preparation share the context; native scene formats remain unchanged. Arbitrary
extra roots alone do not classify a source as SFM. See sfm_standalone.md for actual
proof, the ten-group affected review and visible pre-existing Scout material
defect. Installation admission does not certify native rendering fidelity.

## 2026-11-02 — explicit system choice and common effect-instance edits

Keep Source PCF discovery opt-in for the existing data index. A modeless chooser
distinguishes basic-operator eligibility from successful material preparation,
retains whole-system refusals and requires explicit Add. One managed canonical
JSON/PNG instance goes through the existing world transaction/Undo/HAS/runtime;
there is no source-family posing engine. Static position, uniform size, timing
and visibility are the first editable controls. World tree entries reopen exact
IDs without misrepresenting a particle as a mesh/rig. Derived linked assets
externalize from managed imports rather than referencing a worker cache.

The panel uses a fixed action footer and preserves untouched stored precision.
Native mount overrides/extra paths reach the bounded worker. Isolated actual
native UI/cold-reader/MP4 tests pass; all eight integrated affected review groups
also exit0 with seven clean private graphical receipts. See
particle_browser.md for exact proof and limitations. Existing renderer/backend
full regression stays attributed to its own frozen snapshot; normal source is
not replaced by development integration.

## 2026-11-02 — explicit common effect scenes and project-clock persistence

Use project schema5/world2 only when the world declares effects; ordinary worlds
keep schema4/world1 and models keep their existing contract. A separate typed
native effect instance references content-addressed canonical JSON+PNG, stable
ID, static uniform root, start/end/trim and visibility. One runtime samples by
rational project time, retains that rate during editing reevaluation and feeds
the ordinary renderer/export path. Older Storage/HAS worker code must reject
new scenes. Shared asset inventory supplies Save, linked references and recovery
budgets so textures cannot be omitted. Bounded preparation is transactional.

Ordinary linked/packed/cold Open and MP4/AAC have focused proof; UI controls,
attachments and richer effects remain unfinished. See particle_scenes.md for
actual evidence and failed development checks. The full current verifier and
separate HAS checks subsequently completed0 on frozen source; normal installed
Studio remains separate.

## 2026-11-02 — actual Source sprite foundation before particle UI

Convert a deliberately supported whole childless native system into versioned
canonical effect data plus PNG; one shared deterministic analytic renderer serves
SFM and GMod Workshop inputs. Refuse unsupported behavior rather than silently
importing a subset of the chosen system. Own seeded random/distribution semantics
and simple additive shaders are an approximation, not Source bit equivalence.
PCF/material/texture handling stays data-only and bounded, with existing optional
decoders; no game/add-on execution or new dependency. Fixed single-image VTF7.2
is intentionally restrictive. See source_particles.md for exact limits and proof.

The opt-in experiment passes11 Python tests and29 writer+27 cold GPU checks with
actual textures and MP4. Ordinary editor/world/Model/HAS formats remain untouched;
do not advertise in-app particle support or copy these files over the verified
normal installation. Future persistence must explicitly version required effect
semantics and prove packing/cold loading before simple browser/timeline controls.
The installed-source backup and verified update remain the separate usable app.

1. **Separate worktree component.** The selected worktree has an older Cloudflare
   snapshot; the original C:\a\Programming\cloudflare includes newer projects and
   a large, separate artist-assistant effort. Read the requested spec there and
   copied it unchanged here. No edits to that checkout or its existing animation app.
2. **Installed stable Godot 4.6, standard/GDScript.** Verified executable version
   `4.6.stable.official.89cea1439`. A newer stable release exists according to the
   official archive, but upgrading is unnecessary for the initial measured slice.
   No .NET SDK/runtime or new dependencies needed. OpenGL Compatibility works on
   the actual Intel Arc 140V GPU. Shader disk cache is disabled for this restricted
   development workspace; explicit log paths avoid a Godot startup failure when its
   normal AppData log directory is not writable. Revisit cache policy before shipping.
3. **Mandatory spikes first.** Real GLB import/paint-isolation/GPU capture and a
   silent 48-frame encode passed before editor assembly. The known-tone audio
   variant was completed alongside the small editor, before any Stage 2 UI work.
4. **Constrained usable slice.** Two layers, pen/eraser, holds, camera keys, editable
   directory saves, silent MP4. Current project UI starts at 1080p/24fps/48 frames;
   no duration/FPS settings UI yet. Code stores rational rates and loaded projects
   support bounded settings; common NTSC numerators are not yet enabled by loader.
   A small flat source layout avoids empty future subsystems. No general scene
   modeling or AI features. User-facing buttons all perform real operations.
5. **External encoder.** Verified the existing FFmpeg build and codecs. Do not
   redistribute this GPL/version3 binary as part of the app without a distribution
   review. The owner can configure the local executable. App license remains undecided.
6. **Safety/recovery baseline.** Immutable cel generations + manifest backup and
   replacement; bounded tile stroke undo; managed source copy with checksum; explicit
   key replacement confirmation. Autosave, recovery UI, cache eviction and complete
   adversarial import handling remain follow-up work. No source archive deletion.

Primary references checked at implementation time:

- [Godot 4.6 GLTFDocument](https://docs.godotengine.org/en/4.6/classes/class_gltfdocument.html): runtime buffer import, scene generation, fixture export.
- [SubViewport](https://docs.godotengine.org/en/stable/classes/class_subviewport.html): isolated full-HD scene rendering and texture display.
- [Godot 4.6 Image](https://docs.godotengine.org/en/4.6/classes/class_image.html): RGBA raster and blend operations.
- [Godot 4.6 OS](https://docs.godotengine.org/en/4.6/classes/class_os.html): independent encoder process, nonblocking pipes and cancellation.
- [Godot license](https://godotengine.org/license/) and [FFmpeg license](https://ffmpeg.org/legal.html): component notice/distribution boundaries.
- [FFmpeg manual](https://ffmpeg.org/ffmpeg.html): rational input framerate, image sequence encoding and explicit output duration.

These APIs informed integration; no third-party tutorial code, models or painting
algorithms were copied. The brush uses elementary distance-to-segment geometry.

## Stage 2 continuation — audio

7. **One clip first.** Added PCM16 mono/stereo WAV (8–96kHz, <=60s/32MiB), frame
   placement, sample-based source trim, gain/mute, waveform and audio undo/removal.
   A 48kHz stereo project mix drives both playback and export. No new dependency.
   Source WAV stays byte-for-byte unchanged; source display name survives managed copies.
8. **Schema 2.** Audio metadata/assets require a version bump so the old app will
   not silently save away audio. Schema 1 migrates as silent; tests reopen after
   clearing live state so preserved memory cannot mask a failed load. A Godot JSON
   numeric-type comparison issue was caught and fixed during migration testing.
9. **One time authority.** With hardware audio, use playback position plus time since
   last mix minus output latency, monotonically clamped to avoid tiny backwards jumps.
   With no clip or Dummy driver use explicit silent monotonic fallback. Visual frames
   drop under load; playback ends at the sequence boundary. No audio scrubbing yet.
10. **Measured limits.** Use simple linear resampling and bounded synchronous mixes
    for this short-clip prototype. Clamping can clip positive gain; no hidden limiter
    or normalization. More channels/formats and background mixing come after usability
    evidence. Autosave/recovery remains the next focused increment.

Verified primary audio references: [AudioStreamWAV](https://docs.godotengine.org/en/4.6/classes/class_audiostreamwav.html),
[AudioServer](https://docs.godotengine.org/en/4.6/classes/class_audioserver.html),
[Godot audio synchronization](https://docs.godotengine.org/en/4.6/tutorials/audio/sync_with_audio.html).
The synchronization tutorial labels itself as potentially outdated; tested APIs,
actual bus capture and decoded export were used as implementation evidence.

## Owner-requested compatibility and interaction references

11. Source/GMod maps/models and MMD environments/characters are now an explicit
    owner request, with GMod as the primary manipulation reference. Started with
    read-only Source container audit and tested external MMD preparation; no rewrite
    of the renderer or automatic add-on execution. All original assets remain intact.
12. GLB is the renderer interchange, while native/packed Blender data and a loss/
    parameter report remain part of the preparation bundle. Full native parameter
    persistence inside studio projects is pending; a skeleton's presence is not a
    claim that pose controls exist. Materials use a documented PBR approximation.
13. Ragdoll Mover informs gizmos/axis/selection controls; SMH informs explicit key
    recording and typed modifier channels. Their Lua is reference material only.
    SheepyLord's importer is an optional GMod bridge reference. Direct MMD preparation
    avoids imposing a mandatory Source port; no renderer hook or new AI dependency.
    Reference revision/license evidence and remaining decisions are in
    docs/legacy_compatibility.md.


## 2026-10-29 — Simple presentation over the complete scene

Owner requested Simple by default with an Advanced toggle and XP/early Mac OS
inspired gradients. Use the same project structures, evaluator and export code in
both modes; only control visibility changes. Keep contextual task controls in Simple;
precise numeric/cel/audio/encoder/debug controls in Advanced. No feature migration or
separate simplified project schema. Defaults reset to Simple at launch, with no
project-dirty change when toggled. No saved preference yet.

Use original SVG paths rasterized in memory plus nine-patch gradient theme surfaces,
not a downloaded icon set or a second UI framework. Godot's splash is disabled;
startup uses a windowed Python/engine route with diagnostics on disk. Credits remain
in About. These official API references were checked, without copying their examples:
[StyleBoxTexture](https://docs.godotengine.org/en/4.6/classes/class_styleboxtexture.html),
[Image SVG loading](https://docs.godotengine.org/en/4.6/classes/class_image.html),
[boot splash configuration](https://docs.godotengine.org/en/4.6/classes/class_projectsettings.html#class-projectsettings-property-application-boot-splash-show-image),
and [viewport input](https://docs.godotengine.org/en/4.6/classes/class_viewport.html#class-viewport-method-push-input).


## 2026-10-29 — Owner camera gestures

Adopt LMB pan/translation, RMB yaw/pitch, MMB dolly, and LMB+RMB roll in Scene.
Combined rotation means roll about the view axis, not orbit around an unimplemented
selection/pivot. Draw keeps separate paint/pan semantics. Input uses held-button
masks so releasing one button resumes the remaining gesture; captured motion and
releases continue globally. Escape/focus/mode changes release the mouse. Translation
uses camera-local axes; RMB yaw is world-up and pitch local, preserving existing roll.
No old pitch clamp, allowing free orientation; quaternion is normalized after look.
Only explicit key insertion changes the saved shot. No remapping/sensitivity UI yet.


## 2026-10-29 — Separate recovery, explicit restore

One process-owned recovery session per opened/restored project, 60s default interval.
Atomic existing manifest write/backup path is reused. Recovery editor metadata holds
origin, revision and timestamp, without a schema bump; older schema2 readers ignore
it. Cels use immutable pixel-hash names plus load-time pixel checks only in recovery.
Normal project saves keep generation paths. No automatic replacement on recovery:
restored state is dirty with no save path until the owner chooses one.

Keep current/previous recovery choices and old native files. Resolved notices are
fingerprint-bound, so a later snapshot becomes pending again. Process-ID checks hide
live writers; PID reuse may hide an abandoned session. A conservative global512MiB
preflight budget limits growth but is not an atomic multi-instance quota. No cache
removal, real fsync/power-loss guarantee or background/asynchronous writer is claimed.
An initial demo starts clean, avoiding recovery copies for an untouched sample room.
Ctrl+LMB free-camera input preserves the owner's other camera gestures.

Primary API references checked: [AcceptDialog](https://docs.godotengine.org/en/4.6/classes/class_acceptdialog.html)
and [HashingContext](https://docs.godotengine.org/en/4.6/classes/class_hashingcontext.html).
No external recovery or hashing package, vendor code or artwork is imported.


## 2026-10-29 — Shared model, manual FK before physics

Owner explicitly prioritized imported MMD posing with GMod-style controls and one
standard model contract shared with future GMod adapters. Add one optional character
beside the environment, using GLB + source checksum/native IDs + project overrides.
Do not create a parallel MMD pose engine. Native parameter report stays as metadata;
full native bundle and full native semantics are not implied by the common format.

Store a working draft separately from explicit pose keys. With no keys a pose is
static; once keyed, preview/playback/export use recorded poses, with the current
draft previewed only in Pose mode at its frame. Save/recovery keep that draft.
Include root transform in pose keys. World edits convert through parent transforms;
quaternion slerp avoids Euler interpolation flips. Root scale is uniform only.

One gesture is one command, Escape cancels, existing-key replacement asks. Reference
exclusion applies only to final capture. Import/binding validation precedes live scene
replacement. Schema3 is required so an older reader rejects rather than loses models.
No new framework, native add-on, imported Lua, physics engine or downloaded rig.


## Source compatibility increment - 2026-10-29

Use a pinned SourceIO5.5.5 source cache in isolated external Blender rather than
adding a second renderer or pose engine. Our own adapter stages only resource files,
mounts known content explicitly and builds simple embedded PBR materials. Model
bones/weights/default bodygroups and map geometry/props become standard GLB; native
resources/parameters and an editable Blender intermediate remain together outside
the managed project. UI file pickers invoke the worker asynchronously and replace
assets only after success; cooperative cancellation terminates its Blender child.

Source scale defaults to the decoder constant0.01905 and is configurable. Maps
offer a player-start navigation view; recording a shot stays explicit. Compiled tool
surfaces are removed. No native shader proxy, physics, gameplay, sequence or Lua
execution. Missing mounts produce visible warnings; no automatic asset download.
Full native bundling, live bodygroup/flex UI, VMF and sky/lightmap fidelity remain open.


## Installed GMod / Workshop requirement - 2026-10-29

Owner now requires an existing local GMod installation for native import. Before
staging or Blender startup, preparation checks gameinfo SteamAppId4000 and the
GMod content VPK. Studio supplies/downloads no game or Workshop add-ons. Default
game root is C:/Program Files (x86)/Steam/steamapps/common/GarrysMod; native file
browsing starts at C:/Program Files (x86)/Steam/steamapps/workshop/content/4000
when present, falling back to the game's content directory. The Source dialog
offers editable roots, folder pickers and a Workshop file shortcut, with paths
saved separately in output/source-paths.cfg. Custom library CLI/environment
overrides are available. GLB/MMD and existing standard projects remain independent.

Workshop is currently a browsing root; import reads the chosen archive and explicit
content mounts, without unpacking or merging every subscription. No game launch,
Steam authentication, installation, subscriptions, downloads or game-folder writes.
The private output caches/test assets must remain outside future public releases.


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


## SFM-focused compatibility increment - 2026-10-29

Supersedes old dependency-checkbox-only defaults: installed SFM declared search paths
and GMod loose/GMA add-ons now participate automatically, after own resources and
with contextual base-game precedence. Saved exclusions still apply to browser and
native-file imports. Custom SFM mods and Workshop aggregate/numbered loose/VPK/GMA
layouts are discovered; no subscribed SFM files exist on this machine yet. Missing
Workshop availability is visible in the browser. Unsupported or oversized fallback
GMA packages are reported separately, requested corrupt resources still warn/fail.

A narrow VTX-buffer error normalization permits the pinned decoder's existing extended
layout retry for actual SFM HWM assets. No vendor cache modification or new dependency.
Native bind data remains authoritative: reference-pose experiments did not produce a
reliable neutral pose and were removed. HWM Scout needs a manual90degree root-X
rotation through existing Advanced controls. No generic axis inference, native SFM
sessions/DMX playback, procedural rigs, physics or shader-fidelity claim. Detailed
inspection, behavior and verification instructions: installed_content.md.


## Verification of SFM and automatic dependency increment - 2026-10-29

Actual canonical tests: verify_source_browser.py exit0 (14content fixture cases,
28real UI checks, included CSS model/texture, Workshop Reimu, gm_construct and
a separate GMA supplying a real missing material). verify_sfm.py exit0:13real
checks for library selection, extended VTX Scout83bones/5textures, arm deformation,
undo, shared project/cels, save/reopen and MP4, plus actual SFM box BSP import.
Native selected inputs/gameinfo hashes remain unchanged. Material provenance
confirms tf_movies VMTs and tf textures without manual dependency checkboxes.
SFM movie: H2641920x1080,24/1,48frames,2.000000s, exact exported frame24 agreement.
Actual upright Scout and map PNGs inspected; native eye/material rendering remains
approximate. The fixture explicitly applies Scout's documented90degree root-X
bind-axis correction; automatic orientation is not claimed.

Read-only inventory:8414model files and81maps across available SFM roots, not a
claim every listed file converts. Neither supported SFM Workshop content folder
exists yet. Workshop aggregate/numbered loose/VPK/GMA layouts, contextual order
and persistent exclusions are fixture-tested; no real subscribed SFM item test.

Automatic fallback exposed quadratic provider-membership work. Replaced it with
identity-set membership, fast GMA index misses and a per-import negative cache
invalidated by provider-count changes (including a newly mounted BSP pak). A slow
owned test run was stopped/restarted after this fix; final tests use the saved
code. Unrelated unsupported/oversized GMA indexes produce separate mount warnings,
not false missing-material dialogs. Native-resource CRC failures remain visible.

Canonical verify_source.py also exits0:8archive+6installation fixtures,32actual
native UI checks, original input hashes, cancellation/owned Blender termination,
model/map H2641080p24/48frame/2second exports and exact frame24 agreement. Existing
map reimport tolerance reports6changed color bytes across2pixels (mean0.000063/255).
Canonical full verify.py exits0:unit24, GPU spikes, editor39, encoder failures/cancel,
audio24/Dummy, UI23, recovery14+13 and pose44 with actual Miku. AAC onset1.000s,
RMS5658.30 retained. No native shader fidelity, physical-input/tablet, audible
listening, all-layout, clean-machine or hostile-file certification is implied.

Fresh canonical default-only shrine conversion also exits0, without mount settings,
content paths or an explicit plan:524/525props,718meshes,34textures,83resolved SFM
resources and51672788byte GLB. One embedded-material CRC failure remains visible;
5unsupported/oversized GMA fallback packages are recorded separately. Bundle:
output/compatibility/shrine-automatic-fallbacks. This is actual automatic cross-game
resolution, not just the prior explicit-SFM-mount experiment. Native shaders and
all other documented Source rendering limitations remain unchanged.


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


## HAS verification checkpoint - 2026-10-29

Final canonical tests: verify_has.py exits0 with12Python container fixtures and
22real Godot checks. Packed projects reopen after original GLB/WAV locations move;
linked files omit those assets, locate3missing files through actual prompts/pickers,
remember relocated originals and back up previous saves. Cancelled save/corrupt open
preserve existing files/live project. Recovery records HAS identity, and both recovery
and HAS backup restore unsaved copies. Actual default Save dialog was inspected.
Prepared GMod, SFM and MMD projects preserve GLB checksums, pose keys and native
metadata across packed HAS save/reopen. Synthetic fixture recovery is isolated from
normal sessions; previously created owned test notices were resolved without deletion.

Reopened HAS exports H264/AAC1920x1080,24fps,48frames,2.000seconds. Frame24 equals
the reopened project's preview capture exactly; decoded known-tone onset1.0000417s
matches the frame24 offset within2samples. Independent GLB reimport differs in24color
bytes (mean0.000142/255), within the existing tightly bounded edge tolerance; asset
bytes/checksums remain exact. This is analytical audio verification, not listening.

Canonical full verify.py also exits0:unit24,spikes,editor39,encoder failure/cancel,
audio24/Dummy,UI23,recovery14+13,pose44 actualMiku; existing AAC onset1.000s/RMS5658.30.
Native verify_source.py exits0:8archive+6path fixtures,32real checks, GMod model/map
H2641080p24/48frame/2second movies and matching preview/export frames. An initial
camera fixture assumed2render frames sufficed for delta-time movement; it now waits
up to250ms for the unchanged >0.001unit threshold. One intermediate audio drawing
check failed once; isolated24checks and final full suite pass. Startup diagnostics
remain; no production drawing behavior changed or physical-input reliability claim.

HAS project/backup files and linked sidecars are excluded from source Git by default.
Cache cleanup/global quotas, simultaneous-writer locking, real disk-full/power-cut,
large-scene latency and clean-machine tests remain open. Original native conversion
bundles and broader format adapters remain separate work. No deployment/publishing,
new install, external asset upload or native source edits occurred.


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


## Common-format verification checkpoint - 2026-10-29

Final canonical verify_generic.py exits0:9Python dependency/preflight fixtures and
41real Godot checks. Authored textured two-bone assets exercise FBX7400 with separate
and embedded images, glTF2.0 with external and data-URI resources, and OBJ/MTL with
space-containing texture names. Default imported height2units, exact default scale1,
chosen OBJ scale2/height4, native Tip selection, visible skin deformation and exact
pose undo all pass. OBJ environment replacement preserves the independent actor,
drawings and shot keys. Packed HAS reopen and camera/pose/cel MP4 succeed; H264
1920x1080,24/1,48frames,2.000s, exact frame24 preview/export bytes. Original fixture
files/hashes/inventories remain unchanged. Missing glTF buffers fail before staging/
Blender; ASCII FBX rejection and cancellation preserve current work.

Inspection found Blender's glTF bone-display Icosphere in the imported scene. The
adapter now excludes custom bone-display objects from GLB while retaining them in
the editable Blender rig. Tests inspect actual exported GLB JSON as well as reports:
one source mesh, without helper geometry. File-image counts exclude renderer-only
images. Actual dialog/rig PNGs inspected. A bounded scroll fixes an oversized import
dialog; corrected a SpinBox grid default to exactly1. In-process preview preference
avoids Blender thumbnail writes. The installed exporter supports AUTO/JPEG/WEBP/NONE,
not a PNG enum; AUTO is used and verified with the actual assets.

Canonical full verify.py exits0:unit24, GPU spikes, editor39, encoder failure/cancel,
audio24/Dummy,UI23,recovery14+13,pose44 actualMiku; AAC onset1.000s/RMS5658.30 retained.
Canonical verify_has.py exits0:12container fixtures/22actual checks, packed/linked/
relink/recovery/native metadata plus H264/AAC; onset1.0000417s. Canonical native
verify_source.py exits0:8archive+6path fixtures,32real checks and model/map1080p24/
48frame/2second movies. After helper exclusion, the affected generic and HAS suites
reran successfully. No new production renderer/timeline/storage branch or dependency.

Binary FBX only; native clips are retained in editable.blend rather than mapped to
Studio keys. OBJ is unrigged. PBR/material/constraint/physics/morph and exporter-
specific losses remain documented. Stale author-machine FBX texture paths try a
same-named image beside the source; unresolved images fail rather than silently
reading arbitrary external locations. Global texture searches are not performed.
No universal asset/extension/fidelity, hostile-file, clean-machine or physical-input
certification. Source originals/spec/art unchanged; no tool installation, game/
Workshop download, publishing/deployment, or unrelated project edits.


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

**Owner requirement:** several maps and models must coexist in one standard world,
with editable root transforms and portable HAS saves. Source ecosystem must not
select a separate runtime/pose representation.

**Engineering decision:** version project data to schema4 inside existing HAS ZIPv1.
Use one world list of existing studio_model_1 records, extended with kind, parent ID
and first presence frame. Instance identity remains independent of asset checksum;
shared GLBs are stored/relinked once. No new mesh format or native asset extension.
Legacy schema1–3 normalization keeps original metadata, poses and source identity.

**Staging boundary:** keep ordinary editor Save at schema3 and reject schema4 Open
before changing live state until the entire runtime, selection, Undo and recovery
handle every instance. Enabling partial multi-object Open would risk silently losing
objects on Save. Storage/package validation is usable and tested independently; it
is not labelled completed multi-object editing.

**Retained limits:**64objects,128MiB perGLB,1MiB project metadata,512MiB HAS archive/
expanded budget,128entries,240frames and32cels. No giant-world performance promise.
Presence is separate from static visibility/pose data; visibility fades and motion
clips remain later increments. No OPEN clip-gap/fade-override decisions were invented.

Actual canonical verification and prior test corrections are recorded in
progress_memo.md; [world_format.md](world_format.md) defines the next runtime gate.


## Multi-object runtime gate — 2026-10-29

Continue the staged schema4 integration using the existing Model and Renderer. A
prepared runtime owns separate instance nodes/rigs; parent transforms, first presence
and static/reference visibility evaluate for every object. Prepare all assets and
bindings before replacing any live content. Do not identify editable instances by
array index or source filename; the registry uses stable instance IDs.

Parent objects own child instance roots after each rig has been inventoried. This
preserves the existing imported-root/base-transform contract and avoids absorbing a
child's skeleton into the parent's pose channels. Runtime GPU sharing is not claimed.
Final capture restores preview visibility after readback, keeping reference exclusions
from persisting as accidental editor hides. Existing single-slot renderer calls reject
partial updates to a multi-object world. UI schema4 guard remains until the rest of
the editor can preserve and edit every object; this is a temporary integration gate.


## Stable instance targeting and multi-object editor saves — 2026-10-29

Keep legacy model state separate from the new instance registry. Active selection
is an ID resolved by the renderer; source filename/checksum is not an edit target.
World pose/root history stores stable object_id, so Undo can restore an unselected
object without moving the user's current selection. Finish a drag before switching
its target. Pose commands may change pose/root/flags/presence/name/metadata, but may
not replace geometry or reparent; those need structural world commands later.

Use64distinct GPU ID colors and distance matching for picking/outline. Each mesh
belongs to its own instance, even under a parent map/group. Parent selection can
outline descendants without changing the IDs used for picking. Original materials,
skins, render layers and final shot remain untouched by selection helpers.

Wire all-object HAS/directory/recovery writes now so prepared-world editor work cannot
silently save only one slot. Retain the normal schema4 Open guard until append import,
New/Open replacement and recovery restore transitions are implemented. This is staged
integration, not a new user-facing limit or the requested finished workflow. No OPEN
clip-gap/fade/physics choices were decided. Next must enable ordinary multi-object
creation and reopen safely; do not leave this gate as the final product behavior.


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


### Ordinary workflow and compatibility final verification — 2026-10-29

Saved canonical tests all exit0: full verify.py (unit24,spikes,editor39,encoder fail/
cancel,audio24/Dummy,UI23,recovery14+13,pose45actualMiku,autokey29actualMMD/GMod/SFM,
newscene20,selection41,worlddocument36,runtime43,worldedit37,normalworkflow24);
verify_has.py13Python+32app; verify_world_workflow.py24 plus AAC timing;
verify_world_document.py22Python+36Godot and four separate readers; verify_avatar_samples.py19
plus source SHA/mtime and FFprobe; test_illusion_cards.py9. World packages preserve
5packed/5linked objects with3unique relinks,0empty and9actual native records. Core AAC
onset1.000s/RMS5658.30; HAS and recovered normal-world AAC onset1.0000417s. Movies
H2641920x1080/24fps/48frames/2s; preview/export PNG checks pass. Normal workflow recovery
rebuild differed15channels/mean0.00008379 on255scale in worktree, within existing
<=384/mean<.002 bound; same recovered preview/export is exact. Original inputs unchanged.

Worktree reconversion regressions also passed: generic9+41, Source8+6+32, browser14+28
and separate-addon texture, SFM13/native Scout/map/cross-mod textures. These reconversion
wrappers were not rerun canonically in this patch; full canonical tests exercise actual
prepared native rigs. Final logs have no script/shader errors/leaks; known worktree
shader-cache warning remains. Physical mouse/tablet, subjective sound/native appearance,
clean-machine/large-world/full-disk/power-cut acceptance remain unclaimed.

New owner clarified native HAS destination again: external ecosystems translate INTO
one standard; external-format model exporters are nonpriority. VRM0/1 actual geometry,
FK skinning/auto-key/Undo, morph storage, coexistence, packed HAS and movie test passes;
native VRM picker/materials/springs/gaze/expressions and .vroid parser still pending.
Both VRM captures inspected:0.x faces away under same view, so normalize versions in
the real adapter. Six KK/KKS cards have readable indexes and unchanged SHA/mtime; Keine
is Sunshine. AI layout is fixture-tested only. No direct card/game-map/AA2 support claim.
Existing Hecatia modelBL PMX has complete listed textures but actual isolated conversion
warned invalid mesh and timed out180s in GLB export. Model/textures/toon source hashes
verified unchanged afterward. No retry or successful import implied. All game apps and
plugins remain unlaunched/unmodified. No installation/upload/deployment/publishing.

114tracked canonical source files matched prior checkpoint768d6d2e9 before writes.
Focused files saved with backups, expected-content checks and SHA equality under
output/checkpoints/2026-10-29-222614-world-workflow and follow-up notes. New tests use
private ignored outputs, never redistribute owner/game assets. Full goal stays active;
next connect Explorer drop/presence/spawn, native MMD/VRM adapters, then timeline clips,
visibility/fades, IK/physics/capture and tutorials. Illusion assembly remains a separate
bounded adapter investigation. No new native asset extension or export-back subsystem.


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


### Direct native import final verification — 2026-10-29

Actual CANONICAL runs all exit0: test_vrm_import.py8, test_asset_audit.py8;
verify_native_import.py43real checks, including actual live owned-worker cancellation
proved by the converter's Popen state and joined exit code; full verify.py
(unit24,spikes,editor39,encode fail/cancel,audio24/Dummy,UI23,recovery14+13,pose45actualMiku,
autokey29actualMMD/GMod/SFM,newscene20,selection41,worlddocument36,runtime43,worldedit37,
normalworkflow24); verify_generic.py9Python+41actual FBX/OBJ/glTF checks;
verify_source.py8archive+6path+32actual Source checks. No final Source-browser/SFM wrapper
rerun for this importer patch; their prepared rigs remain in full core regressions.
Native direct-import demo: output/native-import/run_686808/native.has. Actual Miku PMD,
street PMX, VRM1 and VRM0 coexist; original model/texture SHA/mtime unchanged. Native
HAS reopen and exported frame24 are exact. Full-HD movies H2641920x1080,24fps,48frames,
2seconds. Core AAC onset1.000s/RMS5658.30 retained. VRM0 normalized front-facing PNG
visually inspected; MToon/native behavior remains approximate/absent as documented.

Saved18focused files after123canonical tracked files matched checkpointe0f029ce4.
Backups231254-native-import,231421 cancellation diagnostics,231739 notes/label follow-up.
Final change after the broader functional runs is cancellation wording only, making it
correct for stdlib VRM imports too; no further runtime behavior changed. Test wrapper
now always runs8authored VRM fixtures before optional private native samples. Native
MMD requires installed Blender/MMD Tools/Python3.11+; existing Python3.13.1 used here.
No package, game, plugin or executable installed; no art/game source writes or upload,
public release/deployment or external-format exporter. Worktree restricted shader-cache
warning remains; final canonical logs contain no script/shader/exclusivity errors/leaks.
Physical mouse/tablet, audible/native-fidelity, clean-machine, large-rig/large-scene,
hostile-file, full-disk and power-cut certification remain unclaimed.

Misaki comparison also identified a raw native card stream stored under the misleading
name card_data.png in the KKBP export; it is not a PNG, has no preview and includes
KKEx. All corresponding block hashes differ from original Kouhai.png. Differences
are recorded without claiming the cause or changing sources. KKBP outfit/material
assembly and both oversized rigs remain unsupported in this increment. Full goal
stays active: next visible drop/spawn/presence and timeline editing, with large-rig /
KKBP work as a separate adapter increment. Keep one native HAS representation.


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


### Import timing final verification — 2026-10-29

Final CANONICAL verify_import_timing.py exit0:20checks, real optional VRM worker,
packed HAS/frame-boundary PNG agreement and ffprobe H2641920x1080/24fps/48frames/2s.
Added pending-import rejection and actual screen/window/stretch coordinate mapping.
Native Windows OLE source ignores its supplied point and invokes file callback only;
OS-drop handler now queries current DisplayServer screen cursor and applies the
actual CanvasItem screen transform, avoiding cached viewport mouse coordinates.
Primary code reviewed: https://github.com/godotengine/godot/blob/4.6-stable/platform/windows/drop_target_windows.cpp
API: https://docs.godotengine.org/en/4.6/classes/class_canvasitem.html#class-canvasitem-method-get-screen-transform
No engine code copied. Physical Explorer drag, arbitrary DPI/focus and archive-virtual
files are not certified by this synthetic handler test. Real ordinary local files are
the intended route. Single-file drops only; no silently skipped batch contents.

Canonical full verify.py exit0 (unit24,spikes,editor39,encoder fail/cancel,audio24/Dummy,
UI23,recovery14+13,pose45actualMiku,autokey29actualMMD/GMod/SFM,newscene20,selection41,
worlddocument36,runtime43,worldedit37,ordinaryworkflow24). verify_native_import.py
8Python+43app exit0; verify_generic.py9+41 exit0; verify_source.py8archive+6path+32app
exit0. Core AAC onset1.000s/RMS5658.30; all movies retain1080p24/48frames/2s. The final
OS-coordinate-only correction followed the broad core run; affected timing20 reran
canonically afterward. No other behavior changed after these checks. Original assets
unchanged. Canonical logs no script/shader/leak/exclusive errors; restricted worktree
shader-cache warning remains. No physical-input/tablet, subjective hearing/native
fidelity, clean-machine, hostile-file/full-disk/power-cut certification.

128tracked canonical files matched e7627d3c8 before save. Saved12focused files with
conflict guards, backups232501-import-timing and232752screen-coordinate follow-up,
plus final notes; byte/SHA equality checked against retained worktree. No deployment,
installation, game/Steam action, source-art change, external upload or format exporter.
Full goal ACTIVE. Next near-camera grounded spawn and object/clip timeline editing;
keep visibility/fades/IK/physics/capture/tutorial/recovery/render scope and large-rig/
KKBP importer work. Independent native asset-extension choice remains OPEN.


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


## Whole-object timeline retiming — 2026-10-30 0000 EDT

Owner clarified gap semantics: two recorded blocks should try to connect through a
gap; a lone block is absent before its introduction unless explicitly corrected,
and its last state persists afterward. This supersedes the optional question's
suggested hold default. Visibility stays independent. Multiple blocks are not yet
implemented, so this patch preserves existing key interpolation rather than adding
a different gap rule.

First bounded implementation shows all64possible object rows and moves each complete
authored take: first presence, every root/bone key and draft editing address. Existing
schema4/HAS data suffices. The draft address clamps independently; keys never drop.
A single gesture yields one stable-ID Undo command, cancels on Escape/focus/world
replacement and rejects stale same-object state. Parent/child timing stays independent.
Separate splitting/clipboard/animated-channel and visibility/fade work remains required.


## Human-part bone-name estimates — 2026-10-30 0004 EDT

Owner explicitly chose a small dictionary of known parts. Estimates live in an
editable local JSON file, with left/right and numeric suffix composition. English
labels are marked ≈, originals are available in tooltips/search, and unknown names
remain native. This is presentation, not a rename or humanoid/IK inference system.
Native IDs remain authoritative, including repeated/ambiguous display names.


## Independent animation pieces — 2026-10-30 0037 EDT

Owner confirmed connecting motion between recorded pieces, absence before first
introduction unless explicitly keyed earlier, held final state, and independent
visibility. Piece2 records preserve full source curves with source-time slices rather
than inserting approximate boundary keys. Each split/copy owns its own curve so later
manual edits cannot change siblings. Versioned studio_model_2 format protects against
old readers silently ignoring clips; the world/HAS container stay schema4/ZIPv1.

Chosen bounded first policy: half-open nonoverlapping pieces; paste onto identical
GLB source assets; direct edits extend their owning/preceding piece and earlier keys
correct introduction. Source addresses can shift to extend before zero without
changing later original motion. No ripple/stretch/loop/cross-rig retargeting. Those
are reversible future features, not accidental default behavior.32pieces,241keys per
curve,2048total keys and existing1MiBmanifest bound. Static hidden flags/parents remain
authoritative; animated visibility/global fades remain next.


Clip authoring refinement: directly extending a fixed source slice could expose
cropped control keys or change the slice's later interpolation. Outside manual keys
now create an independently owned authored take; additional keys grow that take,
while fixed/split/cropped neighbors retain exact samples. Source shifts only apply
to complete newly authored ranges; splitting or deleting boundary keys clears growth
eligibility. Added near-boundary/existing-motion preservation and saved-growth checks.
Clipboard stores rational FPS and rejects mismatched destination clocks. Version2
requires first presence and enforces it even through standalone Model.apply.


## Persistent visibility — 2026-10-30

Owner-confirmed global300ms default/0cut and persistent state are implemented independently of motion pieces. Engineering choice: fade begins at the keyed timestamp, reversal starts from sampled opacity, repeated same-state keys do not restart, linear transition in rational time. No per-key/object override UI imposed. Options is available in Simple. Version3 extends v2 only for edited objects so old binaries reject unsupported behavior. Instance-local material copies handle Compatibility, which ignores GeometryInstance transparency. Native shader/alpha sorting and light/shadow equivalence remain limitations.


## Expandable animated parts — 2026-10-30

First increment is functional inspection/selection, preserving whole-pose curves. Automatic edits annotate changed stable IDs; same-frame edits merge hints. Old files infer relevant parts and mark those estimates. Shared snapshot controls remain visible for every shown part; no misleading destructive per-part delete/retime UI. Root neutral holds remain inspectable, visibility stays independent. Expansion is ephemeral, clears on document replacement, and does not dirty a project. Advanced independent curves/channel grouping and legacy-lane expansion remain future work.


Next IK investigation (not implemented): actual installed4.6 ClassDB inspection confirms TwoBoneIK3D, CCDIK3D and SkeletonModifier3D exist. The old SkeletonIK3D documentation marks it deprecated. Prefer testing the installed two-bone modifier with explicit rig-chain/pole mapping before choosing a custom solver; preserve sampled FK/Undo/render state and graceful unsupported-rig fallback. Presence of a class is not a passed IK user workflow. Primary references: https://docs.godotengine.org/en/4.6/classes/class_twoboneik3d.html and https://docs.godotengine.org/en/4.6/classes/class_skeletonmodifier3d.html; actual query retained in ignored output/ik-runtime-inspection.log.


## 2026-10-30 — Direct limb authoring and mode-aware names

Implemented default hand/foot movement for validated arm/leg chains using pinned
Godot4.6 TwoBoneIK3D. Solved rotations become existing FK pose keys, preserving
portable/scrubbable/exported motion without a live constraint. Advanced bend reversal
is undoable; Simple opt-out keeps direct bone moves. Root-motion foot planting,
native constraints and physics are separate required increments.

Owner explicitly requests generic body-part names in Simple and internal names in
Advanced. Both tree and expanded timeline follow this; original/native IDs never
change. Unrecognized parts use Other part in Simple and exact source names in
Advanced. The local dictionary includes exact source aliases and VRM role labels.

Owner reiterated GMod-like physics with less clipping and controlled chaos. Physics
and explicit Local/World Record must be visible in Simple; OFF freezes current pose.
No claim of bug-free collisions or a completed simulation. Jolt is bundled with the
pinned engine; its joint-property limitations must be respected. Research reference:
https://docs.godotengine.org/en/4.6/tutorials/physics/using_jolt_physics.html
Actual backend/colliders/joints/grab/throw/recording require the next tested increment.


## 2026-10-30 — First working live physics controls

User-prioritized Simple Physics now starts approximate validated ragdolls, direct
grab/lift/wheel-distance/release, freezes actual pose on disable, and keeps authored
keys untouched. Built-in Jolt explicitly selected,120Hz, CCD and constrained joints;
no unsupported soft-limit tuning. Visible map surfaces supply bounded collisions,
not the editor grid. No separate runtime installed or native model code executed.

Incremental limit: manual Physics activation first; automatic-on for compatible new
imports and explicit Local/World Record remain required next, alongside dynamic
unrigged props/boxes and richer native collision/joint parameters. This does not
fulfil all addendum physics acceptance. Frozen animated poses remain unrecorded
same-frame drafts; scrub/play resumes authored keys. Static frozen poses save/render.
Native parameter reports/IDs stay unchanged; proxy physics is not native fidelity.


## 2026-10-30 — Dynamic props through the standard model

Unrigged and single-bone models use a world-space rigid proxy with bounded convex
hulls per visible mesh; dense meshes use reported fitted boxes. Compatible humanoids
retain their articulated proxy. Both share Simple Physics, picking/pin grabbing,
freeze validation and native-ID/root Undo. Live motion never edits authored data.
No format migration, external-format exporter or new installation. Maps stay static;
flat/hidden/unsupported-scale props and simultaneous nested live bodies are rejected.
Default mass1kg and convex-filled cavities are provisional approximations; native
collision decomposition/mass/joints and automatic import activation remain open.
Explicit Local/World capture remains required next, now with real impacted boxes.


## 2026-10-30 — Explicit Local/World physics capture

Local locks the initially selected live model; World locks all live simulation
targets at start. Stop installs editable ordinary source-independent pieces in one
Undo; unselected Local peers return to authored state. Recorded range replaces only
its owned motion, preserving independent visibility/provenance and outside source
curves; inferred gaps retain existing bridge/hold semantics. Fixed120Hz tick zero
is armed on the next callback, avoiding a one-step timing offset. Playback/export
read baked keys rather than restarting physics. Live recording audio is silent.

No schema/ZIP migration: write existing project JSON compactly within unchanged
1MiB cap. Incremental byte/key accounting avoids copying a complete world each
sample; exact final validation remains mandatory. Keep a valid sampled prefix at
a real limit and report omitted later motion. Automatic import activation, native
physics fidelity, moving-map collisions and broad long-take scaling remain open.

## 2026-10-30 — Freer articulated ragdolls

Owner reports VRM/Scout upper limbs remaining rigid. Replace uniform55/25 cones
with native-bone-independent limb frames, shoulder110/70 and hip100/45 cones,
wrist/ankle/connector profiles and bend-plane elbow/knee hinges. Hinge limits use
the engine sign and offset for current bend; retain already over-bent initial
poses. Lower angular damping1.5→0.6. Keep the same collision fitting,2mm contact
allowance,120Hz CCD, native identities, ordinary FK capture and HAS schemas.
Symmetric cone envelopes are approximate, not full anatomical or native PHY/PMX
constraint reproduction. Straight chains estimate a forward bend plane; unusual
axes/anatomy still require future Advanced tuning. Existing recorded takes stay
unchanged; the refinement affects newly started live simulation.

## 2026-10-30 — Internal contact stability and secondary-motion scope

Do not fit loose unselected hair/cloth descendants into rigid head/torso bodies.
Retain directly weighted body regions and recognized finger/toe/twist helpers;
native skin and identities stay unchanged. Unknown structural helpers may need
manual/native tuning. Positive activation-time overlaps between proxy parts up
to four skeletal links apart receive live-session collision exceptions. Keep
external/distant/later separate parts collidable. Use nominal oriented boxes,
spheres and capsules; rounded box margins can make near-corner results conservative.
Four Jolt position iterations improve constraint accuracy with extra CPU cost.
An earlier eight-iteration experiment with oversized proxies did not solve the
underlying fit conflict and was discarded. No mass/rig/timeline/schema migration.

Owner additionally requested smooth hair/skirt motion and a movable adjustable-
speed fan, plus helper-bone/skin generation for qualifying loose regions lacking
chains. Both actual VRM samples contain declared spring data. Reuse that first;
missing-chain inference needs geometry/weights/anchors and a correctable preview.
Length alone is insufficient; extra bones without weights do not deform clothing.
See secondary_motion.md for full retained scope and implementation gates. No fan
button or claimed wind implementation is introduced by this contact refinement.


### 2026-10-30 — Declared secondary rigs before generated helpers
Use one runtime descriptor from native VRM0/1 data, with existing stable bone IDs
and explicit non-skin endpoints, centers/collider groups and original provenance.
Do not infer identities by original name or assume glTF index equals bone index.
Do not insert extra bones/weights into sources merely to run authored chains.
A unit-world scratch SpringBoneSimulator3D experiment avoids scaled-rig caveats;
its fixed steps output existing FK take data. Setup must complete deferred engine
configuration before tick zero, verified against differing render pacing.
Normal app activation/fan controls and Local/World recording integration remain
required next, followed by correctable missing-rig geometry/weights/helper creation.
Native initial movement and uncalibrated airflow prevent a finished smoothness or
cloth-fidelity claim. No permanent model asset extension, export-back or engine
replacement introduced.


### 2026-10-30 — Usable existing-chain fan and recording increment
Expose Hair & clothes independently of body Physics, with both composable. Create
an original fan as an ordinary HAS model with validated metadata, not a global
wind slider. Root position/rotation use ordinary auto-keys; on/speed remain scene
settings. Lock settings for a fan already in the recording scope to preserve the
existing stale-authoring guard. Hidden/absent fans do not emit; reference-only
fans can drive preview/recording. Positive uniform scale and bounded cone falloff.
Use 0.35s startup ramp/0.15s force smoothing/180degrees/s secondary offset cap;
preserve native settings/source data. A cap trades some immediate/contact fidelity
for bounded motion, not a no-clipping claim. OFF freezes the entire combined pose
in one Undo. Manual activation/default-on import remains unfinished. Fractional
read-only model sampling prevents 24fps anchor steps during120Hz capture; key
validation/storage stays integer. Helper inference/generation WITH weights remains
required next and must use correctable regions/anchors, not length alone.


### 2026-10-30 - Reviewed weighted helpers, attachment seam and immutable revisions
Use connected surface topology, existing weights and attachment geometry for an
explicitly reviewed candidate; no automatic claim that shape proves loose cloth.
Pin a narrow root cross-section, not one closest corner. Transfer only existing
anchor influence; preserve others, expand4to8or refuse overflow. Retain source
mesh/bone indices and derive new assets instead of rewriting original imports.
Exact source-node bindings support UI preview through existing imported skeletons.
Existing springs take priority. Multi-chain additions, unskinned/full-garment masks
and native MMD/full-cloth constraints remain open, not hidden by this increment.


### 2026-10-30 - Add more parts without replacing authored springs
Do not block the whole model merely because one hair chain exists. Protect connected
regions that have any existing spring influence, allow explicit review of other
regions, and append immutable revisions. Store new generated chains in private HAS
GLB extras so they cannot shadow VRM0 secondaryAnimation or rewrite native VRM1
collider/group indices. Parse into the same runtime descriptor; preserve older
VRMC_springBone generated assets. New helper collision-group authoring remains open.


### 2026-10-30 - Reviewed patches with pinned cut boundaries
A box can select a smaller connected area, including inside a partly spring-driven
component. Preserve coincident UV seams and all outside weights. Pin the full cut
boundary, not just one nearest point, so the original mesh stays joined. Refuse
existing spring influence, disconnected/no-free-span patches and preview overflow.
Make front/back inclusion explicit; preserve the5000vertex component preview cap
until a scalable/front-surface editor is implemented. Draft selection is not an
Undo/model change; Apply produces the same immutable revision and normal motion.

### 2026-10-30 - Explicit shape snapshots before import appearance changes
Add bounded POSITION morph evaluation to the existing assessment/preview/build
worker contract first. Keep original topology identities, source geometry/morphs
and existing neutral behavior. Snapshot weights must be explicit or request native
node-over-mesh defaults. This is a tested authoring foundation, not the completed
UI. Do not silently enable nonzero defaults in old projects: the observed runtime
currently leaves them at zero. Next establish exact mesh-instance/source-node
bindings and persist an opt-in/default-for-new-imports appearance choice. Existing
projects must retain their output. No separate ecosystem renderer or shape baking.

### 2026-10-30 - Saved imported-default appearance and exact helper snapshots
Connected the tested shape foundation to normal imports/review. Fresh UI imports
enable declared defaults; optional metadata absent in old records remains neutral.
Advanced opt-in is one model edit/Undo, never a pose key. Validate before live state
replacement. Tag importer source-node resources, verify exact mesh identity, and
use importer-unique names only for reparented mesh placeholders. Keep per-instance
weights despite shared geometry. Shape-aware CPU queries support placement and
physics fitting; no animated expression channels or native collision fidelity claim.

### 2026-10-30 - Editable static setup without pretending expressions are animated
Expose imported positional shape amounts under Advanced as **Base shape · whole
project**, with explicit Apply and reset/Undo. This is an engineering increment
toward importer fidelity; the owner did not request static setup as a replacement
for animated expressions. Retain those animation requirements. Version2 metadata
stores absolute per-node/per-target overrides above imported defaults or zero;
version1/absent settings remain supported. Preserve original names/indices and
source bytes. Prepare all geometry before publishing caches so a late failure does
not invalidate the active shape/Undo. Keep controls out of Simple, preserve their
effect across mode switches, freeze live physics before changing its fit, and
reuse existing model history/helper/HAS paths. Explicit Apply bounds expensive
native520-channel work; no continuous slider-preview claim.

### 2026-10-30 - Animated positional shapes use ordinary motion pieces
Model4 adds absolute source-node/target amounts and captured base values to the
existing pose snapshots/source-time blocks. Do not silently place expression keys
on an unrelated project-time track: split, move, clipboard and gap evaluation must
carry them. Bone edits preserve sampled shapes; physics captures retain authored
shape timing and count its bytes. First edits promote only their own object;
versions1–3 retain existing output, older builds reject4. No native source rewrite
or external-format exporter. Keep static base setup separate from per-frame edits.

Simple gets a small Shapes / expressions window with explicit Apply (an authored
change, auto-key on by default), pinned Close, and bounded scrolling. Known Japanese
labels use a small local marked dictionary; Advanced/tooltips keep originals.
GPU weights and conservative bounds update per frame, while exact CPU vertices
are evaluated on demand. Cache only used target arrays; first use can be slower.
Validate stored amounts/bindings and the conservative union operation budget before
state replacement. Native material/bone morphs, VRM preset/group composition,
independent curves and continuously deformed live colliders remain unfinished.

Post-regression read-only probe confirmed practical snapshot coupling: inserting
an expression control at12 into an existing eased root0→10 over0..24 changes X at6
from1.5625 to2.5, although original endpoints remain. Record the limitation rather
than presenting static-bone isolation tests as proof of independent motion curves.
Next: separate expression control ownership from body controls within source-time
pieces, preserve old model4 evaluation on read, and add an actual eased-body
regression before claiming that refinement. Evidence: output/shape-snapshot-probe.json.

### 2026-10-30 - Separate expression controls without changing legacy motion
Use model5 per-piece shape_keys in the same source-time block space, independently
of body keys. Each target has its own controls and interpolation; separate draft
and introduction addresses prevent unrelated body or expression edits from
rewriting its initial transition. Preserve body snapshot values and evaluation.
Expression-only blocks do not become body-gap anchors, and body-only blocks do
not become expression anchors. Do not grow a block for different expression
targets when this would move another target's gap boundaries; create a new piece.
Existing32-piece/2048 combined-control/1MiB budgets remain explicit limits.

Read model4 exactly as before. On an explicit expression edit, extract every old
full-snapshot expression curve, including empty-block defaults and endpoint hold,
before applying the new edit. Retain old body controls; do not silently repair
historical easing or strip keys. Advanced explicit Record can record body and
expression controls together, while automatic bone edits leave expression controls
alone. Physics capture splits body/expression samples and accounts for both.
Simple removal affects only the chosen expression key, with normal atomic Undo.
Root/bone per-axis curves and native expression presets remain required future work.

### 2026-10-30 - Validate independent body ownership before changing model storage
The actual bone-key probe repeats the earlier expression coupling: inserting a
right-side snapshot changes untouched left easing. Keep existing model1–5 reads
and normal editing unchanged while validating an internal body-curve foundation.
Retain original snapshots once per source piece and add sparse per-part controls
and deletion masks, rather than repeating every native ID on every old key.
Use existing Model blend math/skin/renderer; do not introduce a format-specific rig.
Require native matrix/pixel and source-time invariants before model versioning and
editor/HAS/history/capture integration. Ordinary sampled HAS/movie probes verify
the existing pipeline only; they are not the final independent-track solution.

### 2026-10-30 - Integrate body ownership in the existing model contract
Use model6 only when a body edit/selected deletion needs independent controls;
retain original model1–5 reads and original source snapshots. Sparse per-part
overrides, removal masks and shared explicit rest controls avoid dense native-ID
duplication. Compile indexes per replaced data dictionary, using the same Model
transform/quaternion math in preview and export. Keep expression/unknown clip fields.
Unsliced growing takes need per-part effective endpoints; a block's extension for
one part must not move another's interpolation boundaries. Split/capture fragments
instead retain deliberate fixed ranges. Import placeholders are bases, not phantom
future reset keys. Existing key/metadata budgets remain. This implements per-part
ownership; it does not close per-axis curves or the complete HAS feature scope.

### 2026-10-30 - Retain full numeric precision in editable saves
Strict multi-helper/model6 key comparisons exposed tiny rotation changes after
save/reopen, while the old rounded serialized comparisons still appeared equal.
Write compact JSON with Godot's full_precision option, and use the same option
for body bounds and incremental recording estimates. Keep the1MiB cap and old
JSON readers; no schema change. The unchanged strict59helper checks then pass.
Stored-data fixture expectations now request the writer's actual precision rather
than quantizing expected values through the older default formatting. See
[Godot4.6 JSON](https://docs.godotengine.org/en/4.6/classes/class_json.html#class-json-method-stringify).
Tiny-value exact decoding and compiled half-frame comparisons remain explicit gates.

### 2026-10-30 - Project-wide Unshaded with compatible legacy illumination
Add one Simple lighting menu over the existing renderer. New empty projects use
base-color Unshaded; Lit uses real imported lights with no implicit studio lamp.
Retain Studio light for absent legacy settings and the explicit sample room, plus
an understandable fallback choice. Store the choice in video settings with Undo,
packed/linked/recovery and identical final evaluation; no new model/container format.
Compose Unshaded with fades in the existing per-instance material layer, preserving
native material/texture references and authored emission when returning to Lit.
Do not replace custom shaders, claim native BSP lightmaps or add a separate renderer.
Primary Godot4.6 material/environment docs and actual GLB light tests support this
bounded implementation; native lighting fidelity and detailed light editing remain.

Flat-view multi-map reopen measured12changed RGB bytes at four room-surface
intersection pixels (mean0.00007427/255); all stored data and root/bone matrices
remain exact. Retain before/after PNGs and metrics. Apply the existing<=384channel/
mean<.002 GLB-rebuild criterion to packed reimport, consistent with recovery,
while adding exact state/matrix assertions. Same reopened preview/export stays
pixel-exact. This is a measured rebuild distinction, not a universal rendering
guarantee or a proven driver/ordering root cause.

The animation-piece packed rebuild independently measured27RGBbytes at nine
surface-edge pixels (mean0.0001490162/255), while complete portable world data and
every root/bone matrix remain exact. Keep its before/after images and diagnostics,
and apply the same established rebuild bound with those new exact-state checks.
Packed animation also requires exact cel bytes, camera keys and video settings;
the 3D rebuild allowance cannot conceal a changed drawing or camera control.
The recovered-preview/export comparison remains byte-exact. The failed strict
rebuild runs are retained as development evidence, not reported as passes.

Saved-copy native PMD/PMX/VRM import then exposed a single VRM hair pixel at
(962,249):3RGBbytes, mean0.0000050636574/255. Complete scene/native metadata,
all root/bone matrices, cel bytes, camera keys and video settings compare exactly.
Retain its before/after images and exact-state diagnostics. Use the same existing
GLB rebuild bound here, while reopened-preview/MP4 remains byte-exact. Initial
and diagnostic native failures stay in the record; no native rendering-fidelity
or proven driver/root-cause claim follows from this measured distinction.

### 2026-10-30 - Interactive ragdolls default to live physics
Apply the owner's governing §9.1 choice at the user import boundary, not HAS Open
or low-level asset preparation. Carry explicit transient intent through existing
placement/native conversion. Defer until warnings/modal/conversion are finished;
reject unsupported anatomy/scales using the existing shared adapter. Props keep
their manual toggle; maps are static. Preserve earlier body/secondary modes while
structural imports rebuild, restarting at the frozen pose with zero velocity.
Velocity continuity through structural edits was OPEN; a reset avoids converting
stale velocities into impulses on reconstructed bodies. No uncontrolled playback,
new animation key, saved live flag, native ID change or alternate physics engine.
Cancel pending requests on explicit authoring/lifecycle actions and bind them to
root/data/frame identity. First gravity test used an already grounded limb and
measured only0.00002778units further descent; keep the >.01 threshold and use the
normal aerial placement path. Final aerial probe measures real gravitational fall.

### 2026-10-30 — frame the current skin, keeping placement bounds separate

A real transformed limb probe put the posed skin more than 30 world units away
from its bind box. Frame model/selected/scene therefore use an on-demand current
skin+morph query; import placement keeps its existing bind-oriented query. Static
poses must be available immediately, before rendering catches up. Live physical
modifiers require the final globals from their existing capture callback, with a
weak-owner transient cache cleared at stop/disposal. Do not freeze/record merely
to inspect a model. Limit exact work to 200k vertices and use an explicitly roomy
transformed-box fallback above that budget. Existing camera near-plane distance
protects tiny models. No native source rewrite, project migration or implicit shot
key. See pose_framing.md for evidence and unsupported geometry.

Full regression exposed two lifetime errors despite passing feature assertions:
typed cleanup parameters rejected freed skeletons before their guard, and an
existing GLTFState scene-node lookup could still dereference a discarded import
placeholder. Guard teardown references before using them; resolve non-bone
secondary bindings from uniquely source-tagged live nodes. Tag all source nodes
before generation, preserving native bone IDs and avoiding name guesses. A
20-import regression proves distinct duplicate-name collider anchors and a live
non-bone center. Failed full runs remain evidence, not accepted clean passes.

Audio regression measurement: a displayed preview frame belongs to the clock
sample taken by its process step, not a later clock read after rendering/logging.
The old test failed at frame29 while the hardware sample was1.2428s (frame29),
then compared it with1.3114s. Retain the sampled timestamp as a diagnostic only;
keep the <=1frame assertion and add continued clock/frame advancement over a later
rendered interval. Log the fresh clock separately. Playback/encoding logic is
unchanged; this does not assert an end-to-end latency bound under machine load.

### 2026-10-30 — isolate shot visibility distances from reference framing

Actual large-scene probe: unchanged camera keys rendered139876green wall pixels
at far12000, then0 after framing a nearby box set the shared camera far2000.
Record optional near/far fields with explicit camera keys, sample them for the
shot, and preserve both with temporary view snapshots. Missing fields retain old
cold-start0.05/2000 behavior; do not infer a lost old editor range. Advanced tuning
is temporary until explicit Save camera key. Retain existing interpolation and
schema/model/HAS versions; older builds may ignore the optional fields. Validate
finite ordered ranges before writes/Open. No source-model or native format change.

Focused test development distinguished actual content from representation:
the Advanced-button signal needs its pressed state; JSON frame integers become
numeric floats; packed model source/path addresses relocate. Normalize JSON number
types using the actual full-precision writer, compare every authored field exactly,
and verify relocated binary hashes and bone IDs separately. No pixel or motion
tolerance was loosened. Earlier failed diagnostic logs remain retained.

Custom clipping also applies to visible model imports. Capture near/far with the
request and solve a permitted depth interval from the complete model bounds and
frustum, retaining the old preferred placement when it fits. Do not move the
camera, widen its range, scale the model or change shot keys to hide a failed fit.
An impossible interval refuses with a clear correction before replacing the world.
Older low-level requests without range fields retain their earlier policy.

## 2026-10-31 — default newest-valid recovery

The governing addendum supersedes the old explicit-only startup dialog. Normal
startup now attempts retained candidates newest-first through normal Open's full
asset and rig validation. A failed candidate never replaces the live world; the
first valid result becomes dirty and has no manual-save identity. Retained files
and original manual HAS remain untouched until explicit Save/Dismiss. Deferred
startup has session/revision/interaction guards; no failure-dialog sequence.

An actual unrelated live-writer test exposed the engine's child-process liveness
limitation. Use one narrow Windows/Python SYNCHRONIZE query of recorded owner PIDs,
not process enumeration or a negative child lookup. Unknown owners stay protected.
Normalize numeric JSON PIDs before lookup. Native data and storage schemas stay
unchanged. New process tests cover an actual abrupt self-termination, damaged
generations, native assets, manual-save protection and synchronized MP4; remaining
journal/history/thumbnails/action scheduling are explicitly unfinished. See
startup_recovery.md and the latest progress memo for actual run/save status.

## 2026-10-31 — bounded journal and Advanced history

Use a checksummed catalog plus immutable metadata snapshots over existing shared
assets/cels, rather than copying complete projects. Retain12 visible states and
rollback references; adopt both old generations before rotation. Only exact
journal-owned metadata/preview names are pruned. Shared-asset garbage collection
remains separate, with the existing512MiB guard. Restore archived metadata only
through a matching hash filename and the unchanged full project/rig validation.

Generate previews on a stable idle rendered frame, with session/revision/frame/
view and interaction checks. Copy image data; do not evaluate or record the shot.
Playback/export/live physics or newer edits can leave a valid checkpoint without
a preview. Advanced exposes timestamps and previews; Simple limits recent choices.
Resolved histories remain browsable but stay out of startup recovery. Idle callback
latency is measured and remains a limit, not a universal nonblocking-input claim.
The history dialog uses bounded literal lines rather than an auto-wrapping label
that briefly inflated its native window. See recovery_history.md for evidence and
unfinished action scheduling/cache/performance work.

## 2026-10-31 — completed-edit recovery scheduling

Expose either minutes or completed edits in Advanced, with the existing one-minute
default and initially25 edits as the alternative. Count changed committed commands
and successful changed Undo/Redo once; long strokes count only on release. Count
actual layer visibility changes at their existing non-history callback. Preserve
existing Undo behavior. Compare stored command values, not visual appearance.

Keep pending edits across disabled/busy periods and schedule changes. Reset only
after a successful checkpoint or an exact-current-revision manual Save; preserve
later edits during asynchronous saving. Failed writes retain pending actions and
wait30seconds before automatic retry. Explicit checkpoint bypasses scheduling but
keeps interaction guards. No scene/HAS schema or preference persistence change.
See recovery_schedule.md; synchronous comparisons/writes/previews and cache cleanup
remain unfinished reliability work. No universal background-input latency claim.

## 2026-10-31 — detached preview CPU and file work

Keep viewport GPU readback and independent cel-image snapshots on the main thread.
Move resizing, blending, PNG encoding and journal file work to one low-priority
thread owning only those detached images. Poll finished work during normal app
processing; join only completed work there, and join remaining work at teardown.
Do not disable thread checks, change render/physics threading settings or share
live nodes/resources. No new scene/model/HAS/journal format or image approximation.

Serialize checkpoint writers against the preview worker so catalog updates cannot
overwrite each other. Preserve explicit requests until the worker/interaction
finishes, including when automatic protection is off. New/Open/current-revision
manual Save clear queued intent; an older-session error cannot replace new feedback.
Keep capture and worker timings separate. GPU readback/copy/checkpoint latency,
exit-time I/O delays and all previous cache/large-project limits remain open.
See recovery_preview.md for primary thread API references and actual test scope.

## 2026-10-31 — Home after automatic recovery and local recents

Run normal recovery before showing Home, so valid recovered work goes directly to
editing. Embed Home in the existing app, with working New/Open/Return actions and
bounded personal recent metadata; no separate splash window or scene schema. Show
recovery/open failures in Home without resetting the current scene. Keep confirmed
Tutorials/catalog/practice/teacher scope unfinished rather than adding an inactive
button. Next build real included exercise scenes and observed lesson steps.

Record only successful normal HAS operations, not backups or automatic recovery.
Use existing validated managed previews when an exact saved revision is available;
avoid another full-resolution capture/thumbnail pipeline. Missing previews use an
original icon. Recent removal never deletes files. Personal metadata stays outside
HAS, with isolated test preferences,64KiB/twelve-row limits and atomic writes.
Multi-instance preference locking/content-identity checks for old thumbnails remain
open; normal project loading retains complete existing validation. See home.md.
An active physics recording keeps Home closed with quiet guidance so its Stop
controls remain available. Ordinary live physics is not frozen just by navigation.


Tutorial engineering increment: two original offline practice chapters exercise
real posing/drawing and explicit camera keys before expanding to full courses.
No decision on tutorial Skip. Sessions are retained on Start fresh; Save uses a
personal normal HAS and protects included examples. Original procedural examples
do not impose an app/asset distribution license. Partial course scope, forced-exit
context and retention limits are documented in tutorials.md.


Beginner-course engineering: first-movie-v1 keeps older three-task progress intact.
It uses real normal pickers/import/physics/posing/drawing/clip/save/export paths.
Save remains optional to honor disposable practice; an actual successful export
finishes the final task with or without a personal HAS. Skip remains OPEN. Visual
review found a guide obscuring its target; choose a clearer corner and allow
collapse rather than changing camera/model state. Qualified missing encoder paths
now fail preflight quietly before requesting an OS process.

## 2026-10-31 — Recovery writer identity survives reused process numbers

Use Windows process creation time alongside PID in new recovery owner sidecars.
Keep the full unsigned FILETIME as a decimal string, with strict bounds, rather
than a JSON number that could lose precision. Obtain it from the same read-only
handle used for liveness, requesting limited query rights and falling back to
wait-only liveness when timing access is denied. No process enumeration/control.
Cache our own result to avoid repeated helper launches for every checkpoint.

An exact live match remains protected; a live PID with a different valid creation
time no longer hides an expired writer's checkpoint. Unknown identity/liveness,
malformed present owner data and legacy live PID-only records remain protected.
Missing sidecars retain old ownerless-cache compatibility. Failure to obtain our
own initial token retains PID-only writing until restart. Native scene/model/HAS
and journal schemas stay unchanged. This addresses a known Windows identity
ambiguity; it does not establish the cause of the earlier history fixture failure.
See startup_recovery.md for primary references and current verification gates.

## 2026-10-31 — Drawing fill stays separate and previewed on spills

Add a Simple Fill tool with visible-drawing sampling, exact active-layer RGBA
replacement and Advanced seed tolerance. Keep the old two-layer default/order;
Flats is explicitly inserted beneath selected line art, with stable existing
dictionary/image identities and one Undo. Reuse current four-layer/cel/HAS limits.
No default schema migration or mesh/camera change.

Run bounded scanline traversal on detached byte arrays in one low-priority worker;
only main processing reads/commits Images and GPU textures. Check document revision,
frame and layer again before committing; stale work and previews cannot enter Save
or render. Large/edge regions require visible preview and Apply/Cancel. Preview
composites the candidate stack in its correct order, not a flattened paint change.
This is basic connected fill, not automatic gap closure or art-intent inference.
Preserve gap closing, boundary growth/AA refinement, onion skin, pressure, richer
layers and KRA as required unfinished drawing work. See drawing_fill.md.

## 2026-10-31 — Onion guides are transient exposure references

Default off; Simple toggles one previous/next exposure of the active layer, blue/
pink beneath current drawing layers. Held frames do not repeat the current cel.
Advanced opacity is personal authoring state, not project output. Hide guides in
Scene/Pose, playback, Home, export, hidden layers and pending fill previews.

Use two GPU alpha-tint materials and image-identity/revision texture caching.
Transient Image metadata changes only cache identity, never PNG/HAS data. Exact
shared CanvasRaster rectangles avoid Control offset reconstruction when zooming.
Do not sample these UI items for fill/recovery/export or modify original pixels.
Keep multi-neighbor ranges, richer layers, pressure, gap refinement and KRA open.


## 2026-10-31 — Editable drawing layer structure

Simple Layers dialog shows topmost first; storage keeps its existing bottom-to-top
array. Names/order/visibility/removal use current fields, packed/linked/recovery/
lesson snapshots and final composition. New stays Rough/Ink. Four layers, 32 cels
remain; Effects is a real editable layer. Keep opacity and larger documents open.
Structural Undo uses shallow order arrays, retaining dictionary/Image identity for
older painting history. Property Undo addresses the original dictionary and keeps
another selection. Charge removed cels to the bounded history budget. Populated
removal confirms; last layer cannot be removed. New/Open invalidate dialogs.


## 2026-10-31 — Separate drawing layer opacity

Simple Layers offers an explicit percent Apply/Enter, one Undo/autosave command.
Optional normalized opacity defaults1 in old layers. Source alpha is retained;
only derived output alpha is rounded. Keep existing project/HAS schemas, validate
finite bounds before writes/Open/backup qualification, and disclose old binaries
ignore the added field. Four weak-source cached rasters use stroke/tile damage;
new amounts/full replacements rebuild once. Recovery resizes before fading on
its existing detached worker. No new rendering path or continuous full-HD slider.


## 2026-10-31 — Guide-free color sampling

Simple Draw I picks visible3D plus committed drawings and returns to Pen. Advanced
can sample visible2D RGBA or raw active cel. Color/source choice are personal state,
not project edits. A lazy shared-world one-shot view copies current camera settings
without resampling keys/poses; editor grid19 and selection proxies20 are excluded.
The main grid stays visible. One-pixel native RGBA blend matches drawing opacity.
View picks require frozen physics. Explicit cancellation and an object-bound single
post-draw callback avoid suspended Node state across deletion; current serial-less
connection ownership lets a newer click replace the old one safely. No schema change.

## 2026-11-01 — Held-foot direct body posing

Addendum §5.3 requires root/crouch movement that can keep feet planted. The first
increment is an opt-in Simple Hold feet while posing option for root/common-body
Move edits, using two validated native leg chains and the existing scratch IK.
Atomic whole-edit rollback/last valid drag preview prevents one solved foot from
being committed when the other is unreachable. Physics must already be frozen;
manual edits retain the owner's auto-key preference and normal one-command Undo.

This adds editable FK endpoints, not a persistent world/timeline constraint. An
explicit midpoint-sliding test keeps continuous contacts OPEN. Persistent contact
ranges need versioned evaluation plus clip retiming, parenting, manual correction
and physics/capture transitions; hiding arbitrary state in native metadata would
not close those requirements. No format migration or external exporter is added.

## 2026-11-01 — Development contact correction and explicit knee versioning

Engineering increment under the confirmed editable foot-planting requirement:
the development Model7 range window now corrects one foot through Simple camera-
relative nudges/knee reversal or Advanced world pin/orientation/knee targets. The
explicit interval and Apply/button action create one Undo; no sampled FK replaces
the original body controls. Other-foot changes and release gaps stay independent.
Viewport pin/pole gizmos remain a later usability increment, not a shipped claim.

New knee semantics require nested `studio_foot_contacts_2`; plain contact tracks
stay1. Older experimental validators reject2, preventing silent loss of a chosen
knee direction. Models1–6/world4/HAS ZIPv1 and original asset data are unchanged.
All Model7 work stays separately checkpointed until the six activation gates pass.
This is an engineering compatibility decision, not a new user preference or a
resolution of walking/path/overshoot/cloth OPEN items. See contact_animation.md.

## 2026-11-01 — Transient native bindings and bounded recording ownership

Contact evaluation compiles native leg identities once per unchanged inventory,
with root/order/humanoid and six live binding checks before reuse. Keep requested
track/bone validation and live solver reach checks. The plan is runtime state;
no schema/native-data changes or family-specific posing paths are introduced.
Performance claims distinguish lookup timing from complete pose sampling and FPS.

Actual combined VRM recording exposed first-snapshot leakage into earlier frames
for newly captured channels. Preserve their original baseline before the take as
well as after it. Use the nearest earlier retained piece; add a body-only boundary
piece when necessary and enforce the unchanged capacity limits. Do not rewrite
existing channel curves or change the owner's ordinary gap interpretation. See
the deterministic recording tests and actual native contact/capture/movie evidence.

## 2026-11-01 — A cut contact can transfer its identity once

Repeated Paste must duplicate animation independently. Cut's contact identity may
transfer on the first successful same-instance, unchanged-anchor placement, only
while its original block is absent. Check presence again because Undo may restore
that block without changing the clipboard. Any successful paste consumes transfer;
refusals keep it available. Later copies get fresh pins and do not bridge unrelated
gaps. Keep reusable clipboard content outside project Undo; restore block IDs
exactly through Undo/Redo. No serialized schema or new owner preference is added.

## 2026-11-01 — Selection reads authored alpha before scene fades

Selection masks must retain native material cutouts while remaining usable during
object/parent fades and after hiding. Read the owning ModelOpacity's authored
material rather than its temporary fade/lighting duplicate. Surface overrides
inherit the Mesh material when absent; a global override stays authoritative.
Do not divide by a small fade value or modify authored alpha. Independent baked
geometry, actual green pixels and normal Model6 compatibility verify this repair.
Apply these two compatible files to the normal app separately from Model7; retain
the tested base/overlay hashes and backups. All contact activation gates remain.

## 2026-11-01 — Model scale shares live-contact deferral

Check the same pending/live/recording policy as other contact-affecting edits
before Apply model scale enters a draft. Do not silently freeze a solver, consume
its startup ticket or finish recording as a side effect of a refused scale edit.
Scale operates on the whole model even with a foot selected, so reuse the live
guard without the separate direct-pinned-leg guard. Clear stale reach warnings
when a contact drag returns to a reachable preview. Preserve existing solver math,
schema and unplanted behavior. Native tests retain the supplied root rotation/
scale baseline; do not infer an import bug from an identity-root test fixture.
Actual reparent UI/motion semantics remain unimplemented, not an acceptance claim.

## 2026-11-01 — Derived acting enters before standard contact solving

Keep main pose controls authoritative. Generate bounded, speed-aware detail in a
separate immutable preview plan, then use the existing standard contact evaluator
to hold feet. Turning it off must recover the exact original animation and pixels.
Reject unreachable/stale previews, mismatched source easing and incomplete main
curves; never unpin feet or bake generated detail into FK silently. The first
adapter remains an experiment outside normal editing/storage/final rendering.
Its profile, strength and time constants are provisional, not owner preferences.
Actual source-time curve extraction, Advanced adjustments/manual corrections,
Undo, compatible persistence and normal Export still precede editor activation.
See motion_assistance.md for the current finite checks and limitations.

## 2026-11-01 — Motion helpers retain source phase through clip edits

Compile helper curves from the same indexed source controls used by body playback,
including virtual/rest points and removed controls. A split changes the visible
source window; it must not restart the generated profile. A moved slice carries
its original relative acting. Connect gaps with the existing per-part endpoints/
easing, interpolated carried offsets and bounded extra detail; never infer object
visibility. Preserve explicit Holds. Complete takes may settle, while a trim through
moving source data fades its offset rather than following cropped future motion.
The .24-second trim return is provisional. Source-space helper evaluation has a
separate bounded utility domain; actual project/schema limits stay unchanged.
This is a tested preview adapter, not normal editor/storage/export activation.

## 2026-11-01 — Save character intent while keeping authored controls separate

Model8 adds an explicit versioned enable/amount descriptor and preserves existing
body/expression/contact behavior. Older records do not silently gain acting;
older readers reject8. Source plans are cached by immutable data revision and
project timing. The same derived body/root evaluator feeds normal preview and
final output before contact solving. Authored accessors remain separate. During
manual edits, an unchanged draft peer receives assistance once while a changed
visible target is not offset twice; auto-key writes only changed part controls.
Simple gets one compact opt-in dialog. Advanced currently inspects generated keys
read-only; fine helper editing remains unfinished. Saved default style/intensity
is provisional. User confirmed they will be the first actual artist and want GMod
familiarity with far fewer/slower interruptions than Stop Motion Helper; judge the
whole few-key workflow, not feature count. First-use artistic/speed acceptance is
OPEN. Canonical Model7 installation was explicitly approved separately; this newer
Model8 feature stays in development pending wider testing.

## 2026-11-01 — measure deform regions before adopting inferred categories

The read-only observation backend uses exact source/node/target identity and
explicit weak seed provenance. Same-model changed-vertex similarity can suggest
a region; it cannot prove emotion, native controller behavior or cross-model
generalization. Mixed/weak matches stay Other; no automatic editor adoption yet.
Actual six-asset evidence exposed Source CamelCase compounds polluting brow
seeds. Split names into tokens, retain original bindings and preserve manual
overrides. Brows plus eyelid/squint now stays mixed, while Eye brows stays Brows.
See deform_observations.md for thresholds, tests, retained false positive and gaps.

## 2026-11-01 — explicit in-app study adoption

Advanced now launches the bounded local positional study without blocking the
editor. Results are neutral geometry evidence, not authored animation or saved
inference. Source/job/revision/control/example identities guard review. Cancel,
scene replacement/live motion and teardown invalidate owned work. Adopt through
the existing catalogue/Undo path, preserving native IDs, original assets and
independent body/camera/drawing data. New/Open never resumes a prior study.
Report retention/quota, richer visual review and broad native semantics remain
unfinished. See shape_study.md; normal Model7 and frozen web artifact unchanged.

## 2026-11-01 — isolated neutral/test deformation views

Advanced Compare without recording uses a disposable instance of the shared
standard Model/Renderer, never the document actor or a source-specific pose path.
One camera frames the union of moved neutral/test geometry with the existing skin
palette. Zeroed peer targets and a neutral skeleton make positional evidence
inspectable; ordinary authored poses, keys, paint, pending amount and native source
remain untouched. Rendering uses disconnectable one-shot callbacks and explicit
world/viewport teardown. Source import/focus remain synchronous and bounded, with
possible stalls/memory cost. Native controller combinations and non-position
semantics are still open. See shape_comparison.md; normal Model7/frozen web stay
unchanged until a separately reviewed update.

## 2026-11-01 — declared expression poses through standard deform keys

Preserve native preset/custom identity separately from guessed deform areas.
VRM0 mesh/percentage and VRM1 node/fractional adapters supply one transient grouped
contract; a shared evaluator handles sums/binary poses/override factors. Explicit
Use expression pose replaces only the embedded expression morph set and calls
ordinary independent deform-key authoring once, preserving unrelated deforms and
body/camera/drawing data. Material/texture groups refuse as a whole; material-only
models still expose that guidance. Stored keys remain editable amounts, not a
new native-expression track or promise of continuous native binary/override
semantics. Window opens beside the subject. Full-world deform metadata preflight
prevents unsaveable edits. See expression_presets.md; normal Model7/frozen web
unchanged and broader native expression/rule/fidelity work remains open.

## 2026-11-01 — optional reviewed character height before installation

Owner requested optional six-foot standardization, preserving unusual proportions
and leaving unchecked imports unadjusted. Options now offers a session-only,
initially off review for new model imports. One disposable standard renderer
measures visible neutral extent along the body axis, using real skin weights in
the head and both validated legs to reject separate parts with full skeletons.
Complete ordinary upright figures suggest 1.8288 metres; uncertain short/long
proportions start unchecked. The thresholds are provisional engineering choices,
not a learned classifier. Explicit Add applies uniform root scale before normal
placement and Physics, with one Undo and no invented animation keys.

Source units, geometry and native parameters remain unchanged. Exact decimal-text
measurement provenance and engine float32 scale bits survive packed/linked Open
without commanding another fit. Deferred generation/source/world/revision guards
prevent stale installation. Hashing/import/measurement remain synchronous and
bounded, with possible stalls. No schema change or source-family pose engine.
Map calibration, existing animated resizing and later per-object reset remain
open. See height_import.md. Normal Model7 and frozen web remain unchanged.

## 2026-11-01 — known-distance sizing for static map roots

Use artist-marked exact surface points and an editable real distance, rather than
inferring all buildings from overall map bounds. Simple World > Size map opens a
disposable standard map view, copied working camera and cyan six-foot guide.
Preview size is reversible; Apply uses uniform scale about the first point and
one world Undo, no animation keys or source writes. Door/ceiling presets are
editable examples. Source units remain separate. Exact decimal-text provenance
and ordinary numeric transforms persist without a format change or refitting on
Open. Static unattached unskinned maps only in this increment; animation, attached
instances, live simulation and later contact-aware resizing require their own
workflow. Exact picking is bounded and synchronous; alpha/shader appearance is
not pick geometry. See map_calibration.md; normal app/frozen web unchanged.

## 2026-11-02 — MMD native groups normalized into the shared expression contract

Retain native membership/name/weight in new MMD preparations, flatten nested
vertex groups additively, then attach exact prepared node/target bindings in GLB
asset extras. One runtime validator/catalogue/evaluator and existing ordinary
deform keys/Undo/HAS/render handle MMD and VRM. No separate source-family posing
engine, format migration, source rewrite or external exporter. Nonzero bone/UV/
material effects, missing/ambiguous/cyclic graphs and resource/range excess refuse
the complete group, preserving guidance rather than applying a partial pose.
Simple source-English names/estimate fallback, Advanced original identity. Older
name-only preparations need reimport; continuous native group tracks and broader
native corpus/fidelity remain open. See expression_presets.md. A malformed test
placement context exposed unchecked camera access; placement now refuses it
cleanly and tests preserve world/history. Normal Model7/frozen web unchanged.
