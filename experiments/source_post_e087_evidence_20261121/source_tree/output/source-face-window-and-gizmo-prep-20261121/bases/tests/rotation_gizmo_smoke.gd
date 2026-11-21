extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var folder: String
var checks:=0
var failures:=0
var cases: Array=[]
var view_cases: Array=[]
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Rotation regression watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func same_json_state(a,b) -> bool:
	# JSON readers can choose adjacent double values for the same full-precision
	# decimal. Keep structure exact and allow only sub-float32 scalar differences.
	if a is Dictionary and b is Dictionary:
		if a.size()!=b.size():return false
		for key in a:
			if not b.has(key) or not same_json_state(a[key],b[key]):return false
		return true
	if a is Array and b is Array:
		if a.size()!=b.size():return false
		for index in range(a.size()):
			if not same_json_state(a[index],b[index]):return false
		return true
	if (a is float or a is int) and (b is float or b is int):return absf(float(a)-float(b))<=0.000000000001
	return a==b
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
	app.scene_view.set_setup(false,false)
	if "--read" in OS.get_cmdline_user_args():await cold_read();return
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
				check(editor.handles.filter(func(h):return not h.get("view",false)).size()==1,"axis lock exposes only the intended RGB ring")
				if editor.handles.filter(func(h):return not h.get("view",false)).size()!=1:continue
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
	view_rotation(baseline)
	check(app.keys==keys and FileAccess.get_sha256(fixture)==original,"view-relative edits preserve camera keys and original skin bytes")
	await save_view_pose(baseline)
	await clipping()
	var report:={"checks":checks,"failures":failures,"cases":cases,"view_cases":view_cases,"folder":folder}
	var output:=FileAccess.open("res://output/rotation-gizmo-result.json",FileAccess.WRITE);output.store_string(JSON.stringify(report));output.close()
	print("ROTATION_GIZMO "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
func view_rotation(baseline: Dictionary) -> void:
	var editor=app.pose_editor;var rig: RefCounted=editor.active_rig();var camera: Camera3D=app.renderer.camera;var arm:=""
	for id in rig.order:
		if "arm" in str(rig.bones[id].name).to_lower():arm=id
	check(not arm.is_empty(),"view-ring fixture includes an actual skinned child bone")
	if arm.is_empty():return
	for eye in [Vector3(3,2.2,4),Vector3(-3,1.7,-4),Vector3(1,3,2)]:
		camera.position=eye;camera.look_at(Vector3(0,0.5,0));camera.rotate_object_local(Vector3.BACK,0.4)
		for selected in ["@root",arm]:
			for space in [0,1]:
				for direction in [-1.,1.]:
					rig.data=baseline.duplicate(true);editor.selected=selected;editor.space.select(space);editor.operation.select(0);editor.apply_frame()
					for lock in editor.locks:lock.button_pressed=false
					editor.update_gizmo();var views: Array=editor.handles.filter(func(h):return h.get("view",false))
					check(views.size()==1 and editor.handles.filter(func(h):return not h.get("view",false)).size()==3,"three RGB handles remain alongside one view-relative ring")
					if views.size()!=1:continue
					var view: Dictionary=views[0];var transform: Transform3D=rig.bone_transform(selected);var center: Vector2=camera.unproject_position(transform.origin);var radius_error:=0.
					for p in view.points:radius_error=maxf(radius_error,absf(p.distance_to(center)-90.))
					check(radius_error<0.05 and view.axis.is_equal_approx(camera.global_basis.z.normalized()),"outer ring stays circular and camera-facing in either axis mode")
					var radial: Vector3=(camera.global_basis.x*cos(PI/4)+camera.global_basis.y*sin(PI/4))*view.units
					var marker: Vector3=transform.affine_inverse()*(transform.origin+radial)
					var start: Vector2=camera.unproject_position(transform.origin+radial)
					var end: Vector2=camera.unproject_position(transform.origin+Quaternion(view.axis,direction*0.35)*radial)
					pointer(start,true);check(editor.dragging and editor.drag_axis.is_equal_approx(view.axis),"actual outer-ring click chooses the camera-relative axis")
					motion(end);var projected: Vector2=camera.unproject_position(rig.bone_transform(selected)*marker);var error:=projected.distance_to(end)
					check(error<0.75,"root and child-bone references follow left/right view rotation under rolled cameras")
					var posed: Dictionary=rig.data.duplicate(true);var history: int=app.history.size();pointer(end,false)
					check(not editor.dragging and app.history.size()==history+1,"view rotation releases as one ordinary history command")
					app.undo();check(rig.data==baseline,"view-ring Undo restores exact pose data")
					app.redo();check(rig.data==posed,"view-ring Redo restores exact pose data")
					app.undo();view_cases.append({"eye":str(eye),"selected":selected,"space":space,"direction":direction,"pixel_error":error,"circle_error":radius_error})
	rig.data=baseline.duplicate(true);editor.selected="@root";editor.apply_frame()
	for axis in range(3):
		for index in range(3):editor.locks[index].button_pressed=index==axis
		editor.update_gizmo();var view: Dictionary=editor.handles.filter(func(h):return h.get("view",false))[0]
		var history: int=app.history.size();pointer(view.points[8],true);app.world_selection.cancel_gesture();motion(view.points[16]);pointer(view.points[16],false)
		check(not view.enabled and not editor.dragging and rig.data==baseline and app.history.size()==history,"a locked axis disables outer-ring posing without bypassing the lock")
	for lock in editor.locks:lock.button_pressed=false
	editor.operation.select(1);editor.update_gizmo()
	check(editor.handles.size()==3 and editor.handles.all(func(h):return not h.get("view",false)),"Move mode retains only its three ordinary axis controls")
	editor.operation.select(0);editor.update_gizmo();var view: Dictionary=editor.handles.filter(func(h):return h.get("view",false))[0]
	var transform: Transform3D=rig.bone_transform("@root");var radial: Vector3=camera.global_basis.x*view.units
	editor.snap.button_pressed=true;pointer(camera.unproject_position(transform.origin+radial),true)
	motion(camera.unproject_position(transform.origin+Quaternion(view.axis,deg_to_rad(17.))*radial))
	check(absf(Timeline.quaternion(rig.data.rotation_xyzw).dot(Quaternion(view.axis,deg_to_rad(15.))))>0.99999,"the outer ring honors the existing 15-degree snap control")
	editor.finish_drag(true);editor.snap.button_pressed=false;check(rig.data==baseline,"cancelling view rotation restores exact authored data")
func save_view_pose(baseline: Dictionary) -> void:
	var editor=app.pose_editor;var rig: RefCounted=editor.active_rig();var camera: Camera3D=app.renderer.camera
	rig.data=baseline.duplicate(true);editor.selected="@root";editor.auto_key.button_pressed=true;editor.apply_frame();editor.update_gizmo()
	var view: Dictionary=editor.handles.filter(func(h):return h.get("view",false))[0];var origin: Vector3=view.world.origin;var radial: Vector3=camera.global_basis.x*view.units
	var start:=camera.unproject_position(origin+radial);var end:=camera.unproject_position(origin+Quaternion(view.axis,0.3)*radial)
	pointer(start,true);motion(end);pointer(end,false)
	check(rig.authored_keys().size()==1 and rig.authored_keys()[0].frame==app.frame,"normal auto-key records a view-relative pose at the current frame")
	var expected:={"keys":rig.authored_keys().duplicate(true),"transform":rig.sample_transform(app.frame),"object_id":rig.data.id}
	var out:=FileAccess.open(folder.path_join("view-expected.json"),FileAccess.WRITE);out.store_string(JSON.stringify(expected,"",true,true));out.close()
	app.has_project.cache_root=folder.path_join("cache-writer");app.has_project.save_file(folder.path_join("View-relative pose.has"),"packed")
	while app.has_project.pid>0:await process_frame
	check(FileAccess.file_exists(folder.path_join("View-relative pose.has")) and not app.dirty,"ordinary packed Save stores the view-relative key")
	await settled();root.get_texture().get_image().save_png(folder.path_join("view-ring-reference.png"))
func cold_read() -> void:
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("view-expected.json")))
	app.has_project.cache_root=folder.path_join("cache-reader");app.has_project.open_file(folder.path_join("View-relative pose.has"))
	while app.has_project.pid>0:await process_frame
	await settled();var rig: RefCounted=app.renderer.world_runtime.instance(expected.object_id)
	check(rig!=null,"fresh process opens the packed view-relative pose")
	if rig:
		check(same_json_state(rig.authored_keys(),expected.keys),"cold reopen retains recorded view-relative keys within JSON scalar precision")
		check(same_json_state(rig.sample_transform(app.frame),expected.transform),"cold reopen retains the sampled view-relative transform within JSON scalar precision")
		app.world_selection.select_entity(rig.data.id);app.mode.select(2);app.change_mode(2);app.pose_editor.update_gizmo()
		check(app.pose_editor.handles.any(func(h):return h.get("view",false)),"fresh reopened project exposes the camera-facing ring")
	var result:={"checks":checks,"failures":failures,"json_scalar_tolerance":0.000000000001};var out:=FileAccess.open("res://output/rotation-gizmo-cold-result.json",FileAccess.WRITE);out.store_string(JSON.stringify(result));out.close()
	print("ROTATION_GIZMO_COLD "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
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
