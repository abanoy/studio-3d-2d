# HAS projects and standardized assets

New documents use the [schema4 world record](world_format.md), with multiple maps,
models and groups plus shared asset storage. Normal Open/Save/recovery preserve the
complete world. Existing schema1–3 documents remain readable with their original
defaults; adding another object promotes existing content into the shared world.

Owner-selected project extension: **`.has`** (Hybrid Animation Studio). New Save
and Open use files. Advanced > Save as chooses another filename/storage mode;
Advanced > Open folder retains existing schema1–4 directory projects. Their
ordinary Save remains compatible; Save as migrates them to HAS. Recovery and
opening a `.has.backup` produce unsaved editable copies.

## Save choices

**Packed**, the default, embeds all current playback/editing assets: environment
GLBs for every world instance, embedded textures, raster cels, WAV audio, native parameter
metadata, camera/pose keys, frame timing and settings. Move the HAS elsewhere and
open it without the original asset locations. It does not require Blender or the
games to replay an already prepared project. Existing Godot/FFmpeg requirements
still apply. Packing does not flatten the drawing layers or turn animation into
a movie.

**Linked** keeps camera/pose/cel/audio settings and drawings in HAS, but references
the standardized GLB/WAV files by location, length and SHA256. It does not link
the raw GMA/MDL/PMX and reconvert on every open. Matching files must remain locally
available. Paths beside the HAS are relative; other locations are absolute.
If a file moved or changed, Studio keeps the current project and offers Locate
file. Relinking requires the same bytes; deliberately replacing an asset uses
the normal import controls. Save commits the updated links.

Linked Save from an opened packed file externalizes its cache-only assets into
`<project-name>.assets/` beside HAS. This avoids depending on disposable extraction
paths. Keep that directory with the linked HAS. Linked Save after relinking retains
the actual relocated originals, rather than linking its temporary loaded copies.
No web/UNC references or automatic remote search/downloads are supported.

“Everything” here means the standardized scene and editable Studio animation.
Original conversion bundles (`editable.blend`, original MDL/BSP/PMD/PMX, alternate
skins/bodygroups and converter logs/dependency archives) remain separate. Native
parameter reports already stored in model metadata remain included. Packing
does not restore unsupported native physics, shaders, morph tools, IK or SFM
sessions/DMX, and does not include an entire game installation or toolchain.

## One asset contract

Current adapters:

| Source | Preparation | Studio data |
| --- | --- | --- |
| GLB | Validate self-contained glTF2 | Standard environment/model |
| GMod/SFM MDL/BSP, GMA, legacy BIN, VPK | Local isolated Blender/SourceIO + dependency mounts | Same GLB and `studio_model_1` |
| MMD PMD/PMX | Direct native routing through installed Blender/MMD Tools | Same GLB and `studio_model_1` |
| VRM0/1 | Direct stdlib embedded-GLB/humanoid preparation | Same GLB and `studio_model_1` |
| Binary FBX, OBJ/MTL, glTF2.0 | Local built-in Blender preparation | Same GLB and `studio_model_1` |

Each adapter must retain original files, record scale/axis conversion, preserve
names and supported native parameters, and report missing resources/losses. The
renderer, pose tools and timeline consume the standard result, not source-specific
runtime branches. HAS adds a project container over that existing contract.
Piece-based animation uses version2 of the same model record after editing;
see animation_clips.md. It is included in packed/linked HAS, not baked to video.

Binary FBX, OBJ/MTL and separate glTF now use the common preparation adapter; see
common_import.md for actual coverage. USD/Alembic and other formats remain future
work requiring separate feature/animation/fidelity checks. Converting a format is
not evidence all of its features survive.

## Container v1

2026-11-02 audio continuation: multiple sounds use a versioned `studio_audio_2`
collection inside the existing project; silent/single saves retain their prior
audio layout. All WAV memberships, embedded bytes and linked sidecars/checksums
participate in the same worker contract. Older apps refuse multi-clip scenes
rather than dropping sounds. See [multiple audio](multiple_audio.md). Container
version and bounds below remain unchanged; this is not an external audio exporter.

HAS is an inspectable ZIP container, without executable scripts:

```text
film.has
  has.json             # format/version/storage, payload and asset inventory
  project.json         # editable schema3 legacy model or schema4 world
  cels/content/*.png   # independent held raster cels
  assets/*.glb         # packed mode only
  assets/*.wav         # packed mode only
```

`has.json.format` is `hybrid_animation_studio`, `version` is1, `storage` is
`packed` or `linked`. Asset rows contain `path`, `sha256`, `bytes`, and a `reference`
for linked mode. Payload rows contain path/length/SHA256 for every embedded file
except has.json itself. Only manifest-declared assets/cels may be present. Current
reader accepts project schema3/4 inside HAS; old folder projects can still load and
be saved into HAS through the app.

Bounds:512MiB archive and expanded project,128files,1MiB each metadata document,
128MiB per GLB and32MiB per WAV/PNG. Existing1080p/240frame/32cel/64world-object limits
remain. End-directory preflight bounds ZIP metadata before allocating its index.
Only stored/DEFLATE compression is supported. ZIP64, multi-disk, encrypted,
symlink, duplicate/case-colliding, traversal and
unexpected entries are rejected. CRC plus declared byte hashes are checked.
Hashes detect changed data; they are not signatures or proof of asset ownership.
This is not a certification of a hostile-file sandbox.

Save snapshots the editable project, then a cancellable Python standard-library
worker writes a new temporary archive, flushes it and replaces the target. An older
readable HAS is retained as `<file>.has.backup`. Known unreadable old archives do
not overwrite that backup. Failed/cancelled saves preserve the previous complete
HAS. A cancel received after commit may find the operation already completed.
An OS/power-loss durability guarantee is not claimed.

Open verifies/extracts into a new private folder and runs the existing full project
and GLB validation before installing the scene/model. Linked assets are materialized
as validated working copies for the current session; changing their originals
does not mutate an open project silently. Packing/opening runs asynchronously;
snapshot serialization/copying remains synchronous and needs large-scene profiling.
Cache/temp work stays under `output/has-cache`; it is retained, not automatically
garbage-collected or globally quota-controlled yet. Do not remove active working
copies. No Windows extension association or packaged installer is supplied.

## Verification

Run `python -u tests/verify_has.py` after `tests/verify.py` creates the audio fixture.
It checks packed reopening after originals move, linked omission/relink/backup,
cancel/corruption preserving prior data, recovery identity, actual Save dialog,
camera/model/drawing/audio persistence and H264/AAC export. Available private GMod,
SFM and MMD prepared projects are packed/reopened through the same path; those
private checks are explicitly listed when present. Python fixture tests cover
portable/link/sidecar saves, failure preservation, Unicode filenames, paths,
network reference rejection, metadata/ZIP bounds and unsupported containers.

Repeated capture/export of an opened project must match exactly. Separate GLB
reimports retain the existing tightly bounded edge-pixel tolerance; package asset
bytes/hashes remain exact. Physical file-picker input, clean-machine portability,
large project latency, real disk-full/power-cut and native visual fidelity still
need separate testing.


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


Update2026-10-29: FBX, OBJ/MTL and glTF2.0 now have local preparation adapters.
See common_import.md. Their standard GLB/report outputs use this unchanged HAS contract;
other broader-format candidates above remain future work.


Visibility extension: studio_model_3 retains independently owned motion pieces plus visibility_keys; video.visibility_fade_ms stores the global0–10000ms default300. Packed/linked HAS and recovery use the same existing container/world schema; old records read with static initial flags. See visibility.md.


Physics capture writes ordinary studio_model_2/3 animation pieces within unchanged
world schema4/HAS ZIPv1. New project JSON is compact; existing indented JSON remains
readable. Saved simulation is parametric pose/root keys, never a fresh runtime solver
dependency. See physics_recording.md for scope, timing and existing metadata limits.

Static imported-shape adjustments are optional model metadata (`source_shape`
version2) using sparse numeric source-node/target identities and absolute weights.
Packed and linked saves retain the same configuration alongside the unchanged
standard GLB, native parameter report and animation. Existing version1/default-free
records remain readable without silent appearance changes. Use an updated Studio
for files containing version2 adjustments; older builds reject that setting.
See standard_model.md. This does not introduce external-format export or a new HAS
container version, and does not store animated expression curves.

Animated shapes now use model version4 inside this unchanged container/world schema.
Absolute source-node/target amounts, captured base values, optional display names,
draft and source-time key/piece fields travel with the standard GLB and native
report. Packed, linked and recovery paths share normal Model validation and bind
checks. Old model versions1–3 remain readable. Earlier Studio binaries reject
version4. This supersedes the static-only gate above; see shape_animation.md.

New expression edits use model5, with dedicated per-piece shape controls rather
than body snapshots. The container/world version stays unchanged. Model1–4 remain
readable; model4 upgrades only on an expression edit, preserving its prior curves.
Shape drafts, introduction addresses and per-target interpolation are included in
packed/linked/recovery saves and validated before replacement. Older binaries
reject model5. No original mesh or external-format exporter is introduced.

Model6 extends the same container/world with independently owned root/bone controls,
source snapshots, deletion masks, shared recorded rest keys and per-part introductions.
Packed/linked/recovery save those editable fields directly; rendering uses the same
compiled evaluator rather than baking them into old snapshots. Old model1–5 records
retain their saved evaluation until a body edit. Earlier binaries reject model6.
Complete-project metadata and combined control limits remain unchanged. See
[body controls](body_animation.md); independent per-axis editing remains unfinished.

Project manifests now retain full numeric precision in compact JSON, including
small recorded rotations. Older JSON remains readable and the1MiB metadata limit
is unchanged; recording estimates use the same precision. Strict multi-helper
reopen comparisons exposed the previous rounding. See body_animation.md and the
current progress memo for the actual verification scope.

Optional `video.lighting_mode` saves `unshaded`, `lit` or `studio` with no container
change. Missing fields retain old studio lighting. New projects choose unshaded;
packed/linked/recovery and final export use the same value. Invalid values are
rejected before writes/installation. Older binaries may ignore this field and use
their original lighting; use updated Studio for the selected view. See lighting.md.
