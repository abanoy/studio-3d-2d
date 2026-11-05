extends RefCounted
# Pasted body curves retain their existing semantics. Pins follow the actual
# destination root at piece entry, not an unrelated static receiver pose.
const Contact=preload("res://src/contact_animation.gd")
const Model=Contact.Body.Model
const Airflow=preload("res://src/airflow.gd")
const IK=preload("res://src/limb_ik.gd")
const T=Model.Timeline

static func has_contacts(piece: Dictionary) -> bool:
	return not piece.get("foot_contacts",{}).get("segments",[]).is_empty()

static func anchor(rig: RefCounted,data: Dictionary,frame: float) -> Transform3D:
	var probe:=Model.new();probe.data=data;probe.root=rig.root;probe.base_root=rig.base_root
	var runtime: RefCounted=rig.world_context.get_ref() if rig.world_context else null
	return Airflow.world_transform(probe,runtime,frame)

static func regular(value: Transform3D) -> bool:return value.origin.is_finite() and IK.regular(value.basis)

static func reanchor(piece: Dictionary,source: Transform3D,destination: Transform3D,preserve_identity:=false) -> Dictionary:
	if not regular(source) or not regular(destination):return {"error":"Pasting planted motion needs positive uniform instance transforms. Release its feet before using an unsupported transform."}
	var result:=piece.duplicate(true);var same: bool=source==destination
	var delta:=Transform3D.IDENTITY if same else destination*source.affine_inverse()
	var rotation:=delta.basis.orthonormalized().get_rotation_quaternion()
	for segment in result.foot_contacts.segments:
		if not preserve_identity or not same:segment.id=str(ResourceUID.create_id())
		if same:continue
		for foot in segment.feet:
			var p: Vector3=delta*T.vector(foot.position);var q: Quaternion=(rotation*T.quaternion(foot.rotation_xyzw)).normalized()
			foot.position=[p.x,p.y,p.z];foot.rotation_xyzw=[q.x,q.y,q.z,q.w]
			if foot.has("pole"):
				var pole: Vector3=delta*T.vector(foot.pole);foot.pole=[pole.x,pole.y,pole.z]
	var error:=Contact.Contacts.validate(result.foot_contacts)
	return {"error":error} if not error.is_empty() else {"piece":result}

static func validate_candidate(rig: RefCounted,data: Dictionary,duration: int) -> String:
	var error:=Model.validate(data,duration)
	if not error.is_empty():return error
	var probe:=Model.new();probe.data=data;probe.root=rig.root;probe.base_root=rig.base_root;probe.order=rig.order;probe.bones=rig.bones;probe.world_context=rig.world_context
	error=probe.check_bindings()
	if not error.is_empty():return error
	var before: Dictionary=rig.data;rig.data=data
	var runtime: RefCounted=rig.world_context.get_ref() if rig.world_context else null
	var candidates: Array=runtime.instances.values() if runtime else [rig]
	var prior_errors:={}
	for actor in candidates:prior_errors[actor.data.id]=actor.evaluation_error
	for frame in range(duration+1):
		for actor in candidates:
			if not Model.is_contact(actor.data) or actor!=rig and not rig.root.is_ancestor_of(actor.root):continue
			actor.sample(frame)
			if not actor.evaluation_error.is_empty():error="Frame %d · %s: %s Move the block less, or release its feet first." % [frame,actor.data.name,actor.evaluation_error];break
		if not error.is_empty():break
	rig.data=before
	for actor in candidates:actor.evaluation_error=prior_errors[actor.data.id]
	return error
