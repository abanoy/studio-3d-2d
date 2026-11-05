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
240fps; project at most240frames; four drawing layers and32cels total; normalized
PNG output at most256MiB. A clip must fit the remaining scene range and available
cel slots in full. No dropped frames, partial layer, implicit truncation or raised
limits. Ordinary changing video can quickly exceed32holds. Shorten it externally
or use a shorter/lower-rate source that actually fits. Rotated/non-square-pixel
sources refuse with guidance. Container/codec support depends on installed FFmpeg.
VP8/VP9 WebM explicitly uses libvpx to retain alpha; absence of that decoder refuses.

Only file protocols and reviewed containers are admitted. Conversion runs in an
owned job with bounded metadata/logs/time/output, a cancellation flag, source
checksums before/after preparation and again at Add. No scene changes occur before
packet validation, full PNG decoding and final context/identity/resource checks.
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
Older applications may reject the new ancestry format; no downgrade is automatic.

## Fresh cloud evidence — 2026-11-05 UTC

- Full Python discovery:272run,271pass, one independent MMD-reader skip.
- Video procedural unit tests:10pass, real FFmpeg/QTRLE and VP9-alpha WebM,
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
