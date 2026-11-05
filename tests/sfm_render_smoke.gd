extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("SFM watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func scan(browser) -> void:
	while browser.job_pid > 0: await process_frame

func dismiss_warnings(app) -> void:
	for control in app.get_children():
		if control is AcceptDialog and control.title == "Source import warnings": control.confirmed.emit()

func run() -> void:
	var input_path: String=OS.get_cmdline_user_args()[0]if not OS.get_cmdline_user_args().is_empty()else"res://output/sfm-verification-input.json"
	var input = JSON.parse_string(FileAccess.get_file_as_string(input_path))
	var app = load("res://main.tscn").instantiate(); root.add_child(app); await process_frame
	var folder: String=str(input.get("folder",ProjectSettings.globalize_path("res://output/sfm-smoke")))
	DirAccess.make_dir_recursive_absolute(folder)
	app.source_import.paths_file = folder.path_join("paths.cfg")
	app.source_import.mount_overrides = {}; app.source_import.extra_roots = []
	if input.has("gmod"):
		app.source_import.gmod_root=str(input.gmod);app.source_import.workshop_root=str(input.workshop)
		check(not DirAccess.dir_exists_absolute(app.source_import.gmod_root),"standalone SFM test uses an absent GMod path")
	var browser = app.source_browser
	browser.open(); await scan(browser)
	browser.source_filter.text = "SFM search path / tf_movies"; browser.filter_sources()
	check(browser.source_rows.size() == 1 and browser.source_rows[0].enabled, "installed SFM profile is enabled automatically in the library")
	if browser.source_rows.size() != 1: quit(1); return
	browser.sources.select(0); browser.sources.item_selected.emit(0); await scan(browser)
	browser.search.text = "models/player/hwm/scout.mdl"; browser.filter_assets()
	check(browser.filtered.size() == 1, "SFM HWM model is searchable through the installed browser")
	if browser.filtered.size() != 1: quit(1); return
	browser.entries.select(0); browser.import_button.pressed.emit(); await process_frame
	while app.source_import.pid > 0: await process_frame
	dismiss_warnings(app); await process_frame
	check(Support.rig(app) != null, "SFM model imports through normal asynchronous standard-model path")
	if Support.rig(app) == null: print(app.status.text); quit(1); return
	var model_bundle: String = app.source_import.folder
	var rig = Support.rig(app)
	check(rig.order.size() == 83, "extended VTX HWM Scout retains its 83-bone skeleton")
	var report = JSON.parse_string(FileAccess.get_file_as_string(model_bundle.path_join("parameters.json")))
	check(report.counts.textures == 6, "SFM body and native iris textures resolve across tf_movies and tf without checkbox setup")
	var eyes: Array=report.materials.filter(func(row):return row.get("status","")=="neutral iris approximation")
	check(eyes.size()==2 and report.native_parameters.eyeballs.size()==2 and eyes.all(func(row):return row.neutral_eye.loops>0 and row.warning.contains("unsupported")),"both native eyes retain source parameters and explicit neutral-appearance limitations")
	var arm := ""
	for id in rig.order:
		if str(rig.bones[id].name).ends_with("bip_upperArm_L"): arm = id
	check(not arm.is_empty(), "native Scout arm is selectable by its original name")
	if arm.is_empty(): quit(1); return
	var editor = app.pose_editor
	# HWM Scout's native bind mesh is Y-up, unlike Source's Z-up world.
	# Preserve that native bind data; use the ordinary root Rotate control.
	editor.tree_items["@root"].select(0); editor.refresh_values(); editor.operation.select(0)
	editor.fields[0].value = 90; editor.apply_numeric()
	editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]
	editor.tree_items[arm].select(0); editor.refresh_values(); editor.operation.select(0)
	var before: Image = await app.renderer.capture(app.keys, app.layers, 0)
	editor.fields[2].value = 60; editor.apply_numeric()
	var posed: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(before.get_data() != posed.get_data(), "shared GMod-style pose control visibly deforms native SFM skin")
	app.undo()
	var undone: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(before.get_data() == undone.get_data(), "SFM pose undo restores exact pixels")
	editor.interpolation.select(1); editor.record_key()
	app.set_frame(48); editor.fields[2].value = 75; editor.apply_numeric(); editor.record_key()
	app.mode.select(0); app.change_mode(0); app.set_frame(24); app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1], 24).image, Vector2(100, 100), Vector2(260, 100), 6, Color.RED, false)
	var expected: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	expected.save_png(folder.path_join("scout-posed.png"))
	app.project_folder = folder.path_join("project"); app.save()
	check(app.open_project(app.project_folder), "SFM rig, pose keys and independent cels reopen in the standard project")
	var reopened: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	check(expected.get_data() == reopened.get_data(), "saved SFM pose and independent drawing reproduce identical pixels")
	if input.has("gmod"):
		app.has_project.cache_root=folder.path_join("has-cache");var packed: String=folder.path_join("scout.has")
		app.has_project.save_file(packed,"packed")
		while app.has_project.pid>0:await process_frame
		check(app.has_project.path==packed,"standalone SFM asset saves through ordinary packed HAS")
		app.new_project();app.has_project.open_file(packed)
		while app.has_project.pid>0:await process_frame
		var packed_picture: Image=await app.renderer.capture(app.keys,app.layers,24,true)
		check(app.has_project.path==packed and packed_picture.get_data()==expected.get_data(),"packed SFM Open preserves exact pose/camera/independent drawing without GMod")
	var error: String = await app.export_movie(folder)
	var movie: String = app.last_export_folder.path_join("movie.mp4")
	var frame := Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
	check(error.is_empty() and frame.get_data() == expected.get_data(), "SFM pose animation exports MP4 with matching frame-24 pixels")
	var actor_hash: String = Support.rig(app).data.sha256
	app.source_import.launch(str(input.map), "", false, 0.01905)
	while app.source_import.pid > 0: await process_frame
	dismiss_warnings(app)
	check(FileAccess.get_sha256(app.source)==FileAccess.get_sha256(app.source_import.folder.path_join("scene.glb")) and Support.rig(app).data.sha256 == actor_hash, "native SFM BSP appends environment while preserving the independent actor")
	var map_bundle: String = app.source_import.folder
	Support.rig(app).data.visible = false
	Support.rig(app).apply(0)
	report = JSON.parse_string(FileAccess.get_file_as_string(map_bundle.path_join("parameters.json")))
	check(report.counts.textures > 0 and app.source_import.apply_view(report), "SFM map resolves textures and a usable player-start view")
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]
	var image: Image = await app.renderer.capture(app.keys, app.layers, 0)
	image.save_png(folder.path_join("sfm-box.png"))
	var result := {"checks": checks, "failures": failures, "movie": movie, "model_bundle": model_bundle, "map_bundle": map_bundle}
	var output := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify(result)); output.close()
	print("SFM_SMOKE " + JSON.stringify(result)); quit(0 if failures == 0 else 1)
