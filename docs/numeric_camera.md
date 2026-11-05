# Numeric camera view

Scene / camera → Advanced → Numeric camera view opens position X/Y/Z and
pitch X/yaw Y/roll Z in degrees. Edit a draft, then Apply camera view. This changes
the temporary editor camera only. Save camera key remains a separate explicit
action, with the usual replacement confirmation and one Undo. An unapplied draft
blocks Save camera key and explains how to apply or reload it first.

Simple hides the detailed controls while retaining an applied view. It does not
silently apply a hidden draft. Reload current view discards draft numbers and
reads the latest temporary view. New/Open clears transient draft state. Changing
frame, mode or navigating after editing makes a draft stale; Apply refuses it
until Reload. Playback, export, navigation and open modal/file operations block
Apply. Live model physics does not author camera changes.

Coordinates use the existing right-handed Godot world (+Y up, camera looks −Z).
The camera's parent world is identity. Rotation uses explicit YXZ Euler order
for intuitive entry; existing camera keys still store quaternions. Euler angles
can have equivalent representations and become ambiguous near gimbal poles.
This is numeric authoring, not a new interpolation or physical-camera model.

The display steps by0.001. Unedited position components and the entire basis
remain bit-exact even if displayed rounded. A rotation change rebuilds a regular
basis, keeping the full original unedited Euler components and exact origin.
Applying unchanged fields preserves the original transform. Only genuinely
edited text is flushed; deferred SpinBox display text cannot revert a separate
numeric change. Position bounds are±1e12 scene units; input angles±36000degrees.
These are input guards, not a promise of useful single-precision rendering at
extreme coordinates. FOV/near/far retain their existing controls and key fields.

No project/schema/model changes, draft serialization, source asset edits,
automatic camera keys or world/drawing/history changes occur on Apply. Draw and
export use the authored camera track. Use the existing key Undo to revert a saved
shot; Apply itself behaves like temporary mouse navigation rather than an authored
Undo step.

`python tests/verify_camera_transform.py` covers exact untouched components,
numeric guards, independent Y·X·Z matrix references (including near-pole/multiple
turn cases), actual typed fields/button clicks, no-op/explicit keys/Undo/Redo,
stale view/frame/playback/export/Draw guards, New and exact packed HAS/pixels.
It exports an actual1080p48-frame24fps H264 movie and compares frame13 with the
shared frame12 preview. The dated memo records actual run results. Physical
keyboard/artist comfort and clean-PC acceptance remain separate.

Primary references: Godot4.6 [Node3D rotation conventions](https://docs.godotengine.org/en/4.6/classes/class_node3d.html#class-node3d-property-rotation)
and [Basis Euler conversion](https://docs.godotengine.org/en/4.6/classes/class_basis.html#class-basis-method-from-euler).
