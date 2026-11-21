# Opt-in SDFGI prototype

Follow-up branch `worker/indirect-lighting-20261121`, based on the published lighting
increment plus its handoff (`a5ef11b6`). This prototype is separate from the completed
editable-light qualification at `edf98f68`. Current status: 45 focused headless
checks and 52 private-desktop Forward+ graphics checks pass on Godot 4.6 stable,
Intel Arc 140V. Both Neon and Classic show actual bounced light on imported static
environment geometry and an imported skinned model. This is a tested prototype,
with the scene/history/material limits below; it is not a general GI qualification.

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
fresh packed reopening and closing during a pending settling capture. Final CPU45
passes; the first CPU attempt's six reader failures were a fixture-directory
mismatch and are retained in ignored output. Existing lighting CPU103 passed
before this follow-up's editor-copy exclusion fix; it is a separate scope.

`python tests/verify_scene_lighting.py --indirect` selects Forward+ and the existing
private-desktop launcher. It checks a static red wall's contribution to an
imported skinned white receiver, records actual images/metrics, exports four H.264
frames, and reopen via the actual HAS UI in a fresh process. Final result: 52
checks, no failures. The 32-frame rebuild capture, preview/export PNG and cold
reopen agree exactly in this static fixture, including its model receiver patch.
The bound remains 2/255 mean channel error; exactness is an observation, not a
cross-scene or cross-GPU promise. Both jobs confirmed the private desktop, no
foreground child, and closed their job/desktop. No engine errors or texture-RID
shutdown warnings occurred in this SDFGI run. Actual H.264 is 1920x1080, 24fps,
four frames; the ordinary final capture/composite/encoder path is used.
No private screenshots/models/videos/binaries belong in Git.

The stronger cold-pixel check found a real defect: deferred ID/outline copies
in `world_selection.gd` could retain Godot's default static GI mode and enter
voxelization after the lighting inventory. Before the fix, Classic differed by
2.2108/255 overall and 2.7197/255 on the receiver. Another 80 frames and a rebuild
did not fix that cached contamination. Copies now have GI disabled **before**
entering World3D. Reopening is exactly equal in both themes after that change.
The original failure and diagnostic receipts remain in ignored output; compact
metrics and source hashes are in `benchmarks/indirect_lighting_prototype_2026-11-21.json`.

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
- `world_selection.gd`: set the editor-only mesh copy's GI mode to disabled
  immediately before adding it to `copies_root`. Integrate this two-line hunk;
  do not replace the primary worker's selection module wholesale.
- No app.gd, world-runtime, model/material or encoder edits in this follow-up.

Next practical investigation: compare bounded-room VoxelGI for dynamic model
occlusion against this static-environment SDFGI option. That needs its own bake,
moving-model, cold-reopen and export evidence. Do not advertise dynamic indirect
shadows, path tracing or RTX behavior from the current receiver-only model path.

Official sources rechecked November21,2026:

- [Godot4.6 SDFGI setup, convergence and limitations](https://docs.godotengine.org/en/4.6/tutorials/3d/global_illumination/using_sdfgi.html)
- [GI mesh modes](https://docs.godotengine.org/en/4.6/classes/class_geometryinstance3d.html#enum-geometryinstance3d-gimode)
