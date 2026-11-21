# Contact rotation gesture correction proposal

c315 Full failed four of129 contact-transform assertions; all167 private jobs closed, source1103/HEAD preserved, all626 new UI/camera and height routes passed. The failed Full is not qualified. Preserve source-full-c315-failed-prep-20261121 separately.

The test still generated pointer deltas using a fixed .02 radians-per-pixel assumption. Current rings calculate signed ray/plane angles (or a projected tangent at edge-on views), so that pointer does not request the intended90 degrees. This proposal projects an independently constructed world-Y one-degree and90-degree rotation of the picked plane radial. Its setup refuses the unsupported edge-on profile; existing ring309 regressions separately cover that fallback. Numeric+90 is already proven unreachable immediately before the gesture in each of five native contexts.

All129 assertions, native5×25 counts, original .0002 contact threshold, exact last-valid data, Undo/Redo/Record/physics guards,49frame reach, packed HAS and exact movie comparisons remain. The invalid gesture assertion is stronger: it requires the named native out-of-reach diagnostic. The Python wrapper now requires the exact129 and25-per-native counts. No production file, solver, parser or tolerance changes. This is a SOURCE ONLY proposal; actual private scoped requalification is required before adoption.
