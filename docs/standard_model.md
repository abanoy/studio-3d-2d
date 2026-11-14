# One standard model and pose contract

Both the environment and the character use the same self-contained GLB loader.
Native adapters prepare data for that loader; the pose editor never branches on
PMD, PMX, MDL or an add-on name. Maps, characters and groups use independent
instances in one HAS world, with shared geometry storage and separate poses.

## Future standardization direction — owner clarification, November 14, 2026

This is a recorded development target; it does not describe new implemented
support. Every imported source family must converge on HAS's own native model
representation. Evolve the current GLB/model metadata and portable HAS contract,
consistent with voice addendum sections 3.4–3.5; no new extension is selected here.
Preserved native features, reconstructed physics and part/material swaps can
make a HAS asset richer than its input. Faithful export back to the source format
is not required, and original source assets remain intact.

The planned pipeline inspects/preserves, translates, attempts supported repairs
or reviewed reconstruction, validates and saves a versioned HAS asset/report.
Target roughly 200 meaningful capability/integrity checks with stable IDs,
applicability and evidence. Keep original failures, proposed fixes and validated
outcomes distinct. Report PASS, REPAIRED_PASS, NEEDS_REVIEW, FAIL, UNSUPPORTED,
UNTESTED or NOT_APPLICABLE honestly; the exact catalog remains to be designed.
Missing optional physics on a static prop is not a failed character requirement.
Inferred rigs/weights/physics need editable review and explicit Apply/Undo.

Source-specific MDL, PMX and VRM adapters/fixtures feed this same contract. Work
depends on surviving content and adapter fidelity, not just extension; GMA is
an archive whose contained models/dependencies need their own checks. Preserve
authored declarations before estimating replacements, and disclose unsupported
behavior. Plan explicit HAS schema migrations and reader capability checks;
older readers may reject essential new data rather than silently lose it. This
does not authorize gratuitous breaks to existing project semantics.

See the [current pickup](NEXT_SESSION_PLAN_2026-11-13_SFM.md) and
[master reference, section 15](RESUME_MASTER_PLAN.md) for scope and validation.

Optional `metadata.source_shape` (`studio_source_shape_1`, boolean `enabled`)
selects declared imported default morph weights. New UI imports enable it; absent
means the prior neutral behavior for old projects. Advanced provides one-step
Undo/Redo without authoring a pose key. The loader binds exact source mesh instances;
runtime evaluation, helper review, bounds and collision geometry share the shape.
See secondary_motion.md for bounds and remaining expression-authoring limitations.

## Working interface

1. **Add scene** imports the environment. **Add model** adds a prepared character
   GLB or native PMD/PMX/VRM through local preparation without replacing other objects. The actual provided Miku fixture is at
   `output/compatibility/miku-tested/scene.glb` in this local delivery.
2. Choose **Pose model**. **Frame model** provides a temporary close view.
   Select a bone in the searchable hierarchy or click a visible joint.
3. Choose Rotate or Move, then Local or World axes. Drag a colored handle:
   red X, green Y, blue Z. A drag is one undo operation; Escape cancels it.
   Middle-drag pans the view and wheel zooms it. Camera free-flight remains in
   Scene/camera mode with the owner's existing mouse gestures.
4. Advanced reveals 15-degree/0.1-unit snapping, axis locks, local numeric XYZ,
   root uniform scale, reset and pose interpolation/deletion. Local numeric values
   are always local even when the viewport handles use World axes.
5. Select the model's root item to move/rotate/scale the whole character. Bone
   edits are offsets from the imported base pose; rotating a parent moves children.
6. Manual bone/root edits **automatically key the current master frame** by default.
   Pose frame0, then pose again at frame48 and scrub/play frames0–47. Purple
   diamonds distinguish model keys from camera keys and drawing exposures.
7. A completed drag, local-value edit, reset or scale change creates/updates one pose
   key in the same Undo command. Escape cancels without a key. Selection, scrubbing,
   visibility/reference flags and export do not create pose keys. Advanced > **Auto-key
   pose edits** can be turned off for the original static/draft workflow; then use
   **Record pose key** explicitly. Unrecorded drafts still save/recover. No initial
   rest key is invented. Auto-key defaults on each launch, separate from project data.
8. **Show model** affects preview/output. **Reference only** keeps it visible in
   the working preview but excludes it from exported frames/movie. Bone guides
   and handles are UI overlays and never enter exported imagery.
9. Frame model's view is temporary. Advanced > **Save view as camera key** stores
   it explicitly; existing camera keys require replacement confirmation.

Simple remains the launch default. Detailed controls do not change the underlying
model state when hidden. Pose controls are disabled when no model is loaded.

## Project record

New documents use schema4 worlds containing independent map/model/group records.
Legacy schema3's optional `model` and schema1/2 scenes remain readable. Both record
versions share the same geometry, rig, root, visibility, provenance and pose contract:

- `studio_model_1`: root position/quaternion/scale, working pose/draft and a single
  `pose_keys` curve, plus source SHA/path and native metadata.
- `studio_model_2`: the same identity/working fields with independently owned
  [animation pieces](animation_clips.md). Each piece retains its original source
  curve and time slice. Source adapters still emit version1; splitting/cutting/
  pasting promotes only the edited object. Other objects remain unchanged.

Version2 deliberately changes the record `format`; older apps reject it instead of
silently treating piece data as static version1 poses. HAS container/world versions
stay unchanged. Unknown native parameter fields remain inert data.

Bone identities combine the GLB checksum with skeleton-relative path/native bone
name. There is no guessed humanoid renaming or automatic retargeting. Reopening
validates bindings before replacing the live scene. Reimporting a changed GLB
at the same path rebuilds its runtime rig rather than reusing stale bones.

The renderer samples camera, root and bones at the same integer frame for preview
and export. Quaternion slerp interpolates rotations; position/scale interpolate
linearly with the selected easing. Native scene animation players are stopped
so they do not compete with the master frame clock. Source GLBs stay unchanged.

Current bounds:64world objects, up to512bones per object,241source keys per curve,
32pieces/2048total source keys per piece-based object,128MiB per GLB,1MiB
project manifest. Parameter reports above 256 KiB or invalid JSON produce an
explicit error rather than silently discarding their contents. These are prototype
limits, not general claims about model formats.

## Native compatibility and preservation limits

MMD preparation already provides standard skinning and native bone names. Actual
Miku has 126 runtime bones, including import helpers, and 15 morph channels. Posing
uses exactly the same code as the original two-bone fixture. Source/GMod conversion
now emits this same GLB/model record and attaches native metadata. The supplied
77-bone ValveBiped model uses these identical pose controls and timeline. Native
file selection invokes an isolated preparation worker; see source_import.md.

The supplied `parameters.json` is copied into the project record as metadata.
The full native/Blender preparation directory remains external: keep it intact.
Native PMD/PMX editing or lossless round-trip export is not implemented. Native
rigid bodies, constraints, IK, bone/material/group morph semantics, toon/sphere/edge
shading and Source bodygroups/flex/pose parameters are not made functional merely
by preserving their metadata. Facial morph controls are still pending. Imported IK/control bones do not solve IK;
use deforming FK bones (the Miku test uses 左腕).

Manual FK/root animation now includes validated hand/foot IK authoring; see
[limb posing](limb_posing.md). Approximate live ragdolls and solid unrigged/single-bone
props share a Simple toggle, grab/release and freeze; see
[physics](physics.md) and [Local/World recording](physics_recording.md). Native physics
fidelity and long dense capture remain limited. [Persistent contacts](contact_animation.md)
use versioned Model7 ranges. General
child world-position lock, bone scaling and pose libraries remain open.
Framing uses current posed skin/morph bounds with bounded fallback for large models;
see pose_framing.md. Rotation handles use a provisional screen-drag sensitivity;
physical mouse/tablet comfort and all rig/DPI combinations need owner feedback.

## Actual evidence

`python run.py --test pose` creates an original skinned GLB, exercises the real
bone tree, handles, world movement through a rotated/scaled parent, snapping/locks,
undo/redo, explicit pose recording, root/skin interpolation, save/reopen, malformed
bone rejection, recovery, reference exclusion and real MP4 export. On this machine
it also exercises the supplied prepared Miku: native arm selection, skin deformation,
animated export, frame-24 PNG equality and pose reopen with unchanged GLB SHA256.

`tests/autokey_smoke.gd` additionally checks default automatic keys at frames0/4,
easing, root/scale edits, overwrite/undo, completed/cancelled gizmos, unchanged-value
edits, explicit opt-out, HAS reopen and exact exported frame4. The original pose
runner deliberately turns Auto-key off to retain explicit draft/record regression coverage.

`python tests/verify.py` includes both runners and ffprobe checks for their movies:
1920×1080 H.264, 24 fps, 48 frames, 2 seconds. The actual Miku portion reports a
clear skip when that private local fixture is absent; original-rig checks remain
mandatory in a clean source checkout. Test output/native assets stay outside Git.

Primary APIs checked: [Skeleton3D](https://docs.godotengine.org/en/4.6/classes/class_skeleton3d.html)
and [Camera3D projection](https://docs.godotengine.org/en/4.6/classes/class_camera3d.html).
GMod workflow references and native conversion limitations remain in
[legacy_compatibility.md](legacy_compatibility.md). No GMod Lua or third-party
posing implementation is copied or executed.


## Multi-instance editor continuation

A prepared schema4 world now uses the same pose/root controls for all maps, actors
and groups. Renderer.active_model resolves the selected stable ID; legacy model data
is not reused as a hidden alias. World history targets object_id, preserving edits
across selection switches, and all-object snapshots feed HAS/directory/recovery saves.
Real combined MMD/GMod/SFM rigs are selected, deformed, auto-keyed, undone after a
selection switch and saved without changing original files. See world_editor.md.
Normal Add appends instances; schema4 New/Open/recovery restores the complete world.


Version3 adds persistent project-time visibility keys to the version2 motion-piece contract. Current readers accept all three versions; first visibility edit promotes only that object. Native GLB/rig identities remain unchanged. See visibility.md for fade, presence and material semantics.


Pose keys may carry optional authored_channels hints for the root/bones actually edited. These UI hints retain stable native IDs, validate against the rig and do not change whole-pose sampling or model format versions. Older snapshots infer channel rows. See animated_channels.md.


Direct hand/foot IK authoring now bakes solved rotations into these same ordinary
native-ID pose keys. No new format or playback constraint is needed. Simple body
labels and Advanced internal names remain presentation only. See limb_posing.md
and bone_names.md. Persistent foot ranges are separate Model7 constraints; broader
native/anatomical constraint fidelity remains unfinished.


Reviewed helper authoring can derive a new immutable standard GLB with appended
joints/skin weights/secondary metadata. Existing bone IDs/native mesh indices and
animation remain intact; generated_helpers metadata records source SHA and reviewed
parameters. Source originals remain untouched. Ordinary pose/take/HAS contracts
carry the result; no source-family-specific playback format. See secondary_motion.md.


Additional weighted helper chains use extras.has_secondary_helpers_1 in the
normalized GLB. Existing VRM0/1 or older HAS native extension data is retained and
adapted before generated additions. No new scene/pose/HAS version. Optional
metadata.generated_helper_history records ordered per-chain source provenance;
metadata.generated_helpers remains the latest report for backwards compatibility.


Reviewed helper reports may include region.vertex_mask, the exact original source
vertex indices expanded across welded UV seams. Generated assets preserve original
mesh indices and unselected weights; pinned cut boundaries keep the surrounding
surface attached. Multiple disjoint masks can coexist with existing chains in the
same standard model and retain ordered source revision history. This is optional
metadata/geometry, not a scene/pose/HAS schema change.

## Static base-shape adjustments

Advanced's **Base shape · whole project** uses the same per-source-node mesh
bindings as imported default shapes. Select a part and a named shape, enter an
Amount, then Apply. It affects every frame; no pose/camera key is made. Reset this
removes only that explicit adjustment; Reset all retains the imported-default
choice. Each applied edit uses existing model Undo. Physics is frozen before
changing its fitted geometry. Simple/Advanced toggles preserve the result.

An actual edit stores optional `metadata.source_shape` with
`format: "studio_source_shape_2"`, boolean `enabled`, and sparse `overrides`, e.g.
`{"3":{"0":0.2,"1":0.8}}`. Decimal source-node/shape indices identify bindings;
display names never rename them. Amounts are absolute weights, not deltas from
defaults. `enabled` chooses original imported defaults or zero beneath overrides.
Removing an override restores that inherited value. Version1 remains readable and
unchanged until edited; absent settings retain legacy neutral appearance. Earlier
Studio builds do not support version2; use this updated app to reopen adjusted
projects. Model/world/HAS container versions and source GLB bytes remain unchanged.

Validation permits up to2048 total finite overrides, absolute amount<=100, existing
source nodes and targets only, and preserves the existing2M active vertex-target
calculations per primitive/8M per operation. Prepare all affected geometry before
replacing cached data. A rejected later part cannot poison the earlier active
shape or Undo. CPU effective vertices/bounds and GPU values share one setting.
Actual native MMD/GMod/SFM positional channels are tested; native material/bone
morphs, VRM expression-group presets and animated expression tracks remain open.
Apply is explicit rather than continuous: a measured520-channel Scout edit took
about1.8seconds in development, versus about0.07–0.08seconds for MMD/GMod fixtures.
These are individual fixture timings, not broad performance guarantees.

## Animated shape versions4 and5

Model readers retain `studio_model_4` historical snapshot evaluation. It retains
version3 visibility and version2 source-time pieces, adding
`shape_base`, `shape_pose`, optional bounded `shape_names`, optional key `shapes`
and piece `base_shapes`. Values are absolute amounts identified by original numeric
source node/target. Original static amounts fill channels missing from older
snapshots; copy resolves them before transferring a piece. The same frame location,
interpolation, split/retime/gap and ordinary Undo/HAS contracts apply. Legacy readers
reject version4 rather than silently ignoring its animation. No world/container
version or native source rewrite. See shape_animation.md for authoring and limits.

New expression edits promote to `studio_model_5`: per-piece `shape_keys` are
independent of body `keys`, with separate draft/introduction addresses and optional
per-target interpolation choices at shared control frames. Expression-only pieces
do not anchor body gaps. Model4 promotion extracts its full old snapshots before
applying a new edit; it preserves old interpolation rather than silently repairing
authored motion. Combined body/expression controls count toward2048, with241 per
array and the same1MiB project cap. See shape_animation.md for exact field roles.

## Independent body version6

Normal body auto-key/IK/Record and selected-part deletion now use `studio_model_6`,
retaining dedicated expressions and original native geometry/IDs. Source snapshots
remain once per piece with legacy ownership; sparse per-part controls/deletion masks
preserve untouched easing. Optional shared recorded rest controls retain intentional
neutral keys for parts animated later. Per-part effective ranges permit normal take
growth without shifting peer curve endpoints; split/capture slices fix their bounds.
Models1–5 remain readable with their historical evaluation until explicitly edited.
Compiled per-revision source indexes feed preview/export and editable HAS/recovery.
Combined controls still obey2048/1MiB limits. Per-axis curves remain open; see
[body animation](body_animation.md) for fields, version behavior and verification.
