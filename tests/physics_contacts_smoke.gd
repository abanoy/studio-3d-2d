extends SceneTree
const Fixture=preload("res://tests/torso_fixture.gd")
const Model=preload("res://src/model.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Contacts=preload("res://src/physics_self_collision.gd")
const Rig=preload("res://src/physics_rig.gd")
var checks:=0
var failures:=0
var folder: String
var metrics:={}
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Contact watchdog expired");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func measure(app,data: Dictionary,label: String,legacy: bool) -> Dictionary:
	app.new_project();app.load_demo_room();data=data.duplicate(true);data.position=[0,3,0];app.append_object(data,"model")
	var actor: RefCounted=app.renderer.active_model();var before: Dictionary=actor.data.duplicate(true);var digest:=FileAccess.get_sha256(actor.data.source)
	app.physics_editor.change(true)
	var simulation: RefCounted=app.physics_editor.simulations[actor.data.id]
	if legacy:
		for pair in simulation.rest_exclusions:simulation.bodies[pair[0]].remove_collision_exception_with(simulation.bodies[pair[1]])
	var pairs: Array=simulation.rest_exclusions.duplicate(true)
	var valid:=true
	for pair in pairs:
		valid=valid and Contacts.nearby(actor,pair[0],pair[1]) and Contacts.overlapping(simulation.bodies[pair[0]].get_child(0),simulation.bodies[pair[1]].get_child(0))
	check(valid,"only nearby initially overlapping proxy shapes gain exceptions: "+label)
	for i in range(360):await physics_frame
	var pose: Dictionary=simulation.pose();var max_strain:=0.0;var helper_strain:=0.0;var speed:=0.0
	for id in pose:
		var parent: String=actor.parent_id(id)
		if parent=="@root":continue
		var offset:=Timeline.vector(pose[id].position)-Timeline.vector(simulation.initial_pose.get(id,Model.identity()).position)
		var distance: float=(simulation.skeleton.global_basis*simulation.latest[parent].basis*offset).length()
		if simulation.bodies.has(id):
			# A free physical root (VRM hips below a nonphysical scene root)
			# moves through space; its fall is not separation at a physical joint.
			if simulation.bodies.has(parent):max_strain=maxf(max_strain,distance)
		else:helper_strain=maxf(helper_strain,distance)
	for body in simulation.bodies.values():speed=maxf(speed,body.linear_velocity.length())
	var center:=Vector3.ZERO
	for body in simulation.bodies.values():center+=body.global_position
	center/=simulation.bodies.size()
	app.renderer.camera.position=center+Vector3(1.4,0.8,2);app.renderer.camera.look_at(center)
	var count:=pairs.size();app.physics_editor.change(false);await settled()
	check(actor.data.pose_keys.is_empty() and actor.data.metadata==before.metadata and FileAccess.get_sha256(data.source)==digest,"contact setup preserves native data/source and never records motion implicitly: "+label)
	var image: Image=await app.renderer.capture([Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,55)],[],0,true)
	image.save_png(folder.path_join(label+"-"+("before" if legacy else "after")+".png"))
	return {"strain":max_strain,"helper_strain":helper_strain,"speed":speed,"pairs":count}
func compare(app,data: Dictionary,label: String) -> void:
	var before: Dictionary=await measure(app,data,label,true);var after: Dictionary=await measure(app,data,label,false)
	metrics[label]={"before":before,"after":after}
	print("CONTACT_METRIC "+label+" "+JSON.stringify(metrics[label]))
	if label in ["authored","sfm-smoke"]:check(after.pairs>0 and after.strain<0.005 and after.strain<before.strain*0.25,"reproduced joint stretch drops below five millimeters and to less than one quarter: "+label)
	else:check(after.strain<0.005,"native control rig keeps joint separation below five millimeters: "+label)
	check(after.helper_strain<0.00001 and after.speed<2,"helper bones follow normally and the improved ragdoll settles: "+label)
func geometry(app) -> void:
	var bodies: Array=[]
	for i in range(2):
		var body:=StaticBody3D.new();body.collision_layer=8;body.collision_mask=0;app.renderer.world.add_child(body)
		var collision:=CollisionShape3D.new();collision.shape=BoxShape3D.new();collision.shape.size=Vector3(2,0.2,0.1);body.add_child(collision);bodies.append(body)
	var cases: Array=[[Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,true],[Vector3.ZERO,Vector3.ZERO,Vector3(3,0,0),false],[Vector3(0,PI/4,0),Vector3(0,PI/4,0),Vector3(0.15,0,0.15),false],[Vector3.ZERO,Vector3(0,PI/2,0),Vector3.ZERO,true]]
	for c in cases:
		bodies[0].rotation=c[0];bodies[1].rotation=c[1];bodies[1].position=c[2];await physics_frame
		var query:=PhysicsShapeQueryParameters3D.new();query.shape=bodies[0].get_child(0).shape;query.transform=bodies[0].get_child(0).global_transform;query.collision_mask=8;query.exclude=[bodies[0].get_rid()]
		var engine: bool=not app.renderer.viewport.find_world_3d().direct_space_state.intersect_shape(query,4).is_empty()
		check(engine==c[3] and Contacts.overlapping_boxes(bodies[0].get_child(0),bodies[1].get_child(0))==engine,"rotated-box overlap agrees with actual Jolt shape query")
	for types in [["sphere","sphere"],["sphere","capsule"],["capsule","capsule"],["capsule","box"]]:
		for i in range(2):
			var shape: Shape3D
			if types[i]=="sphere":shape=SphereShape3D.new();shape.radius=0.2
			elif types[i]=="capsule":shape=CapsuleShape3D.new();shape.radius=0.15;shape.height=1
			else:shape=BoxShape3D.new();shape.size=Vector3(1,0.4,0.3)
			bodies[i].get_child(0).shape=shape
		bodies[0].rotation=Vector3(0.3,0.6,0.2);bodies[1].rotation=Vector3(-0.4,0.1,0.8)
		for offset in [0.0,3.0]:
			bodies[1].position=Vector3(offset,0,0);await physics_frame
			var query:=PhysicsShapeQueryParameters3D.new();query.shape=bodies[0].get_child(0).shape;query.transform=bodies[0].get_child(0).global_transform;query.collision_mask=8;query.exclude=[bodies[0].get_rid()]
			var engine: bool=not app.renderer.viewport.find_world_3d().direct_space_state.intersect_shape(query,4).is_empty()
			var collision: bool=Contacts.overlapping(bodies[0].get_child(0),bodies[1].get_child(0))
			check(engine==(offset==0.0) and collision==engine and collision==Contacts.overlapping(bodies[1].get_child(0),bodies[0].get_child(0)),"round-shape overlap agrees symmetrically with Jolt: "+str(types))
	for body in bodies:body.free()
func loose_fitting(app) -> void:
	var asset:=folder.path_join("original-loose-parts.glb");Fixture.create(asset,true)
	app.new_project();app.append_object(Model.definition(asset),"model");var actor: RefCounted=app.renderer.active_model()
	var created:=Rig.create(actor);check(not created.has("error"),"authored loose-part fixture uses the same standard rig adapter")
	if created.has("error"):return
	var simulation: RefCounted=created.physics;var chosen: Array[String]=[];var ids:={}
	for id in simulation.bodies:chosen.append(id);ids[preload("res://src/limb_ik.gd").normalized(actor.bones[id].name)]=id
	var original:=Rig.weighted_bounds(actor,simulation.skeleton,chosen,true)
	var fitted:=Rig.weighted_bounds(actor,simulation.skeleton,chosen)
	check(fitted[ids.head].size.y<0.35 and original[ids.head].size.y>1.5,"loose spring-weighted hair no longer inflates the rigid head collider")
	check(fitted[ids.upperarml].size.z<0.3 and original[ids.upperarml].size.z>0.5,"loose sleeve helpers do not become rigid upper-arm volume")
	check(fitted[ids.handl].size.x>0.8,"known finger weights still extend the hand collision fit")
	check(not Rig.body_weight_helper("spring_tip") and not Rig.body_weight_helper("HoodString") and not Rig.body_weight_helper("hlp_sleeve") and Rig.body_weight_helper("bip_ring_0_L") and Rig.body_weight_helper("bip_bicep_twist_01_L"),"spring/string names remain distinct from ring fingers and structural twists")
	var far_a: String=ids.hips;var far_b: String=ids.handl;var body: PhysicalBone3D=simulation.bodies[far_b];var saved:=body.global_transform
	body.global_position=simulation.bodies[far_a].global_position
	check(Contacts.overlapping(simulation.bodies[far_a].get_child(0),body.get_child(0)),"distant-part collision stress setup actually overlaps proxy shapes")
	Contacts.apply(actor,simulation.bodies)
	check(not simulation.bodies[far_a].get_collision_exceptions().has(body) and not body.get_collision_exceptions().has(simulation.bodies[far_a]),"distant body parts remain collidable even when brought into overlap")
	body.global_transform=saved;simulation.dispose()
func run() -> void:
	folder=ProjectSettings.globalize_path("res://output/physics-contacts/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false
	await geometry(app)
	await loose_fitting(app)
	var asset:=folder.path_join("original-torso.glb");check(Fixture.create(asset)==OK,"original overlapping torso fixture writes a standard skinned GLB")
	await compare(app,Model.definition(asset),"authored")
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional contact sample: "+sample);continue
		var source: Dictionary=World.from_project(Storage.load_project(path)).objects[-1];var model:=Model.new();model.data=source
		var data:=Model.definition(source.source);data.metadata=source.metadata.duplicate(true);data.rotation_xyzw=model.sample_transform(0).rotation_xyzw;data.scale=model.sample_transform(0).scale
		await compare(app,data,sample.split("/")[0])
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP optional VRM contact sample: "+name);continue
		var digest:=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path)
		while app.source_import.pid>0:await process_frame
		for child in app.get_children():
			if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
		await settled();var data: Dictionary=app.renderer.active_model().data.duplicate(true)
		await compare(app,data,name.trim_suffix(".vrm"));check(FileAccess.get_sha256(path)==digest,"VRM source bytes remain unchanged: "+name)
	var result:={"checks":checks,"failures":failures,"folder":folder,"metrics":metrics}
	var output:=FileAccess.open("res://output/physics-contacts-result.json",FileAccess.WRITE);output.store_string(JSON.stringify(result));output.close()
	print("PHYSICS_CONTACTS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
