# Delivery output sizes

In **Advanced → Movie encoder → Output size**, choose 1920 × 1080 (default),
1280 × 720, or 960 × 540. The choice applies to new MP4 renders and complete or
transparent PNG sequences. Movie quality controls compression independently.
A new application session starts at 1080p; this choice is not saved in a HAS.
Returning to Simple mode keeps the current session choice.

The source canvas, camera evaluation and saved cel coordinates remain 1920 × 1080.
The complete composite is resized once before writing each delivery PNG. Smaller
exports contain downsampled artwork; this does not add native variable-resolution
canvases, extra source detail, 4K, different aspect ratios, or project-persisted
render settings. OUTPUT-02 remains partial for those canvas/settings requirements.
Existing project files and resource limits are unchanged.

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

The owned procedural fixture passed 12 unit, 14 app and 3 fresh-reader checks:
independent alpha/color interpolation oracles, unchanged sources/default pixels,
720p movie and retry, 48 transparent 540p PNGs, captured selection, invalid-input
refusal, ordinary packed HAS and cold load with the writer cache unavailable.
Independent ffprobe/PNG-header checks confirmed actual dimensions; both movies
have 48 H264 frames at 24fps and AAC, with the authored one-second cue decoded at
sample 48043 of 48000Hz. The original 1080p quality and PNG export regressions
are recorded separately in the progress memo. These are cloud software checks,
not native model fidelity, Windows hardware or artist acceptance.
