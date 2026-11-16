# Source jiggle: measured readiness and next runtime increment

Current behavior includes exact inactive metadata retention and a qualified
native→Blender→glTF→HAS identity bridge for the exact Junko hair/default profile.
All69 bones/49 rule owners survive ordinary import, Undo/Redo and packed/linked
cold reopening. Simple loose-part review prioritizes two verified existing hair
chains and offers explicit Enable these existing joints without replacing
weights. Source coefficients remain inactive in production. A bounded native8
live-pose/deformation proof now passes; wider chains and product integration
remain next.
See the [current scoped results](benchmarks/sfm_source_bone_binding_main_2026-11-13.json).

November 15 continuation at f0dd57a: actual Model/SceneIO FK transport and
standalone Godot scalar64 dynamics mathematics now pass their separate bounded
checks. Actual native8 leaf application then passed its separate one-rule probe.
All were parsed, executed, reaped and authoritatively closed after a fresh complete
default pass. None activates native Source physics in Studio.
See [current readiness evidence](benchmarks/native_source_readiness_2026-11-15.json).

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
The actual Model/SceneIO world/rest/FK probe now passes **41,588 checks over
220 configurations**, joining all 69 bones and 49 native-Z tips. It includes
signed XYZ rotations at native8/17/18/26/27, moved parent anchors and moved/rotated
roots at uniform root scales1/2. Maximum bone/rest matrix error is
1.0013580322265625e-5; native-Z tip distance is3.885747446474852e-6. Parse/run
exit0, retained child reaping, unchanged locked inputs and root closure pass.

That is actual skeleton transport at the single source conversion0.01905.
It does not measure posed weighted skin, GPU/render appearance or native
dynamics. A second actual conversion scale remains UNRUN; two root scales
must not be relabelled as two source conversions.

Record native local position/quaternion, Blender rest matrices, exported joint
transforms/inverse-bind matrices and imported HAS base poses. Establish the
actual transform between these domains and any per-bone rest-basis correction.
Neutral weighted-vertex agreement and the scoped skeleton/world checks above
have separate evidence. Preserve their parent/inverse-bind and positive-uniform
guards. Next measure actual weighted deformation and restoration through live
pose application; reject mirrored, nonuniform or degenerate transforms rather
than inferring broader import support from this one profile.

Junko's raw rule length is20. Derive endpoints using the actual conversion scale
and verified native axis. The native reference uses goal-matrix column2; the
current generic scratch runner's virtual tail uses localY or a next-joint
direction. The new actual skeleton probe confirms native joint-local+Z.
Use that native-specific endpoint without changing generic helper behavior.

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

The new standalone GDScript mathematical candidate passes **8,994 checks and
1,440 integration ticks** on Godot4.6-stable. Maximum scalar64 vector difference
from the public synthetic Python oracle is9.374856803373542e-13. Independent
rational force/Euler and damping controls, zero-cone cases, reset/instance/atomic
refusals and explicit Vector3/Basis binary32 boundaries are included. Parse and
run each exit0; both retained children are reaped, inputs stay unchanged and
root authoritative closure releases the lease without killing processes.

This is isolated scalar64 mathematics, not native-model application or an
executed SDK/client trajectory comparison. Its clock explicitly seeds tick0
and integrates at120Hz, without SDK first-call1ms/fallback history. Original
104/1000 zero-cone failures remain frozen separately; the exact-zero analytic
correction and independent root reproduction are retained. Synthetic converted
coordinate cases do not qualify a second actual native import conversion.

The actual native8 FrontHair1 leaf readiness probe now passes **7,289 checks,
1,440 ticks and12 cases**: two root contexts at requested scales1/2, each with
control, signed3 and positive12/50 temporary world accelerations and a repeated12
cycle. Its retained stiffness is100, damping5, length20 and mass20. Actual loaded
skin bindings confirm152 influenced vertices,144 shared and9,509 outside the
leaf. Maximum desired/actual basis error is5.068859995960295e-6, native-Z tip error
3.4960614812007407e-6 and adapter correction4.934248870047675e-6, within the
unchanged2e-5 boundary. Measured weighted displacement reaches0.03188145160675049.

The actual complete sampled live-pose overlay preserves authored leaf position
and all68 other world bones exactly. The9,509 weight-zero region stays exact;
direct live_pose=null/apply restores keyed frame24, nonrest frame12 and every
weighted point exactly. Cleared-state12-input repeats produce identical hashes,
and signed/input-strength cases differ from their gravity-only control. These
are actual CPU mesh/skin queries, not GPU skinning or rendered appearance.

Attempts1 and2 remain **FAILED**, each after2 checks/0 dynamics steps. Their
blanket modifier guard encountered one engine-default-shaped internal, direct,
script-free PhysicalBoneSimulator3D with active=true but simulation=false and no
physical bodies. Attempt3 source review permits at most that exact empty built-in
context, rejects all other modifiers/bodies, and rechecks it at each root's end.
No node is disabled/removed and no numeric, geometry, Off or count gate changes.
The private compatibility flag remains UNMEASURED. All three attempts retain
their parsed/reaped/root-closed evidence; no process was killed and inputs remain
unchanged. Compact execution evidence is at
[native leaf actual packet](../experiments/native_leaf_actual_20261115).

This is temporary one-leaf readiness, not regular Studio physics activation.
Native SDK/artist parity, procedural-parent chains, actual GUI/body/fan/Record,
saved HAS and GPU/render integration remain unqualified. Retained source flags
stay inactive and the full-layout verification flag remains false. Next qualify
parent17→18 and26→27 recomposition, then broader lifecycle/recording behavior.

Reuse the scratch skeleton/FK contract in [secondary_spring.gd](../src/secondary_spring.gd)
and transient authored/body overlays in [secondary_live.gd](../src/secondary_live.gd).
Do not silently map unsupported flags or native controller behavior.

## 4. Check fan response and exact Off restoration

The native8 probe above measures direct clear/apply restoration under synthetic
world accelerations. It does not exercise the ordinary Hair & clothes button,
actual fan field, live body coexistence or recorded playback. Keep those next
checks separate instead of treating one-leaf readiness as their pass.

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

The richer common HAS model contract, PMX physics/reconstruction assistant and
six-foot human baseline at user scale1 remain planned requirements. These narrow
Source readiness results do not implement those features or change existing
projects, formal acceptance scores or the optional height-review behavior.
