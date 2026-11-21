extends "res://tests/scene_lighting_smoke.gd"
const Fixture=preload("res://tests/posed_bounds_fixture.gd")

func write_scene(path: String,node: Node3D) -> void:
	var document:=GLTFDocument.new();var state:=GLTFState.new()
	check(document.append_from_scene(node,state)==OK and document.write_to_filesystem(state,path)==OK,"Original indirect-light fixture GLB written")
	node.free()

func fixtures() -> void:
	var room:=Node3D.new();room.name="IndirectRoom"
	SceneIO.box(room,"Floor",Vector3(0,-.15,0),Vector3(6,.3,6),Color(.75,.75,.75))
	SceneIO.box(room,"RedWall",Vector3(-1.3,1.4,0),Vector3(.3,2.8,4),Color(.8,.03,.03))
	SceneIO.box(room,"Back",Vector3(0,1.4,-1.8),Vector3(4,2.8,.3),Color(.8,.8,.8))
	SceneIO.box(room,"Ceiling",Vector3(0,2.9,0),Vector3(4,.3,4),Color(.75,.75,.75))
	write_scene(folder.path_join("room.glb"),room)
	var actor:=Fixture.scene();var material:=StandardMaterial3D.new();material.albedo_color=Color(.8,.8,.8);material.roughness=1.
	actor.get_node("Panel").material_override=material
	write_scene(folder.path_join("actor.glb"),actor)

func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];graphics=not "--cpu" in args
	if "--read" in args:await reader();return
	var defaults:=Document.indirect(Document.empty())
	check(not defaults.enabled,"Indirect lighting is opt-in")
	for field in ["energy","cell_size","settle_frames","enabled"]:
		var bad:=Document.empty();bad["indirect"]=defaults.duplicate(true)
		bad.indirect[field]=NAN if field=="energy" else 0 if field=="cell_size" else 8.5 if field=="settle_frames" else 1
		check(not Document.error(bad).is_empty(),"Reject invalid indirect "+field)
	fixtures()
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		check(app.load_scene(folder.path_join("room.glb")).is_empty(),"Room imports normally in "+theme)
		var room_id: String=app.last_import_id
		check(app.pose_editor.add_model(folder.path_join("actor.glb")).is_empty(),"Skinned receiver imports normally")
		var actor_id: String=app.last_import_id
		var room=app.renderer.world_runtime.instance(room_id);var actor=app.renderer.world_runtime.instance(actor_id)
		room.data.position=[0,0,0];room.data.rotation_xyzw=[0,0,0,1];room.data.scale=1.
		actor.data.position=[0,.8,0];actor.data.rotation_xyzw=[0,-.3007058,0,.95371695];actor.data.scale=1.
		app.video.duration_frames=4
		app.renderer.camera.position=Vector3(2,1.5,3.5);app.renderer.camera.look_at(Vector3(0,.8,0))
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55.)];app.set_frame(0)
		var editor: Node=app.scene_lighting_editor;editor.open();app.change_lighting(1);editor.refresh()
		var lights:=Document.empty();var light:=Document.create("spot",Vector3.ZERO)
		light.position=[-.65,1.4,.7];var direction:=Basis.looking_at(Vector3(-1.15,1.2,-.3)-Vector3(-.65,1.4,.7)).get_euler()
		light.rotation_degrees=[rad_to_deg(direction.x),rad_to_deg(direction.y),rad_to_deg(direction.z)];light.spot_angle=30.;light.energy=3.;light.range=5.
		lights.lights=[light];editor.commit(lights,"Fixture wall spotlight")
		var world: Dictionary=app.renderer.world_state().duplicate(true);var keys: Array=app.keys.duplicate(true)
		var mesh: MeshInstance3D=actor.opacity_materials.meshes[0];var map_mesh: MeshInstance3D=room.opacity_materials.meshes[0]
		var material: Material=actor.opacity_materials.authored_material(mesh,0)
		map_mesh.gi_mode=GeometryInstance3D.GI_MODE_DISABLED;mesh.gi_mode=GeometryInstance3D.GI_MODE_STATIC
		var grid_mode: int=app.renderer.editor_grid.gi_mode
		var before: Image=await app.renderer.capture(app.keys,[],0,true) if graphics else null
		editor.refresh();editor.indirect_enabled.set_pressed_no_signal(true);editor.indirect_energy.get_line_edit().text="1";editor.indirect_cell.get_line_edit().text="0.15";editor.indirect_settle.get_line_edit().text="32"
		var history: int=app.history.size();editor.apply_indirect();await settled()
		var gi=app.renderer.scene_lighting.indirect
		check(Document.indirect(Document.document(app.video)).enabled and app.history.size()==history+1,"Apply indirect is one history transaction")
		check(map_mesh.gi_mode==GeometryInstance3D.GI_MODE_STATIC and mesh.gi_mode==GeometryInstance3D.GI_MODE_DYNAMIC,"Only environment contributes; skinned model receives")
		check(app.renderer.editor_grid.gi_mode==GeometryInstance3D.GI_MODE_DISABLED,"Editor grid excluded from voxel contribution")
		check(gi.capture_frames(app.video)==32,"Explicit settling budget is used by capture")
		check(actor.data==world.objects.filter(func(row):return row.id==actor_id)[0] and app.renderer.world_state()==world and app.keys==keys and material==actor.opacity_materials.authored_material(mesh,0),"GI leaves model/world/shot and original material unchanged")
		app.undo();await settled();check(map_mesh.gi_mode==GeometryInstance3D.GI_MODE_DISABLED and mesh.gi_mode==GeometryInstance3D.GI_MODE_STATIC and app.renderer.editor_grid.gi_mode==grid_mode,"Undo restores exact original live GI modes")
		app.redo();await settled();check(Document.indirect(Document.document(app.video)).enabled,"Redo restores indirect settings")
		app.change_lighting(0);await settled();check(not app.renderer.world_environment.environment.sdfgi_enabled and map_mesh.gi_mode==GeometryInstance3D.GI_MODE_DISABLED,"Unshaded disables GI and restores runtime flags")
		app.change_lighting(1);await settled()
		if graphics:
			for warmup in range(80):await process_frame
			var after: Image=await app.renderer.capture(app.keys,[],0,true)
			var point: Vector2=app.renderer.camera.unproject_position(Vector3(0,.8,.025))
			var direct:=sum_region(before,point,8);var indirect:=sum_region(after,point,8)
			measurements[theme]={"model_direct_rgb":[direct.x,direct.y,direct.z],"model_indirect_rgb":[indirect.x,indirect.y,indirect.z],"gi_pixel_difference":difference(before,after)}
			check(indirect.x>direct.x+5 and indirect.x>indirect.y*1.2,"Static red wall visibly bounces color onto skinned receiver")
			before.save_png(folder.path_join(theme+"-direct.png"));after.save_png(folder.path_join(theme+"-indirect.png"))
		var expected: Dictionary=Document.indirect(Document.document(app.video)).duplicate(true)
		var directory:=folder.path_join(theme+"-snapshot")
		check(Storage.save_project(directory,app.video,app.keys,app.layers,"",0,{}, {},{},false,app.renderer.world_state()).is_empty(),"Indirect settings save through ordinary Storage")
		write_json(folder.path_join(theme+"-expected.json"),{"indirect":expected})
		if graphics:
			var packed:=folder.path_join(theme+".has");app.has_project.save_file(packed,"packed");await wait_job(app.has_project)
			check(FileAccess.file_exists(packed),"Actual project saver writes packed indirect HAS")
		if graphics and theme=="neon":
			var preview: Image=await app.renderer.capture(app.keys,[],0,true)
			var why: String=await app.export_movie(folder)
			check(why.is_empty(),"Settled indirect-light movie exports")
			if why.is_empty():
				var picture:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
				var drift:=mean_difference(preview,picture);measurements.preview_export_mean=drift
				check(drift<=2.,"Settled preview/export mean channel error stays within 2/255")
				var point: Vector2=app.renderer.camera.unproject_position(Vector3(0,.8,.025))
				var patch:=Rect2i(Vector2i(point)-Vector2i(8,8),Vector2i(16,16))
				var receiver_drift:=mean_difference(preview.get_region(patch),picture.get_region(patch));measurements.receiver_preview_export_mean=receiver_drift
				check(receiver_drift<=2.,"Receiver patch also stays within 2/255 preview/export mean error")
				measurements.movie=app.last_export_folder.path_join("movie.mp4")
		if not graphics:
			gi.rebuild();app.renderer.apply_lighting()
			check(not gi.active and gi.capture_frames(app.video)==32,"Capture retains its settling budget while a rebuild is pending")
			var pending:={"finished":false,"image":null}
			capture_pending(app.renderer,app.keys,pending)
			check(app.renderer.native_readbacks==1,"Settling capture owns one native frame wait")
			app.free();await process_frame
			check(pending.finished and pending.image==null,"Closing during GI settling completes capture safely")
		else:app.free();await process_frame
	finish("writer")

func capture_pending(renderer: Node,keys: Array,result: Dictionary) -> void:
	result.image=await renderer.capture(keys,[],0,true)
	result.finished=true

func mean_difference(a: Image,b: Image) -> float:
	var x:=a.get_data();var y:=b.get_data();var total:=0.
	for index in range(x.size()):total+=absf(int(x[index])-int(y[index]))
	return total/maxi(1,x.size())

func reader() -> void:
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		if graphics:
			var packed:=folder.path_join(theme+".has");app.has_project.open_file(packed);await wait_job(app.has_project)
			check(app.has_project.path==packed,"Fresh process opens packed indirect project through actual app")
		else:
			var directory:=folder.path_join(theme+"-packed-unpacked")
			var loaded:=Storage.load_project(directory);check(not loaded.has("error") and app.install_project_data(loaded,directory),"Fresh process installs packed indirect project")
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(theme+"-expected.json")))
		check(saved_equal(Document.indirect(Document.document(app.video)),expected.indirect),"Fresh process retains indirect settings")
		app.scene_lighting_editor.open();app.scene_lighting_editor.indirect_energy.get_line_edit().text="0.7";app.scene_lighting_editor.apply_indirect();app.undo();await settled()
		check(saved_equal(Document.indirect(Document.document(app.video)),expected.indirect),"Reopened indirect setting remains editable and undoable")
		app.free();await process_frame
	finish("reader")
