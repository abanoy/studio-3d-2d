# Body Physics at an explicit human-reference size

Status: source-only design, 2026-11-19. No adapter is implemented here. No test,
Godot/native application, process query or Git command was run for this design.
The existing safe refusal remains the product behavior until a candidate earns
its own evidence. This note accompanies the independent `proxy.md` assessment.

Worktree: `C:/a/Programming/cloudflare/has-height-addition-20261119`.

## Recommendation and next visible addition

The next addition should let an explicitly normalized humanoid use Body Physics
at its current size, including relative size 0.5 and 2, while keeping ordinary
posing, Hair & clothes, Freeze and Record. It should not change the meaning of
Scale 1 or introduce another saved model representation.

The smallest promising route is **direct world-space body planning with an
inverse bone-to-body offset**, rather than only multiplying collider radii.
Prove its rest-pose/writeback identities on the pinned engine before selecting
it. A unit-world shadow skeleton is a viable fallback, but has a much larger
canonical-pose and visual-composition boundary. Neither route is certified by
the current legacy physics passes.

## Observed contracts that the adapter must preserve

These are source observations, not new execution results.

- `model.gd::capture_import_root` saves raw B0 once; `base_root = C * B0`.
  `Model.apply` evaluates the artist transform outside that base. Canonical
  bone bases, IDs, source hashes, `asset_basis` and lineage are not rewritten.
- `physics_editor.gd::enable_body` stores a simulation whose `rig` is the
  **original Model**. It selects `PhysicsRig` for structural skeletons and the
  separate world-baked `PhysicsProp` path for solid props. Simulated nested
  parent/child objects remain refused. Grabbing identifies ownership through
  the simulation's canonical-ID `bodies` dictionary.
- `physics_rig.gd::create` selects validated limb chains, adds connecting
  ancestors up to their common ancestor, retains one skeleton and a 48-body
  limit, and computes profiles plus weighted bounds. Its current shape sizes
  and body offsets use source skeleton/bone-local units.
- `weighted_bounds` uses `SourceShape.vertices` and actual skin poses/binds,
  supports four/eight influences, and excludes loose hair/cloth branches from
  rigid torso bounds. Preserve that ownership policy and the 100,000-vertex
  budget. An adapter must not silently replace valid skin-fitted boxes with
  generic capsules just because its private rig has no meshes.
- `PhysicsRig.capture_pose` reads physical body transforms at the fixed tick;
  `pose` uses captured modifier output. Both return ordinary original-ID
  deltas from `Model.bones[id].base`. `root_transform` removes the actual
  parent and `base_root`, so saved scale is the artist multiplier, not C.
- `physics_recording.gd::read_state` consumes that pose/root contract. It keeps
  the original authored data as the capture target, refuses data drift, uses
  existing budgets, and commits ordinary editable motion with one history
  operation. Saving/playing a take must not start a fresh simulation.
- `physics_editor.gd::freeze` validates and commits the returned pose/root,
  then stops/disposes the solver. Body Physics Off freezes; Hair & clothes Off
  restores authored loose-part pose and can keep the primary body alive.
- `secondary_live.gd` wraps the original actor and borrows the primary solver.
  Its `initial_pose` and the primary's public `initial_pose` are canonical
  source poses. Its shared `bodies` keys detect conflicting rotating joints.
  The existing native Source-hair/body exclusion remains in effect.
- `pose_bounds.gd::FINAL_META` contains a complete array of **original
  skeleton-space** global poses with a live weak owner. Unit-world proxy
  transforms must never be placed into that array.

## Why the safe refusal is necessary

For notation, S is the original skeleton world transform, G_i is a bone's
skeleton-space global pose, W_i = S * G_i, and O_i is its body offset.

The pinned engine derives a physical world frame from the orthonormalized
product W_i * O_i. Its writeback uses S^-1 * B_i * O_i^-1. The offset setter
stores an affine inverse; editor offset adjustment itself derives the offset
from bone-world inverse times body-world. Starting simulation makes bodies
top-level. These observations come from the official
[Godot 4.6 PhysicalBone3D source](https://raw.githubusercontent.com/godotengine/godot/4.6/scene/3d/physics/physical_bone_3d.cpp),
especially `reset_to_rest_position`, `_body_state_changed`, `set_body_offset`,
`update_offset` and `_start_physics_simulation`.

Consequently, raw collider dimensions do not inherit C from the skeleton.
The old unscaled O_i also fails to invert a world frame whose scale was removed.
The earlier idea to repair only `physics_self_collision.gd` was withdrawn:
its current radii describe the actual unit-basis physical shapes. Construction,
offsets and writeback must agree first. No self-collision change is proposed.

## Route A: direct repair in the existing PhysicalBone rig

### The exact boundary to prove

For each structural bone, choose a desired positive **unit-basis** physical
world frame B_i. Its origin is the desired collider center; its orientation
aligns the chosen box/capsule/sphere. Set the conceptual offset to:

`O_i = W_i.affine_inverse() * B_i`

For the existing raw unit-basis offset R_i, one concrete construction is
`B_i = (W_i * R_i).orthonormalized()`. This retains the intended transformed
center and orientation while deriving inverse scale in O_i automatically.

Then W_i * O_i is already unit-basis. Stripping scale has no mathematical
effect, and S^-1 * B_i * O_i^-1 reconstructs G_i at rest. Under later unit
physical motion it restores the source bone's original world scale rather
than canceling the visible model's C.

This identity is a design inference from the observed formulas. It has **not**
been tried on the pinned executable/Jolt. In particular, nonunit O_i bases,
joint setup/reset ordering, modifier restoration and fixed-tick writeback need
the independent oracles below. Do not mistake an accepted setter for successful
physics support.

### Shape and joint units

- Plan shape points in B_i coordinates. For an original bone-local point p,
  use `B_i^-1 * W_i * p`. This handles actual artist, parent, raw-root and C
  contributions once, without reading only `data.scale`.
- A skin-fitted box can use the existing bone-local weighted AABB, with its
  eight corners transformed into the chosen unit body frame. Derive its
  actual size/center from those transformed corners. Keep the loose-part
  exclusion and shape-ownership rules.
- Capsules use actual world segment length/radius and a unit body orientation;
  spheres use a radius in world metres. Review the current mixed bone-local
  length/skeleton-local size clamps when a source has local bone scale. A
  global scalar applied to every old variable is insufficient for that case.
- Existing metre-based margins, penetration slop and gravity remain metre
  quantities. Do not multiply gravity, mass or angular limits by C merely to
  obtain visually similar trajectories at different physical sizes.
- Derive the anatomical joint's desired unit world frame and express it
  through B_i^-1. `configure_joint` currently includes `body_offset.basis`
  inverse; a new nonunit offset must not leave scale in the joint basis.
  Check the engine's clamped joint origin after setting offsets, and verify
  both connected frames at the actual source bone pivot.
- Preserve initial construction order: install the final body offset and joint
  orientation before assigning the initial joint type. Offset setters reset
  placement but are not a substitute for rebuilding an existing constraint;
  assigning the same joint type again can return without reloading it. Do not
  build the old constraint and patch its scale afterward. The independent
  source assessment in `proxy.md` also flags this ordering boundary.

The `configure_joint` correction has a specific algebraic oracle. Write the
raw offset rotation as R_o, original bone skeleton-space rotation as R_g,
world uniform bone scale as s_i, and unit skeleton-space anatomical profile
basis as P. The current expression becomes
`s_i * R_o^-1 * R_g^-1 * P` with the corrected O_i. Its final basis must be
orthonormalized, yielding `R_o^-1 * R_g^-1 * P`; after multiplication by the
physical body world rotation its axes are the intended skeleton-world profile
axes. Preserve the offset origin already obtained from O_i^-1. It is
`-s_i * R_o^-1 * raw_center`, in physical metres, so the world joint origin
lands exactly on the original bone pivot. Normalizing the complete transform
or replacing that origin with the unscaled raw center would break this result.
This derivation assumes the already-required positive uniform unsheared frames;
it is not evidence of a successful native joint run.

The original skeleton, simulator callback, canonical pose capture, root
conversion, `FINAL_META`, primary-body ownership and editor lifecycle can then
remain the existing path. That is the principal reason to prefer proving this
route before adding an entire shadow-model abstraction.

### Metric thresholds: plan in metre frames, not raw source units

Multiplying the final shape size by C is insufficient even when every original
bone has unit local scale. The current `max(raw_span, 0.01)` and valid-child
distance `> 0.0001` can choose different proxies for a very small or large raw
skeleton that later becomes the same six-foot visible figure. World size must
be established before those decisions.

One precise planning frame is F, the original skeleton world transform with
its basis orthonormalized. Its axes preserve the existing skeleton-aligned
policy; its coordinates are metres. Use `F^-1 * W_i.origin` for structural
bone points, and compute their enclosing diagonal in that frame. Thus a pure
rotation of the whole scene does not change its span policy. A bone-centered
unit frame H_i likewise expresses child directions and weighted bounds in
physical metres. Keep separate source/raw values only for constructing O_i.

| Existing decision | Unit-world planning interpretation |
|---|---|
| Structural zero-length rejection `< 0.00001` | Already evaluated by `actor.bone_transform`; retain the 10-micrometre world check. |
| `size = max(raw skeleton diagonal, 0.01)` | Use `max(metre-frame skeleton diagonal, 0.01 metre)`, before radius/shape selection. |
| Child direction eligible `> 0.0001` | Use the bone-centered unit-frame child offset; threshold is 0.1 millimetre in the scene. |
| Nearest-child distance and `length` | Compare metre lengths, not inverse scaled bone-space lengths. |
| Radius clamp `length * .16`, `size * .012` through `size * .045` | All operands are metre lengths. |
| Weighted bounds length in `.005 * size` through `.75 * size` | Convert bounds to a unit bone/body frame before the comparison. This also avoids mixing scaled bone units with skeleton units. |
| Capsule decision `length > .025 * size` | Both values use the same physical metric. |
| Box padding `Vector3.ONE * size * .003` | Add metre padding to the transformed metre box dimensions. |
| Box margin `min(.005, smallest_shape_extent * .025)` | Evaluate after shape conversion: cap remains five millimetres; do not multiply it by C. |
| Existing self-contact geometric epsilons | Unit physical body/shape frames make their distances metre quantities; no C-specific self-collision patch. |

This describes the new active-reference planning branch. It does not silently
retune old saved actors. Unit-reference control cases must demonstrate that
changing representation alone preserves the intended existing proxy choice.
Actual very small visible characters can still encounter the deliberate metre
floors; those are distinct from a tiny raw source normalized to ordinary size.

### Minimum implementation boundary if Route A qualifies

1. Add an ephemeral, bounded body-geometry plan for active nonunit references:
   original IDs; actual source transforms; unit body/joint frames; offsets;
   shape descriptions. Perform full input/scale/size/budget validation before
   adding any simulator/body. No saved schema or source-mesh changes.
2. Allocate through the existing rig using that plan. Keep legacy and already
   unit-world models on their old behavior. Keep the safe error until the
   new path is explicitly qualified; do not remove it speculatively.
3. Reuse the existing canonical `capture_pose`, `pose`, `root_transform`,
   `start`, `stop` and `dispose` contracts only after independent rest/reset
   and changed-body writeback comparisons demonstrate they remain correct.
4. Exercise Freeze/Record/Undo/reopen and combined generic Hair & clothes
   before offering the new path in the existing Body Physics toggle.

Do not temporarily remove C from the original scene root, scale its rests or
skin bind matrices, or compensate by changing the artist's saved scale. Those
approaches would disturb source identity, picking, hair, interpolation and HAS
roundtrips.

## Route B: unit-world shadow skeleton feeding the existing rig

### What the shadow represents

Choose H0 as the original model's current root-world transform with unit basis.
For every original bone, let H_i retain W_i's actual origin and orthonormal
orientation. Build a complete shadow hierarchy with world frames H_i and local
parent-relative frames. The shadow root/skeleton world bases must be unit.

Its owner must occupy the **same renderer SubViewport/World3D as map and prop
colliders**. A top-level Node3D below `renderer.world`, with an explicitly set
unit world frame, is a possible boundary. Do not copy the secondary spring
runner's SceneTree-root placement without checking physics-world membership.
The root orientation H0 matters because `PhysicsRig.profiles` uses the root's
forward axis as an anatomical fallback.

Use a private facade keyed manually by the original canonical IDs. Do not call
`Model.inventory` and invent shadow-path IDs, or `capture_import_root` and apply
C to world-baked geometry again. The facade supplies the narrow fields and
methods actually consumed by IK/PhysicsRig (`root`, `data`, `order`, `bones`,
`parent_id`, `bone_transform`, `sample`, live state), with private copied data.
It is runtime machinery, not another serialized HAS Model.

The editor-facing wrapper's `rig` must remain the **original** actor, and its
public `initial_pose` remains the original canonical pose. Its internal
PhysicsRig points at the facade. Editor reassignment of `initial_pose` when
combining hair must update the outer contract, not replace the shadow baseline.

### Boundaries that cannot simply forward to the inner rig

- **Weighted geometry:** convert original bone-local bounds through
  `H_i^-1 * W_i`, or independently evaluate current skinned vertices. Add an
  explicit bounded planning input to the inner factory; facade meshes cannot
  silently disappear. Avoid cloning entire meshes/skins merely to persuade
  `weighted_bounds` to find them.
- **Pose output:** inner deltas are relative to shadow bases. Read actual
  physical frames, restore each original bone's retained positive world scale,
  convert through the original S and original parents, and subtract original
  bases. Merge unsimulated joints from the complete original authored pose.
  Preserve helper ancestry and original local scale. Never forward the inner
  `pose`/`capture_pose` dictionaries as source poses.
- **Root output:** use the original parent/current original world root and
  original `base_root`. Inner `root_transform` would remove the facade base
  instead and return the wrong artist transform. Keep the existing choice of
  encoding ragdoll movement in bone poses; do not silently extract hips into
  new object motion.
- **Live visuals:** publish body output to the original model once per accepted
  fixed-step state. Render-time reads must not advance/reset physics. An outer
  `sync_visual` that applies body-only FK can overwrite hair: current
  `Secondary.sync_visual` calls the primary and then assigns its combined
  `latest` without immediately applying it. Explicitly order body snapshot,
  generic spring composition and final original-model application.
- **Bounds:** any authoritative final-pose metadata must contain all original
  bone indices in original skeleton space, including unsimulated descendants
  and final hair composition. Since the original skeleton would have no live
  physical modifier, normal Model FK plus `PoseBounds.palette` may suffice
  without original `FINAL_META`; this is unverified and must be demonstrated.
  Do not introduce a stale body-only metadata palette to solve a proxy issue.
- **Teardown:** remove only the adapter's host/solver and its own metadata;
  preserve the original model, source descriptors and a still-running primary
  when Hair & clothes is detached. Borrowed-wrapper cancellation remains safe.

The shadow route has a clearer unit-only engine surface, but doubles the pose,
ownership and visual-composition mapping. It needs a new wrapper and planning
hook rather than a shallow `Model.new()` clone.

## Independent oracles and a bounded qualification sequence

These are planned acceptance checks, not tests run by this task. Use actual
world factors 0.5, 1 and 2, with rotated/translated B0, nonzero imported origin,
rotated/scaled static parents, an intermediate helper bone, source local scale
where supported, and distinct artist multipliers. Include cases where C and
artist/parent scale compensate to the same world geometry.

1. **Rest identity before stepping:** an independent geometric oracle derives
   bone pivots and weighted fixture vertices directly from known fixture
   values. Physical shape corners/ends/radii must be in the expected world
   positions, joint pivots agree, and reset plus fixed-tick capture reproduces
   the original pose without a scale-dependent translation or pop. Do not use
   the candidate planner as the expected-value generator.
2. **Known body movement/writeback:** with gravity disabled, apply a known
   rigid world transform to a body. Compare independently reconstructed source
   FK and representative skinned vertices with the resulting rendered model.
   Verify original bone/local scales and C/B0 remain unchanged. Then test real
   engine stepping and modifier/reset behavior.
3. **Actual collision oracle:** compare independent Jolt shape queries/contact
   points against analytic original fixtures at the floor and a box. Check
   sphere/capsule/box geometry, skin corners, neighboring overlap exclusions
   and distant-part collisions. Reuse established world-space tolerances only
   where justified, and report actual maxima. A passing unit-size control
   alone does not admit 0.5/2.
4. **Equivalent geometry, equivalent representation:** redistribute the same
   total scale between C, artist multiplier and a static parent, preserving
   actual initial world geometry. Collider/world-pose results should agree.
   Do not require equal real-time trajectories between physically different
   sizes: fixed metre gravity does not make a twice-sized pendulum move on the
   same clock.
5. **Live controls and bounds:** grab/toss, settle, select/frame the actual
   deformed source, render with ordinary source materials/morphs, then Freeze.
   Compare the last live source geometry against frozen FK, Undo/Redo and cold
   packed reopen. No doubled C, disappearing material, stale framing or extra
   source inventory is acceptable.
6. **Record lifecycle:** Local and World capture at existing fixed/rational
   timing; Stop and Escape; scrub; cold reopen; preview/movie agreement.
   Original root animation components and canonical pose/shape identities
   survive. A take records editable canonical motion, not a proxy scene.
7. **Hair composition/lifetime:** enable generic declared loose parts before
   and after Body Physics, verify body and hair joint sets remain disjoint,
   toggle hair off/on while body continues, and test cancellation during
   pending setup. Compare original hair/base transforms and final framing.
   Keep the current unsupported native Source-hair/body combination refused.
8. **Atomicity and isolation:** unsupported reflected/nonuniform/sheared input,
   singular/oversized geometry and changed preparation state refuse before
   allocation. Snapshots cover original data, bases, raw/C roots, source/lineage,
   mesh/skin/shape data, live pose, topology and history. Teardown leaves no
   adapter nodes, callbacks, owned metadata or simulation recording state.

First implement the chosen adapter and these focused mechanical/lifecycle
checks as one reviewable addition. Run the affected existing physics, recording,
secondary, framing and human-reference checks afterward. Broader verification
follows an actual integration; repeated unrelated normal startup probes do not
answer the body-scale question.

For the first candidate, report qualified factors 0.5/1/2 explicitly. Later
bounded representation oracles should encode the same ordinary physical figure
with much smaller/larger raw bone coordinates and compensating factors near
the accepted import limits, including fixtures immediately around the old
`.01` span floor and `.0001` raw-child threshold. Those tests must check proxy
selection, shape dimensions, reciprocal-offset conditioning and finite complete
writeback, rather than merely successful import. Accepted import metadata does
not itself certify engine physics at every extreme. Keep a clear refusal for
unqualified or numerically unsafe cases.

## Remaining limits

The current 48-body/one-skeleton/positive-uniform restrictions, source geometry
budgets and nested live-body exclusions are still design boundaries. This note
does not add deformable cloth, PMX solver fidelity, new collision shapes, scale
animation during a live take or broader Source native motion support. Data or
effective-scale drift while a solver owns a frozen preparation must fail safely
or use an explicit existing stop/rebuild policy; it must not retune silently.
