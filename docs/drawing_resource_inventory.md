# Drawing-resource bounds before larger cel counts

This is a source audit of declared pixel storage, not a process/GPU memory guarantee.
Owned-raster admission is verified separately. The production live-cel cap remains32
while dense unique-art measurement is prepared.

| Storage | Current bound and lifecycle | Limit of the claim |
|---|---|---|
| Registered hot/cold authorities plus retained decoded cache |320MiB admission across live cels, Undo, retired sequence data and clipboard; shared immutable payloads counted once | Conservative logical accounting; external borrowed/transient Images excluded |
| Retained decoded cache | Two full-HD RGBA frames inside the320MiB bound | Caller read materialization can outlive its cache entry |
| Drawing history |64MiB charged storage and128 commands; global sequence trimming includes Undo/Redo | Policy retains one command even when its charge exceeds target; structural authorities are also bounded by ownership admission |
| Layer-opacity images | At most4RGBA images,33,177,600pixel bytes at1080p | Image/container/allocator overhead excluded; clears on document replacement/exit |
| Front overlay cache | One full-HD RGBA image,8,294,400pixel bytes | Final-render/readback temporaries are separate |
| Onion guides | Two texture references; inactive guides release textures and selected cels |16,588,800nominal baseRGBA bytes, not driver allocation; no physical VRAM assertion |
| Nested frame cache | One Image/texture entry per asset, at most4assets | CPU baseRGBA32MiB approximately; textures/mipmaps separate |
| Nested mask cache | One texture entry per immutable graph clip, at most8clips per runtime | GPU mipmaps/driver overhead excluded; graph replacement shuts down old runtime |
| Nested compositor | One viewport per runtime | GPU attachments and transient old/new runtime overlap need measurement |
| Pixel edit tiles | Before/after damage tiles, charged by actual Image byte sizes | Full-canvas pixel edit is bounded by native full-HD maxima; nonpixel metadata is not measured by a tile count |
| Raster preparation/readback | Per-file encoded bound32MiB; native decoded size at most1920×1080RGBA | Compression/decoder workspaces and worker/selection previews need process-level observation |
| Incoming Open | Separate validated candidate before live replacement | Old and incoming owner caches can coexist; each has its own320MiB bound |

Relevant sources are `cel_raster_snapshot_cache.gd`, `cel_raster_budget.gd`,
`app.gd:push_history`, `sequence_editor.gd:trim_history`, `drawing.gd:layer_image`,
`drawing_overlay_cache.gd`, `onion_editor.gd` and `sequence_runtime.gd`.
The sequence graph bounds assets/clips and requires a shared native canvas.

The remaining work is empirical dense unique-art loading, seek/edit/composition,
source-preserving persistence and old/incoming-context observation. A procedural
benchmark may exercise the storage foundation above32records without claiming the
normal application accepts or saves that many cels. Any cap expansion must then
verify the ordinary application and container boundary changes explicitly.

The400unique-raster foundation measurement is recorded in
[dense raster measurement](dense_raster_measurement.md). Before expanding ordinary
project limits, address the128member HAS boundary and the eager duplicate decode
in `lesson_store.gd:load_snapshot`, then test ordinary large-project workflows.
