extends RefCounted
# Direct pose authoring only. No persistent playback constraint or floor inference.
const IK=preload("res://src/limb_ik.gd")

static func chains(rig: RefCounted) -> Array:
	var result:=[]
	if not rig:return result
	var declared: Dictionary={}
	var parameters=rig.data.metadata.get("native_parameters",{})
	if parameters is Dictionary and parameters.get("humanoid") is Dictionary:declared=parameters.humanoid
	for role in ["leftFoot","rightFoot"]:
		var entry=declared.get(role,{})
		var explicit: String=entry.get("node_name","") if entry is Dictionary and entry.get("node_name","") is String else ""
		var matches:=[]
		for id in rig.order:
			var name: String=rig.bones[id].name
			if (name==explicit if not explicit.is_empty() else IK.normalized(name) in IK.ALIASES[role]):matches.append(id)
		if matches.size()!=1:return []
		var limb:=IK.chain(rig,matches[0])
		if limb.get("role","")!=role:return []
		result.append(limb)
	return result

static func supports(rig: RefCounted, selected: String, legs: Array) -> bool:
	if legs.size()!=2:return false
	if selected=="@root":return true
	for limb in legs:
		var id: String=rig.parent_id(limb.ids[0])
		while id!="@root" and id!=selected:id=rig.parent_id(id)
		if id!=selected:return false
	return true

static func capture(rig: RefCounted, selected: String) -> Dictionary:
	var legs:=chains(rig)
	if not supports(rig,selected,legs):return {"error":"Hold feet needs two supported legs and a body/root joint above both legs."}
	var feet:=[]
	for limb in legs:
		var transform: Transform3D=rig.bone_transform(limb.ids[2])
		feet.append({"limb":limb,"position":transform.origin,"rotation":transform.basis.orthonormalized().get_rotation_quaternion()})
	return {"feet":feet}

static func solve(rig: RefCounted, captured: Dictionary, apply_pose: Callable) -> String:
	var original: Dictionary=rig.data.pose.duplicate(true)
	for foot in captured.feet:
		var solved:=IK.solve(rig,foot.limb,foot.position)
		if solved.has("error") or solved.get("clamped",false):
			rig.data.pose=original;apply_pose.call()
			return solved.get("error","That move puts a foot out of reach. Move the body less, or turn Hold feet off.")
		rig.data.pose=solved.pose;apply_pose.call()
	# Verify both AFTER both solves: shared/incorrect chains must not silently drift.
	for foot in captured.feet:
		var transform: Transform3D=rig.bone_transform(foot.limb.ids[2])
		if transform.origin.distance_to(foot.position)>0.0002 or absf(transform.basis.orthonormalized().get_rotation_quaternion().dot(foot.rotation))<0.99999:
			rig.data.pose=original;apply_pose.call()
			return "These legs could not hold both feet. The move was kept unchanged."
	return ""
