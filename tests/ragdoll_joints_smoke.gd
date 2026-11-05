extends SceneTree
const Fixture=preload("res://tests/limb_fixture.gd")
const Model=preload("res://src/model.gd")
const Rig=preload("res://src/physics_rig.gd")
const IK=preload("res://src/limb_ik.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
var metrics:={}
func _initialize() -> void:
	create_timer(240).timeout.connect(func():push_error("Joint watchdog expired");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func drive(actor: RefCounted, id: String, legacy: bool) -> float:
	var created:=Rig.create(actor)
	if created.has("error"):check(false,created.error);return 0
	var simulation: RefCounted=created.physics
	var body: PhysicalBone3D=simulation.bodies[id]
	var parent: String=actor.parent_id(id)
	var fixed: PhysicalBone3D=simulation.bodies[parent]
	var initial: Basis=fixed.global_basis.inverse()*body.global_basis
	var axis: Vector3=body.global_basis*body.joint_offset.basis.z
	var pivot: Vector3=body.global_transform*body.joint_offset.origin
	if legacy:
		body.joint_type=PhysicalBone3D.JOINT_TYPE_NONE
		var offset:=body.joint_offset;offset.basis=Basis.IDENTITY;body.joint_offset=offset
		body.joint_type=PhysicalBone3D.JOINT_TYPE_CONE
		body.set("joint_constraints/swing_span",55.0);body.set("joint_constraints/twist_span",25.0)
	# Remove other physical bodies entirely: in this engine, setting joint type
	# NONE does not clear an already-created server constraint.
	for key in simulation.bodies.keys():
		if key not in [id,parent]:simulation.bodies[key].free();simulation.bodies.erase(key)
	simulation.start()
	for value in simulation.bodies.values():
		value.gravity_scale=0;value.collision_mask=0;value.collision_layer=0
		if value!=body:
			PhysicsServer3D.body_set_mode(value.get_rid(),PhysicsServer3D.BODY_MODE_STATIC)
	var peak:=0.0
	for i in range(90):
		body.angular_velocity=axis*3.0
		body.linear_velocity=(axis*3.0).cross(body.global_position-pivot)
		await physics_frame
		var relative: Basis=fixed.global_basis.inverse()*body.global_basis
		var angle:=rad_to_deg(initial.get_rotation_quaternion().angle_to(relative.get_rotation_quaternion()))
		peak=maxf(peak,angle)
	simulation.dispose();actor.apply(0);await settled()
	return peak
func inspect_actor(app, label: String) -> void:
	var actor: RefCounted=app.renderer.active_model()
	var before: Dictionary=actor.data.duplicate(true)
	var limbs:={};var all_limbs: Array=[];var landmarks:={}
	for tip in actor.order:
		var limb:=IK.chain(actor,tip)
		if not limb.is_empty():all_limbs.append(limb);landmarks[limb.role]=actor.bone_transform(limb.ids[0]).origin
		if not limb.is_empty() and ((limb.role.ends_with("Hand") and not limbs.has("arm")) or (limb.role.ends_with("Foot") and not limbs.has("leg"))):limbs["arm" if limb.role.ends_with("Hand") else "leg"]=limb
	if landmarks.has_all(["leftHand","rightHand","leftFoot","rightFoot"]):
		var forward: Vector3=(landmarks.leftHand-landmarks.rightHand).cross(landmarks.leftHand+landmarks.rightHand-landmarks.leftFoot-landmarks.rightFoot).normalized()
		var simulation: RefCounted=Rig.create(actor).physics
		var planes:=true;var straight:=0
		for limb in all_limbs:
			var ids: Array=limb.ids
			var upper: Vector3=(actor.bone_transform(ids[1]).origin-actor.bone_transform(ids[0]).origin).normalized()
			var lower: Vector3=(actor.bone_transform(ids[2]).origin-actor.bone_transform(ids[1]).origin).normalized()
			var expected:=upper.cross(lower)
			if expected.length()<0.05:
				expected=upper.cross(forward if limb.role.ends_with("Hand") else -forward);straight+=1
			expected=(expected-lower*expected.dot(lower)).normalized()
			var body: PhysicalBone3D=simulation.bodies[ids[1]]
			planes=planes and (body.global_basis*body.joint_offset.basis.z).normalized().dot(expected)>0.999
			var upper_body: PhysicalBone3D=simulation.bodies[ids[0]]
			planes=planes and (upper_body.global_basis*upper_body.joint_offset.basis.x).normalized().dot(upper)>0.999
		check(planes,"actual shoulder/hip twist and elbow/knee hinge frames follow native limb geometry: "+label)
		print("STRAIGHT_PLANES "+label+" "+str(straight))
		simulation.dispose();actor.apply(0);await settled()
	var data:={}
	for part in limbs:
		var limb: Dictionary=limbs[part];var ids: Array=limb.ids
		# A fixed parent and continuous bounded angular drive isolate limits from
		# floor friction, costumes and other limbs. No render-time bone teleports.
		for index in [0,1]:
			if actor.parent_id(ids[index])=="@root":continue
			var old: float=await drive(actor,ids[index],true)
			var improved: float=await drive(actor,ids[index],false)
			data[part+str(index)]={"before":old,"after":improved}
			print("JOINT_METRIC "+label+" "+part+str(index)+" "+JSON.stringify(data[part+str(index)]))
			var increase:=5.0 if part=="leg" and index==0 else 10.0
			var minimum:=70.0 if part=="leg" and index==0 else 80.0
			check(improved>old+increase and improved>minimum,"actual "+label+" "+part+(" shoulder/hip" if index==0 else " elbow/knee")+" rotates beyond its old restricted range")
	check(actor.data==before,"joint probes leave native bindings and authored animation unchanged: "+label)
	var first: Array=limbs.values()[0].ids;var sk: Skeleton3D=actor.bones[first[1]].skeleton
	var index: int=actor.bones[first[1]].index;var position:=sk.get_bone_pose_position(index);var children:=sk.get_child_count()
	sk.set_bone_pose_position(index,Vector3.ZERO);sk.force_update_all_bone_transforms()
	var rejected:=Rig.create(actor)
	check(rejected.has("error") and sk.get_child_count()==children and actor.data==before,"zero-length limb fails before allocating physics bodies: "+label)
	sk.set_bone_pose_position(index,position);actor.apply(0)
	metrics[label]=data
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/joints/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false
	for leg in [false,true]:
		var path:=folder.path_join("leg.glb" if leg else "arm.glb");Fixture.create(path,leg,true);app.new_project();app.append_object(Model.definition(path),"model");await settled();await inspect_actor(app,"authored leg" if leg else "authored arm")
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional joint fixture: "+sample);continue
		var source: Dictionary=World.from_project(Storage.load_project(path)).objects[-1];var original:=Model.new();original.data=source
		var data:=Model.definition(source.source);data.metadata=source.metadata.duplicate(true);data.rotation_xyzw=original.sample_transform(0).rotation_xyzw;data.scale=original.sample_transform(0).scale
		app.new_project();app.append_object(data,"model");await settled();await inspect_actor(app,sample)
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var source: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(source):print("SKIP optional VRM joint sample: "+name);continue
		app.new_project();app.pose_editor.add_model(source)
		while app.source_import.pid>0:await process_frame
		for child in app.get_children():
			if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
		await settled();await inspect_actor(app,name)
	var result:={"checks":checks,"failures":failures,"metrics":metrics,"folder":folder}
	var file:=FileAccess.open("res://output/joints-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close()
	print("RAGDOLL_JOINTS "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
