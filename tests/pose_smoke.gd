extends Node
const Support = preload("res://tests/world_test_support.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Model = preload("res://src/model.gd")
const Timeline = preload("res://src/timeline.gd")
const Storage = preload("res://src/storage.gd")
const Drawing = preload("res://src/drawing.gd")
var checks := 0
var failures := 0

func check(ok: bool, text: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func bone(rig, name: String) -> String:
	for id in rig.order:
		if rig.bones[id].name == name: return id
	return ""

func select_bone(editor, id: String) -> void:
	editor.tree_items[id].select(0)
	editor.tree.scroll_to_item(editor.tree_items[id])
	editor.refresh_values()

func rotate(editor, degrees: Vector3) -> void:
	editor.operation.select(0)
	for i in range(3): editor.fields[i].value = degrees[i]
	editor.apply_numeric()

func pointer(app, point: Vector2, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = pressed
	var rect: Rect2 = app.canvas.image_rect()
	event.position = rect.position + point / Vector2(1920, 1080) * rect.size
	app.canvas._gui_input(event)

func shot(app) -> void:
	app.pose_editor.frame_model()
	var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(48, camera.position, camera.quaternion, camera.fov)]

func run(app) -> void:
	var folder := ProjectSettings.globalize_path("res://output/pose-smoke")
	DirAccess.make_dir_recursive_absolute(folder)
	var fixture := folder.path_join("original-rig.glb")
	check(SceneIO.make_pose_fixture(fixture) == OK, "original skinned GLB fixture exported")
	var scene_hash := FileAccess.get_sha256(app.source)
	var source_hash := FileAccess.get_sha256(fixture)
	var editor = app.pose_editor
	# Retain regression coverage for the explicit draft/key workflow available in Advanced.
	editor.auto_key.button_pressed = false
	check(editor.add_model(fixture).is_empty(), "standard GLB model added beside environment")
	var rig = Support.rig(app)
	check(rig != null and rig.order.size() == 2 and FileAccess.get_sha256(app.source) == scene_hash, "separate actor keeps existing environment and skeletal identity")
	var id := bone(rig, "arm")
	if id.is_empty(): check(false, "arm bone required"); get_tree().quit(1); return
	select_bone(editor, id)
	check(editor.selected == id, "bone tree selects the actual skeleton joint")
	shot(app)
	select_bone(editor, id)
	var root_transform: Transform3D = rig.root.transform
	var original: Image = await app.renderer.capture(app.keys, app.layers, 0)
	rotate(editor, Vector3(0, 0, 60))
	var posed: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(original.get_data() != posed.get_data() and rig.root.transform == root_transform, "bone rotation visibly deforms skin without moving actor root")
	app.undo()
	var undone: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(undone.get_data() == original.get_data(), "pose undo restores exact rendered skin")
	app.redo()
	var redone: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(redone.get_data() == posed.get_data(), "pose redo restores exact rendered skin")
	select_bone(editor, id)
	rotate(editor, Vector3.ZERO)
	editor.interpolation.select(1)
	editor.record_key()
	app.set_frame(48)
	rotate(editor, Vector3(0, 0, 90))
	select_bone(editor, "@root")
	rotate(editor, Vector3(0, 40, 0))
	editor.scale_field.value = 1.5; editor.scale_apply.pressed.emit()
	editor.operation.select(1); editor.refresh_values()
	editor.fields[0].value = 0.5; editor.apply_numeric()
	select_bone(editor, id)
	editor.record_key()
	app.set_frame(24)
	var midpoint := Timeline.quaternion(rig.sample(24)[id].rotation_xyzw)
	check(midpoint.is_equal_approx(Quaternion(Vector3.BACK, PI / 4)), "pose keys sample quaternion midpoint at exact master frame")
	check(absf(rig.sample_transform(24).position[0] - 0.25) < 0.0001, "model root placement shares the same interpolated pose timeline")
	check(absf(rig.sample_transform(24).scale - 1.25) < 0.0001 and Timeline.quaternion(rig.sample_transform(24).rotation_xyzw).is_equal_approx(Quaternion(Vector3.UP, deg_to_rad(20))), "root rotation and uniform scale interpolate with the same keys")
	Support.set_pose_interpolation(rig,0,"hold")
	check(Timeline.quaternion(rig.sample(24)[id].rotation_xyzw).is_equal_approx(Quaternion.IDENTITY), "hold pose interpolation uses prior key")
	Support.set_pose_interpolation(rig,0,"ease")
	check(Timeline.quaternion(rig.sample(12)[id].rotation_xyzw).is_equal_approx(Quaternion(Vector3.BACK, PI / 2 * 0.15625)), "ease pose interpolation samples exact quarter time")
	Support.set_pose_interpolation(rig,0,"linear")
	editor.operation.select(0)
	editor.refresh_values()
	editor.apply_frame()
	editor.update_gizmo()
	check(editor.handles.size() == 3 and not app.canvas.pose_joints.is_empty(), "real projected skeleton and three colored rotation handles exist")
	var hip := bone(rig, "hip")
	for joint in editor.joints:
		if joint.id == hip:
			pointer(app, joint.point, true); pointer(app, joint.point, false); break
	check(editor.selected == hip, "viewport joint click selects the bone and matching tree item")
	select_bone(editor, id); editor.update_gizmo()
	var handle: Dictionary = editor.handles[2]
	var start: Vector2 = handle.points[6]
	var history: int = app.history.size()
	var camera_keys := JSON.stringify(app.keys)
	var cel_count: int = app.layers[1].cels.size()
	pointer(app, start, true)
	check(editor.dragging, "actual canvas press hits a pose handle")
	var motion := InputEventMouseMotion.new()
	var rect: Rect2 = app.canvas.image_rect()
	var end := start + Vector2(45, -25)
	motion.position = rect.position + end / Vector2(1920, 1080) * rect.size
	app.canvas._gui_input(motion)
	pointer(app, end, false)
	check(app.history.size() == history + 1, "a complete gizmo drag is one undo command")
	check(rig.data.draft_frame == 24 and rig.authored_keys().size() == 2, "gizmo edits a draft without silently recording a key")
	check(app.layers[1].cels.size() == cel_count and JSON.stringify(app.keys) == camera_keys, "pose drag cannot paint or edit camera keys")
	editor.record_key()
	check(rig.authored_keys().size() == 3, "explicit Record adds pose to shared timeline")
	app.undo()
	app.undo()
	select_bone(editor, id)
	editor.snap.button_pressed = true
	rotate(editor, Vector3(0, 0, 22))
	check(Timeline.quaternion(rig.data.pose[id].rotation_xyzw).is_equal_approx(Quaternion(Vector3.BACK, deg_to_rad(15))), "rotation snapping uses 15 degree increments")
	editor.locks[2].button_pressed = true
	rotate(editor, Vector3(0, 0, 60))
	check(Timeline.quaternion(rig.data.pose[id].rotation_xyzw).is_equal_approx(Quaternion(Vector3.BACK, deg_to_rad(15))), "locked axis preserves existing rotation")
	editor.locks[2].button_pressed = false
	editor.snap.button_pressed = false
	editor.operation.select(1)
	editor.refresh_values()
	editor.fields[0].value = 0.2
	editor.apply_numeric()
	check(absf(rig.data.pose[id].position[0] - 0.2) < 0.0001, "bone position overrides are independent from rotation")
	editor.record_key()
	# JSON numbers reload as floats; compare normalized data, not Variant type tags.
	var expected: Dictionary = JSON.parse_string(JSON.stringify(rig.data,"",true,true))
	app.project_folder = folder.path_join("generic-project")
	app.save()
	check(not app.dirty, "standard model/pose project saves")
	var previous_root: Node3D=rig.root
	check(app.open_project(app.project_folder) and Support.rig(app) != null, "reopen rebuilds model rather than retaining old live skeleton")
	rig = Support.select_rig(app,expected.id)
	check(rig.root!=previous_root,"reopen installs a fresh independent rig while restoring all world objects")
	check(rig.data.pose == expected.pose and Support.same_keys(rig.data,expected), "bone draft and recorded pose keys survive managed save/reopen")
	check(FileAccess.get_sha256(fixture) == source_hash and FileAccess.get_sha256(app.source) == scene_hash, "pose operations preserve original model/environment bytes")
	var manifest_path: String = app.project_folder.path_join("project.json")
	var manifest_bytes := FileAccess.get_file_as_bytes(manifest_path)
	var broken: Dictionary = JSON.parse_string(manifest_bytes.get_string_from_utf8())
	for row in broken.world.objects:
		if row.id==rig.data.id:row.pose["missing::bone"] = Model.identity()
	var manifest := FileAccess.open(manifest_path, FileAccess.WRITE)
	manifest.store_string(JSON.stringify(broken)); manifest.close()
	var current_model = Support.rig(app)
	check(not app.open_project(app.project_folder) and Support.rig(app) == current_model, "missing bone binding rejects project before replacing live scene/model")
	manifest = FileAccess.open(manifest_path, FileAccess.WRITE)
	manifest.store_buffer(manifest_bytes); manifest.close()
	app.mode.select(2); app.change_mode(2)
	editor.set_flag("reference_only", true)
	var visible: Image = await app.renderer.capture(app.keys, app.layers, 24)
	var excluded: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	editor.set_flag("visible", false)
	var hidden: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
	check(visible.get_data() != excluded.get_data() and excluded.get_data() == hidden.get_data(), "reference model is visible in preview and excluded from movie")
	editor.set_flag("visible", true)
	editor.set_flag("reference_only", false)
	app.recovery_root = folder.path_join("recovery")
	app.begin_recovery_session()
	app.changed(); app.autosave_tick(true)
	var checkpoint: String = app.recovery_root.path_join(app.recovery_session)
	check(not Storage.load_project(checkpoint).has("error"), "pose model/assets included in complete recovery checkpoint")
	check(app.restore_checkpoint({"folder": checkpoint}) and Support.same_keys(Support.rig(app).data,expected), "recovery restores actual model bone animation")
	Support.select_rig(app,expected.id)
	app.mode.select(2); app.change_mode(2)
	select_bone(editor, id)
	editor.operation.select(1); editor.space.select(1); editor.apply_frame(); editor.update_gizmo()
	var move_handle: Dictionary = editor.handles[0]
	var move_start: Vector2 = move_handle.points[0].lerp(move_handle.points[1], 0.7)
	var world_before: Vector3 = Support.rig(app).bone_transform(id).origin
	pointer(app, move_start, true)
	var move_end: Vector2 = move_start + (move_handle.points[1] - move_handle.points[0]).normalized() * 30
	var move := InputEventMouseMotion.new()
	var view: Rect2 = app.canvas.image_rect()
	move.position = view.position + move_end / Vector2(1920, 1080) * view.size
	app.canvas._gui_input(move)
	pointer(app, move_end, false)
	var moved: Vector3 = Support.rig(app).bone_transform(id).origin - world_before
	check(moved.length() > 0.001 and moved.normalized().dot(Vector3.RIGHT) > 0.999, "world-axis handle translates bone in world X through its parent transform")
	app.undo()
	editor.update_gizmo()
	move_handle = editor.handles[0]
	move_start = move_handle.points[0].lerp(move_handle.points[1], 0.7)
	var before_cancel := JSON.stringify(Support.rig(app).data)
	pointer(app, move_start, true)
	app.canvas._gui_input(move)
	var escape := InputEventKey.new(); escape.keycode = KEY_ESCAPE; escape.pressed = true
	app._input(escape)
	check(not editor.dragging and JSON.stringify(Support.rig(app).data) == before_cancel, "Escape cancels a pose drag without recording or changing data")
	pointer(app, move_start, false)
	# Export animated standard model plus an independent painted overlay.
	app.mode.select(0); app.change_mode(0); app.set_frame(0)
	app.create_cel(false)
	Drawing.stroke(Drawing.cel_at(app.layers[1], 0).image, Vector2(100, 100), Vector2(200, 100), 6, Color.RED, false)
	app.changed()
	var reference: Image = await app.renderer.capture(app.keys, app.layers, 0, true)
	var error: String = await app.export_movie(folder)
	var movies: Array[String] = [app.last_export_folder.path_join("movie.mp4")]
	var first := Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	var last := Image.load_from_file(app.last_export_folder.path_join("frame_000048.png"))
	check(error.is_empty() and FileAccess.file_exists(app.last_export_folder.path_join("movie.mp4")), "actual animated model and drawing export to MP4")
	check(first.get_data() == reference.get_data() and first.get_data() != last.get_data(), "export uses identical pose evaluation and changes skin/root across frames")
	var reload_path := folder.path_join("reload-rig.glb")
	DirAccess.copy_absolute(fixture, reload_path)
	editor.add_model(reload_path)
	var old_root = Support.rig(app).root
	var bytes := FileAccess.get_file_as_bytes(reload_path)
	var length := bytes.decode_u32(12)
	var text := bytes.slice(20, 20 + length).get_string_from_utf8().replace("OriginalPoseFixture", "ModifiedPoseFixture")
	var replacement := text.to_utf8_buffer()
	check(replacement.size() == length, "same-path asset reload fixture preserves binary chunk lengths")
	for i in range(length): bytes[20 + i] = replacement[i]
	var changed := FileAccess.open(reload_path, FileAccess.WRITE); changed.store_buffer(bytes); changed.close()
	check(editor.add_model(reload_path).is_empty() and Support.rig(app).root != old_root and Support.rig(app).data.sha256 == FileAccess.get_sha256(reload_path), "reimporting changed model at same path rebuilds runtime rig")
	# This local sample is optional for clean-checkout CI; mandatory evidence on owner's machine.
	var miku := ProjectSettings.globalize_path("res://output/compatibility/miku-tested/scene.glb")
	var native_tested := false
	if FileAccess.file_exists(miku):
		var miku_hash := FileAccess.get_sha256(miku)
		check(editor.add_model(miku).is_empty(), "actual prepared PMD enters the same standard model slot")
		rig = Support.rig(app)
		check(rig.order.size() >= 122 and rig.data.metadata.has("native_parameters"), "native MMD bone metadata stays with standard pose record")
		var arm := bone(rig, "左腕")
		check(not arm.is_empty(), "actual MMD native arm bone can be selected")
		if not arm.is_empty():
			shot(app)
			select_bone(editor, arm)
			var before: Image = await app.renderer.capture(app.keys, app.layers, 0)
			rotate(editor, Vector3(0, 0, 65))
			var after: Image = await app.renderer.capture(app.keys, app.layers, 0)
			check(before.get_data() != after.get_data(), "actual MMD mesh deforms when native arm is rotated")
			after.save_png(folder.path_join("miku-posed.png"))
			editor.interpolation.select(1); editor.record_key()
			app.set_frame(48); rotate(editor, Vector3(0, 0, -20)); editor.record_key()
			app.set_frame(24)
			var native_midpoint: Image = await app.renderer.capture(app.keys, app.layers, 24, true)
			check(native_midpoint.get_data() != before.get_data() and native_midpoint.get_data() != after.get_data(), "actual MMD pose animation interpolates the skinned mesh")
			var native_error: String = await app.export_movie(folder)
			movies.append(app.last_export_folder.path_join("movie.mp4"))
			var exported_midpoint := Image.load_from_file(app.last_export_folder.path_join("frame_000025.png"))
			check(native_error.is_empty() and exported_midpoint.get_data() == native_midpoint.get_data(), "actual MMD animated MP4 uses identical frame-24 pose pixels")
			editor.apply_frame(); editor.update_gizmo()
			await get_tree().process_frame
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(folder.path_join("miku-editor.png"))
			app.project_folder = folder.path_join("miku-project"); app.save()
			var native_metadata: Dictionary = JSON.parse_string(JSON.stringify(Support.rig(app).data.metadata,"",true,true))
			check(app.open_project(app.project_folder) and Support.rig(app).data.pose.has(arm) and FileAccess.get_sha256(miku) == miku_hash, "actual MMD pose reopens without changing its source")
			check(Support.rig(app).data.metadata == native_metadata, "native parameter report and unknown fields survive managed save/reopen")
			native_tested = true
	else: print("SKIP actual MMD sample absent; original standard rig checks still required")
	var result := {"checks": checks, "failures": failures, "actual_mmd_tested": native_tested, "movies": movies}
	var report := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	report.store_string(JSON.stringify(result)); report.close()
	print("POSE_SMOKE " + JSON.stringify(result))
	get_tree().quit(0 if failures == 0 else 1)
