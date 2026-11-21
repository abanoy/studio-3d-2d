extends SceneTree
# Authored/unrun. Root must run with an owned private GPU desktop, never visibly.
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0
var app
var cases: Array=[]
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Handle size smoke watchdog");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+"handle_size."+label)
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func pointer(point: Vector2,pressed: bool) -> void:
	var frame: Rect2=app.canvas.image_rect();var event:=InputEventMouseButton.new()
	event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;event.position=frame.position+point/app.canvas.resolution*frame.size
	app.canvas._gui_input(event)
func white_near(image: Image,point: Vector2) -> bool:
	var center:=Vector2i(point.round())
	for y in range(center.y-3,center.y+4):
		for x in range(center.x-3,center.x+4):
			if x<0 or y<0 or x>=image.get_width() or y>=image.get_height():continue
			var color:=image.get_pixel(x,y)
			if color.r>.7 and color.g>.7 and color.b>.7:return true
	return false
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("Expected an owned output folder");quit(2);return
	var folder: String=args[0];var pref_path:=folder.path_join("prefs.cfg")
	root.size=Vector2i(1600,1000)
	var legacy:=ConfigFile.new();legacy.set_value("display","percent",100);legacy.set_value("display","theme","neon");legacy.set_value("navigation","scheme","orbit");legacy.set_value("sentinel","keep",23);legacy.set_value("pose","handle_percent","malformed")
	check(legacy.save(pref_path)==OK,"owned_legacy_preferences_are_created")
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=pref_path
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.pose_editor.handle_size_percent==150,"missing_or_invalid_handle_preference_uses_large_default")
	var read_only:=ConfigFile.new();read_only.load(pref_path)
	check(read_only.get_value("pose","handle_percent")=="malformed","reading_an_invalid_handle_preference_does_not_rewrite_it")
	var fixture:=folder.path_join("handle-fixture.glb")
	check(SceneIO.make_pose_fixture(fixture)==OK,"owned_skinned_fixture_is_generated")
	var source_sha:=FileAccess.get_sha256(fixture)
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	check(app.pose_editor.add_model(fixture,0,context).is_empty(),"normal_model_import_loads_fixture")
	app.mode.select(2);app.change_mode(2);app.scene_view.set_setup(false,false)
	var editor=app.pose_editor;var actor: RefCounted=editor.active_rig();var actor_id: String=actor.data.id
	actor.data.position=[0,0,0];actor.data.rotation_xyzw=[0,0,0,1];actor.data.scale=1.;editor.selected="@root";editor.operation.select(0);editor.space.select(1);editor.auto_key.button_pressed=false;editor.apply_frame()
	for lock in editor.locks:lock.button_pressed=false
	var camera: Camera3D=app.renderer.camera;camera.position=Vector3(0,0,4);camera.look_at(Vector3.ZERO)
	var authored:=var_to_bytes([actor.data,app.keys,app.video,app.history])
	app.show_display_settings();await settled()
	check(editor.handle_size_controls.size()==1 and editor.handle_size_controls[0].is_visible_in_tree(),"handle_size_setting_is_available_in_Simple_mode")
	var choices: OptionButton=editor.handle_size_controls[0];choices.select(4);choices.item_selected.emit(4);app.display_dialog.hide();await settled()
	check(editor.handle_size_percent==200 and root.content_scale_factor==1.,"actual_setting_signal_changes_handles_without_interface_zoom")
	var changed:=ConfigFile.new();changed.load(pref_path)
	check(changed.get_value("pose","handle_percent")==200 and changed.get_value("display","percent")==100 and changed.get_value("display","theme")=="neon" and changed.get_value("navigation","scheme")=="orbit" and changed.get_value("sentinel","keep")==23,"saving_the_handle_choice_preserves_other_preference_fields")
	for extent in [Vector2i(1600,1000),Vector2i(3440,1440)]:
		for interface_scale in [1.,1.5]:
			root.size=extent;root.content_scale_factor=interface_scale;await settled()
			app.world_selection.select_entity(actor_id,false);editor.selected="@root";editor.apply_frame();editor.update_gizmo();await settled()
			var views: Array=editor.handles.filter(func(handle):return handle.get("view",false))
			check(views.size()==1,"a_view_rotation_ring_survives_window_and_scale_changes")
			if views.size()!=1:continue
			var view: Dictionary=views[0];var center: Vector2=camera.unproject_position(actor.bone_transform("@root").origin)
			var frame: Rect2=app.canvas.image_rect();var to_image: Transform2D=root.get_stretch_transform()*app.canvas.get_global_transform_with_canvas()
			var center_image:=to_image*(frame.position+center/app.canvas.resolution*frame.size)
			var image:=root.get_texture().get_image();var white_hits:=0;var wrong_band_hits:=0
			for angle in [.35,.8,1.25,1.7,2.15,2.6]:
				var radial:=Vector2(cos(angle),sin(angle))
				if white_near(image,center_image+radial*180.):white_hits+=1
				if white_near(image,center_image+radial*205.):wrong_band_hits+=1
			check(white_hits>=5 and wrong_band_hits<=1,"actual_white_ring_pixels_keep_180_screen_radius_at_"+str(extent)+"_scale_"+str(interface_scale))
			var metric: Dictionary=editor.handle_metrics();var radial: Vector2=(view.points[8]-center).normalized();var pixels_per_native: float=metric.native_to_screen.x.length()
			var near: Vector2=view.points[8]+radial*(metric.hit_pixels-2.)/pixels_per_native
			pointer(near,true);check(editor.dragging,"the_larger_visible_ring_accepts_its_physical_grabbing_band")
			editor.finish_drag(true);app.world_selection.cancel_gesture(true);pointer(near,false)
			app.world_selection.select_entity(actor_id,false);editor.selected="@root";editor.update_gizmo()
			var far: Vector2=view.points[8]+radial*(metric.hit_pixels+5.)/pixels_per_native
			pointer(far,true);check(not editor.dragging,"outside_the_physical_grabbing_band_does_not_start_rotation")
			if editor.dragging:editor.finish_drag(true)
			app.world_selection.cancel_gesture(true);pointer(far,false)
			cases.append({"window":str(extent),"interface_scale":interface_scale,"ring_pixel_hits":white_hits,"wrong_band_hits":wrong_band_hits})
	check(authored==var_to_bytes([actor.data,app.keys,app.video,app.history]),"interface_preferences_do_not_change_model_camera_video_or_history")
	check(FileAccess.get_sha256(fixture)==source_sha,"gizmo_size_never_rewrites_the_source_skin")
	app.free();await settled()
	var reader=load("res://main.tscn").instantiate();reader.recovery_root=folder.path_join("recovery-reader");reader.recent_path=folder.path_join("recent-reader.json");reader.display_prefs_path=pref_path;root.add_child(reader);await settled()
	check(reader.pose_editor.handle_size_percent==200,"fresh_editor_instance_restores_saved_handle_preference")
	var report:={"checks":checks,"failures":failures,"cases":cases,"application_adopted":false,"owner_hand_comfort_certified":false}
	var output:=FileAccess.open(folder.path_join("handle-size-result.json"),FileAccess.WRITE);output.store_string(JSON.stringify(report));output.close()
	print("HANDLE_SIZE_SMOKE "+JSON.stringify(report));reader.free();quit(0 if failures==0 else 1)
