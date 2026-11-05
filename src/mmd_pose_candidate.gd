extends RefCounted
const Model=preload("res://src/model.gd")
const T=preload("res://src/timeline.gd")
const Shapes=preload("res://src/shape_animation.gd")
const Shape=preload("res://src/source_shape.gd")
const Presets=preload("res://src/expression_presets.gd")
const PoseShapes=preload("res://src/mmd_pose_shapes.gd")

static func candidate(rig: RefCounted, converted: Dictionary, at: int, duration: int) -> Dictionary:
	if converted.get("format")!="studio_mmd_pose_conversion_1" or converted.get("model_sha256")!=rig.data.sha256:
		return {"error":"This pose conversion belongs to another model. Import again for the selected character."}
	if at<0 or at>=duration:return {"error":"Choose a frame inside the shot."}
	var interpolation: String=converted.get("sample_interpolation","ease")
	if not interpolation in ["hold","linear","ease"]:return {"error":"Invalid imported interpolation."}
	if not converted.get("bones") is Array:return {"error":"Invalid pose bones."}
	var names:={}
	for id in rig.order:
		var name: String=rig.bones[id].name
		if names.has(name):return {"error":"Duplicate native bone name: "+name}
		names[name]=id
	var pose: Dictionary=rig.sample_body(at,true).duplicate(true)
	var channels: Array=[]
	for control in converted.bones:
		if not control is Dictionary or not names.has(control.get("name")):return {"error":"Pose binding no longer matches the character."}
		var id: String=names[control.name]
		if id in channels:return {"error":"Pose refers to the same bone twice."}
		var value:={"position":control.get("translation"),"rotation_xyzw":control.get("rotation_xyzw")}
		if not Model.transform_valid(value):return {"error":"Invalid converted pose value."}
		var shift: Vector3=rig.bones[id].base.basis*T.vector(value.position)
		pose[id]={"position":[shift.x,shift.y,shift.z],"rotation_xyzw":value.rotation_xyzw}
		channels.append(id)
	var trial:=Model.new()
	trial.data=rig.data.duplicate(true)
	var key:={"frame":at,"pose":pose,"transform":rig.sample_authored_transform(at,true),"authored_channels":channels,"interpolation":interpolation}
	var error: String=trial.put_pose_key(key,duration,false,rig.data) if not channels.is_empty() else ""
	if not error.is_empty():return {"error":error}
	var descriptor: Dictionary=rig.root.get_meta(Shape.META,{"rows":[],"error":""})
	var presets: Dictionary=rig.root.get_meta(Presets.META,{"entries":[],"error":""})
	var controls=converted.get("morphs",converted.get("unapplied_morphs",[]))
	var resolved:=PoseShapes.resolve(controls,descriptor.rows if descriptor.get("error","").is_empty() else [],presets)
	if resolved.has("error"):return resolved
	if channels.is_empty() and resolved.matched.is_empty():return {"error":"No matching pose bones or supported shapes."}
	if not resolved.values.is_empty():
		var data:=Shapes.promote(trial.data)
		var values: Dictionary=rig.sample_shapes(at,true).duplicate(true)
		var known:={}
		for row in descriptor.rows:known[str(row.node)]=row
		for node in resolved.values:
			if not known.has(node):return {"error":"A pose expression refers to a missing model part."}
			var inherited:=Shape.effective(known[node],Shape.setting(rig.data))
			for index in resolved.values[node]:
				if not Shape.index_key(index,inherited.size()):return {"error":"A pose expression refers to a missing shape."}
				if not data.shape_base.has(node):data.shape_base[node]={}
				if not data.shape_base[node].has(index):data.shape_base[node][index]=inherited[int(index)]
				if not data.shape_starts.has(node):data.shape_starts[node]={}
				if not data.shape_starts[node].has(index):data.shape_starts[node][index]=int(rig.data.get("start_frame",0))
				if not data.shape_names.has(node):data.shape_names[node]={}
				data.shape_names[node][index]=str(known[node].names[int(index)]).left(200)
				if not values.has(node):values[node]={}
				values[node][index]=resolved.values[node][index]
		data.shape_pose=Shapes.fill(values,data.shape_base);data.shape_draft_frame=at
		trial.data=Shapes.put_key(data,{"frame":at,"shapes":resolved.values,"interpolation":interpolation},duration)
		error=Model.validate(trial.data,duration)
		if not error.is_empty():return {"error":error}
	return {"data":trial.data,"matched_morphs":resolved.matched,"skipped_morphs":resolved.skipped}
