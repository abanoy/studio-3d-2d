# Reusable body poses

Select a rigged model in Pose mode and choose **Body poses**. Name the pose and
choose **Save current body pose**. Select a thumbnail, seek to another frame and
choose **Use at this frame**. With normal Auto-key enabled this creates ordinary
editable bone keys; an identical pose is a no-op. With Auto-key off it adjusts
the draft, and Record pose key keeps it on the timeline. Camera keys stay explicit.

Saved poses contain authored local bone deltas only. Model position, rotation,
scale, face controls, visibility, planted-foot targets, physics and Motion Assist
settings stay independent. Generated helper offsets are not baked into these
black-key poses. Existing contact validation can refuse an unreachable application;
the previous pose/keys are restored. Live Physics/Hair & clothes and other file
operations must finish before capture or application. Foot constraints and motion
helpers still evaluate normally after applying the authored pose.

Thumbnails render an isolated, short-lived copy of the character at96×54 on the
GPU, framing its posed geometry on a neutral background. The live camera, body
and scene do not move. This removes an environment that might hide the character.
The copy uses the authored FK pose; current face/bodygroup/material appearance
may be visible in its thumbnail but is not stored as part of the body pose.
Rendering still has native material/skin/framing limitations; a thumbnail is not
a native-source fidelity certificate. Changing frame/scene/view during capture
discards it. Temporary viewport/clone nodes are freed after capture.

Rename, Duplicate and Remove operate on the library; each change has one Undo.
Removing a saved pose never removes animation keys that already used it. Each
model instance carries its own library inside `.has`; packed, linked and recovery
use the same model metadata. A source checksum and ordered bone bindings prevent
applying poses to another rig by guessed bone names. Another instance of the
identical imported GLB can use exported poses. This increment does not retarget
between different characters, formats, rig revisions or differently generated
GLBs, even if their body-part labels look similar.

Advanced also exposes **Import HAS poses** and **Export HAS poses**, using a
small data-only `.hasposes.json` file. Import merges compatible entries in one
Undo; identical entries are skipped, names are made unique and budget/identity
failures refuse the complete transaction. Export includes bone deltas and
thumbnails, not model geometry/textures. It never exports a vendor's model format
or runs content from the file. Existing HAS schemas remain unchanged because the
library is optional metadata; earlier readers can preserve it opaquely, without
offering these controls. It never changes normal playback unless a pose is used.

Current bounds are16entries and192KiB per library, at most512declared bones and
24KiB per inline PNG. The global1MiB project metadata budget still applies; complex
rigs may reach it earlier. The budget estimate now includes Krita drawing ancestry.
No mesh, native source or source parameter report is modified. Bone IDs are the
same internal standard bindings used for ordinary pose animation across adapters.

Verification entry points: `tests/test_pose_library.py`, `pose_library_unit.gd`,
`verify_pose_library.py` and `verify_pose_library_native.py`. The latter uses the
existing local Miku PMD, Reimu GMod, Scout SFM and VRM1 preparations without
reconverting/copying their native assets. Actual accepted runs, initial fixture
mistakes, receipts and scope are recorded in the dated progress memo. A generic
component-model scene covers keys, draft/no-op, Undo, file exchange, cold HAS and
pixel-exact MP4. These are scoped tests, not complete Stage3–5/artist acceptance.
