# Interactive practice

Home → Tutorials opens a beginner path and focused chapters using an included,
original room and seventeen-bone practice figure:

- **Basic · Your first movie** starts from empty `first-movie.has`. Eleven observed
  tasks cover normal map/model import, default live ragdoll and freeze, selection/
  Reset pose, camera navigation and explicit keys, auto-keyed arm posing, Ink,
  playback, split/dragging a motion piece and MP4. The import buttons open the
  ordinary picker beside included assets and call the shared importer. Save is an
  optional normal project operation before rendering; an unsaved practice can also
  finish by choosing an export folder. No forced permanent personal project.

- **Basic · Pose and draw**: select the figure, raise and auto-key its left arm at
  frame 24, then add visible paint on Ink at frame 24.
- **Advanced · Camera shots**: reveal Advanced, move and explicitly record the
  camera at frame 24, then record a changed field of view.

The guide observes actual scene states approximately and advances after a completed
action. Wrong-frame, unkeyed-camera, neutral-arm, empty-cel and hidden-Ink states do
not qualify. A quiet Hint offer appears after fifteen seconds without a meaningful
change; requesting it changes instructions without manipulating the scene.
Requested hints now outline a real control or the projected upper-arm joint,
without capturing input or adding anything to final output. The guide chooses
a corner away from that part. The −/+ control collapses/expands instructions for
more viewport room, including at 1200px. These visual aids are transient UI.

**Previous restores the whole saved exercise state**, including world/poses,
camera keys and temporary editor view, frame, cels, audio and project settings,
selection, active layer, mode, Advanced, canvas zoom/pan. Undo history and live
simulation velocities are not restored; checkpointing freezes simulations first.
The beginner course also stores three narrowly validated observations (actual live
physics, preview playback, successful export) atomically with each lesson snapshot.
Previous restores those observations too: returning to the final task requires a
new successful export, not merely an old movie on disk. Camera navigation compares
to the immutable step baseline, so Continue does not reset an already moved view.
The room and figure use the same standard world, skin, posing and HAS storage as
imported assets. The included file opens as an unsaved copy, never as its own Save
destination or a personal recent project. Save normally to keep your own practice.

Continue reopens the latest saved practice; Start fresh creates a separate session.
Saved practices lists earlier sessions when more than one exists. Progress is
personal data under `tutorial-progress` beside the recent-project preferences,
separate from ordinary scene recovery. A step boundary, Leave, successful New/Open
replacement or normal app close saves a checkpoint/resume state. Forced termination
may lose teacher context since that boundary even if ordinary recovery protects
newer scene edits. No periodic lesson autosave or recovered-lesson reattachment yet.
Session folders retain shared content-addressed cels within each fixed checkpoint;
there is no cross-session deduplication, retention policy or concurrent writer lock.

This is a runnable beginner route and initial focused chapters, **not complete
tutorial coverage**. Still needed: focused advanced lighting/interpolation/
constraints/rigging/physics/render sections, more topic/subsection entry points,
progressive demonstrations and beginner usability feedback. Physics here teaches
live/unrecorded motion and freeze; full capture is an advanced lesson still to add.
Tutorial Skip remains OPEN. The new course has identity `first-movie-v1` and eleven
tasks; both older three-task course identities/contracts stay unchanged. Future
task changes require explicit migration/versioning rather than shifting old steps.

Original sample geometry comes from `src/tutorial_assets.gd`; offline developer
authoring uses `python tools/build_tutorial.py --install`. It verifies existing
sample hashes and backs up prior files rather than overwriting edited examples.
Semantically unchanged HAS ZIPs retain installed bytes instead of being replaced
just because ZIP timestamps changed. The original room/figure/older practice HAS
remain byte-identical in this increment.
The app/sample distribution license is still the owner's decision. No third-party
model or art is included, and this is not an external-format exporter for users.

`python tests/verify_tutorials.py` tests the real Windows GPU app privately, ordinary
HAS worker/personal saving, full Previous, a separate-process Continue, input-state
grading, failure preservation and 1080p24 MP4/preview agreement. See the current
progress memo for actual source versus installed-copy verification results.
`python tests/verify_first_movie.py` exercises the beginner path through actual
pickers/physics/pose/drawing/play/clip drags/personal Save/export, smaller-window
guide behavior, failed encoder preflight and fresh-process Continue/Previous/
unsaved export. It also checks all included asset/manifest hashes unchanged.

When Home has no recent projects, Make your first movie opens the guided practice
directly. After leaving an unfinished practice, the same space offers Continue your
first movie. A finished practice can be reopened. Tutorials also provides Start
fresh and access to saved sessions. Starting or continuing from Home uses the
existing confirmation when replacing unsaved scene edits.

An unfinished first-movie lesson also appears beside recent personal projects.
Continue restores its practice session. If the first-movie lesson is already
open, Return to your first movie closes Home and keeps the live scene, including
its current personal Save path and pending edits.

During Play and pause, Add practice sound places an included short tone at frame
24 alongside the hand raise and Ink drawing. It is optional. The action creates
one ordinary timeline audio clip and one Undo entry. Selecting it again reports
the existing cue's frame. The sound follows normal project saving and MP4 export.

After successful export, Show movie folder appears in the footer. It opens the
folder containing the last completed MP4 when you click it. Its tooltip gives
the movie path. A failed or cancelled export does not replace that destination.

If an export stops after writing frames, Show saved frames opens that attempt's
PNG folder. Show movie folder still points to the most recent completed MP4.

If all frames and the synchronized sound mix were saved but MP4 encoding failed
or was cancelled, Retry MP4 encodes that render again with the current encoder
path. It writes a separately named movie and log in the same folder. This retry
is available in the current session until another render starts. A render stopped
before all frames are written offers Show saved frames instead.
