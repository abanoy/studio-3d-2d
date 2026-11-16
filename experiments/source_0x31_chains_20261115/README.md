# Parent-first Source0x31 chain candidate

**Implemented experimental code; CPU synthetic checks PASS. All new GDScript is UNPARSED/UNRUN. No production integration or native-chain qualification.** Root declared source context `9de4e6c`; this child did not invoke Git, engines, parsers, apps or process inspection. Original models, production source and the retained single-rule candidates were not changed. Read source SHA256 values are in `READ_SOURCE_HASHES.json`.

The bounded native subset is **17(parent7)→18 and26(parent25)→27**. Both child bones are leaves. Native25 remains authored and unsimulated in this four-rule experiment, although its separate retained Source rule still exists. All49 original rules and69 bindings remain inactive/current. This is a subset experiment, not the complete Junko native chain system. `PUBLIC_PROFILE.json` records exact retained coefficients, parents, prefix hashes, input hashes and measured influence counts without positions, normals, UVs or native rest arrays.

## Goal and pose contract

1. Clear the previous temporary overlay, apply the current authored baseline once, and capture every bone's **absolute parent-local pose**. The initial actual probe refuses an active body/live-world owner. A later body integration needs its own tests.
2. Traverse actual parents before children, with stable ordering independent of rule/native/Gltf index order. Unsimulated intermediate bones also pass through this traversal.
3. For each bone, `goalWorld = effectiveParentWorld * authoredLocal`. A rule replaces that goal's world orientation while retaining its base position and uniform size. Descendants use this **same-tick solved parent**, their original authored local translation/orientation/scale, and their own persistent tip state. The previous live result is never reinterpreted as an authored local goal.
4. Reconstruct the Model delta with `deltaRotation = inverse(baseRotation) * inverse(effectiveParentWorldRotation) * desiredWorldRotation`. Model.apply already computes `baseRotation * deltaRotation`; Skeleton global pose already computes `parentGlobal * absoluteLocalPose`. Applying a further rest transform double counts it.
5. Start the full output pose from a deep copy of the complete sampled authored pose. Override only the four selected rotation channels and preserve their authored translation channels. `Model.live_pose` is a complete replacement, so a sparse four-bone pose is invalid as an integration strategy.
6. Skeleton roots use **Skeleton.global_transform** as the prefix. They do not assume that Model.root and Skeleton.global_transform are equal.

This is an explicit HAS orchestration policy. The local pinned Valve packet contains the solver receiving `goalMX`, but no caller establishing the exact closed Source-client procedural traversal. **Native SDK/client parent-policy parity is unproved.** The SDK was read, not compiled or executed. The existing120Hz clock, raw0x31 refusal policy, global downward acceleration, native+Z tip axis, exact zero-cone handling and solver constraints remain unchanged.

GLB local positions already contain source scale0.01905. Only native rule length and tip_mass downward acceleration receive `0.01905 * actual positive uniform world size`. World acceleration inputs are already in HAS world units and receive no extra source factor. Root-size changes require reset/replay. This is not a mapping from the actual fan's controls.

## Code and checks

- `chain_solver.py`: immutable scalar64 frames, topology, rule-local state, staged actor-wide commit and desired-world-to-Model delta matrices. It imports the retained Python candidate only after checking SHA256 `dd472f2b4de64adebc83a03c2e812ac2e14805c752b220c26c53dd58bf99519c`.
- `check_chains.py`: independent rational first impulse and child force/Euler calculation, stale-parent and double-rest negative controls, unsimulated intermediate FK, authored channels, order invariance, isolation/replay, late-child failure atomicity, unit covariance, cone/length bounds and zero-cone/strong finite input cases. It also compares two simultaneous parent-shaped branches with independently owned branch-only actors. Latest CPU result (`CPU_RESULT_two_pairs.json`): **3,681 checks,0 failures**, maximum numerical difference `4.440892098500626e-16`;1,424 completed actor steps/3,088 rule evaluations. These are synthetic CPU results.
- `chain_solver.gd`: equivalent scalar64 orchestration over the unchanged qualified GDScript math candidate. No Node registration or automatic processing.
- `math_checks.gd`: a proposed root-invoked synthetic check object, including the independently derived first impulse and1,000 tilted zero-cone parent/child cases, mutable snapshot/result/input cases and refusals. **UNPARSED/UNRUN**.
- `model_adapter.gd`: the bounded actual Model/binding profile, qualified float32→scalar64 boundary adapter, explicit parent/local closure and complete pose overlay. Raw float32 matrices are never described as meeting strict1e-9 orthonormal math input. Boundary correction and actual transport gates remain **2e-5**.
- `chain_capture.gd`: a narrow derivative of the qualified CPU weighted capture. Its sole functional change is membership in an explicit selected bone set. Mesh/skin geometry remains in memory; only aggregate counts/hashes leave it.
- `chain_harness.gd`: proposed actual headless harness inheriting the qualified compat3 leaf harness. It has a separate root lease format and refuses to run under the old leaf lease.

Reproduce the CPU checks with the approved Python, bytecode disabled, and a fresh result filename:

```powershell
& 'C:\Program Files\Python313\python.exe' -B experiments/source_0x31_chains_20261115/check_chains.py --result CPU_RESULT_rerun.json
```

`CPU_RESULT.json`/`check_chains_attempt1.py` preserve the initial2,601-check run. That result's manually entered `dynamic_ticks=820` counter was inaccurate; the final run corrects the count and adds480 independent cone assertions. `prepare_packet_attempt1.py` plus `PREPARATION_HISTORY.json` preserve the exact metadata assertion that caught an erroneous draft assumption that native26 had parent7. The corrected metadata is25. No failed observation is relabelled as a pass.

## Root-only next actual increment

After root source review and a fresh, closed runtime lease, stage these exact sources in an isolated owned project containing the pinned actual application source:

| Staged path | Source |
| --- | --- |
| `leaf_candidate.gd` | `experiments/source_0x31_godot_candidate_20261115/candidate.gd` |
| `leaf_adapter.gd`, `weighted_capture.gd`, `leaf_harness.gd` | Unchanged files from `experiments/source_0x31_native_leaf_compat_20261115` |
| `chain_solver.gd`, `model_adapter.gd`, `chain_capture.gd`, `chain_harness.gd`, `math_checks.gd` | This directory |

Use **`ROOT_LEASE_READY_TEMPLATE.json`** only as an **unapproved source-only template**, updating all predecessor/closure proof pins, approved engine SHA256, expiry, fresh aggregate result and staged source paths. The earlier `ROOT_LEASE_TEMPLATE.json` is an intermediate unrun draft; the ready template binds the final packet sources. Its expected approval phase is `ROOT_APPROVED_AFTER_FULL_FK_MATH_LEAF_AND_CLOSURE`; the inherited leaf harness never accepts this format. Root must preserve first actual parse/runtime failures in fresh attempt paths. The script target for a later leased actual run is `chain_harness.gd`; this preparation did not execute it. Root can first preload `math_checks.gd` and call `new().run()` in a separate bounded synthetic harness.

The proposed actual probe uses two root placements/scales, six acceleration profiles per placement,120ticks/profile (1,440actor ticks/5,760rule evaluations if it completes). It checks all69 baseline FK frames against actualModel before dynamics; then four desired/actual orientations, native+Z tips, same-tick parent origins,65 unselected world bones and authored sample preservation at each tick. Exact CPU-read input influence counts are:

| Selected set | Weighted vertices | Shared with other bones | Zero-selected-weight vertices |
| --- | ---: | ---: | ---: |
|17,18,26,27 |542 |340 |9,119 |
|17,18 |184 |118 |9,477 |
|26,27 |358 |222 |9,303 |

These are counts from the retainedGLB's9,661vertices/four surfaces, not measured motion. Proposed motion gates require each pair to deform, differ from gravity control under temporary±3/12/50 world acceleration, repeat exactly, preserve unaffected regions exactly, and restore all bone/rest/data/key/weighted state exactly through `live_pose=null; Model.apply` at authored frames24and12.

The unchanged imported-modifier guard is called through native17(parent7) for the common Skeleton context. It permits only the already measured single empty native internal/direct `PhysicalBoneSimulator3D`, no script, not simulating, and zero actualPhysicalBone3D descendants anywhere in the actor. It rejects active bodies/foreign modifiers/final-pose owners; it never disables/removes engine nodes. Native26's actual parent25 is independently checked by the bridge. The private compatibility flag remains unmeasured.

Actual full native49-rule motion, SDK/client/artist parity, GPU rendering, actual body/fan/Record/seek/serialization integration, PMX reconstruction and canonical six-foot standardization remain unqualified or unimplemented. The historical2e-5 normal-fidelity failure remains failed; this work does not address or waive it.
