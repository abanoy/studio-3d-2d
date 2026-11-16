# Actual FrontHair1 leaf readiness preparation — November 15, 2026

**SOURCE ONLY: leaf GDScript UNPARSED / runtime UNRUN.** No engine or parser was
launched by this preparation. It is not a product feature or whole native solver.
There is no class_name, @tool, autoload, editor registration or project change.

## Exact source profile

Read-only CPU inspection confirms the original qualified GLB/report/MDL/VVD hashes
in `PUBLIC_PROFILE.json`. Native8 is FrontHair1, parent7, with no descendants.
Its actual retained0x31 rule uses stiffness100 in both transverse axes, damping5,
length20, tipMass20 and angle0.7853981852531433. It does not use the generic50
prototype default. Source conversion is exactly0.01905.

The four primitives contain9,661 vertices:152 receive native8 influence,144 of
those also receive other bones, and9,509 have zero native8 influence. These counts
were measured from skin bindings/weights, without publishing coordinates, normals
or other private geometry. The runtime harness must establish them again using
the actual loaded MeshInstance/Skin/Skeleton indices, not assume bind slot8.

## Guarded live-pose derivation

`Model.live_pose` replaces the complete sampled pose. The harness copies
`actor.sample(frame,false)`, changes only the selected leaf rotation and retains
its authored position and every other channel. It creates a disposable nonrest
keyed fixture at frames0/24; no original project or source file is edited.

Godot4.6 stores an absolute parent-local bone pose. Its enabled-bone world pose
is parent-world times that local pose, while Model.apply sets local rotation to
base rotation times authored delta. Thus:

`delta = inverse(base_rotation) * inverse(parent_world_rotation) * desired_world_rotation`

An independent source audit verified [immutable Godot4.6 Skeleton code](https://github.com/godotengine/godot/blob/89cea143987d564363e15d207438530651d943ac/scene/3d/skeleton_3d.cpp#L1106).
Exact source hash and reset/pose anchors are in STATIC_PREPARATION.json. This
supports the derivation; it is not a runtime pass. The harness independently
requires actual `parentWorld * localPose` closure within2e-5, then tests an
authored orientation roundtrip before dynamics. It refuses rest-only/disabled
bones, descendants, foreign modifiers/final-pose caches or a different parent.
Parentless bones would need a skeleton-world prefix and are deliberately excluded.

`leaf_adapter.gd` first rejects nonpositive, mirrored, nonuniform or sheared
transforms. It uses scalar64 Gram-Schmidt only after the declared2e-5 positive-
uniform boundary check, and bounds the correction by that same gate. The resulting
scalar64 basis must satisfy the math candidate's unchanged1e-9 validator. Raw
float32 engine matrices are not claimed to meet that strict mathematical domain.

The GLB/rest translations already contain0.01905. Only native length and tipMass
acceleration are multiplied by `0.01905 * actual_uniform_world_scale`, exactly
once. World gravity stays HAS-global-Y. This tests the existing source asset
at root scales1/2; it does not implement the new six-foot-normalized scale1 asset.

## Proposed bounded execution

Root must first establish complete default, actual FK and scalar64 Godot math
PASS plus authoritative process closure, then review the source and create a
fresh root lease. The current template deliberately authorizes nothing.

Stage the200 files in SOURCE_LOCK.json unchanged into a fresh owned runtime
snapshot, including the existing project/run/main files. Add these aliases:

- the previously executed mathematical `candidate.gd` SHA14053abf… as
  `leaf_candidate.gd`;
- `leaf_adapter.gd`, `weighted_capture.gd` and `leaf_harness.gd` from this packet.

The retained GLB must have its hash-locked parameters.json adjacent, and original
MDL/VVD/proof bytes stay read-only. Use only the approved headless/private engine
policy. The harness requires root-approved phase
`ROOT_APPROVED_AFTER_FULL_FK_MATH_AND_CLOSURE`, PASS statuses, root_closed_all,
future expiry, exact engine/source/proof pins and a fresh public result path.
Root remains responsible for interpreting receipts and owning/reaping the process.

The proposed run has two root contexts (identity scale1 and moved/rotated scale2),
with control and signed transverse synthetic world accelerations3,12,50, plus
an exact cleared-state repeat. Each uses120 ticks at120Hz. These are temporary
acceleration inputs, not HAS fan-speed units or native Source fan behavior.

Every tick compares desired/math versus actual leaf world orientation and native-Z
tip, preserves authored position, all68 other world bones and the sampled keys.
The actual mesh arrays/shape decoder/skin palette drive a CPU weighted query.
Private point arrays stay in memory; only aggregate counts/errors/hashes are saved.
Mesh transforms, arrays and the9,509 zero-weight region must remain exact. Shared
influences are disclosed rather than mislabelled as unrelated body deformation.

Off-style clear uses `live_pose=null` and actual Model.apply, restoring both the
current keyed frame24 and nonrest frame12. Data/keys/base/rest/pose snapshots and
all weighted points must restore exactly. Repeated12-input cycles must yield
identical weighted hashes. Imported source metadata stays inert/unchanged.

## Preregistered gates and remaining limits

World/basis reconstruction/orientation use2e-5, and virtual-tip/origin distance
uses2e-5 times root scale, matching the existing FK precision boundary. Meaningful
weighted displacement uses1e-5 times root scale; unaffected regions, source data,
mesh arrays and Off restoration use exact private-byte/hash equality. These gates
are declared before this leaf engine parse/run; preserve failures without relaxing
them after observation.

Success would establish only this one imported leaf's temporary live-pose transport,
CPU weighted deformation and direct clear/apply restoration. It would not certify
GPU skinning/render appearance, native SDK execution, artist parity, procedural
parent chains, GUI toggle behavior, body/fan coexistence, Record/Undo, saved HAS
or movie output. Existing generic helpers and installed Studio remain unchanged.

PUBLIC_PROFILE.json is an actual CPU metadata/weight observation. Everything
about leaf engine execution remains **UNPARSED/UNRUN**. Do not mistake previous
41,588-FK/8,994-math results for this new application/deformation test.
