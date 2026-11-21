# Face window and pose-handle usability candidate

Status: SOURCE AUTHORED; UNPARSED, UNRUN, UNADOPTED. No current application, installed review, owner project or shared tool was changed. Root owns every runtime/GPU/native test and adoption decision.

## Scope and source map

The owner reported a narrow, non-adjustable Shapes window with a short list and large unused region, and rotation rings too small to grab on a3440×1440 screen. These are two independently applicable scopes in PATCHES.json. Both start from the same exact e087 pose_editor.gd baseline; variants/face_pose_editor.gd and variants/handle_pose_editor.gd are standalone successors, while payload/src/pose_editor.gd composes both scopes. There are7 face anchors,9 handle anchors and2 existing rotation-regression lookup/expectation updates. Root should use either the explicit anchors or the combined payload, never overlay both whole variants in succession.

### Face window

- pose_editor.gd setup(): explicitly keeps resizing enabled and the title accessible. The existing Panel/VBox/outer ScrollContainer, Close command, asset-change close hook, shape editor object and all signals remain.
- pose_editor.gd open_shapes(): bounded first-open dimensions are480–680 pixels wide and520–900 high when the parent can accommodate them. Smaller parent windows clamp the size/minimum to their available region. User-resized dimensions survive close/reopen during the current Studio session. A temporarily smaller parent clamps the opening without replacing the stored larger size. Startup layout changes cannot be mistaken for a user resize before the first opening.
- shape_window_layout.gd: pure personal-window sizing/position policy; no model/project state. This candidate does not persist shape-window size across application restarts.
- pose_editor.gd shape_body and base_shape_editor.gd animated panel + ItemList: expansion flags distribute surplus height to the actual shape list. Animated minimum list height rises105→160. The Advanced base-shape inspector retains its original105 minimum and non-expanding layout.
- Existing area/part/search logic, selected control, expression preview, Amount range[-100,100]/step.001, Apply/reset/remove/record commands, Advanced organization and native-control labels are byte-identical. It does not clamp or reinterpret authored shape amounts and does not diagnose the separate distance-dependent missing face.
- Outer scrolling remains available when Advanced controls or a compact display need more vertical space. Close stays outside that scroll. The native/embedded window policy remains the existing one; this does not force a new OS window.

### Pose handles

- editor_handle_metrics.gd: computes native-projection to physical-screen conversion from the fitted canvas rectangle plus its true local-to-screen transform. The same transform measures picking distances. Positive finite, nonsingular geometry is required; invalid/zero layouts expose no grab geometry.
- pose_editor.gd setup(): reads optional personal ConfigFile[pose] handle_percent. Supported integer values75,100,125,150,200. Missing/malformed values use150 without writing preferences. ConfigFile has no project schema migration; reads do not rewrite old preference data.
- pose_editor.gd add_handle_size_control()/set_handle_size_percent(): Settings exposes a Simple-mode Pose handle size choice. Changes finish an existing pose gesture through its original path and redraw; the existing save_display_preference helper preserves other configuration fields. This is a personal interface preference, not a saved model or animation field.
- app.gd show_display_settings(): one added call before the existing fullscreen command. Midnight Neon and both classic themes keep their existing construction/style code.
- update_gizmo(): default150 gives105 physical pixels for the RGB-ring nominal radius and135 for the camera-facing ring;100 gives70/90. Small75 and larger200 remain options. Native renderer resolution, fitted canvas dimensions, UI scaling and editor panning do not reduce the requested physical size. World radius is derived through the existing camera projection; no object transform, camera setting, render resolution or exported pixel is changed.
- input(): handle and joint pick distances use transformed physical-screen points with a12-pixel minimum band (15 at150%;20 at200%). The displayed line geometry and picking conversion share the same mapping. Existing drag vectors/units, ray-plane angles, axis locks,15° snap, IK/contacts, auto-key/history, off-scene start rejection and global release/cancel remain unchanged.
- Existing RGB/view-ring ratio is preserved. UI line thickness and joint-dot artwork remain existing theme drawing. This does not implement neighboring-joint motion, change rotation direction, or alter model scale.

## Authored verification (not executed)

1. editor_geometry_unit.gd:37 controls for preference parsing, physical radius/hit size under100–200% interface scale,1080p/4K coordinates, fitted canvas changes, invalid geometry refusal, transformed origins, bounded window sizes and retained user size. It uses no app/native asset/GPU.
2. face_window_layout_smoke.gd:30 real-widget checks. Root supplies an owned output directory and an existing generated morph GLB (for example the shape_fixture prepared by tests/verify_source_shapes.py). It opens the actual Shapes window, grows the actual list by resizing, checks reopen/filter/selection, Simple/Advanced commands and unchanged shape amounts/authored state/source hash. It awaits actual drawing and therefore requires the private graphical runner; it is not a headless surrogate or owner comfort certification.
3. pose_handle_size_smoke.gd:27 actual UI/pixel/picking checks using an owned generated skinned fixture. It tests missing/invalid old preference reads and explicit200% setting through the real Settings signal, preserves unrelated preference fields, checks actual white outer-ring pixels at1600×1000 and3440×1440 under100%/150% UI scale, accepts an inside-band click and rejects an outside-band click, preserves model/camera/video/history/skin, and restores the preference in a fresh editor instance. It requires real GPU draws on the private Windows desktop. Pixel mapping uses Window.get_stretch_transform independently from the production viewport-to-screen path, so an accidental extra DPI factor is detectable.
4. Updated existing rotation_gizmo_smoke.gd: every original assertion remains. Its obsolete fixed90 render-pixel circle expectation becomes the requested physical radius; its invisible-handle fixture places the target far enough outside using the actual current radius, and still explicitly proves the tested point is outside. Existing direction/quadrant/rolled-camera/root+bone/locks/snap/Undo/Redo/global release/cold persistence/frame clipping checks remain. Run existing tests/verify_rotation_gizmo.py; do not treat these source changes as a pass.
5. Root should also run existing shape-comparison/catalog/animation regressions and relevant pose/IK/contact/UI/neon checks before adopting. Broaden to the required Windows verification for an integrated release when appropriate. Preserve failed results and use new versioned source candidates for any discovered fixes.

Root invocation examples (always via the approved private runner, absolute writable log): headless tests/editor_geometry_unit.gd; graphical tests/face_window_layout_smoke.gd -- <owned-folder> <owned-morph.glb>; graphical tests/pose_handle_size_smoke.gd -- <owned-folder>. These are script arguments, not authorization for a visible fallback. Do not run these during another owned native/GPU lane.

## Official API references

Coordinate composition follows Godot4.6: CanvasItem.get_global_transform_with_canvas maps local points into its viewport, and Viewport.get_screen_transform maps viewport points into the containing window-manager screen. Window.content_scale_factor is incorporated by the engine’s stretch transform; it is not multiplied manually a second time. Native Window.size uses physical pixels. Root must verify the platform’s actual rendering/picking with the supplied smoke tests.

- https://docs.godotengine.org/en/4.6/classes/class_canvasitem.html#class-canvasitem-method-get-global-transform-with-canvas
- https://docs.godotengine.org/en/4.6/classes/class_viewport.html#class-viewport-method-get-screen-transform
- https://docs.godotengine.org/en/4.6/classes/class_viewport.html#class-viewport-method-get-stretch-transform
- https://docs.godotengine.org/en/4.6/classes/class_window.html#class-window-property-content-scale-factor

No code was copied from these documentation pages. No assets, images, tool binaries or private scene data are included.

## Version2 controller-memory qualification

The independent source peer raised a possible lifecycle gap: a native resize notification produced by popup_centered may arrive after a synchronous busy flag is cleared. No runtime failure has been measured for version1; it remains frozen unchanged. Version2 treats the pre-popup size, requested fit and immediate actual popup size as programmatic extents for that opening. An asynchronously delivered size_changed that still matches those extents does not replace the remembered user preference. A different size is treated as a user resize for this panel cache; subsequent resize events in the same opening continue to record the final manual size, including a return to an initial extent. There is no timed lockout or input delay.

The expanded actual-widget smoke closes a manually enlarged650×800 window, shrinks the main host, reopens/clamps queues one explicitly controlled late size_changed notification and permits15 process frames plus a completed draw, closes/restores/reopens, and requires the original650×800 preference and size. It then manually resizes while compact and requires that new size to survive restoration. Simple and Advanced controls/outer scrolling/Close are checked under both100% and150% main-interface scaling. These add15 checks for30 total. The previous15 checks remain. The37 pure geometry controls remain unchanged and are not claimed to prove controller event ordering.

Godot4.6 source inspection confirms popup_centered sets the requested size before its base popup path and native resize notifications are delivered through the window callback. This source inspection motivates the explicit policy; only Root's real private-desktop execution can qualify the lifecycle and DPI cases. No actual GUI/DPI result is asserted.

- https://github.com/godotengine/godot/blob/4.6/scene/main/window.cpp

No current application or owner preference file was edited. Both prior source scopes and all unchanged targets are preserved; the handle-only variant is byte-identical to version1.

The controlled late signal is identified in each resize-case record. It is a deterministic controller ordering control, not a claim that the OS naturally delayed an event in the measured run. Ordinary popup/manual-size changes still use real Window properties and signals. The no-argument signal has no origin tag; this bounded guard recognizes only sizes generated by this panel's opening path. A future feature that programmatically resizes this panel through another path must extend that policy.

## Version3: actual close-lifecycle failure and correction

Root ran qualification host v2 in an isolated private window. Headless import and all37 geometry assertions passed. All30 face assertions emitted PASS, but ordinary app.free() then logged SCRIPT ERROR from handle_metrics: the still-valid Canvas had already left the tree, so its viewport was null. WindReview, PendingWind and setup cleanup all reached update_gizmo during teardown. The strict error guard correctly failed the job; no handle pixel or existing rotation success is implied. All three attempted private jobs closed and inputs/environment/HEAD remained unchanged.

This successor guards handle_metrics against invalid/detached Canvas and invalid/detached viewport before measuring screen coordinates. update_gizmo clears derived handle/joint caches first and returns while Canvas is invalid or outside the tree. It does not suppress errors or modify the wind/setup owners, model state, source geometry, values or preferences.

Six new real-widget lifecycle assertions extend the face smoke30→36. It detaches the actual valid Canvas and confirms its missing viewport, requests metrics, invokes the same ordinary wind/setup stop paths, reinserts Canvas and confirms live measurements recover. A synchronous freed dummy Canvas reference exercises the invalid-instance branch and is restored before yielding. The regression verifies derived caches clear and authored state/source bytes remain unchanged. Ordinary final app.free() still runs under the existing strict engine-error and leak checks. Other GUI/picking controls and existing rotation regressions remain intact. New total qualification assertion count is413, with six private jobs unchanged.

All v3 code/tests remain unrun by this author. The previous frozen23-file UI v2 packet remains unchanged. Root owns fresh qualification; the observed30 face PASS lines do not establish a successful UI qualification or owner acceptance.

## Version4: handle fixture type annotation

Root's actual v3 run passed import, geometry37 and face36/lifecycle6 without engine errors. The next handle script failed to parse before any handle assertion: center_image inferred its value through dynamic app.canvas.resolution, leaving its type unset. This is an authored-fixture failure; the production lifecycle correction passed its exercised controls.

V4 changes only var center_image:= to var center_image: Vector2= in pose_handle_size_smoke.gd. The expression, fixture geometry, pixel sampling, pointer controls and27 assertions are unchanged. Every production payload, face36 regression, existing rotation fixture and qualification contract is byte-identical to v3. The other := declarations in the handle and rotation fixtures were inspected: they have concrete constructors, typed receiver methods or typed static returns; no additional concrete inference defect was identified. That inspection is not a parser pass.

The frozen24-file UI v3 packet remains unchanged. Root owns fresh parsing and the full413 assertion qualification. V4 is source-only and unrun by this author; no error guard was relaxed and no whole-UI pass is claimed.
