# Size a static map from a known distance

Select the map in the World tree, position the working camera near a doorway or
other known span, then choose **Size map…**. A separate map view opens. Click the
first and second solid surfaces, enter their known distance in metres, and use
**Preview size** to compare the proposed map against the cyan six-foot person.
Turn Preview off to measure again. **Apply map size** commits one Undo operation;
Cancel leaves the world unchanged. Right drag looks, middle drag pans, the wheel
moves closer/farther, and Frame map finds the whole environment in this view.

The doorway (80 inches / 2.032 m) and ceiling (8 feet / 2.4384 m) entries are
editable examples. They are not universal building standards. The six-foot entry
is exactly 1.8288 m. Choose the distance appropriate to this particular map. The
tool never infers a building's dimensions from its overall bounds or from a model
name. Existing source unit conversion remains separate.

Yellow marks the measured span; cyan is an editor-only six-foot reference person,
always shown upright at the first point. Preview scales only a disposable standard
Model/Renderer. It does not change the real world, working camera, shot keys,
independent drawing, peers or history. Applying uniformly scales the selected map
about the first point so the chosen base stays fixed, preserving root rotation.
It creates no animation keys. Preview markings never enter the document or MP4.

## Supported scope and safety

This increment handles visible, static, unattached environment roots with no
attached instances, authored keys, animation blocks or draft bone pose. Freeze
Physics and Hair & clothes first. Other models remain unchanged; the tool does
not reposition characters or rewrite their existing foot pins when the floor moves.
Existing animated/attached maps require a later range/contact-aware workflow.
Skinned maps refuse instead of measuring undeformed triangles as if they were
final surfaces. Character proportions use the separate optional height review.

Picking uses the nearest exact triangle hit between the copied camera's near/far
planes, including indexed/unindexed transformed static mesh positions. The whole
query refuses above 200,000 triangles; there is no bounds/proxy or partially
sampled fallback. Texture alpha, shader displacement and visual transparency do
not change the picking surface; choose a solid edge. GLB import, triangle collection
and each pick are synchronous, so large maps may pause. Artist latency/comfort and
arbitrary native asset fidelity are not certified by these tests.

Changing selection, frame, world, document revision, playback/export/live Physics
or Home invalidates the review. Generation guards prevent stale deferred work.
Apply checks source SHA and full world/metadata validity before installation.
Unsupported or stale work is refused without replacing scene data. App teardown
releases the private preview and its world. Original source files stay intact.

`metadata.map_reference` (`studio_map_reference_1`) stores original size/position,
source identity, both marked points, measured/target distance as exact decimal
text, and float32 scale bits. It records the choice; it is not a command to resize
again on Open. Scale/position remain ordinary standard model fields. No model,
world or HAS version change, native pose fork, external-format exporter or game
execution is introduced.

## Verification

`python tests/verify_map_calibration.py` runs private GPU writer and cold-reader
checks. It exercises real preview pointer signals, nearest surface geometry,
rotated/scaled roots, anchor preservation, reversible preview, unchanged live
render, one Undo/Redo, cancellation/stale selection/frame/New, deferred reopen and
teardown, packed/linked provenance/engine scale, editable drawing and ordinary
1080p24 two-second H264 MP4 with exact frame comparison. A real prepared
`gm_construct` map has 109,583 triangles and accepts actual surface picks/fitting
through the same standard path. The native source SHA/mtime are checked.

Current accepted counts and affected regression scope are recorded in the
append-only progress memo/checkpoint. Full verifier integration is wiring, not
evidence of a fresh whole-suite pass. Normal installed Model7 and the frozen web
preview remain unchanged. Future work includes animated/attached maps, contact
reanchoring, persistent per-map reset and broader asset/first-use acceptance.

Final current-source run passes 36 editor/native checks plus three cold-reader
checks. Affected world workflow24, placement21, HAS13 container+32 editor and UI23
also pass:152 scoped checks total, zero failures, six accepted private GPU receipts.
Source map distance uses a 0.0001-unit bound at its native coordinates; the authored
and rotated-anchor checks use 0.00002. Screenshots were inspected after removing
the disposable renderer's unrelated empty-world grid and copying project background.
The earlier 28/32/39-check development runs also passed and remain separate evidence.

The camera projection and triangle query use the pinned engine's documented APIs:
[Camera3D](https://docs.godotengine.org/en/4.6/classes/class_camera3d.html) and
[Geometry3D](https://docs.godotengine.org/en/4.6/classes/class_geometry3d.html).
