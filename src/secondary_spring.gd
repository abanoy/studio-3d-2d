extends RefCounted
# Explicit fixed-step experimental runner. Unit-world scratch skeletons avoid the
# engine spring modifier's scaled-skeleton limitation. No auto-processing, keys,
# data mutation or user-facing activation until lifecycle/recording is integrated.
const Definition=preload("res://src/secondary_rig.gd")
const IK=preload("res://src/limb_ik.gd")
var actor: RefCounted
var host: Node3D
var chains: Array=[]
var colliders: Array=[]
var error:=""

static func create(rig: RefCounted) -> Dictionary:
	var definition: Dictionary=rig.root.get_meta("has_secondary_rig",{})
	if not definition.get("error","").is_empty():return {"error":definition.error}
	if definition.get("chains",[]).is_empty():return {"error":"This model has no declared secondary chains."}
	var runner=new();runner.actor=rig;runner.host=Node3D.new();runner.host.name="SecondaryMotionScratch"
	rig.root.get_tree().root.add_child(runner.host)
	for c in definition.colliders:
		if not IK.regular(Definition.binding_transform(rig,c.binding).basis):runner.dispose();return {"error":"Secondary colliders need positive uniform scale."}
		var node: SpringBoneCollision3D
		if c.shape=="sphere":node=SpringBoneCollisionSphere3D.new()
		else:node=SpringBoneCollisionCapsule3D.new()
		runner.colliders.append({"definition":c,"node":node})
	for source in definition.chains:
		var scratch:=Skeleton3D.new();runner.host.add_child(scratch);scratch.modifier_callback_mode_process=Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_MANUAL
		scratch.add_bone("Anchor")
		var ids: Array=[];var poses: Array[Transform3D]=[]
		for i in range(source.joints.size()):
			var binding: Dictionary=source.joints[i].binding
			if i<source.joints.size()-1 or source.end_extension>0:
				if binding.kind!="bone" or not rig.bones.has(binding.id):runner.error="Secondary rotating joint is not a poseable skin bone.";break
				ids.append(binding.id)
			poses.append(Definition.binding_transform(rig,binding))
		if not runner.error.is_empty():break
		var parent: String=rig.parent_id(ids[0]);var anchor: Transform3D=rig.bone_transform(parent)
		if not IK.regular(anchor.basis):runner.error="Secondary motion needs positive uniform scale.";break
		scratch.set_bone_rest(0,Transform3D(anchor.basis.orthonormalized(),anchor.origin))
		if source.end_extension>0:
			var last: Transform3D=poses[-1];var axis: Vector3=poses[-1].origin-poses[-2].origin if poses.size()>1 else last.basis.y
			last.origin+=axis.normalized()*source.end_extension*last.basis.get_scale().x;poses.append(last)
		var previous: Transform3D=scratch.get_bone_rest(0)
		for i in range(poses.size()):
			if not IK.regular(poses[i].basis):runner.error="Secondary motion needs positive uniform bone scale.";break
			var global:=Transform3D(poses[i].basis.orthonormalized(),poses[i].origin)
			if previous.origin.distance_to(global.origin)<0.000001 and i>0:runner.error="Secondary chain contains a zero-length segment.";break
			scratch.add_bone("Joint"+str(i));scratch.set_bone_parent(i+1,i);scratch.set_bone_rest(i+1,previous.affine_inverse()*global);previous=global
		if not runner.error.is_empty():break
		scratch.reset_bone_poses()
		var spring:=SpringBoneSimulator3D.new();scratch.add_child(spring);spring.setting_count=1;spring.set_root_bone(0,1);spring.set_end_bone(0,poses.size());spring.set_extend_end_bone(0,false);spring.set_individual_config(0,true)
		spring.set_center_from(0,SpringBoneSimulator3D.CENTER_FROM_WORLD_ORIGIN)
		var center: Node3D
		if not source.center.is_empty():
			center=Node3D.new();runner.host.add_child(center);center.global_transform=Definition.binding_transform(rig,source.center)
			spring.set_center_from(0,SpringBoneSimulator3D.CENTER_FROM_NODE);spring.set_center_node(0,spring.get_path_to(center))
		var scale: float=poses[0].basis.get_scale().x
		for j in range(spring.get_joint_count(0)):
			var config: Dictionary=source.joints[mini(j,source.joints.size()-1)]
			spring.set_joint_stiffness(0,j,config.stiffness);spring.set_joint_drag(0,j,config.drag);spring.set_joint_radius(0,j,config.radius*scale)
			var gravity_direction:=Vector3(config.gravity_direction[0],config.gravity_direction[1],config.gravity_direction[2])
			spring.set_joint_gravity(0,j,config.gravity if gravity_direction.length_squared()>0 else 0)
			if gravity_direction.length_squared()>0:spring.set_joint_gravity_direction(0,j,gravity_direction)
		# Collision nodes are children of each spring, with per-chain membership.
		var collision_nodes: Array=[]
		for ci in source.colliders:
			var c: Dictionary=runner.colliders[ci];var copy: Node3D=c.node.duplicate();spring.add_child(copy);collision_nodes.append({"definition":c.definition,"node":copy})
		spring.set_enable_all_child_collisions(0,true)
		runner.chains.append({"source":source,"scratch":scratch,"spring":spring,"ids":ids,"parent":parent,"center":center,"colliders":collision_nodes})
	for c in runner.colliders:c.node.free()
	runner.colliders.clear()
	if not runner.error.is_empty():runner.dispose();return {"error":runner.error}
	runner.update_colliders()
	# Spring joint configuration commits through engine deferred calls. Complete
	# those before tick zero, otherwise the first tight loop has no initialized
	# Verlet state and behavior depends on when a render happens to run.
	await rig.root.get_tree().process_frame
	await RenderingServer.frame_post_draw
	if not is_instance_valid(rig.root) or not rig.root.is_inside_tree():runner.dispose();return {"error":"The model changed during secondary setup."}
	return {"runner":runner}

func update_colliders() -> void:
	for chain in chains:
		for c in chain.colliders:
			var def: Dictionary=c.definition;var t:=Definition.binding_transform(actor,def.binding);var scale:=t.basis.get_scale().x
			var start: Vector3=t*Vector3(def.offset[0],def.offset[1],def.offset[2]);var node: Node3D=c.node
			node.global_transform=Transform3D(Basis.IDENTITY,start);node.radius=def.radius*scale
			if def.shape=="capsule":
				var end: Vector3=t*Vector3(def.tail[0],def.tail[1],def.tail[2]);var axis:=end-start
				node.global_position=(start+end)*0.5;node.height=axis.length()+2*node.radius
				if axis.length()>0.000001:node.global_basis=Basis(Quaternion(Vector3.UP,axis.normalized()))

func step(delta: float,wind: Vector3,forces: Array=[]) -> Dictionary:
	if not is_instance_valid(host) or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return {"error":"Secondary runner is no longer attached to a model."}
	if not is_finite(delta) or delta<=0 or delta>1.0/60 or not wind.is_finite():return {"error":"Secondary runner needs bounded fixed steps and finite wind."}
	update_colliders()
	var result: Dictionary={}
	var chain_index:=0
	for chain in chains:
		var sk: Skeleton3D=chain.scratch;var anchor: Transform3D=actor.bone_transform(chain.parent)
		var previous:=Transform3D(anchor.basis.orthonormalized(),anchor.origin)
		sk.set_bone_pose(0,previous)
		# Engine modifiers restore their input pose after each notification. Feed
		# authored local rotations, never last step's simulated rotations as rest.
		for i in range(chain.ids.size()):
			var world: Transform3D=actor.bone_transform(chain.ids[i]);var current:=Transform3D(world.basis.orthonormalized(),world.origin)
			sk.set_bone_pose(i+1,previous.affine_inverse()*current);previous=current
		if chain.center:chain.center.global_transform=Definition.binding_transform(actor,chain.source.center)
		var force: Vector3=forces[chain_index] if chain_index<forces.size() else wind
		if not force.is_finite():return {"error":"Invalid local airflow."}
		chain.spring.external_force=force;chain_index+=1
		var captured: Array[Transform3D]=[]
		var callback:=func():
			for i in range(chain.ids.size()):captured.append(sk.get_bone_global_pose(i+1))
		chain.spring.modification_processed.connect(callback,CONNECT_ONE_SHOT)
		sk.advance(delta);sk.notification(Skeleton3D.NOTIFICATION_UPDATE_SKELETON)
		if captured.size()!=chain.ids.size():return {"error":"Secondary modifier produced no pose."}
		var solved:={}
		for i in range(chain.ids.size()):solved[chain.ids[i]]=captured[i]
		for i in range(chain.ids.size()):
			var id: String=chain.ids[i];var base: Transform3D=actor.bones[id].base
			var parent: String=actor.parent_id(id);var parent_world: Transform3D=actor.bone_transform(parent);var ancestor:=parent
			while ancestor!="@root":
				if solved.has(ancestor):parent_world=solved[ancestor]*actor.bone_transform(ancestor).affine_inverse()*parent_world;break
				ancestor=actor.parent_id(ancestor)
			var q: Quaternion=(base.basis.get_rotation_quaternion().inverse()*parent_world.basis.get_rotation_quaternion().inverse()*captured[i].basis.get_rotation_quaternion()).normalized()
			var local: Transform3D=actor.bones[id].skeleton.get_bone_pose(actor.bones[id].index);var p:=local.origin-base.origin
			result[id]={"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	return {"pose":result}

func dispose() -> void:
	chains.clear()
	for collider in colliders:
		if is_instance_valid(collider.node):collider.node.free()
	colliders.clear()
	if is_instance_valid(host):host.free()
	host=null
