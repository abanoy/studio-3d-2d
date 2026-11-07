extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func press(index: int) -> void:
	var event:=InputEventMouseButton.new();event.button_index=index;event.pressed=true;event.ctrl_pressed=true;app.canvas_input(event,Vector2(960,540))
func motion(delta: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.relative=delta;app.canvas_input(event,Vector2(960,540))
func release(index: int) -> void:
	var event:=InputEventMouseButton.new();event.button_index=index;app._input(event)
func physical(code: int,down: bool) -> void:
	var event:=InputEventKey.new();event.physical_keycode=code;event.keycode=code;event.pressed=down;Input.parse_input_event(event);Input.flush_buffered_events()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var prefs_path:=folder.path_join("display.cfg")
	app=load("res://main.tscn").instantiate();app.display_prefs_path=prefs_path;app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	if "--read" in args:
		var prefs:=ConfigFile.new();check(prefs.load(prefs_path)==OK and app.navigation_scheme=="orbit" and is_equal_approx(app.get_window().content_scale_factor,1.25),"fresh app restores orbit and125percent interface preference")
		check(prefs.get_value("unrelated","keep")=="preserved","saving navigation and scale preserves unrelated preferences")
		print("ORBIT_NAVIGATION_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.navigation_scheme=="fly","new users retain the existing fly controls")
	var asset:=folder.path_join("figure.glb");check(SceneIO.make_pose_fixture(asset)==OK and app.pose_editor.add_model(asset).is_empty(),"original skinned fixture loads")
	app.physics_editor.freeze_all();app.pose_editor.frame_model();var rig: RefCounted=app.renderer.active_model();app.mode.select(2);app.change_mode(2);app.set_frame(8)
	physical(KEY_RIGHT,true);physical(KEY_RIGHT,false);check(app.frame==9,"default Right advances exactly one frame")
	physical(KEY_LEFT,true);physical(KEY_LEFT,false);check(app.frame==8,"default Left returns exactly one frame")
	physical(KEY_SPACE,true);physical(KEY_SPACE,false);check(app.playing,"default Space starts synchronized preview")
	physical(KEY_SPACE,true);physical(KEY_SPACE,false);check(not app.playing,"default Space pauses preview")
	app.set_frame(8);app.frame_box.get_line_edit().grab_focus();physical(KEY_RIGHT,true);physical(KEY_RIGHT,false)
	check(app.frame==8,"numeric text focus blocks frame shortcuts");app.frame_box.get_line_edit().release_focus()
	app.mode.select(0);app.change_mode(0);var old_opacity: float=app.brush_opacity.value;app.brush_opacity.value=0
	press(MOUSE_BUTTON_LEFT);motion(Vector2(8,4));release(MOUSE_BUTTON_LEFT)
	check(not app.navigating and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE,"Draw mode never captures the 3D fly camera")
	app.brush_opacity.value=old_opacity;app.mode.select(2);app.change_mode(2)
	var keys: Array=app.keys.duplicate(true);var data: Dictionary=rig.data.duplicate(true);var history: int=app.history.size()
	var camera: Camera3D=app.renderer.camera;var old_position:=camera.global_position;var old_rotation:=camera.quaternion
	var initial_view: Dictionary=app.renderer.view_state();var expected: Image=await app.renderer.capture(app.keys,app.layers,8,true);app.renderer.restore_view(initial_view)
	press(MOUSE_BUTTON_LEFT);motion(Vector2(20,10));release(MOUSE_BUTTON_LEFT)
	check(camera.global_position==old_position and absf(camera.quaternion.dot(old_rotation))<.99999,"default Ctrl-left remains free mouse look")
	app.set_process(false);press(MOUSE_BUTTON_LEFT)
	physical(KEY_W,true);check(Input.is_physical_key_pressed(KEY_W),"engine input authority receives physical forward key")
	var fly_start: Vector3=camera.position;var fly_basis: Basis=camera.basis;app._process(.1)
	check(camera.position.distance_to(fly_start-fly_basis.z*.3)<.00001,"held W flies forward at the default speed")
	physical(KEY_D,true);fly_start=camera.position;app._process(.1)
	check(absf(camera.position.distance_to(fly_start)-.3)<.00001,"diagonal fly speed is normalized")
	physical(KEY_SHIFT,true);fly_start=camera.position;app._process(.1)
	check(absf(camera.position.distance_to(fly_start)-.8)<.00001,"Shift selects the documented faster fly speed")
	physical(KEY_W,false);physical(KEY_D,false);physical(KEY_SHIFT,false);fly_start=camera.position;app._process(.1)
	check(camera.position==fly_start,"released fly keys stop camera movement")
	physical(KEY_E,true);fly_start=camera.position;app._process(.1)
	check(camera.position.distance_to(fly_start+camera.basis.y*.3)<.00001,"E flies along the camera up axis")
	app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT);fly_start=camera.position;app._process(.1)
	check(not app.navigating and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE and camera.position==fly_start,"focus loss releases default fly capture even with a held key")
	physical(KEY_E,false);app.set_process(true)
	app.pose_editor.frame_model();app.show_display_settings();await settle()
	check(not app.navigation_choices.is_visible_in_tree(),"Simple Settings hides the optional camera scheme")
	app.set_advanced(true);check(app.navigation_choices.is_visible_in_tree(),"Advanced reveals the camera scheme")
	var prefs:=ConfigFile.new();prefs.set_value("unrelated","keep","preserved");prefs.save(prefs_path)
	app.navigation_choices.select(1);app.navigation_choices.item_selected.emit(1);app.display_dialog.hide();app.set_advanced(false)
	check(app.navigation_scheme=="orbit" and "Orbit:" in app.canvas.tooltip_text,"chosen orbit behavior remains active after returning to Simple")
	app.mode.select(1);app.change_mode(1);check("free fly" not in app.canvas.tooltip_text and "orbit" in app.canvas.tooltip_text,"Scene help describes the chosen orbit controls without contradictory fly instructions");app.mode.select(2);app.change_mode(2)
	var pivot: Vector3=app.orbit_pivot();var radius:=camera.global_position.distance_to(pivot);var projected:=camera.unproject_position(pivot)
	press(MOUSE_BUTTON_LEFT);check(app.orbit_control.active and app.navigating,"routed Ctrl-left begins orbit capture")
	motion(Vector2(60,20));check(absf(camera.global_position.distance_to(pivot)-radius)<.0001 and camera.unproject_position(pivot).distance_to(projected)<.01,"orbit preserves radius and target screen position")
	for i in range(100):motion(Vector2(1,-.2))
	check(absf(camera.global_basis.determinant()-1)<.00001 and absf(camera.global_position.distance_to(pivot)-radius)<.0001,"repeated orbit motion keeps a regular camera basis and radius")
	var during_wheel:=InputEventMouseButton.new();during_wheel.button_index=MOUSE_BUTTON_WHEEL_UP;during_wheel.pressed=true;during_wheel.ctrl_pressed=true;app.canvas_input(during_wheel,Vector2(960,540));motion(Vector2(2,1))
	check(app.orbit_control.active and app.orbit_control.action=="orbit" and camera.global_position.distance_to(pivot)<radius,"wheel dolly during an orbit keeps the active orbit gesture")
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	check(not app.navigating and not app.orbit_control.active and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE,"Escape releases orbit capture")
	old_position=camera.global_position;old_rotation=camera.quaternion;press(MOUSE_BUTTON_RIGHT);motion(Vector2(12,7));release(MOUSE_BUTTON_RIGHT)
	check(camera.global_position!=old_position and absf(camera.quaternion.dot(old_rotation))>.99999,"Ctrl-right pans without rotating")
	radius=camera.global_position.distance_to(app.orbit_pivot());var wheel:=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_UP;wheel.pressed=true;wheel.ctrl_pressed=true;app.canvas_input(wheel,Vector2(960,540))
	check(camera.global_position.distance_to(app.orbit_pivot())<radius and not app.navigating,"Ctrl-wheel dollies nearer without capturing the mouse")
	press(MOUSE_BUTTON_LEFT);var ctrl_up:=InputEventKey.new();ctrl_up.keycode=KEY_CTRL;app._input(ctrl_up)
	check(not app.navigating and not app.orbit_control.active,"releasing Ctrl ends an orbit gesture")
	press(MOUSE_BUTTON_LEFT);app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(not app.navigating and not app.orbit_control.active,"focus loss releases orbit capture")
	var before: Transform3D=camera.global_transform;app.orbit_control.begin(camera,app.orbit_pivot(),"orbit");app.orbit_control.motion(camera,Vector2(NAN,0));app.orbit_control.end()
	check(camera.global_transform==before,"nonfinite pointer motion cannot damage the camera")
	check(not app.orbit_control.begin(camera,camera.global_position,"orbit"),"a pivot at the camera refuses safely")
	var alt:=InputEventKey.new();alt.keycode=KEY_ALT;alt.pressed=true;app._input(alt)
	check(app.pose_editor.reveal_bones,"Alt still reveals bones with orbit selected")
	alt.pressed=false;app._input(alt);check(not app.pose_editor.reveal_bones,"Alt release still hides the full skeleton")
	var operation: int=app.pose_editor.operation.selected;var middle:=InputEventMouseButton.new();middle.button_index=MOUSE_BUTTON_MIDDLE;middle.position=app.canvas.image_rect().get_center();middle.pressed=true;app.canvas._gui_input(middle);middle.pressed=false;app.canvas._gui_input(middle)
	check(app.pose_editor.operation.selected!=operation and not app.navigating,"middle click still switches pose tools with orbit selected")
	var original_view: Transform3D=camera.global_transform;var pole_point:=Vector3.ZERO
	camera.global_position=Vector3(0,5*sin(deg_to_rad(80)),5*cos(deg_to_rad(80)));camera.look_at(pole_point,Vector3.UP)
	app.orbit_control.begin(camera,pole_point,"orbit");app.orbit_control.motion(camera,Vector2(0,-10000));app.orbit_control.end()
	check(camera.global_position.z>0,"a large pitch gesture cannot jump over the vertical pole")
	camera.global_transform=original_view
	app.world_selection.clear();check(app.orbit_pivot().distance_to(camera.global_position)>4.99,"no selection uses a bounded point ahead of the view")
	check(app.keys==keys and rig.data==data and app.history.size()==history,"navigation does not author shot keys, model edits or Undo entries")
	app.show_display_settings();app.set_advanced(true)
	var scale: OptionButton
	for child in app.display_dialog.get_children():
		if child is VBoxContainer:
			for item in child.get_children():
				if item is OptionButton:scale=item;break
	scale.select(1);scale.item_selected.emit(1);await settle();app.get_viewport().get_texture().get_image().save_png(folder.path_join("orbit-settings.png"))
	prefs.load(prefs_path);check(prefs.get_value("navigation","scheme")=="orbit" and prefs.get_value("display","percent")==125 and prefs.get_value("unrelated","keep")=="preserved","scale updates retain navigation and other preference values")
	app.display_dialog.hide();check((await app.renderer.capture(app.keys,app.layers,8,true)).get_data()==expected.get_data(),"temporary orbiting leaves final shot pixels unchanged")
	var saved:=folder.path_join("orbit-scene.has");app.has_project.cache_root=folder.path_join("cache");app.has_project.save_file(saved,"packed")
	while app.has_project.pid>0:await process_frame
	check(app.has_project.path==saved,"navigated scene saves through ordinary packed HAS")
	app.new_project();app.has_project.open_file(saved)
	while app.has_project.pid>0:await process_frame
	await settle();check(app.navigation_scheme=="orbit" and (await app.renderer.capture(app.keys,app.layers,8,true)).get_data()==expected.get_data(),"reopening HAS keeps personal navigation and exact authored shot pixels")
	if "--original-only" not in args:
		app.new_project();app.has_project.open_file(folder.path_join("native.has"))
		while app.has_project.pid>0:await process_frame
		await settle();var native: RefCounted
		for row in app.current_world().objects:
			if row.kind=="model":app.world_selection.select_entity(row.id);native=app.renderer.active_model();break
		check(native!=null and native.order.size()>100,"real packed Miku is available for native orbit acceptance")
		if native:
			app.mode.select(2);app.change_mode(2);app.pose_editor.frame_model();var native_before: Dictionary=native.data.duplicate(true);var native_keys: Array=app.keys.duplicate(true)
			var center: Vector3=app.orbit_pivot();var distance:=camera.global_position.distance_to(center)
			press(MOUSE_BUTTON_LEFT);motion(Vector2(45,15));release(MOUSE_BUTTON_LEFT)
			check(absf(camera.global_position.distance_to(center)-distance)<.0001 and native.data==native_before and app.keys==native_keys,"posed native Miku orbits without changing its joints or authored camera")
	else:print("UNRUN native orbit acceptance: original-only software run")
	var result:={"checks":checks,"failures":failures,"prefs":prefs_path,"native_checks_unrun":"--original-only" in args};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("ORBIT_NAVIGATION_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
