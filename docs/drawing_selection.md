# Select and reposition drawing pixels

In Draw, choose **Select area [M]**. Drag a rectangular area, then drag inside it
to move its pixels. Hold Shift when starting that second drag to keep a copy.
Releasing commits one tile-based Undo step; there is no extra Apply button.
Escape or right-click cancels an unfinished gesture. Clear selection hides the
border without erasing pixels. Ctrl+Z during a drag cancels that uncommitted
gesture first; the next Undo operates on existing project history.

The tool is available in Simple and Advanced. M respects text-field focus.
Selection and offsets use output pixels through ordinary canvas zoom/pan.
Rectangle ends snap to pixel edges; motion rounds to whole pixels without
resampling. The entire selected rectangle stops at canvas bounds, including
release outside the view. You cannot drag pixels off the document with this
first tool. A click without motion, stationary Shift-click, or entirely
transparent selected area creates no history edit. No cel is allocated merely
by selecting on a layer with no drawing.

Only the active visible cel is edited. Held frames share that image: use Copy
drawing here first if only one exposure should change. Moving cuts the rectangle
to transparent black, then alpha-blends its detached original patch over the
destination; transparent patch pixels do not erase destination artwork. Copy
keeps the original. Overlap is safe because the patch is detached before cutting.
Unselected pixels/layers, scene sources, model/bone data and camera keys stay
independent. One bounded before/after tile command preserves the existing Image
identity, full RGBA Undo and live3D physics. Layer opacity is a display/composite
property and is not baked into moved pixel colors.

While dragging, the source cel remains untouched. At most one candidate composite
is built per UI frame using the latest offset; pointer events are coalesced.
The canvas-only preview and high-contrast border never enter saves, recovery or
the final renderer. Drop uses the latest guarded result even when no preview
frame occurred. Seek, mode/tool/layer changes, document edits/replacement,
hidden/zero-opacity layers, playback/export, imports, window focus loss or invalid
release coordinates discard transient state. Save/export uses committed pixels;
export explicitly cancels any unfinished gesture. New releases all references.
Pixel/cel identity, revision, frame and session are validated before commit.

The direct canvas gesture supports one rectangular raster selection with
integer move/Shift-copy. [Resize / rotate](drawing_transform.md) separately
adds previewed numeric scale/free-angle rotation and Advanced stretch/copy.
Lasso/magic-wand masks, clipboard/cut/paste/delete, cross-cel selection and
animated2D placement remain unfinished. No system clipboard, project schema or
standard-model format changes; the larger drawing feature set remains open.

`python tests/verify_drawing_selection.py` checks detached move/copy, overlaps,
clamping, no-ops, transparent hidden RGB and invalid inputs. Its independent
per-pixel source-over/translation oracle covers192 cases:64 opaque cases must
match exactly; fractional-alpha cases permit at most one8bit step of engine
float quantization against the mathematical reference. Undo, saved pixels and
preview/movie comparisons remain byte-exact. A full-HD840,000pixel translation
and actual preview timing are measured, not claimed universal latency.

The private app test routes zoomed/panned selection/move input, Shift-copy,
outside release, text focus, actual Clear button at1200pixels, Escape, coalesced
events, stale/focus/hidden/tool/New guards and a real running standard-model
ragdoll. Persistence/export deliberately restores the authored world first for
deterministic packed/linked/recovery/cold-reader/movie comparisons; it does not
claim this test bakes live physics. Physical artist/tablet/keyboard acceptance,
clean-PC and larger production projects remain unverified.

Primary reference: [Godot Image blend_rect/blit_rect semantics](https://docs.godotengine.org/en/4.6/classes/class_image.html).
