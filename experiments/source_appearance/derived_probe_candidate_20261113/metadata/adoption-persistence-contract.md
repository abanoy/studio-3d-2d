# Derived SFM app probe contract

This is an output-only source review of the ordinary HAS adoption and persistence contracts for `nitori-skin-0` and `keiki-000`. It does not certify original Source shader fidelity, native appearance selection in the import UI, or editable native conversion. No Godot, app, Blender, GPU, or model runtime was launched by this reviewer. The app harness was not parsed by this reviewer; the parent owns source parsing and any later GPU execution.

The frozen candidate is `source/app_probe.gd`, 17,775 bytes, SHA256 `51dcb316702f843d56eba3a0b500bd8f3ec98454c2548a15ec473960be9581fe`. Its public entry point is `await run(tree, manifest, folder, mode)`. It returns checks, failures, observations, and the completed `app_cases`. The phase folder is `<run>/writer` or `<run>/reader`; packages and expected records are shared at `folder.get_base_dir()`. It makes one normal native renderer capture per case per phase. The parent's eight raw reference captures are separate.

## Ordinary adoption

Use `app.pose_editor.add_model(prepared_glb, 0, {})`, checking its returned error string, then `app.last_import_id` and `app.renderer.world_runtime.instance(id)`. `src/pose_editor.gd` reads the adjacent `parameters.json` and stores its entire report as `actor.data.metadata.native_parameters`. The skin/bodygroup selections therefore reside inside `actor.data.metadata.native_parameters.native_parameters`, not directly in the outer metadata. Adoption also enables the source-shape metadata defaults.

`app.append_object_data` copies the exact GLB into the managed import cache using its SHA256 and pushes one `world` history operation. Record both `actor.data.sha256` and `FileAccess.get_sha256(actor.data.source)`, plus the full report, portable world, root transform, and binding inventory. Compare native bone names against the recorded native report, allowing additional Godot helper bones. The report's recorded native count is 66 for Nitori and 31 for Keiki.

Undo/Redo reconstructs runtime instances through `restore_world`. Reacquire the actor by object ID after every Undo, Redo, and Open. Holding an old RefCounted rig can otherwise produce a false comparison against stale actor data after its scene root has been freed. `renderer.active_model()` is not a reliable lookup after restore until ordinary selection has been reinstated; use the explicit object ID and `world_selection.select_entity(id)`.

The harness selects the exact unique `bip_hand_L`/`box` binding through the existing bone Tree, uses the existing numeric rotation fields with an X value of 20 degrees, and invokes `pose_editor.apply_numeric()`. It checks one authored frame-zero pose key, an actual selected-bone transform change, unchanged model root/source/report, and precise pose Undo/Redo restoration. This is a bounded pose contract; it does not prove every accessory, all native sequences, or native flex semantics.

## Packed project persistence

Connect `has_project.operation_finished(action, success)` before `save_file(path, "packed")` or `open_file(path)`. Require the exact action and `success == true`, plus idle project-loader/snapshot workers, nonpositive project/source import PIDs, and no export operation. A PID becoming idle alone is not a successful Save/Open assertion.

Use `World.portable(app.current_world())` for source-path-independent serialized world comparison. Packed Open is expected to clear history, redo history, and selection; preserve the saved frame/camera/video and serialized actor data; mark the project clean; and resolve the managed GLB below the fresh reader cache. Reacquire its actor by the saved object ID.

The writer stores whole native report metadata, exact source SHA, all binding records, authored keys, model-root and bone transforms, camera/video/frame, package SHA, and one capture's raw RGBA8 hash and dimensions. The reader opens the package with the original owned import alias absent and requires those records and raw pixels to match exactly. No pixel tolerance or extra capture is introduced automatically. A later cold-reader pixel failure is evidence to investigate, not permission to weaken the assertion silently.

The reader is a separate exact-commit source copy with a separate profile and caches. The parent driver changes only the dedicated run's complete copied input tree from `inputs` to `inputs.offline`; it does not move the retained conversion bundles or any original archive/native source. The expected proof is independence from the original import aliases, not disappearance of every historical native path on the PC.

## Existing shape selector APIs

For a static base shape, use `ui = app.pose_editor.base_shapes`, `app.set_advanced(true)`, and `ui.sync()`. Find a `ui.parts` item whose `int(ui.parts.get_item_metadata(i))` equals the exact source-node index, then call `ui.parts.select(i)` and emit `ui.parts.item_selected.emit(i)`. Find a `ui.shapes` item whose item metadata is the desired native target index (Tools target zero), select it and emit its `item_selected`. Set `ui.amount.value`, then emit `ui.apply_button.pressed` or call `ui.apply_amount()`.

`pose_editor.animated_shapes` offers the corresponding frame-key workflow. `pose_editor.set_shape_amounts({str(source_node): {str(target): amount}})` is the existing higher-level authored-shape API. The separate raw harness directly tests the one actual Tools channel at 0, 0.5, and 1 against its independent derived-GLB reference; the app probe above deliberately remains limited to ordinary adoption, numeric bone pose, Undo/Redo, and packed persistence.

## Provenance limits

The app preserves the report as opaque metadata. It does not independently validate or expose the selected native skin/bodygroup controls. Production Source import does not currently expose/pass the experimental appearance request. This proof adopts an already baked GLB; it does not demonstrate pre-conversion native controls or live appearance switching.

Packed HAS preserves the managed GLB (including its embedded textures) and serialized report metadata. It does not package original RAR/MDL/VVD/VTX/VMT files, dependencies.json, editable.blend, the independent native-column proof, or private-desktop/nonce/PID/reader-source attestation receipts. Historical `original_source` and `external_bundle` strings are not portable native files. Original archive/member/CRC provenance remains upstream of the loose-MDL report and is not reconstructed by this app probe.

Existing relevant limits are the 256 KiB adjacent report cap, 1 MiB total metadata cap, 128 MiB imported GLB cap, and 64 world objects. The two selected cases fit the bounded scenario; this does not waive these limits for other models.

## Parent driver static review

The reviewed `probe_driver.py` confines preparation and mutation to its owned output task, hashes the twelve retained bundles and source/runtime inputs, freezes exact-commit writer/reader copies, checks those copies before/after, and requires an exact reviewed manifest hash. Actual graphics require explicit exclusive-lease confirmation, the approved private wrapper, an isolation-success receipt, and exact successful app-case membership. Parse-only uses explicit headless/check-only, without the actual harness arguments. No new path/launch blocker was found in these routes.

One concrete failed-evidence issue was reported to the parent: `subprocess.run(timeout=210)` can raise before `process.log`/`execution.json` are written. A timeout handler should retain partial stdout/stderr, command, and timeout/elapsed facts in the phase folder before re-raising. Existing fail-and-retain/no-retry behavior should remain. This review does not constitute approval to launch graphics; the root owns that decision and lease.
