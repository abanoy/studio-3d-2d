# Optional stroke smoothing

In Draw, enable **Advanced** and set **Stroke smoothing (pixels)**. Zero is the
original brush and is the default. A small positive value filters hand jitter by
letting the painted point trail within that distance of the pointer. The maximum
is32 canvas pixels, independent of viewport zoom. Larger distances smooth more
and feel less immediate; the last short tail finishes when the gesture ends.

Smoothing works on pen and eraser paths. Existing size, pressure, color and opacity
remain separate. All these settings, including smoothing distance, are captured
when a stroke starts; changing a control midway applies to the next stroke.
Release outside the viewport, focus loss and ordinary stroke completion finish
the pending tail before committing one pixel Undo command. Zero tablet pressure
finishes the preceding contact at its last positive-pressure point, then resets
the stabilizer. It never draws a bridge across a hover gap. With no positive
pressure, no new cel, artwork or history is created.

This is a deterministic distance-based stabilizer, not a clock-dependent animation
filter or a pressure predictor. It does not change cel exposures or synthesize
intermediate animation drawings. Fill and area transforms keep their existing
workflows. Smoothing is a session brush setting; only resulting normal RGBA pixels
enter HAS, recovery and export. New sessions default to zero. Existing projects
need no new format/reader. Disable smoothing to use the original raster path.
Drawing and drawing Undo/Redo preserve running3D physics as before.

Run `python tests/verify_stroke_smoothing.py --isolated-display :99` on Linux with
an already provisioned private display and pinned Godot/FFmpeg. Windows retains
private-desktop receipt checks. Fresh private llvmpipe checks:12 domain tests,
26 actual app checks and4 cold-reader checks. They verify byte-identical disabled
brush output, changed smoothed geometry, tail completion, pressure gaps, no-cel
waiting, captured settings, pen/eraser opacity, exact Undo/Redo, live physics,
source preservation, normal packed HAS/recovery and exact H2641080p24/48-frame
movie input. No transient stabilizer fields appear in the archive.

Existing pressure and brush-opacity verifiers also accept explicit private Linux
displays while retaining Windows checks. Their fresh regressions pass unchanged
mathematics, ordinary drawing, cold HAS and real movie output. Synthetic routed
pressure events establish software behavior, not physical tablet/driver feel.
Pen comfort, latency and artistic smoothing preference remain owner acceptance.
