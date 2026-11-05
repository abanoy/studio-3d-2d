extends RefCounted
# Versioned bridge over the same model/clip records. Geometry and native IDs stay shared.
const B=preload("res://src/body_curves.gd")
const Model=B.Model
const Clips=Model.Clips
const Shapes=Model.ShapeAnimation
const FORMAT:="studio_model_6"
const Runtime=preload("res://src/body_curve_runtime.gd")
static func has_data(data: Dictionary) -> bool:return Model.is_body(data)

static func compile(data: Dictionary) -> RefCounted:
	var runtime:=Runtime.new();runtime.build(view(data));return runtime

static func view(data: Dictionary) -> Dictionary:
	var pieces:=[]
	for piece in data.animation_clips:
		var shapes=piece.get("shape_keys",[])
		var external: bool=not shapes is Array or not shapes.is_empty()
		for field in piece:
			if not field in ["id","start","length","source_in","keys","base_pose","base_transform","auto_extend","base_shapes","shape_keys","shape_only","shape_origin","shape_leading_hold","body_origin","body_legacy_channels","body_controls","body_removed","body_rest_keys","body_placeholder","body_untrimmed"]:external=true
		pieces.append({"id":piece.id,"start":piece.start,"length":piece.length,"source_in":piece.source_in,"keys":piece.keys,"base_pose":piece.base_pose,"base_transform":piece.base_transform,"origin":piece.get("body_origin"),"legacy_channels":piece.get("body_legacy_channels"),"controls":piece.get("body_controls"),"removed":piece.get("body_removed"),"rest_keys":piece.get("body_rest_keys",[]),"placeholder":piece.get("body_placeholder",false),"untrimmed":piece.get("body_untrimmed",false),"external_tracks":external,"auto_extend":piece.get("auto_extend",false) and not external})
	return {"format":B.FORMAT,"start_frame":data.start_frame,"presence_offset":data.presence_offset,"base_pose":data.get("body_base_pose"),"base_transform":data.get("body_base_transform"),"starts":data.get("body_starts"),"pieces":pieces}

static func install(data: Dictionary,body: Dictionary) -> Dictionary:
	var result:=data.duplicate(true);result.format=str(data.format) if Model.is_contact(data) else FORMAT
	result["body_base_pose"]=body.base_pose.duplicate(true);result["body_base_transform"]=body.base_transform.duplicate(true);result["body_starts"]=body.starts.duplicate(true)
	var old:={}
	for piece in result.animation_clips:old[piece.id]=piece
	var pieces:=[]
	for piece in body.pieces:
		var stored: Dictionary=old.get(piece.id,Clips.clip(result,int(piece.start),int(piece.length),int(piece.source_in),piece.keys)).duplicate(true)
		for field in ["id","start","length","source_in","keys","base_pose","base_transform","auto_extend"]:stored[field]=piece[field].duplicate(true) if piece[field] is Array or piece[field] is Dictionary else piece[field]
		stored["body_origin"]=piece.origin;stored["body_legacy_channels"]=piece.legacy_channels.duplicate();stored["body_controls"]=piece.controls.duplicate(true);stored["body_removed"]=piece.removed.duplicate(true)
		stored["body_rest_keys"]=piece.get("rest_keys",[]).duplicate(true)
		stored["body_placeholder"]=piece.get("placeholder",false);stored["body_untrimmed"]=piece.get("untrimmed",false)
		if not piece.legacy_channels.is_empty() or not piece.controls.is_empty() or not stored.body_rest_keys.is_empty():stored["shape_only"]=false
		pieces.append(stored)
	result.animation_clips=pieces;result.start_frame=int(body.start_frame);result.presence_offset=int(body.presence_offset)
	return result

static func promote(data: Dictionary,duration: int) -> Dictionary:
	if has_data(data):return data.duplicate(true)
	var shaped:=Shapes.promote(data);var body:=B.extract(shaped,duration)
	if body.has("error"):return body
	for piece in body.pieces:
		piece.auto_extend=piece.get("untrimmed",false) and piece.source_in==0 and Clips.complete_range(piece)
	var no_keys: bool=body.pieces.all(func(piece):return piece.keys.is_empty())
	if no_keys:
		for piece in body.pieces:
			if piece.start==body.start_frame and piece.length==1 and not piece.legacy_channels.is_empty():piece["placeholder"]=true
	return install(shaped,body)

static func validate(data: Dictionary,duration: int) -> String:
	if not has_data(data):
		for field in ["body_base_pose","body_base_transform","body_starts"]:
			if data.has(field):return "Independent body curves require model version6."
		for piece in data.get("animation_clips",[]):
			for field in ["body_origin","body_legacy_channels","body_controls","body_removed","body_rest_keys","body_placeholder","body_untrimmed"]:
				if piece.has(field):return "Independent body curves require model version6."
		return ""
	var error:=B.validate(view(data),duration)
	if not error.is_empty():return error
	var count:=0
	for piece in data.animation_clips:
		if not piece.get("shape_keys",[]) is Array:return "Invalid expression controls."
		count+=piece.keys.size()+piece.get("shape_keys",[]).size()+piece.get("body_rest_keys",[]).size()
		for id in piece.body_controls:count+=piece.body_controls[id].size()
		for id in piece.body_removed:count+=piece.body_removed[id].size()
	return "Animation exceeds2048 combined body/expression controls." if count>Clips.MAX_TOTAL_KEYS else ""

static func put(data: Dictionary,key: Dictionary,duration: int,prior: Dictionary) -> Dictionary:
	if prior.get("format")=="studio_model_9":return load("res://src/root_component_document.gd").put(data,key,duration,prior)
	var result:=promote(prior,duration)
	if result.has("error"):return result
	# Draft changes are separate from immutable curve baselines captured before the edit.
	for field in ["pose","position","rotation_xyzw","scale","draft_frame"]:result[field]=data[field].duplicate(true) if data[field] is Dictionary or data[field] is Array else data[field]
	if Shapes.has_data(data):
		result.shape_pose=data.shape_pose.duplicate(true)
		result.shape_draft_frame=int(data.draft_frame) if data.format==Shapes.LEGACY_FORMAT else int(data.shape_draft_frame)
	var values:={}
	for id in key.get("authored_channels",["@root"]+key.pose.keys()):
		if str(id).begins_with("@shape/"):continue
		values[id]=key.transform if id=="@root" else key.pose.get(id,Model.identity())
	if values.is_empty():return {"error":"Choose a body part to key."}
	var changed:=B.put(view(result),int(key.frame),values,str(key.interpolation),duration)
	return changed if changed.has("error") else {"data":install(result,changed.data)}

static func remove_key(data: Dictionary,frame: int,id: String,duration: int) -> Dictionary:
	if data.get("format")=="studio_model_9":return load("res://src/root_component_document.gd").remove_part_key(data,frame,id,duration)
	var changed:=B.remove_key(view(data),frame,id,duration)
	if changed.has("error"):return changed
	var result:=install(data,changed.data);var state:=B.sample(changed.data,frame)
	result.pose=state.pose;result.position=state.transform.position;result.rotation_xyzw=state.transform.rotation_xyzw;result.scale=state.transform.scale;result.draft_frame=frame
	return {"data":result}

static func sample(data: Dictionary,frame: float) -> Dictionary:return B.sample(view(data),frame)

static func record_rest(data: Dictionary,frame: int,interpolation: String) -> void:
	var index:=Clips.index_at(data,frame)
	if index<0:return
	var piece: Dictionary=data.animation_clips[index]
	if not piece.has("body_rest_keys"):piece["body_rest_keys"]=[]
	Model.Timeline.put_key(piece.body_rest_keys,{"frame":int(piece.source_in)+frame-int(piece.start),"interpolation":interpolation})
	piece["shape_only"]=false

static func authored_keys(data: Dictionary) -> Array:
	var body:=view(data);var by_frame:={};var runtime:=compile(data)
	for id in B.known_channels(body):
		for piece in body.pieces:
			for key in B.points(body,piece,id,false):
				if key.frame<piece.source_in or key.frame>=piece.source_in+piece.length:continue
				var frame:=int(piece.start)+int(key.frame)-int(piece.source_in)
				if not by_frame.has(frame):by_frame[frame]={}
				by_frame[frame][id]=str(key.interpolation)
	var addresses: Array=by_frame.keys();addresses.sort();var result:=[]
	for frame in addresses:
		var state: Dictionary=runtime.sample(frame);var channels: Array=by_frame[frame].keys()
		channels.sort()
		result.append({"frame":frame,"pose":state.pose,"transform":state.transform,"interpolation":by_frame[frame][channels[0]],"authored_channels":channels,"body_modes":by_frame[frame]})
	return result

static func prepare_take(data: Dictionary,take: Dictionary) -> void:
	var ids: Array=B.known_channels(view(data))
	for key in take.keys:
		for id in key.pose:
			if not id in ids:ids.append(id)
	take["body_legacy_channels"]=ids;take["body_origin"]=int(take.source_in);take["body_controls"]={};take["body_removed"]={};take["body_rest_keys"]=[];take["body_untrimmed"]=true;take["body_placeholder"]=false
