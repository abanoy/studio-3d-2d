# Measured verification — 2026-10-29

Actual local Windows execution: OS version reported 10.0.26300.0, Intel Arc 140V
8GB, OpenGL 3.3 driver 32.0.101.8626. Godot 4.6.stable.official.89cea1439, Python
3.13.1, FFmpeg N-118448-g43be8d0728-20250208. OS/GPU CIM queries were denied; OS
version came from .NET Environment and GPU information from the running renderer.

| Check | Actual result |
|---|---|
| Headless unit tests | 24 checks, 0 failures, exit 0 |
| Spike A/B render runner | Runtime original GLB, RGBA layer toggle, unchanged GLB SHA256, identical repeated GPU frame; exit 0 |
| Latest editor regression | 26 checks, 0 failures, exit 0; includes simulated mouse-look/WASD, actual input-event Space/arrows, tile undo/redo, duplicate isolation, zoom/pan, Unicode/spaces save twice, backup, reopen with frame restoration, PNG/MP4, pixel capture comparison, cancellation and corrupt-open preservation |
| Encoder failure runner | Missing sequence returns nonzero/readable log; cancellation stops the owned process and retains PNGs; exit 0 |
| Silent MP4 | H.264, 1920×1080, 24/1, 48 decoded frames, 2.000000s |
| Known-tone MP4 | H.264/AAC, 48 video frames, 2.000000s; decoded 10ms RMS tone onset 1.000s, expected frame 24 at 1.000s |
| Repository whitespace check | git diff --check, exit 0 |

Full orchestrated run: unit 0.374s; GPU spikes 5.345s; editor 6.206s;
encoder negative/cancel 1.259s. Subsequent targeted editor run, after adding saved
frame restoration and pointer-release handling, passed all 26 checks (exit 0).
These process durations include startup and tests, not real-time playback FPS.

Latest full-run microbenchmarks: 100 synthetic full-HD brush segments, radius 9:
6.875ms **total**; sequential rendering, RGBA composite and PNG write for 48 full-HD
frames: 2.840s. Initial run was 8.893ms / 2.568s; another run was 10.183ms / 3.317s.
This is a simple room, not a complex user scene. UI screenshot debug overlay update
was about 6.7ms for the two-cel fixture. No stylus end-to-end latency measurement
or artist assessment is implied; no quality claim about a finished painting engine.

Generated output/verification.json includes representative frame PNG SHA256 hashes,
run timings and duration metadata. output/editor-smoke/result.json records the latest
targeted run and successful movie path. output/editor-smoke/editor.png is an actual
application viewport screenshot, visually inspected. Outputs are ignored by Git.
Hashes establish repeatability on this GPU; they are not cross-driver golden tests.

An initial restricted-environment run crashed before scripts loaded because Godot
could not create its default AppData log directory. The launcher now passes an
absolute writable log file. Godot still prints a **shader-cache-folder startup
error** because its GL initialization attempts user:// before respecting the disabled
shader-cache setting. No test failed from this warning; rendering and encoding work.
Do not hide other engine/script errors or assume this applies to arbitrary failures.

Initial editor checks also exposed an incorrect Viewport method name in the keyboard
handler; fixed and rerun. Synthetic event tests wait between frames to avoid queued
event ambiguity. These earlier failures are not current passing results.

Unrun: clean-machine installer/EXE, physical tablet pressure/tilt, audible listening,
owner scene/art quality, very long Windows paths, real disk-full/power interruption,
importer fuzzing, alternate GPUs, texture/material-extension coverage. The full
acceptance story with editor audio/reference rig is not yet available.

## Stage 2 audio continuation

The current app now imports, previews, saves and exports one WAV clip. Latest full
`python -u tests/verify.py` exit 0: unit24 checks, editor26 checks, GPU/encoder spikes,
encoder negative/cancel, audio editor24 checks, and Dummy-audio fallback checks.
Suite process times: unit0.351s, spikes5.671s, editor6.147s, export failures1.485s,
audio editor6.269s, Dummy2.399s. This supersedes the earlier no-editor-audio limitation;
reference posing and the rest of Stage 2 remain unfinished.

The combined fixture uses the animated GLB room, an independent held stick-character
drawing, and a generated 44.1kHz mono WAV at project frame24 with -6dB gain. It clears
live audio and reopens schema2 to verify actual disk restoration; schema1 migration
is tested separately. The actual app bus is captured under WASAPI, muted after its
capture effect, proving real AudioStreamPlayer samples and seek/pause behavior.
Dummy mode proves explicit silent fallback without requiring an output device.

FFprobe verifies both silent output and the editor's audio output at H264/1080p,
24fps/48frames, exactly2.000000s. AAC decoded to PCM has onset1.000s and RMS5658.30
in the tone window, consistent with -6dB. These are analytical sync/gain results,
not subjective listening, speaker latency calibration or real voice lip-sync tests.
The device-reported output latency in the smoke logs is0.010s. Timer-based tests
use the actual compensated clock rather than assuming a fixed UI wall-clock frame
when synchronous edits delay a visual update.

An initial test incorrectly used PackedFloat32Array.max(), which Godot does not
provide; corrected with explicit peak reduction. An initial schema type membership
check rejected JSON numeric versions; changed to bounded integer validation, then
tested after clearing live state. No failing checks remain in the final full run.
Additional strict fallback checks exposed a harness timing/teardown issue: a first
render can exceed a short timer, so the test now waits for monotonic elapsed time
and at least three completed render frames before checking displayed position.
It also clears the player stream and allows pending audio work to finish before
removing the capture bus. A verbose Dummy rerun and final full run show no leaked
AudioStreamWAV/Playback resources. The verifier now treats ObjectDB leak warnings
as failures; the documented shader-cache initialization message remains unrelated.

## GMod/MMD compatibility continuation

Read-only inventory ran successfully on all six supplied native/container files.
Eight Python audit tests pass (exit0), including required-content records, traversal,
truncation, Lua-as-data, PMD/PMX metadata and LZMA wrapping. The initial compressed
test fixture incorrectly rewrote an EOS-terminated LZMA stream's declared size;
corrected it and added bounded unknown-size-stream support. Actual supplied legacy
files have known sizes and their indexes were read successfully.

Installed external Blender5.1.2 + MMD Tools4.5.11 prepared the street PMX and Miku PMD
into new staging directories. Source/dependency SHA256 values were unchanged after
conversion. Initial attempts caught missing shared toon ramps, then Blender's lazy
BMP data flag; explicit toon staging and image decoding resolved both. Original
native copies and packed editable Blender data are retained beside GLB and reports.

Real Godot compatibility runner: 13 checks,0 failures,exit0. Street: one mesh,103
surfaces,one bone. Miku: one mesh,17 surfaces,126 imported bones (122 native plus
helpers),15 vertex morph channels. Both render 1080p PNGs and survive managed project
save/reopen unchanged. Frame 3D scene leaves shot keys intact. Images inspected:
Miku bind pose looks usable; street single-sided geometry and materials remain
partial fidelity. A nonblank render test is not a visual-fidelity acceptance test.

Full existing `python -u tests/verify.py` exit0 after the framing control addition:
unit24,editor26,audio-editor24, GPU/encoder/cancellation and Dummy tests all pass;
silent and AAC outputs still48frames/2.000s, editor AAC onset1.000s.

No Source BSP/MDL render conversion, GMod add-on execution, physics simulation,
parameter editing or SMH save import was tested/implemented. The new owner-supplied
Ragdoll Mover/SMH/SheepyLord references were inspected via public primary sources
and the GitHub connector; relevant exact revisions are recorded in the compatibility
document. Their code was not copied or run.

One additional diagnostic Blender launch omitted factory startup and loaded a user
startup add-on that attempted a pip update. Network DNS failed and that owned process
was stopped; no successful install was reported. The actual preparation adapter
always uses factory startup/disabled autoexec/offline mode and isolated config.


## Recovery baseline — 2026-10-29

One1080p red-stroke cel plus managed procedural GLB/WAV and camera keys: checkpoint
32.404ms in the Windows worktree runner (includes scan/budget, hashing and manifest
write). Real separate-process restart and failed/partial manifest writes tested.
This is a small fixture, not latency/power-failure/maximum-cel or large-map evidence.
No shell package or new runtime added. Final canonical suite timings are in
output/verification.json.
