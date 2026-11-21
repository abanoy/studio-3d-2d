extends "res://tests/movement_path_smoke.gd"
const Lens=preload("res://src/camera_lens_gesture.gd")
const ColdWire=preload("res://tests/camera_cold_wire_oracle.gd")
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Camera lens gesture watchdog");quit(2));call_deferred("run")
func wheel_event(index: int,ctrl:=false) -> InputEventMouseButton:
	var event:=InputEventMouseButton.new();event.button_index=index;event.pressed=true;event.factor=1.;event.ctrl_pressed=ctrl;return event
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var prefs:=ConfigFile.new();prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon");prefs.set_value("display","percent",150 if "--150" in OS.get_cmdline_user_args() else 100);prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.set_advanced("--advanced" in OS.get_cmdline_user_args());await settled()
	app.mode.select(1);app.change_mode(1);app.set_frame(12);await settled()
	var camera: Camera3D=app.renderer.camera;camera.fov=60.
	var initial_transform: Transform3D=camera.transform;var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();var revision: int=app.recovery_revision
	var returned: Array=[];app.camera_cursor_return_requested.connect(func(point):returned.append(point))
	var origin:=Vector2(180,210);var wheel:=wheel_event(MOUSE_BUTTON_WHEEL_UP)
	check(not Lens.handle(app,wheel) and camera.fov==60.,"wheel alone does not change lens")
	var pending:=InputEventMouseButton.new();pending.button_index=MOUSE_BUTTON_RIGHT;pending.pressed=true
	# Use actual selection API, then bind the same off-centre origin it normally records.
	app.world_selection.input(pending,Vector2(960,540));app.world_selection.pending_cursor=origin
	check(app.world_selection.pending_button==MOUSE_BUTTON_RIGHT and not app.navigating,"right press remains normal pending context gesture")
	app._input(wheel)
	check(camera.fov==57. and app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_RIGHT and app.world_selection.pending_button==0,"global wheel upgrades only pending canvas right press to lens gesture")
	check(camera.transform==initial_transform,"lens gesture preserves camera position and orientation")
	check(app.camera_cursor_origin==origin and app.camera_cursor_restore_pending,"lens gesture preserves original right-click cursor origin")
	app._input(wheel_event(MOUSE_BUTTON_WHEEL_DOWN))
	check(camera.fov==60. and camera.transform==initial_transform,"captured global wheel adjusts lens without moving camera")
	var released:=InputEventMouseButton.new();released.button_index=MOUSE_BUTTON_RIGHT;app._input(released)
	check(returned==[origin] and not app.navigating and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE,"right release returns cursor exactly once through existing capture cleanup")
	app.camera_button(MOUSE_BUTTON_RIGHT,true,false,origin);camera.fov=60.
	event_at(app.canvas,app.canvas.size/2,wheel_event(MOUSE_BUTTON_WHEEL_UP));await process_frame
	check(camera.fov==57.,"actual viewport wheel is handled once rather than by both global and canvas routes")
	app.release_mouse();camera.fov=60.
	app.camera_button(MOUSE_BUTTON_LEFT,true,false,origin)
	check(not Lens.handle(app,wheel) and camera.fov==60.,"left-drag WASD navigation keeps ordinary wheel behavior")
	app.camera_button(MOUSE_BUTTON_RIGHT,true)
	check(not Lens.handle(app,wheel) and camera.fov==60.,"two-button roll does not become lens zoom")
	app.release_mouse()
	app.camera_button(MOUSE_BUTTON_MIDDLE,true,false,origin)
	check(not Lens.handle(app,wheel) and camera.fov==60.,"middle-drag dolly remains distinct")
	app.release_mouse();app.navigation_scheme="orbit"
	app.camera_button(MOUSE_BUTTON_RIGHT,true,false,origin);var position_before:=camera.position
	check(not Lens.handle(app,wheel_event(MOUSE_BUTTON_WHEEL_UP,true)),"Ctrl wheel keeps orbit dolly priority")
	app.canvas_input(wheel_event(MOUSE_BUTTON_WHEEL_UP,true),Vector2(960,540))
	check(camera.position!=position_before and camera.fov==60.,"existing Ctrl wheel changes orbit distance rather than lens")
	app.release_mouse();app.navigation_scheme="fly";camera.transform=initial_transform
	app.camera_button(MOUSE_BUTTON_RIGHT,true,false,origin);app.exporting=true
	check(not Lens.handle(app,wheel) and camera.fov==60.,"export refuses lens gesture")
	app.exporting=false;app.playing=true
	check(not Lens.handle(app,wheel) and camera.fov==60.,"playback refuses lens gesture")
	app.playing=false;app.release_mouse();app.mode.select(0);app.change_mode(0)
	check(not Lens.handle(app,wheel),"Draw mode does not gain a lens gesture")
	app.mode.select(1);app.change_mode(1)
	check(app.keys==keys and app.history.size()==history and app.recovery_revision==revision,"all temporary gestures preserve authored keys Undo and dirty revision")
	camera.transform=initial_transform;camera.fov=60.;app.camera_button(MOUSE_BUTTON_RIGHT,true,false,origin);app._input(wheel);app.release_mouse()
	app.insert_key()
	var captured: Dictionary=app.keys.filter(func(key):return int(key.frame)==12)[0]
	check(captured.fov==57. and app.history.size()==history+1,"ordinary Save camera key explicitly captures temporary lens with one Undo")
	var after: Array=app.keys.duplicate(true);app.undo();check(app.keys==keys,"Save camera key Undo restores previous exact keys");app.redo();check(app.keys==after,"Save camera key Redo restores captured lens")
	# Match the exact serialized wire BEFORE Save; original engine inputs stay separate.
	var expected_wire: Array=JSON.parse_string(JSON.stringify(after,"",true,true))
	var saved:=folder.path_join("camera-lens.has");app.has_project.cache_root=folder.path_join("cache");app.has_project.save_file(saved,"packed");await wait_job()
	check(app.has_project.path==saved,"ordinary packed HAS save completes")
	app.new_project();app.has_project.open_file(saved);await wait_job()
	check(ColdWire.matches(app.keys,expected_wire,after,int(app.video.duration_frames)) and app.keys.filter(func(key):return int(key.frame)==12)[0].fov==57.,"packed HAS reopen preserves explicitly saved lens")
	print("CAMERA_LENS_GESTURE_SMOKE ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
