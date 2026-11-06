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
The beginner course also stores narrowly validated observations (actual live
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
replacement or normal app close saves a checkpoint/resume state. Ordinary recovery
now includes the active teacher context and reattaches it after a crash when the
local practice history remains available. See [lesson recovery](lesson_recovery.md)
for checkpoint scheduling, validation, fallback and remaining limitations. There
is no separate periodic lesson autosave.
Session folders retain shared content-addressed cels within each fixed checkpoint;
there is no cross-session deduplication, retention policy or concurrent writer lock.

This is a runnable beginner route and initial focused chapters, **not complete
tutorial coverage**. Further work: advanced rig-authoring practice, more topic/subsection entry points,
progressive demonstrations and beginner usability feedback. The focused physics chapter below now teaches explicit Local capture; multi-body
World recording and native secondary rigs need their own practice/acceptance.
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


## 2026-11-05 UTC — lighting and export tutorial chapter

Home → Tutorials now includes **Advanced · Lighting and export**. Start fresh
opens the existing included editable room/figure practice. Four tasks cover
Advanced, Unshaded base colors, Studio light versus imported-scene Lit, and an
actual successful MP4. Hints highlight the real lighting menu/export control.
PNG-only output or a failed export does not award the movie task. Saving the
practice project remains optional. Previous restores prior lighting and export
observation; Continue/Fresh retains independent sessions and unsaved-copy identity.

New course identity `advanced-lighting-v1` has4steps. All existing course IDs,
lengths, asset hashes and lesson progress1/observation contracts stay unchanged.
The export action row now remains visible for chapters with an export button
without another action. No app project format, lighting implementation, native
material editing, compulsory Save or tutorial Skip policy is changed.

Fresh isolated llvmpipe app checks: new chapter19 + cold reader5; unchanged
basic pose/draw + camera chapter52 + cold reader5. Both actual H2641080p24 movies
have48frames/two seconds. New lesson preview/export input bytes match exactly,
failed encoder preserves progress, Previous requires a new export, and original
practice geometry/audio/HAS hashes remain exact. Windows private-desktop checks
remain in the portable wrapper but were not run here. Logs/copied verification
JSON are in /workspace/has-handoff-audit/lighting-lesson and tutorial-regression*.

Reproduce with `python tests/verify_tutorials.py --chapter lighting`; on Linux
provide an already provisioned private dummy display using `--isolated-display :99`.
Default chapter preserves the existing pose/camera regression. This adds focused
coverage; advanced interpolation/constraints/rigging/physics chapters, richer
demonstrations and artist feedback remain. Full application is still incomplete.


## Interpolation and cuts

Home → Tutorials → **Advanced · Interpolation and cuts** opens the included
editable room/figure. Five tasks compare saved camera endpoints, hold/cut, linear
and ease. The interpolation stored on the outgoing key controls the interval.
Changing the dropdown without saving does not change animation. In Draw, seek0
to reload the saved starting shot, switch to Scene to replace its interpolation,
then return to Draw and seek the comparison frame. Scene mode keeps a temporary
navigation view when seeking; Draw evaluates the recorded camera.

Hold waits until the next key, linear travels a quarter of the distance at frame6
between0 and24, and ease travels15.625% at that time while preserving both exact
key poses. Painted cels keep their independent exposures. Grading checks actual
saved keys, requested sample/mode and evaluated view; extra intervening keys need
to be removed for this two-key exercise. Previous restores the whole prior
checkpoint; Continue and fresh sessions preserve earlier practice. Save remains
optional. Existing course identities and sample bytes stay unchanged.

Run `python tests/verify_tutorials.py --chapter interpolation`; Linux additionally
requires an explicitly provisioned `--isolated-display :99`. Fresh cloud checks:
26 writer +6 cold reader, rendered hold/linear/ease comparison, ordinary HAS save,
exact preview/MP4 input and H2641920×1080/24fps/48frames. These procedural llvmpipe
checks do not establish Windows/GPU/physical-device or artist acceptance.


## Rig posing and foot constraints

**Advanced · Rig posing and foot constraints** uses the existing included figure's
bone tree and skinned mesh. Five exercises select the figure in Pose mode, key an
arm pose, plant both feet for0–24 inclusive, lower the root at12 while retaining
world foot targets, then release12–24 while keeping earlier pins. The teacher
checks saved ranges, root key and actual foot positions. A toggle or open window
alone does not count. Unreachable motion refuses safely.

This chapter teaches existing rig posing and constraints. It does not author a
new skeleton or weights. **Hold feet while posing** is a temporary authoring
helper; **Planted feet…** saves persistent playback ranges. Previous restores the
whole constrained scene, and Continue/Fresh retains independent practices. Native
rigs still need their own import/binding fidelity checks.

Run `python tests/verify_tutorials.py --chapter constraints`, with an explicit
private `--isolated-display :99` on Linux. Fresh procedural llvmpipe checks:
24 writer +5 cold reader, real Plant/Release and pose controls, Undo/Redo, exact
Previous pixels, ordinary HAS and H2641080p24/48frames movie input agreement.


## Explicit physics recording

**Advanced · Physics recording** separates live simulation, frozen pose and saved
animation. Five tasks select the original figure, run/freeze Physics, commit a
Local take from0 through12 or later, play/pause the recorded take with Physics off,
and export an MP4. The teacher observes successful capture installation and checks
scope, figure identity, range and saved sample keys. Cancelled and World takes do
not satisfy the Local exercise. The hint explains that World instead records all
currently simulated bodies; one figure does not demonstrate multi-body capture.

The saved take remains editable. Previous before capture removes that take and
its completion flag; Previous before preview retains the take but requires a new
Play/pause. Continue restores these observations with the project, and Start fresh
keeps prior practices. Save stays optional. The growing catalog has a scroll area.
Run `python tests/verify_tutorials.py --chapter physics`, adding an explicitly
provisioned private `--isolated-display :99` on Linux. Fresh software checks:
25 writer +5 cold reader, actual simulation and capture, exact movie input and
H2641080p24/48frames. Native joints/cloth and physical-device acceptance are separate.

The original beginner path verifier now also accepts `--isolated-display :99` on
Linux and preserves Windows private-desktop checks. Fresh79writer +8coldreader,
actual AAC sync and render/encoder cancellation plus retry pass. Linux encoder
cancellation avoids querying an already reaped child; cancelled frames/mix remain
available for retry. See `tests/verify_first_movie.py`.
