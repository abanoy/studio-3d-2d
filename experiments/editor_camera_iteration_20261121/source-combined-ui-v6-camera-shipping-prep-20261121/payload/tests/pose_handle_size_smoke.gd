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
func vector_data(value: Vector2) -> Array:return [value.x,value.y]
func rectangle_data(value: Rect2) -> Dictionary:return {"position":vector_data(value.position),"size":vector_data(value.size),"end":vector_data(value.end)}
func transform_data(value: Transform2D) -> Dictionary:return {"x":vector_data(value.x),"y":vector_data(value.y),"origin":vector_data(value.origin),"determinant":value.determinant()}
func clip_diagnostic(canvas,to_image: Transform2D,image: Image) -> Dictionary:
	var physical_image:=Rect2(Vector2.ZERO,Vector2(image.get_size()))
	var canvas_image: Rect2=to_image*Rect2(Vector2.ZERO,canvas.size)
	var visible: Rect2=canvas_image.intersection(physical_image)
	var clips: Array=[];var ancestor: Node=canvas
	while ancestor!=null:
		if ancestor is Control:
			var control: Control=ancestor
			var mapping: Transform2D=root.get_stretch_transform()*control.get_global_transform_with_canvas()
			var bounds: Rect2=mapping*Rect2(Vector2.ZERO,control.size)
			clips.append({"path":str(control.get_path()),"clip_contents":control.clip_contents,"physical_rect":rectangle_data(bounds),"local_to_image":transform_data(mapping)})
			if control.clip_contents:visible=visible.intersection(bounds)
		ancestor=ancestor.get_parent()
	var scene: Rect2=canvas.scene_rect();var frame: Rect2=canvas.image_rect()
	return {"image_rect":rectangle_data(physical_image),"canvas_local_size":vector_data(canvas.size),"canvas_image_rect":rectangle_data(canvas_image),"visible_canvas_image_rect":rectangle_data(visible),"scene_local_rect":rectangle_data(scene),"scene_image_rect":rectangle_data(to_image*scene),"frame_local_rect":rectangle_data(frame),"frame_image_rect":rectangle_data(to_image*frame),"visible_scene_image_rect":rectangle_data(visible.intersection(to_image*scene)),"ancestor_controls":clips}
func closest_handle_distance(native_point: Vector2,handle: Dictionary,native_to_screen: Transform2D) -> float:
	var point: Vector2=native_to_screen*native_point;var result:=INF
	for index in range(handle.points.size()-1):
		var start: Vector2=native_to_screen*handle.points[index];var end: Vector2=native_to_screen*handle.points[index+1]
		result=minf(result,point.distance_to(Geometry2D.get_closest_point_to_segment(point,start,end)))
	return result
func visible_probe_angles(center: Vector2,visible: Rect2) -> Array[float]:
	# The 7x7 white_near kernel must fit on both radii; preserve 180/205px.
	var room: Rect2=visible.grow(-8.)
	var candidates: Array[float]=[]
	for index in range(192):
		var angle: float=.03+TAU*float(index)/192.
		var radial:=Vector2(cos(angle),sin(angle))
		if room.has_point(center+radial*180.) and room.has_point(center+radial*205.):candidates.append(angle)
	var selected: Array[float]=[]
	if candidates.size()<6:return selected
	for index in range(6):selected.append(candidates[floori(float(index)*candidates.size()/6.)])
	return selected
func clipped_probe_angle(center: Vector2,visible: Rect2,image: Image) -> float:
	# Retain the historical sample arcs as explicit clipping controls.
	var image_bounds:=Rect2(Vector2.ZERO,Vector2(image.get_size())).grow(-8.)
	for angle in [.35,.8,1.25,1.7,2.15,2.6]:
		var point: Vector2=center+Vector2(cos(angle),sin(angle))*180.
		if image_bounds.has_point(point) and not visible.grow(8.).has_point(point):return float(angle)
	return -1.
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
			var center_image: Vector2=to_image*(frame.position+center/app.canvas.resolution*frame.size)
			var image:=root.get_texture().get_image();var white_hits:=0;var wrong_band_hits:=0
			var clip_info: Dictionary=clip_diagnostic(app.canvas,to_image,image)
			var visible_info: Dictionary=clip_info.visible_scene_image_rect
			var visible_scene:=Rect2(Vector2(visible_info.position[0],visible_info.position[1]),Vector2(visible_info.size[0],visible_info.size[1]))
			var samples: Array=[];var image_name: String="handle-case-"+str(cases.size())+".png"
			var image_error: Error=image.save_png(folder.path_join(image_name))
			if image_error!=OK:push_error("Cannot save handle diagnostic image")
			var visible_angles: Array[float]=visible_probe_angles(center_image,visible_scene)
			check(visible_angles.size()==6,"six_distinct_180_and_205_probes_fit_inside_the_actual_visible_scene_with_margin")
			for angle in visible_angles:
				var radial:=Vector2(cos(angle),sin(angle))
				if white_near(image,center_image+radial*180.):white_hits+=1
				if white_near(image,center_image+radial*205.):wrong_band_hits+=1
				samples.append({"angle":angle,"sample180_image":vector_data(center_image+radial*180.),"sample205_image":vector_data(center_image+radial*205.),"sample180_inside_visible_scene":visible_scene.has_point(center_image+radial*180.),"sample205_inside_visible_scene":visible_scene.has_point(center_image+radial*205.),"white180":white_near(image,center_image+radial*180.),"white205":white_near(image,center_image+radial*205.)})
			check(white_hits==6 and wrong_band_hits==0,"all_six_visible_ring_samples_keep_180_screen_radius_and_no_205_pixels_at_"+str(extent)+"_scale_"+str(interface_scale))
			var metric: Dictionary=editor.handle_metrics();var pixels_per_native: float=metric.native_to_screen.x.length()
			var native_to_screen: Transform2D=metric.native_to_screen
			var pick_angle: float=visible_angles[0] if not visible_angles.is_empty() else 0.
			var radial:=Vector2(cos(pick_angle),sin(pick_angle))
			var pick_center_screen: Vector2=native_to_screen*center
			var near: Vector2=native_to_screen.affine_inverse()*(pick_center_screen+radial*(metric.view_screen_pixels+metric.hit_pixels-2.))
			var near_local: Vector2=frame.position+near/app.canvas.resolution*frame.size
			var near_image: Vector2=to_image*near_local
			var near_allowed: bool=app.canvas.scene_contains(near)
			var near_distance: float=closest_handle_distance(near,view,native_to_screen)
			pointer(near,true);check(editor.dragging,"the_larger_visible_ring_accepts_its_physical_grabbing_band")
			var near_dragging: bool=editor.dragging
			editor.finish_drag(true);app.world_selection.cancel_gesture(true);pointer(near,false)
			app.world_selection.select_entity(actor_id,false);editor.selected="@root";editor.update_gizmo()
			var far: Vector2=native_to_screen.affine_inverse()*(pick_center_screen+radial*(metric.view_screen_pixels+metric.hit_pixels+5.))
			pointer(far,true);check(not editor.dragging,"outside_the_physical_grabbing_band_does_not_start_rotation")
			if editor.dragging:editor.finish_drag(true)
			app.world_selection.cancel_gesture(true);pointer(far,false)
			check(near_allowed and app.canvas.scene_contains(far) and visible_scene.has_point(near_image) and near_distance<metric.hit_pixels and closest_handle_distance(far,view,native_to_screen)>metric.hit_pixels,"near_and_far_grabs_are_visible_with_unchanged_inside_and_outside_physical_distances")
			var clipped_test: Dictionary={}
			if extent==Vector2i(1600,1000) and is_equal_approx(interface_scale,1.5):
				var clipped_angle: float=clipped_probe_angle(center_image,visible_scene,image)
				var clipped_radial:=Vector2(cos(clipped_angle),sin(clipped_angle))
				var clipped_image: Vector2=center_image+clipped_radial*180.
				check(clipped_angle>=0. and not white_near(image,clipped_image),"a_historical_clipped_180px_arc_is_absent_outside_the_focus_frame")
				var clipped_near: Vector2=native_to_screen.affine_inverse()*(pick_center_screen+clipped_radial*(metric.view_screen_pixels+metric.hit_pixels-2.))
				check(not app.canvas.scene_contains(clipped_near) and closest_handle_distance(clipped_near,view,native_to_screen)<metric.hit_pixels,"clipped_arc_inside_distance_band_is_outside_the_editable_scene")
				var clipped_before:=var_to_bytes([actor.data,app.keys,app.history])
				pointer(clipped_near,true)
				check(not editor.dragging and var_to_bytes([actor.data,app.keys,app.history])==clipped_before,"clipped_arc_refuses_drag_without_changing_authored_state")
				clipped_test={"angle":clipped_angle,"image_point":vector_data(clipped_image),"white_at_180":white_near(image,clipped_image),"near_native":vector_data(clipped_near),"scene_contains":app.canvas.scene_contains(clipped_near),"minimum_ring_distance_screen":closest_handle_distance(clipped_near,view,native_to_screen),"started_drag":editor.dragging,"assertions":3}
				if editor.dragging:editor.finish_drag(true)
				app.world_selection.cancel_gesture(true);pointer(clipped_near,false)
			var ring_image_points: Array=[]
			for ring_point in view.points:
				var ring_native: Vector2=ring_point
				ring_image_points.append(vector_data(to_image*(frame.position+ring_native/app.canvas.resolution*frame.size)))
			var measurement: Dictionary={"visible_probe_angles":visible_angles,"pick_angle":pick_angle,"clipped_test":clipped_test,"image":image_name,"image_save_error":image_error,"image_size":[image.get_width(),image.get_height()],"root_size":vector_data(Vector2(root.size)),"root_visible_rect":rectangle_data(root.get_visible_rect()),"root_content_scale_factor":root.content_scale_factor,"root_stretch_transform":transform_data(root.get_stretch_transform()),"root_screen_transform":transform_data(root.get_screen_transform()),"canvas_global_with_canvas":transform_data(app.canvas.get_global_transform_with_canvas()),"canvas_viewport_screen_transform":transform_data(app.canvas.get_viewport().get_screen_transform()),"canvas_to_image":transform_data(to_image),"native_to_screen":transform_data(native_to_screen),"metric_radius_native":metric.radius,"metric_view_radius_native":metric.view_radius,"metric_axis_screen_pixels":metric.axis_screen_pixels,"metric_view_screen_pixels":metric.view_screen_pixels,"metric_hit_pixels":metric.hit_pixels,"pixels_per_native":pixels_per_native,"native_resolution":vector_data(app.canvas.resolution),"center_native":vector_data(center),"center_image":vector_data(center_image),"center_screen":vector_data(native_to_screen*center),"ring_point8_native":vector_data(view.points[8]),"ring_image_points":ring_image_points,"samples":samples,"clipping":clip_info,"near_native":vector_data(near),"near_canvas":vector_data(near_local),"near_image":vector_data(near_image),"near_screen":vector_data(native_to_screen*near),"near_scene_contains":near_allowed,"near_inside_visible_scene":visible_scene.has_point(near_image),"near_minimum_ring_distance_screen":near_distance,"near_started_drag":near_dragging,"far_native":vector_data(far),"far_scene_contains":app.canvas.scene_contains(far),"scene_setup":app.canvas.scene_setup,"canvas_zoom":app.canvas.zoom,"canvas_pan":vector_data(app.canvas.pan)}
			cases.append({"window":str(extent),"interface_scale":interface_scale,"ring_pixel_hits":white_hits,"wrong_band_hits":wrong_band_hits,"measurement":measurement})
	check(authored==var_to_bytes([actor.data,app.keys,app.video,app.history]),"interface_preferences_do_not_change_model_camera_video_or_history")
	check(FileAccess.get_sha256(fixture)==source_sha,"gizmo_size_never_rewrites_the_source_skin")
	app.free();await settled()
	var reader=load("res://main.tscn").instantiate();reader.recovery_root=folder.path_join("recovery-reader");reader.recent_path=folder.path_join("recent-reader.json");reader.display_prefs_path=pref_path;root.add_child(reader);await settled()
	check(reader.pose_editor.handle_size_percent==200,"fresh_editor_instance_restores_saved_handle_preference")
	var report:={"checks":checks,"failures":failures,"cases":cases,"historical_assertions":27,"visible_geometry_assertions":8,"clipped_arc_assertions":3,"pixel_requirement":"six_visible_white180_zero_white205","application_adopted":false,"owner_hand_comfort_certified":false}
	var output:=FileAccess.open(folder.path_join("handle-size-result.json"),FileAccess.WRITE);output.store_string(JSON.stringify(report));output.close()
	print("HANDLE_SIZE_SMOKE "+JSON.stringify(report));reader.free();quit(0 if failures==0 else 1)
