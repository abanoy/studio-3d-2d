extends RefCounted
const Body=preload("res://src/body_animation.gd")
const Model=Body.Model
const T=Model.Timeline
const MAX_POINTS:=256
const Components=preload("res://src/root_component_document.gd")

static func component_duration(data: Dictionary) -> int:
	var duration:=maxi(int(data.get("draft_frame",0)),int(data.get("start_frame",0)))
	for piece in data.animation_clips:duration=maxi(duration,int(piece.start)+int(piece.length)-1)
	return duration

static func controls(data: Dictionary) -> Array:
	if data.get("format")==Components.FORMAT:
		var prepared:=Components.compile(data,component_duration(data));var points:=[]
		if prepared.has("error"):return []
		for key in Components.controls(data):
			if key.components.has("position"):points.append({"frame":int(key.frame),"position":T.vector(Components.Adapter.compiled_sample(prepared,key.frame).position),"mode":str(key.components.position)})
		return points
	var probe:=Model.new();probe.data=data;var result:=[]
	for key in probe.authored_keys():
		if not "@root" in key.get("authored_channels",["@root"]):continue
		result.append({"frame":int(key.frame),"position":T.vector(key.transform.position),"mode":str(key.get("body_modes",{}).get("@root",key.interpolation))})
	return result

static func refresh_draft(edited: Dictionary,frame: int,duration: int) -> Dictionary:
	if edited.has("error"):return edited
	var data: Dictionary=edited.data
	var prepared:=Components.compile(data,duration)
	if prepared.has("error"):return prepared
	var value:=Components.Adapter.compiled_sample(prepared,frame)
	data.pose=Body.compile(Components.legacy_view(data)).sample(frame).pose
	for field in Components.Adapter.Components.FIELDS:data[field]=value[field]
	data.draft_frame=frame
	var error:=Components.validate(data,duration)
	return edited if error.is_empty() else {"error":error}

static func change(data: Dictionary,frame: int,position: Vector3,duration: int) -> Dictionary:
	if not position.is_finite() or not Model.integer(frame,0,duration):return {"error":"Invalid path point."}
	var prior:=Components.promote(data,duration)
	if prior.has("error"):return prior
	var mode:="ease"
	for point in controls(prior.data):
		if point.frame==frame:mode=point.mode
	var edited:=Components.put_component(prior.data,frame,"position",[position.x,position.y,position.z],mode,duration)
	if not edited.has("error") and controls(edited.data).size()>MAX_POINTS:return {"error":"Movement path supports up to256 model keys in this increment."}
	return refresh_draft(edited,frame,duration)

static func remove(data: Dictionary,frame: int,duration: int) -> Dictionary:
	return refresh_draft(Components.remove_component(data,frame,"position",duration),frame,duration)

static func projected(value: Vector3,view: int) -> Vector2:
	return Vector2(value.x,-value.z) if view==0 else Vector2(value.x,value.y) if view==1 else Vector2(value.z,value.y)

static func unprojected(point: Vector2,prior: Vector3,view: int) -> Vector3:
	return Vector3(point.x,prior.y,-point.y) if view==0 else Vector3(point.x,point.y,prior.z) if view==1 else Vector3(prior.x,point.y,point.x)

static func preview(data: Dictionary,video: Dictionary) -> Array:
	var probe:=Model.new();probe.data=data;probe.motion_video=video.duplicate(true)
	var prepared:={};var assistance: RefCounted
	if data.get("format")==Components.FORMAT:
		prepared=Components.compile(data,int(video.duration_frames))
		if prepared.has("error"):return []
		if data.get("motion_assist",{}).get("enabled",false):
			assistance=preload("res://src/root_component_motion.gd").new()
			if not assistance.build(data,video,{"strength":data.motion_assist.strength}).is_empty():return []
	var keys:=controls(data);var frames:={0:true,int(video.duration_frames):true}
	var stride:=maxi(1,ceili(float(video.duration_frames)/256.))
	for frame in range(0,int(video.duration_frames)+1,stride):frames[frame]=true
	for key in keys:
		frames[key.frame]=true
		if key.frame>0:frames[key.frame-1]=true
	var times: Array=frames.keys();times.sort();var result:=[];var previous:=-1
	for frame in times:
		if frame<int(data.get("start_frame",0)):continue
		var join:=previous>=0
		for n in range(1,keys.size()):
			if keys[n-1].mode=="hold" and previous<keys[n].frame and frame>=keys[n].frame:join=false
		var value: Dictionary=probe.sample_transform(frame) if prepared.is_empty() else Components.Adapter.compiled_sample(prepared,frame)
		if assistance:value=assistance.apply(value,frame)
		if not probe.evaluation_error.is_empty():return []
		result.append({"frame":frame,"position":T.vector(value.position),"join":join});previous=frame
	return result
