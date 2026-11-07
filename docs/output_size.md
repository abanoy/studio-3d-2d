# Delivery output sizes

In **Advanced → Movie encoder → Output size**, choose 1920 × 1080,
1280 × 720, or 960 × 540. The choice applies to new MP4 renders and complete or
transparent PNG sequences. Movie quality controls compression independently.
New and legacy1080p projects default to1080p. A native720p/540p project defaults
to its own canvas size; the list labels that profile as native. The selected delivery size is saved with
the scene in packed/linked HAS, directory saves and recovery. It supports Undo/Redo,
marks the project changed, and follows parent/child scene navigation. Returning to
Simple mode keeps the saved choice.

Choosing a delivery size keeps the current native canvas and saved cel coordinates.
When dimensions differ, the complete composite is resized once before writing each
delivery PNG. Smaller exports contain downsampled artwork; larger exports add no
source detail. To draw at a different native size in a new project, use
[Native drawing canvas](native_canvas.md) in Options before creating artwork or
sequences. Supported native profiles are1080p/720p/540p;4K and other aspect ratios
remain unsupported. Existing files without `video.output_size` use their native
canvas, preserving legacy1080p behavior. Resource limits are unchanged.

Settings are captured before rendering starts. Changing the selection during an
attempt cannot change that attempt's size. Retry MP4 reuses its saved PNGs, WAV and
dimensions, regardless of the current size selection. To change size, start a new
render. Invalid size selections refuse before creating an output folder.

The default-size path returns the original Image without copying or conversion.
Downsampling uses a detached RGBA8 image and bilinear interpolation, with alpha
premultiplication before resizing and conversion back to straight alpha afterward.
This prevents hidden RGB under transparent pixels from bleeding into drawing
edges. Interpolation operates on encoded byte values; it is not linear-light,
HDR or a color-management expansion. The source Image is never modified.

PNG `sequence.json.video` records delivery dimensions. When they differ from the
source, `source_video` additionally records the original canvas/timing contract.
Frame count, rational FPS, duration and synchronized audio remain unchanged.

## Verification

Run `python tests/verify_output_size.py --isolated-display :105` with an explicitly
provisioned private Linux display and activated pinned tools. Windows uses the
existing private-desktop launcher. The display number is an example, not shared
or automatically discovered desktop authorization.

The owned procedural media fixture passed22 unit,14 app and3 fresh-reader checks:
independent alpha/color interpolation oracles, unchanged sources/default pixels,
720p movie and retry, 48 transparent 540p PNGs, captured selection, invalid-input
refusal, ordinary packed HAS and cold load with the writer cache unavailable.
Independent ffprobe/PNG-header checks confirmed actual dimensions; both movies
have 48 H264 frames at 24fps and AAC, with the authored one-second cue decoded at
sample 48043 of 48000Hz. The original 1080p quality and PNG export regressions
are recorded separately in the progress memo. These are cloud software checks,
not native model fidelity, Windows hardware or artist acceptance.


Project-settings checks additionally verify16 writer and1 fresh-reader cases:
reversible scene metadata, unchanged physics during settings Undo, export-time
mutation guards, ordinary packed/directory save, a real recovery checkpoint,
invalid settings preserving the prior manifest/current project, scene navigation
and New reset. The writer cache is unavailable for fresh packed Open. Two Python
container tests exercise all3valid values and mistyped/unknown values, preserving
the prior HAS on refusal (22container tests pass). Earlier media assertions now
expect the intentional two settings history commands and saved540p choice; source
video/canvas, world, keys, drawings and sound still compare exactly.

See [persisted settings evidence](benchmarks/output_settings_2026-11-06.json).
