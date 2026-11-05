# Independent drawing Undo

Undo and Redo for brush/fill pixels, cel creation/deletion/exposure, and drawing
layer properties/order/addition/removal refresh the drawing overlay and timeline.
They preserve the current frame, authored world, camera keys, editor view and
live 3D simulation. The same applies to project palette metadata.

Previously, these commands used the generic world-history refresh: the pixels
were restored correctly, but it cleared a running ragdoll and reevaluated the
3D scene. Drawing commands now use the ordinary dirty-overlay refresh without
world reconstruction. Exposure and layer controls still refresh immediately;
onion guides and composite caches follow the existing drawing refresh path.
No save schema, common model format or input controls change.

This does not change world/model/camera/audio/video Undo behavior. Undo during
active physics recording still cancels that recording first. Seeking, playback,
physics preview freezing and exporting retain their existing policies.

`python tests/verify_drawing_history.py` runs the actual app privately with an
original standard-model ragdoll, animated camera and independent drawing. The
36 editor checks exercise pixel/cel/exposure/layer Undo and Redo, body transforms
within the input event, simulation identity and generation, later UI frames,
exact overlay, packed HAS and ordinary H264 export. Three fresh-open checks
verify drawing/world/camera/render preservation and the untouched manual save.
The `--baseline` test option reproduces the original simulation-stopping defect
only on the old source; its successful reproduction is not a fixed-version pass.

The persistence/movie portion deliberately stops simulation and restores the
authored world first for deterministic image comparison. It proves drawing and
camera export, not live physics baking or universal ragdoll behavior. Existing
physics-recording tests cover that separate workflow. Physical input and artist
acceptance remain separate from the automated private-desktop checks.
