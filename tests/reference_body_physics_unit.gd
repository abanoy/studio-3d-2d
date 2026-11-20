extends SceneTree
# Independent real-engine oracles. Expected geometry is derived from the fixture's
# source constants and FK, never ReferenceBodyPlan or PhysicsRig geometry helpers.
const Model=preload("res://src/model.gd")
const ImportBasis=preload("res://src/import_basis.gd")
const Rig=preload("res://src/physics_rig.gd")
const PoseBounds=preload("res://src/pose_bounds.gd")
const SHA="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
const NAMES=["upper_arm.L","arm_twist","forearm.L","hand.L"]
const REST_POINTS=[Vector3(0,1,0),Vector3(.08,.02,.01),Vector3(.72,.13,-.02),Vector3(.8,-.15,.03)]
const REST_ANGLES=[Vector3(.04,-.03,.1),Vector3(-.07,.04,.03),Vector3(.02,.08,-.11),Vector3(.05,.01,.04)]
const POSE_POINTS=[Vector3(.03,-.02,.01),Vector3(.004,.002,-.001),Vector3(-.01,.015,.004),Vector3(.004,-.003,.005)]
const POSE_ANGLES=[Vector3(.02,-.04,.03),Vector3(-.02,.01,.02),Vector3(.03,.02,-.08),Vector3(.01,-.03,.04)]
const BOX_CENTER=Vector3(.21,.02,-.03)
const BOX_SIZE=Vector3(.42,.16,.12)
const EPS=.00003
const ANGLE_EPS=.0005
var checks:=0
var failures:=0
var max_position_error:=0.0
var max_basis_error:=0.0
var max_relative_basis_error:=0.0
var max_pose_world_error:=0.0
var max_pose_angle_error:=0.0
var max_collision_error:=0.0
var fixed_tick_cases:=0

func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Reference body physics watchdog expired");quit(2))
	call_deferred("run")

func rotation(angles: Vector3) -> Basis:
	return Basis.from_euler(angles)

func height_for_factor(factor: float) -> String:
	if factor==.001:return "1828.8"
	if factor==.5:return "3.6576"
	if factor==1:return "1.8288"
	if factor==2:return "0.9144"
	if factor==1000:return "0.0018288"
	return "invalid-test-factor"

func pose_entry(point: Vector3,angles: Vector3) -> Dictionary:
	var q:=rotation(angles).get_rotation_quaternion()
	return {"position":[point.x,point.y,point.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}

func local_rest(index: int,raw_units: float,helper_scale: float,root_bone_scale:=1.0) -> Transform3D:
	var scale: float=root_bone_scale if index==0 else helper_scale if index==1 else 1.0
	var origin_units: float=raw_units*(root_bone_scale if index==0 else 1.0)
	return Transform3D(rotation(REST_ANGLES[index]).scaled(Vector3.ONE*scale),REST_POINTS[index]*origin_units)

func source_globals(raw_units: float,helper_scale: float,pose: Dictionary,ids: Array[String],root_bone_scale:=1.0) -> Array[Transform3D]:
	var result: Array[Transform3D]=[]
	for i in range(NAMES.size()):
		var rest:=local_rest(i,raw_units,helper_scale,root_bone_scale)
		var delta: Dictionary=pose.get(ids[i],Model.identity())
		var q:=Quaternion(float(delta.rotation_xyzw[0]),float(delta.rotation_xyzw[1]),float(delta.rotation_xyzw[2]),float(delta.rotation_xyzw[3])).normalized()
		var point:=Vector3(float(delta.position[0]),float(delta.position[1]),float(delta.position[2]))
		var scale: float=root_bone_scale if i==0 else helper_scale if i==1 else 1.0
		var local:=Transform3D((rotation(REST_ANGLES[i])*Basis(q)).scaled(Vector3.ONE*scale),rest.origin+point)
		result.append(local if i==0 else result[i-1]*local)
	return result

func corners(center: Vector3,size: Vector3) -> PackedVector3Array:
	var result:=PackedVector3Array()
	for x in [-.5,.5]:
		for y in [-.5,.5]:
			for z in [-.5,.5]:result.append(center+size*Vector3(x,y,z))
	return result

func fixture(factor: float,artist_scale:=1.0,parent_scale:=1.0,raw_units:=1.0,helper_scale:=1.0,reference:=true,root_bone_scale:=1.0) -> Dictionary:
	var actor:=Model.new()
	var artist_rotation:=rotation(Vector3(-.2,.4,.13));var artist_q:=artist_rotation.get_rotation_quaternion()
	# Keep the outer translation fixed when redistributing linear scale into a
	# static parent. Otherwise compensation would accidentally move the actor.
	var artist_position:=Vector3(.45,-.1,.25)/parent_scale
	actor.data={"format":"studio_model_1","id":"reference_body_fixture","name":"Authored reference arm","kind":"model","parent_id":"","start_frame":0,"source":"res://synthetic-not-read.glb","sha256":SHA,"position":[artist_position.x,artist_position.y,artist_position.z],"rotation_xyzw":[artist_q.x,artist_q.y,artist_q.z,artist_q.w],"scale":artist_scale,"visible":true,"reference_only":false,"pose":{},"pose_keys":[],"draft_frame":0,"metadata":{}}
	if reference:actor.data["asset_basis"]=ImportBasis.create_record(SHA,height_for_factor(factor)).record
	actor.root=Node3D.new();actor.root.name="ReferenceBodyFixture"
	var sk:=Skeleton3D.new();sk.name="Rig"
	# A source root-bone scale can compensate C while the skeleton itself stays
	# scaled. Keep the same world figure by compensating only source placements
	# outside that bone; its children and mesh retain their original local units.
	var outer_units: float=raw_units*root_bone_scale
	var skeleton_local:=Transform3D(rotation(Vector3(-.11,.18,.05)),Vector3(-.13,.27,.09)*outer_units)
	sk.transform=skeleton_local;actor.root.add_child(sk)
	for i in range(NAMES.size()):
		sk.add_bone(NAMES[i]);sk.set_bone_rest(i,local_rest(i,raw_units,helper_scale,root_bone_scale))
		if i>0:sk.set_bone_parent(i,i-1)
	sk.reset_bone_poses()
	# Eight real skinned vertices are sufficient to give the helper a full AABB.
	# The first segment deliberately crosses the OLD raw .0001 child cutoff when
	# raw_units=.001; its physical length remains approximately .086 metres.
	var vertices:=corners(BOX_CENTER*raw_units,BOX_SIZE*raw_units)
	var helper_rest: Transform3D=local_rest(0,raw_units,helper_scale,root_bone_scale)*local_rest(1,raw_units,helper_scale,root_bone_scale)
	for i in range(vertices.size()):vertices[i]=helper_rest*vertices[i]
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices
	arrays[Mesh.ARRAY_INDEX]=PackedInt32Array([0,1,3,0,3,2,4,6,7,4,7,5,0,4,5,0,5,1,2,3,7,2,7,6,0,2,6,0,6,4,1,5,7,1,7,3])
	var bind_indices:=PackedInt32Array();var weights:=PackedFloat32Array()
	bind_indices.resize(vertices.size()*4);weights.resize(vertices.size()*4)
	for i in range(vertices.size()):bind_indices[i*4]=1;weights[i*4]=1.0
	arrays[Mesh.ARRAY_BONES]=bind_indices;arrays[Mesh.ARRAY_WEIGHTS]=weights
	var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	var instance:=MeshInstance3D.new();instance.name="WeightedHelper";instance.mesh=mesh
	actor.root.add_child(instance);instance.skeleton=instance.get_path_to(sk);instance.skin=sk.create_skin_from_rest_transforms()
	var raw_root:=Transform3D(rotation(Vector3(.15,-.25,.08)),Vector3(.7,-.2,.4)*outer_units)
	check(actor.capture_import_root(raw_root).is_empty(),"fixture captures immutable rotated/translated B0")
	actor.inventory(actor.root)
	for i in range(NAMES.size()):actor.data.pose[actor.order[i]]=pose_entry(POSE_POINTS[i]*(outer_units if i==0 else raw_units),POSE_ANGLES[i])
	var parent:=Node3D.new()
	var parent_transform:=Transform3D(rotation(Vector3(.3,.15,-.2)).scaled(Vector3.ONE*parent_scale),Vector3(1.1,3.2,-.6))
	parent.transform=parent_transform;root.add_child(parent);parent.add_child(actor.root)
	actor.apply(0,false,true)
	var artist:=Transform3D(artist_rotation.scaled(Vector3.ONE*artist_scale),artist_position)
	var source_to_world:=parent_transform*artist*Transform3D(Basis.IDENTITY.scaled(Vector3.ONE*(factor if reference else 1.0)),Vector3.ZERO)*raw_root*skeleton_local
	return {"actor":actor,"sk":sk,"parent":parent,"mesh":instance,"factor":factor,"artist_scale":artist_scale,"parent_scale":parent_scale,"raw_units":raw_units,"helper_scale":helper_scale,"root_bone_scale":root_bone_scale,"reference":reference,"source_to_world":source_to_world,"raw_root":raw_root}

func source_snapshot(f: Dictionary) -> Dictionary:
	var actor: RefCounted=f.actor;var bases: Array=[];var poses: Array=[];var binds: Array=[]
	for id in actor.order:
		bases.append(actor.bones[id].base);poses.append(actor.bones[id].skeleton.get_bone_pose(actor.bones[id].index))
	for i in range(f.mesh.skin.get_bind_count()):binds.append([f.mesh.skin.get_bind_bone(i),f.mesh.skin.get_bind_name(i),f.mesh.skin.get_bind_pose(i)])
	return {"data":var_to_bytes(actor.data),"base":actor.base_root,"raw":actor.raw_import_root,"order":actor.order.duplicate(),"bone_bases":bases,"evaluated_poses":poses,"mesh":var_to_bytes(f.mesh.mesh.surface_get_arrays(0)),"skin":var_to_bytes(binds),"root":actor.root.transform,"skeleton":f.sk.transform}

func atomic_snapshot(f: Dictionary) -> Dictionary:
	var result:=source_snapshot(f);var nodes: Array=[];var pending: Array=[f.actor.root];var poses: Array=[]
	while not pending.is_empty():
		var node: Node=pending.pop_back();nodes.append(node.get_instance_id());pending.append_array(node.get_children(true))
	for i in range(f.sk.get_bone_count()):poses.append(f.sk.get_bone_pose(i))
	result["nodes"]=nodes;result["poses"]=poses;result["live_pose"]=var_to_bytes(f.actor.live_pose);result["live_world"]=f.actor.live_world_transform
	result["final_pose"]=f.sk.get_meta(PoseBounds.FINAL_META) if f.sk.has_meta(PoseBounds.FINAL_META) else null
	result["secondary"]=f.actor.root.get_meta("has_secondary_rig",{}).duplicate(true)
	return result

func basis_error(a: Basis,b: Basis) -> float:
	return maxf(a.x.distance_to(b.x),maxf(a.y.distance_to(b.y),a.z.distance_to(b.z)))

func frame_close(actual: Transform3D,expected: Transform3D,label: String) -> void:
	var position_error:=actual.origin.distance_to(expected.origin);var orientation_error:=basis_error(actual.basis,expected.basis)
	var basis_scale:=maxf(1.0,maxf(expected.basis.x.length(),maxf(expected.basis.y.length(),expected.basis.z.length())))
	max_position_error=maxf(max_position_error,position_error);max_basis_error=maxf(max_basis_error,orientation_error)
	max_relative_basis_error=maxf(max_relative_basis_error,orientation_error/basis_scale)
	check(position_error<EPS and orientation_error<EPS*basis_scale,label+" (position="+str(position_error)+", basis="+str(orientation_error)+")")

func unit_frame(transform: Transform3D,label: String) -> void:
	var b:=transform.basis
	check(absf(b.x.length()-1)<EPS and absf(b.y.length()-1)<EPS and absf(b.z.length()-1)<EPS and absf(b.x.dot(b.y))<EPS and absf(b.x.dot(b.z))<EPS and absf(b.y.dot(b.z))<EPS and absf(b.determinant()-1)<EPS,label)

func worlds(f: Dictionary,pose: Dictionary) -> Array[Transform3D]:
	var source:=source_globals(f.raw_units,f.helper_scale,pose,f.actor.order,f.root_bone_scale)
	var result: Array[Transform3D]=[]
	for transform in source:result.append(f.source_to_world*transform)
	return result

func expected_geometry(f: Dictionary,legacy:=false) -> Array[Dictionary]:
	var actor: RefCounted=f.actor;var global_source:=source_globals(f.raw_units,f.helper_scale,actor.data.pose,actor.order,f.root_bone_scale)
	var bone_world:=worlds(f,actor.data.pose)
	var scale: float=1.0 if legacy else f.source_to_world.basis.x.length()
	var minimum:=Vector3(INF,INF,INF);var maximum:=-minimum
	for transform in global_source:
		minimum=minimum.min(transform.origin*scale);maximum=maximum.max(transform.origin*scale)
	var size:=maxf(minimum.distance_to(maximum),.01)
	var result: Array[Dictionary]=[]
	for i in range(NAMES.size()):
		var raw: Transform3D=global_source[i];var w: Transform3D=bone_world[i]
		var unit_bone:=Transform3D(w.basis.orthonormalized(),w.origin)
		var direction:=Vector3.ZERO
		if i+1<NAMES.size():
			direction=raw.affine_inverse()*global_source[i+1].origin if legacy else unit_bone.affine_inverse()*bone_world[i+1].origin
		var length:=direction.length();var radius:=clampf(length*.16,size*.012,size*.045)
		var row: Dictionary={"bone_world":w,"size_policy":size}
		if i==1:
			row.kind="box"
			var bone_scale:=1.0 if legacy else w.basis.x.length()
			row.dimensions=BOX_SIZE*f.raw_units*bone_scale+Vector3.ONE*size*.003
			row.margin=minf(.005,minf(row.dimensions.x,minf(row.dimensions.y,row.dimensions.z))*.025)
			row.frame=Transform3D(w.basis.orthonormalized(),w*(BOX_CENTER*f.raw_units))
		elif i<NAMES.size()-1:
			row.kind="capsule";row.radius=radius;row.height=maxf(2*radius,length*.9)
			var offset:=Transform3D(Basis(Quaternion(Vector3.UP,direction.normalized())),direction*.45)
			row.frame=(w*offset).orthonormalized() if legacy else unit_bone*offset
		else:
			row.kind="sphere";row.radius=size*.035;row.frame=unit_bone
		result.append(row)
	return result

func expected_joint_basis(f: Dictionary,index: int) -> Basis:
	var g:=source_globals(f.raw_units,f.helper_scale,f.actor.data.pose,f.actor.order,f.root_bone_scale)
	var upper: Vector3=(g[2].origin-g[0].origin).normalized()
	var lower: Vector3=(g[3].origin-g[2].origin).normalized()
	var axis: Vector3=upper if index==0 else lower
	var profile: Basis
	if index==2:
		axis=upper.cross(lower).normalized()
		profile=Basis(lower,axis.cross(lower).normalized(),axis)
	else:
		if index==1:axis=g[1].basis.x.normalized()
		var y:=axis.cross(Vector3.FORWARD)
		if y.length()<.05:y=axis.cross(Vector3.UP)
		y=y.normalized();profile=Basis(axis,y,axis.cross(y).normalized())
	return f.source_to_world.basis.orthonormalized()*profile

func verify_shapes(f: Dictionary,simulation: RefCounted,legacy:=false) -> Array:
	var expected:=expected_geometry(f,legacy);var signature: Array=[]
	check(simulation.bodies.size()==NAMES.size() and simulation.rig==f.actor and simulation.skeleton==f.sk and simulation.simulator.get_parent()==f.sk,"existing canonical rig owns all three limb joints and the fixed helper")
	for i in range(NAMES.size()):
		var id: String=f.actor.order[i];var body: PhysicalBone3D=simulation.bodies[id];var row: Dictionary=expected[i]
		var shape: Shape3D=body.get_child(0).shape
		unit_frame(body.global_transform,"physical body has a positive unit world frame: "+str(i))
		frame_close(body.global_transform,row.frame,"independent physical center/orientation: "+str(i))
		if row.kind=="box":
			check(shape is BoxShape3D,"full-weight helper retains a fitted box")
			if shape is BoxShape3D:
				check(shape.size.distance_to(row.dimensions)<EPS and absf(shape.margin-row.margin)<EPS,"box dimensions/padding/margin are in the expected units")
				var actual_corners:=corners(Vector3.ZERO,shape.size);var expected_corners:=corners(Vector3.ZERO,row.dimensions)
				var error:=0.0
				for j in range(actual_corners.size()):error=maxf(error,(body.global_transform*actual_corners[j]).distance_to(row.frame*expected_corners[j]))
				check(error<EPS,"all eight independent world box corners agree")
				signature.append({"kind":"box","size":shape.size,"frame":body.global_transform,"margin":shape.margin})
		elif row.kind=="capsule":
			check(shape is CapsuleShape3D,"eligible physical child retains a capsule: "+str(i))
			if shape is CapsuleShape3D:
				check(absf(shape.radius-row.radius)<EPS and absf(shape.height-row.height)<EPS,"capsule radius/height use metric thresholds: "+str(i))
				var error:=0.0
				for sign_value in [-1,1]:error=maxf(error,(body.global_transform*Vector3(0,sign_value*(shape.height*.5-shape.radius),0)).distance_to(row.frame*Vector3(0,sign_value*(row.height*.5-row.radius),0)))
				check(error<EPS,"capsule hemisphere centers agree independently: "+str(i))
				signature.append({"kind":"capsule","radius":shape.radius,"height":shape.height,"frame":body.global_transform})
		else:
			check(shape is SphereShape3D,"terminal joint uses a sphere")
			if shape is SphereShape3D:
				check(absf(shape.radius-row.radius)<EPS,"terminal radius uses the physical skeleton span")
				signature.append({"kind":"sphere","radius":shape.radius,"frame":body.global_transform})
		if not legacy:
			frame_close(body.global_transform*body.body_offset.affine_inverse(),row.bone_world,"reciprocal offset reconstructs the complete source world bone: "+str(i))
			var joint_world:=body.global_transform*body.joint_offset
			unit_frame(joint_world,"joint frame has no inverse-scale residue: "+str(i))
			frame_close(joint_world,Transform3D(expected_joint_basis(f,i),row.bone_world.origin),"joint axes and pivot agree with independent anatomy: "+str(i))
	return signature

func verify_pose(f: Dictionary,state: Dictionary,expected_world: Array[Transform3D],label: String) -> void:
	check(state.size()==NAMES.size(),label+": canonical pose covers exactly the original joints")
	if state.size()!=NAMES.size():return
	for id in f.actor.order:
		if not state.has(id):check(false,label+": missing canonical ID");return
	var actual_world:=worlds(f,state);var position_error:=0.0;var angle_error:=0.0
	for i in range(NAMES.size()):
		position_error=maxf(position_error,actual_world[i].origin.distance_to(expected_world[i].origin))
		var relative:=actual_world[i].basis.orthonormalized().get_rotation_quaternion().inverse()*expected_world[i].basis.orthonormalized().get_rotation_quaternion()
		angle_error=maxf(angle_error,2*atan2(Vector3(relative.x,relative.y,relative.z).length(),absf(relative.w)))
		check(absf(actual_world[i].basis.x.length()-expected_world[i].basis.x.length())<EPS*maxf(1.0,expected_world[i].basis.x.length()),label+": source local scale is retained: "+str(i))
	max_pose_world_error=maxf(max_pose_world_error,position_error);max_pose_angle_error=maxf(max_pose_angle_error,angle_error)
	check(position_error<EPS and angle_error<ANGLE_EPS,label+": independent source FK preserves world pivots/orientation (position="+str(position_error)+", angle="+str(angle_error)+")")
	var mesh_error:=0.0
	for corner in corners(BOX_CENTER*f.raw_units,BOX_SIZE*f.raw_units):mesh_error=maxf(mesh_error,(actual_world[1]*corner).distance_to(expected_world[1]*corner))
	check(mesh_error<EPS,label+": independent full-weight skin corners retain world positions")

func collision_queries(f: Dictionary,simulation: RefCounted,label: String) -> void:
	# The ray starts on the known +X normal through a face/cylinder/sphere center.
	# These analytic surfaces are independent of shape resource inspection. Jolt
	# must hit the actual body at the expected world surface, not merely accept
	# the requested dimensions. Other bodies are excluded by RID, never by name.
	var expected:=expected_geometry(f);var direct: PhysicsDirectSpaceState3D=f.actor.root.get_world_3d().direct_space_state
	for i in range(NAMES.size()):
		var row: Dictionary=expected[i];var body: PhysicalBone3D=simulation.bodies[f.actor.order[i]]
		var extent: float=row.dimensions.x*.5 if row.kind=="box" else row.radius
		var excluded: Array[RID]=[]
		for other in simulation.bodies.values():
			if other!=body:excluded.append(other.get_rid())
		var start: Vector3=row.frame*Vector3(extent+.1,0,0)
		var target: Vector3=row.frame.origin
		var ray:=PhysicsRayQueryParameters3D.create(start,target,2,excluded)
		var hit: Dictionary=direct.intersect_ray(ray)
		check(not hit.is_empty() and hit.get("collider")==body,label+": real collision ray identifies shape "+str(i))
		if not hit.is_empty():
			var surface: Vector3=row.frame*Vector3(extent,0,0)
			var error: float=surface.distance_to(hit.position);max_collision_error=maxf(max_collision_error,error)
			check(error<.001,label+": independent analytic collision surface agrees: "+str(i)+" (metres="+str(error)+")")

func exercise(f: Dictionary,label: String,fixed_ticks:=true) -> Array:
	var actor: RefCounted=f.actor;var before:=source_snapshot(f);var authored_world:=worlds(f,actor.data.pose)
	for i in range(NAMES.size()):frame_close(actor.bone_transform(actor.order[i]),authored_world[i],label+": fixture FK independently agrees before physics")
	var result: Dictionary=Rig.create(actor)
	check(result.has("physics") and not result.has("error"),label+": active reference is admitted: "+str(result.get("error","")))
	if not result.has("physics"):f.parent.free();return []
	var simulation: RefCounted=result.physics
	check(source_snapshot(f)==before and actor.live_pose==null and actor.live_world_transform==null,label+": allocation preserves data, bases, B0/C, source mesh/skin and inactive live state")
	var signature:=verify_shapes(f,simulation)
	verify_pose(f,simulation.capture_pose(),authored_world,label+": capture before stepping")
	# Apply one known rigid world motion to EVERY body so constraints remain valid.
	# The expected source pose is reconstructed independently, rather than using
	# the candidate's body_offset as the expected-value generator.
	var motion:=Transform3D(Basis(Vector3(0,1,0),.17),Vector3(.04,.08,-.03))
	var moved_world: Array[Transform3D]=[]
	for i in range(NAMES.size()):
		var body: PhysicalBone3D=simulation.bodies[actor.order[i]]
		body.global_transform=motion*body.global_transform;moved_world.append(motion*authored_world[i])
	var moved_pose: Dictionary=simulation.capture_pose()
	verify_pose(f,moved_pose,moved_world,label+": known rigid body translation/rotation writeback")
	actor.live_pose=moved_pose;actor.apply(0,false,false)
	for i in range(NAMES.size()):frame_close(actor.bone_transform(actor.order[i]),moved_world[i],label+": real Model applies captured source pose without a second C")
	actor.live_pose=null;actor.apply(0,false,true)
	if fixed_ticks:
		for body in simulation.bodies.values():body.gravity_scale=0.0
		simulation.start()
		verify_pose(f,simulation.capture_pose(),authored_world,label+": start resets to the authored pose before gravity")
		for i in range(4):await physics_frame
		verify_pose(f,simulation.capture_pose(),authored_world,label+": fixed-tick rest capture retains the authored pose with gravity disabled")
		collision_queries(f,simulation,label)
		var stopped: Dictionary=simulation.stop()
		verify_pose(f,stopped,authored_world,label+": stop returns original-ID pose")
		actor.apply(0,false,true);simulation.start()
		verify_pose(f,simulation.capture_pose(),authored_world,label+": repeated start resets without scale-dependent pop")
		simulation.stop()
		fixed_tick_cases+=1
	else:
		simulation.dispose()
		check(source_snapshot(f)==before,label+": formula checks preserve all source data")
		check(not f.sk.has_meta(PoseBounds.FINAL_META) and actor.live_pose==null and actor.live_world_transform==null,label+": disposal clears only its live state and final-pose ownership")
		f.parent.free();return signature
	actor.apply(0,false,true);simulation.dispose()
	check(source_snapshot(f)==before,label+": lifecycle preserves data/source/rest/root/artist scale")
	check(not f.sk.has_meta(PoseBounds.FINAL_META) and actor.live_pose==null and actor.live_world_transform==null and f.sk.get_child_count()==0,label+": teardown leaves original skeleton without solver nodes or owned live state")
	f.parent.free();return signature

func equivalent(a: Array,b: Array,label: String) -> void:
	check(a.size()==NAMES.size() and b.size()==a.size(),label+": complete shape signatures")
	if a.size()!=NAMES.size() or b.size()!=a.size():return
	for i in range(a.size()):
		check(a[i].kind==b[i].kind,label+": same proxy choice: "+str(i))
		frame_close(a[i].frame,b[i].frame,label+": same physical world frame: "+str(i))
		if a[i].kind=="box":check(a[i].size.distance_to(b[i].size)<EPS and absf(a[i].margin-b[i].margin)<EPS,label+": same box/margin")
		elif a[i].kind=="capsule":check(absf(a[i].radius-b[i].radius)<EPS and absf(a[i].height-b[i].height)<EPS,label+": same capsule")
		else:check(absf(a[i].radius-b[i].radius)<EPS,label+": same sphere")

func legacy_case(artist_scale: float) -> void:
	var f:=fixture(1,artist_scale,1,1,1,false);var before:=source_snapshot(f);var result: Dictionary=Rig.create(f.actor)
	check(result.has("physics") and not result.has("error"),"legacy nonunit actor retains admission: "+str(artist_scale))
	if result.has("physics"):
		verify_shapes(f,result.physics,true);result.physics.dispose()
	check(source_snapshot(f)==before,"legacy allocation/disposal preserves original source data")
	f.parent.free()

func invalid_case(kind: String) -> void:
	var f:=fixture(.5);var actor: RefCounted=f.actor;var sk: Skeleton3D=f.sk
	actor.live_pose=actor.data.pose.duplicate(true);actor.live_world_transform=actor.root.global_transform
	actor.root.set_meta("has_secondary_rig",{"format":"studio_secondary_rig_1","chains":[],"colliders":[],"error":""})
	if kind=="nonuniform":sk.scale=Vector3(1,2,1)
	elif kind=="reflected":sk.scale=Vector3(-1,1,1)
	elif kind=="bone nonuniform":sk.set_bone_pose_scale(1,Vector3(1,2,1));sk.force_update_all_bone_transforms()
	else:
		# Collapse BOTH segments to the semantic elbow; the helper remains an
		# inventoried source joint rather than being removed for this refusal.
		sk.set_bone_pose_position(1,Vector3.ZERO);sk.set_bone_pose_position(2,Vector3.ZERO);sk.force_update_all_bone_transforms()
	var before:=atomic_snapshot(f);var result: Dictionary=Rig.create(actor)
	check(result.has("error") and not String(result.error).is_empty() and not result.has("physics"),"unsupported "+kind+" refuses clearly")
	check(atomic_snapshot(f)==before,"unsupported "+kind+" refusal is atomic across source/live pose/topology/metadata")
	f.parent.free()

func run() -> void:
	for factor in [.5,1.0,2.0]:await exercise(fixture(factor),"reference C="+str(factor))
	var canonical: Array=await exercise(fixture(1),"equivalent ordinary source",false)
	var small_raw: Array=await exercise(fixture(1000,1,1,.001),"equivalent .001 source units")
	var large_raw: Array=await exercise(fixture(.001,1,1,1000),"equivalent 1000 source units")
	equivalent(canonical,small_raw,"small raw source across old span/child thresholds")
	equivalent(canonical,large_raw,"large raw source uses physical metre margin cap")
	var artist_compensated: Array=await exercise(fixture(.5,2),"C .5 / artist 2 compensation")
	var parent_compensated: Array=await exercise(fixture(2,1,.5),"C 2 / parent .5 compensation")
	equivalent(canonical,artist_compensated,"artist compensation preserves geometry")
	equivalent(canonical,parent_compensated,"static-parent compensation preserves geometry")
	var root_compensated_fixture:=fixture(2,1,1,1,1,true,.5)
	check(absf(root_compensated_fixture.sk.global_basis.x.length()-2)<EPS,"source root compensation keeps the original skeleton at world scale2")
	var unit_world_bones:=true
	for bone in root_compensated_fixture.actor.order:unit_world_bones=unit_world_bones and root_compensated_fixture.actor.bone_transform(bone).basis.get_scale().is_equal_approx(Vector3.ONE)
	check(unit_world_bones,"source root .5 compensates C2 into genuinely unit world bones")
	var root_compensated: Array=await exercise(root_compensated_fixture,"C2 / source root bone .5 compensation")
	equivalent(canonical,root_compensated,"source root compensation preserves metric proxies and world geometry")
	await exercise(fixture(.5,1,1,1,1.25),"source-local helper scale 1.25")
	legacy_case(.5);legacy_case(2)
	for kind in ["nonuniform","reflected","bone nonuniform","zero length"]:invalid_case(kind)
	print("REFERENCE_BODY_PHYSICS_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"fixed_tick_cases":fixed_tick_cases,"max_position_error":max_position_error,"max_basis_error":max_basis_error,"max_relative_basis_error":max_relative_basis_error,"max_pose_world_error":max_pose_world_error,"max_pose_angle_error":max_pose_angle_error,"max_collision_error":max_collision_error}))
	quit(0 if failures==0 else 1)
