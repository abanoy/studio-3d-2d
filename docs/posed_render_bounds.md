# Automatic bounds for posed models

HAS updates the render bounds of supported skinned models automatically. This
keeps a moved or posed part, such as a face, visible when it extends beyond the
mesh's original bounds. There is no new switch to enable. The update follows
ordinary model loading, pose and expression edits, live poses and the final
transforms published by body physics. Selection and outline copies use the same
per-instance margin.

The cache changes only the instance's extra culling margin. SourceShape keeps
ownership of facial-shape geometry, `custom_aabb` and morph-bound metadata.
Original assets, shared mesh/skin resources, authored poses, camera keys and Undo
history are untouched. Leaving the scene releases the cache and restores its
still-owned margin. External margin changes remain under their existing owner.
Duplicated thumbnail teardown cannot release the original model's cache.

An admitted inventory reads weighted vertices once, within limits of 256 meshes,
200000 vertices and 512 binds per skin. Later refreshes use cached weight information
and current pose matrices; they do not rescan vertex arrays. Static unskinned
maps are excluded. Changed source/binding ownership or an unsupported profile
stops this optional cache and retains baseline rendering, with a transient
diagnostic available through `Model.render_bounds_diagnostics()`.

## Verified feature-build coverage, 2026-11-21

- 17 Model/Skeleton checks cover shared meshes, authored/live/final poses,
  physics publication/release, warm-cache behavior, detach/reattach, thumbnail
  duplication, external margin ownership and cleanup.
- 20 ordinary-app headless checks cover Add model, pose commit, Undo/Redo,
  expressions, source preservation, packed saving and New.
- 20 graphical writer/reader checks pass in Neon Simple and again in Classic
  Advanced: actual deformation, expression bounds, rendered pixels, ID picking,
  packed saving and separate-process reopening. These use generated geometry.
- 13 ordinary-Open checks use the protected saved Youmu scene through the normal
  application, with no explicit bounds helper or margin edits in the test. Four
  private1920×1080 captures cover the saved view and a whole-body view at frames0
  and43. Independent visual inspection confirms the face, hair, arms, torso and
  clothing remain visible; the whole-body views also retain both legs and shoes.
  Source hashes, authored world, shot keys, Undo count and balanced readbacks
  remain intact.

The reusable Windows wrapper is `tests/verify_posed_bounds_owner.py --project
<protected-stuff.has>`. Its isolated-settings repeat passed the same 13 checks;
all four PNGs were byte-identical to the separately inspected captures. This is
a repeat of the same native scope, not 13 additional independent controls.

That saved scene admitted9 weighted meshes and27453 vertices with20 initial
surface-array reads and one cache construction. Both recorded contexts reported
zero hot vertex-array reads. These counters are not a frame-rate benchmark.
The earlier explicit head-only diagnostic remains separate evidence; it did not
validate whole-model display.

This is coverage of the current feature build, not a new whole-suite or release
qualification. Nonuniform mesh/ancestor scale behavior, shader displacement,
arbitrary native rigs and original-renderer equivalence remain outside this
specific visual check. The protected scene's culling fix does not establish a
fix for Summer Sakuya's separate extreme expression-value report. Native assets
and captures remain private. See `tests/posed_bounds_integration_unit.gd`,
`tests/posed_bounds_app_headless.gd`, `tests/posed_bounds_app_gui.gd` and
`tests/posed_bounds_owner_open.gd` for the focused routes.
