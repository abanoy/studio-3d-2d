# Frame3000 to frame0

The addendum explicitly requires moving a character's animation block from
frame3000 to frame0 through the timeline. This scenario is now freshly verified
with ordinary independent body animation (Model6) and root components (Model9).
It uses the existing clip operation; this check adds no new ownership semantics.

An original procedural rig is introduced at frame3000 in a3600frame60fps parent.
Root and bone poses are authored through frame3024, alongside a separate model,
background, drawing hold and sound. A real fitted-timeline drag previews exactly
−3000frames, then commits the complete source interval at0 in one Undo command.
Source keys and component curves remain unchanged. All97quarter-frame root/bone
samples match the original relative motion, and moved frame12 has exactly the
same world pixels as original frame3012. Independent audio PCM, drawing pixels,
camera keys and other world rows stay unchanged.

The fixture explicitly sets the existing visibility-fade option to zero to
isolate motion from elapsed fades. The normal300ms default is unchanged. The
source file identities, current frame-addressed sound placement and non-overlap
rules retain their established meanings.

`python tests/verify_late_clip_move.py --isolated-display :101` uses an explicitly
provisioned private Linux display; Windows uses the existing private launcher.
Each model path includes packed schema8 cold Open and unchanged normal startup
after an actual SIGKILL, with original GLBs/WAV and writer cache unavailable.
Both preserve complete source/world data, exact independent sound/ink, moved
pixels and the editable60second timing domain. This check does not export a full
3600frame movie or establish native/physical/artist acceptance. Existing longer-
project export checks cover their own separate movie scope.
