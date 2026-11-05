# Fill beneath line edges

Choose Draw → Fill → Color layer below. Keep ink above Flats and keep Sample
visible drawings enabled. In Advanced, **Grow under lines (pixels)** extends
the discovered fill region by0–8 pixels into a square neighborhood. Default0
keeps previous fill behavior. The setting is a session tool adjustment, not a
saved project field. Simple mode uses the same engine without showing this
specific control; switching modes does not change an already selected amount.

Small amounts can put flat color underneath translucent/anti-aliased ink edges
that would otherwise leave a transparent or pale seam. The original ink remains
unchanged because only the active drawing layer is painted. Existing target
pixels are replaced with the chosen exact RGBA, including its alpha. Use a
separate Flats layer: growth on the ink layer itself can overwrite its pixels.

Every changed nonzero-growth result requires preview and Apply/Cancel, even for
a small enclosed region. Growth deliberately crosses sampled boundaries: it
can cover an adjacent narrow detail, an existing nearby color, or a virtual
gap closure. It does not understand artistic intent. Reduce the amount or use0
if the candidate crosses an intended boundary. Growth clips to the canvas and
never expands the document. Square corners and a hard mask are explicit current
limits; this is not adaptive anti-alias reconstruction or subpixel feathering.

Gap closing happens first, then ordinary connected-region discovery, then growth.
The existing detached worker dilates the visited-region byte mask with two
separable rolling-count passes, using a centered square of width2r+1 and zero
padding. Sampled boundaries are not dilated into the target or copied as ink.
Work/storage remain linear in the bounded full-HD canvas. UI frames continue;
fills still take seconds on this machine. Cancellation discards the result but
does not interrupt the bounded worker, and app teardown joins it as before.

Radius joins the existing context/settings guard, so changing it during work or
immediately before Apply rejects a stale candidate. Ordinary revision, frame,
layer, color, tolerance, sampling, tool, mode and export checks still apply.
Committed growth becomes ordinary cel pixels with existing cel/tile Undo; no
schema/common-model changes. Packed/linked HAS, recovery and MP4 share those
pixels. Preview candidates are never saved or included in the final renderer.

`python tests/verify_fill_expand.py` compares the engine against an independent
per-pixel BFS plus full2D-neighborhood oracle on45 combinations of thin/tiny and
irregular canvases and radius0–8. Domain checks cover exact bounds, clipping,
no-op replacement, invalid radius, source immutability, gap interaction and a
full-HD canvas. Private app checks route zoomed drawing input and real preview
buttons at1200pixels, compare translucent-edge coverage, Undo/Redo, stale worker
and Apply, linked/recovery/cold packed Open, unchanged world/camera/source and
ordinary movie pixels. See the dated memo/report for actual completed results.

Primary mathematical reference: [OpenCV dilation and rectangular kernels](https://docs.opencv.org/4.13.0/d9/d61/tutorial_py_morphological_ops.html).
No OpenCV package/runtime is used. Advanced [Fill connections](fill_connections.md)
chooses whether corner neighbors join before growth. Further edge refinement,
richer drawing/KRA/video tools and physical artist acceptance remain unfinished.
