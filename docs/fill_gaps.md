# Gap-aware fill

Draw → Fill offers **Close gaps (pixels)** in Simple and Advanced. Default0
keeps ordinary fill with the chosen [connection rule](fill_connections.md)
(edges only by default). Values1–8 use temporary boundaries to seal
small breaks in sampled line art. Every changed nonzero-gap result requires **Apply fill**
or **Cancel**, even if small and fully enclosed. It never applies automatically.
Original ink remains unchanged; only the selected drawing layer receives color.

For separate line art, use **Color layer below** and keep **Sample visible
drawings** on. Invisible layers and the3D environment are not sampled. A virtual
closure is not a new painted line: with zero growth its pixels remain unfilled. This does not repair
the source drawing or infer artistic intent. The separate Advanced
[Grow under lines](fill_expand.md) can extend color beneath anti-aliased edges;
zero growth keeps virtual closures unpainted.
Intentional narrow corridors/details can also close. Review the candidate; reduce
the amount or use0 when an opening should remain. If filtering removes the clicked
narrow region itself, the fill refuses with guidance rather than choosing another
region. Threshold behavior depends on orientation and surrounding geometry; tests
cover straight gaps1–8, not a guarantee for arbitrary hand-drawn shapes.

The worker first classifies pixels against the seed using the existing tolerance
and premultiplied RGBA comparison. Binary opening of passable pixels gives the
complement of virtual barrier closing. A square kernel of width gap+1 uses two
rolling-count erosion passes and two reflected dilation passes. Odd-gap anchors
are reflected to avoid shifting the drawing. Neutral boundary padding and a final
intersection preserve original barriers and avoid inventing an empty-canvas border.
Scanline fill then traverses the filtered mask. Work/storage are linear in the
bounded1920×1080canvas; temporary byte masks add several MiB, not full RGBA layers.
No OpenCV runtime or additional dependency is installed.

All computation uses detached byte arrays on the existing low-priority worker.
The UI keeps running while it works. Full-HD processing takes seconds on this
machine; it is not a Krita-speed or universal-latency claim. Cancel invalidates
results immediately but does not interrupt CPU work already running. Teardown
can still wait for that bounded worker, as with the original fill implementation.
Settings and the document/frame/layer identity are captured: changing gap,
tolerance, color or sampling rejects stale work, including an immediate Apply
before the next UI frame. Gap is a session tool setting, not scene metadata.

The result remains ordinary independent RGBA cel pixels with one existing
cel/tile Undo action. Packed/linked HAS, recovery, preview and MP4 share the same
stored pixels. There is no project schema or standard-model change. Source
asset paths, original line art, model rigs and camera keys are unaffected.

`tests/verify_fill_gaps.py` checks an independent nonseparable square-neighborhood
oracle against32masks, exact gap thresholds, source/target isolation, a removed
seed, invalid input and full-HD traversal. Its private actual-app workflow covers
zoomed fill input, spill/closed previews, real Apply/Cancel clicks at1200pixels,
new-cel/tile Undo/Redo, stale settings, worker UI frames, packed/cold/linked/recovery,
ordinary movie pixel agreement and New while work is live. See the dated progress
memo and verification report for actual completed results and timings.

Primary mathematical reference: [OpenCV morphology tutorial](https://docs.opencv.org/4.13.0/d9/d61/tutorial_py_morphological_ops.html).
The implementation is bounded native GDScript; the independent oracle uses full
two-dimensional neighborhoods rather than the production separable rolling sums.
Previewed [under-line expansion](fill_expand.md) is separate from gap closure;
refined anti-alias filling and more general artistic cleanup
remain unfinished.
