# Video artwork import

In Draw mode choose **Import video artwork…**, select a local MP4, MOV, MKV,
WebM or AVI, review the source, then choose **Prepare preview**. Installed FFmpeg
and its neighboring FFprobe are required. No converter is downloaded or bundled.

True alpha is preserved. For a solid background, enable green/blue removal and
adjust Color tolerance and Edge softness before preparing. Keying multiplies its
matte by the source alpha and suppresses the selected color's spill. Scaling uses
premultiplied alpha to avoid transparent-edge color fringes. Review the complete
result against the checkerboard and scrub its source-local frames; the main
playhead stays put. **Add drawing layer** commits one Undo operation. Cancel,
seeking, editing the scene, or changing projects invalidates an unfinished import.

The complete clip becomes independent, editable RGBA drawing holds at the project
frame rate, starting at the playhead. Consecutive identical pictures share a hold.
The source is never rewritten, and later source edits do not change imported cels.
Video audio is **not imported**; use the existing Import audio operation separately.
This is raster artwork import, not a linked video track or an editable nested sequence.

Bounds remain deliberate: source at most192MiB,16,777,216pixels,60seconds and
240fps. A parent project can use the existing extended scene timing (up to60seconds
and7200frames), while one video preparation decodes at most400project frames.
There are four drawing layers and400drawings total across the project and direct
children. Normalized PNG output stays at most256MiB; registered owned raster plus
retained decoded cache admission stays320MiB. A clip must fit the remaining scene
range, drawing capacity and byte budgets in full. Complex/noisy material can
refuse before400drawings. No frames are dropped or truncated. Shorten the source
or lower the project rate when its decoded range exceeds400frames. Rotated/non-square-pixel
sources refuse with guidance. Container/codec support depends on installed FFmpeg.
VP8/VP9 WebM explicitly uses libvpx to retain alpha; absence of that decoder refuses.

Only file protocols and reviewed containers are admitted. Conversion runs in an
owned job with bounded metadata/logs/time/output, a cancellation flag, source
checksums before/after preparation and again at Add. No scene changes occur before
packet validation, incremental per-frame PNG decoding into admitted cold owners,
and final context/identity/resource checks.
Krita and video reviews cannot race each other. Close requests cancel an active
worker and wait for it to drain before the next close.

## Data compatibility

`studio_raster_clip_1` and `studio_drawing_origin_1` retain their Krita meaning.
Video uses explicit `studio_raster_clip_2` and descriptive
`studio_drawing_origin_2` (`kind: video`). Its13fields retain source basename,
SHA256, dimensions, exact source rate/duration rationals, four chroma choices,
canvas fit, project rate, placement and duration. Ancestry contains no required
external path and never resolves source assets. Python and Godot validate it.
Prepared packets stay local to the job; projects embed ordinary cel pixels in
both packed and linked HAS. Scene5, Model9, audio4 contracts are unchanged.
Extended video placement uses the existing `studio_drawing_origin_4`; its video
duration now admits up to400frames. Legacy origin2 and Krita origin1/3 bounds
remain unchanged. Older builds can refuse a duration above their former240frame
bound; no downgrade or silent truncation is automatic.

## Fresh cloud evidence — 2026-11-05 UTC

- Full Python discovery:281run,280pass, one independent MMD-reader skip.
- Video procedural unit tests:11pass, real FFmpeg/QTRLE and VP9-alpha WebM,
  fractional24000/1001timing, green key, semi-transparent alpha, fit, budgets,
  cancellation, immutable source, invalid settings and fresh-output refusal.
- Python/Godot drawing-origin corpus:51matching decisions; headless core24 and
  existing Krita raster-packet17checks pass.
- Actual application:19checks; separate process packed/linked reader7checks.
  Portable runner also moves the source before reopening. Recovery pixels,
  exact preview/export input pixels, Undo/Redo and cancellation guards pass.
- Decoded H.2641920×1080,24fps,48frames,2seconds; no audio track required.

Graphical runs used an isolated dummy X display and llvmpipe, not the shared
desktop. These results do not certify Windows, native model fidelity, hardware
audio, tablet latency or artist acceptance. The Windows private-desktop branch of
the new runner has not been exercised here.

Reproduce units with `python -m unittest discover -s tests -p test_video_import.py`.
`python tests/verify_video_import.py` uses the existing private Windows launcher.
On Linux, first provision an owned isolated dummy X server, then explicitly pass
`--isolated-display :99`; the runner refuses an implicit shared-display fallback.
Set `HYBRID_GODOT` to pinned4.6stable and `HYBRID_FFMPEG` to installed FFmpeg.
Local fresh logs and `verification.json` are under
`/workspace/has-handoff-audit/video-portable`; generated media are not source files.

Per-stream duration takes priority over container duration. Matroska/WebM stream
DURATION tags and known frame counts are accepted when ordinary stream duration
is absent. A longer ignored audio stream does not create extra video holds. A
source without usable picture-stream timing refuses instead of guessing from the
container's audio end. The added procedural FFV1/PCM Matroska case verifies this.

## 400 prepared drawings — November 7

The actual app now passes 28 writer and 7 source/job/cache-offline cold-reader
checks for 400 unique drawings normalized from an original generated alpha video
to full HD. The test cancels a complete pending import and releases every owner,
then repeats preparation, adds one reversible layer, paints one cel, checks all
399 peers, saves recovery/HAS and exports a 400-frame 1080p/24 H.264 movie.
All 400 prepared and reopened pixel hashes match; four GPU/export inputs repeat
exactly. The short-video regression passes 27 writer and 7 reader checks.

Two preparations took 46.878 and 46.689 seconds while 1403 application frames ran;
the largest observed ingress frame gap was 172.802 ms on this cloud run. Prepared
PNGs used 35,603,691 bytes. Final registered drawing storage was 51,212,405 bytes
under the unchanged 335,544,320-byte limit; cold reader storage was 42,989,051 bytes.
The separate Godot-process peak was 545,894,400 bytes. These counters are not a
whole-application RAM limit and do not certify physical-device responsiveness.

Background recovery completed in 120.796 seconds. Manual Save took 76.036 seconds;
its PNG snapshot still blocks the main thread before packaging. Moving that stage
to a worker is the next task. Native Krita preparation and noisy400-frame videos
are not certified by this original generated corpus. See the
[curated receipt](benchmarks/large_prepared_video_2026-11-07.json).
