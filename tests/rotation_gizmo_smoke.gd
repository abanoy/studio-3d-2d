extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var folder: String
var checks:=0
var failures:=0
var cases: Array=[]
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Rotation regression watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func pointer(point: Vector2,pressed: bool) -> void:
	var rect: Rect2=app.canvas.image_rect();var e:=InputEventMouseButton.new()
	e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed;e.position=rect.position+point/app.canvas.resolution*rect.size
	app.canvas._gui_input(e)
func motion(point: Vector2) -> void:
	var rect: Rect2=app.canvas.image_rect();var e:=InputEventMouseMotion.new()
	e.position=rect.position+point/app.canvas.resolution*rect.size;e.button_mask=MOUSE_BUTTON_MASK_LEFT
	app.canvas._gui_input(e)
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	var fixture:=folder.path_join("original-rig.glb")
	check(SceneIO.make_pose_fixture(fixture)==OK,"ordinary skinned fixture is created without owner assets")
	var placement: Dictionary=app.import_actions.placement();placement.physics_on_import=false
	check(app.pose_editor.add_model(fixture,0,placement).is_empty(),"ordinary Add model loads the fixture")
	app.world_selection.select_entity(app.last_import_id);app.mode.select(2);app.change_mode(2)
	var editor=app.pose_editor;var rig: RefCounted=editor.active_rig();editor.selected="@root";editor.auto_key.button_pressed=false;editor.operation.select(0);editor.space.select(1)
	# Use a neutral transform only for this newly generated, owned fixture.
	rig.data.position=[0,0,0];rig.data.rotation_xyzw=[0,0,0,1];rig.data.scale=1.;editor.apply_frame()
	var baseline: Dictionary=rig.data.duplicate(true);var keys: Array=app.keys.duplicate(true);var original:=FileAccess.get_sha256(fixture)
	var camera: Camera3D=app.renderer.camera
	for eye in [Vector3(3,2.2,4),Vector3(-3,1.7,-4)]:
		camera.position=eye;camera.look_at(Vector3(0,0.5,0))
		for axis in range(3):
			for quadrant in [6,18,30,42]:
				rig.data=baseline.duplicate(true);editor.selected="@root";editor.apply_frame()
				for index in range(3):editor.locks[index].button_pressed=index!=axis
				editor.update_gizmo()
				check(editor.handles.size()==1,"axis lock exposes only the intended ring")
				if editor.handles.size()!=1:continue
				var handle: Dictionary=editor.handles[0];var origin: Vector3=handle.world.origin;var basis: Basis=Basis.IDENTITY
				var parameter: float=TAU*quadrant/48.;var radial: Vector3=(basis[(axis+1)%3]*cos(parameter)+basis[(axis+2)%3]*sin(parameter))*handle.units
				var local_marker: Vector3=rig.root.to_local(origin+radial)
				var start: Vector2=camera.unproject_position(origin+radial);var end: Vector2=camera.unproject_position(origin+Quaternion(handle.axis,0.25)*radial)
				pointer(start,true);check(editor.dragging,"actual canvas press starts the projected ring")
				motion(end)
				var projected: Vector2=camera.unproject_position(rig.root.to_global(local_marker));var error:=projected.distance_to(end)
				check(error<0.75,"the actual model marker follows the requested ring arc from either side/quadrant")
				var history: int=app.history.size();pointer(end,false)
				check(not editor.dragging and app.history.size()==history+1,"release records one pose edit")
				app.undo();check(rig.data==baseline,"Undo restores the exact pre-drag authored state")
				cases.append({"axis":axis,"eye":str(eye),"quadrant":quadrant,"pixel_error":error})
	# Cross both angular wrap boundaries in one gesture; inspect real orientation.
	rig.data=baseline.duplicate(true);editor.selected="@root";editor.apply_frame();camera.position=Vector3(3,2.2,4);camera.look_at(Vector3(0,0.5,0))
	for index in range(3):editor.locks[index].button_pressed=index!=2
	editor.update_gizmo();var handle: Dictionary=editor.handles[0];var origin: Vector3=handle.world.origin;var radial: Vector3=Vector3.RIGHT*handle.units
	var start: Vector2=camera.unproject_position(origin+radial);pointer(start,true)
	for degrees in [170.,190.,350.,370.]:motion(camera.unproject_position(origin+Quaternion(Vector3.BACK,deg_to_rad(degrees))*radial))
	var actual:=Timeline.quaternion(rig.data.rotation_xyzw);var expected:=Quaternion(Vector3.BACK,deg_to_rad(370.))
	check(absf(actual.dot(expected))>0.99999,"rotation remains continuous after passing half and full turns")
	editor.finish_drag(true);check(rig.data==baseline,"Escape/cancel restores the exact pose after an extended drag")
	# A projected edge-on ring still follows its local visible tangent.
	camera.position=Vector3(0,0,4);camera.look_at(Vector3.ZERO)
	for index in range(3):editor.locks[index].button_pressed=index!=1
	editor.update_gizmo();handle=editor.handles[0];start=handle.points[6]
	var tangent: Vector2=(handle.points[7]-handle.points[6]).normalized();var marker: Vector3=rig.root.to_local(origin+(Vector3.BACK*cos(PI/4)+Vector3.RIGHT*sin(PI/4))*handle.units)
	pointer(start,true);motion(start+tangent*8.)
	var movement: Vector2=camera.unproject_position(rig.root.to_global(marker))-start
	check(editor.dragging and movement.dot(tangent)>0 and is_finite(movement.x),"edge-on drag uses the visible tangent with a finite matching direction")
	editor.finish_drag(true)
	# Off-frame handles may exist mathematically, but must not start a drag.
	var depth: float=-camera.to_local(rig.root.global_position).z;var offscreen: Dictionary=baseline.duplicate(true);var position: Vector3=camera.project_position(Vector2(-160,540),depth)
	offscreen.position=[position.x,position.y,position.z];rig.data=offscreen;editor.apply_frame();editor.update_gizmo();app.canvas.zoom=0.6
	var outside: Vector2=editor.handles[0].points[6];check(outside.x<0,"off-frame handle setup is genuinely outside the output rectangle")
	pointer(outside,true);check(not editor.dragging and rig.data==offscreen,"a letterbox-margin click cannot grab an invisible rotation handle")
	app.world_selection.cancel_gesture();pointer(outside,false)
	rig.data=baseline.duplicate(true);editor.selected="@root";editor.apply_frame();editor.update_gizmo();app.canvas.zoom=1.
	# Existing global motion/release still handles a gesture leaving the frame.
	start=editor.handles[0].points[6];pointer(start,true);motion(Vector2(-40,540))
	check(editor.dragging,"an active ring gesture continues outside the image")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-10,-10);app._input(release)
	check(not editor.dragging,"global release safely ends a gesture outside the canvas")
	app.undo();check(rig.data==baseline and app.keys==keys and FileAccess.get_sha256(fixture)==original,"camera keys and original skin file remain unchanged")
	await clipping()
	var report:={"checks":checks,"failures":failures,"cases":cases,"folder":folder}
	var output:=FileAccess.open("res://output/rotation-gizmo-result.json",FileAccess.WRITE);output.store_string(JSON.stringify(report));output.close()
	print("ROTATION_GIZMO "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
func clipping() -> void:
	var probe=load("res://src/canvas_view.gd").new();probe.position=Vector2(24,24);probe.size=Vector2(600,600);root.add_child(probe)
	var background:=Image.create(16,16,false,Image.FORMAT_RGBA8);background.fill(Color(0.1,0.15,0.2));probe.background=ImageTexture.create_from_image(background)
	probe.zoom=0.65;probe.queue_redraw();await settled();var before:=root.get_texture().get_image()
	probe.pose_lines=[{"a":Vector2(-300,540),"b":Vector2(2200,540),"color":Color.RED}]
	probe.pose_joints=[{"point":Vector2(-200,540),"selected":true},{"point":Vector2(960,540),"selected":true}]
	probe.review_lines=PackedVector2Array([Vector2(960,-300),Vector2(960,1400)])
	probe.queue_redraw();await settled();var after:=root.get_texture().get_image();var frame: Rect2=probe.image_rect();var outside_changes:=0;var inside_changes:=0
	for y in range(2,598):
		for x in range(2,598):
			var point:=Vector2i(x+24,y+24)
			if before.get_pixelv(point)==after.get_pixelv(point):continue
			if frame.grow(2).has_point(Vector2(x,y)):inside_changes+=1
			else:outside_changes+=1
	check(outside_changes==0 and inside_changes>100,"actual line/joint/helper pixels clip to the white frame while remaining visible inside")
	before.save_png(folder.path_join("frame-overlay-before.png"));after.save_png(folder.path_join("frame-overlay-after.png"));probe.free()
