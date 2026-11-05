# Hold feet while posing

In Simple Pose, enable **Hold feet while posing**, select the model root or a body
joint above both thighs, choose **Move**, and drag a colored handle. Both feet keep
their starting world positions and orientations as the knees bend. Advanced local
numeric Move values use the same path. Rotate, model scale and individual limbs
remain direct edits. Turn the option off to reposition the whole character.

Physics and Hair & clothes must be off first; the control refuses live simulation
without stopping or recording it. Unsupported rigs need two uniquely identified,
connected thigh–knee–foot chains. VRM humanoid names or the existing conservative
MMD/Source/English bindings identify them. The body joint must be an actual common
ancestor; its display name is not used to guess topology. Unsupported scales and
unreachable moves keep the prior whole pose, with an explanation. During a drag,
the last reachable preview remains available; Escape restores the original pose.

This is an opt-in **direct posing assist**, initially off each launch, retained
through New/Open and Simple/Advanced in the same session. It produces ordinary
editable root/leg keys using the existing automatic-key preference and one Undo.
It adds no persistent constraint, model version, hidden floor or native asset edit.
The existing hand/foot IK toggle remains independent.

**This option alone is sparse FK.** Use [Planted feet ranges](contact_animation.md)
for the separate continuous-contact implementation. This option holds endpoints during authoring,
not throughout playback interpolation. A native fixture explicitly measures sliding
at the midpoint between two sparse solved FK poses; green endpoint tests do not
prove continuous contact. Timeline ranges, retiming, parent movement, corrections
and recording ownership use the separate Model7 implementation. Neither option
completes Motion Assist, walking,
motion paths, ground detection, full-body IK or anatomical constraints.

Both legs use the existing disposable
[Godot 4.6 TwoBoneIK3D](https://docs.godotengine.org/en/4.6/classes/class_twoboneik3d.html)
solver sequentially. Both final endpoints and orientations are checked together;
an unsuccessful solve rolls back instead of publishing a partially held pose.
`tests/verify_foot_hold.py` runs hidden Windows checks for crouches, root/pelvis,
numeric/gizmo moves, reach failure, zero moves, Escape, Undo, scales/parents,
live-physics protection, MMD/GMod/SFM/VRM0/1, packed HAS and actual MP4 pixels.
Physical mouse comfort and all-rig fidelity remain unverified.

The [continuous-contact track](foot_contacts.md) shares normal project evaluation;
this direct FK checkbox remains an independent authoring option.
