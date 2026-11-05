extends RefCounted
# Model7 contact integration WIP. No source-family-specific pose representation.
const FORMAT:="studio_model_7"
const Contacts=preload("res://src/foot_contacts.gd")
const Body=preload("res://src/body_animation.gd")
const T=preload("res://src/timeline.gd")

static func validate(data: Dictionary) -> String:
	var count:=0
	for piece in data.get("animation_clips",[]):
		if not piece.has("foot_contacts"):continue
		if not Body.Model.is_contact(data):return "Foot contacts require model version7."
		var error:=Contacts.validate(piece.foot_contacts)
		if not error.is_empty():return error
		count+=piece.foot_contacts.segments.size()
	return "Too many stored foot contact ranges." if count>32*Contacts.MAX_SEGMENTS else ""

static func promote(data: Dictionary,duration: int) -> Dictionary:
	var result:=Body.promote(data,duration)
	if result.has("error"):return result
	if result.get("format")=="studio_model_9":
		if result.component_base_format!=Body.Model.MOTION_FORMAT:result.component_base_format=FORMAT
	elif result.get("format")!=Body.Model.MOTION_FORMAT:result.format=FORMAT
	return result

static func check_bindings(rig: RefCounted) -> String:
	for piece in rig.data.animation_clips:
		if not piece.has("foot_contacts"):continue
		var error:=Contacts.check_bindings(rig,piece.foot_contacts)
		if not error.is_empty():return error
	return ""

static func sample(rig: RefCounted,frame: float,editing: bool,pose: Dictionary,editing_ancestor: String="") -> Dictionary:
	var segment:=Contacts.active(rig.data.animation_clips,frame)
	if segment.is_empty():return {"pose":pose}
	if not is_instance_valid(rig.root) or not rig.root.is_inside_tree():return {"error":"Foot contacts need the model's evaluated world."}
	# Temporary pose evaluation must not change the displayed frame, skeleton or root.
	var original: Transform3D=rig.root.transform;var bones:=[];var updated:=[]
	for id in rig.order:
		var info: Dictionary=rig.bones[id]
		bones.append({"position":info.skeleton.get_bone_pose_position(info.index),"rotation":info.skeleton.get_bone_pose_rotation(info.index),"scale":info.skeleton.get_bone_pose_scale(info.index)})
		if not info.skeleton in updated:updated.append(info.skeleton)
	var runtime: RefCounted=rig.world_context.get_ref() if rig.world_context else null
	var parents:=[];var parent: String=rig.data.get("parent_id","")
	while runtime and not parent.is_empty():
		var actor: RefCounted=runtime.instance(parent)
		parents.push_front({"actor":actor,"transform":actor.root.transform});parent=actor.data.parent_id
	# Set exact authored LOCAL transforms, rather than divide by a differently
	# displayed parent and introduce seek-order-dependent inverse/recompose rounding.
	for entry in parents:
		var actor: RefCounted=entry.actor;var transform: Dictionary=actor.sample_transform(frame,actor.data.id==editing_ancestor)
		actor.root.transform=Transform3D(Basis(T.quaternion(transform.rotation_xyzw)).scaled(Vector3.ONE*transform.scale),T.vector(transform.position))*actor.base_root
	var value: Dictionary=rig.sample_transform(frame,editing)
	var local: Transform3D=Transform3D(Basis(T.quaternion(value.rotation_xyzw)).scaled(Vector3.ONE*value.scale),T.vector(value.position))*rig.base_root
	rig.root.transform=local
	var result:=Contacts.resolve(rig,pose,segment)
	rig.root.transform=original
	for entry in parents:entry.actor.root.transform=entry.transform
	for i in range(rig.order.size()):
		var info: Dictionary=rig.bones[rig.order[i]];var prior: Dictionary=bones[i]
		info.skeleton.set_bone_pose_position(info.index,prior.position)
		info.skeleton.set_bone_pose_rotation(info.index,prior.rotation)
		info.skeleton.set_bone_pose_scale(info.index,prior.scale)
	for skeleton in updated:skeleton.force_update_all_bone_transforms()
	return result
