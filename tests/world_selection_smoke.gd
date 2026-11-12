extends SceneTree
const Support = preload("res://tests/world_test_support.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Timeline = preload("res://src/timeline.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	create_timer(90).timeout.connect(func(): push_error("Selection watchdog expired"); quit(2))
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	checks+=1; print(("PASS " if ok else "FAIL ")+text)
	if not ok: failures+=1

func settled() -> void:
	for i in range(3): await process_frame
	await RenderingServer.frame_post_draw

func click(app, point: Vector2, index := MOUSE_BUTTON_LEFT) -> void:
	var rect: Rect2=app.canvas.image_rect()
	for pressed in [true,false]:
		var e:=InputEventMouseButton.new();e.button_index=index;e.pressed=pressed
		e.position=rect.position+point/Vector2(1920,1080)*rect.size
		app.canvas._gui_input(e)
	await settled()

func green_pixels(image: Image) -> int:
	var bytes:=image.get_data();var count:=0
	for i in range(0,bytes.size(),4):
		if bytes[i]<95 and bytes[i+1]>180 and bytes[i+2]<160:count+=1
	return count

func id_point(image: Image, color: Vector3) -> Vector2:
	for y in range(50,image.get_height()-50):
		for x in range(50,image.get_width()-50):
			var pixel:=image.get_pixel(x,y)
			if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<0.001:return Vector2(x*2+1,y*2+1)
	return Vector2(-1,-1)

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/world-selection/run_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app)
	await settled()
	var selection=app.world_selection
	check(selection.selected.is_empty() and selection.items.is_empty() and selection.tree.get_selected()==null,"empty world hierarchy opens without a selection")
	var fixture:=folder.path_join("rig.glb");SceneIO.make_pose_fixture(fixture)
	app.pose_editor.add_model(fixture);await settled();app.pose_editor.frame_model()
	var model_key: String=Support.key(app,Support.rig(app))
	var camera: Camera3D=app.renderer.camera
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov)]
	await settled()
	check(selection.items.has(model_key) and selection.selected==model_key and selection.entries.size()==2,"imported shared model appears in hierarchy with skinned selection copies")
	var source_hash:=FileAccess.get_sha256(fixture)
	var rig=Support.rig(app)
	var original_materials:=[]
	for entry in selection.entries: original_materials.append([entry.original.layers,entry.original.get_active_material(0)])
	var final_before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	selection.select_entity("");await settled()
	var unselected:=root.get_texture().get_image()
	var transform: Transform3D=camera.transform
	var shot_keys:=JSON.stringify(app.keys)
	var point:=camera.unproject_position(Vector3(0.8,1,0))
	await click(app,point)
	check(selection.selected==model_key and app.mode.selected==2 and camera.transform==transform,"viewport click selects model and enters posing without moving camera")
	check(not app.navigating and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE and JSON.stringify(app.keys)==shot_keys,"short selection click does not capture mouse or alter shot keys")
	var highlighted:=root.get_texture().get_image();highlighted.save_png(folder.path_join("selected.png"))
	check(green_pixels(highlighted)>green_pixels(unselected)+20,"selected model has an actual green editor outline")
	var final_selected: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	final_before.save_png(folder.path_join("final-before.png"));final_selected.save_png(folder.path_join("final-selected.png"))
	var a:=final_before.get_data();var b:=final_selected.get_data();var changed:=0;var total:=0
	for i in range(a.size()):
		if a[i]!=b[i]:changed+=1;total+=absi(a[i]-b[i])
	print("SELECTION_FINAL_DIFFERENCE channels=",changed," mean=",float(total)/a.size())
	check(changed<=384 and float(total)/a.size()<0.002 and not camera.get_cull_mask_value(20),"selection is excluded from final frames within existing bounded GPU edge tolerance")
	var alt:=InputEventKey.new();alt.keycode=KEY_ALT;alt.pressed=true;app._input(alt);app.pose_editor.update_gizmo()
	check(app.pose_editor.reveal_bones and app.canvas.pose_joints.size()==2,"holding Alt reveals full joint structure")
	alt.pressed=false;app._input(alt);app.pose_editor.update_gizmo()
	check(not app.pose_editor.reveal_bones and app.canvas.pose_joints.size()<2 and app.pose_editor.handles.filter(func(handle):return not handle.get("view",false)).size()==3,"releasing Alt hides full skeleton while selected handles remain")
	var free_before:=JSON.stringify(rig.data)
	var handle_point: Vector2=app.pose_editor.handles[0].points[0]
	var free_event:=InputEventMouseButton.new();free_event.button_index=MOUSE_BUTTON_LEFT;free_event.pressed=true;free_event.ctrl_pressed=true
	var free_rect: Rect2=app.canvas.image_rect();free_event.position=free_rect.position+handle_point/Vector2(1920,1080)*free_rect.size
	app.canvas._gui_input(free_event)
	check(app.camera_free and app.navigating and not app.pose_editor.dragging,"Ctrl+LMB takes free-camera priority over selected pose handle")
	free_event.pressed=false;app.canvas._gui_input(free_event)
	check(not app.navigating and JSON.stringify(rig.data)==free_before,"free-camera release creates no accidental pose edit")
	var arm: String=rig.order[1]
	app.pose_editor.tree_items[arm].select(0);app.pose_editor.operation.select(0);app.pose_editor.refresh_values()
	var old_mask: Image=selection.viewport.get_texture().get_image()
	app.pose_editor.fields[2].value=65;app.pose_editor.apply_numeric();await settled()
	var posed_mask: Image=selection.viewport.get_texture().get_image()
	check(old_mask.get_data()!=posed_mask.get_data() and rig.authored_keys().size()==1,"selection mask follows actual skin deformation and normal auto-keying")
	app.undo();await settled()
	check(selection.viewport.get_texture().get_image().get_data()==old_mask.get_data(),"pose undo restores exact skinned selection mask")
	await click(app,point,MOUSE_BUTTON_RIGHT)
	check(selection.menu.visible and selection.selected==model_key,"right-click on entity opens actual object context menu")
	app.video["visibility_fade_ms"]=0 # This fixture checks fully hidden endpoint ghosts; default fades have their own suite.
	selection.context_action(2);await settled()
	var saved_visibility: bool=rig.visible_at(app.frame)
	check(not saved_visibility and selection.outline_material.get_shader_parameter("ghost"),"hidden selected model retains green ghost selection")
	var hidden_final: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var ghost:=root.get_texture().get_image();ghost.save_png(folder.path_join("hidden-ghost.png"))
	check(green_pixels(ghost)>20 and hidden_final.get_data()!=final_selected.get_data(),"hidden ghost remains editor-only and model stays absent in final frame")
	var hidden_mask: Image=selection.viewport.get_texture().get_image()
	app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[2].value+=35;app.pose_editor.apply_numeric();await settled()
	check(not rig.visible_at(app.frame) and hidden_mask.get_data()!=selection.viewport.get_texture().get_image().get_data(),"hidden selected model remains poseable without enabling visibility")
	app.undo();await settled()
	selection.clear();selection.items[model_key].select(0);await settled()
	check(selection.selected==model_key and not rig.visible_at(app.frame),"tree selects hidden model without changing visibility")
	app.pose_editor.set_visibility_key(true);await settled()
	app.pose_editor.tree_items[arm].select(0);app.pose_editor.operation.select(0);app.pose_editor.fields[2].value=45;app.pose_editor.apply_numeric()
	selection.context_action(1)
	check(rig.data.pose.is_empty() and rig.authored_keys()[0].pose.values().all(func(delta):return Timeline.vector(delta.position)==Vector3.ZERO and Timeline.quaternion(delta.rotation_xyzw).is_equal_approx(Quaternion.IDENTITY)),"context Reset pose records effective imported neutral transforms through manual auto-key")
	await click(app,Vector2(10,10),MOUSE_BUTTON_RIGHT)
	check(selection.selected.is_empty() and app.mode.selected==1 and not selection.menu.visible,"right-click empty space deselects and returns to free camera")
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_RIGHT;e.pressed=true;app.canvas._gui_input(e)
	var motion:=InputEventMouseMotion.new();motion.relative=Vector2(20,8);app.canvas._gui_input(motion)
	check(app.navigating and not camera.transform.is_equal_approx(transform),"right drag remains POV navigation after movement threshold")
	e.pressed=false;app._input(e);app.canvas._gui_input(e)
	check(not app.navigating and not selection.menu.visible,"right-drag release opens no context menu")
	e.button_index=MOUSE_BUTTON_LEFT;e.pressed=true;app.canvas._gui_input(e)
	app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(selection.pending_button==0 and not app.navigating and not app.pose_editor.reveal_bones,"focus loss clears pending click and skeleton reveal")
	camera.transform=transform
	selection.choose_at(point)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	await settled()
	check(selection.selected.is_empty() and selection.picking==0,"Escape invalidates in-flight GPU selection before it can select an object")
	check(FileAccess.get_sha256(fixture)==source_hash,"selection operations never alter original GLB bytes")
	var unchanged:=true
	for i in range(selection.entries.size()):
		var original=selection.entries[i].original
		if original.layers!=original_materials[i][0] or original.get_active_material(0)!=original_materials[i][1]:unchanged=false
	check(unchanged,"original meshes keep their own material and render layers")
	var wall:=Node3D.new();wall.name="OcclusionFixture"
	SceneIO.box(wall,"Wall",Vector3(0,1,1),Vector3(8,8,0.2),Color.GRAY)
	var document:=GLTFDocument.new();var state:=GLTFState.new();document.append_from_scene(wall,state)
	var wall_path:=folder.path_join("wall.glb");document.write_to_filesystem(state,wall_path);wall.free()
	app.load_scene(wall_path);await settled();selection.items[model_key].select(0)
	app.pose_editor.set_visibility_key(false);await settled()
	var xray: Image=selection.viewport.get_texture().get_image()
	check(id_point(xray,selection.color_for(model_key)).x>=0 and selection.selected==model_key,"selected hidden model ghost remains available through occluding map geometry")
	var native:=[]
	for sample in [{"path":"pose-smoke/miku-project","bone":"左腕"},{"path":"source-smoke/source-project","bone":"L_UpperArm"},{"path":"sfm-smoke/project","bone":"bip_upperArm_L"}]:
		var path:=ProjectSettings.globalize_path("res://output/"+str(sample.path))
		if not FileAccess.file_exists(path.path_join("project.json")):
			print("SKIP private selection fixture absent: "+str(sample.path));continue
		check(app.open_project(path),"native project opens in same world: "+str(sample.path));await settled()
		check(selection.selected.is_empty() and app.mode.selected==1,"reopened native project starts with no world selection and free camera: "+str(sample.path))
		Support.select_rig(app);model_key=Support.key(app,Support.rig(app));app.pose_editor.frame_model();await settled()
		var native_mask: Image=selection.viewport.get_texture().get_image()
		var native_point:=id_point(native_mask,selection.color_for(model_key));selection.select_entity("")
		await click(app,native_point)
		check(native_point.x>=0 and selection.selected==model_key,"GPU picking selects actual native skinned model: "+str(sample.path))
		var native_id: String=""
		for candidate in Support.rig(app).order:
			if str(Support.rig(app).bones[candidate].name).ends_with(str(sample.bone)):native_id=candidate
		if native_id.is_empty():check(false,"required native bone present");continue
		app.pose_editor.tree_items[native_id].select(0);app.pose_editor.operation.select(0);app.pose_editor.refresh_values()
		app.pose_editor.fields[2].value+=35;app.pose_editor.apply_numeric();await settled()
		check(native_mask.get_data()!=selection.viewport.get_texture().get_image().get_data(),"selection mask deforms with native arm: "+str(sample.path))
		native.append(sample.path)
	app.new_project();await settled()
	check(selection.selected.is_empty() and selection.entries.is_empty() and selection.items.is_empty(),"New removes stale hierarchy, selection meshes and highlighted state")
	app.load_demo_room();await settled();selection.items.scene.select(0);await settled()
	check(selection.selected=="scene" and not selection.outline_material.get_shader_parameter("ghost"),"environment root can be found and selected in same world hierarchy")
	var map_final: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	selection.clear();var map_without: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(map_final.get_data()==map_without.get_data(),"selected environment outline also remains absent from export")
	var report:={"checks":checks,"failures":failures,"folder":folder,"native_projects":native,"final_changed_channels":changed,"final_mean_delta":float(total)/a.size()}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/world-selection-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("WORLD_SELECTION_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)
