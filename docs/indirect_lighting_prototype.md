# Opt-in SDFGI prototype

Follow-up branch `worker/indirect-lighting-20261121`, based on the published lighting
increment plus its handoff (`a5ef11b6`). This prototype is separate from the completed
editable-light qualification at `edf98f68`. Current status: runnable controls and
41 focused headless checks pass; actual bounced-light pixels/convergence/movie
checks are authored but have not run. Do not infer graphics support from CPU checks.

## Use and behavior

Launch `python run.py --forward-plus`, import an environment and model, open
Lights, choose Lit and expand **Environment bounce (SDFGI prototype, Forward+)**.
Enable, set strength/cell size/render settling frames, then Apply. It is off by
default and has the existing video-history Undo/Redo and native project persistence.

Only imported environment meshes become static GI contributors. Model meshes
receive indirect light but do not contribute dynamic occlusion/emission. Editor
geometry is excluded. The controller owns temporary live-instance GI flags and
restores their exact prior values on disable/Undo/Unshaded; it does not change
mesh/material resources, original assets or saved model/world records.

**Rebuild from current environment** disables SDFGI for a rendered frame, then
re-enables it from the current geometry. Rebuild after moving environment geometry.
Imported lights retain their existing bake modes; disabled/static GI-light modes
retain Godot's limitations. Authored lights use their normal dynamic bake mode.

Export holds the exact evaluated timeline frame for the explicit 8–120-frame
settling budget (default32), then performs the normal readback/composite. This
spends render time without changing project FPS or frame addresses. Preview also
converges over rendered frames. More settling frames do not guarantee convergence
after a large camera cut or a geometry change. No exact pixel identity is promised
for this history-dependent GI method; its new pixel comparison records an explicit
2/255 mean-channel bound. Ordinary lighting with GI off retains its original path.

## Focused checks and current limits

`python tests/verify_scene_lighting.py --indirect --cpu` runs actual transactions,
contributor/receiver flags, exact restoration, ordinary directory persistence,
fresh packed reopening and closing during a pending settling capture. Final CPU41
passes; the first CPU attempt's six reader failures were a fixture-directory
mismatch and are retained in ignored output. Existing lighting CPU103 also passes.

`python tests/verify_scene_lighting.py --indirect` selects Forward+ and the existing
private-desktop launcher. It will check a static red wall's contribution to an
imported skinned white receiver, record actual images/metrics, export four H.264
frames, and reopen via the actual HAS UI in a fresh process. It has not run yet.
No private screenshots/models/videos/binaries belong in Git.

This is Godot's semi-real-time signed-distance-field GI, not path tracing. Dynamic
models do not occlude bounced light, transparent/cutout materials and thin walls
can leak, and camera cascades/history can shift. Lit unlit/custom material warnings
remain actionable. SDFGI is expensive and only enabled on Forward+; no new runtime,
installation or renderer-default change is introduced.

## Integration delta after the completed lighting increment

- Add `src/scene_indirect_runtime.gd`; it owns temporary flags, reset and SDFGI setup.
- Lighting document validates optional `indirect` settings; lighting runtime delegates.
- Lighting panel adds one collapsed prototype section with Apply/Rebuild.
- Renderer passes itself to lighting setup and adds an explicit bounded warmup loop
  before readback. The existing owner-bound native-frame signal/cancellation path
  remains authoritative; the close-during-settling CPU test exercises it.
- No app.gd, world-runtime, model/material or encoder edits in this follow-up.

Official sources rechecked November21,2026:

- [Godot4.6 SDFGI setup, convergence and limitations](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_sdfgi.html)
- [GI mesh modes](https://docs.godotengine.org/en/4.6/classes/class_geometryinstance3d.html#enum-geometryinstance3d-gimode)
