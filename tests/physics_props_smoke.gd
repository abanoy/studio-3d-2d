extends SceneTree
const Fixture=preload("res://tests/limb_fixture.gd")
const Model=preload("res://src/model.gd")
const Prop=preload("res://src/physics_prop.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Physics props watchdog expired");quit(2))
	call_deferred("run")
func check(ok: bool, text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func box_asset(path: String) -> Error:
	var node:=Node3D.new();node.name="OriginalPhysicsBox"
	var instance:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=Vector3(0.8,0.8,0.8);instance.mesh=mesh
	var material:=StandardMaterial3D.new();material.albedo_color=Color("ed9275");instance.material_override=material
	node.add_child(instance);instance.owner=node
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	node.free();return error
func enable(app,id: String) -> void:
	app.world_selection.select_entity(id);app.physics_editor.change(true)
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/physics-props/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("box.glb");var arm_asset:=folder.path_join("arm.glb")
	check(box_asset(asset)==OK and Fixture.create(arm_asset)==OK,"original solid prop and skinned ragdoll fixtures export as standard GLB")
	var digest:=FileAccess.get_sha256(asset)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.load_demo_room()
	var data:=Model.definition(asset);data.position=[0,3,0];app.append_object(data,"model")
	var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var physics=app.physics_editor
	app.mode.select(1);app.change_mode(1)
	app.renderer.camera.position=Vector3(4,3,6);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var paint: PackedByteArray=Drawing.cel_at(app.layers[1],0).image.get_data()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav");var audio_tested:=FileAccess.file_exists(wav)
	if audio_tested:app.import_audio(wav);app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	var audio_before: Dictionary=app.audio_clip.duplicate(true)
	var before: Dictionary=actor.data.duplicate(true);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	physics.toggle.button_pressed=true;await settled()
	check(physics.active(id) and physics.simulations[id] is Prop,"Simple Physics starts an unrigged prop through the shared model path")
	if not physics.active(id):app.free();quit(1);return
	var simulation: RefCounted=physics.simulations[id];var body: RigidBody3D=simulation.body
	check(body.get_parent()==app.renderer.world and body.continuous_cd and body.get_child_count()==1 and body.get_child(0).shape is ConvexPolygonShape3D,"prop uses a world-space CCD body and fitted convex mesh collision")
	physics.change(true)
	check(physics.simulations[id]==simulation,"repeated activation cannot replace or leak a live prop body")
	for i in range(300):await physics_frame
	await settled()
	check(absf(actor.root.global_position.y-0.4)<0.03 and body.linear_velocity.length()<0.1,"solid box falls and settles with its visible bottom on the real map floor")
	check(actor.root.global_transform.is_equal_approx(body.global_transform*simulation.visual_offset),"live visual follows the simulated body instead of the authored root")
	check(actor.data==before and app.history.size()==history and actor.data.pose_keys.is_empty(),"prop simulation leaves authored data and automatic keys untouched")
	var expected: Dictionary=simulation.root_transform(0,false)
	physics.toggle.button_pressed=false;await settled()
	check(not physics.active(id) and actor.data.position==expected.position and actor.data.pose_keys.is_empty() and app.history.size()==history+1,"Physics off freezes prop position in one Undo without adding motion keys")
	var frozen: Dictionary=actor.data.duplicate(true);var frozen_world: Transform3D=actor.root.global_transform
	for i in range(20):await physics_frame
	check(actor.root.global_transform.is_equal_approx(frozen_world) and actor.live_world_transform==null,"frozen prop remains still after its physical proxy is removed")
	app.undo();check(actor.data==before,"Undo restores exact authored prop state before simulation")
	app.redo();check(actor.data==frozen,"Redo restores exact frozen prop state")
	check(app.keys==shots and FileAccess.get_sha256(asset)==digest,"camera keys and source prop bytes remain unchanged")
	check(Drawing.cel_at(app.layers[1],0).image.get_data()==paint and app.audio_clip==audio_before,"physics and Undo leave independent drawing pixels and audio timing untouched")
	var project:=folder.path_join("props.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.data.position==JSON.parse_string(JSON.stringify(frozen.position,"",true,true)) and not physics.is_running(),"packed HAS reopens the frozen prop as native root data with physics off")
	check(Drawing.cel_at(app.layers[1],0).image.get_data()==paint and (not audio_tested or app.audio_clip.start_frame==24 and app.audio_clip.gain_db==-6),"packed prop scene preserves editable RGBA drawing and independent WAV timing")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);reference.save_png(folder.path_join("reopened.png"))
	var export_error: String=await app.export_movie(folder)
	var exported:=Image.load_from_file(app.last_export_folder.path_join("frame_000001.png"))
	check(export_error.is_empty() and exported.get_data()==reference.get_data(),"frozen prop renders into MP4 using the exact reopened preview")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.world_selection.select_entity(id);enable(app,id);await settled();simulation=physics.simulations[id];body=simulation.body
	var point: Vector2=app.renderer.camera.unproject_position(body.global_position)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,point);await settled()
	check(physics.grabbing() and physics.grabbed==body,"actual viewport click grabs a rigid prop using the same control as ragdolls")
	var start:=body.global_position;var motion:=InputEventMouseMotion.new();app.canvas_input(motion,point-Vector2(0,130))
	for i in range(120):await physics_frame
	check(body.global_position.y>start.y+0.4,"cursor movement lifts a rigid prop against gravity")
	var release:=InputEventMouseButton.new();release.button_index=MOUSE_BUTTON_LEFT;release.pressed=false;release.position=Vector2(-20,-20);app._input(release)
	check(not physics.grabbing() and physics.active(id),"outside release drops the prop while live physics continues")
	physics.freeze_all();app.undo()
	# A static rotated/scaled parent must not become part of the physics body's moving ancestry.
	var world: Dictionary=app.renderer.world_state();var parent:=Model.definition(asset);parent.id="prop-parent";parent.kind="group";parent.parent_id="";parent.start_frame=0;parent.position=[2,0,-2];parent.rotation_xyzw=[0,sin(0.35),0,cos(0.35)];parent.scale=1.5
	world.objects.append(parent)
	for row in world.objects:
		if row.id==id:row.parent_id=parent.id;row.position=[0,2,0];row.scale=0.6
	app.restore_world(world);actor=app.renderer.world_runtime.instance(id);var parent_data: Dictionary=app.renderer.world_runtime.instance(parent.id).data.duplicate(true)
	enable(app,id);await settled();simulation=physics.simulations[id]
	for i in range(260):await physics_frame
	var global_frozen: Transform3D=simulation.body.global_transform*simulation.visual_offset
	physics.freeze(id);await settled()
	check(actor.root.global_transform.is_equal_approx(global_frozen) and is_equal_approx(float(actor.data.scale),0.6),"freeze converts world physics back through a rotated uniformly scaled parent")
	check(app.renderer.world_runtime.instance(parent.id).data==parent_data,"child prop simulation never edits its parent group")
	var old_scale: Vector3=actor.root.scale;var children: int=app.renderer.world.get_child_count();var unchanged: Dictionary=actor.data.duplicate(true)
	actor.root.scale=Vector3(1,2,1);var rejected:=Prop.create(actor,app.renderer.world,app.frame);actor.root.scale=old_scale
	check(rejected.has("error") and app.renderer.world.get_child_count()==children and actor.data==unchanged,"unsupported scale is rejected before creating a proxy or changing the model")
	actor.root.visible=false;physics.change(true)
	check(not physics.active(id) and not physics.toggle.button_pressed,"hidden prop activation fails visibly without leaving a checked Physics control")
	actor.root.visible=true
	var mesh_instance: MeshInstance3D=actor.opacity_materials.meshes[0];var original_mesh: Mesh=mesh_instance.mesh
	var dense:=BoxMesh.new();dense.size=Vector3(0.8,0.8,0.8);dense.subdivide_width=45;dense.subdivide_height=45;dense.subdivide_depth=45
	var dense_mesh:=ArrayMesh.new();dense_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,dense.surface_get_arrays(0));mesh_instance.mesh=dense_mesh
	var dense_result:=Prop.create(actor,app.renderer.world,app.frame)
	check(not dense_result.has("error") and dense_result.physics.box_fallbacks==1 and dense_result.physics.body.get_child(0).shape is BoxShape3D,"dense collision geometry uses a bounded fitted-box fallback")
	if not dense_result.has("error"):dense_result.physics.dispose()
	var plane:=PlaneMesh.new();var plane_mesh:=ArrayMesh.new();plane_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,plane.surface_get_arrays(0));mesh_instance.mesh=plane_mesh
	var mesh_transform: Transform3D=mesh_instance.transform;mesh_instance.rotation=Vector3(0.3,0.4,0.5);children=app.renderer.world.get_child_count()
	var flat:=Prop.create(actor,app.renderer.world,app.frame)
	check(flat.has("error") and app.renderer.world.get_child_count()==children,"tilted flat geometry is rejected before it reaches the solid-body solver")
	mesh_instance.transform=mesh_transform
	mesh_instance.mesh=original_mesh
	world=app.renderer.world_state()
	for row in world.objects:
		if row.id==parent.id:row.kind="model"
	app.restore_world(world);actor=app.renderer.world_runtime.instance(id)
	enable(app,parent.id);enable(app,id)
	check(physics.active(parent.id) and not physics.active(id) and physics.simulations.size()==1,"a live parent rejects a second nested simulation without affecting the parent")
	physics.freeze_all();app.world_selection.select_entity(id)
	# Existing animated roots get a same-frame draft, preserving every authored key.
	app.world_selection.select_entity(id);app.pose_editor.record_key();app.set_frame(8)
	app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[1].value=3;app.pose_editor.apply_numeric();app.set_frame(4)
	var keys_before: Array=actor.authored_keys();enable(app,id);await settled()
	for i in range(160):await physics_frame
	physics.freeze(id);var draft: Transform3D=actor.root.global_transform;app.set_advanced(true);app.set_advanced(false);await settled()
	check(actor.root.global_transform.is_equal_approx(draft) and actor.authored_keys()==keys_before,"animated prop freeze holds its same-frame root draft across mode switches without overwriting keys")
	app.set_frame(5)
	check(actor.preview_transform.is_empty() and actor.preview_frame==-1 and actor.authored_keys()==keys_before,"scrub clears the temporary physics-root draft and resumes authored animation")
	# Ragdoll contact must actually displace another live object, not just overlap it visually.
	app.new_project();app.load_demo_room();app.mode.select(1);app.change_mode(1)
	var box_ids: Array[String]=[]
	for i in range(3):
		data=Model.definition(asset);data.position=[0,0.42+i*0.82,0];app.append_object(data,"model");box_ids.append(app.last_import_id)
	data=Model.definition(arm_asset);data.position=[-2.3,0.2,0];app.append_object(data,"model");var arm_id: String=app.last_import_id
	for box in box_ids:enable(app,box)
	enable(app,arm_id);await settled()
	check(physics.simulations.size()==4,"three dynamic boxes and a skinned ragdoll simulate independently in one world")
	for i in range(180):await physics_frame
	var contacts: Array=[];var starts:={};var originals:={}
	for box in box_ids:
		body=physics.simulations[box].body;body.contact_monitor=true;body.max_contacts_reported=16
		body.body_entered.connect(func(other):
			if other is PhysicalBone3D:contacts.append(other.get_instance_id()))
		starts[box]=body.global_position;originals[box]=physics.simulations[box].rig.data.duplicate(true)
	for part in physics.simulations[arm_id].bodies.values():part.apply_central_impulse(Vector3(8,1,0))
	var displacement:=0.0
	for i in range(300):
		await physics_frame
		for box in box_ids:
			var offset: Vector3=physics.simulations[box].body.global_position-starts[box]
			displacement=maxf(displacement,Vector2(offset.x,offset.z).length())
	check(not contacts.is_empty() and displacement>0.25,"physical ragdoll contact knocks and displaces live boxes")
	var untouched:=true
	for box in box_ids:untouched=untouched and physics.simulations[box].rig.data==originals[box]
	check(untouched,"impacted boxes still create no keys or authored edits without explicit recording")
	app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,0.7,0));await settled();root.get_texture().get_image().save_png(folder.path_join("ragdoll-boxes.png"))
	physics.freeze(box_ids[0]);check(not physics.active(box_ids[0]) and physics.simulations.size()==3,"selected prop freeze leaves peer boxes and ragdoll running")
	app.set_frame(1);check(not physics.is_running() and physics.colliders==null,"timeline seek safely freezes all remaining props and ragdolls")
	enable(app,box_ids[0]);simulation=physics.simulations[box_ids[0]];unchanged=simulation.rig.data.duplicate(true);history=app.history.size()
	simulation.body.global_position=Vector3(200001,0,0)
	var invalid_save:=folder.path_join("invalid-prop.has");app.has_project.save_file(invalid_save,"packed")
	check(not physics.is_running() and simulation.rig.data==unchanged and app.history.size()==history and not FileAccess.file_exists(invalid_save),"invalid simulated prop roots cannot corrupt authored data, Undo or a saved HAS")
	check(not physics.toggle.button_pressed,"rejected prop freeze immediately clears the Physics control")
	var native_samples:=[]
	var sources: Array=[]
	var css:=ProjectSettings.globalize_path("res://output/source-browser-smoke/project")
	if FileAccess.file_exists(css.path_join("project.json")):
		var loaded:=Storage.load_project(css)
		if not loaded.has("error"):sources.append(World.from_project(loaded).objects[-1])
	var generic:=ProjectSettings.globalize_path("res://output/generic-result.json")
	if FileAccess.file_exists(generic):
		var report=JSON.parse_string(FileAccess.get_file_as_string(generic))
		var converted: String=report.bundles.get("textured.obj","").path_join("scene.glb")
		if FileAccess.file_exists(converted):sources.append(Model.definition(converted))
	for source in sources:
		app.new_project();app.load_demo_room();data=Model.definition(source.source);data.name=source.name;data.metadata=source.metadata.duplicate(true);data.position=[0,3,0]
		var original_sha:=FileAccess.get_sha256(source.source);app.append_object(data,"model");actor=app.renderer.active_model();unchanged=actor.data.duplicate(true)
		enable(app,actor.data.id);await settled()
		check(physics.active(actor.data.id) and physics.simulations[actor.data.id] is Prop,"prepared community prop uses shared rigid-body physics: "+source.name)
		if not physics.active(actor.data.id):continue
		simulation=physics.simulations[actor.data.id];var start_y: float=simulation.body.global_position.y
		for i in range(300):await physics_frame
		check(simulation.body.global_position.y<start_y-0.5 and simulation.body.global_position.y>-0.05 and simulation.body.linear_velocity.length()<0.5,"prepared prop falls and settles on the map: "+source.name)
		physics.freeze(actor.data.id)
		check(actor.data.metadata==unchanged.metadata and actor.data.pose_keys.is_empty() and FileAccess.get_sha256(source.source)==original_sha,"native prop freeze preserves metadata/source and creates no keys: "+source.name)
		native_samples.append(source.name)
	var result:={"checks":checks,"failures":failures,"folder":folder,"movie":movie,"project":project,"ragdoll_contacts":contacts.size(),"max_box_displacement":displacement,"native_samples":native_samples,"audio":audio_tested}
	var file:=FileAccess.open("res://output/physics-props-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("PHYSICS_PROPS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
