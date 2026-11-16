# Proposed qualification of the retained49-rule Junko profile

This is a metadata and source blueprint. No49-rule application backend or actual49-rule motion probe was implemented or run here. The shipping bounded backend remains the separately qualified FrontHair1 rule. The four-rule pair experiment is a separate root-owned runtime task; this plan does not assume its outcome.

The exact retained profile has69 bones and49 rules, all with flags0x31 (flexible, angle constraint and length constraint), no unknown flag bits, and two parameter/prefix groups:17 rules with yaw/pitch stiffness100 and32 with stiffness50. The source metadata remains `retained_inert`, `applied=false` and `full_native_rule_layout_verified=false`. Qualifying all49 owners of this bounded120-byte rule prefix would still leave complete SDK layout, Source-client traversal/timing and artist motion parity unproved.

## Exact topology to cover

There are26 independent rule branches:13 singletons,5 chains of two,6 chains of three and2 chains of four. The current pair subset covers17→18 and26→27. The additional root/chain groups are:

| Group | Native branches | Extra behavior |
| --- | --- | --- |
| Front fringe |8 through16, each a singleton | Nine stiffness100 siblings under authored7 |
| Side hair |19→20;21,22,23,24 singletons | Mirrored side branch and four stiffness50 siblings |
| Remaining two-step hair |29→30;32→33 | Authored parents28 and31 |
| Three-step back hair |35→36→37;39→40→41;43→44→45;47→48→49;51→52→53;55→56→57 | Greater same-tick depth, authored roots34/38/42/46/50/54 |
| Hat accessories |60→61→62→63;65→66→67→68 | Four-rule depth, stiffness100, authored ancestry6→58→59/64 |

All20 non-rule bones are ancestors or intermediate roots. Nine back-hair intermediates25/28/31/34/38/42/46/50/54 remain authored; hat58 and its gathering parents59/64 remain authored. No non-rule bone lies below a selected rule, and no non-rule bone lies between two selected rules in this exact profile. The general traversal must still walk every actual bone so that future profiles cannot silently skip intermediates. Native25 has **no retained rule**; one sentence in the frozen earlier chain README incorrectly said otherwise. Its code and measured parent mapping correctly keep25 authored.

## Practical sequence after the pair probe

1. Preserve the pair run, including its first failures, closure and exact source hashes. Correct its prose in a successor note while retaining the frozen original. Reuse actual successful gates only; do not infer a pass from this plan.
2. In a fresh experimental adapter/harness, retain exact GLB/report/source pins and full69-parent admission. Replace the hard-coded four-owner selection with an explicit allowed selection from this exact49-owner catalogue. Reject missing, duplicate, changed or extra owners, different flags, altered coefficients, stale bindings, disabled bones, mixed Skeletons, nonuniform/mirrored scales, body owners and foreign final-pose modifiers. Preserve the already qualified exception for one empty inert native PhysicalBoneSimulator3D; never remove or disable it. Keep root-approved leases and original files read-only.
3. First exercise35→36→37 and60→61→62→63 in isolation and together. These seven rules cover both coefficient groups and the previously untested three/four-rule depths. Establish the same baseline/parent/tip/Off gates as the pair probe before widening the selection. Do not change solver tolerances to make a deeper chain pass.
4. Run the exact49-owner selection with the same authored baseline, six acceleration profiles, two root placements and120ticks per profile:1,440 actor ticks and70,560 rule evaluations if complete. These are proposed budgets, not observed counts. Derive assertion totals from the written harness and actual completed results; do not reuse pair/leaf totals.
5. After headless/FK/weighted qualification, port the proven multi-rule orchestration behind the exact production profile admission. Extend the actual GUI fan, Off/seek/Save, LocalRecord Stop/Cancel/Undo/Redo, linked/packed cold-open and final-frame tests. Keep the generic HAS spring route and independent actor physics behavior intact. Label this exact49-rule profile separately from generic Source support. Full same-actor ragdoll coupling requires another design and fixture.

The existing `chain_solver.gd` already accepts explicit bone and parameter dictionaries with parent ordering and staged actor-wide commit. The main bounded changes are in the experimental `model_adapter.gd` selection/admission and `chain_harness.gd` loop/capture assertions. `chain_capture.gd` already accepts a selected binding set. Avoid copying the solver mathematics or changing the0x31 coefficient interpretation while broadening coverage.

## Pose and numerical gates

Capture a complete authored absolute-parent-local baseline once per fixed tick, after clearing the previous temporary overlay. Walk all69 actual parents before children, beginning at Skeleton.global_transform. A selected child's goal is its authored local transform composed under its already-solved same-tick parent; prior live results never become authored input. Preserve every local translation and base scale. Reconstruct each Model rotation as base inverse × effective-parent inverse × desired-world, then overlay49 rotations into a complete69-channel authored-pose copy.

Check all69 baseline FK frames; all49 desired/actual world orientations and native+Z tips; every selected parent's same-tick child origin; all20 non-rule world frames; all69 stored authored poses, keys, raw reports and rest/binding data. The retained adapter transport gate stays2e-5, with tip error at most2e-5 times positive uniform world size; strict scalar64 math gates remain independent. Apply source conversion0.01905 only to native rule length and tip-mass acceleration, once. Actual world fan acceleration receives no additional source factor. Reject discontinuous time or changed root size before committing state, requiring reset/replay.

Each rule owns its own persistent state. Compare branch-only versus combined49 solves with identical authored ancestors and world accelerations. In this catalogue the26 branches have no simulated ancestor in another branch, so each branch's rule state/world output must agree. Test rule-order permutations, separate actor instances, exact reset/replay, translated/rotated/scaled placement, zero and strong finite acceleration, and late-child failure after earlier branches computed. A refusal at the final rule must leave every earlier state, tick and overlay unchanged. Add changed ancestor/parent/parameter/report/disabled-owner and mutated returned-result negative cases; preserve the measured continuous-file-guard limitation for edits that retain header, length and mtime.

## Weighted-region gates

The retained mesh reference has9,661 vertices and4 surfaces. The earlier four-rule selection measured542 selected-weight vertices,340 shared vertices and9,119 zero-selected-weight vertices. **All49 union and per-branch weight counts are not measured by this plan.** Obtain them in a future approved actual capture, keeping points, weights, rest matrices and palettes in memory. Publish only counts, maxima and hashes.

For the full49 selection, require the affected/shared/unaffected mask to remain constant and all zero-selected-weight points to remain exact. This is valid here because the selection is descendant-closed and the20 non-rule world transforms stay exact. Keep mesh/skin/array/transform hashes unchanged. An individual non-leaf rule needs a descendant-closed subtree mask: counting only weight to its own bone would falsely call its moving children's region unaffected.

Require each weighted branch to respond under at least one suitable force profile; report any zero-weight rule rather than pretending visible motion proves it. Independently compare actual weighted positions against the desired full skin-palette result in memory. Shared vertices may mix multiple moving branches, so combined versus branch-only point positions need not match; verify their complete weighted sum instead. Preserve shared-weight counts and branch overlap counts, and do not require every affected vertex to move under every force direction. Off at authored frames12/24 must restore all weighted points,69 bone worlds, keys and source report bytes exactly.

## Publication and qualification boundary

Use a fresh owned output tree, root-approved runtime lease, exact tool/source/input hash pins, before/after preservation gates, retained process receipts and authoritative closure. A parse failure, partial run, late refusal or fidelity failure stays failed. Do not publish native files, rest/geometry/skin arrays, weighted points, private render references or decoded media. This plan itself reads only the pinned parameter metadata and existing code/public profile. It does not read GLB/MDL/VVD geometry or weights.

All49 flags belong to the same bounded0x31 family; no rigid/base spring, additional yaw/pitch constraint flags, collisions, self-collision or PMX joint reconstruction is qualified by this profile. Source report status remains an immutable historical import fact. If the future exact profile is supported, represent that as a separate HAS runtime capability. Rendering, PMX reconstruction, canonical six-foot normalization and full49 GUI integration remain separate work until their own actual evidence exists.
