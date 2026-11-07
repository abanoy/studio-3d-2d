extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
var failures := 0
var checks := 0

func _initialize() -> void:
	create_timer(150).timeout.connect(func(): push_error("Source smoke watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func run() -> void:
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	var folder := ProjectSettings.globalize_path("res://output/source-smoke")
	DirAccess.make_dir_recursive_absolute(folder)
	var source_import = app.source_import
	source_import.paths_file = folder.path_join("test-source-paths.cfg")
	source_import.gmod_root = source_import.DEFAULT_GMOD
	source_import.workshop_root = source_import.DEFAULT_WORKSHOP
	check(source_import.default_browse_dir().replace("\\", "/") == source_import.DEFAULT_WORKSHOP, "native file browser starts in the installed Workshop 4000 directory")
	check(source_import.save_paths() == OK, "Source folder choices save outside project data")
	source_import.gmod_root = ""; source_import.workshop_root = ""
	source_import.load_paths()
	check(source_import.gmod_root == source_import.DEFAULT_GMOD and source_import.workshop_root == source_import.DEFAULT_WORKSHOP, "installed game and Workshop paths survive preference reload")
	app.pose_editor.import_dialog()
	var file_picker: FileDialog
	for child in app.get_children():
		if child is FileDialog: file_picker = child
	check(file_picker != null and file_picker.current_dir.replace("\\", "/") == source_import.DEFAULT_WORKSHOP, "actual Add model picker browses installed Workshop content by default")
	if file_picker: file_picker.canceled.emit()
	await process_frame
	var source := "C:/a/tools/touhou_reimu_bikini.gma"
	var map_path := ProjectSettings.globalize_path("res://output/compatibility/source-map-v3/scene.glb")
	if not FileAccess.file_exists(source) or not FileAccess.file_exists(map_path):
		check(false, "private Source assets and prepared map required; see docs/source_import.md")
		quit(1); return
	var original_hash := FileAccess.get_sha256(source)
	var scene_before: String = app.source
	app.source_import.start(source, true)
	var choice: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title == "Import Source model": choice = child
	check(choice != null, "native Add model opens the real archive member chooser")
	if choice == null: quit(1); return
	for field in choice.find_children("*", "LineEdit", true, false):
		var row := field.get_parent()
		if row is HBoxContainer and row.get_child_count() == 2:
			row.get_child(1).pressed.emit()
			break
	var folder_picker: FileDialog
	for child in choice.get_children():
		if child is FileDialog: folder_picker = child
	check(folder_picker != null and folder_picker.file_mode == FileDialog.FILE_MODE_OPEN_DIR, "Source setup offers a nested folder picker for custom game libraries")
	if folder_picker: folder_picker.canceled.emit()
	await process_frame
	await RenderingServer.frame_post_draw
	check(choice.size.y <= root.size.y and choice.position.y >= 0 and choice.position.y + choice.size.y <= root.size.y and choice.get_ok_button().get_global_rect().end.y <= choice.size.y, "scrollable Source setup keeps Prepare and Cancel inside the app window")
	root.get_texture().get_image().save_png(folder.path_join("source-setup.png"))
	var members: OptionButton
	for control in choice.find_children("*", "OptionButton", true, false): members = control
	for i in range(members.item_count):
		if members.get_item_text(i) == "models/ragdoll/reimu_hakurei_bikini_ragdoll.mdl": members.select(i)
	check(members.item_count == 9, "GMA inventory lists nine models without extracting or running Lua")
	choice.confirmed.emit()
	check(app.source_import.pid > 0 and app.source == scene_before, "preparation runs asynchronously and preserves existing environment")
	var pulses := 0
	while app.source_import.pid > 0:
		pulses += 1
		await process_frame
	check(pulses > 3 and Support.rig(app) != null, "editor processes frames while Blender converts and standard actor installs")
	if Support.rig(app) == null: print(app.status.text); quit(1); return
	var rig = Support.rig(app)
	check(rig.order.size() == 77, "actual MDL skeleton retains 77 bones in the shared model system")
	check(rig.data.metadata.native_parameters.standard == "studio_model_1", "Source native parameters use the existing model metadata contract")
	var arm := ""
	for id in rig.order:
		if str(rig.bones[id].name).ends_with("L_UpperArm"): arm = id
	check(not arm.is_empty(), "native ValveBiped arm can be selected")
	if arm.is_empty(): quit(1); return
	var editor = app.pose_editor
	editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]
	editor.tree_items[arm].select(0); editor.refresh_values()
	var before: Image = await app.renderer.capture(app.keys, app.layers, 0)
	editor.operation.select(0)
	editor.fields[2].value = 60; editor.apply_numeric()
	var after: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(before.get_data() != after.get_data(), "native Source arm rotation visibly deforms imported skin")
	app.undo()
	var undone: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(before.get_data() == undone.get_data(), "Source pose undo restores exact rendered pixels")
	editor.interpolation.select(1); editor.record_key()
	app.set_frame(48); editor.fields[2].value = 75; editor.apply_numeric(); editor.record_key()
	app.mode.select(0); app.change_mode(0); app.set_frame(24)
	app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1], 24)), Vector2(100, 100), Vector2(260, 100), 6, Color.RED, false)
	app.changed()
	var expected: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	expected.save_png(folder.path_join("source-posed.png"))
	app.project_folder = folder.path_join("source-project"); app.save()
	var metadata: Dictionary = JSON.parse_string(JSON.stringify(rig.data.metadata,"",true,true))
	check(app.open_project(app.project_folder) and Support.rig(app).data.metadata == metadata, "managed save/reopen restores Source rig keys and native parameters")
	var reopened: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	check(expected.get_data() == reopened.get_data(), "Source saved pose and independent cel reproduce identical pixels")
	var error: String = await app.export_movie(folder)
	var movie: String = app.last_export_folder.path_join("movie.mp4")
	var exported := Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
	check(error.is_empty() and exported.get_data() == expected.get_data(), "actual Source pose animation exports MP4 with exact frame-24 pixels")
	check(FileAccess.get_sha256(source) == original_hash, "original supplied GMA remains byte-identical")
	var raw_map := "C:/Program Files (x86)/Steam/steamapps/common/GarrysMod/garrysmod/maps/gm_construct.bsp"
	var raw_hash := FileAccess.get_sha256(raw_map)
	app.load_scene(raw_map)
	var map_choice: ConfirmationDialog
	for child in app.get_children():
		if child is ConfirmationDialog and child.title == "Import Source map": map_choice = child
	check(map_choice != null, "Add scene routes raw BSP through the real preparation dialog")
	if map_choice == null: quit(1); return
	map_choice.confirmed.emit()
	while app.source_import.pid > 0: await process_frame
	map_path = app.source_import.folder.path_join("scene.glb")
	check(FileAccess.get_sha256(app.source)==FileAccess.get_sha256(map_path) and app.source != scene_before and app.mode.selected == 1 and Support.rig(app)!=null, "BSP conversion appends standard map, preserves actor and enters Scene mode")
	check(FileAccess.get_sha256(raw_map) == raw_hash, "installed original BSP remains byte-identical")
	app.frame_3d_scene()
	var map_report = JSON.parse_string(FileAccess.get_file_as_string(map_path.get_base_dir().path_join("parameters.json")))
	check(app.source_import.apply_view(map_report), "map offers a usable native player-start view without rewriting camera keys")
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position + Vector3(1, 0, 0), camera.quaternion, camera.fov)]
	app.set_frame(0); app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1], 0)), Vector2(100, 80), Vector2(260, 80), 6, Color.YELLOW, false)
	var map_image: Image = await app.renderer.capture(app.keys, app.layers, 0, true)
	var map_repeat: Image = await app.renderer.capture(app.keys, app.layers, 0, true)
	check(map_image.get_data() == map_repeat.get_data(), "map capture repeats deterministically before saving")
	var saved_keys: Array = app.keys.duplicate(true)
	map_image.save_png(folder.path_join("source-map.png"))
	var variations := {}
	for y in range(50, 1080, 50):
		for x in range(50, 1920, 50): variations[map_image.get_pixel(x, y).to_html()] = true
	check(variations.size() > 30, "actual converted map renders textured geometry rather than a blank viewport")
	app.project_folder = folder.path_join("map-project"); app.save()
	var saved_map_folder: String=app.project_folder
	app.new_project()
	check(app.open_project(saved_map_folder), "converted map managed project reopens")
	var map_reopened: Image = await app.renderer.capture(app.keys, app.layers, 0, true)
	var same_keys := true
	for i in range(saved_keys.size()):
		if Timeline.vector(saved_keys[i].position) != Timeline.vector(app.keys[i].position) or Timeline.quaternion(saved_keys[i].rotation_xyzw) != Timeline.quaternion(app.keys[i].rotation_xyzw): same_keys = false
	check(same_keys, "map camera transforms survive managed save/reopen")
	var changed := 0; var total := 0
	if map_image.get_data() != map_reopened.get_data():
		var a := map_image.get_data(); var b := map_reopened.get_data()
		for i in range(a.size()):
			var difference := absi(int(a[i]) - int(b[i]))
			if difference > 0: changed += 1; total += difference
		print("MAP_REIMPORT bytes_changed=", changed, " mean=", float(total) / a.size())
	map_reopened.save_png(folder.path_join("source-map-reopened.png"))
	# Independent GLB imports may reorder coplanar/transparent edges. Bound that
	# GPU variation tightly rather than treating two edge pixels as lost scene data.
	check(changed <= 384 and float(total) / map_image.get_data().size() < 0.002 and map_reopened.get_pixel(150, 80).g > 0.9, "saved map and independent cel reopen within bounded GPU edge tolerance")
	var map_midpoint: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	var map_error: String = await app.export_movie(folder)
	var map_movie: String = app.last_export_folder.path_join("movie.mp4")
	var map_exported := Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
	check(map_error.is_empty() and map_exported.get_data() == map_midpoint.get_data(), "actual Source map camera and independent cel export MP4 with exact frame-24 pixels")
	# Cancellation uses the same worker path and must leave current project intact.
	var retained: String = app.source
	app.source_import.launch("C:/Program Files (x86)/Steam/steamapps/common/GarrysMod/garrysmod/maps/gm_construct.bsp", "", false, 0.01905)
	app.source_import.cancel()
	while app.source_import.pid > 0: await process_frame
	check(app.source == retained and app.source_import.cancelled, "cancelled Source preparation preserves current project")
	var worker = JSON.parse_string(FileAccess.get_file_as_string(app.source_import.folder.path_join("worker.json")))
	check(worker is Dictionary and not OS.is_process_running(int(worker.blender_pid)), "cancellation waits until its own Blender worker terminates")
	source_import.gmod_root = folder.path_join("not-installed")
	source_import.launch(source, "models/ragdoll/reimu_hakurei_bikini_ragdoll.mdl", true, 0.01905)
	while source_import.pid > 0: await process_frame
	check(app.source == retained and app.status.text.contains("must already be installed") and not DirAccess.dir_exists_absolute(source_import.folder), "missing GMod blocks native import before staging or Blender without replacing the scene")
	source_import.gmod_root = source_import.DEFAULT_GMOD
	var result := {"checks": checks, "failures": failures, "movie": movie, "map_movie": map_movie, "model_bundle": metadata.external_bundle, "map_bundle": map_path.get_base_dir()}
	var file := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(result)); file.close()
	print("SOURCE_SMOKE " + JSON.stringify(result))
	quit(0 if failures == 0 else 1)
