extends SceneTree

func _initialize() -> void:
	create_timer(120).timeout.connect(func(): quit(2))
	call_deferred("run")

func run() -> void:
	var request := OS.get_environment("HAS_MMD_TEST_REQUEST")
	if not FileAccess.file_exists(request):
		print("SKIP missing fixture; run tests/verify_mmd_missing_texture.py")
		quit(0)
		return
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(request))
	var source: String = meta.folder.path_join("fixture").path_join(meta.source.get_file())
	var folder: String = meta.folder.path_join("app_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	root.add_child(app)
	await process_frame
	app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("cache")
	if meta.has("packed"):
		app.has_project.open_file(meta.packed)
		while app.has_project.pid > 0: await process_frame
		var ids: Array = app.renderer.world_runtime.order
		var portable := false
		if ids.size() == 1:
			var instance = app.renderer.world_runtime.instance(ids[0])
			var loaded_path: String = instance.data.source.simplify_path()
			var cache_prefix: String = app.has_project.cache_root.simplify_path() + "/"
			portable = meta.absent in instance.data.metadata.native_parameters.missing_textures and not instance.root.find_children("*", "MeshInstance3D", true, false).is_empty()
			portable = portable and loaded_path.begins_with(cache_prefix) and FileAccess.get_sha256(loaded_path) == meta.geometry_hash
		print("MISSING_TEXTURE_PORTABLE ", portable)
		app.free()
		quit(0 if portable else 1)
		return
	app.load_scene(source)
	while app.source_import.pid > 0: await process_frame
	var warning := false
	var closed_dialog: WeakRef
	for child in app.get_children():
		if child is AcceptDialog and child.title == "Imported with limitations":
			warning = child.visible and not child.exclusive and child.dialog_text.begins_with("Missing texture files: 1\n") and meta.absent in child.dialog_text
			closed_dialog = weakref(child)
			child.close_requested.emit()
	await process_frame
	await process_frame
	warning = warning and closed_dialog.get_ref() == null
	if not warning or app.renderer.world_runtime.instances.size() != 1:
		print("Import failed: ", app.status.text, " warning=", warning)
		app.free()
		quit(1)
		return
	var id: String = app.last_import_id
	var saved: String = folder.path_join("street.has")
	app.has_project.save_file(saved, "packed")
	while app.has_project.pid > 0: await process_frame
	if app.has_project.path != saved:
		print("Save failed: ", app.status.text)
		app.free()
		quit(1)
		return
	app.new_project()
	app.has_project.open_file(saved)
	while app.has_project.pid > 0: await process_frame
	var restored = app.renderer.world_runtime.instance(id)
	var ok: bool = restored != null and meta.absent in restored.data.metadata.native_parameters.missing_textures
	print("MISSING_TEXTURE_REOPEN ", ok, " ", saved)
	app.free()
	quit(0 if ok else 1)

