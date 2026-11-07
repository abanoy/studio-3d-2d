# Native drawing canvases

Open **Options → Native drawing canvas**, choose 1920 × 1080, 1280 × 720 or
960 × 540, and press **Apply canvas size** before drawing or adding sequences.
New still starts at 1920 × 1080 and 24fps. The canvas setting supports Undo/Redo.
The project-options dialog scrolls to keep controls accessible.

This changes the actual cel dimensions, drawing-input coordinates, camera viewport,
nested compositor and saved project metadata. It is different from delivery
resampling: a native720p drawing contains1280×720 editable pixels. The movie/PNG
default follows the native canvas. Advanced output controls can still choose a
separate delivery size; upscaling does not create source detail. The native option
is labelled in that list, and the selected delivery override persists as before.

Existing drawings are never resized by this command. It refuses current artwork,
sequences and drawing/sequence history that could restore artwork at another size.
Start a new project to choose another native size for existing artwork. An ordinary
Undo can restore the prior canvas after subsequent drawing commands are undone.
Playback, physical recording and unfinished drawing operations defer changes.
Native canvas changes preserve3D source files, object transforms and camera keys.
All profiles are16:9 and stay within the existing full-HD allocation bounds.

Packed and directory projects and recovery keep their native dimensions, exact
editable RGBA and rational timing. Parent/child scenes share canvas and frame rate;
child masks use their actual pixel bounds. Preparation requests already supply the
project dimensions to the Krita/video converters. Native-format fidelity still
requires its own approved fixtures; a smaller canvas does not establish it.

No project schema is renumbered. Existing1080p files keep their pixels and default
behavior. Older application builds that only support1080p refuse the new native
sizes; use a project copy with those builds. This is not a destructive migration.
Full-HD pixel maxima and memory targets are unchanged. Projects now permit up to
400 drawings across editable scenes, subject to byte admission; see
[larger projects](large_projects.md). Adaptive loading estimates use each scene's
actual decoded dimensions.

Verification exercises the actual project control, brush pointer mapping, exact
GPU preview, source/camera projection, canvas and pixel Undo/Redo, refusal with
live/deleted artwork, directory and packed Open, recovery checkpoints, nested
editing/masks and actual nested file publication. The cold reader runs without
the original3D/audio files or writer cache. Media probes and decoded PCM check
native dimensions, frame count/rational rate/duration and audio onset. These are
owned generated cloud fixtures, not Windows, physical-device or artist acceptance.

Run `python tests/verify_native_canvas.py --isolated-display :107` with an explicitly
owned private Linux display. Windows retains the private-desktop launch checks.
See [recorded evidence](benchmarks/native_canvas_2026-11-06.json).
