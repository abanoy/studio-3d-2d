# Import an MMD pose

In the desktop Studio, select an MMD character and open **Import MMD pose…**
in its Model / pose properties. Choose a `.vpd` file. Studio prepares the pose
without changing the character, then asks whether to apply its matched bones
and shapes at the current frame. Apply creates one editable transaction with
independent body and expression keys. Undo restores the previous character state.

Moving to a different frame or editing the scene during preparation/review
invalidates the pending import. Choose the pose again at the intended frame.
Cancelling preparation or review leaves the imported pose unapplied. Missing
files and preparation failures allow retry. Existing camera keys, independent
drawing cels and other objects retain their own tracks.

The adapter matches exact original bone names, including Japanese names, before
converting rest-basis coordinates into standard HAS body channels. Generalized
English labels are presentation only. It requires the MMD preparation metadata
retained with the standard model and the desktop installation of Blender/Python.
It reads source files; it does not change the native pose, model or game files.
Imported poses use ordinary `.has` save, recovery, playback and MP4 rendering.

VPD raw vertex shapes and supported embedded PMX groups use the existing standard
expression tracks. Groups may combine, nest or use signed target amounts. Native
names match exactly; duplicate/ambiguous names and unsupported group effects are
skipped with reasons in review. An unsupported group is skipped as a whole.
Overlapping requested raw/group bindings add together. Unmentioned shapes retain
their current tracks. A shapes-only VPD creates no body key. Zero amounts are
explicit keys, allowing a later imported pose to release an expression.

Freshly prepared models retain [supported joint chains](standard_ik.md), which
are baked into ordinary joint keys during pose import. Older models need a
fresh preparation to gain these declarations. Native inherited transforms,
live native IK authoring, retargeting and unsupported material/UV/bone morph
effects remain unfinished. VMD has a separate
[Import MMD motion action](mmd_motion_import.md). Foot and hand targets may need manual adjustment. Browser preparation
is unavailable. Native MMD shading and arbitrary third-party pose fidelity are
not implied by successful conversion.

Verification uses a generated Japanese bone/blink pose and the retained real
Miku PMD preparation. Its conversion basis was independently compared with
installed MMD Tools over 126 joints (translation error below 1e-5 scene units;
zero angular difference at mathutils precision). The real desktop app exercises
the picker, cancellation, missing-file retry, stale-review rejection, one Undo/
Redo step, preserved unrelated mouth control, real blink pixel changes, a
shapes-only reset without new body keys, packed HAS reopen and exact
preview/export-frame equality. The movie
is H264, 1920x1080, 24fps, 48 frames, two seconds. This is local evidence for that
fixture, not a claim of complete PMX rig or native IK coverage.

Run `python tests/verify_mmd_pose.py` for the native fixture check. It writes an
original bone/blink and shapes-only VPD fixtures and launches `tests/mmd_pose_import_smoke.gd`
through `run.command()` on the private test desktop. It requires the ignored
retained `output/native-import-verification.json`; no vendor model is packaged
with the source.

`tests/mmd_pose_shapes_unit.gd` checks native-name ambiguity, unsupported-group
refusal, multi-part/additive bindings and amount validation. The separate private
`tests/mmd_pose_groups_smoke.gd` uses the retained original PMX group-test
preparation from `output/mmd-groups-verification.json`: compound, nested and
signed groups change real pixels, preserve body/camera/native data and Undo, and
skip the mixed UV group. That PMX is an authored fixture, not evidence for every
owner-supplied native group.
