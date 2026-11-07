extends Node
const Recovery = preload("res://src/recovery.gd")
const Storage = preload("res://src/storage.gd")
const Drawing = preload("res://src/drawing.gd")
const Journal=preload("res://src/recovery_journal.gd")
var checks := 0
var failures := 0

func check(ok: bool, description: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + description)
	if not ok: failures += 1

func write(path: String, text: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(text)
	file.close()

func run(app) -> void:
	await get_tree().process_frame
	var base := ProjectSettings.globalize_path("res://output/recovery-smoke")
	DirAccess.make_dir_recursive_absolute(base)
	if "--recovery-write" in OS.get_cmdline_user_args():
		app.recovery_root = base.path_join("run_%d_%d" % [Time.get_unix_time_from_system(), Time.get_ticks_usec()])
		app.begin_recovery_session()
		app.project_folder = app.recovery_root.path_join("manual")
		app.save()
		var manual := FileAccess.get_sha256(app.project_folder.path_join("project.json"))
		app.set_frame(18)
		app.create_cel(false)
		var cel := Drawing.cel_at(app.layers[1], 18)
		Drawing.stroke(Drawing.image(cel), Vector2(900, 480), Vector2(1020, 600), 8, Color.RED, false)
		app.renderer.camera.position.x += 1
		app.insert_key()
		app.import_audio(ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav"))
		app.audio_start.value = 12
		app.audio_gain.value = -9
		app.apply_audio_settings()
		for guard in ["drawing", "navigating", "playing", "exporting"]:
			app.set(guard, true)
			app.autosave_due = 0
			app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
			check(app.checkpoint_revision == -1, "autosave defers while " + guard)
			app.set(guard, false)
		var modal := AcceptDialog.new()
		app.add_child(modal)
		modal.popup_centered()
		app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
		check(app.checkpoint_revision == -1, "autosave defers while a dialog is open")
		modal.queue_free()
		await get_tree().process_frame
		app.autosave_enabled.set_pressed_no_signal(false)
		app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
		check(app.checkpoint_revision == -1, "automatic recovery respects disabled preference")
		app.autosave_enabled.set_pressed_no_signal(true)
		app.autosave_due = 0
		app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
		var folder: String = app.recovery_root.path_join(app.recovery_session)
		check(FileAccess.file_exists(folder.path_join("project.json")) and app.dirty, "timer path writes complete recovery without marking manual save clean")
		check(Recovery.candidates(app.recovery_root).is_empty(), "a live writer's recovery is not offered to another app")
		var first := Recovery.read_json(folder.path_join("project.json"))
		var cel_path: String = first.layers[1].cels[0].path
		# Simulate interrupted cached-file writes; a retry must repair from live data.
		write(folder.path_join(first.scene.path), "partial scene")
		write(folder.path_join(first.audio.path), "partial audio")
		write(folder.path_join(cel_path), "partial raster")
		app.changed()
		app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
		var second := Recovery.read_json(folder.path_join("project.json"))
		check(not Storage.load_project(folder).has("error"), "retry repairs interrupted scene, WAV and raster files before commit")
		check(second.layers[1].cels[0].path == cel_path, "unchanged recovery raster is reused by pixel hash")
		var backup_hash := FileAccess.get_sha256(folder.path_join("project.backup.json"))
		write(folder.path_join("project.json"), "{")
		app.changed()
		app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
		check(not Storage.load_project(folder).has("error") and FileAccess.get_sha256(folder.path_join("project.backup.json")) == backup_hash, "corrupt current JSON never replaces the previous complete backup")
		check(FileAccess.get_sha256(app.project_folder.path_join("project.json")) == manual, "automatic recovery leaves manual project byte-identical")
		var previous := FileAccess.get_sha256(folder.path_join("project.json"))
		app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
		check(FileAccess.get_sha256(folder.path_join("project.json")) == previous, "no redundant checkpoint for unchanged revision")
		# Leave a half-written temp file, then exit without resolving the recovery.
		write(folder.path_join("project.json.tmp"), "{interrupted")
		check(not Storage.load_project(folder).has("error"), "partial manifest temp does not replace last committed checkpoint")
		write(base.path_join("last-run.json"), JSON.stringify({"root": app.recovery_root, "folder": folder, "manual": app.project_folder, "manual_sha256": manual, "pixels": Storage.image_hash(Drawing.image(cel)), "keys": app.keys, "checkpoint_ms": app.last_recovery_ms},"",true,true))
		print("RECOVERY_WRITE failures=%d" % failures)
	else:
		var expected := Recovery.read_json(base.path_join("last-run.json"))
		if expected.is_empty():
			check(false, "writer fixture required before restart check")
			get_tree().quit(1)
			return
		app.recovery_root = expected.root
		app.begin_recovery_session()
		var candidates := Recovery.candidates(app.recovery_root)
		check(candidates.size()==Journal.entries(expected.folder).size() and candidates.size()>=2 and candidates[0].manifest=="project.json", "new process discovers deduplicated committed history and current checkpoint after writer exits")
		app.show_recovery()
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(base.path_join("recovery-dialog.png"))
		var dialog: AcceptDialog
		for child in app.get_children():
			if child is AcceptDialog and child.title == "Recover work": dialog = child
		check(dialog != null and dialog.visible, "recovery choices are visible in real app window")
		# Exercise the same confirmation action as the actual Restore button.
		dialog.get_ok_button().pressed.emit()
		await get_tree().process_frame
		check(app.dirty and app.project_folder.is_empty() and app.frame == 18, "restore is an unsaved copy at the checkpoint frame")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1], 18))) == expected.pixels and JSON.parse_string(JSON.stringify(app.keys,"",true,true)) == expected.keys, "restart recovery preserves exact editable paint and camera keys")
		check(app.audio_clip.start_frame == 12 and app.audio_clip.gain_db == -9, "restart recovery preserves managed audio and timing/gain")
		check(FileAccess.get_sha256(expected.manual.path_join("project.json")) == expected.manual_sha256, "restoring does not touch original manual project")
		var complete := Recovery.read_json(expected.folder.path_join("project.json"))
		var raster_path: String = expected.folder.path_join(complete.layers[1].cels[0].path)
		var raster_bytes := FileAccess.get_file_as_bytes(raster_path)
		var damaged := Image.load_from_file(raster_path)
		damaged.set_pixel(900, 480, Color.BLUE)
		damaged.save_png(raster_path)
		check(Storage.load_project(expected.folder).has("error"), "changed cached raster is rejected by pixel checksum")
		var restored := FileAccess.open(raster_path, FileAccess.WRITE)
		restored.store_buffer(raster_bytes)
		restored.close()
		# A failed write must leave the previous complete checkpoint usable.
		var folder: String = expected.folder
		DirAccess.remove_absolute(folder.path_join("project.json.tmp"))
		DirAccess.make_dir_recursive_absolute(folder.path_join("project.json.tmp"))
		var before := FileAccess.get_sha256(folder.path_join("project.json"))
		var error := Storage.save_project(folder, app.video, app.keys, app.layers, app.source, app.frame, app.audio_clip)
		check(not error.is_empty() and FileAccess.get_sha256(folder.path_join("project.json")) == before, "manifest-write failure preserves last committed recovery")
		DirAccess.remove_absolute(folder.path_join("project.json.tmp"))
		# Corrupt the latest test checkpoint. The previous generation is explicit.
		write(folder.path_join("project.json"), "{")
		candidates = Recovery.candidates(app.recovery_root)
		check(candidates.size()==Journal.entries(folder).size() and Journal.is_manifest(candidates[0].manifest) and candidates.any(func(entry):return entry.manifest=="project.backup.json"), "corrupt current manifest retains the immutable latest and explicit older checkpoint")
		check(app.restore_checkpoint(candidates[0]), "previous checkpoint restores successfully")
		var original_source: String = app.source
		var original_frame: int = app.frame
		check(not app.restore_checkpoint({"folder": base.path_join("missing")}) and app.source == original_source and app.frame == original_frame, "failed recovery preserves the open project")
		app.project_folder = base.path_join("restored_saved_%d" % Time.get_ticks_usec())
		app.save()
		check(not app.dirty and Recovery.candidates(app.recovery_root).is_empty(), "manual save of restored copy resolves its pending recovery notice")
		Recovery.write_json(folder.path_join("resolved.json"), {"sha256": "older-resolution"})
		check(Recovery.candidates(app.recovery_root).size()==Journal.entries(folder).size() and Recovery.resolve(folder).is_empty() and Recovery.candidates(app.recovery_root).is_empty() and FileAccess.file_exists(folder.path_join("project.backup.json")), "dismissal hides matching checkpoint without deleting its files")
		print("RECOVERY_SMOKE " + JSON.stringify({"checks": checks, "failures": failures, "checkpoint_ms": expected.checkpoint_ms}))
	get_tree().quit(0 if failures == 0 else 1)
