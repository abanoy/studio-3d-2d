# Live ragdolls and solid props

Interactive imports of compatible ragdolls start with **Physics on** after the import
dialogs close. The immediate on/off control is visible in Simple. Existing models
and solid props can also use that toggle explicitly. Left-click a simulated body to grab it, move the
cursor to lift/drag, use the wheel to change distance, and release to let it go
with its current velocity. Ctrl+left remains free camera. Release outside the
viewport, Escape and focus loss remove the grab constraint safely.

**Physics off freezes the current simulated pose**, retaining manual posing and
Undo. Live simulation and grabbing stay unrecorded until **Record** is pressed.
**Local record** captures the initially selected live model; **World record**
captures all currently live models and props. Stop keeps an editable take; Escape
discards it. See [recording](physics_recording.md). Explicit **Record pose key**
still stores one held pose. Native collision/constraint fidelity remains incomplete.
See [interactive import behavior](import_physics.md) for activation and lifecycle rules.

Use a real imported floor/map. **The empty-world grid is not a collision floor.**
Advanced > Sample room supplies an original practice floor and walls. With no map,
the model falls through empty space until stopped. Imported visible map triangle
surfaces supply approximate static collisions (100000 triangles; skipped surfaces
are reported). These do not reproduce Source collision flags or every native map
feature. Colliders are rebuilt for a new live session; animated moving maps are
not implemented. Enable Physics on each box/prop to make a live interacting pile.

Unrigged models and single-bone props use one rigid body, with one convex collision
hull per visible mesh. Hollow spaces inside an individual mesh are filled by that
hull; this is approximate, not a native Source collision model. Up to32 meshes and
100000 vertices are supported. Meshes above4096 vertices use fitted boxes, reported
in the status message. Flat planes, oversized bounds, hidden/absent objects and
nonuniform/negative root or parent scales are rejected before creating bodies.
Unknown multi-bone characters remain unsupported ragdolls; they are not silently
converted into rigid characters. Maps/groups are static, with Physics disabled.

Props share grab/wheel/release with ragdolls, collide with one another, and can be
knocked by a ragdoll. The visual root follows a separate world-space body, keeping
physics outside the imported hierarchy. OFF converts the actual root position and
rotation back through the parent transform and imported root. Static rotated/scaled
parents work. Simultaneous live simulation of a parent and its descendant is rejected
until those compound transitions are supported; separate objects can simulate together.
Mass currently defaults to1kg for props. Native mass, inertia, collision decomposition,
bodygroups and richer material tuning remain future work.

The standard native rig feeds one shared physics adapter: validated arm/leg chains,
their connecting ancestors and recognized head/torso bones, capped at48 bodies.
Small fingers/accessories inherit movement. Positive uniform skeleton/bone scales
are required; unknown or disconnected rigs get a useful explanation. Geometry is
never renamed or rewritten. Bounded skin-weight boxes fit structural parts where
practical; capsules/spheres are fallbacks. Unusual costumes, hair and native colliders
remain approximate. This is not a promise of no clipping on arbitrary assets.
Actual Scout previews still show clothing distortion in deep folds. More joint
freedom does not by itself reproduce native skin/helper-bone and collision behavior.

Body fitting now uses structural skin weights and recognized finger/toe/twist
helpers. Loose or unknown descendant branches are excluded from the rigid fit;
they retain their original rendered skin. This prevents long hair or sleeves
from inflating a head/arm collider. Unknown structural helpers may need better
classification; capsule/sphere fallbacks remain approximate. No new hair/cloth
simulation is implied by excluding those vertices from a rigid-body proxy.

At activation, intersecting proxy shapes within four skeletal links receive a
session-local collision exception. Box orientation, sphere radius and capsule
segments determine overlap; touching alone is insufficient. This prevents fitted
neighbors from pushing connected joints apart. Distant parts, initially separate
parts, maps and other models remain collidable. Closely connected excluded parts
can overlap during deep folds; native collision shapes remain preferable.
Nominal box extents make near-corner tests conservative relative to rounded margins.
The bounded48body rig has at most1128pairs to inspect once at activation.
Jolt now uses four position iterations (previously two), retaining120Hz,10velocity
iterations and the2mm penetration allowance; additional accuracy costs CPU time.

The pinned engine uses built-in Jolt at120Hz, neighbor collision exceptions,
2mm penetration allowance and continuous collision detection. Joint frames follow
the actual limb directions, independent of imported bone axes. Shoulders use
110degree swing/70degree twist, hips100/45, wrists45/35, ankles35/20 and connecting
bones40/30. Elbows and knees use hinges:150degrees of bend and a
5degree extension allowance. A pose already bent farther is retained at activation.
Limits account for the pose at activation. Angular
damping is0.6 instead of the previous1.5 so limbs lose less momentum in midair.
Bone properties take degrees, unlike the physics server's radian API.
These are inferred shared profiles, not imported Source PHY/PMX/VRM constraints.
For a straight chain the hinge plane is estimated from the body's left/right and
torso landmarks; an incomplete rig falls back to its model direction. An already
bent chain supplies its own plane. Unusual anatomy,
custom front axes and strongly preposed rigs may still need native tuning.
Grabbing adds a temporary
pin to a kinematic anchor whose target speed is bounded, rather than directly
teleporting the dynamic body. Unsupported Jolt soft-limit properties are not tuned.

Scrubbing/playback, Save and export stop live simulation. A frozen unanimated rig
is an ordinary static pose, saved in HAS and rendered without rerunning physics.
For a model that already has animation, the frozen pose/root is an **unrecorded draft**
at the current frame. It remains visible across workspace/Draw switches, but
scrubbing resumes the original authored take. Save preserves the ordinary draft
data; reopening in Scene resumes the recorded track. Use an explicit pose key for
a lasting single-frame edit. Motion capture samples and bakes only after the
explicit Local/World Record action. Recovery defers while simulation is active.

Tests cover connected UI, actual falls/contact/skin geometry, grab/lift/outside
release, high-speed wall contact, two live ragdolls, per-object freezing, unchanged
keys/camera/source, animated-root/draft behavior, Undo, packed HAS and48-frame MP4.
Private Miku, Reimu, Scout and VRM0/1 samples are optional; authored fixtures always
run. Native appearance, all-rig collision quality and physical mouse comfort need
further testing. No source physics code or game scripts are executed/copied.
Prop tests additionally check a real ragdoll striking three settled boxes, horizontal
box displacement and physical contacts, viewport grabbing, parent conversion, safe
invalid-root rejection, source/Undo isolation, independent drawing/WAV, packed HAS and
MP4. Optional prepared CSS chair/OBJ samples test the shared prop path; this is not
a fresh native reconversion or all-prop acceptance test.

Primary references: [ragdolls](https://docs.godotengine.org/en/4.6/tutorials/physics/ragdoll_system.html),
[Jolt](https://docs.godotengine.org/en/4.6/tutorials/physics/using_jolt_physics.html),
[PhysicalBoneSimulator3D](https://docs.godotengine.org/en/4.6/classes/class_physicalbonesimulator3d.html),
[PhysicalBone3D](https://docs.godotengine.org/en/4.6/classes/class_physicalbone3d.html),
[PinJoint3D](https://docs.godotengine.org/en/4.6/classes/class_pinjoint3d.html),
[RigidBody3D](https://docs.godotengine.org/en/4.6/classes/class_rigidbody3d.html),
[ConvexPolygonShape3D](https://docs.godotengine.org/en/4.6/classes/class_convexpolygonshape3d.html).

Joint-frame implementation was checked against pinned
[PhysicalBone3D source](https://github.com/godotengine/godot/blob/4.6-stable/scene/3d/physics/physical_bone_3d.cpp)
and [Jolt constraint construction](https://github.com/godotengine/godot/blob/4.6-stable/modules/jolt_physics/joints/jolt_cone_twist_joint_3d.cpp).
Cone twist uses joint X; hinge bending uses Z with the engine's limit sign.

Run `python tests/verify_ragdoll_joints.py` for bounded-velocity before/after
joint comparisons and actual native frame-direction/degenerate-limb checks.
`python tests/verify_physics.py` exercises normal falls, contacts, grabbing,
freezing and static save/export. The full `tests/verify.py` additionally covers
dynamic props and explicit recorded replay. Private sample portions skip clearly
when unavailable; original authored fixtures remain mandatory.
`python tests/verify_physics_contacts.py` adds actual overlapping-torso stress,
Jolt-backed primitive-overlap comparisons, loose-part skin-weight fitting and
native joint-separation controls. The full verifier includes that suite too.


Current secondary controls: Simple Hair & clothes uses supported authored VRM
chains independently of body Physics; both solvers may run on the same model.
Add fan supplies a selectable, movable, aimable ordinary model with contextual
on/off and blowing-speed controls. Existing Local/World Record keeps secondary
motion as ordinary editable FK. Turning either combined toggle OFF freezes the
whole current pose and stops both. Reviewed weighted HAS helpers can supply missing
chains; native MMD secondary rules and full physical cloth fidelity remain incomplete.
See secondary_motion.md for
controls, smoothing, fixed-step sampling, portability and explicit limitations.

## Limb mass trial (development, 2026-11-03)

An experimental distribution assigned relative weights of 1.0 / 0.70 / 0.35 to the upper arm, forearm and hand and 2.2 / 1.35 / 0.65 to the thigh, shin and foot. The total mass of each rig stayed the same. Joint limits, collision shapes and damping stayed at their existing settings.

The test dropped each model for 360 physics frames and measured the largest separation between physically connected joints at the end, in millimeters. Each column is one run of the same test.

| Model | Experimental | Restored |
| --- | ---: | ---: |
| Miku | 33.81 | 0.35 |
| GMod Reimu | 23.97 | 0.73 |
| SFM Scout | 1.67 | 1.45 |
| VRM1 | 43.91 | 0.49 |
| VRM0 | 1.12 | 0.13 |

The experimental profile failed three of 58 checks. The restored profile passed all 58. We retained the existing distribution. These end-of-drop measurements do not assess transient joint separation or subjective looseness. The next investigation should identify when and where a limb becomes constrained before trying another mass distribution.

## Limb travel during a six-second drop

Every six physics ticks, the diagnostic measures each physical limb joint relative to its physical parent and compares that orientation to its initial orientation. The table gives the smaller and larger of the two peak angles (left and right), rounded to whole degrees. It includes twist and swing, and may miss peaks between samples. Each condition uses one drop at the same starting height with the existing masses, joint limits and floor.

| Rig and condition | Shoulders | Elbows | Hips | Knees |
| --- | ---: | ---: | ---: | ---: |
| Scout ordinary | 127 / 139 | 38 / 39 | 46 / 63 | 124 / 126 |
| Scout floor contact only | 110 / 133 | 84 / 101 | 105 / 106 | 136 / 138 |
| VRM1 ordinary | 82 / 115 | 38 / 69 | 35 / 58 | 135 / 139 |
| VRM1 floor contact only | 122 / 136 | 14 / 21 | 103 / 109 | 149 / 153 |
| VRM0 ordinary | 58 / 68 | 38 / 40 | 38 / 40 | 146 / 146 |
| VRM0 floor contact only | 125 / 133 | 98 / 102 | 118 / 123 | 152 / 154 |

The floor-only condition is a diagnostic and is never selected in Studio. Compare corresponding native joint IDs in the JSON for per-side peaks, peak ticks and final angles. Whole-body falls can change trajectories when contacts change. A difference between these columns does not by itself identify the collider or prove that a joint limit should be loosened.

VRM1 sensitivity check: two ordinary runs with unchanged mass and contact settings gave peak left/right elbow travel of 18 / 81, then 69 / 38 degrees in the same joint order. Scout was within one degree across these two runs. Inspect Scout arm contacts before considering broader rig changes.

## Scout forearm contact trace

Each forearm reported up to 32 physics contacts, sampled every tick of a 360-tick drop. Counts are ticks with at least one reported contact against that peer, not impact force or uninterrupted contact duration. Static scene colliders are recorded separately from named model bodies.

| Condition | Left elbow peak | Right elbow peak | Left arm/spine contact ticks | Maximum final joint separation |
| --- | ---: | ---: | ---: | ---: |
| Ordinary | 38.2 degrees | 38.6 degrees | 21 | 2.60 mm |
| All model self-contacts disabled | 84.1 degrees | 101.4 degrees | 0 | 6.56 mm |
| Only left forearm / upper spine excluded | 38.8 degrees | 41.6 degrees | 0 | 0.31 mm |

These are single trials. Changing contacts can change how the whole character lands. Comparable peak travel does not prove comparable animation quality. The pair exclusion and the all-model exclusion are diagnostic only; runtime collision behavior is unchanged.

## Scout full arm-chain contacts

One ordinary 360-tick native drop, with both upper arms, forearms and hands reporting. Rows count ticks, not contact force. First/last can span multiple separated intervals. The JSON includes those intervals and static-scene contacts.

| Body | Other model body | Contact ticks | First | Last |
| --- | --- | ---: | ---: | ---: |
| bip_hand_L | bip_foot_L | 7 | 107 | 113 |
| bip_hand_L | bip_hip_L | 3 | 100 | 104 |
| bip_hand_L | bip_knee_L | 5 | 105 | 109 |
| bip_hand_L | bip_pelvis | 83 | 278 | 360 |
| bip_hand_R | bip_foot_R | 21 | 108 | 128 |
| bip_hand_R | bip_hip_R | 4 | 100 | 105 |
| bip_hand_R | bip_knee_R | 13 | 106 | 118 |
| bip_lowerArm_L | bip_pelvis | 98 | 263 | 360 |
| bip_lowerArm_L | bip_spine_2 | 119 | 144 | 360 |
| bip_upperArm_L | bip_collar_R | 1 | 163 | 163 |
| bip_upperArm_L | bip_pelvis | 13 | 101 | 113 |
| bip_upperArm_L | bip_spine_0 | 23 | 103 | 125 |
| bip_upperArm_L | bip_spine_1 | 122 | 2 | 124 |
| bip_upperArm_L | bip_spine_3 | 13 | 165 | 177 |
| bip_upperArm_R | bip_head | 159 | 193 | 360 |
| bip_upperArm_R | bip_pelvis | 10 | 102 | 111 |
| bip_upperArm_R | bip_spine_0 | 10 | 101 | 110 |

The same physical encounter can appear in both reporting bodies. A frequently reported peer is a candidate for an isolated test, not a reason on its own to disable collisions.

A first six-reporter trace ended with 9.29 mm joint separation, exceeding the existing 5 mm target. Enabling contact reporting on additional bodies can change the observed trajectory. That failing run is retained in scout-six-reporters-first.json. The established release-profile stability check continues with its original reporting setup.

Matched six-body diagnostic trace_arm_chain: left/right elbow peaks [59.1, 38.1] degrees, maximum end separation 0.76 mm.

Matched six-body diagnostic without_left_upper_arm_spine: left/right elbow peaks [40.5, 38.2] degrees, maximum end separation 0.53 mm.

## Grab attachment at the clicked surface

The physical grab uses a pin at the selected world point. Both its anchor and the
pin now have their world-relative position before entering the physics world.
The same point initializes screen position and ray depth for every grab entry.
Previously the anchor entered at the scene origin and was repositioned afterward.

A controlled Scout test fixes the upper arm, leaves the limb's ordinary collision
settings in place, disables gravity on this disposable rig, settles for90 ticks and
pins the forearm three quarters of the way toward the wrist. The ordinary pointer
motion handler then drives a stationary hold or a 45-degree arc over45 ticks and
holds through tick90. With the previous attachment order, the stationary case
briefly reached141 degrees and returned to neutral. With the new order it measured
0 degrees throughout. Opposite pulls finished at about41.3 and45.0 degrees, within
2.2mm of the requested world points. These results address initial grab snap in
this fixture; they do not establish the quality of unrestricted whole-body falls.

Run tests/verify_scout_grab.py with the existing prepared SFM Scout fixture. The
test also checks that grab/release leaves authored motion intact.
