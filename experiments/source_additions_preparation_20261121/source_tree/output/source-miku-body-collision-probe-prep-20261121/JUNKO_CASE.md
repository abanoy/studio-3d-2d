# Distinct owner-reported Junko settling case

The owner reports Junko GMOD hair remaining diagonally behind her, wants it to settle down behind the body while retaining curls, then react to actor movement without crossing the body. The supplied screenshot was viewed locally only and is not copied or uploaded. It shows the reported diagonal long-hair silhouette and curled ends; a still image establishes neither the active solver path nor a trajectory/contact failure.

The unchanged protected stuff2.has SHA036eb37f... contains the separately investigated Miku generated rig. It is **not a reproduced saved Junko project**. No actual Junko rest-pose, fan, root movement, baked keys, gravity or collision run has been performed for this report.

## Confirmed current source behavior

- Generated HAS chains in tools/secondary_helpers.py supply stiffness1, drag.45, radius.005 and no gravityPower. SecondaryRig.settings defaults gravityPower to0. Thus that route has no gravity unless explicitly authored/imported. Spring constructs its rest from the authored pose and feeds authored local rotations again at each tick; it does not reconstruct a hanging rest pose.
- Exact admitted Junko native motion is a different route: source_secondary.gd calls Chains.create with world gravity[0,-1,0]. source_chain_math.gd scales the retained length and tip_mass by source scale. SourceJiggleMath.solve_one adds that downward acceleration while yaw/pitch springs pull toward the authored goal basis and the retained cone constrains deviation. Retained native parameters use about45degrees, not a free-hanging rope. Curled geometry and authored goal orientations are preserved rather than classified by a hair name.
- The shipped bounded native route selects five exact rule owners. The separate all49 candidate preserves the49 retained coefficients/hierarchy, but is not yet a qualified back-hair settling feature. Any explicit generic/helper chain takes priority over the native route.
- Generic SecondaryLive applies startup blending and a180degree/second rotation-rate limit after the engine spring result. A raw solver contact pass therefore does not alone prove the visible pose remains outside the body.
- When body Physics is absent and Record is inactive, SecondaryLive uses the initial authored pose/world transform. Native preview stops on timeline seeking. Under Record it instead samples actor/parent movement at each rational fixed tick. World-space spring state can then lag a moving anchor, but the owner's requested continuous movement workflow remains to be qualified. Body/fan movement and gravity/rest-pose changes must be measured separately.

## Smallest honest Junko probe after an exact saved case is supplied/staged

1. Identify the actual active route from exact source hash + helper definition + native resolution, and distinguish authored rest pose from recorded/baked FK keys. Record counts/status only; preserve the original style and all IDs.
2. With fan absent/disabled, compare authored baseline, native/generic no-gravity control where appropriate, and the actual configured gravity. Measure per-chain attachment/endpoint trajectories and rest-relative angular offsets. Do not rotate every bone whose display name resembles hair.
3. If the desired hanging baseline lies outside retained cone/rest directions, treat this as explicit reviewed rest-pose reconstruction: propose a reversible rest/pose adjustment on the selected chain/roots, preserve internal curl relationships and skin weights, show a preview, and require ordinary Undo for adoption. Do not silently replace retained native coefficients or label the reconstruction recovered PMX physics.
4. On the chosen rest baseline, add independently reviewed body sphere/capsule geometry and qualify clearance separately (see the saved-Miku probe). Segment/skin clearance, not just particle endpoints, remains necessary for the visual promise.
5. Use the same bounded actor translation/rotation path twice, with and without fan, at120Hz; compare zero movement/rest recovery and repeated replay. Scope actor inertia, fan response, gravity and collision as four separate measurements. Then qualify Off/reset, Record/bake, Undo and independent cold reopen before adoption.

No Junko implementation/default change or solved-case claim is made by this note.
