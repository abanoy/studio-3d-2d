extends Node
const Drawing = preload("res://src/drawing.gd")
var checks := 0
var failures := 0

func check(ok: bool, description: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + description)
	if not ok: failures += 1

func settled() -> void:
	for i in range(3): await get_tree().process_frame
	await RenderingServer.frame_post_draw

func click(control: Control) -> void:
	var point := control.get_global_rect().get_center()
	var motion := InputEventMouseMotion.new()
	motion.position = point
	get_viewport().push_input(motion, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		get_viewport().push_input(event, true)
		await settled()
	await settled()

func screenshot(path: String) -> void:
	await settled()
	check(get_viewport().get_texture().get_image().save_png(path) == OK, "captured " + path.get_file())

func run(app) -> void:
	var folder := ProjectSettings.globalize_path("res://output/ui-smoke")
	DirAccess.make_dir_recursive_absolute(folder)
	await settled()
	check(get_window().title == "Hybrid Animation Studio", "window title uses studio identity")
	check(not ProjectSettings.get_setting("application/boot_splash/show_image"), "default Godot boot image is disabled")
	check(not app.advanced_mode and not app.advanced_toggle.button_pressed, "new launch defaults to Simple")
	check(app.drawing_section.is_visible_in_tree() and not app.camera_section.is_visible_in_tree(), "Simple Draw shows contextual drawing controls")
	check(not app.fov.is_visible_in_tree() and not app.debug_label.is_visible_in_tree(), "Simple hides technical controls and diagnostics")
	check(app.radius.is_visible_in_tree() and app.layer_choice.is_visible_in_tree(), "basic brush and layer controls remain available")
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	app.canvas_input(press, Vector2(960, 470))
	app.paint_segment(Vector2(1010, 520))
	press.pressed = false
	app.canvas_input(press, Vector2(1010, 520))
	var cel := Drawing.cel_at(app.layers[1], 0)
	var paint: PackedByteArray = Drawing.image(cel).get_data()
	await screenshot(folder.path_join("simple.png"))
	app.mode.select(1)
	app.change_mode(1)
	check(app.camera_section.is_visible_in_tree() and not app.drawing_section.is_visible_in_tree(), "Simple Scene shows camera controls")
	app.renderer.camera.position += Vector3(0.25, 0.1, 0.2)
	var transform: Transform3D = app.renderer.camera.transform
	var frame: int = app.frame
	var history_size: int = app.history.size()
	await click(app.advanced_toggle)
	check(app.advanced_mode and app.fov.is_visible_in_tree() and app.interpolation.is_visible_in_tree(), "actual toggle click reveals advanced camera controls")
	check(app.drawing_section.is_visible_in_tree() and app.debug_label.is_visible_in_tree(), "Advanced exposes all panels and diagnostics")
	check(app.frame == frame and app.renderer.camera.transform == transform and app.history.size() == history_size, "mode toggle preserves frame, temporary camera and undo")
	app.fov.value = 47
	app.interpolation.select(2)
	app.insert_key()
	var keys := JSON.stringify(app.keys)
	var scene_hash := FileAccess.get_sha256(app.source)
	app.mode.select(0)
	app.change_mode(0)
	var before: Image = await app.renderer.capture(app.keys, app.layers, 0)
	await screenshot(folder.path_join("advanced.png"))
	await click(app.advanced_toggle)
	check(not app.advanced_mode and not app.fov.is_visible_in_tree(), "actual toggle click returns to Simple")
	check(app.fov.value == 47 and app.interpolation.selected == 2 and JSON.stringify(app.keys) == keys, "hidden advanced FOV and hold interpolation remain active")
	check(Drawing.image(cel).get_data() == paint and FileAccess.get_sha256(app.source) == scene_hash, "switching preserves independent drawing and scene asset bytes")
	var after: Image = await app.renderer.capture(app.keys, app.layers, 0)
	check(before.get_data() == after.get_data(), "Simple and Advanced render identical project pixels")
	check(app.import_audio(ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")).is_empty(), "WAV import works in Simple")
	check(app.audio_section.is_visible_in_tree() and not app.audio_trim.is_visible_in_tree(), "Simple reveals audio timing when a clip exists")
	app.set_advanced(true)
	app.audio_gain.value = -9
	app.audio_trim.value = 25
	app.apply_audio_settings()
	var audio: Dictionary = app.audio_clip.duplicate(true)
	app.set_advanced(false)
	app.audio_start.value = 12
	app.apply_audio_settings()
	check(app.audio_clip.gain_db == -9 and app.audio_clip.source_in_sample == audio.source_in_sample and app.audio_clip.start_frame == 12, "Simple audio edits preserve hidden gain and trim")
	app.toggle_play()
	var origin: int = app.play_origin
	app.set_advanced(true)
	check(app.playing and app.play_origin == origin, "revealing details does not restart or stop playback")
	app.stop()
	app.set_advanced(false)
	var minimum: Vector2 = app.get_combined_minimum_size()
	check(minimum.x <= 1200, "layout minimum fits a 1200px workspace")
	get_window().size = Vector2i(1200, 800)
	await screenshot(folder.path_join("simple-1200.png"))
	check(app.canvas.size.x >= 600 and app.advanced_toggle.get_global_rect().end.x < app.size.x, "1200px layout retains usable canvas and accessible Advanced toggle")
	print("UI_SMOKE " + JSON.stringify({"checks": checks, "failures": failures}))
	get_tree().quit(0 if failures == 0 else 1)
