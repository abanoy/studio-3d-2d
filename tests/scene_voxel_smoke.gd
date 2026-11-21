extends "res://tests/scene_indirect_smoke.gd"

func fixtures() -> void:
	var room:=Node3D.new();room.name="VoxelRoom"
	SceneIO.box(room,"Floor",Vector3(0,-.2,0),Vector3(6,.4,8),Color(.8,.8,.8))
	SceneIO.box(room,"RedWall",Vector3(0,1.5,-2),Vector3(6,3,.4),Color(.8,.02,.02))
	SceneIO.box(room,"Left",Vector3(-3,1.5,0),Vector3(.4,3,8),Color(.7,.7,.7))
	SceneIO.box(room,"Right",Vector3(3,1.5,0),Vector3(.4,3,8),Color(.7,.7,.7))
	SceneIO.box(room,"Ceiling",Vector3(0,3.2,0),Vector3(6,.4,8),Color(.7,.7,.7))
	write_scene(folder.path_join("room.glb"),room)
	var actor:=Fixture.scene();var panel: MeshInstance3D=actor.get_node("Panel")
	var arrays:=panel.mesh.surface_get_arrays(0);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	for index in range(vertices.size()):vertices[index]*=Vector3(4,2.4,6)
	arrays[Mesh.ARRAY_VERTEX]=vertices;var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);panel.mesh=mesh
	var material:=StandardMaterial3D.new();material.albedo_color=Color(.01,.01,.01);material.roughness=1.;panel.material_override=material
	write_scene(folder.path_join("actor.glb"),actor)

func wait_bake(app: Node) -> void:
	await settled()
	while app.renderer.scene_lighting.indirect.voxel.baking:await process_frame
	await settled()

func patch_color(image: Image,app: Node) -> Vector3:
	return sum_region(image,app.renderer.camera.unproject_position(Vector3(0,.001,0)),8)*(255./256.)

func patch_difference(a: Image,b: Image,app: Node) -> float:
	var point: Vector2=app.renderer.camera.unproject_position(Vector3(0,.001,0))
	var patch:=Rect2i(Vector2i(point)-Vector2i(8,8),Vector2i(16,16))
	return mean_difference(a.get_region(patch),b.get_region(patch))

func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];graphics=not "--cpu" in args
	if "--read" in args:await reader();return
	for bad in ["method","size","subdiv"]:
		var document:=Document.empty();document.indirect=Document.indirect(document).duplicate(true)
		document.indirect.method="voxelgi";document.indirect.voxel=Document.voxel({}).duplicate(true)
		if bad=="method":document.indirect.method="raytrace"
		elif bad=="size":document.indirect.voxel.size=[0,8,8]
		else:document.indirect.voxel.subdiv=3
		check(not Document.error(document).is_empty(),"Reject invalid VoxelGI "+bad)
	var empty_app=await make_app("neon");var empty_editor: Node=empty_app.scene_lighting_editor
	empty_editor.open();empty_app.change_lighting(1);empty_editor.refresh()
	empty_editor.indirect_method.select(1);empty_editor.indirect_enabled.set_pressed_no_signal(true);empty_editor.apply_indirect();await wait_bake(empty_app)
	check(empty_app.renderer.scene_lighting.indirect.capture_error(empty_app.video).contains("No static environment"),"Empty room reports an actionable bake/export limitation")
	empty_app.free();await process_frame
	fixtures()
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		check(app.load_scene(folder.path_join("room.glb")).is_empty(),"Import original bounded room in "+theme)
		var room=app.renderer.world_runtime.instance(app.last_import_id)
		check(app.pose_editor.add_model(folder.path_join("actor.glb")).is_empty(),"Import original skinned moving blocker")
		var actor=app.renderer.world_runtime.instance(app.last_import_id)
		room.data.position=[0,0,0];room.data.rotation_xyzw=[0,0,0,1];room.data.scale=1.
		actor.data.position=[-2.2,.6,-.8];actor.data.rotation_xyzw=[0,0,0,1];actor.data.scale=1.
		actor.data.pose_keys=[]
		for frame in range(4):actor.data.pose_keys.append({"frame":frame,"pose":{},"interpolation":"hold","transform":{"position":[-2.2 if frame in [0,3] else 0.,.6,-.8],"rotation_xyzw":[0,0,0,1],"scale":1.}})
		app.video.duration_frames=4
		app.renderer.camera.position=Vector3(3,2.5,4);app.renderer.camera.look_at(Vector3(0,.7,-.4))
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55.)];app.set_frame(0)
		var editor: Node=app.scene_lighting_editor;editor.open();app.change_lighting(1);editor.refresh()
		var lights:=Document.empty();var light:=Document.create("spot",Vector3.ZERO)
		light.position=[0,2,-.5];var rotation:=Basis.looking_at(Vector3(0,1.5,-2)-Vector3(0,2,-.5)).get_euler()
		light.rotation_degrees=[rad_to_deg(rotation.x),rad_to_deg(rotation.y),rad_to_deg(rotation.z)];light.spot_angle=30.;light.energy=6.;light.range=5.;light.shadows=false
		lights.lights=[light];editor.commit(lights,"Fixture wall spotlight")
		var direct: Array=[]
		if graphics:
			for frame in [0,1]:direct.append(patch_color(await app.renderer.capture(app.keys,[],frame,true),app))
			check(direct[0].length()<.1 and direct[1].length()<.1,"Measured floor patch has no direct illumination or direct shadow")
		var world: Dictionary=app.renderer.world_state().duplicate(true);var keys: Array=app.keys.duplicate(true)
		var material: Material=actor.opacity_materials.authored_material(actor.opacity_materials.meshes[0],0)
		editor.refresh();editor.indirect_enabled.set_pressed_no_signal(true);editor.indirect_method.select(1)
		editor.indirect_energy.get_line_edit().text="1";editor.indirect_settle.get_line_edit().text="32"
		for axis in range(3):editor.voxel_positions[axis].get_line_edit().text=str([.0123456789,1.5,0][axis]);editor.voxel_sizes[axis].get_line_edit().text=str([7.0123456789,4,9][axis])
		var history: int=app.history.size();editor.apply_indirect();await wait_bake(app)
		var gi=app.renderer.scene_lighting.indirect;var voxel=gi.voxel
		check(app.history.size()==history+1 and Document.indirect(Document.document(app.video)).method=="voxelgi","Apply VoxelGI is one saved video transaction")
		check(voxel.error.is_empty() and voxel.probe.data!=null and voxel.bake_count==1,"Deferred room bake produces runtime probe data")
		check(not app.renderer.world_environment.environment.sdfgi_enabled and actor.opacity_materials.meshes[0].gi_mode==GeometryInstance3D.GI_MODE_DYNAMIC,"VoxelGI replaces SDFGI and model participates dynamically")
		check(app.renderer.world_state()==world and app.keys==keys and material==actor.opacity_materials.authored_material(actor.opacity_materials.meshes[0],0),"Bake preserves world, animation, camera and authored materials")
		var exact_room: Dictionary=Document.voxel(Document.indirect(Document.document(app.video))).duplicate(true)
		editor.refresh();editor.indirect_energy.get_line_edit().text="1.1";editor.apply_indirect();await wait_bake(app)
		check(saved_equal(Document.voxel(Document.indirect(Document.document(app.video))),exact_room) and voxel.bake_count==1,"Strength-only edit preserves hidden room precision without rebaking")
		app.undo();await wait_bake(app)
		app.undo();await settled();check(not voxel.probe.visible and actor.opacity_materials.meshes[0].gi_mode==GeometryInstance3D.GI_MODE_STATIC,"Undo hides room probe and restores GI flags")
		app.redo();await wait_bake(app);check(voxel.probe.visible,"Redo restores room VoxelGI")
		var images: Array=[]
		if graphics:
			var preview_errors:={}
			var setup_colors: Array=[]
			for frame in [0,1,3]:
				app.scene_view.set_setup(true,false)
				app.set_frame(frame);await settled()
				for warmup in range(40):await process_frame
				var setup_image: Image=app.scene_view.viewport.get_texture().get_image()
				var setup_point: Vector2=app.scene_view.camera.unproject_position(Vector3(0,.001,0))
				setup_colors.append(sum_region(setup_image,setup_point,8)*(255./256.))
				setup_image.save_png(folder.path_join(theme+"-scene-setup-"+str(frame)+".png"))
				# Camera focus is the actual output-shaped live preview. Scene setup
				# deliberately uses another viewport/projection and disables this one.
				app.scene_view.set_setup(false,false);await settled()
				for warmup in range(40):await process_frame
				var preview: Image=app.renderer.viewport.get_texture().get_image();preview.convert(Image.FORMAT_RGBA8)
				var preview_model:=str(actor.root.global_transform)
				var image: Image=await app.renderer.capture(app.keys,[],frame,true);images.append(image)
				var drift:=mean_difference(preview,image)
				preview_errors[str(frame)]={"mean":drift,"patch_mean":patch_difference(preview,image,app),"preview_rgb":str(patch_color(preview,app)),"model_before":preview_model,"model_after":str(actor.root.global_transform)}
				preview.save_png(folder.path_join(theme+"-preview-"+str(frame)+".png"))
				check(drift<=2. and patch_difference(preview,image,app)<=2.,"Live preview and final VoxelGI capture agree, including bounce patch, at frame "+str(frame))
				image.save_png(folder.path_join(theme+"-frame-"+str(frame)+".png"))
			var open:=patch_color(images[0],app);var blocked:=patch_color(images[1],app);var returned:=patch_color(images[2],app)
			measurements[theme]={"open_rgb":[open.x,open.y,open.z],"blocked_rgb":[blocked.x,blocked.y,blocked.z],"returned_rgb":[returned.x,returned.y,returned.z],"bake_ms":voxel.bake_ms,"preview_errors":preview_errors}
			check(open.x>5 and open.x>open.y*1.2,"VoxelGI lights the floor through red wall bounce")
			check(open.x-blocked.x>2.5 and blocked.x<open.x*.85,"Moving skinned model occludes indirect light away from direct spotlight")
			check(absf(returned.x-open.x)<=2.,"Moving model away restores indirect illumination")
			measurements[theme].scene_setup_red=[setup_colors[0].x,setup_colors[1].x,setup_colors[2].x]
			check(setup_colors[0].x>5 and setup_colors[0].x-setup_colors[1].x>2.5 and absf(setup_colors[2].x-setup_colors[0].x)<=2.,"Scene setup live viewport also shows moving indirect occlusion and recovery")
		app.set_frame(0)
		var directory:=folder.path_join(theme+"-snapshot")
		check(Storage.save_project(directory,app.video,app.keys,app.layers,"",0,{}, {},{},false,app.renderer.world_state()).is_empty(),"Room recipe and animated world save normally")
		write_json(folder.path_join(theme+"-expected.json"),{"indirect":Document.indirect(Document.document(app.video))})
		if graphics:
			app.has_project.save_file(folder.path_join(theme+".has"),"packed");await wait_job(app.has_project)
			check(FileAccess.file_exists(folder.path_join(theme+".has")),"Actual portable HAS saver includes room recipe and original assets")
			if theme=="neon":
				var why: String=await app.export_movie(folder);check(why.is_empty(),"Moving VoxelGI movie exports through actual encoder")
				if why.is_empty():
					for index in range(3):
						var frame: int=[0,1,3][index];var exported:=Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png"%(frame+1)))
						var drift:=mean_difference(images[index],exported);measurements[theme]["export_mean_"+str(frame)]=drift
						var patch_drift:=patch_difference(images[index],exported,app);measurements[theme]["export_patch_mean_"+str(frame)]=patch_drift
						check(drift<=2. and patch_drift<=2.,"Movie source matches VoxelGI preview and bounce patch at frame "+str(frame))
					measurements.movie=app.last_export_folder.path_join("movie.mp4")
		app.free();await process_frame
	finish("writer")

func reader() -> void:
	for theme in ["neon","light"]:
		var app=await make_app(theme)
		if graphics:
			app.has_project.open_file(folder.path_join(theme+".has"));await wait_job(app.has_project)
		else:
			var directory:=folder.path_join(theme+"-packed-unpacked");var loaded:=Storage.load_project(directory)
			check(not loaded.has("error") and app.install_project_data(loaded,directory),"Fresh process installs packed room recipe")
		await wait_bake(app)
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(theme+"-expected.json")))
		check(saved_equal(Document.indirect(Document.document(app.video)),expected.indirect),"Fresh process retains VoxelGI bounds, strength and resolution")
		var voxel=app.renderer.scene_lighting.indirect.voxel
		check(voxel.bake_count==1 and voxel.error.is_empty() and voxel.probe.data!=null,"Cold reopen regenerates room bake without external cache")
		if graphics:
			for frame in [0,1,3]:
				var image: Image=await app.renderer.capture(app.keys,[],frame,true);var original:=Image.load_from_file(folder.path_join(theme+"-frame-"+str(frame)+".png"))
				var drift:=mean_difference(image,original)
				measurements[theme+"_cold_"+str(frame)]=drift
				var patch_drift:=patch_difference(image,original,app);measurements[theme+"_cold_patch_"+str(frame)]=patch_drift
				check(drift<=2. and patch_drift<=2.,"Cold room bake matches original moving frame and bounce patch "+str(frame))
				image.save_png(folder.path_join(theme+"-cold-"+str(frame)+".png"))
		app.scene_lighting_editor.open();app.scene_lighting_editor.indirect_energy.get_line_edit().text="0.8";app.scene_lighting_editor.apply_indirect();app.undo();await wait_bake(app)
		check(saved_equal(Document.indirect(Document.document(app.video)),expected.indirect),"Reopened room controls remain editable and undoable")
		app.free();await process_frame
	finish("reader")
