# Source map read after UI/camera adoption

- src/pose_bounds.gd:33 palette; :58 conservative; :65 mesh_bounds; :105 query. Existing bounded framing evaluator; reads current source shapes and optionally final body-modifier poses.
- src/source_shape.gd:143 and :226 publish morph custom_aabb; :233 mesh_bounds returns current morph bounds or mesh.get_aabb. Preserve this input/output ownership distinction.
- src/model.gd:189 inventory runs before child actor attachment; :474 apply converges shape/root/bone updates, ending in forced skeleton transforms. Shared proposed transient refresh boundary.
- src/world_runtime.gd:92 evaluate applies each actor in topological order. Parent and child actors must keep independent mesh ownership.
- src/renderer.gd:163 evaluate and :311 capture share actor evaluation; final capture uses the authored final evaluation and can repeat a frame.
- src/physics_rig.gd:279 capture publishes final modifier global poses at :287. A refresh only in Model.apply would miss this later body state.
- src/secondary_live.gd advance uses apply_current for authored baseline and final live-hair pose; capture_pose/stop/dispose preserve the ordinary recording/freeze contract.
- tests/pose_bounds_smoke.gd independent engine bake already checks current morph+skin geometry, transformed parents, named skins, 8 influences, conservative fallback, live body/hair framing, final output parity, and reopen. Extend meaningful culling coverage without replacing those assertions.

Exact bytes/hash for these eight sources are in BASE_SOURCE_PINS.json. They are review context, not payload replacements or a new Full verification claim.
