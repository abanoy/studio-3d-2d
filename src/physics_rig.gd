extends RefCounted
# Live, unrecorded simulation. This adapter never writes model data or animation keys.
const IK=preload("res://src/limb_ik.gd")
const Model=preload("res://src/model.gd")
const SelfCollision=preload("res://src/physics_self_collision.gd")
const PoseBounds=preload("res://src/pose_bounds.gd")
const EXTRA={"head":["頭","head","biphead","valvebipedbip01head1"],"hips":["下半身","hips","bippelvis","valvebipedbip01pelvis"],"spine":["上半身","spine","bipspine0","valvebipedbip01spine"]}
var rig: RefCounted
var simulator: PhysicalBoneSimulator3D
var skeleton: Skeleton3D
var bodies:={}
var latest:={}
var running:=false
var initial_pose: Dictionary={}
var joint_profiles: Dictionary={}
var rest_exclusions: Array=[]

static func body_weight_helper(name: String) -> bool:
	var normalized:=IK.normalized(name)
	for word in ["hair","skirt","hood","ribbon","cloth","sleeve","髪","ｽｶｰﾄ","スカート","リボン","袖"]:
		if word in normalized:return false
	for word in ["twist","hlp","捩","捻","finger","thumb","index","middle","pinky","toe","指","つま先"]:
		if word in normalized:return true
	# Match ring fingers without accidentally treating "spring"/"string" as fingers.
	var ring:=normalized.trim_prefix("valvebipedbip01").trim_prefix("bip")
	if not ring.begins_with("ring"):return false
	var suffix:=ring.trim_prefix("ring").trim_suffix("l").trim_suffix("r")
	return suffix.is_empty() or suffix.is_valid_int()

static func profiles(actor: RefCounted, chosen: Array[String], sk: Skeleton3D) -> Dictionary:
	var result:={};var limbs: Array=[];var landmarks:={}
	for tip in actor.order:
		var limb:=IK.chain(actor,tip)
		if limb.is_empty():continue
		limbs.append(limb)
		landmarks[limb.role]=sk.get_bone_global_pose(actor.bones[limb.ids[0]].index).origin
	var forward: Vector3=sk.global_basis.inverse()*actor.root.global_basis.z
	if landmarks.has_all(["leftHand","rightHand","leftFoot","rightFoot"]):
		var left: Vector3=landmarks.leftHand-landmarks.rightHand
		var up: Vector3=(landmarks.leftHand+landmarks.rightHand-landmarks.leftFoot-landmarks.rightFoot)*0.5
		if left.cross(up).length()>0.00001:forward=left.cross(up).normalized()
	for limb in limbs:
		var ids: Array=limb.ids
		var arm: bool=limb.role.ends_with("Hand")
		var a: Vector3=sk.get_bone_global_pose(actor.bones[ids[0]].index).origin
		var b: Vector3=sk.get_bone_global_pose(actor.bones[ids[1]].index).origin
		var c: Vector3=sk.get_bone_global_pose(actor.bones[ids[2]].index).origin
		var upper: Vector3=(b-a).normalized();var lower: Vector3=(c-b).normalized()
		# X is cone twist; Z is hinge rotation. Imported bone bases need not
		# point down the limb (VRM and Source commonly differ).
		result[ids[0]]={"part":"shoulder" if arm else "hip","axis":upper,"swing":110.0 if arm else 100.0,"twist":70.0 if arm else 45.0}
		var normal:=upper.cross(lower)
		var angle:=rad_to_deg(upper.angle_to(lower))
		if normal.length()<0.05:
			# Prefer the body's left/right + torso directions. Source up-axis
			# correction and VRM0 facing wrappers need not share the root's axes.
			normal=upper.cross(forward if arm else -forward)
			if normal.length()<0.05:normal=upper.cross(Vector3.UP)
			if normal.length()<0.05:normal=upper.cross(Vector3.RIGHT)
		normal=(normal-lower*normal.dot(lower)).normalized()
		# Hinge limit sign is opposite the positive child rotation around Z.
		result[ids[1]]={"part":"elbow" if arm else "knee","axis":normal,"tangent":lower,"lower":minf(angle-150.0,0.0),"upper":angle+5.0}
		result[ids[2]]={"part":"wrist" if arm else "ankle","axis":lower,"swing":45.0 if arm else 35.0,"twist":35.0 if arm else 20.0}
	for id in chosen:
		if not result.has(id):result[id]={"part":"connector","axis":sk.get_bone_global_pose(actor.bones[id].index).basis.x.normalized(),"swing":40.0,"twist":30.0}
	return result

static func configure_joint(body: PhysicalBone3D, pose: Transform3D, profile: Dictionary) -> void:
	var axis: Vector3=profile.axis
	var hinge: bool=profile.has("lower")
	var basis: Basis
	if hinge:
		var x: Vector3=profile.tangent.normalized()
		basis=Basis(x,axis.cross(x).normalized(),axis)
	else:
		var y:=axis.cross(Vector3.FORWARD)
		if y.length()<0.05:y=axis.cross(Vector3.UP)
		y=y.normalized();basis=Basis(axis,y,axis.cross(y).normalized())
	var offset:=body.joint_offset
	offset.basis=body.body_offset.basis.inverse()*pose.basis.orthonormalized().inverse()*basis
	body.joint_offset=offset
	body.joint_type=PhysicalBone3D.JOINT_TYPE_HINGE if hinge else PhysicalBone3D.JOINT_TYPE_CONE
	# PhysicalBone properties use degrees; PhysicsServer properties use radians.
	if hinge:
		body.set("joint_constraints/angular_limit_enabled",true)
		body.set("joint_constraints/angular_limit_lower",profile.lower)
		body.set("joint_constraints/angular_limit_upper",profile.upper)
	else:
		body.set("joint_constraints/swing_span",profile.swing)
		body.set("joint_constraints/twist_span",profile.twist)

static func weighted_bounds(actor: RefCounted, sk: Skeleton3D, chosen: Array[String], include_all_descendants:=false) -> Dictionary:
	var result:={};var used:=0;var mapped:={}
	for id in chosen:mapped[actor.bones[id].index]=id
	var meshes: Array=[]
	if actor.opacity_materials:meshes=actor.opacity_materials.meshes
	else:
		var queue: Array=[actor.root]
		while not queue.is_empty():
			var node: Node=queue.pop_back()
			if node is MeshInstance3D and node.mesh:meshes.append(node)
			queue.append_array(node.get_children())
	for mesh in meshes:
		if not mesh.skin or mesh.get_node_or_null(mesh.skeleton)!=sk:continue
		var binds: Array=[];var owners: Array=[]
		for i in range(mesh.skin.get_bind_count()):
			var bone: int=mesh.skin.get_bind_bone(i)
			if bone<0:bone=sk.find_bone(mesh.skin.get_bind_name(i))
			binds.append(sk.get_bone_global_pose(bone)*mesh.skin.get_bind_pose(i) if bone>=0 else Transform3D.IDENTITY)
			var owner: int=bone
			while owner>=0 and not mapped.has(owner):owner=sk.get_bone_parent(owner)
			if owner>=0 and owner!=bone and not include_all_descendants:
				# Loose hair/cloth branches must not enlarge a rigid head/torso
				# collider merely because they descend from that body bone.
				if not body_weight_helper(sk.get_bone_name(bone)):owner=-1
			owners.append(mapped.get(owner,""))
		for surface in range(mesh.mesh.get_surface_count()):
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=preload("res://src/source_shape.gd").vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			if used+vertices.size()>100000:continue
			used+=vertices.size()
			var bones=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
			if not bones is PackedInt32Array or not weights is PackedFloat32Array or vertices.is_empty():continue
			var stride: int=bones.size()/vertices.size()
			if stride not in [4,8] or weights.size()!=bones.size():continue
			for i in range(vertices.size()):
				var point:=Vector3.ZERO;var influences:={}
				for j in range(stride):
					var weight: float=weights[i*stride+j];var bind: int=bones[i*stride+j]
					if weight<=0 or bind<0 or bind>=binds.size():continue
					point+=(binds[bind]*vertices[i])*weight
					if not owners[bind].is_empty():influences[owners[bind]]=influences.get(owners[bind],0.0)+weight
				var owner:="";var best:=0.0
				for id in influences:
					if influences[id]>best:best=influences[id];owner=id
				if owner.is_empty() or best<0.5:continue
				var local: Vector3=sk.get_bone_global_pose(actor.bones[owner].index).affine_inverse()*point
				result[owner]=result[owner].expand(local) if result.has(owner) else AABB(local,Vector3.ZERO)
	return result

static func create(actor: RefCounted, frame:=0) -> Dictionary:
	if not actor or actor.order.is_empty():return {"error":"This model has no skeleton for ragdoll physics."}
	var chosen: Array[String]=[]
	for id in actor.order:
		var chain:=IK.chain(actor,id)
		var ids: Array=chain.get("ids",[])
		for i in range(ids.size()-1):
			if actor.bone_transform(ids[i]).origin.distance_to(actor.bone_transform(ids[i+1]).origin)<0.00001:return {"error":"A ragdoll limb has a zero-length segment. Use direct posing for this rig."}
		for member in chain.get("ids",[]):
			if not member in chosen:chosen.append(member)
	if chosen.size()<3:return {"error":"This rig has no validated arm or leg chain for automatic ragdoll setup."}
	var sk: Skeleton3D=actor.bones[chosen[0]].skeleton
	if not IK.regular(sk.global_basis):return {"error":"Ragdoll physics needs a positive uniformly scaled skeleton."}
	var role_ids:={}
	var native=actor.data.metadata.get("native_parameters",{})
	var humanoid: Dictionary=native.humanoid if native is Dictionary and native.get("humanoid") is Dictionary else {}
	for role in EXTRA:
		var entry=humanoid.get(role,{})
		var declared: String=entry.get("node_name","") if entry is Dictionary and entry.get("node_name","") is String else ""
		var matches:=[]
		for id in actor.order:
			var name: String=actor.bones[id].name
			if actor.bones[id].skeleton==sk and (name==declared if not declared.is_empty() else IK.normalized(name) in EXTRA[role]):matches.append(id)
		if matches.size()==1:
			role_ids[role]=matches[0]
			if not matches[0] in chosen:chosen.append(matches[0])
	for id in chosen:
		if actor.bones[id].skeleton!=sk:return {"error":"Automatic ragdolls currently need one connected skeleton."}
		if not IK.regular(actor.bone_transform(id).basis):return {"error":"Ragdoll physics needs positive uniform bone scale."}
	# Include connecting ancestors only as far as the lowest common ancestor.
	var common: String=chosen[0]
	while common!="@root":
		var connects:=true
		for id in chosen:
			var at: String=id
			while at!="@root" and at!=common:at=actor.parent_id(at)
			if at!=common:connects=false;break
		if connects:break
		common=actor.parent_id(common)
	if common=="@root":return {"error":"Ragdoll limbs do not share a bone root."}
	for id in chosen.duplicate():
		var at: String=id
		while at!=common:
			at=actor.parent_id(at)
			if not at in chosen:chosen.append(at)
	if chosen.size()>48:return {"error":"Automatic ragdoll exceeds48 structural bodies; use a simpler rig."}
	for id in chosen:
		if not IK.regular(actor.bone_transform(id).basis):return {"error":"A connecting ragdoll bone has unsupported scale. Use direct posing for this rig."}
	var candidate=new();candidate.rig=actor;candidate.skeleton=sk;candidate.initial_pose=actor.sample(frame,true)
	var sim:=PhysicalBoneSimulator3D.new();candidate.simulator=sim;sk.add_child(sim)
	var minimum:=Vector3(INF,INF,INF);var maximum:=-minimum
	for id in chosen:
		var point: Vector3=sk.get_bone_global_pose(actor.bones[id].index).origin
		minimum=minimum.min(point);maximum=maximum.max(point)
	var size:=maxf((maximum-minimum).length(),0.01)
	var bounds:=weighted_bounds(actor,sk,chosen)
	candidate.joint_profiles=profiles(actor,chosen,sk)
	for id in actor.order:
		if not id in chosen:continue
		var index: int=actor.bones[id].index
		var pose: Transform3D=sk.get_bone_global_pose(index)
		var direction:=Vector3.ZERO;var nearest:=INF
		for child in chosen:
			if actor.parent_id(child)!=id:continue
			var offset: Vector3=pose.affine_inverse()*sk.get_bone_global_pose(actor.bones[child].index).origin
			if offset.length()>0.0001 and offset.length()<nearest:direction=offset;nearest=offset.length()
		var length:=direction.length()
		var radius:=clampf(length*0.16,size*0.012,size*0.045)
		var physical:=PhysicalBone3D.new();physical.name="Body_%d" % index;physical.set("bone_name",actor.bones[id].name)
		physical.mass=3.0 if id in [role_ids.get("hips",""),role_ids.get("spine","")] else 1.0
		physical.friction=0.8;physical.bounce=0
		physical.linear_damp=0.15;physical.angular_damp=0.6
		physical.collision_layer=2;physical.collision_mask=3
		sim.add_child(physical)
		var shape:=CollisionShape3D.new()
		if bounds.has(id) and bounds[id].size.length()>size*0.005 and bounds[id].size.length()<size*0.75:
			# Include skin corners: a narrow capsule can let a bent rectangular limb
			# visibly enter the floor even when its center is above the surface.
			var box:=BoxShape3D.new();box.size=bounds[id].size+Vector3.ONE*size*0.003;shape.shape=box
			# Jolt rounds convex edges using this upper bound. Keep visible skin
			# corners close to the contact surface, with a nonzero relative margin.
			box.margin=minf(0.005,minf(box.size.x,minf(box.size.y,box.size.z))*0.025)
			physical.body_offset=Transform3D(Basis.IDENTITY,bounds[id].get_center())
		elif length>size*0.025:
			var capsule:=CapsuleShape3D.new();capsule.radius=radius;capsule.height=maxf(radius*2,length*0.9);shape.shape=capsule
			physical.body_offset=Transform3D(Basis(Quaternion(Vector3.UP,direction.normalized())),direction*0.45)
		else:
			var sphere:=SphereShape3D.new();sphere.radius=size*(0.045 if id==role_ids.get("head","") else 0.035);shape.shape=sphere
		physical.add_child(shape)
		configure_joint(physical,pose,candidate.joint_profiles[id])
		PhysicsServer3D.body_set_enable_continuous_collision_detection(physical.get_rid(),true)
		candidate.bodies[id]=physical
	# Linked capsules overlap at their shared joint; exclude only direct neighbors.
	for id in chosen:
		var parent: String=actor.parent_id(id)
		if candidate.bodies.has(parent):candidate.bodies[id].add_collision_exception_with(candidate.bodies[parent])
	candidate.rest_exclusions=SelfCollision.apply(actor,candidate.bodies)
	sim.modification_processed.connect(candidate.capture)
	candidate.running=true;candidate.capture();candidate.running=false
	return {"physics":candidate}

func capture() -> void:
	if not running:return
	latest={}
	var globals: Array[Transform3D]=[];globals.resize(skeleton.get_bone_count())
	for id in rig.order:
		if rig.bones[id].skeleton==skeleton:
			var index: int=rig.bones[id].index;var transform:=skeleton.get_bone_global_pose(index)
			latest[id]=transform;globals[index]=transform
	skeleton.set_meta(PoseBounds.FINAL_META,{"owner":weakref(simulator),"poses":globals})

func start() -> void:
	rig.live_world_transform=rig.root.global_transform;rig.live_pose=initial_pose
	running=true;simulator.physical_bones_start_simulation()

func root_transform(frame: int, editing: bool) -> Dictionary:
	var local: Transform3D=rig.root.get_parent().global_transform.affine_inverse()*rig.root.global_transform*rig.base_root.affine_inverse()
	var q:=local.basis.orthonormalized().get_rotation_quaternion().normalized()
	return {"position":[local.origin.x,local.origin.y,local.origin.z],"rotation_xyzw":[q.x,q.y,q.z,q.w],"scale":local.basis.get_scale().x}

func capture_pose() -> Dictionary:
	# Read physics body transforms at the fixed tick, rather than a render-time modifier.
	var globals: Dictionary=latest.duplicate()
	var inverse:=skeleton.global_transform.affine_inverse()
	for id in bodies:globals[id]=inverse*bodies[id].global_transform*bodies[id].body_offset.affine_inverse()
	var result: Dictionary=initial_pose.duplicate(true)
	for id in bodies:
		var parent: String=rig.parent_id(id)
		var local: Transform3D=globals[parent].affine_inverse()*globals[id] if globals.has(parent) else globals[id]
		var base: Transform3D=rig.bones[id].base
		var rotation: Quaternion=(base.basis.get_rotation_quaternion().inverse()*local.basis.get_rotation_quaternion()).normalized()
		var offset:=local.origin-base.origin
		result[id]={"position":[offset.x,offset.y,offset.z],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
	return result

func pose() -> Dictionary:
	var result: Dictionary=initial_pose.duplicate(true)
	for id in latest:
		var parent: String=rig.parent_id(id)
		var local: Transform3D=latest[parent].affine_inverse()*latest[id] if latest.has(parent) else latest[id]
		var base: Transform3D=rig.bones[id].base
		var rotation: Quaternion=(base.basis.get_rotation_quaternion().inverse()*local.basis.get_rotation_quaternion()).normalized()
		var offset:=local.origin-base.origin
		result[id]={"position":[offset.x,offset.y,offset.z],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
	return result

func stop() -> Dictionary:
	var result:=pose();running=false
	PoseBounds.clear_final(skeleton,simulator)
	rig.live_world_transform=null;rig.live_pose=null
	if is_instance_valid(simulator):simulator.physical_bones_stop_simulation()
	return result

func dispose() -> void:
	running=false
	PoseBounds.clear_final(skeleton,simulator)
	rig.live_world_transform=null;rig.live_pose=null
	if is_instance_valid(simulator):
		simulator.physical_bones_stop_simulation();simulator.free()
	bodies.clear();latest.clear();simulator=null
