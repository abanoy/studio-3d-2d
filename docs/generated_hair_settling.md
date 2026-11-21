# Generated hair: shape or gravity

After configuring generated HAS loose parts, the control beside **Hair & clothes** offers **Keep hair shape** and **Natural gravity**. Existing projects default to Keep. Pause live motion and close wind review before changing the choice.

Natural reduces the rest-shape bias and supplies world-down gravity. A recognized loose first joint can bend while its attachment position stays fixed. Declared humanoid and familiar body/limb joints are excluded; an ambiguous first joint retains its original tuning. Original joint settings, rest transforms, skin weights and imported physics declarations are not rewritten. The model-level choice saves normally and has ordinary Undo/Redo. Hair & clothes Off returns to the authored pose; use Record to retain a simulated take as FK keys for playback/export.

Both **Review local wind** and **Try a local blow** explicitly inherit the selected tuning. A disposable context binds the original model, candidate and checked groups, and refuses changed owners/settings. It carries only the mode and minimal exclusion/helper flags. Native and unopted private definitions retain their previous behavior. The existing checked group/collider selection is preserved; a filtered try-out does not acquire every contact participant from the complete scene.

The normal generated runner and opted-in previews also convert world airflow into the selected spring-center frame. This fixes front/back direction on rotated imported attachment axes. The conversion follows the center-space integration in the [pinned Godot 4.6 spring implementation](https://github.com/godotengine/godot/blob/4.6-stable/scene/3d/spring_bone_simulator_3d.cpp#L1624).

Natural surface correction first searches a downward clear orbit around the existing arm capsule, then falls back to the ordinary correction. Capsule dimensions, skin weights, attachment positions and collision tolerances remain unchanged. This is a bounded skeletal approximation, not general cloth contact or a guarantee that every intermediate pose is penetration-free.

## Verified and still open

Focused headless checks cover settings, gravity with rotated centers, both airflow directions, live/preview consistency, stale-context refusal, isolation/disposal, ordinary controls, Undo/Redo, packed save and a fresh-process reopen. The previous protected Miku contact contract is retained separately. See the scalar [benchmark record](benchmarks/generated_hair_settling_20261121.json) for exact results and source hashes.

The diagonal Junko request remains open. Her protected original has no configured helper chains. Enabling one supported existing four-joint chain preserves the original skin and adds only an unweighted endpoint. That chain touches 903 of the 5,600 vertices in hair-named material primitives: it cannot relax all back hair. A recorded trial lowered its terminal about 7 cm, but the entire affected geometry averaged only 7.6 mm lower, failing the retained 1 cm settling criterion. Final sampled skin contact pairs reached zero; transient penetration and significant CPU cost remain. This is not visual acceptance or a complete hair reconstruction.

Further work needs explicit reviewed setup of the other hair groups, appropriate additional degrees of freedom where the native weights lack them, and graphical checks of the full body and motion. Source-only preparation and headless geometry results do not establish appearance. No graphical verification or whole-suite result is claimed for this feature branch.

## Focused checks

Run `python tests/verify_generated_secondary_motion.py` on Windows. Its headless children use owned descendant Jobs and individual profiles, without desktop creation. The optional `--existing-source <read-only GLB> --region <node> <primitive> <component>` adds the existing-chain trial; the protected Junko trial intentionally remains a failing quality check.

The unchanged `tests/verify_secondary_body_contact.py` checks the prior Miku contract, with its documented three protected input arguments. A private-desktop lifecycle resource may require the approved host even though Godot itself runs headlessly. No visible fallback is used.
