# Saved Miku hair/arm collision diagnosis

The protected stuff2 project contains one generated existing-joints spring with six rotating joints and one terminal endpoint, but **zero body colliders, collision groups, or per-chain collider memberships**. Its GLB has no native VRM spring/collider configuration either. This explains why the configured hair can cross the right arm: the generic spring solver receives no arm obstacle. This is a source/metadata finding, not a runtime reproduction or a completed fix.

The protected copy is 5,672,389 bytes, SHA256 036eb37fcb17d71e6292751bb1af4b73350512c69a0c31a59efb4fa6a4341101. ZIP central-directory and JSON metadata alone were inspected; no positions, indices, weights, texture pixels or normal arrays were inspected or published. The protected file remained byte/stamp-identical. Original owner file was not opened or written. Only bounded counts and file hashes are retained here.

## Existing implementation

- src/secondary_rig.gd:94–109 adapts explicit VRM1 sphere/capsule colliders and chain groups; 112–118 adapts VRM0 spheres. Lines195–199 deliberately reject generated-helper colliders/groups.
- src/secondary_spring.gd:20–25 constructs SpringBoneCollision sphere/capsule nodes. Lines64–69 install only the selected explicit colliders under each spring. Lines88–99 update collider transforms from their exact bone/node binding every tick.
- tools/secondary_helpers.py:630–631 and663–666 append springs and hitRadius=.005, without body colliders or collider groups. The radius gives a joint particle thickness; it does not create an arm obstacle.
- src/physics_rig.gd and src/physics_editor.gd build Jolt body/map collision objects. Generic springs do not query or attach those Jolt objects. Turning body Physics on does not bridge this gap.
- tests/secondary_motion_smoke.gd:181–192 compares an obstructed synthetic rig with colliders enabled/disabled. That proves an effect on pose, not full geometric nonpenetration.

## Smallest qualification sequence

1. Root opens an owned copy of the exact saved project in an isolated review snapshot. Confirm the model/asset hash, six exact configured source joint bindings, terminal binding, zero current memberships, and the saved fan transform/settings. Preserve all authored state, source bytes, IDs, materials, weights, camera, selection and history. Do not tune the fan to hide contact failure.
2. Run the existing saved fan scenario as the zero-collider control. Record only compact per-tick analytic distances and finite FK checks; keep any private visual capture local. The control must actually cross the intended right-arm region. If it does not, report that the repro was not reproduced.
3. In a private runtime definition only, add an explicitly reviewed sphere/capsule on the exact right upper-arm/forearm bone references, with locally specified endpoints/radius. Reuse Spring.construct(actor, private_definition, owned_host); do not alter the embedded GLB, native extension, generated-helper parser, original weights or project. Require positive uniform transforms and exact current bone ownership. Assign this collider to only the selected hair chain. No display-name or nearest-point identity inference.
4. Compare the same fixed 120Hz fan inputs and authored arm motion with/without that membership. Independently compute joint-particle-to-capsule signed clearance using actual world endpoints/radii and each joint radius. Check after every tick, not just a final screenshot. Verify the obstacle follows a bent/moving arm, and verify another chain does not inherit membership. Include scale .5/1/2 and translated/rotated parent controls. A pose difference alone is insufficient.
5. Measure BOTH scratch-solver output and the final visible FK after SecondaryLive's startup blend/angular smoothing. Smoothing can change the collision-resolved pose; it must not silently invalidate clearance. Starting rest intersections must be reported separately.
6. Check the hair chain segments and actual deformed hair against the arm independently. Sphere/capsule joint contact does not prove every intervening segment or weighted vertex remains outside. A joint-clearance pass is scoped to particle contact. If the owner case still clips between joints, add an explicit segment/swept-contact requirement rather than declaring success from endpoint clearance. Fast fan-driven crossing needs a per-tick tunneling control; do not assume discrete constraints are continuous collision detection.
7. Off/reset, restart, Record, Undo, packed/linked save and independent cold reopen must preserve the same explicit collider configuration and authored data before a user-facing fix is adopted. Recording budgets remain unchanged. No native PMX rigid-body equivalence or full cloth simulation claim follows from this bounded collider feature.

## Product boundary after qualification

The missing addition is a user-reviewable HAS body-collider setup shared with generated loose-part rigs. Persist exact HAS bone/path bindings, explicit sphere/capsule dimensions, and local per-chain membership in a separately versioned generated-HAS definition; native VRM groups remain immutable and cannot be borrowed by index. Validate and apply the complete definition atomically, and expose the actual collider preview plus a clear no-body-colliders state. Existing assets/default behavior stay unchanged until explicitly configured. No parser relaxation or production code is authored in this audit packet.

All runtime/native/GPU/contact/recording qualifications above remain UNRUN.
