# Bounded-room VoxelGI

Branch `worker/voxel-room-20261121`, based on qualified SDFGI tip `634f854d`.
This adds one optional room probe; existing direct lights, SDFGI, imported lights
and imported probes remain available. No RTX hardware or path tracing is used.

## Use

Launch `python run.py --forward-plus`. Import a static environment and a model,
choose **Lit**, open **Lights → Environment bounce**, select **Bounded room —
VoxelGI**, enable it and use **Fit scene / near view**. Review the center and room
dimensions, then **Apply indirect light**. Start with 64 subdivisions. The room
must contain environment geometry; an empty room reports an actionable error and
cannot silently export an unbaked GI frame. Strength changes do not require baking.

Bounds are axis-aligned, 1–128 scene units per axis. Small scenes fit their bounds;
very large maps use a 12×8×12 room near the view instead of an enormous map volume.
128 subdivisions is available for more detail at greater cost; pixels were tested
at 64 subdivisions. This is one authored probe, not automatic room partitioning.

Static environments supply the baked geometry. Models use Godot's dynamic GI mode
and can affect indirect illumination as they move. **Rebuild from current
environment** rebakes after static geometry changes. Baking runs synchronously
after the imported nodes/materials are ready and can pause Studio for seconds on
larger scenes. The status reports the bake result. Thin walls, transparency,
custom shaders and small geometry can still leak or lose detail.

## Save, preview and export

The project saves the room's editable recipe with the ordinary lighting/video
history. Undo hides its probe and restores prior live mesh GI modes; Redo restores
it. Native HAS saving includes the original scene/model assets. **Baked binary data
is regenerated in memory on reopening**, not embedded in the project, copied into
the imported GLB, or dependent on a machine-local cache. Reopening therefore has a
bake cost. This avoids adding a second binary asset/persistence format.

Scene setup uses Studio's live overscan viewport; Camera focus uses its native
output-shaped viewport. Both receive the authored probe. Offline capture uses the
same room data and dynamic model poses, holds the exact authored frame for the
explicit settling budget, and rejects a missing/failed/pending bake. The fixture
uses 32 warmup draws per captured frame. This is extra render work, not path-tracing
samples, and it does not change the project's FPS or timeline frame addresses.

## Actual checks

`python -B tests/verify_scene_lighting.py --voxel --cpu` passes **34 checks**.
It covers validation, an empty-room error, deferred baking, one history
transaction, exact hidden room-bound precision during a strength-only edit,
Undo/Redo, preservation of world/animation/material data, ordinary saving and
fresh packed reopening with a newly generated bake. SDFGI CPU45 also passes on
the same production source. These headless checks do not establish GPU pixels.

`python -B tests/verify_scene_lighting.py --voxel` passes **60 checks** using the
existing Windows private-desktop launcher, Godot 4.6 stable and Intel Arc 140V.
Neon and Classic both pass. The original fixture imports a room and a skinned
black blocker with four authored root-animation frames. A spotlight illuminates
the red wall; the measured floor patch is black with GI off, and direct shadows
are disabled. Its average red channel with VoxelGI is **22.3828 → 18.8672 →
22.3828** as the model moves into the bounce path and away (about 15.7% reduction).
This demonstrates moving-model indirect occlusion, separately from direct shadows.
It is soft, coarse voxel occlusion, not a physically exact contact shadow.

The actual Scene setup viewport independently shows occlusion and recovery.
Camera-focus live preview, final capture, fresh-process packed reopening/rebaking
and movie-source PNGs agree **exactly** at frames 0, 1 and 3, including the 16×16
floor patch. The asserted mean-channel bound is 2/255; exactness is a fixture
observation, not a general promise. Actual H.264 output is 1920×1080, 24fps,
four frames. Both final jobs confirm private desktops, no foreground child and
closed jobs/desktops; no engine errors occurred. Screenshots, video, generated
GLBs and bake resources stay outside Git.

Earlier evidence is preserved: the first CPU attempt found an untyped test Image
variable; a stronger preview check then caught the test reading the inactive
export viewport while Scene setup was active. The test now exercises the actual
Scene setup view and switches to Camera focus for native pixel comparisons.
No tolerance was loosened and no application viewport behavior was changed.

## Limits and integration

Forward+ only. Compatibility retains the saved recipe but uses its direct-light
path; turn indirect lighting off or relaunch with Forward+. Only one small room,
one GPU, 64 subdivisions, supported lit materials and skinned **root movement**
were graphically verified. Arbitrary native shader fidelity, bone-deformation
occlusion, large maps, nested sequences, multiple overlapping probes, fast camera
cuts and performance scaling are not qualified by this fixture. Static custom
ShaderMaterials bake as blockers without their shader colors; some UV mappings,
transparent/cutout surfaces and thin walls are limited by Godot. Original materials
are retained. Two-bounce mode is off; no ray-traced reflection claim is made.

Integrate after the SDFGI increment:

- Add `src/scene_voxel_runtime.gd` (one probe, deferred in-memory bake and status).
- Add optional `indirect.method` and `indirect.voxel` document validation.
- Delegate the VoxelGI branch from `scene_indirect_runtime.gd`; retain its exact
  mesh-flag restoration and existing SDFGI branch.
- Extend the existing collapsed lighting section with method/bounds/quality/fit
  controls. Keep the primary worker's `load_number`/`typed` exact-value snapshots
  and Compatibility reflection-Off fix; this branch adopts both and applies the
  numeric helper to the new room fields. Do not overwrite the primary editor.
- Renderer: three lines after settling to return an actionable bake error.
- No app.gd, world-runtime, model/material, storage or encoder edits.

Official Godot 4.6 references checked November 21, 2026:
[VoxelGI setup and limitations](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_voxel_gi.html),
[runtime bake API](https://docs.godotengine.org/en/4.6/classes/class_voxelgi.html),
[bake data properties](https://docs.godotengine.org/en/4.6/classes/class_voxelgidata.html).


## Primary integration checkpoint

The primary retains the worker60 graphics result as separate branch evidence.
Its own final headless checks pass42 Voxel (including eight native early-return
rebake failure/recovery controls),45 SDFGI and103 direct lighting. Old probe data
is cleared before native bake admission. Primary graphics remain pending after
the frozen published5d full Windows run. A separately reported empty-contributor
preview path is still open in this checkpoint; see the preserved evidence packet
experiments/voxel_integration_20261121. This is work in progress, not a new primary
GPU or complete-suite pass.
