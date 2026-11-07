extends Node
const Drawing = preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
var failures := 0
var checks := 0

func check(ok: bool, text: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func mouse(app, output_point: Vector2, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = pressed
	var rect: Rect2 = app.canvas.image_rect()
	event.position = rect.position + output_point / Vector2(1920, 1080) * rect.size
	app.canvas._gui_input(event)

func camera_button(app, index: int, pressed: bool, outside := false, ctrl := false) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = index
	event.pressed = pressed
	event.ctrl_pressed = ctrl
	if outside: app._input(event)
	else: app.canvas._gui_input(event)

func camera_drag(app, relative: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.relative = relative
	app.canvas._gui_input(motion)

func run(app) -> void:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var hash := FileAccess.get_sha256(app.source)
	app.color.color = Color("f2d2aa")
	app.radius.value = 8
	mouse(app, Vector2(960, 470), true)
	# Draw an original simple character outline through actual canvas coordinate mapping.
	for i in range(1, 65):
		var angle := TAU * i / 64
		app.paint_segment(Vector2(960 + sin(angle) * 90, 560 - cos(angle) * 90))
	mouse(app, Vector2(960, 470), false)
	var cel := Drawing.cel_at(app.layers[1], 0)
	check(not cel.is_empty() and Drawing.image(cel).get_pixel(960, 470).a > 0.9, "canvas pointer maps to full-HD pixels")
	var painted: PackedByteArray = Drawing.image(cel).get_data()
	app.undo()
	check(Drawing.image(cel).get_pixel(960, 470).a == 0, "stroke undo restores touched tiles")
	app.redo()
	check(Drawing.image(cel).get_data() == painted, "stroke redo exact RGBA")
	app.set_frame(24)
	app.create_cel(true)
	check(app.layers[1].cels.size() == 2 and app.layers[1].cels[0].duration == 24, "duplicate splits exposure without gaps")
	app.tool.select(1)
	mouse(app, Vector2(960, 470), true)
	mouse(app, Vector2(960, 470), false)
	check(Drawing.image(Drawing.cel_at(app.layers[1], 24)).get_pixel(960, 470).a == 0, "transparent eraser on duplicate")
	check(Drawing.image(Drawing.cel_at(app.layers[1], 0)).get_data() == painted, "duplicate edit leaves source cel intact")
	app.tool.select(0)
	app.set_frame(0)
	app.mode.select(1)
	app.change_mode(1)
	var count: int = app.layers[1].cels.size()
	mouse(app, Vector2(100, 100), true)
	mouse(app, Vector2(100, 100), false)
	check(not app.drawing and app.layers[1].cels.size() == count, "scene navigation left click cannot paint")
	var keys_before := JSON.stringify(app.keys)
	var pan: Vector2 = app.canvas.pan
	var position_before: Vector3 = app.renderer.camera.position
	var orientation_before: Quaternion = app.renderer.camera.quaternion
	camera_button(app, MOUSE_BUTTON_LEFT, true)
	camera_drag(app, Vector2(20, 10))
	var outside_position: Vector3 = app.renderer.camera.position
	var captured := InputEventMouseMotion.new()
	captured.position = Vector2(-100, -100)
	captured.relative = Vector2(8, 0)
	app._input(captured)
	check(app.renderer.camera.position != outside_position, "captured drag continues outside canvas bounds")
	camera_button(app, MOUSE_BUTTON_LEFT, false)
	check(app.renderer.camera.position != position_before and app.renderer.camera.quaternion.is_equal_approx(orientation_before), "left drag translates camera without rotating or painting")
	position_before = app.renderer.camera.position
	camera_button(app, MOUSE_BUTTON_RIGHT, true)
	var old_rotation: Quaternion = app.renderer.camera.quaternion
	camera_drag(app, Vector2(20, 10))
	check(app.renderer.camera.quaternion != old_rotation and app.renderer.camera.position == position_before, "right drag adjusts POV without translation")
	var fly := InputEventKey.new()
	fly.pressed = true
	fly.keycode = KEY_W
	fly.physical_keycode = KEY_W
	var old_position: Vector3 = app.renderer.camera.position
	Input.parse_input_event(fly)
	# Navigation is delta-time driven. Two very fast render frames can cover
	# less than the movement threshold; bound real time without relaxing it.
	var flight_deadline := Time.get_ticks_msec() + 250
	while app.renderer.camera.position.distance_to(old_position) <= 0.001 and Time.get_ticks_msec() < flight_deadline:
		await get_tree().process_frame
		# process_frame is emitted before nodes process; verify a completed update.
		await RenderingServer.frame_post_draw
	fly = fly.duplicate()
	fly.pressed = false
	Input.parse_input_event(fly)
	await get_tree().process_frame
	camera_button(app, MOUSE_BUTTON_RIGHT, false, true)
	check(app.renderer.camera.position.distance_to(old_position) > 0.001, "WASD input moves temporary camera")
	position_before = app.renderer.camera.position
	orientation_before = app.renderer.camera.quaternion
	camera_button(app, MOUSE_BUTTON_LEFT, true, false, true)
	camera_drag(app, Vector2(12, 5))
	check(app.camera_free and app.renderer.camera.position == position_before and not app.renderer.camera.quaternion.is_equal_approx(orientation_before), "Ctrl plus left enters free-camera mouse look instead of pan")
	fly.pressed = true
	Input.parse_input_event(fly)
	flight_deadline = Time.get_ticks_msec() + 250
	while app.renderer.camera.position.distance_to(position_before) <= 0.001 and Time.get_ticks_msec() < flight_deadline:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
	fly = fly.duplicate()
	fly.pressed = false
	Input.parse_input_event(fly)
	await get_tree().process_frame
	check(app.renderer.camera.position.distance_to(position_before) > 0.001, "Ctrl-left free camera supports WASD flight")
	camera_button(app, MOUSE_BUTTON_LEFT, false, true)
	check(not app.camera_free and not app.navigating, "Ctrl-left release clears free-camera state")
	position_before = app.renderer.camera.position
	orientation_before = app.renderer.camera.quaternion
	var forward_axis: Vector3 = app.renderer.camera.basis.z
	camera_button(app, MOUSE_BUTTON_MIDDLE, true)
	camera_drag(app, Vector2(0, 12))
	camera_button(app, MOUSE_BUTTON_MIDDLE, false, true)
	var dolly: Vector3 = app.renderer.camera.position - position_before
	check(dolly.length() > 0.001 and dolly.normalized().dot(forward_axis) > 0.999 and app.renderer.camera.quaternion.is_equal_approx(orientation_before), "middle drag dollies along view axis without rotating")
	position_before = app.renderer.camera.position
	orientation_before = app.renderer.camera.quaternion
	camera_button(app, MOUSE_BUTTON_LEFT, true)
	camera_button(app, MOUSE_BUTTON_RIGHT, true)
	camera_drag(app, Vector2(20, 0))
	check(app.renderer.camera.position == position_before and not app.renderer.camera.quaternion.is_equal_approx(orientation_before), "left plus right drag rolls without translation")
	camera_button(app, MOUSE_BUTTON_LEFT, false, true)
	check(app.navigating and app.camera_buttons == MOUSE_BUTTON_MASK_RIGHT, "releasing one combined button keeps the other gesture active")
	camera_button(app, MOUSE_BUTTON_RIGHT, false, true)
	check(not app.navigating and app.camera_buttons == 0 and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "release outside canvas ends capture and clears gesture")
	check(app.canvas.pan == pan and app.layers[1].cels.size() == count and JSON.stringify(app.keys) == keys_before, "all camera gestures preserve canvas pan, drawings and shot keys")
	camera_button(app, MOUSE_BUTTON_LEFT, true)
	app._notification(NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(not app.navigating and app.camera_buttons == 0, "focus loss clears camera drag state")
	camera_button(app, MOUSE_BUTTON_MIDDLE, true)
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	app._input(escape)
	check(not app.navigating and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Escape releases any camera drag")
	app.renderer.camera.position.x += 0.2
	app.set_frame(12)
	app.insert_key()
	check(app.keys.size() == 3 and app.keys[1].frame == 12, "editor camera key insertion")
	app.undo()
	check(app.keys.size() == 2, "camera key undo")
	app.mode.select(0)
	app.change_mode(0)
	var shot_transform: Transform3D = app.renderer.camera.transform
	var middle := InputEventMouseButton.new()
	middle.button_index = MOUSE_BUTTON_MIDDLE
	middle.pressed = true
	app.canvas._gui_input(middle)
	var pan_motion := InputEventMouseMotion.new()
	pan_motion.relative = Vector2(7, 9)
	app.canvas._gui_input(pan_motion)
	middle.pressed = false
	app.canvas._gui_input(middle)
	check(app.canvas.pan == Vector2(7, 9) and app.renderer.camera.transform == shot_transform, "Draw middle drag pans canvas without moving camera")
	app.canvas.zoom = 1.75
	app.canvas.pan = Vector2(30, -20)
	app.set_frame(0)
	mouse(app, Vector2(1100, 620), true)
	mouse(app, Vector2(1100, 620), false)
	check(Drawing.image(Drawing.cel_at(app.layers[1], 0)).get_pixel(1100, 620).a > 0.9, "zoom/pan maps brush to output pixels")
	app.canvas.zoom = 1
	app.canvas.pan = Vector2.ZERO
	var parent := ProjectSettings.globalize_path("res://output/editor-smoke")
	DirAccess.make_dir_recursive_absolute(parent)
	var folder := parent.path_join("Editable project — тест")
	app.project_folder = folder
	app.set_frame(24)
	app.save()
	check(not app.dirty and FileAccess.file_exists(folder.path_join("project.json")), "save managed project to Unicode/spaces path")
	app.save()
	check(FileAccess.file_exists(folder.path_join("project.backup.json")), "second atomic save retains backup")
	var before := Drawing.composite(app.layers, 0, 1920, 1080).get_data()
	app.open_project(folder)
	check(not app.dirty and Drawing.composite(app.layers, 0, 1920, 1080).get_data() == before, "reopen preserves exact editable paint")
	check(app.frame == 24, "reopen restores saved timeline frame")
	check(FileAccess.get_sha256(app.source) == hash, "scene hash preserved after paint and managed import")
	app.set_frame(1)
	var key_event := InputEventKey.new()
	key_event.pressed = true
	key_event.keycode = KEY_RIGHT
	app.canvas.grab_focus()
	Input.parse_input_event(key_event)
	await get_tree().process_frame
	check(app.frame == 2, "Right steps one exact frame")
	key_event = InputEventKey.new()
	key_event.pressed = true
	key_event.keycode = KEY_SPACE
	Input.parse_input_event(key_event)
	await get_tree().process_frame
	check(app.playing, "Space starts master timeline")
	await get_tree().create_timer(0.2).timeout
	Input.parse_input_event(key_event.duplicate())
	await get_tree().process_frame
	check(not app.playing and app.frame >= 5, "Space pauses at current frame")
	app.set_frame(0)
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(parent.path_join("editor.png"))
	var reference: Image = await app.renderer.capture(app.keys, app.layers, 0)
	var error: String = await app.export_movie(parent)
	check(error.is_empty(), "editor PNG + MP4 export: " + error)
	var exported := Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	check(exported != null and exported.get_data() == reference.get_data(), "preview evaluation/export identical frame-0 pixels")
	check(app.frame == 0 and app.mode.selected == 0, "export restores editor frame/mode")
	var successful_export: String = app.last_export_folder
	get_tree().create_timer(0.03).timeout.connect(func(): app.cancel_export = true)
	var cancelled: String = await app.export_movie(parent)
	check(cancelled.contains("cancelled") and not app.exporting and not app.cancel_button.visible, "cancel during PNG rendering restores usable editor")
	# Keep the successful export as the verification target.
	app.last_export_folder = successful_export
	# Fail safely on malformed projects; no mutation of the open document.
	var corrupt := parent.path_join("corrupt")
	DirAccess.make_dir_recursive_absolute(corrupt)
	var bad := FileAccess.open(corrupt.path_join("project.json"), FileAccess.WRITE)
	bad.store_string("{broken")
	bad.close()
	check(Storage.load_project(corrupt).has("error"), "corrupt manifest returns readable failure")
	var old_source: String = app.source
	app.open_project(corrupt)
	check(app.source == old_source, "failed open preserves active project")
	var report := {"checks": checks, "failures": failures, "export": app.last_export_folder, "renderer": RenderingServer.get_video_adapter_name()}
	var file := FileAccess.open(parent.path_join("result.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	print("APP_SMOKE ", JSON.stringify(report))
	get_tree().quit(0 if failures == 0 else 1)
