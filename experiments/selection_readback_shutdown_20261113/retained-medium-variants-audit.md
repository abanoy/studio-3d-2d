# Drawing selection shutdown: retained Variant audit and focused regression design

Read-only source audit, 2026-11-13. Baseline source references are HEAD `2904f3f`, before the parent's pending-pick repair. No main/prototype source changes or application runs were performed for this audit. This document proposes checks; it is not a passing test report.

## Established evidence

The original writer and unchanged replay both print `DRAWING_SELECTION_SMOKE` with 35 checks / 0 failures, then fail at native shutdown. These bodies are not successful verification runs:

- `output/drawing-selection/1794546848161578700/writer.log` and the preserved child 11444 dump.
- `output/drawing-selection/1794547328073692300/writer.log` (unchanged replay).
- `output/drawing-selection-crash-20261113/verbose-1794547680031445800/process.log`: immediately before free, `picking == 1`, exactly one RenderingServer `frame_post_draw` connection whose callable is `GDScriptFunctionState::_signal_callback` (flags 4), zero native readbacks/callbacks, no selection/transform reveal connection, no active physics, no selection preview, project pid -1 and zero orphan Nodes. After application free, verbose shutdown reports one unclaimed `frame_post_draw` StringName.
- Parent's exact-binary dump research identifies one outstanding `Variant::Pools::BucketMedium` allocation. Its Basis/Transform3D narrowing and static-destructor/error-mutex route are documented in `output/godot-shutdown-symbol-research-20261113/README.md`. This does not independently identify a driver fault.

## Matching source lifetime

`src/world_selection.gd:275–284` is the concrete match:

1. `choose_at` increments `picking` at 278.
2. At 280, the coroutine retains `view = app.scene_view.pick_state()`.
3. `src/scene_view.gd:97` puts exactly one Transform3D (`source.global_transform`) in that Array; its other members are numeric values, flags and Vector2 values.
4. At 282, `choose_at` directly awaits the singleton `RenderingServer.frame_post_draw` signal.
5. `picking` is decremented only after resumption, at 283. Serial/view/mode invalidation is also checked only after resumption, at 284. `cancel_gesture(true)` changes serial but does not unwind this await.

Thus the observed pending counter, callable type, orphan signal name and one medium Variant all agree with this pending pick continuation. `tests/drawing_selection_smoke.gd:73–74` ends with New followed immediately by application free and quit, without allowing the next draw. The diagnostic establishes the pending request at that boundary; this audit does not establish which earlier routed event originally launched it.

The existing native-readback repair is separate and remains applicable. `src/renderer.gd:268–294` disconnects its Node-owned draw callback, completes waiting scopes on exit, and retains a local RefCounted notification owner during emission. The diagnostic's zero native scopes/callbacks distinguishes that path from the pending selection coroutine. Do not remove its existing 58-case coverage.

## Other medium-bearing ownership inspected

| Owner | Exact retention / release | Relevance |
| --- | --- | --- |
| Selection writer local `view` (`tests/drawing_selection_smoke.gd:29`) | `renderer.view_state()` contains one camera Transform3D (`src/renderer.gd:259–260`); retained until the test coroutine unwinds. | Legitimate local lifetime. A leaked entire test coroutine would also retain the model below, so it is a poorer match for exactly one allocation. |
| Selection writer local `simulation` (`:29`) | PhysicsRig holds `rig` (`src/physics_rig.gd:8,189`). Dispose clears latest/bodies/simulator and live pose, but does not clear that owning rig reference (`:294–300`). Model contains `base_root` (`src/model.gd:12`) and each `bones[id].base` (`:167–172`). | Legitimate lifetime after physics clear at test:47 until the local is released. No reverse strong reference/cycle found on this fixture path. |
| Live physics skeleton metadata | `src/physics_rig.gd:245–250` stores an Array of Transform3D poses; owner is a WeakRef. `PoseBounds.clear_final` removes the metadata (`src/pose_bounds.gd:16–23`), called during Rig.dispose. | This path is explicitly cleared at test:47. Final diagnostic confirms zero live physics. |
| Old installed world | Model base/bone transforms are owned by its runtime. `renderer.clear_assets` disposes the runtime (`src/renderer.gd:125–132`); `WorldRuntime.dispose` frees root and clears instances (`src/world_runtime.gd:143–147`). | A remaining test-local simulation can independently retain its model, as above; no static world cache found. |
| Pose thumbnail / spring initialization | Other direct draw-await paths are `src/pose_thumbnail.gd:31`, `src/secondary_spring.gd:77`, and sequence compositor `src/sequence_runtime.gd:139`. | This writer does not open a pose thumbnail, initialize secondary motion, or install a sequence. The independently observed pending pick is the closer match. |

Passed `tests/drawing_history_smoke.gd` is an important control: it keeps simulation as a SceneTree member (`:11,43`), a saved view Transform3D (`:44`) and an Array/Dictionary of physical transforms (`:47–48`), then clears physics at 76 and frees the application after movie export at 81. Mere retention of a disposed physics/model object or saved view therefore does not explain the selection failure by itself.

Selection algorithms, selection/transform editor preview data, drawing raster ownership and snapshot caches contain no explicit Basis/Transform3D. The inspected `src` static variables contain JSON strings/numbers, byte lookup arrays, derived Images/WeakRefs, or textures: BoneLabels.lexicon, CharacterHeight.queries, Drawing.opacity_cache/counters, Recovery discovery/owner-record cache, SequencePixels.lookup, ShapeLabels.names and StudioTheme.icons. No static transform cache or strong self-cycle was found there. This is a source ownership audit, not a heap proof that those engine Resources cannot contain native data.

## Minimal focused regression design (not implemented)

Preserve all current assertions and body/movie/readback limits. The test must check real process teardown, not turn the 35/0 marker into success by adding an arbitrary settle to the old footer.

### 1. Real picking positive control

Reuse the deterministic pose fixture and independently known projected model point from `tests/world_selection_smoke.gd:44–55` (`SceneIO.make_pose_fixture`, model key from World support, native camera projection of the fixture geometry). Disable Setup only through the existing view API for this fixture.

- Begin with no selection and a fully settled real renderer, zero native readbacks, and record the actual global draw-connection count.
- Call the real `world_selection.choose_at(point)` with an in-bounds point. Before yielding, require `picking == 1` and one newly pending draw connection. This proves the teardown cases really reach the asynchronous boundary.
- After the real draw, require the expected independently known model ID, `picking == 0`, and baseline connection count. Also require exact camera transform, authored keys and portable world data preservation.
- Keep existing viewport-click, skinned mask, outline, final-image, Escape, material and source-hash tests in `world_selection_smoke`; do not replace them with this direct-call probe.

### 2. Pending-pick teardown matrix

Use fresh owned application instances, their own recovery/display/recent paths, the same real fixture/point, and both Focus and Setup view. After a positive-control instance has proved real picking works, run `free`, `queue_free`, and `remove_from_tree` closures (six bounded cases, matching existing native readback lifecycle conventions).

- Settle first and record actual Nodes/orphans and draw-connection baseline. Begin a real pick, assert it is pending, then close/detach **before any process/draw await**.
- For immediate free, assert receiver/viewports/camera WeakRefs are released. For queued free, assert after the queue has run. For detachment, keep the receiver alive long enough to verify pending work is canceled, then explicitly free it.
- Allow subsequent process/draw boundaries only **after** the immediate close/detach operation. Require no extra global draw connection and no retained/orphan Nodes relative to the baseline; require no selection notification/action from the discarded request. A surviving detached receiver must have no pending pick.
- Do not hold strong test references to Model/PhysicsRig solely for liveness checks; use WeakRefs and numeric IDs. Avoid keeping a test-generated Transform3D in a never-completed diagnostic coroutine.
- Exact callback names or the new pending-record structure are not the oracle. Public outcomes, actual signal connection ownership, WeakRefs and engine exit are the oracle.

### 3. New/document replacement stale-request control

Begin a genuine pending pick on a populated world. Call the normal `new_project()` before its next draw. Require the new empty world and no selection, then allow a draw and require that the old request does not select an obsolete ID or change the new camera/keys/history/dirty state. Retain the existing Escape invalidation check at `tests/world_selection_smoke.gd:132–137` and add view-change cancellation only if that existing guard lacks a focused assertion.

Also include the specific shutdown boundary: on a fresh empty New world, start one in-bounds real pick, assert pending, then immediately free Studio and quit. Empty geometry is intentional here: this proves lifecycle cleanup without relying on successful hit selection. The separate positive control above prevents a disabled picker from passing the suite.

### 4. Previously failing complete writer

Re-run the **unchanged** `tests/drawing_selection_smoke.gd` writer and its normal cold reader/movie wrapper on the candidate frozen source. Require its original 35/0 writer and all original cold-read/movie assertions, plus clean child exit and receipt. Preserve the failed logs/dump and an old-source focused pending-pick comparison so failure sensitivity is demonstrated rather than inferred. Do not mutate the original failed artifact or relax native-exit checks.

## Required wrapper evidence

- Parse/normal-startup checks before private GPU work; all application work remains serial under the parent's GPU lease.
- Frozen functional file hashes before/after; the exact shared regression test hash; source revision/overlay receipt. If a lifecycle wrapper is reused, its allowed runtime overlay must explicitly include `src/world_selection.gd` rather than silently dropping that file.
- Per-case results and a completion marker; process and receipt exit 0; confirmed private desktop; no foreground child; closed job/desktop.
- Reject `ERROR:`, `FAIL`, ObjectDB/FunctionState leaks, unclaimed/orphan StringNames and allocator leak reporting. A 35/0 body followed by exit 1 or 0xC0000005 remains failed.
- Keep the existing 58-case renderer/close suite and world-selection native/final-frame suite; they protect separate behavior. This design does not claim they have been rerun or that the repair has passed.

No repair is prescribed by the earlier static-cache audit. The parent independently selected a pending-pick callback repair after the live pending-pick diagnostic; this document only defines the evidence needed to verify it.
