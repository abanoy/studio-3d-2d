# Wind, hair and loose clothing — owner steering, 2026-10-30

The owner requested smooth hair/skirt motion without the jerking seen in MMD,
driven by a movable fan with adjustable blowing speed. HAS must also interpret
models that lack appropriate bones, assess whether regions are long/loose enough,
and provide its own helper joints/bones in the common native representation.
This is required development scope. Existing-chain fan motion is now usable as
described below; a first reviewed weighted-helper setup is also implemented.
Unskinned models and a complete garment/region editor remain unfinished.

### Parts already weighted to several native joints

Loose-part review offers **Use existing joints** for a validated linear native
chain when no single new-helper attachment can cover the selected vertices.
Review the orange shared regions and named chain, then choose **Enable these
existing joints**. The attachment and native joint positions are read-only in
this mode; small-patch isolation is unavailable because shared joints can move
other regions too. Ordinary weighted-helper generation remains a separate path.

This keeps original weights, skin, mesh/material data, binary buffers and poses.
The derived GLB adds an unweighted terminal endpoint and declares the existing
chain for simulation; the original file is preserved. Existing springs/helper
history remain intact. Setup is Undoable and portable. New node, combined spring
and coordinate bounds refuse oversized derivations before creating output.

Actual Bikini Reimu Back hair spans Head plus back_hair1/2/3 and had no eligible
single attachment. Its reviewed chain affects3connected regions/1369weighted
vertices. Pristine26checks and existing-ribbon composition29checks pass, with
exact posed pixels, real fan movement, off restoration, Undo/Redo, packed reopen
and24frame1080p24H264. The composition test seeds history from the actual ribbon
report; it is not a test of the owner's private recorded project. See
[evidence](benchmarks/back_hair_existing_joints_2026-11-12.json). Multiple selection
and per-item blow inclusion remain separate UI work.

### Scene-click selection and simpler chain review

While reviewing loose parts, click a visible part to suggest its connected region.
Orange outlines and the list show the guess; choose another list item to correct
it. Picking uses source bounds transformed by the current attachment joint, so it
is approximate rather than exact skinned-surface or occlusion selection. Dragging
still navigates, Ctrl retains camera controls, and Escape/focus loss cancels a
pending click. Clicking an already configured area clears the previous Apply
proposal and lets smaller-patch review start on that same component.

Simple now automatically reviews a validated existing chain when all ordinary
weighted attachments are unavailable. It still requires explicit Apply and shows
the shared affected areas. Unchecking **Use existing joints** is respected until
the selected part changes; Advanced and patch mode retain their explicit choices.
Reviewing, picking and correcting do not edit model data, keys or Undo history.
Actual native pristine30/ribbon-composed33 and focused20unit/25interaction checks
pass; see [selection evidence](benchmarks/secondary_part_picking_2026-11-12.json).

## Evidence and existing representation

Read-only inspection of the actual supplied VRMs confirms:

- AvatarSample_A.vrm: VRMC_springBone1.0,12springs and22colliders.
- AvatarSample_Avrm0.vrm: legacy secondaryAnimation,10bone groups and10collider groups;
  declared categories include Hair, Hood and HoodString.

The normalized immutable GLBs retain these native extensions and source indices.
At the first inventory checkpoint the parameter report only inventoried extension
names; it did not provide
a canonical spring-chain runtime or simulate those chains. Runtime bone bindings
must be resolved and validated, including duplicates and VRM0 facing normalization.
No need to invent an extra hair rig where suitable authored chains already exist.

Godot4.6 exposes SpringBoneSimulator3D with spring chains, stiffness/drag, external
force and separate spring colliders. Its scaled-rig caveat and branched-chain limit
need actual tests; API availability is not a passed native-wind workflow.
The installed4.6 engine was queried headlessly: simulator plus sphere, capsule and
plane spring-collider classes are present. No secondary simulation acceptance yet.
[Pinned documentation](https://docs.godotengine.org/en/4.6/classes/class_springbonesimulator3d.html).

## Required behavior and implementation gates

1. Adapt existing declared spring/cloth chains into source-independent HAS metadata,
   retaining native parameters/provenance. Validate chains, anchors, collision groups
   and unit/axis transforms against actual rendered deformation.
2. A fan is a scene object: position and aim determine a local airflow region, and
   its blowing speed is adjustable. Avoid replacing this with an unexplained global
   wind slider. Save its state in HAS; keep ordinary scene selection/manipulation.
3. Use stable fixed-step damped motion and bounded collision response. Test fan start,
   stop, direction/strength changes, moving anchors and timestep/render-rate changes.
   Smoothness must be measured and inspected, not inferred from a damping number.
4. Keep body ragdolls and secondary hair/clothing behavior separable so an authored,
   upright character can react to wind. Explicit Local/World Record must capture the
   resulting motion; scrubbing, save/reopen and MP4 must replay the same baked take.
5. Missing-bone assessment uses geometry, connected regions, material/seam clues,
   existing skin weights and head/hip/body anchors. Length alone cannot establish
   looseness. Show a correctable candidate region/anchor; preserve uncertain cases
   for inspection instead of guessing that every long surface is cloth.
6. Generated helpers need effective skin weights, not merely extra nodes. Store a
   derived native asset revision containing bones/weights/constraints, keep the
   imported original intact and retain existing bone identities and animation.
   Generated changes must be inspectable, undoable and portable in packed/linked HAS.
7. Preserve UVs/materials, unrelated geometry, body poses, camera, independent RGBA
   cels and audio. Validate native-helper budgets rather than silently dropping bones.

The first runtime experiment should use existing declared chains and an authored
hair/skirt fixture. Geometry-based helper generation follows a working stable
wind/record/replay path; it remains part of the objective, not an optional substitute.
Fan falloff/air-drag calibration, precision UI and the helper-generation algorithm
are engineering decisions still to be tested. No fluid-simulation fidelity claim.

## First declared-chain adapter and wind experiment — 2026-10-30

`secondary_rig.gd` now derives `studio_secondary_rig_1` from retained VRM0/1 GLB
extensions at normal GLB load. This runtime descriptor contains stable existing
bone IDs, node/offset bindings, ordered joint settings, centers and collider groups.
It is reconstructed from the embedded immutable GLB on reopen, not another project
schema or duplicated giant native report. Non-VRM models receive an empty descriptor.
Invalid secondary data disables that complete descriptor with a reason while the
ordinary model remains usable. No source geometry, weights, names or keys change.

Bindings use each exact imported GLTFNode's generated unique resource name and
skeleton association. Original-name matching is insufficient for duplicate/JP names.
The4.6 GLTFSkeleton bone map is empty on import; its node-path helper also errors on
some root bones. Neither is used. Non-skin terminal nodes retain offset bindings;
VRM0 root lists expand into unbranched chains with the specified7cm virtual tail.
Legacy collider Z offsets convert to glTF convention. Unsupported branched legacy
chains refuse with a reason; no first-child-only truncation. Limits128chains,
512rotating joints,256colliders; hierarchy, centers, numeric/list bounds validated.

`secondary_spring.gd` is an explicitly invoked experimental runner around installed
Godot SpringBoneSimulator3D. Scratch bones operate in unit world coordinates to
handle positive uniform model scale. Original rigs are not given live modifiers.
It accepts authored input, produces sparse ordinary FK offsets, supports sphere/
capsule groups and centers, and handles skipped intermediate source joints.
Setup awaits engine deferred configuration before tick zero. Stepping is explicit
at120Hz in the experiment; differing UI/render pacing must not advance it implicitly.
Use authored input each step, never last simulated output as the desired rest pose.
No normal app toggle or automatic spring activation is wired at this checkpoint.

`tests/verify_secondary_motion.py` runs original skinned hair/skirt geometry plus
optional actual owner VRM0/1 normalization workers. Both actual avatars produce
12chains/22colliders (VRM0's10groups contain12roots),34rotating bones. Tests include
wind on/off, matched moving-anchor no-wind controls, repeat render pacing, explicit
collision-disabled comparison, scaled/skipped-joint FK reconstruction, malformed
data/duplicate names, Undo and packed reopen. Experiment-only baked FK takes use
the existing range-replacement/Undo contract; they do not prove integration with
the normal Simple Local/World Record button. Authored take exports silent H264
1080p24/48frames/2s with exact reopened preview pixels. Native takes reopen with
native provenance and independent drawing/camera data; originals' SHA/mtime stay.

This is a proof of the declared-chain path, not finished hair/cloth quality. The
authored fixture settles after wind stops. Native hood/string gravity and initial
contact transients can move more strongly; initial observed maxima near9.8degrees
per120Hz step and differing VRM0/1 responses need calibration and visual review.
The20degree test ceiling is a gross discontinuity guard, not perceptual smoothness
acceptance. Force0.15 is an experimental coefficient, not calibrated fan speed.
Collision influence is tested, not universal surface nonpenetration or cloth
self-collision. Dynamic scale changes, multi-skeleton chains, animated map/wind
obstacles and long/dense capture budgets still need integration work.

Next: controlled initialization/settling and a saved movable fan with local airflow,
Simple secondary-only activation independent of body collapse, lifecycle-safe
Local/World recording, then the correctable missing-rig/helper/weights workflow.
All remain required; the experiment does not replace those product requirements.

Primary sources checked: [VRMC_springBone1.0](https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_springBone-1.0/README.md),
[Godot4.6 spring API](https://docs.godotengine.org/en/4.6/classes/class_springbonesimulator3d.html),
[pinned engine implementation](https://github.com/godotengine/godot/blob/4.6-stable/scene/3d/spring_bone_simulator_3d.cpp),
and [three-vrm3.5.3 loader](https://github.com/pixiv/three-vrm/blob/v3.5.3/packages/three-vrm-springbone/src/VRMSpringBoneLoaderPlugin.ts)
for the legacy collider-coordinate convention. Original adapter/wrapper/fixtures;
no third-party implementation copied, installed or redistributed.

## Current usable fan and secondary controls — 2026-10-30

Add and aim a fan first, then select a model with supported declared chains and
enable **Hair & clothes** in Simple. Its body stays posed. Enable **Physics** too for a ragdoll with secondary
motion; either activation order works. A malformed/unsupported descriptor disables
Hair & clothes with an explanation. A skinned model without declared chains
offers reviewed helper setup instead. Import activation remains manual.

**Add fan** creates an original selectable standard model. Move and rotate it with
ordinary root handles; its blue arrow points along the blowing direction (+Z).
Selecting the fan reveals **Fan on** and **Blowing speed** (0–50 relative strength,
0 stops wind). Nonlive fan root edits keep other live hair running. Root edits
auto-key normally; speed/on are scene settings, not animated channels. The field
has smooth width/range falloff, scales with positive uniform fan scale, and uses
defaults radius1/reach6 in scene units. These bounds currently have no precision UI.
Hidden/absent fans and hidden/absent parents emit no force; reference-only fans
remain useful in preview/capture. No airflow obstacle/fluid simulation is implied.
Adding/removing an object uses the existing world-rebuild stop barrier: add the
fan before activating motion, or select the character and enable motion again.

Supported chains use existing native settings with a 0.35s activation ramp,
0.15s force smoothing and a 180degrees/s cap on secondary rotation offsets
relative to the authored pose. This bounds initial snaps but may delay response
or soften contact response. Body animation itself is not rate limited. Fields are
sampled per chain at its anchor; they are not per-vertex aerodynamic forces.

Live motion creates no keys. Existing **Local Record** captures the selected
simulation; **World Record** captures all live models, including a moving physical
fan. Combined body/secondary samples become ordinary editable native-ID FK takes.
Secondary-only recording follows authored root/bone motion at120Hz, using fractional
sampling between integer authored frames. Project addresses and saved keys remain
integer/rational. Live unrecorded preview holds the activation pose/root.

Turning **Hair & clothes OFF** removes live secondary offsets and restores the
authored/current-frame pose, keeping manual drafts and recorded animation. It
does not author a freeze draft or add an Undo command. An existing body solver
continues running; cancelling unfinished hair setup preserves that borrowed body.
Turning **Physics OFF** still freezes the whole combined pose, stops both solvers
and supplies one Undo. If Record is active, switching off hair finishes the take
through the established recording stop/commit path.
Seek/play/save/export use the established stop/commit
barriers; New invalidates deferred setup. Static frozen poses save normally;
animated frozen drafts resume authored motion on scrub/reopen unless recorded.
Explicit Record is the reliable way to preserve moving hair. Cancel discards the
unfinished take; seek and Save keep the completed prefix. Recording audio preview
and dense/long-take limits are unchanged; see physics_recording.md.

Fan metadata (`studio_airflow_1`) lives in the standard model's validated metadata;
its original embedded GLB, root animation and settings travel through packed HAS.
No source format branch, mesh/weight rewrite or project-version migration occurs.
`SecondaryLive` composes the existing body solver and scratch spring runner, using
the existing capture/freeze contract and one simulation registry.

`tests/verify_fan_motion.py` covers normal controls/recording/HAS/MP4 and optional
actual VRM0/1 workers. The full verifier runs the authored fixture without private
assets. Matched raw/live native tests retain identical spring/field input: measured
maximum joint steps fell from18.13degrees (VRM1) /22.20degrees (VRM0) to1.50degrees
per120Hz tick. This is a bounded transition metric, not perceptual smoothness or
nonpenetration acceptance. No native MMD secondary adapter, cloth self-collision,
animated-map collision, dynamic scale or all-rig fidelity claim.

Next required increment: preview suitable unrigged loose regions using connectivity,
geometry, existing weights and anchors. Hair length or a material name alone cannot
establish looseness: long rigid accessories and close-fitting clothes must remain
correctable/excludable. Generate helpers **with effective skin weights** in an
immutable derived HAS asset, preserve original bones/UVs/materials/source provenance,
and verify deformation, Undo, packed/linked reopen and recorded replay. Adding empty
bones without influence on vertices does not satisfy that requirement.


## Reviewed weighted helper setup

Select a skinned model, then **Set up loose parts**. Existing spring-driven
regions are marked **already set up** and cannot be reweighted by this action.
Studio assesses connected surfaces and their existing weights. Select a part,
inspect its orange wire outline and pale proposed joints in the scene, and choose
a weighted attachment. Simple uses body-part names; Advanced exposes original
names and editable joint positions. Cancel keeps the original. **Add joints to
this part** creates a new immutable standard GLB revision as one Undo step.
Use Hair & clothes and an ordinary fan, then Local/World Record to retain motion.

**Hair & clothes** also opens this review when a skinned model has no declared
secondary chains. The toggle stays off until joints have been reviewed and added;
turn it on again to start simulation. Existing declared chains use the ordinary
simulation path. Source material labels identify the parts in the list. Opening
from Hair & clothes favors a usable hair/ribbon/clothing-labelled initial preview;
this hint does not classify surfaces or apply weights automatically. Every usable
region remains selectable and Apply is explicit.

For the supplied Bikini Reimu player model (`reimu_hakurei_bikini.mdl`), select
the model, turn on Hair & clothes, and review **Hair Acce** attached to the left
hair ribbon. Add joints, then turn Hair & clothes on again. Add/aim an ordinary
fan and press Record to keep the motion. The tested region has244vertices and
13pinned seam vertices; one Apply adds4weighted joints to the77-bone source.
Other connected hair surfaces lack a common weighted attachment and need manual
patch/attachment refinement. This is a reviewed part setup, not full automatic
hair/cloth rigging. The original GMA and converted source are preserved.

`tests/verify_reimu_helpers.py --prepared-source <scene.glb>` repeats the actual
native setup, Cancel, Undo/Redo, fan-off/on, Local Record, packed Save/cold Open
and24-frame1080p24H264 export. Keep the conversion's `parameters.json` sibling.
On Linux add `--isolated-display :N` for a provisioned private display; Windows
uses the existing hidden desktop launcher. Private models are not in Git.
See `docs/benchmarks/reimu_missing_helpers_2026-11-10.json` for scoped results.

The longest local extent and nearest-anchor cross-section estimate the attachment
edge. All vertices within a3percent cross-section band seed geodesic distances;
the estimated seam stays pinned, with a smooth weight ramp down the surface.
This avoids one-corner diagonal peeling. Preview reports the pinned vertex count.
The control-point positions can be corrected. A smaller patch can now be selected
as described below; its cut boundary is pinned to retain the surrounding surface. Shape cannot establish physical looseness:
a suggested part can still be a rigid ornament, face detail or close-fitting cloth.
Inspect it before applying. No automatic bone/weight changes happen on import.

Only the chosen connected component's existing attachment weight is redistributed.
Other joint weights remain;4influences can expand to8, while an overflow refuses
rather than pruning. UVs, materials, morph targets, original mesh indices, native
animation data and original bone names/IDs remain. Native clips are retained data,
not newly played by Studio. Inverse bind matrices preserve the existing rest shape.
Generated joints use the same secondary-rig adapter, FK posing, recording and
packed/linked HAS pipeline as existing springs, with retained source provenance.

Bounds: embedded128MiBGLB,512bones,100kvertices/200ktriangles per primitive,
500kvertices/1024regions per assessment,5000vertices per preview,2–8segments.
Sparse/compressed selected geometry, unskinned meshes, shared mesh instances,
unsupported weights and malformed inputs refuse with a reason. Assessment reports
skipped sections/truncation. Existing declared springs take priority on their weighted regions. Each Apply
authors one region/chain per immutable revision; repeat review for other regions.
The combined limit is128chains and512bones. Existing weights, chain parameters,
collider memberships and earlier pose keys are preserved. Connected garments can now receive reviewed patches; larger or more complex
regions still need a stronger region editor. Native MMD dynamics, cloth self/body collision, automatic stiffness
inference and generated full-body rigs remain unfinished.

`tests/verify_secondary_helpers.py` checks authored skin/UV/material preservation,
attachment seam,8weight overflow, actual review controls/Advanced correction,
visible deformation/Undo, fan/Record, independent RGBA/WAV, packed/linked HAS and
H264/AAC output. Optional prepared native MMD/GMod cases test source-index bindings
and weighted deformation; SFM receives read-only region assessment. These tests do
not certify that an automatically suggested native surface is physically loose,
or that every imported model can receive a generated rig. Windows graphical tests
run on the private hidden desktop; no visible fallback.


## Additional parts alongside existing springs

Review can now stay available after the first setup and on models with valid native
VRM0/1 chains. Any connected region using an existing spring joint (including a
tail) is protected from duplicate helper weights. In whole-part mode this can protect a connected garment with only a small
rigged section. Patch mode lets you select a separate unrigged area within it. Unrigged regions remain selectable and correctable.
Each Apply is one independent Undo/Redo step and keeps earlier generated-bone keys.

New chains live in GLB `extras.has_secondary_helpers_1`, with specVersion1.0 and
explicit joint settings/bindings. The loader appends these to the same standardized
secondary descriptor after the imported native adapter. Imported VRM0/1 data and
older HAS VRMC_springBone chains remain in their original JSON fields; adding a
helper cannot shadow legacy secondaryAnimation. Older generated assets remain
readable and augmentable. No project/HAS schema change or external exporter.

Generated additions currently carry no collision-group references of their own;
existing native chain/collider memberships remain exact. Authoring new helper/body
contact groups is still unfinished. Revisions retain per-chain source provenance
in the immutable asset and an ordered generated_helper_history in model metadata.
Normal Local/World Record captures the combined pose; packed HAS retains all chains
and takes. Unskinned/full-garment masks and subjective cloth fidelity remain open.


## Choose a smaller patch

Enable **Choose a smaller patch**, then drag a box on the scene. **Replace patch**
starts a new selection; **Add to patch** and **Remove from patch** refine it. **Whole
part** clears the mask. Escape or losing window focus cancels a rectangle without
changing the previous selection. Ctrl-left remains available for camera movement.
Switching patch mode off stops box selection while retaining the reviewed patch.

The box acts on the current connected part and includes front AND back vertices;
it does not use surface occlusion. Turn the view and inspect the orange area before
Apply. This is a bounded selection tool, not a semantic clothing recognizer, pressure
brush, lasso or front-surface picker. A component must fit the existing5000vertex
preview bound; selecting a small patch inside a larger component is not supported
yet. No scene geometry or source weights change during selection.

Only one connected patch can be applied per step. UV seam copies stay together.
Every cut-boundary vertex linked to the outside is pinned to its original weights,
so the surrounding body does not detach. Natural free hems remain free. Very thin
or entirely internal patches can have no free span; enlarge/refine them. The pinned
cut boundary replaces the nearest-anchor root estimate when it exists. Selected
source vertex indices are retained in the generated report/provenance.

In patch mode an already rigged whole component can be inspected. Apply remains
disabled for any selected area that overlaps existing spring weights. Choose a
separate unrigged area and an available attachment; earlier chain weights and keys
remain intact. This allows multiple reviewed patches on one original connected
surface. All unselected weights/UVs/materials/indices remain unchanged. Actual
cloth stretching, body/self contact, custom pin painting and unskinned assets still
need work; this uses weighted helper chains rather than a full cloth solver.

Focused tests route canvas input through zoom/pan and exercise Add/Remove,
disconnected-mask refusal/recovery, Escape/focus cancellation, camera priority,
visible patch deformation with identical surrounding pixels, ordinary pose/asset
Undo, two nonoverlapping patches, packed masks/history, real fan/Record/WAV,
portable reopen/seek and matching MP4 pixels. First invalid-mask preview fault was
fixed by retaining the last valid preview's joint points while the draft is invalid.


Review closes if playback or live motion starts, keeping the current asset.
Generated JSON is bounded to16MiB and bind transforms to the reader coordinate
range before writing. Preview follows skin poses; active/default nonzero morph
geometry still needs explicit selection-fidelity validation. Use neutral morphs
for this bounded patch workflow; morph-aware editing remains required work.

## Shape-aware authoring foundation (experimental, 2026-10-30)

The helper worker now accepts an explicit shape snapshot for assessment, preview and
immutable derivation. `source_morph_defaults: true` uses source node weights, then
mesh weights, then zero. `morph_weights` optionally maps canonical decimal source
node indices to complete weight arrays and overrides those defaults. Omitted shape
options keep the existing neutral review path unchanged. This is an experimental
worker contract, **not yet connected to the normal review UI**.

POSITION targets are deltas applied before skinning. Multiple signed weights,
strided float targets, sparse zero bases and sparse replacements are supported.
Component identities and seam groups come from the original geometry; attachment
coordinates, geodesic distances, preview wires, generated controls and inverse binds
use the evaluated shape. Morphing two formerly separate parts together must not
merge their review identities. Derived assets preserve original POSITION/targets,
default weights, source indices and BIN prefix. The report retains the effective
review weights. No destructive shape baking or facial animation channel is added.

Bounds:2048targets per shaped mesh, absolute weight100,100kvertices per primitive,
2million active vertex-target evaluations per primitive/8million per operation;
existing128MiB/16MiB JSON/512bones/5000preview limits remain. Malformed/sparse
references, counts, order, bounds, nonfinite values and unsupported target layouts
refuse. NORMAL/TANGENT targets are retained; helper positions do not evaluate them.
Quantized morph POSITION extensions need a separate adapter.

Actual GPU comparisons cover source defaults, an explicit signed mixture and a
partially sparse target. Godot's blend-shape bake agrees with CPU positions within
1.7e-7units in the authored fixtures; generated joints visibly deform those shaped
surfaces. These are authored tests, not native expression-fidelity certification.
`tests/verify_helper_morphs.py` runs these checks on the private hidden desktop.

A separate probe found that the current runtime loader leaves declared mesh/node
default weights at zero. Correcting new imports needs exact per-source-node mesh
bindings and a saved appearance setting that preserves older projects. Those UI/
loader steps remain required; the worker foundation does not claim to fix them.
Morph sliders/keys, material/bone expressions and MMD nonvertex morphs remain open.

Primary sources: [Khronos morph/instance specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#_morph_targets),
[Godot4.6 mesh blend-shape baking](https://docs.godotengine.org/en/4.6/classes/class_meshinstance3d.html#class-meshinstance3d-method-bake-mesh-from-current-blend-shape-mix),
[pinned loader source](https://github.com/godotengine/godot/blob/4.6-stable/modules/gltf/gltf_document.cpp).
Implementation is original; no third-party implementation code copied.

## Imported shapes in normal Studio (supersedes the experiment-only gate above)

New UI model/map imports enable their declared glTF default shape. Node weights
override mesh weights; omitted defaults are zero. Existing model records without
the new setting keep neutral appearance. Advanced **Use imported shape** opts an
older model in or returns a new model to neutral, with one Undo and no motion key.
Simple/Advanced switching leaves the setting active. It saves inside the ordinary
model metadata and packed/linked HAS; no source GLB changes or new ecosystem branch.

The loader tags GLTFNode resources before scene generation. Rendered instances are
identified by that tag plus exact generated mesh resource identity. The skinned
placeholder/child case uses the importer's unique resource_name plus the same exact
mesh identity; original display names are never guessed. Shared mesh nodes retain
independent weights. Unresolved identities/invalid defaults refuse when the imported
shape is requested, before replacing the current scene. Neutral old records remain
available. Reparented/root mesh cases are exercised by the actual UI test.

Review snapshots nonzero weights from those actual mesh instances and carries the
same snapshot through assessment, part/anchor changes, preview and Apply. Wires and
proposed joints follow the shaped skin. Immutable revisions preserve source morphs
and defaults. Cached effective POSITION arrays feed framing, initial placement,
static map collision, rigid prop hulls and ragdoll weighted fitting. Existing
geometry/triangle budgets remain; this does not establish native collider fidelity,
cloth contacts or animated map collision. Stored bounds describe shaped bind
geometry; arbitrary bone-pose bounds remain approximate as before.

The setting is `metadata.source_shape={format:"studio_source_shape_1",enabled:true}`.
It is optional and validated. Current Studio reads old projects without changing
their pixels. Earlier Studio binaries may ignore this newly introduced metadata;
use the updated Studio to reproduce projects that enable imported shapes.
This increment is static default-shape support, not general expression sliders,
expression animation, native material/bone morphs or complete VRM/MMD semantics.

Actual prepared Scout contains520targets in one mesh. The initial256target limit
was insufficient; the target-list bound is now2048, with the same2M/8M limits on
active vertex-target calculations. No targets are pruned. A separate high-index
GPU fixture checks target519; actual prepared MMD/GMod/SFM bindings are tested.

Advanced **Base shape · whole project** now supports explicit static imported-shape
amounts (version2 source_shape settings). Helper review snapshots their actual GPU
values; Apply preserves the adjustments and original channels in the immutable
weighted revision. Use imported shape changes only the defaults underneath those
overrides. Complete candidate preparation protects the active geometry cache if an
edit is refused. This does not add expression animation, material/bone morphs or
cloth physics; see standard_model.md for controls, compatibility and limits.

Model version4 expressions can now animate alongside generated helpers. Review
snapshots the expression at the current frame; immutable Apply retains its source
curves and bindings. Normal Local/World physics recording retains authored shape
amounts while capturing secondary/body poses, with shape bytes included in the
existing budget. Fits/collision shapes are constructed at activation, not rebuilt
continuously for changing morph geometry. Full cloth/contact semantics remain open.

Live pose refreshes preserve the lighting and parent opacity already applied by
the world evaluator, including after a peer import rebuild. Enabling Hair & clothes
in a new Unshaded scene no longer selects lit materials accidentally. This uses
transient instance context; no scene migration, new keys or source-material edit.
See lighting.md and verify_live_appearance.py for the focused regression scope.
