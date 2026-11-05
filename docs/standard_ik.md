# Standard joint-chain declarations, posing and import baking

Fresh PMD/PMX preparation retains supported native IK as GLB asset extras under
`studio_ik_constraints`, format `studio_ik_constraints_1`, and in the readable
native report. Each chain identifies controller/effector skin-joint node indices,
ordered distal-to-proximal links, optional local XYZ rotation-delta limits in
radians, an iteration count and a maximum angular step. No humanoid-name guesses
or native plugin callbacks are required by the standard evaluator.

The MMD adapter reads declarations through the separately installed MMD Tools
parser. PMD knee conventions and PMX limits are converted to the imported local
joint basis. Unsupported/ambiguous chains are reported. Native append/inherited
bone movement is not evaluated; chains dependent on it are skipped as a whole
instead of presenting a partly deformed result as fully supported.

The bounded generic solver uses constrained CCD. Two-link hinges receive a
geometric bend seed to avoid poor convergence from nearly straight knees; the
seed respects the per-joint angular step and limits. Small rotations use an
atan2 angle calculation to avoid losing useful motion when float32 dot products
round to one. The evaluator changes joint rotations, not segment lengths.
Residuals and known single-link geometric reach limits are retained for review.
This is not a claim to reproduce every native MMD algorithm or pose exactly.

VPD/VMD preparation combines native controls with the actor's captured authored
FK baseline. Only affected chains run. An unrelated arm edit does not reset
legs merely because their native model declares IK. VMD IK switches are stepped
at their source frames. A disabled chain explicitly keys its original FK
baseline, preventing the previous baked IK result from remaining held.

Solved joints become the same editable FK body keys as other poses. HAS
playback/export does not run a separate MMD solver or need the native source
model. Existing geometry bytes remain unchanged when declarations are embedded.
The new metadata is portable in packed/linked HAS. Older prepared models retain
their prior FK behavior; reimport the original model to retain declarations.

With **Move limbs naturally** enabled (the default), selecting an exactly bound
imported joint controller and dragging its handles also poses its declared links.
Numeric Move/Rotate and Reset selected use the same authoring solver. Dependent
chains, such as Miku's toe following the foot control, run in declared order.
Release auto-keys all changed joints as one ordinary pose edit. Escape restores
the starting data; returning the pointer to the gesture origin restores the
starting pose without solver drift. Turn the switch off for direct FK edits.

This is an authoring assist. Results become ordinary editable FK keys; sparse
interpolation between them does **not** continuously enforce the imported target
constraint. Use Planted feet for a persistent foot lock. An active planted range
owns its leg joints and refuses competing native-controller edits until released.
There is no added per-frame native playback engine or file-format migration.
Older prepared GLBs need reimporting to retain declarations. Missing declarations
retain ordinary direct/natural-hand-foot posing. Known unsupported declarations
give guidance; invalid chains and nonuniform/negative scale refuse atomically.
Inherited transforms, native physics/bone morphs and broad native-rig fidelity
remain unfinished. Native visibility/camera/light tracks remain separate.

Limits: 64 chains, 32 links/chain, 256 iterations/chain, 32768 declared joint
steps/pose and 256 parent depth. Invalid topology, self-dependent targets and
invalid limits are refused/reported. Unreachable or unconverged targets keep the
bounded solved pose with a review notice; they are not hidden by stretching.
Dense motion still obeys the existing control/metadata budgets and worker time
limit. Solving/per-frame candidate construction needs further profiling.

## Actual verification

`python tests/verify_joint_constraints.py` checks the runtime solver against the
independently prepared Miku/PMX reference poses and Blender's Euler conversion.
Bone lengths and declared limits are checked, input poses remain unchanged, and
unsupported work budgets refuse. The runtime interprets local XYZ limits using
Godot's ZYX Euler composition to match the imported Rz*Ry*Rx rotation product.

`python tests/verify_joint_authoring.py` drives actual editor handles on the real
Miku and original PMX hinge: preview without keys, pointer return, Escape,
release/auto-key, unrelated FK, camera isolation, numeric/no-op/reset, opt-out,
invalid/unsupported/scale guards, planted-foot ownership, Undo/Redo, packed HAS
and two ordinary 48-frame H2641080p24 movies. Packed-reopened and exported frames
must match preview exactly with an independent drawing. Private-desktop receipts
and original source checksums are checked. These are targeted same-machine tests,
not physical mouse or artistic acceptance of arbitrary native rigs.

`tests/standard_ik_unit.py`, run in background Blender: nine constraint-domain
checks for reach, hinge limits, disabled FK restoration, unrelated-control
isolation, finite unreachable output and invalid chains. Mathutils float32
serialization is compared numerically, not against an exact Python decimal.

`tests/mmd_ik_reference.py`: retained real Miku, seven declared chains, an 8cm
left-foot lift with limited knee and toe, and a separately evaluated installed
MMD/Blender rig. The early plain CCD run missed the foot by 13mm. The hinge seed
reduced this below 0.03mm; small-angle refinement is covered by the final app
run. The toe has about a 4.45mm minimum geometric mismatch in this retained rig;
Blender reproduces a roughly 4.57mm toe mismatch. Its bounded result is checked
against that geometric lower bound, not silently declared perfect reach.

`python tests/verify_mmd_ik.py`: fresh raw PMD and original raw PMX preparation,
embedded declarations and unchanged geometry tail, actual VPD foot posing while
preserving unrelated manually posed limbs, VMD on/off/on switches with explicit
FK reset, Undo/Redo, packed HAS reopen and ordinary H2641080p24 movie with an
independent drawing and exact exported-frame agreement. An authored inherited
PMX chain is explicitly rejected as unsupported, both when its inherited source
is a solved link and when the source is a descendant of a solved link. Original input hashes and a
private-desktop receipt are checked. The tiny PMX fixture is original test
geometry, not a product exporter or broad model-corpus acceptance.

The external parser's [PMX importer](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/mmd_tools/core/pmx/importer.py)
and [PMD adapter](https://github.com/MMD-Blender/blender_mmd_tools/blob/main/mmd_tools/core/pmd/importer.py)
were inspected alongside the installed versions. Their code remains external;
the standard evaluator and normalization adapter here are original project code.
