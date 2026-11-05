extends RefCounted
# Direct authoring assist. Native model identity and playback remain shared FK poses.
const Timeline=preload("res://src/timeline.gd")
const ALIASES={
	"leftUpperArm":["左腕","upperarml","bipupperarml","valvebipedbip01lupperarm"],
	"leftLowerArm":["左ひじ","左肘","forearml","lowerarml","biplowerarml","valvebipedbip01lforearm"],
	"leftHand":["左手首","handl","biphandl","valvebipedbip01lhand"],
	"rightUpperArm":["右腕","upperarmr","bipupperarmr","valvebipedbip01rupperarm"],
	"rightLowerArm":["右ひじ","右肘","forearmr","lowerarmr","biplowerarmr","valvebipedbip01rforearm"],
	"rightHand":["右手首","handr","biphandr","valvebipedbip01rhand"],
	"leftUpperLeg":["左足","thighl","biphipl","valvebipedbip01lthigh"],
	"leftLowerLeg":["左ひざ","左膝","calfl","shinl","bipkneel","valvebipedbip01lcalf"],
	"leftFoot":["左足首","footl","bipfootl","valvebipedbip01lfoot"],
	"rightUpperLeg":["右足","thighr","biphipr","valvebipedbip01rthigh"],
	"rightLowerLeg":["右ひざ","右膝","calfr","shinr","bipkneer","valvebipedbip01rcalf"],
	"rightFoot":["右足首","footr","bipfootr","valvebipedbip01rfoot"]}

static func normalized(name: String) -> String:
	return name.to_lower().replace("_","").replace(".","").replace("-","").replace(" ","")

static func chain(rig: RefCounted, tip: String) -> Dictionary:
	if not rig or not rig.bones.has(tip):return {}
	var declared: Dictionary={}
	var parameters=rig.data.metadata.get("native_parameters",{})
	if parameters is Dictionary and parameters.get("humanoid") is Dictionary:declared=parameters.humanoid
	var roles:={};var explicit_roles:={}
	for role in ALIASES:
		var matches:=[]
		var entry=declared.get(role,{})
		var explicit: String=entry.get("node_name","") if entry is Dictionary and entry.get("node_name","") is String else ""
		for id in rig.order:
			var name: String=rig.bones[id].name
			if (name==explicit if not explicit.is_empty() else normalized(name) in ALIASES[role]):matches.append(id)
		if matches.size()==1:roles[role]=matches[0];explicit_roles[role]=not explicit.is_empty()
	for names in [["leftUpperArm","leftLowerArm","leftHand"],["rightUpperArm","rightLowerArm","rightHand"],["leftUpperLeg","leftLowerLeg","leftFoot"],["rightUpperLeg","rightLowerLeg","rightFoot"]]:
		if roles.get(names[2],"")!=tip or not roles.has(names[0]) or not roles.has(names[1]):continue
		var a: String=roles[names[0]];var b: String=roles[names[1]]
		if rig.parent_id(tip)!=b or rig.parent_id(b)!=a:continue
		if rig.bones[a].skeleton!=rig.bones[b].skeleton or rig.bones[b].skeleton!=rig.bones[tip].skeleton:continue
		return {"ids":[a,b,tip],"role":names[2],"declared":explicit_roles.get(names[2],false)}
	return {}

static func regular(basis: Basis) -> bool:
	var scale:=basis.get_scale()
	return basis.determinant()>0 and scale.x>0.00001 and absf(scale.x-scale.y)<scale.x*0.001 and absf(scale.x-scale.z)<scale.x*0.001 and absf(basis.x.normalized().dot(basis.y.normalized()))<0.001 and absf(basis.x.normalized().dot(basis.z.normalized()))<0.001

static func solve(rig: RefCounted, limb: Dictionary, target: Vector3, flip := false, pose_override = null,pole_override=null) -> Dictionary:
	if limb.is_empty() or not target.is_finite() or not rig.root.is_inside_tree():return {"error":"This limb has no validated IK chain."}
	var ids: Array=limb.ids;var skeleton: Skeleton3D=rig.bones[ids[0]].skeleton
	var world: Array[Transform3D]=[];var global: Array[Transform3D]=[];var local: Array[Transform3D]=[]
	for id in ids:
		var index: int=rig.bones[id].index
		global.append(skeleton.get_bone_global_pose(index));local.append(skeleton.get_bone_pose(index));world.append(skeleton.global_transform*global[-1])
		if not regular(world[-1].basis):return {"error":"Natural limb movement needs positive uniform bone scale. Use direct posing for this rig."}
	var length_a:=world[0].origin.distance_to(world[1].origin);var length_b:=world[1].origin.distance_to(world[2].origin)
	var total:=length_a+length_b
	if minf(length_a,length_b)<0.00001:return {"error":"This limb has a zero-length segment. Use direct posing."}
	var epsilon:=minf(minf(length_a,length_b)*0.001,0.0001)
	var direction:=target-world[0].origin
	if direction.length()<epsilon:direction=world[2].origin-world[0].origin
	if direction.length()<epsilon:direction=world[0].basis.x
	var reach:=clampf(target.distance_to(world[0].origin),absf(length_a-length_b)+epsilon,total-epsilon)
	var goal:=world[0].origin+direction.normalized()*reach
	var axis: Vector3=direction.normalized()
	if pole_override!=null and (not pole_override is Vector3 or not pole_override.is_finite()):return {"error":"Invalid knee direction target."}
	var bend: Vector3=(pole_override if pole_override is Vector3 else world[1].origin)-world[0].origin
	bend-=axis*bend.dot(axis)
	if pole_override is Vector3 and bend.length()<epsilon:return {"error":"Move the knee target away from the straight leg line."}
	if bend.length()<total*0.0001:
		for candidate in [world[0].basis.z,world[0].basis.y,world[0].basis.x]:
			bend=candidate-axis*candidate.dot(axis)
			if bend.length()>epsilon:break
	bend=bend.normalized()*(-1 if flip else 1)
	var pole_world:=world[0].origin+axis*reach*0.5+bend*total
	# A scratch skeleton is processed exactly once and freed. Never manually notify
	# the live rig or leave a solver overriding the saved pose after this function.
	var host:=Node3D.new();host.transform=skeleton.global_transform;skeleton.get_tree().root.add_child(host)
	var scratch:=Skeleton3D.new();host.add_child(scratch)
	for name in ["Root","Middle","End"]:scratch.add_bone(name)
	scratch.set_bone_parent(1,0);scratch.set_bone_parent(2,1)
	scratch.set_bone_rest(0,global[0]);scratch.set_bone_rest(1,global[0].affine_inverse()*global[1]);scratch.set_bone_rest(2,global[1].affine_inverse()*global[2]);scratch.reset_bone_poses()
	scratch.modifier_callback_mode_process=Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_MANUAL
	var goal_node:=Node3D.new();host.add_child(goal_node);goal_node.global_position=goal
	var pole:=Node3D.new();host.add_child(pole);pole.global_position=pole_world
	var modifier:=TwoBoneIK3D.new();scratch.add_child(modifier);modifier.setting_count=1
	modifier.set_root_bone(0,0);modifier.set_middle_bone(0,1);modifier.set_end_bone(0,2)
	modifier.set_target_node(0,modifier.get_path_to(goal_node));modifier.set_pole_node(0,modifier.get_path_to(pole))
	modifier.set_pole_direction(0,SkeletonModifier3D.SECONDARY_DIRECTION_PLUS_Z)
	var solved: Array=[]
	modifier.modification_processed.connect(func():
		for i in range(3):solved.append(scratch.get_bone_global_pose(i)))
	scratch.advance(0);scratch.notification(Skeleton3D.NOTIFICATION_UPDATE_SKELETON)
	host.free()
	if solved.size()!=3:return {"error":"The limb solver did not produce a pose."}
	var parent: int=skeleton.get_bone_parent(rig.bones[ids[0]].index)
	var parent_pose: Transform3D=skeleton.get_bone_global_pose(parent) if parent>=0 else Transform3D.IDENTITY
	var values: Array[Transform3D]=[parent_pose.affine_inverse()*solved[0],solved[0].affine_inverse()*solved[1],solved[1].affine_inverse()*solved[2]]
	# Preserve the hand/foot's original global orientation while moving its chain.
	values[2].basis=solved[1].basis.inverse()*global[2].basis
	var pose: Dictionary=(pose_override if pose_override is Dictionary else rig.data.pose).duplicate(true)
	for i in range(3):
		var base: Transform3D=rig.bones[ids[i]].base
		var rotation: Quaternion=(base.basis.get_rotation_quaternion().inverse()*values[i].basis.get_rotation_quaternion()).normalized()
		var position: Vector3=local[i].origin-base.origin
		pose[ids[i]]={"position":[position.x,position.y,position.z],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]}
	return {"pose":pose,"target":goal,"clamped":goal.distance_to(target)>epsilon,"role":limb.role}
