extends SceneTree
# Neon Pro screenshot helper for docs/redesign-mock/app-*.png (see docs/REDESIGN-PORT.md).
# Launched by tools/linux/shoot.sh: godot --script <abs>/shoot.gd -- --demo-room --shoot-out <dir>
const SceneIO = preload("res://src/scene3d.gd")
var out := ""

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--shoot-out")
	out = args[i + 1] if i >= 0 and i + 1 < args.size() else ProjectSettings.globalize_path("res://output/neon-shots")
	DirAccess.make_dir_recursive_absolute(out)
	create_timer(120).timeout.connect(func(): push_error("SHOOT watchdog expired"); quit(2))
	call_deferred("run")

func settled(n := 4) -> void:
	for k in range(n): await process_frame
	await RenderingServer.frame_post_draw

func shot(name: String) -> void:
	await settled(8)
	var image := root.get_texture().get_image()
	var path := out.path_join(name)
	print(("SHOT " if image.save_png(path) == OK else "SHOT FAILED ") + path + " " + str(image.get_size()))

func run() -> void:
	var scratch := ProjectSettings.globalize_path("res://output/neon-shoot/run_%d" % OS.get_process_id())
	DirAccess.make_dir_recursive_absolute(scratch)
	var app = load("res://main.tscn").instantiate()
	app.recovery_root = scratch.path_join("recovery")
	# Never read or write the owner's interface prefs.
	app.display_prefs_path = scratch.path_join("display.cfg")
	root.add_child(app)
	await settled(10)
	if app.home and app.home.visible: app.home.hide()
	if OS.get_environment("SHOOT_MODEL") != "0":
		var fixture := scratch.path_join("rig.glb")
		if SceneIO.make_pose_fixture(fixture) == OK:
			app.pose_editor.add_model(fixture)
			await settled()
	# A short stroke so the Draw view shows ink, like ui_smoke.
	app.set_advanced(false)
	app.pick_mode(0)
	await settled()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	app.canvas_input(press, Vector2(860, 420))
	for p in [Vector2(900, 470), Vector2(960, 500), Vector2(1020, 480), Vector2(1080, 430)]: app.paint_segment(p)
	press.pressed = false
	app.canvas_input(press, Vector2(1080, 430))
	app.message("Drawing copied to frame 0. Keep drawing, or press Play to preview.")
	await shot("draw.png")
	app.pick_mode(1)
	await shot("camera.png")
	app.pick_mode(2)
	await shot("pose.png")
	app.set_advanced(true)
	app.pick_mode(0)
	await shot("advanced.png")
	app.set_advanced(false)
	app.pick_mode(0)
	await settled()
	print("SHOOT_DONE " + out)
	app.dirty = false
	quit(0)
