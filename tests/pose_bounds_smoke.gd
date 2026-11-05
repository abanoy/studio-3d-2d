extends SceneTree
const Bounds=preload("res://src/pose_bounds.gd")
const Model=preload("res://src/model.gd")
const Fixture=preload("res://tests/limb_fixture.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Pose bounds watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func engine_geometry(actor) -> Dictionary:
	# Independent engine bake: first morphs, then registered-skin deformation.
	# Temporary copies are removed before the product's bounds query runs.
	var points:=PackedVector3Array();var bounds:=AABB();var first:=true
	for mesh in actor.opacity_materials.meshes:
		var reference: MeshInstance3D=mesh;var copy: MeshInstance3D
		if mesh.get_blend_shape_count()>0:
			copy=MeshInstance3D.new();copy.mesh=mesh.bake_mesh_from_current_blend_shape_mix();copy.skin=mesh.skin;copy.transform=mesh.transform;copy.visible=false
			mesh.get_parent().add_child(copy)
			var sk=mesh.get_node_or_null(mesh.skeleton)
			if sk is Skeleton3D:copy.skeleton=copy.get_path_to(sk);sk.force_update_all_bone_transforms()
			reference=copy
		var baked: Mesh=reference.bake_mesh_from_current_skeleton_pose() if reference.get_skin_reference()!=null else reference.mesh
		for surface in range(baked.get_surface_count()):
			for vertex in baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
				var point: Vector3=mesh.global_transform*vertex;points.append(point)
				if first:bounds=AABB(point,Vector3.ZERO);first=false
				else:bounds=bounds.expand(point)
		if copy:copy.free()
	return {"bounds":bounds,"points":points}
func error(a: AABB,b: AABB) -> float:return a.position.distance_to(b.position)+a.size.distance_to(b.size)
func fits(camera: Camera3D,points: PackedVector3Array) -> bool:
	for point in points:
		if camera.is_position_behind(point):return false
		var depth: float=-camera.to_local(point).z
		if depth<camera.near or depth>camera.far:return false
		var pixel:=camera.unproject_position(point)
		if pixel.x<0 or pixel.x>1920 or pixel.y<0 or pixel.y>1080:return false
	return true
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var path:=folder.path_join("limb.glb");Fixture.create(path)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	app.pose_editor.add_model(path);var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id
	actor.data.position=[4,3,2];actor.data.scale=1.7;actor.data.rotation_xyzw=[0,.38268343,0,.92387953]
	actor.data.pose[actor.order[0]]={"position":[0,-20,0],"rotation_xyzw":[0,0,0,1]};actor.apply(0,true)
	var immediate:=Bounds.query(actor.root)
	await settled();var actual:=engine_geometry(actor);var query:=Bounds.query(actor.root)
	check(immediate.error.is_empty() and error(immediate.bounds,actual.bounds)<.0001,"immediate framing reads the current pose before a rendered-frame delay")
	check(query.error.is_empty() and error(query.bounds,actual.bounds)<.0001 and query.conservative==0,"exact skin bounds match the independent engine snapshot")
	# Exercise named palettes and eight nonzero influences, with transformed parents.
	var mesh: MeshInstance3D=actor.opacity_materials.meshes[0]
	var original_mesh: Mesh=mesh.mesh;var original_skin: Skin=mesh.skin
	var arrays: Array=original_mesh.surface_get_arrays(0);var joints:=PackedInt32Array();var weights:=PackedFloat32Array()
	for vertex in arrays[Mesh.ARRAY_VERTEX]:
		# Weights are UNORM16 in Godot; choose a sum of exactly 65535 units.
		for j in range(8):joints.append(j%original_skin.get_bind_count());weights.append(float(8191 if j==7 else 8192)/65535.)
	arrays[Mesh.ARRAY_BONES]=joints;arrays[Mesh.ARRAY_WEIGHTS]=weights
	var eight:=ArrayMesh.new();eight.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,[],{},Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS)
	var named:=Skin.new();var sk: Skeleton3D=mesh.get_node(mesh.skeleton)
	for bind in range(original_skin.get_bind_count()):named.add_named_bind(sk.get_bone_name(original_skin.get_bind_bone(bind)),original_skin.get_bind_pose(bind))
	mesh.mesh=eight;mesh.skin=named;await settled();var eight_actual:=engine_geometry(actor);var eight_query:=Bounds.query(actor.root)
	check(eight_query.error.is_empty() and error(eight_query.bounds,eight_actual.bounds)<.0001,"named skin binds and eight weighted influences match engine geometry under transformed parents")
	mesh.mesh=original_mesh;mesh.skin=original_skin;await settled()
	check(app.renderer.scene_bounds(actor.root).get_center().distance_to(query.bounds.get_center())>30,"fixture proves the old bind bound misses the model's current location")
	var before: Dictionary=actor.data.duplicate(true);var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();var frame: int=app.frame;var dirty: bool=app.dirty
	app.pose_editor.frame_model()
	check(fits(app.renderer.camera,actual.points),"Simple Frame model contains every current posed vertex")
	check(actor.data==before and app.keys==keys and app.history.size()==history and app.frame==frame and app.dirty==dirty,"framing changes only the temporary view, without pose/shot/history edits")
	actor.data.visible=false;actor.apply(0,true);app.world_selection.select_entity(id);app.world_selection.frame_selected()
	check(not actor.root.visible and fits(app.renderer.camera,actual.points) and not actor.data.visible,"hidden selected model frames without changing visibility")
	actor.data.visible=true;actor.apply(0,true)
	var fallback:=Bounds.query(actor.root,0)
	check(fallback.error.is_empty() and fallback.conservative>0 and fallback.bounds.encloses(actual.bounds),"bounded fallback conservatively contains all posed geometry")
	actor.data.scale=.001;actor.apply(0,true);actual=engine_geometry(actor);app.pose_editor.frame_model()
	check(fits(app.renderer.camera,actual.points),"very small models remain in front of the existing near clipping plane")
	var empty:=Node3D.new();app.renderer.world.add_child(empty);var view: Transform3D=app.renderer.camera.transform
	check(not app.renderer.frame_scene(empty) and app.renderer.camera.transform==view,"empty framing refuses without moving the camera");empty.free()
	var metrics:={};var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	for plan in plans:
		app.new_project();app.pose_editor.add_model(plan.source);actor=app.renderer.active_model();id=actor.data.id
		actor.data.position=[9,3,-4];actor.data.scale=1.3;actor.data.rotation_xyzw=[0,.258819,0,.9659258]
		var scale: float=actor.bones[actor.order[0]].skeleton.global_basis.get_scale().x*1.3
		actor.data.pose[actor.order[0]]={"position":[0,-20/maxf(scale,.00001),0],"rotation_xyzw":[0,0,0,1]}
		actor.apply(0,true);await settled()
		actual=engine_geometry(actor);before=actor.data.duplicate(true);keys=app.keys.duplicate(true);history=app.history.size()
		var began:=Time.get_ticks_usec();app.pose_editor.frame_model();var elapsed:=Time.get_ticks_usec()-began;query=app.renderer.last_framing
		check(query.error.is_empty() and error(query.bounds,actual.bounds)<.001 and fits(app.renderer.camera,actual.points),"native/morph pose fits independent baked geometry: "+plan.label)
		check(actor.data==before and app.keys==keys and app.history.size()==history,"framing preserves native identities/data and explicit shot keys: "+plan.label)
		metrics[plan.label]={"vertices":query.vertices,"conservative":query.conservative,"bound_error":error(query.bounds,actual.bounds),"elapsed_us":elapsed}
		if plan.label=="Shaped":
			app.video.lighting_mode="unshaded";app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.cel_at(app.layers[1],0).image.set_pixel(80,80,Color.CYAN)
			var snapshot: Image=await app.renderer.capture(app.keys,app.layers,0,true);app.pose_editor.frame_model()
			var export_error: String=await app.export_movie(folder)
			check(export_error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==snapshot.get_data(),"temporary pose framing does not change authored MP4 camera or independent cel")
			metrics.movie=app.last_export_folder.path_join("movie.mp4")
		elif plan.label!="Shaped":
			app.physics_editor.change(true);await settled()
			if str(plan.label).begins_with("VRM"):
				app.physics_editor.change_hair(true)
				var deadline:=Time.get_ticks_msec()+10000
				while not app.physics_editor.pending.is_empty() and Time.get_ticks_msec()<deadline:await process_frame
				await settled()
			for i in range(24):await physics_frame
			before=actor.data.duplicate(true);keys=app.keys.duplicate(true);history=app.history.size();app.pose_editor.frame_model()
			await RenderingServer.frame_post_draw;actual=engine_geometry(actor)
			check(app.physics_editor.active(id) and fits(app.renderer.camera,actual.points) and actor.data==before and app.keys==keys and app.history.size()==history,"live native body/VRM hair frames without recording or stopping: "+plan.label)
			app.physics_editor.change(false)
	app.new_project();app.pose_editor.add_model(path);actor=app.renderer.active_model();id=actor.data.id;actor.data.position=[0,10,0];actor.apply(0,true)
	app.physics_editor.change(true);await settled()
	for i in range(60):await physics_frame
	before=actor.data.duplicate(true);keys=app.keys.duplicate(true);history=app.history.size();app.pose_editor.frame_model()
	await RenderingServer.frame_post_draw;actual=engine_geometry(actor)
	check(app.physics_editor.active(id) and fits(app.renderer.camera,actual.points),"live falling ragdoll frames at its current location without stopping physics")
	check(actor.data==before and app.keys==keys and app.history.size()==history,"live framing creates no pose, recording or camera key")
	var live_skeleton: Skeleton3D=actor.bones[actor.order[0]].skeleton
	check(not Bounds.final_pose(live_skeleton).is_empty(),"live bounds use the final physical modifier pose")
	app.physics_editor.change(false);app.pose_editor.frame_model();await settled();actual=engine_geometry(actor);query=Bounds.query(actor.root)
	check(Bounds.final_pose(live_skeleton).is_empty() and error(query.bounds,actual.bounds)<.0001,"Physics Off clears the transient final pose and frames the frozen editable skin")
	app.physics_editor.change(true);await settled();app.physics_editor.simulations[id].dispose();app.physics_editor.simulations.erase(id)
	var removed:=Skeleton3D.new();var removed_owner:=Node3D.new();removed.free();removed_owner.free();Bounds.clear_final(removed,removed_owner)
	check(Bounds.final_pose(live_skeleton).is_empty(),"disposing live physics removes its transient framing cache")
	actor.apply(0,true);app.pose_editor.frame_model();await settled();root.get_texture().get_image().save_png(folder.path_join("framed-editor.png"))
	var project:=folder.path_join("framed.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	app.world_selection.select_entity(id);actor=app.renderer.active_model();actual=engine_geometry(actor);app.pose_editor.frame_model()
	check(fits(app.renderer.camera,actual.points) and not app.physics_editor.is_running(),"reopened frozen pose frames correctly without fresh simulation")
	var result:={"checks":checks,"failures":failures,"folder":folder,"metrics":metrics,"movie":metrics.movie}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("POSE_BOUNDS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
