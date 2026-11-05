extends SceneTree
var failures := 0
var counts := {}

func _initialize() -> void:
	call_deferred("run")

func inventory(node: Node) -> void:
	if node is Skeleton3D: counts.bones += node.get_bone_count()
	if node is MeshInstance3D:
		counts.meshes += 1
		counts.morphs += node.get_blend_shape_count()
		if node.mesh: counts.surfaces += node.mesh.get_surface_count()
	for child in node.get_children(): inventory(child)

func check(ok: bool, text: String) -> void:
	print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func run() -> void:
	var app = load("res://main.tscn").instantiate()
	root.add_child(app)
	await process_frame
	var report := {}
	for sample in ["street-tested", "miku-tested"]:
		var directory := ProjectSettings.globalize_path("res://output/compatibility/" + sample)
		var scene := directory.path_join("scene.glb")
		var hash := FileAccess.get_sha256(scene)
		app.load_scene(scene)
		check(FileAccess.get_sha256(app.source) == hash, sample + " imports with the application's real managed GLB loader")
		var keys_before := JSON.stringify(app.keys)
		app.frame_3d_scene()
		check(JSON.stringify(app.keys) == keys_before, "Frame 3D scene changes navigation camera without rewriting shot keys")
		if sample == "street-tested":
			# This map is built from many single-sided facades, viewed from its street-facing side.
			var bounds: AABB = app.renderer.scene_bounds(app.renderer.environment_root())
			var distance: float = app.renderer.camera.position.distance_to(bounds.get_center())
			app.renderer.camera.position = bounds.get_center() + Vector3(0, 0.55, -1).normalized() * distance
			app.renderer.camera.look_at(bounds.get_center(), Vector3.UP)
		app.set_frame(0)
		app.insert_key()
		app.mode.select(0)
		app.change_mode(0)
		counts = {"bones": 0, "meshes": 0, "morphs": 0, "surfaces": 0}
		inventory(app.renderer.environment_root())
		check(counts.meshes > 0 and counts.surfaces > 0, sample + " contains renderable geometry/material surfaces")
		if sample == "miku-tested": check(counts.bones >= 122 and counts.morphs > 0, "PMD bones and vertex morph channels survive into Godot")
		var image: Image = await app.renderer.capture(app.keys, app.layers, 0)
		check(image.save_png(directory.path_join("studio-frame.png")) == OK, sample + " rendered full-HD frame")
		var color := image.get_pixel(0, 0)
		var different := 0
		for y in range(100, 1080, 100):
			for x in range(100, 1920, 100):
				if image.get_pixel(x, y) != color: different += 1
		check(different > 5, sample + " render is not a blank viewport")
		app.project_folder = directory.path_join("studio-project")
		app.save()
		app.open_project(app.project_folder)
		check(not app.dirty and FileAccess.get_sha256(app.source) == hash, "converted GLB survives managed save/reopen unchanged")
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(directory.path_join("studio-editor.png"))
		report[sample] = counts.duplicate()
	var file := FileAccess.open(ProjectSettings.globalize_path("res://output/compatibility/render-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures": failures, "samples": report}, "\t"))
	print("LEGACY_RENDER ", JSON.stringify(report), " failures=", failures)
	quit(0 if failures == 0 else 1)
