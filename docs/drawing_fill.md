# Color fill without changing line art or 3D

Choose **Draw**, then **Fill [F]**. **Color layer below** creates Flats beneath the
selected drawing layer, or selects existing Flats. Ink keeps its own original
pixels. Existing projects and New retain their layer order until this explicit
action; no migration or extra default layer is imposed. This prototype supports
four layers and32 full-HD cels. Undo restores the layer and its selection while
retaining older stroke history.

Pick a color and click inside a drawn outline. By default **Sample visible
drawings** uses the composite of visible2D cels as the region boundary; it never
samples the3D background. Turn it off to sample only the active layer. Hidden
layers cannot be painted. The filled result changes only the active cel, including
its existing held frames; Copy drawing here first when a variation is wanted.
An absent cel is created only when the fill is committed.

Fill defaults to four-connected; Advanced [Fill connections](fill_connections.md)
can also join diagonal neighbors. It compares against the clicked seed, using premultiplied
RGB and alpha distance so invisible RGB cannot create false boundaries. Advanced
offers tolerance0–255, initially8. It replaces selected pixels with the exact
chosen RGBA color. Identical results are no-ops. Existing cels use changed64pixel
tiles for one-step Undo; a new filled cel is also one undoable action.

Small enclosed fills apply directly. A fill reaching any canvas edge or covering
over half the canvas shows a candidate preview and **Apply fill / Cancel**. This
is spill protection. The newer [Close gaps control](fill_gaps.md), default0,
adds virtual closures with mandatory preview and leaves original ink untouched.
The preview composites all drawing
layers in their normal order over the unchanged3D view; it does not alter project
pixels, save/recovery data or final rendering. Escape cancels. Ordinary painting,
Undo, seek, New/Open, mode/tool changes, playback or export invalidate stale work.
Pan/zoom can continue without changing the fill's raster coordinates.

When the preview appears, Properties scrolls just enough to reveal its Apply and
Cancel buttons after layout. This matters with resized/docked panels at1200px
width. It happens once per new preview, leaves manual scrolling available and
does not move focus or create an exclusive dialog. Closing the app disconnects a
pending reveal callback. The actual narrow-window check verifies both complete
button rectangles and routes pointer clicks to Cancel and Apply.

One low-priority worker owns only detached RGBA byte arrays and a bounded iterative
scanline traversal. It never accesses live Images, textures, nodes or native model
data. Main processing joins completed work, verifies document revision/frame/layer
identity, and commits or discards it. Teardown joins remaining work. Full-HD fills
take about2seconds on the development machine; UI frames continue while scanning.
Initial snapshot/composite copies, preview texture preparation, tile history and
commit remain on the main thread. No universal latency/tablet/DPI guarantee.

The existing layer/cel schema, packed/linked HAS, recovery, master timeline and
MP4 renderer are unchanged. Older two-layer files retain exact pixels. No source
asset, rig, camera key or model/world format is modified by filling.

## Verification and remaining work

The full particle-scene regression on2026-11-02 caught clipped preview buttons in
the new workspace layout. That run is retained as failed. The correction passes
18 unit+48 app checks, including actual pointer routing, independent pixels,
packed/linked/recovery and MP4, at `output/fill/1793671335667726600`.
The source was then frozen again; the replacement complete verifier and separate
HAS wrapper subsequently terminated0. The original failed run remains separate.

`python -u tests/verify_fill.py` checks exact region/bounds/alpha, independent BFS
oracle pixels, transparent RGB, seed tolerance, invalid inputs and full-HD traversal.
The hidden actual-app check routes zoom/pan pen and fill events, validates original
layer/image identities through older Undo/Redo, exact ink/world/camera isolation,
no-op and tile history, actual background UI frames, precise candidate preview,
edge/gap cancel/Apply, real intervening painting, hidden-layer refusal, New/Home
lifecycle, packed/linked/recovery, older two-layer files and MP4 preview agreement.
See the latest progress memo for completed run counts and saved-copy status.

Advanced [Grow under lines](fill_expand.md) offers previewed0–8pixel expansion
to cover beneath translucent ink; adaptive anti-alias edge refinement and
richer layer counts remain required drawing work. [Pressure size](brush_pressure.md)
and the existing color sampler have separate controls; physical tablet acceptance
remains open. [Project swatches](project_palette.md), [layer management](drawing_layers.md) and one neighboring
exposure each side as [onion guides](onion_skin.md) now have separate controls.
Visible-stack sampling includes [layer opacity](layer_opacity.md); very faint
boundaries may fall within the chosen tolerance. The current gap
check starts from an unfilled color layer; existing colored regions can themselves
form a boundary when sampling all visible drawings. It does not infer artistic
intent or automatically repair imported art. General native KRA remains unsupported.

Primary implementation references: [Godot4.6 thread-safe APIs](https://docs.godotengine.org/en/4.6/tutorials/performance/thread_safe_apis.html)
and [Thread joining/lifecycle](https://docs.godotengine.org/en/4.6/classes/class_thread.html).
No engine thread-safety checks or render/physics threading settings are disabled.
