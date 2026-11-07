extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const World = preload("res://src/world_document.gd")
const Model = preload("res://src/model.gd")
const Storage = preload("res://src/storage.gd")
const Timeline = preload("res://src/timeline.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("World edit watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func mask_point(selection,id: String) -> Vector2:
	selection.picking+=1;selection._process(0);selection.viewport.render_target_update_mode=SubViewport.UPDATE_ONCE
	await RenderingServer.frame_post_draw
	var image: Image=selection.viewport.get_texture().get_image();selection.picking-=1
	var color: Vector3=selection.color_for(id)
	for y in range(5,image.get_height()-5,2):
		for x in range(5,image.get_width()-5,2):
			var pixel:=image.get_pixel(x,y)
			if Vector3(pixel.r,pixel.g,pixel.b).distance_squared_to(color)<0.001:return Vector2(x*2+1,y*2+1)
	return Vector2(-1,-1)

func click(app,point: Vector2) -> void:
	var rect: Rect2=app.canvas.image_rect()
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed
		event.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(event)
	await settled()

func green_pixels(image: Image) -> int:
	var bytes:=image.get_data();var total:=0
	for i in range(0,bytes.size(),4):
		if bytes[i]<95 and bytes[i+1]>180 and bytes[i+2]<160:total+=1
	return total

func run() -> void:
	var runtime_report: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://output/world-runtime-result.json"))
	var data:=Storage.load_project(runtime_report.snapshot)
	if data.has("error"):push_error(data.error);quit(1);return
	var folder:=ProjectSettings.globalize_path("res://output/world-edit/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.video=data.video;app.keys=data.camera_keys;app.layers=data.layers;app.frame=24;app.active_layer=0
	check(app.renderer.install_world(app.renderer.prepare_world(data.world,48),24),"install prepared multi-object world in real app shell")
	app.mode.select(1);app.change_mode(1);app.set_frame(24);app.renderer.evaluate(app.keys,24);await settled()
	var selection=app.world_selection;var editor=app.pose_editor;var runtime: RefCounted=app.renderer.world_runtime
	check(selection.items.size()==5 and selection.selected.is_empty() and app.renderer.active_model()==null,"all hierarchy instances appear with no default selection")
	check(selection.items["actor-0"].get_parent()==selection.items["map-0"] and selection.items["map-0"].get_parent()==selection.items["sets"],"world tree reflects actual map/group parenting")
	check(selection.entries.size()==8,"selection copies each map/actor mesh once without collecting child rigs twice")
	var camera: Camera3D=app.renderer.camera;var camera_before:=camera.transform;var shots:=JSON.stringify(app.keys)
	var point: Vector2=await mask_point(selection,"actor-0")
	await click(app,point)
	check(point.x>0 and selection.selected=="actor-0" and app.renderer.active_model()==runtime.instance("actor-0") and app.mode.selected==2 and camera.transform.is_equal_approx(camera_before),"routed click selects the correct shared-asset actor without moving camera")
	var left: RefCounted=runtime.instance("actor-0");var right: RefCounted=runtime.instance("actor-1");var arm: String=left.order[1]
	var left_before: Dictionary=left.data.duplicate(true);var right_before: Dictionary=right.data.duplicate(true)
	editor.tree_items[arm].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=25;editor.apply_numeric()
	check(left.data!=left_before and right.data==right_before and app.history[-1].type=="world_object" and app.history[-1].object_id=="actor-0","pose auto-key and history target stable actor ID, preserving shared-asset peer")
	var left_after: Dictionary=left.data.duplicate(true)
	selection.select_entity("actor-1");app.undo()
	check(left.data==left_before and right.data==right_before and selection.selected=="actor-1" and app.renderer.active_instance_id=="actor-1","Undo after selecting another actor restores original target without changing selection")
	await settled()
	var canvas_rect: Rect2=app.canvas.image_rect()
	var other_set:=Rect2i(app.canvas.global_position+canvas_rect.position+canvas_rect.size*Vector2(0.1,0.1),canvas_rect.size*Vector2(0.4,0.8))
	var stray_green:=green_pixels(root.get_texture().get_image().get_region(other_set))
	print("UNSELECTED_SET_GREEN_PIXELS ",stray_green)
	check(stray_green==0,"selection color filtering never outlines an unrelated map")
	app.redo()
	check(left.data==left_after and right.data==right_before and runtime.snapshot().objects[0]==left_after,"Redo restores original actor and world snapshot reflects replaced data")
	var invalid:=left_after.duplicate(true);invalid.pose["missing bone"]=Model.identity()
	check(not editor.restore_state(invalid,false).is_empty() and left.data==left_after and right.data==right_before,"invalid stored bone edit preserves target and peers")
	selection.items["map-1"].select(0);await settled()
	check(app.renderer.active_model()==runtime.instance("map-1") and editor.selected=="@root" and editor.handles.size()==3,"map root gets same direct transform controls as models")
	editor.operation.select(1);editor.refresh_values();var old_map: Dictionary=runtime.instance("map-1").data.duplicate(true)
	var peer_origin: Vector3=left.root.global_position;var child_origin: Vector3=right.root.global_position
	editor.fields[0].value=5;editor.fields[1].value=1;editor.fields[2].value=-1;editor.apply_numeric()
	check(runtime.instance("map-1").authored_keys()[-1].frame==24 and right.root.global_position.distance_to(child_origin+Vector3(2,1,-1))<0.01 and left.root.global_position.is_equal_approx(peer_origin),"map XYZ edit auto-keys complete map and child while other set stays still")
	selection.select_entity("sets");app.undo()
	check(runtime.instance("map-1").data==old_map and selection.selected=="sets","map edit Undo remains attached to map ID after selecting group")
	selection.select_entity("sets");editor.set_flag("visible",false)
	selection.items["actor-0"].select(0);await settled()
	check(not left.root.is_visible_in_tree() and left.data.visible and selection.outline_material.get_shader_parameter("ghost"),"hidden-parent actor remains selected as editor-only ghost without modifying its visibility")
	var hidden: Image=await app.renderer.capture(app.keys,[],24,true)
	var ink:=hidden.get_data();var lit:=0
	for i in range(0,ink.size(),4):
		if ink[i]>0 or ink[i+1]>0 or ink[i+2]>0:lit+=1
	check(lit==0,"parent-hidden world stays black in final render despite selected ghost")
	editor.tree_items[arm].select(0);editor.refresh_values();editor.fields[2].value=15;editor.apply_numeric()
	check(not left.root.is_visible_in_tree() and left.authored_keys()[-1].frame==24,"bone remains poseable under hidden parent and edit auto-keys")
	app.undo();selection.select_entity("sets");editor.set_flag("visible",true)
	selection.select_entity("actor-0");app.set_frame(0);editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.update_gizmo()
	var start: Vector2=editor.handles[0].points[-1]
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true
	editor.input(press,start)
	var motion:=InputEventMouseMotion.new();editor.input(motion,start+Vector2(20,0))
	var history_size: int=app.history.size();selection.select_entity("actor-1")
	check(not editor.dragging and app.history.size()==history_size+1 and app.history[-1].object_id=="actor-0" and right.data==right_before,"selection switch finishes active drag on its original object in one Undo command")
	app.undo()
	# Parent-rotated/scaled root movement must convert world gizmo motion to local data.
	selection.select_entity("sets");editor.operation.select(0);editor.refresh_values();editor.fields[1].value=90;editor.apply_numeric();editor.scale_field.value=2;editor.scale_apply.pressed.emit()
	selection.select_entity("actor-0");editor.operation.select(1);editor.space.select(1);editor.refresh_values();editor.update_gizmo()
	var handle: Dictionary=editor.handles[0];start=handle.points[-1];var before_drag: Vector3=left.root.global_position
	press.pressed=true;editor.input(press,start)
	var travel: Vector2=(handle.points[-1]-handle.points[0])*0.25;editor.input(motion,start+travel)
	press.pressed=false;editor.input(press,start+travel)
	check(left.root.global_position.distance_to(before_drag+Vector3.RIGHT*handle.units*0.25)<0.02,"world-axis root drag respects rotated and scaled map/group ancestry")
	check(JSON.stringify(app.keys)==shots,"all multi-object pose/root/flag edits leave explicit camera keys unchanged")
	app.undo();selection.select_entity("sets");editor.auto_key.button_pressed=false
	var neutral: Dictionary=runtime.instance("sets").data.duplicate(true);neutral.rotation_xyzw=[0,0,0,1];neutral.scale=1;neutral=Support.legacy_model(neutral);editor.restore_state(neutral,false);editor.auto_key.button_pressed=true
	app.set_frame(24);selection.select_entity("actor-1")
	var expected:=World.portable(app.renderer.world_state())
	var project:=folder.path_join("edited.has");app.has_project.save_file(project,"packed")
	while app.has_project.pid>0:await process_frame
	var saved:=Storage.load_project(app.has_project.pending.folder)
	check(app.has_project.path==project and saved.schema_version==4 and World.portable(saved.world)==JSON.parse_string(JSON.stringify(expected,"",true,true)),"real HAS Save includes every instance and stable-ID edits")
	var linked_project:=folder.path_join("linked-edited.has");app.has_project.save_file(linked_project,"linked")
	while app.has_project.pid>0:await process_frame
	check(app.has_project.path==linked_project and app.has_project.storage_mode=="linked","real linked HAS Save inventories all shared world assets")
	app.has_project.clear_identity();app.project_folder=folder.path_join("directory");app.save()
	var directory:=Storage.load_project(app.project_folder)
	check(not directory.has("error") and directory.schema_version==4 and World.portable(directory.world)==JSON.parse_string(JSON.stringify(expected,"",true,true)),"directory Save also preserves all edited instances")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session))
	check(not recovered.has("error") and recovered.schema_version==4 and World.portable(recovered.world)==JSON.parse_string(JSON.stringify(expected,"",true,true)),"quiet recovery checkpoint preserves whole edited world")
	check(app.open_project(app.has_project.pending.folder) and app.renderer.world_runtime.instances.size()==5 and selection.selected.is_empty(),"normal schema4 Open restores the whole edited world with no selected object")
	selection.select_entity("actor-1")
	var frame24: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==frame24.get_data(),"real app exports edited multi-object world and independent drawing with matching frame24")
	await settled()
	check(not app.exporting and not editor.scale_apply.disabled and app.renderer.active_instance_id=="actor-1","export restores active world controls and selection")
	root.get_texture().get_image().save_png(folder.path_join("editor.png"))
	var original_world: Dictionary=app.renderer.world_state();var rig_source: String=left.data.source
	# All64 palette IDs must resolve from real rendered pixels, including nonprimary colors.
	var many:=World.empty()
	for i in range(64):
		var row:=World.object(rig_source);row.id="instance-%d" % i;row.position=[(i%8-3.5)*2.5,(i/8)*2.2,0];many.objects.append(row)
	app.history.clear();app.redo_history.clear();app.history_bytes=0
	app.renderer.install_world(app.renderer.prepare_world(many,48));app.mode.select(1);app.change_mode(1)
	camera.position=Vector3(0,8,30);camera.look_at(Vector3(0,8,0),Vector3.UP);await settled()
	var palette_picks:=0
	for i in range(64):
		var id:="instance-%d" % i;var object: RefCounted=app.renderer.world_runtime.instance(id)
		point=camera.unproject_position(object.root.global_position+Vector3(0,0.5,0))
		selection.choose_at(point);await settled()
		if selection.selected==id:palette_picks+=1
	check(palette_picks==64,"all64 independent instance colors resolve to correct objects from actual GPU picking")
	var native:=[];var native_world:=World.empty()
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private world edit fixture absent: "+sample);continue
		var source:=Storage.load_project(path);var row: Dictionary=World.from_project(source).objects[-1]
		row=Support.legacy_model(row)
		row.id="native-%d" % native.size();row.pose_keys=[];row.position=[native.size()*3-3,0,0]
		native_world.objects.append(row);native.append(sample)
	var native_project:=""
	if native.size()==3:
		app.history.clear();app.redo_history.clear();app.history_bytes=0
		app.renderer.install_world(app.renderer.prepare_world(native_world,48));await settled()
		for id in app.renderer.world_runtime.order:
			var instance: RefCounted=app.renderer.world_runtime.instance(id);var bounds: AABB=app.renderer.scene_bounds(instance.root)
			instance.data.scale*=2/maxf(0.001,bounds.size.y)
		app.set_frame(0);camera.position=Vector3(0,3.2,10);camera.look_at(Vector3(0,0.9,0),Vector3.UP)
		app.keys=[Timeline.key(0,camera.position,camera.quaternion,60)];await settled()
		for i in range(3):
			var id:="native-%d" % i;point=await mask_point(selection,id)
			selection.choose_at(point);await settled()
			var instance: RefCounted=app.renderer.active_model()
			check(point.x>0 and selection.selected==id and instance.order.size()>50,"GPU selection binds active native rig in combined world: "+native[i])
			var before: Dictionary=instance.data.duplicate(true);var source_hash:=FileAccess.get_sha256(instance.data.source)
			var peer_id:="native-%d" % ((i+1)%3);var peer: RefCounted=app.renderer.world_runtime.instance(peer_id);var peer_data: Dictionary=peer.data.duplicate(true)
			var bone:=""
			for candidate in instance.order:
				if str(instance.bones[candidate].name).ends_with(["左腕","L_UpperArm","bip_upperArm_L"][i]):bone=candidate
			var before_image: Image=await app.renderer.capture(app.keys,[],0,true)
			editor.tree_items[bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value+=35;editor.apply_numeric()
			var after_image: Image=await app.renderer.capture(app.keys,[],0,true)
			check(instance.authored_keys()[0].frame==0 and before_image.get_data()!=after_image.get_data() and peer.data==peer_data,"native arm auto-keys and deforms without changing peer: "+native[i])
			selection.select_entity(peer_id);app.undo()
			check(instance.data==before and peer.data==peer_data and selection.selected==peer_id and FileAccess.get_sha256(instance.data.source)==source_hash,"native Undo targets original ID after selection switch and preserves source: "+native[i])
			app.redo()
		native_project=folder.path_join("native-edited.has");app.has_project.save_file(native_project,"packed")
		while app.has_project.pid>0:await process_frame
		var native_saved:=Storage.load_project(app.has_project.pending.folder)
		check(app.has_project.path==native_project and World.portable(native_saved.world)==JSON.parse_string(JSON.stringify(World.portable(app.renderer.world_state()),"",true,true)),"HAS Save preserves all three native rigs, metadata and per-object edit keys")
		var native_image: Image=await app.renderer.capture(app.keys,app.layers,0,true);native_image.save_png(folder.path_join("native-reference.png"))
	app.renderer.install_world(app.renderer.prepare_world(original_world,48),24);await settled()
	var report:={"checks":checks,"failures":failures,"folder":folder,"movie":app.last_export_folder.path_join("movie.mp4"),"project":project,"linked_project":linked_project,"palette_picks":palette_picks,"native_projects":native,"native_project":native_project,"unselected_green_pixels":stray_green}
	var file:=FileAccess.open(ProjectSettings.globalize_path("res://output/world-edit-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("WORLD_EDIT_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)
