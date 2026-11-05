extends SceneTree
const Timeline = preload("res://src/timeline.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(60).timeout.connect(func(): push_error("Mount render watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks += 1; print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func run() -> void:
	var app = load("res://main.tscn").instantiate(); root.add_child(app); await process_frame
	var folder := ProjectSettings.globalize_path("res://output/source-mount-render")
	DirAccess.make_dir_recursive_absolute(folder)
	var before: Image
	var before_props := 0
	for sample in ["source-shrine-tested", "shrine-sfm-dependencies"]:
		var path := ProjectSettings.globalize_path("res://output/compatibility/" + sample)
		var report = JSON.parse_string(FileAccess.get_file_as_string(path.path_join("parameters.json")))
		if not report is Dictionary: check(false, "prepared private shrine sample required: " + sample); quit(1); return
		app.new_project();app.load_scene(path.path_join("scene.glb"))
		check(FileAccess.get_sha256(app.source) == FileAccess.get_sha256(path.path_join("scene.glb")), sample + " imports with normal managed GLB loader")
		check(app.source_import.apply_view(report), "native player-start view remains usable")
		var camera: Camera3D = app.renderer.camera
		app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]
		var image: Image = await app.renderer.capture(app.keys, app.layers, 0)
		image.save_png(folder.path_join(sample + ".png"))
		if sample == "source-shrine-tested": before = image; before_props = int(report.native_parameters.props_loaded)
		else:
			check(report.native_parameters.props_loaded > before_props and report.native_parameters.props_loaded >= 524, "installed SFM content supplies missing native props without copying into GMod")
			check(report.counts.textures >= 34 and report.warnings.size() == 1, "more materials resolve and corrupt embedded material remains an explicit error")
			check(image.get_data() != before.get_data(), "resolved dependencies visibly change the actual rendered map")
			app.project_folder = folder.path_join("project"); app.save()
			check(app.open_project(app.project_folder), "dependency-resolved standard scene survives managed save/reopen")
	var output := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	output.store_string(JSON.stringify({"checks": checks, "failures": failures})); output.close()
	print("SOURCE_MOUNTS checks=", checks, " failures=", failures)
	quit(0 if failures == 0 else 1)
