# Held drawing preview reuse

The ordinary preview reuses its drawing overlay while the same visible cels are
held. The 3D world, camera, playhead and audio continue to evaluate independently.
A new cel, brush edit, Undo, opacity/visibility/order change, document revision or
output-size change rebuilds the overlay. An unchanged overlay also avoids another
full-raster GPU upload. Onion guides and canvas redraws still update normally.

`drawing_overlay_cache.gd` belongs to one app instance. It retains one derived
image of at most2073600pixels (8294400RGBA bytes), plus small identity metadata
and weak source references. A miss releases the preceding cache entry before
compositing. Oversized results are returned without retention. Source Images,
pixels, cel ownership and history are unchanged. A document revision invalidates
raw pixel changes reported through the ordinary `app.changed()` path even when
an editing helper has not set pixel-revision metadata.

This cache is used only by the app's ordinary overlay update. `Drawing.composite`
keeps its existing fresh-image behavior; final rendering, transparent PNG output,
fill/selection sampling and recovery workers retain their existing paths. No new
project fields, format version or dependency is introduced.

Run `python tests/verify_drawing_overlay_cache.py --isolated-display :103` on an
explicitly provisioned private Linux display. `--output /absolute/new/folder`
keeps its proof outside the checkout. Windows retains the private launcher.
The verifier checks20cache cases,26actual GUI/edit/save/export cases and4fresh
packed readers with originals and writer cache unavailable. The actual48frame
1080p24 H264/AAC movie has exact preview/PNG input and decoded cue onset48001
versus48000 at48kHz. Manual HAS and original room/WAV bytes remain unchanged.
This50check run passes; proof is under
`/workspace/has-handoff-audit/held-preview-accepted/verification.json`.

The existing34check onion-skin scenario also passes, including real GPU guide
pixels, fill sampling, held-neighbor texture reuse, brush Undo/Redo, canvas
zoom/pan, recovery and exact48frame movie exclusion. Proof:
`/workspace/has-handoff-audit/held-preview-onion/verification.json`.
These software checks do not establish physical tablet feel or whole-app frame
pacing on the owner's GPU.

The reproducible seek-loop script is `tests/held_preview_benchmark.gd`. Launch it
through `run.command()` after `run.configure_private_display()` on Linux, passing
a new output directory after `--`. It disables automatic app processing, warms
frame0, then times three240-seek loops through normal `set_frame` and `_process`
with two original1080p held cels. Each run compares the actual GPU overlay to the
uncached compositor. This measures overlay/UI seek work; it excludes movie
rendering waits, audio-device latency and physical input.

Three-run mean for this controlled seek loop changed from2993.490ms to
29.705ms. Baseline runs were3044.441/2989.180/2946.849ms; final cache runs
were33.041/28.973/27.101ms. After excluded frame0 warmup, each cached loop
has1build at the second drawing and239hits. No other owned regression ran
during these recorded measurements. This is about100.8times less time in
that specific loop, not an overall renderer/frame-rate claim. See the
[scoped measurement](benchmarks/held_drawing_preview_2026-11-06.json).

The existing161check drawing-timing/cold/SIGKILL verifier also passes with this
cache, including its full1440frame1080p24 H264/AAC60second movie and exact sampled
preview/PNG frames. The decoded56second sound onset is2688001 versus2688000.
That export overlapped other regression work, so its230.176second duration is
a scoped run result rather than a performance comparison. Proof:
`/workspace/has-handoff-audit/held-preview-cel-timing/verification.json`.
Full Python discovery runs312tests, with311passes and one existing independent-
MMD-reader skip. Existing frame/cel/layer limits remain unchanged.
