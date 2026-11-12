extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var helper
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Part picking watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func ready() -> void:
	while helper.pid>0:await process_frame
	await settle()
func global_point(point: Vector2) -> Vector2:
	var rect: Rect2=app.canvas.image_rect()
	return app.canvas.get_global_transform_with_canvas()*(rect.position+point/Vector2(app.video.width,app.video.height)*rect.size)
func button(point: Vector2,pressed: bool,index:=MOUSE_BUTTON_LEFT,ctrl:=false,mask:=-1) -> void:
	var event:=InputEventMouseButton.new();event.button_index=index;event.pressed=pressed;event.ctrl_pressed=ctrl
	event.button_mask=(1<<(index-1) if pressed else 0) if mask<0 else mask;event.position=global_point(point);event.global_position=event.position
	app.get_viewport().push_input(event,true)
func motion(point: Vector2,delta: Vector2,mask:=MOUSE_BUTTON_MASK_LEFT) -> void:
	var event:=InputEventMouseMotion.new();event.position=global_point(point);event.global_position=event.position;event.relative=delta;event.button_mask=mask
	app.get_viewport().push_input(event,true)
func key(code: int,pressed: bool) -> void:
	var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=pressed
	Input.parse_input_event(event);await process_frame
func click(point: Vector2) -> void:
	button(point,true);button(point,false);await ready()
func selected(primitive: int,component: int) -> bool:
	return not helper.preview.is_empty() and int(helper.preview.region.primitive)==primitive and int(helper.preview.region.component)==component
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var source: String=args[1]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	app.scene_view.set_setup(false,false)
	app.append_object(Model.definition(source),"model");await settle();app.mode.select(2);app.change_mode(2);app.set_advanced(false)
	var actor: RefCounted=app.renderer.active_model();var source_bones: Dictionary=actor.root.get_meta("has_source_bones",{});var head: String=source_bones.get(2,"")
	check(not head.is_empty(),"actual source Head binding is available")
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)]
	var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true);var sha:=FileAccess.get_sha256(source)
	helper=app.physics_editor.helper_editor;helper.open(true);await ready()
	check(selected(1,0),"ordinary strip remains the initial recommended review")
	var torso: Vector2=app.renderer.camera.unproject_position(Vector3(0,.8,0))
	await click(torso);check(selected(0,0),"a routed scene click selects the actual torso region")
	var strand: Vector2=app.renderer.camera.unproject_position(actor.bone_transform(head)*Vector3(.4,-.6,.1))
	await click(strand);check(selected(1,0),"a routed scene click guesses the independent hanging strip")
	app.canvas.zoom=1.15;app.canvas.pan=Vector2(12,-8);app.canvas.queue_redraw();await settle();await click(torso)
	check(selected(0,0),"part picking respects the scene canvas zoom and pan")
	var chosen: Dictionary=helper.request.duplicate(true);button(torso,true);button(Vector2(-50,-50),false);await ready()
	check(helper.request==chosen and not helper.part_press and app.world_selection.pending_button==0,"release outside the image cancels the guess without selecting another part")
	button(torso,true);var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app.get_viewport().push_input(escape,true);button(strand,false);await ready()
	check(helper.request==chosen and not helper.part_press and app.world_selection.pending_button==0,"Escape cancels a pending part click without applying it")
	button(torso,true);app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT);button(strand,false);await ready()
	check(helper.request==chosen and not helper.part_press and app.world_selection.pending_button==0,"focus loss cancels a pending part click")
	var camera: Transform3D=app.renderer.camera.transform;button(torso,true);motion(torso+Vector2(20,0),Vector2(20,0));await process_frame
	check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_LEFT,"a left drag enters ordinary camera movement")
	button(torso+Vector2(20,0),false);await ready()
	check(not app.navigating and app.camera_buttons==0 and helper.request==chosen and app.renderer.camera.transform!=camera,"left drag release keeps the selection and releases camera capture")
	app.renderer.camera.transform=camera;await settle();button(torso,true,MOUSE_BUTTON_LEFT,true);await process_frame
	check(app.navigating and app.camera_free and not helper.part_press,"Ctrl-left remains the free camera gesture")
	button(torso,false,MOUSE_BUTTON_LEFT,true);await settle();check(not app.navigating and helper.request==chosen,"Ctrl-left release does not choose a part")
	var pan: Vector2=app.canvas.pan;button(torso,true,MOUSE_BUTTON_MIDDLE);motion(torso+Vector2(0,10),Vector2(0,10),MOUSE_BUTTON_MASK_MIDDLE);await process_frame
	check(not app.navigating and app.canvas.pan!=pan,"Pose mode middle drag retains its existing canvas pan")
	button(torso,false,MOUSE_BUTTON_MIDDLE);app.canvas.pan=pan;app.mode.select(1);app.change_mode(1);await settle()
	button(torso,true,MOUSE_BUTTON_MIDDLE);motion(torso+Vector2(0,10),Vector2(0,10),MOUSE_BUTTON_MASK_MIDDLE);await process_frame
	check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_MIDDLE,"Camera mode middle drag retains camera navigation")
	button(torso,false,MOUSE_BUTTON_MIDDLE);app.mode.select(2);app.change_mode(2);await settle();button(torso,true,MOUSE_BUTTON_RIGHT);motion(torso+Vector2(12,0),Vector2(12,0),MOUSE_BUTTON_MASK_RIGHT);await process_frame
	check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_RIGHT,"right drag retains camera navigation");button(torso,false,MOUSE_BUTTON_RIGHT);await settle()
	app.renderer.camera.transform=camera;button(torso,true);await key(KEY_W,true);await process_frame;await process_frame
	check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_LEFT,"WASD with a pending left press starts normal camera movement")
	await key(KEY_W,false);button(torso,false);await ready();check(not app.navigating and helper.request==chosen,"WASD release keeps the reviewed part and releases capture")
	app.renderer.camera.transform=camera
	# Verify source bounds follow the current authored Head pose, not its bind location.
	helper.close();var q:=Quaternion(Vector3.UP,.32);actor.data.pose[head]={"position":[.6,.1,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]};app.pose_editor.apply_frame();app.changed();await settle()
	var posed: Dictionary=actor.data.duplicate(true);var posed_history: int=app.history.size();helper.open(true);await ready()
	strand=app.renderer.camera.unproject_position(actor.bone_transform(head)*Vector3(.4,-.6,.1));await click(strand)
	check(selected(1,0),"scene click follows actual translated and rotated source joint bounds")
	var correction:=-1
	for i in range(helper.assessment.regions.size()):
		if int(helper.assessment.regions[i].primitive)==1 and int(helper.assessment.regions[i].component)==1:correction=i
	helper.parts.select(correction);helper.parts.item_selected.emit(correction);await ready()
	check(correction>=0 and selected(1,1),"the list corrects a best-effort scene guess")
	helper.patch_toggle.button_pressed=true;helper.draw_preview();var point: Vector2=helper.projected_vertices[0]
	button(point,true);motion(point+Vector2(10,10),Vector2(10,10));check(helper.box_dragging and app.canvas.review_box_visible,"smaller-patch mode still owns its box gesture")
	helper.cancel_patch_drag();button(point,false);await settle()
	check(actor.data==posed and app.history.size()==posed_history and app.keys==shots and FileAccess.get_sha256(source)==sha,"picking, navigation and correction author no asset, pose, camera key or history")
	helper.window.get_texture().get_image().save_png(folder.path_join("review.png"));root.get_texture().get_image().save_png(folder.path_join("editor.png"));helper.close();await settle()
	check(not app.canvas.review_pointer.is_valid() and not helper.part_press,"closing review removes the part-click interceptor")
	# Separate Setup oracle: move actual source geometry to a virtual native pixel
	# beyond the output frame, while retaining the original camera projection.
	app.canvas.reparent(root);app.canvas.position=Vector2(12,12);app.canvas.size=Vector2(1200,360);app.canvas.z_index=100
	app.scene_view.set_setup(true,false);app.renderer.camera.transform=camera;await settle()
	var outside:=Vector2(-250,540);var wanted: Vector3=app.renderer.camera.project_position(outside,4.)
	var current: Vector3=actor.bone_transform(head)*Vector3(.4,-.6,.1);var shift: Vector3=wanted-current
	actor.data.position=[shift.x,shift.y,shift.z];app.pose_editor.apply_frame();app.changed();await settle()
	var setup_world: Dictionary=app.current_world().duplicate(true);var setup_history: int=app.history.size();var setup_keys: Array=app.keys.duplicate(true)
	helper.open(true);await ready()
	check(app.canvas.scene_setup and app.canvas.scene_contains(outside) and not Rect2(Vector2.ZERO,app.canvas.resolution).has_point(outside),"Setup test geometry lies visibly outside native output but inside the scene")
	await click(outside);check(selected(1,0),"a routed Setup click guesses the actual off-frame source strip")
	helper.parts.select(correction);helper.parts.item_selected.emit(correction);await ready()
	check(selected(1,1),"the list can correct an off-frame Setup guess")
	var setup_choice: Dictionary=helper.request.duplicate(true)
	button(outside,true,MOUSE_BUTTON_MIDDLE);motion(outside+Vector2(0,10),Vector2(0,10),MOUSE_BUTTON_MASK_MIDDLE);await process_frame
	check(app.navigating and app.camera_buttons==MOUSE_BUTTON_MASK_MIDDLE,"Pose middle drag navigates the 3D camera in Setup")
	button(outside,false,MOUSE_BUTTON_MIDDLE);await ready()
	check(not app.navigating and helper.request==setup_choice,"Setup middle release keeps the corrected selection and releases capture")
	check(app.current_world()==setup_world and app.history.size()==setup_history and app.keys==setup_keys and FileAccess.get_sha256(source)==sha,"off-frame Setup picking and navigation change no authored scene or source")
	root.get_texture().get_image().save_png(folder.path_join("setup-editor.png"));helper.close();app.scene_view.set_setup(false,false)
	app.new_project();app.append_object(Model.definition(args[2]),"model");await settle();app.mode.select(2);app.change_mode(2)
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));helper.open();await ready()
	check(not helper.preview.is_empty() and not helper.apply_button.disabled,"a different unconfigured area can be reviewed beside existing helper weights")
	strand=app.renderer.camera.unproject_position(Vector3(.4,1.4,.1));await click(strand)
	check(helper.preview.is_empty() and helper.apply_button.disabled and helper.info.text.contains("already has motion joints"),"clicking an already configured front part clears the previous Apply proposal")
	helper.patch_toggle.button_pressed=true;await ready()
	check(selected(1,0) and not helper.preview.can_apply and helper.apply_button.disabled,"smaller-patch correction starts on the clicked protected component without overwriting it")
	helper.close()
	var result:={"checks":checks,"failures":failures,"source_sha256":sha,"original_pose":before.pose,"posed_pose":posed.pose,"initial_history":history}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true));print("SECONDARY_PICK "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
