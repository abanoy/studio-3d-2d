# Camera timeline UX candidate — 2026-11-21

SOURCE ONLY, NOT ADOPTED, NOT PARSED OR RUN. No native application, Godot, GPU, Git, encoder, or owner project was executed or changed to prepare this folder. The four tests are authored checks, not pass evidence.

The owner asked for selectable/draggable Camera keypoints; empty-lane double-click to add and existing-key double-click to remove; working Ctrl-wheel timeline zoom; and RMB+wheel to change lens zoom. This candidate keeps existing camera and timeline controls and adds these interactions.

## Camera keys

`camera_key_edits.gd` plans edits over detached dictionaries. It preserves all unedited data, including clipping distances, interpolation, unknown nested metadata, and valid legacy off-scene keys. It allows target edits at the scene end boundary, refuses occupied retime targets and invalid input, caps at the existing 241-key limit, and explains why the last camera key cannot be removed.

`camera_timeline_editor.gd` owns session selection and a drag ghost on the actual Camera ruler. Click selects/seeks. Drag commits on release using the existing `type: keys` history exactly once. Double-click captures the current temporary camera in an empty frame or removes the hit key. The 4-physical-pixel drag threshold and shared physical hit map respect viewport scaling. Esc, RMB cancellation, focus loss, independent key edits, scene ownership changes, and New discard the ghost. Source-only busy guards refuse concurrent live physics, recording, drawing, pose drags, numeric camera drafts, loading, export, or dialogs. Playback is stopped through the existing timeline behavior before a new UI press.

Classic and Neon drawing pass their own selection/error palette into the same overlay geometry. No application source rewrite is included: app.gd changes are narrow anchors only.

## Ctrl-wheel evidence and bounded fix

The actual source ALREADY has a Ctrl-wheel handler and shared navigation controller. It zooms the default 48-frame scene 48 → 24 → 12. This packet adds no second wheel handler.

A concrete source lifecycle gap exists: the main app cancels generic Timeline seek dragging on main-window focus loss, but the Timeline View previously cancelled only audio/cel gestures on Control focus exit. After a seek press in a FLOATING Timeline followed by missing release/focus loss, the View can retain `dragging=true`; the existing navigation busy guard then refuses zoom. The candidate gives the actual View one cancellation method for Control focus exit, window/application focus-loss notifications and teardown. That also discards any new Camera ghost or existing audio/cel/object gesture without committing it.

The smoke routes actual wheel events through ruler and tracks, docked/floated/redocked, with a 48-frame compact scene. It deliberately sends the real focus-loss notification after an unreleased seek to make the lifecycle regression deterministic. That controlled notification is not a claim that the owner's exact OS event ordering or exact reported cause has been reproduced. Actual Windows event execution remains required.

While a camera key is being dragged, the existing navigation busy guard now includes that gesture so zoom cannot change its frame mapping mid-drag. It uses guarded has_method checks to preserve existing lightweight navigation fixtures.

## Temporary lens gesture

`camera_lens_gesture.gd` handles pressed wheel events only while the camera owns RMB alone, or while a canvas RMB is pending in the existing selection controller. Wheel up narrows FOV; down widens it. The proportional 3° step is bounded 15–120°, matching the existing visible editor FOV range. Existing legacy FOV outside that range refuses with a reason instead of jumping. Invalid wheel factors refuse.

A pending RMB is upgraded to existing camera capture using its ORIGINAL cursor origin, preventing a context pick on release. Camera position and orientation stay unchanged. The usual release restores the pointer. Left/middle/two-button motion, Ctrl slow fly, ordinary camera motion, and Ctrl-wheel orbit dolly keep their original paths. The common helper is called from the global capture route and the canvas route; consuming the global event prevents a double application.

It is a temporary camera view change: no automatic key, Undo entry, dirty revision, or saved-document update. Ordinary Save camera key already captures FOV, near and far, then saves through existing HAS serialization. The existing camera help gains a short RMB+wheel line.

## Integration map

| File / helper | Narrow integration |
| --- | --- |
| camera_key_edits.gd | Pure validation, retime, toggle, exact content digest |
| camera_timeline_editor.gd | App child set up after existing TimelineNavigation; attaches to ruler |
| timeline_view.gd | Own-viewport global gesture route, mouse GUI delegation, cancellation, two palette-specific overlays |
| timeline_navigation.gd | Existing busy guard additionally recognizes an active Camera drag |
| camera_lens_gesture.gd | Same static handler at app._input and canvas_input; no state or parallel navigation controller |
| app.gd | One field, one controller setup, two lens calls, one camera-help line; none overlap the face agent's Settings anchors |

PATCHES.json has 13 ordered exact replacements. Every before anchor occurs exactly once on the preserved baseline and remains unique after preceding replacements. Owned full timeline_view.gd and timeline_navigation.gd payloads equal applying those replacements; app.gd has ONLY anchors, not a whole-file payload. BASES.json pins original inputs, with original copies retained under bases/. The source baseline revision is e0879c7df74bc3704902bfdaf4ff74eee40c3aea; Root's later eight-file 59a112a adoption does not change these app/ruler/navigation inputs. Use immutable Git source plus explicit candidate and report the later current-source preservation separately; do not claim an old full-checkout identity.

## Authored qualification plan — ALL UNRUN

| Test | Authored checks | Scope |
| --- | ---: | --- |
| camera_key_edits_unit.gd |26| Pure exact planning, nested preservation, legacy frames, limits/refusals |
| camera_lens_gesture_unit.gd |12| Pure FOV direction, fractional factors, bounds and invalid values |
| camera_timeline_ux_smoke.gd |34| Actual app/view events, real Undo/Redo, ghost/cancel/stale ownership, compact/floating Ctrl-wheel |
| camera_lens_gesture_smoke.gd |22| Actual app navigation/capture APIs plus routed wheel event, orbit priority, original cursor return, explicit key/save/reopen |

Both application tests accept --classic (otherwise Neon), --150 (otherwise 100%), and --advanced (otherwise Simple). Their ConfigFile is in the caller's disposable output directory. The owner-facing app and existing preferences are untouched. The timeline regression deliberately uses the compact default 48-frame scene; no fixture conversion or supplied native artwork is needed.

Run the 38 pure checks first in the approved hidden/headless qualification host. Then qualify 56 app assertions per style/scale run with the approved private Windows desktop and isolation receipts. Ensure both Simple and Advanced can still reach existing controls (the new gestures work independently of inspector visibility). Existing `timeline_navigation`, `orbit_navigation`, `camera_transform`, `camera_range`, workspace, animated-channel and `verify.py` regressions remain required for adoption. Capture/save/reopen exactness, no leaked instances/script errors, and real GPU/encoder agreement are not proved by authoring source.

Current qualification booleans: parsed=false; pure_execution=false; app_execution=false; native_asset_qualification=false; actual_owner_repro=false; adoption=false. Peer source/API review is separate from execution. Parent performs all runtime and final Git/repository publication. Frozen hair, Miku, Junko bundle and easing packets were not modified; they remain separate work with their own evidence and limitations.

Independent source/API peers: cold_import_fix reviewed pure key/lens code against actual APIs; face_gizmo reviewed the Timeline controller and all 13 integration anchors. Both found no concrete blocker; neither executed these tests. See SOURCE_REVIEW.json. Frozen originals under bases/ remain part of this source handoff.
