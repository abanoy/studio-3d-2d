# Source jiggle: next runtime increment

Current behavior includes exact inactive metadata retention and a qualified
native→Blender→glTF→HAS identity bridge for the exact Junko hair/default profile.
All69 bones/49 rule owners survive ordinary import, Undo/Redo and packed/linked
cold reopening. Simple loose-part review prioritizes two verified existing hair
chains and offers explicit Enable these existing joints without replacing
weights. Source coefficients remain inactive; native dynamics is still next.
See the [current scoped results](benchmarks/sfm_source_bone_binding_main_2026-11-13.json).

## 1. Prove the export and runtime binding

Completed for the restricted SHA/default0.01905/standalone profile: a ledger for
all69 native bones and49 rule owners joins native
MDL SHA/index/parent to the actual Blender bone, exported glTF joint-node index
and skin membership, GLB SHA, HAS bone ID and skeleton index. Keep those numeric
domains separate. Reject missing, duplicate, reordered or wrong-parent joins.

Pinned SourceIO enumerates native bones, parents by native index and truncates
labels to 63 characters. Junko labels fit that bound, but names alone must not
become the binding algorithm. Inspect the pinned Blender exporter's actual joint
mapping or an audited export hook; preserve the native identity through export.
Do not assume native order equals exported joint order.

Existing [scene import](../src/scene3d.gd) records glTF node to HAS bone ID in
`has_source_bones`; [model bindings](../src/model.gd) record the actual skeleton,
bone index, generated name, path and base pose. The normal report and
[read-only resolver](../src/source_bone_bindings.gd) now verify that link. Broader
profiles remain unqualified. For the next dynamics increment, start with
native8 FrontHair1; then17→18 Side1Steps-1_L→
Side2Steps-1_L; then26→27 2Steps-1_L→3Steps-1_L. Preserve the actual hierarchy:
these declarations include26 rule roots, rather than one continuous chain.

## 2. Prove rest coordinates, units and neutral deformation

The restricted independent native→glTF rest/neutral subset is now measured:
69rest/parent joins,49native-Ztips,69inverse binds and9661VVDvertices across
two meshes/four primitives. At conversion scale0.01905, the common axis map
is(+X,+Z,-Y) and G=C*N; conjugation is refuted. Native forward stays joint-localZ.
Position/weight/UV-compatible multiset coverage preserves neutral skinning;
duplicate attributes prevent unique native vertex identity claims. The first
2e-5normal-fidelity gate failed and remains unqualified (maximum0.0012165467).
No native-normal/artist fidelity or changed generic-helper behavior is claimed.
See [measurements](benchmarks/native_source_coordinates_2026-11-13.json).
The actual HAS posed/world/two-scale checks below remain next; two root scales
and two conversion scales are separate qualifications.

Record native local position/quaternion, Blender rest matrices, exported joint
transforms/inverse-bind matrices and imported HAS base poses. Establish the
actual transform between these domains and any per-bone rest-basis correction.
Require neutral weighted-vertex agreement, parent/inverse-bind closure and
finite positive uniform scale. Check small positive/negative rotations around
all three axes under moved/rotated roots and moved parent anchors at two scales.
Reject mirrored, nonuniform or degenerate transforms for the initial subset.

Junko's raw rule length is20. Derive endpoints using the actual conversion scale
and verified native axis. The native reference uses goal-matrix column2; the
current scratch runner's virtual tail uses localY or a next-joint direction.
Measure that correspondence before constructing a terminal endpoint.

## 3. Implement a bounded dynamics subset with an independent reference

Junko flags are0x31: flexible, angle constraint and length constraint. Angle
limit is approximately0.7853981853, tip mass20, yaw/pitch damping5 and along
stiffness100. Yaw/pitch stiffness is50 on32 rules and100 on17 rules.

The current HAS stiffness/drag/gravity tuple does not directly express these
semantics. Pin and inspect an immutable official solver reference, document
units, and compare a bounded0x31 implementation against independent numerical
traces. Begin with one rule, then the two parent/child cases, then all49. Resolve
procedural-parent ordering explicitly. Keep mutable state per actor instance
and preserve retained raw metadata unchanged.

Reference inspection is now pinned to Valve SDK commit
019e91ccd650a34745934c65cdbbe89ffcc44ede; exact public blob hashes are saved.
Full SDK source stays local and unexecuted. It uses native localZ forward,
tip mass as downward acceleration and bypasses along-axis spring terms while
length constraint is active. Its frame-rate fallback is not yet a HAS clock
policy. This is a reference candidate, not proof of the artist's closed SFM/GMod
client behavior. No production solver or full-layout flag is enabled.

Reuse the scratch skeleton/FK contract in [secondary_spring.gd](../src/secondary_spring.gd)
and transient authored/body overlays in [secondary_live.gd](../src/secondary_live.gd).
Do not silently map unsupported flags or native controller behavior.

## 4. Check fan response and exact Off restoration

Compare matched trajectories with identical authored baseline, gravity, clock
and initialization. Native gravity can cause settling without a fan; measure
the difference attributable to airflow. Check fan off/speed0, a genuine field
miss, aimed hit, opposite flow and strengths3/12/50. Record world-space sample
positions and field vectors. A miss must match its no-wind control; an aimed
hit must deform measurably, and strong input must remain finite and constrained.
Preserve actual displaced model placement and aim the ordinary fan at it.

Extend [the restoration regression](../tests/fan_motion_smoke.gd) using a non-rest
manual baseline at frame12 and recorded keys at24. First prove meaningful bone
and weighted-geometry deformation. Hair & clothes Off must clear `live_pose`
and restore the current-frame authored/body baseline exactly. Repeated cycles
must not accumulate offsets, force history or changed rest poses. Preserve
keys, history, raw metadata, peer solver identity, shapes, camera, drawing and
audio; disabling hair must preserve the same running body solver. Cancelled or
stale setup must never resurrect simulation.

## 5. Record, persist and export

Exercise ordinary Local/World Record, cancellation, partial takes, Undo/Redo,
packed and linked cold reopening, reverse seeking and exported-frame agreement.
Check the actual1MiB project budget with the49-joint take and retained report;
preserve existing project/report limits. Reopening preserves bindings and
recorded FK while live simulation remains off until explicitly enabled.

Use only owned copied inputs and approved local tools; keep automated graphics
private. Save compact source/metadata/log evidence, preserve failures and retain
native art/media locally. Run affected tests and the complete default Windows
suite, then commit, push and verify remote contents. Artist/native-motion
fidelity and the owner's deferred manual checks remain separate observations.
