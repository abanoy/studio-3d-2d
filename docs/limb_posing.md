# Natural hand and foot posing

Select a supported hand or foot and use **Move** with an RGB handle. **Move limbs
naturally** is on by default in Simple. The elbow or knee bends to reach the target;
the hand/foot keeps its orientation. Rotate remains direct joint rotation. Switch
the assist off to move individual bones freely. Advanced offers **Reverse limb
bend**, which is an ordinary undoable pose edit.

A completed drag stores solved joint rotations as ordinary native-ID pose keys.
One release makes one Undo step; Escape restores the preceding pose. Camera keys
remain explicit. No new model/project format or persistent constraint is introduced.

Only validated three-joint arm/hand and leg/foot chains are supported. Declared VRM
humanoid node names take precedence; exact conservative MMD, ValveBiped, SFM and
common English conventions are fallbacks. Parent links and skeleton must agree.
Display labels do not determine chain identity. Unknown/incomplete rigs keep direct
posing. Zero-length segments and nonuniform/negative scale report an explanation
rather than an invalid key. Reach is clamped; the bend plane starts from the current
elbow/knee. The hand or foot keeps its preceding world orientation.

The implementation uses Godot4.6's [TwoBoneIK3D](https://docs.godotengine.org/en/4.6/classes/class_twoboneik3d.html)
on a disposable scratch skeleton, captures the solved pose, then frees it. No live
modifier overrides the saved pose. See [Skeleton3D](https://docs.godotengine.org/en/4.6/classes/class_skeleton3d.html)
and [SkeletonModifier3D](https://docs.godotengine.org/en/4.6/classes/class_skeletonmodifier3d.html).

Simple now also offers opt-in [Hold feet while posing](foot_hold.md) for root/body
Move edits. It stores solved FK endpoints; it does not impose playback contacts.

**Remaining:** persistent timeline foot planting during root movement, native constraints,
joint-limit tuning, full-body IK, motion paths and secondary motion. This authoring
assist is separate from the first live [physics increment](physics.md), which adds
a manual Simple toggle, grab/release and freeze. [Local/World Record](physics_recording.md)
now creates editable motion pieces; automatic import activation remains next.
The grid is still a visual guide, not a floor.

`tests/verify_limb_ik.py` checks actual gizmo edits, skin deformation, endpoint error,
orientation, undo/cancel, unsupported rigs/scales, parents, packed HAS and synchronized
drawing/WAV/movie. Optional private Miku, Reimu, Scout and owner VRM0/1 samples are
tested when available with source hashes preserved. Physical mouse feel and all rigs
are not certified by those checks.
