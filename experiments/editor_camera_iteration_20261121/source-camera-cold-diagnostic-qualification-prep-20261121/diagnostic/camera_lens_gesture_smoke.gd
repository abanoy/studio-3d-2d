extends "res://tests/movement_path_smoke.gd"
const Lens=preload("res://src/camera_lens_gesture.gd")
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Camera lens gesture watchdog");quit(2));call_deferred("run")
func wheel_event(index: int,ctrl:=false) -> InputEventMouseButton:
	var event:=InputEventMouseButton.new();event.button_index=index;event.pressed=true;event.factor=1.;event.ctrl_pressed=ctrl;return event
# Diagnostic only: strict original assertions below remain byte-exact.
func cold_types(value, at: String, rows: Array) -> void:
	if rows.size()>=4096:return
	rows.append({"path":at,"type":type_string(typeof(value))})
	if value is Dictionary:
		for key in value:cold_types(value[key],at+"["+JSON.stringify(str(key))+"]",rows)
	elif value is Array:
		for index in range(value.size()):cold_types(value[index],at+"["+str(index)+"]",rows)
func cold_diff(expected, actual, at: String, rows: Array) -> void:
	if rows.size()>=4096:return
	if typeof(expected)!=typeof(actual):rows.append({"path":at,"kind":"type","expected_type":type_string(typeof(expected)),"actual_type":type_string(typeof(actual))})
	if (expected is int or expected is float) and (actual is int or actual is float):
		if float(expected)!=float(actual):rows.append({"path":at,"kind":"number","expected_full_precision":JSON.stringify(expected,"",true,true),"actual_full_precision":JSON.stringify(actual,"",true,true),"delta_full_precision":JSON.stringify(float(actual)-float(expected),"",true,true)})
	elif expected is Dictionary and actual is Dictionary:
		for key in expected:
			if not actual.has(key):rows.append({"path":at,"kind":"missing_key","key":str(key)})
			else:cold_diff(expected[key],actual[key],at+"["+JSON.stringify(str(key))+"]",rows)
		for key in actual:
			if not expected.has(key):rows.append({"path":at,"kind":"added_key","key":str(key)})
	elif expected is Array and actual is Array:
		if expected.size()!=actual.size():rows.append({"path":at,"kind":"array_length","expected":expected.size(),"actual":actual.size()})
		for index in range(mini(expected.size(),actual.size())):cold_diff(expected[index],actual[index],at+"["+str(index)+"]",rows)
	elif expected!=actual:rows.append({"path":at,"kind":"value","expected_full_precision":JSON.stringify(expected,"",true,true),"actual_full_precision":JSON.stringify(actual,"",true,true)})
func cold_write(name: String,value) -> void:
	var target:=FileAccess.open(folder.path_join(name),FileAccess.WRITE)
	if target==null:push_error("Cannot write camera cold diagnostic");quit(2);return
	target.store_string(JSON.stringify(value,"\t",true,true)+"\n");target.flush()
	var error: Error=target.get_error();target.close()
	if error!=OK:push_error("Cannot complete camera cold diagnostic");quit(2)
func record_cold_diagnostic(before_text: String, before_types: Array, after_save: Array, expected_original: Array, loaded: Array) -> void:
	var expected_wire=JSON.parse_string(before_text)
	var loaded_types: Array=[];cold_types(loaded,"$",loaded_types)
	var original_differences: Array=[];cold_diff(expected_original,loaded,"$",original_differences)
	var wire_differences: Array=[];cold_diff(expected_wire,loaded,"$",wire_differences)
	var save_differences: Array=[];cold_diff(expected_original,after_save,"$",save_differences)
	var frame12: Array=loaded.filter(func(key):return key is Dictionary and int(key.get("frame",-1))==12)
	var report:={"format":"has_camera_lens_cold_exact_diagnostic_1","fixture_predecessor_sha256":"072d32cc7cdfce86c1070b3980ac5dae9cebbd9d90597f6b3eae90c89bfd275e","original_native_equality":expected_original==loaded,"wire_expected_equality":expected_wire==loaded,"loaded_frame12_count":frame12.size(),"loaded_frame12_fov":frame12[0].get("fov") if frame12.size()==1 else null,"save_mutated_keys":expected_original!=after_save,"before_save_full_precision_json":before_text,"after_save_full_precision_json":JSON.stringify(after_save,"",true,true),"loaded_full_precision_json":JSON.stringify(loaded,"",true,true),"before_types":before_types,"loaded_types":loaded_types,"original_vs_loaded":original_differences,"wire_vs_loaded":wire_differences,"original_vs_after_save":save_differences,"comparison_policy_changed":false,"product_persistence_changed":false}
	cold_write("camera-lens-cold-diagnostic.json",report)
	print("CAMERA_LENS_COLD_DIAGNOSTIC ",JSON.stringify(report,"",true,true))
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
	var cold_before_text: String=JSON.stringify(after,"",true,true)
	var cold_before_types: Array=[];cold_types(after,"$",cold_before_types)
	cold_write("camera-lens-before-save.json",{"full_precision_json":cold_before_text,"types":cold_before_types})
	var saved:=folder.path_join("camera-lens.has");app.has_project.cache_root=folder.path_join("cache");app.has_project.save_file(saved,"packed");await wait_job()
	check(app.has_project.path==saved,"ordinary packed HAS save completes")
	var cold_after_save: Array=app.keys.duplicate(true)
	app.new_project();app.has_project.open_file(saved);await wait_job()
	record_cold_diagnostic(cold_before_text,cold_before_types,cold_after_save,after,app.keys)
	check(app.keys==after and app.keys.filter(func(key):return int(key.frame)==12)[0].fov==57.,"packed HAS reopen preserves explicitly saved lens")
	print("CAMERA_LENS_GESTURE_SMOKE ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
