# VRoid / VRM importing and sample checks

Current: Add model accepts .vrm directly, with an asynchronous stdlib adapter into
the same native model path. VRM0 is rotated180degrees aroundY to match VRM1 +Z facing.
Humanoid node mappings/names, source identity, meta and expression bindings are retained
in native reports; complete native extension data remains in the normalized GLB.
Native .vroid parsing and full MToon/gaze/native-constraint semantics remain unfinished.
Shared limb posing and supported Hair & clothes simulation are available. Development
also offers [embedded expression poses](expression_presets.md); continuous native
expression animation and material/texture expression effects remain unfinished.
No VRoid Studio, Blender, game or plugin is needed for this VRM container adapter.

The following initial feasibility record is historical; the direct-import checkpoint
is recorded in progress_memo.md and tests/verify_native_import.py.

HAS is the destination format: import adapters translate external conventions into
the same native world/model/pose contract. A GLB holds geometry/textures/rigs inside
HAS; HAS owns hierarchy, animation, parameters and project packaging. Exporting assets
back to VRM, PMX or Source is not current scope. Retaining a native extension block
as provenance does not make its behavior implemented.

Owner samples: `AvatarSample_A.vrm` (VRM1.0), `AvatarSample_Avrm0.vrm` (VRM0.x),
and `model.vroid`, from VRoid Studio2.1.3. The installed application was found under
`C:/Users/noble/AppData/Local/Programs/VRoidStudio/2.1.3`; it was not launched or changed.

Both VRMs are self-contained glTF2 binary containers with3meshes,3skins,27images and
face morph geometry. The1.0 sample declares VRMC_vrm,VRMC_springBone and MToon;
the0.x sample declares VRM. Version conventions differ and need explicit adapters.
The `.vroid` is a separate4entry ZIP with metadata, opaque native `data.bin` and
a thumbnail. Its metadata records last update2.1.3. It is not a renamed VRM, and
native `.vroid` model parsing is not implemented. Prefer the supplied VRM export
for the first shared-model route; no compulsory online service or exporter-back path.

`python tests/verify_avatar_samples.py` prepares **test-only byte-identical GLB
copies** and native provenance reports under ignored output/. The normal shared
model path then tests each skeleton/arm, visible skin deformation, auto-key and
exact Undo, retained morph geometry, both versions coexisting, packed HAS save/
normal reopen, independent RGBA drawing and H2641080p24/48frame/2s export.
The wrapper checks source hashes/modification times and FFprobe metadata.
Private samples are optional and explicitly skip when absent; none enter source Git.

This is an actual runtime feasibility test, **not a shipping native VRM importer**.
No MToon fidelity, VRM0/1 orientation normalization, humanoid IK, springs, gaze,
first-person behavior, expression UI, license policy enforcement or VRMA playback
is implemented by merely reading the base glTF. Raw extension bytes stay in test
GLBs; schema metadata identifies losses. A product adapter must map supported
semantics and show understandable loss reports before advertising those features.

Primary source:
[VRM features and version differences](https://vrm.dev/en/vrm/vrm_features/).
The linked VRoid help article was inaccessible; no inaccessible documentation was
used as proof. The `.vroid` findings above come from its actual local archive index
and small metadata files, without decompressing the native model payload.

Worktree result:19actual checks pass; original SHA/mtime unchanged, packed reopen exact, H2641920x1080/24fps/48frames/2seconds. Both captured versions were inspected: VRM0 faces away from the same default view while VRM1 faces forward, confirming that version-specific orientation normalization is still needed. Initial test-script type/property errors were fixed; its watchdog ended the failed run before the corrected wrapper passed.

Canonical verification: the same19checks, source checks and full-HD MP4 probe pass from the requested Studio folder. Example packed project is output/avatar-samples/run_790538/avatars.has; local/private, not source-distributed.

Current adapter: tools/prepare_vrm.py bounds GLB128MiB/JSON16MiB, rejects external resources, validates version/humanoid indices, preserves BIN bytes and appends normalization wrappers without changing source indices. Eight authored preflight/normalization tests pass. Primary layout references: [VRM0](https://github.com/vrm-c/vrm-specification/blob/master/specification/0.0/README.md), [VRM1](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/README.md). Native extension behavior is explicitly reported as incomplete.

Direct native verification: `python tests/verify_native_import.py` always runs8authored VRM tests, then exercises the optional owner PMD/PMX/VRM inputs when present. MMD requires installed Blender/MMD Tools and Python3.11+ (tomllib); VRM needs Python stdlib only. Installed Python3.13.1 is used here.


Current runtime increment (2026-10-30): supported retained VRM0/1 springs are
adapted at normal GLB load into one HAS descriptor. Simple Hair & clothes and
Add fan now run those chains while posed or together with body Physics. Actual
Local/World Record, packed reopen and MP4 use ordinary native-ID FK takes.
This supersedes older no-spring-UI statements above; it does not reproduce native
MToon, gaze/first-person/expression behavior or full physical cloth constraints.
Missing-chain assessment/generated helpers with skin weights are still required.
See secondary_motion.md and the current progress checkpoint for exact evidence.


## Current cloud native samples, 2026-11-09

The four newly uploaded VRM files now have a [current receipt](benchmarks/native_vrm_2026-11-09.json). Sakuya, Marisa and both AvatarSample versions pass actual native-worker ingress, manual posing/UndoRedo, expression edits, supported native spring startup and generated HAS physics/freeze. Original source hashes, embedded BIN and source mesh/skin/material/morph definitions stay exact. Four packed projects cold reopen with exact authored pose, metadata, camera and GLB checksum while conversion bundles and writer cache are offline.

Sakuya exposed an unweighted terminal-helper case. Its real empty leaf offsets now serve as spring endpoints; no native bone or extra tail is invented. Geometry, camera, extension and collider-bearing helpers cannot silently use this path. The focused safety and existing spring regression pass.

The strict pixel assertions are retained: Sakuya and Avatar0 match exactly, while Avatar1 and Marisa each differ at one RGB pixel out of1920x1080 after cold reconstruction. This is a recorded limitation, not an exact-image pass. Native MToon, gaze/first-person, native constraints and procedural/material-expression effects remain diagnosed approximations or unsupported. The real24frame1080p24H264 movie was probed and decoded against the posed preview (51.23dB PSNR). No native assets or private projects are committed.

Reproduction uses private plans rather than distributing art: prepare each approved input with tools/prepare_vrm.py; pass a plans.json folder to tests/vrm_native_smoke.gd (writer, then --read in a new process with conversion/cache folders offline, and --physics separately) and tests/vrm_features_smoke.gd. Plans list name, glb, all original skin joint indices and the humanoid leftUpperArm node name as bone_suffix. tests/native_backend_smoke.gd also accepts a third argument containing file/member/actor/scale plans for actual native worker ingress. Run GUI cases only through run.command on an explicitly isolated display. tests/vrm_leaf_endpoint_unit.gd is headless. Exact failed checks must remain visible in receipts.
