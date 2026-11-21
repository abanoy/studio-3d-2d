extends SceneTree
# Owned review preparation only; no imported artist arrays are printed.
const Timeline = preload("res://src/timeline.gd")
const Storage = preload("res://src/storage.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Native = preload("res://src/source_secondary.gd")
const EXPECTED_GLB := "b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71"
var app
var request: Dictionary = {}
var checks: Dictionary = {}
var failed := false
var target_id := ""
func _initialize() -> void:
	create_timer(180).timeout.connect(func(): push_error("Review preparation timed out"); quit(2))
	call_deferred("run")
func check(ok: bool, label: String) -> bool:
	checks[label] = ok
	failed = failed or not ok
	print(("PASS " if ok else "FAIL ") + label)
	return ok
func settle() -> void:
	for _index in range(5): await process_frame
	await RenderingServer.frame_post_draw
func wait_job() -> void:
	while app.has_project.pid > 0: await process_frame
	await settle()
func actor() -> RefCounted:
	return app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else null
func digest(value: Variant) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(JSON.stringify(value,"",true,true).to_utf8_buffer())
	return context.finish().hex_encode()
func inspect_native() -> Dictionary:
	var rig: RefCounted = actor()
	if not check(rig != null,"review_actor_exists"): return {}
	check(rig.data.get("sha256") == EXPECTED_GLB,"corrected_glb_exact")
	var resolved: RefCounted = Bindings.resolve(rig)
	check(resolved.status == "bound_inactive" and resolved.bindings.size() == 69 and resolved.rule_owner_ids.size() == 49,"native_69_bones_49_rules_bound")
	check(Native.offered(rig),"imported_hair_option_offered")
	var report: Dictionary = rig.data.get("metadata",{}).get("native_parameters",{})
	var native: Dictionary = report.get("native_parameters",{})
	var crosswalk: Dictionary = native.get("source_export_crosswalk",{})
	check(crosswalk.get("proof_sha256") == Native.LIVE_CROSSWALK_PROOF_SHA and crosswalk.get("glb_sha256") == EXPECTED_GLB,"final_glb_crosswalk_preserved")
	return {"metadata_sha256":digest(rig.data.get("metadata",{})),"crosswalk_sha256":str(crosswalk.get("proof_sha256","")),"bones":resolved.bindings.size(),"rules":resolved.rule_owner_ids.size()}
func run() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 1: quit(2); return
	request = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if request.get("format") != "has_corrected_junko_owner_review_request_1": quit(2); return
	var folder: String = request.folder
	var mode: String = request.mode
	app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("UserData/preparation-recovery")
	app.display_prefs_path = folder.path_join("UserData/preparation-prefs.cfg")
	app.recent_path = folder.path_join("UserData/preparation-recents.json")
	root.add_child(app); await settle()
	app.home.hide(); app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("UserData/" + mode + "-cache")
	app.new_project()
	var project: String = folder.path_join("Examples/Junko.has")
	var expected_path: String = folder.path_join("Verification/expected-private.json")
	if mode == "writer":
		var error: String = app.pose_editor.add_model(folder.path_join("Assets/Junko/scene.glb"))
		check(error.is_empty() and app.current_world().objects.size() == 1,"single_junko_import")
		if not error.is_empty(): finish({}); return
		target_id = app.last_import_id
		app.world_selection.select_entity(target_id); app.pose_editor.frame_model(); await settle()
		var camera: Camera3D = app.renderer.camera
		var key: Dictionary = Timeline.key(0,camera.position,camera.quaternion,camera.fov)
		key["near"] = camera.near; key["far"] = camera.far
		app.keys = [key]; app.video.duration_frames = 48; app.set_frame(0); await settle()
		var native: Dictionary = inspect_native()
		var pixels: Dictionary = {}
		for lighting in ["unshaded","lit"]:
			app.lighting_choice.item_selected.emit(app.Renderer.Lighting.MODES.find(lighting)); await settle()
			var image: Image = await app.renderer.capture(app.keys,[],0,true)
			check(image != null and not image.is_empty(),"writer_" + lighting + "_capture")
			image.save_png(folder.path_join("Verification/Junko-" + lighting + ".png")); pixels[lighting] = Storage.image_hash(image)
		app.lighting_choice.item_selected.emit(0); await settle()
		app.has_project.save_file(project,"packed"); await wait_job()
		check(app.has_project.path == project and not app.dirty,"packed_junko_saved")
		FileAccess.open(expected_path,FileAccess.WRITE).store_string(JSON.stringify({"native":native,"camera":app.keys,"pixels":pixels},"",true,true))
		finish(native)
	elif mode == "reader":
		var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(expected_path))
		app.has_project.open_file(project); await wait_job()
		check(app.has_project.path == project and not app.dirty and app.current_world().objects.size() == 1,"packed_junko_cold_open")
		if app.current_world().objects.size() != 1: finish({}); return
		target_id = app.current_world().objects[0].id
		app.world_selection.select_entity(target_id); await settle()
		var native: Dictionary = inspect_native()
		check(native == expected.native,"cold_native_metadata_exact")
		check(app.keys == expected.camera,"cold_camera_exact")
		for lighting in ["unshaded","lit"]:
			app.lighting_choice.item_selected.emit(app.Renderer.Lighting.MODES.find(lighting)); await settle()
			var image: Image = await app.renderer.capture(app.keys,[],0,true)
			check(Storage.image_hash(image) == expected.pixels[lighting],"cold_" + lighting + "_pixels_exact")
		finish(native)
	else: quit(2)
func finish(native: Dictionary) -> void:
	var result: Dictionary = {"format":"has_corrected_junko_owner_review_observation_1","mode":request.mode,"passed":not failed,"checks":checks,"native":native,"profile":OS.get_user_data_dir()}
	FileAccess.open(str(request.result),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	app.free(); quit(1 if failed else 0)
