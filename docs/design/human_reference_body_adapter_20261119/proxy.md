# Unit-world shadow body adapter: source-only assessment

Status: design only. No adapter, fixture, engine run, native conversion, process
inspection or Git change was made for this assessment. The current refusal
guard remains the production boundary. None of the reasoning below qualifies
scaled body simulation.

## Smaller direct route: preferred first qualification target

The independent source review supports assessing the direct offset repair
before implementing the shadow architecture below. Let `W` be the actual
original world bone transform and `O_raw` the intended raw bone-to-body offset.
Define a desired physical frame `B = orthonormalized(W * O_raw)`, retaining
that product's origin, then set `O = W^-1 * B`. Algebraically `W * O = B` is
already unit and `B * O^-1 = W` restores the original scaled bone. With
positive uniform `W` scale `s`, `O` has inverse scale `1/s`, its raw center
translation stays unchanged, and physical shape dimensions use world units.
The existing callback's `S^-1 * B * O^-1` then returns the source global pose.

The engine's joint-origin clamp uses `O^-1.origin`, so it also scales the
body-to-bone pivot correctly. Joint reload orthonormalizes the parent frame
but passes the child frame to cone/hinge constraints directly: normalize the
final child joint basis explicitly. Offset setters reset rest placement but
do not reload constraints; finalize them before the initial joint-type setter,
whose reload must see the completed offsets. Reassigning an unchanged joint
type does not reload. [Pinned joint/setter source](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/scene/3d/physics/physical_bone_3d.cpp)

This is an unexecuted algebraic candidate, not adoption approval. Box dimensions,
capsule/sphere fallback radii, margins, centers, joint axes and source writeback
must be checked together. Current fallback sizing mixes a bone-local segment
length with a skeleton-space overall size; varying internal bone scales need a
coherent world-unit calculation, not blanket multiplication of every quantity
by one factor. If direct repair passes the geometric and lifecycle oracles it
preserves the existing modifier, final-bounds, canonical-ID, hair and Record
paths and avoids the proxy-specific integration hazards described below.

## Decision

A private unit-world skeleton is feasible for the existing positive-uniform,
unsheared, one-connected-skeleton ragdoll domain. It avoids asking a scaled
source skeleton to own PhysicalBone3D nodes. It is **not** a drop-in call to
`PhysicsRig.create(Model.new())`: collider input, canonical output conversion,
live publication, combined hair ordering and ownership all need explicit APIs.

Keep this as the fallback architecture while the smaller inverse-scale
`body_offset` repair is assessed. Both paths need the same geometric oracles;
a shadow implementation has substantially more integration surface.

“The proxy never modifies the source skeleton” must mean no changes to source
hierarchy, rests, bindings, geometry, import facts or serialized data, and no
proxy PhysicalBone modifier attached to it. Rendering motion necessarily still
updates the original skeleton's *live bone poses* through normal `Model.apply`.
A literal prohibition on those transient writes is incompatible with rendering
the existing skinned mesh.

## Pinned engine facts

In Godot 4.6-stable, `PhysicalBone3D.reset_to_rest_position()` orthonormalizes
the skeleton/bone/body-offset product; starting simulation makes the body
top-level. Its state callback maps a body back with skeleton inverse and inverse
body offset. `set_body_offset()` stores the supplied transform and its affine
inverse without normalizing its basis. These facts explain the current scale
loss and make inverse-scale offsets an alternative worth checking; the setter
alone does not prove correct contacts or constraints. [PhysicalBone3D source](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/scene/3d/physics/physical_bone_3d.cpp)

The simulator caches bone globals, refreshes non-simulated bones and applies
cached simulated globals in its modifier pass. Bindings use bone names and
indices. [PhysicalBoneSimulator3D source](https://raw.githubusercontent.com/godotengine/godot/4.6-stable/scene/3d/physics/physical_bone_simulator_3d.cpp)

The pinned engine's skeleton updates skins using modified global poses and
restores the pre-modifier local-pose backup afterward. Resetting poses copies
the rest transforms into position/rotation/scale. Therefore source inspection
outside the modification callback is not an authoritative solver sample.
[Skeleton3D source at 89cea1439](https://raw.githubusercontent.com/godotengine/godot/89cea1439/scene/3d/skeleton_3d.cpp)
The modifier signal fires after its processing call, and its skeleton is its
direct Skeleton3D parent. [SkeletonModifier3D source at 89cea1439](https://raw.githubusercontent.com/godotengine/godot/89cea1439/scene/3d/skeleton_modifier_3d.cpp)

## Coordinate contract

At activation, latch the actual evaluated original actor and skeleton transforms,
the immutable original local bone bases, and the original canonical initial FK
pose. Do not measure or reconstruct the six-foot basis again.

Let `S` be the original skeleton's world transform and `G_i` its evaluated
skeleton-space global bone transform. Let `W_i = S * G_i`. Each relevant
`W_i.basis` must pass the existing positive-uniform/unsheared checks. Let `s_i`
be its positive uniform scale. Define the unit bone world frame `P_i` by keeping
`W_i.origin` and orthonormalizing its basis.

Choose `H` as the original actor root world transform with an orthonormal basis
and unchanged origin. Put an invisible Node3D host under **renderer.world in the
same SubViewport/World3D** as the actual maps, other actors and props. Make that
host top-level and assign `H`; its Skeleton3D child has identity local transform.
The scene-tree root is not an acceptable host: Renderer owns a separate World3D.

Shadow global bones are `Q_i = H^-1 * P_i`. Shadow rest locals are
`Q_parent^-1 * Q_i`, or `Q_i` at a skeleton root. Build the full global table
before computing locals, preserving original index/parent tables rather than
assuming source index order is parent-first. Reset shadow poses to these baked
activation rests. The resulting world bone bases are unit while segment
positions already include original source size, artist scale, parent scale,
rotation and the single `C * rawB0` application.

Do not call `Model.capture_import_root()` or `Model.inventory()` on the shadow,
and do not give its baked transforms another artist scale or import factor.
Otherwise `C`, raw-root scale or both are applied twice. The shadow is a
transient solver representation, never a HAS asset or scene object.

For a solved physical body world transform `B_i` and its shadow body offset `O_i`,
recover the unit bone frame `P'_i = B_i * O_i^-1`. Restore the original world
scale to its basis while retaining its solved origin, giving `W'_i`. Convert
to original skeleton space with `G'_i = S^-1 * W'_i`; then obtain each original
local pose from its actual original parent. Delta position is local origin
minus the original immutable base origin; delta rotation is inverse original
base rotation times local rotation. These are ordinary canonical HAS FK values.

This conversion must retain the original local scale exactly: `Model.apply`
always restores `bones[id].base` scale and has no per-pose bone-scale channel.
Positive uniform scale makes child/parent scale ratios invariant under rigid
rotation. Refuse singular, reflected, sheared or otherwise non-representable
results rather than orthonormalizing them into apparently valid saved keys.

The common body's original parent may be outside the physical set. Its original
evaluated parent frame must remain in the conversion, not become identity.
Unsimulated descendants must be recomputed by original FK from canonical deltas;
do not retain their initial globals or copy proxy globals into source metadata.

## Reuse boundary and minimal APIs

| Area | Required boundary |
|---|---|
| Selection | Extract/reuse current chain, semantic extra-bone, lowest-common-ancestor and connecting-ancestor plan before allocation. Preserve original errors, one skeleton, 48 structural bodies and all existing budgets. |
| Identity | Manually map original canonical ID strings to shadow skeleton/index entries. Preserve names and parent-ID lookup; never replace saved IDs with shadow node paths. |
| Inner facade | Supply `root`, `order`, `bones`, `data.metadata`, `parent_id`, `bone_transform`, a shadow-baseline `sample`, and private live fields to the existing builder. A real Model with original data would sample deltas against the wrong baked rests. |
| Public adapter | Expose `rig = original_model`, canonical `bodies`, original-space `initial_pose`, `start`, `pose`, `capture_pose`, `root_transform`, `sync_visual`, `stop`, `dispose`. The inner facade must never escape into editor or Record. |
| Builder input | Allow a checked plan and explicit per-canonical-bone shadow bounds, rather than recomputing geometry from the meshless facade. Leave the legacy create path unchanged. |
| Mapping | One pure conversion of physical unit body frames into original-space canonical FK; one full original FK table for visual/framing output. |
| Publication | A composed-pose publication boundary, shared by body-only and body-plus-hair, which applies original Model live state and then publishes matching original-index final bounds globals. |

Existing `PhysicsRig.pose()` and `capture_pose()` compute deltas against
`inner.rig.bones[id].base`; those results cannot be forwarded. Its
`root_transform()` also cannot be forwarded. The outer root transform must
continue using the original actor:

`original_parent_world^-1 * original_root_world * original_base_root^-1`

This removes the original `C * rawB0` once and returns the existing artist root
channels. Preserve the current frozen-root ragdoll policy; do not silently
recenter the actor root around its fallen pelvis.

## Collider and joint correctness

The current `weighted_bounds()` reads original meshes/skins and excludes loose
hair/cloth descendants when fitting structural bodies. A meshless facade would
silently produce no weighted boxes, changing contact behavior to capsule/sphere
fallbacks. Compute the existing source bone-local AABBs from the original actor,
then convert each through `P_i^-1 * W_i`. In the admitted domain that transform
is positive uniform scale: box centers and dimensions become physical units
without changing bone-relative axes. Feed these bounds explicitly to the inner
builder. Keep mesh/vertex/helper exclusion limits unchanged.

Segment-based fallback lengths and body-size fractions must come from the
baked shadow positions. Margins, offsets, capsule radii and box sizes must all
be in those same physical units. Existing joint axis/hinge/cone construction
can then operate on unit shadow bases. Choosing `H` from the original actor
orientation preserves the root-forward fallback when anatomical landmarks are
missing. Keep canonical self-collision parent/nearby tests and actual body
shapes; do not infer new collision exclusions from proxy node ancestry.

This makes the dimensions and frames coherent; it does not establish the right
mass distribution, damping, collision fidelity or simulation stability at all
reference sizes. Those remain separate qualification questions.

## Integration contracts that cannot be skipped

**Original model identity.** PhysicsEditor detects nested simulated actors via
`simulation.rig.root`, associates grabs through canonical `bodies`, and Record
copies/compares `simulation.rig.data`. All must see the original actor. Keep the
private proxy in the same physics world but outside authored World objects and
render/mesh inventories.

**Fixed tick versus render.** Record prefers `capture_pose()` and samples body
transforms at the fixed tick; it must map those direct body samples, not a
previous rendered modifier cache. `pose()` may use the last complete visual
sample for existing Freeze behavior, but its coordinate conversion must match.
Do not advance physics or run an extra modifier pass merely to answer either
query. Continue the existing recording interpolation and metadata budgets.

**Hair composition.** `SecondaryLive` borrows a primary, copies its body
dictionary and reads its canonical `capture_pose()`. Body/hair overlapping
joint refusal must continue using original IDs. PhysicsEditor can assign the
primary's `initial_pose` from the preexisting secondary wrapper: that property
must remain a canonical original-pose contract, not a shadow rest dictionary.

There is a concrete new-ordering hazard: `SecondaryLive.sync_visual()` calls
`primary.sync_visual()` and then only assigns `rig.live_pose = latest`. A new
primary that applies its body-only pose at that call would overwrite rendered
hair without reapplying the final composed pose. Separate body sampling/root
sync from final pose publication, or explicitly publish/apply the composed
secondary result afterward. Publish bounds globals **after the final body +
hair pose**, with all original skeleton indices; a body-only `FINAL_META` would
make framing disagree with rendered loose parts. Imported Source-motion plus
body remains refused by the existing independent backend gate.

**Off and lifecycle.** Physics Off currently freezes a canonical pose/root draft
with validation, contact release and ordinary Undo; hair Off restores authored
hair while retaining a borrowed primary. Preserve those behaviors. Make outer
disposal idempotent if the original actor or renderer world was already freed;
clear original final metadata only when its weak owner belongs to this adapter.
Stop/free the inner solver and host without writing source data, rests or shape
settings. Detaching a primary from SecondaryLive must transfer ownership rather
than free the still-running proxy. All failure paths before installation must
leave original live/authored state and topology unchanged.

**Parent/root changes.** Latch a coherent original `S` and root frame. If an
external edit, reparent, source replacement or incompatible ancestor transform
invalidates that frame, stop/refuse through existing lifecycle handling; do not
quietly reinterpret cached world scales. Keep current nested-live-body limits.

## Smallest qualification sequence before adoption

1. Prove activation and mapping round trips on authored positive-uniform rigs:
   source/intrinsic/artist/parent scale, rotated imported roots, translations,
   compensating factors, selected connectors and a nonphysical parent above
   the lowest common ancestor. Check every relevant local scale is representable.
2. Compare actual physical body frames, original FK reconstruction, weighted
   collider corners/centers, joint pivots/axes and original-index framing globals
   at tick zero and after controlled motion. Retain a same-size legacy control.
3. Exercise fixed-tick Record/replay, Freeze/Undo, held-foot release, actual map
   contacts and grab ownership; preserve exact basis/lineage and source bytes.
4. Exercise body + generic hair ordering, hair Off, body Off, pending cancellation,
   borrowed-primary transfer, renderer replacement and disposal. Native backend
   exclusions remain exclusions. Only then repeat a private prepared-VRM review.

No step above has been executed for this proposal. Prefer the smaller direct
offset route if its pinned-engine algebra and geometric oracles can be proven;
the shadow route remains an explicit fallback rather than an assumed shortcut.
