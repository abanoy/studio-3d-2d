# Fill connections

Advanced Draw → Fill → **Fill connections** offers:

- **Edges only** (default): pixels must share an edge. Corner-touching color
  areas remain separate. This is the previous four-connected behavior.
- **Edges and corners**: diagonally touching pixels also connect. It can color
  several touching details in one click, and can escape through a diagonal
  opening that Edges only would not cross.

Simple hides this specific adjustment. Switching modes does not reset the
selected connection rule. The choice is session tool state; reopened projects
retain their pixels without storing fill-tool settings. Fresh launches default
to Edges only. Tolerance still compares premultiplied RGBA against the clicked
seed, so transparent hidden RGB does not create a boundary and tolerance does
not drift through a gradient.

Ordinary small enclosed fills commit directly with Undo in either mode. Any
canvas-edge or large fill still previews before Apply. Nonzero gap closing or
under-line growth also retains its mandatory preview. Review a candidate if
corner connections reveal an unintended opening. The choice joins existing
stale-worker and immediate-Apply guards: changing it rejects a pending result.

Gap closing runs before connected-region discovery; growth runs afterwards.
The existing byte-only scanline worker handles corner neighbors at either end
of each row span. An additional byte mask for corner mode queues each pixel at
most once, bounding its pending frontier by the canvas pixel count. Edges only
does not allocate that mask. The canvas/memory bounds and cancellation/teardown
policies remain unchanged; CPU fills still take seconds on the development PC.

Only the active cel is painted with the chosen RGBA. Sample visible drawings
uses visible2D pixels, never the3D environment. Use Flats below ink to preserve
sampled line art. Existing cel/tile Undo, packed/linked HAS, recovery and final
rendering share the committed pixels. No scene/common-model schema change or
new native import/export dependency.

`python tests/verify_fill_connections.py` uses an independent per-pixel graph
oracle for every3×3 binary pattern, every seed and both connection rules
(9,216 combinations). Additional small irregular cases combine seed tolerance,
gap filtering and growth, including expected removed-seed refusals. Pixel data,
region/changed counts, bounds, edge detection and pending bounds are checked.
Domain checks include a large checkerboard and full-HD corner traversal.

The private actual-app workflow checks the real dropdown click/keyboard choice,
zoomed input, two enclosed compartments touching at one corner, RGBA/cel/tile
Undo and Redo, growth preview/cancel, stale connection changes, ink/world/camera
isolation, linked/recovery/cold packed Open and ordinary MP4 pixel agreement.
A separate deliberately altered test fixture confirms diagonal escape to the
canvas edge remains an unapplied spill preview. The saved example contains the
earlier intact ink fixture. See the dated memo/report for actual completed runs.

Primary terminology references: [OpenCV floodFill connectivity](https://docs.opencv.org/doc/doxygen/html/d7/d1b/group__imgproc__misc.html),
[Godot PopupMenu](https://docs.godotengine.org/en/4.6/classes/class_popupmenu.html).
This is an original bounded GDScript implementation, not an OpenCV runtime.
Adaptive anti-alias reconstruction and broader2D/KRA/video authoring remain
unfinished; automated tests do not certify physical artist/tablet acceptance.
