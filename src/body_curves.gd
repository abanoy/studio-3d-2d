extends RefCounted
# Body-data view used by the versioned normal-model adapter and standalone probes.
# Legacy snapshots remain intact; explicit per-part controls override only that part.
const Model=preload("res://src/model.gd")
const Clips=Model.Clips
const Timeline=Model.Timeline
const FORMAT:="studio_body_curves_1"

static func channels(data: Dictionary) -> Array:
	var ids: Array=["@root"]
	for id in data.pose:
		if not id in ids:ids.append(id)
	for piece in data.animation_clips:
		for id in piece.base_pose:
			if not id in ids:ids.append(id)
		for key in piece.keys:
			for id in key.pose:
				if not id in ids:ids.append(id)
	return ids

static func extract(data: Dictionary,duration:=240) -> Dictionary:
	var error:=Model.validate(data,duration)
	if not error.is_empty():return {"error":error}
	if Model.is_body(data):return Model.body_animation().view(data).duplicate(true)
	var document:=Clips.promote(data);var ids:=channels(document)
	var result:={"format":FORMAT,"start_frame":int(document.start_frame),"presence_offset":int(document.presence_offset),"base_pose":document.pose.duplicate(true),"base_transform":Clips.transform(document),"starts":{},"pieces":[]}
	for source in document.animation_clips:
		var piece:={"id":source.id,"start":int(source.start),"length":int(source.length),"source_in":int(source.source_in),"origin":int(source.source_in),"keys":source.keys.duplicate(true),"base_pose":source.base_pose.duplicate(true),"base_transform":source.base_transform.duplicate(true),"legacy_channels":[] if source.get("shape_only",false) else ids.duplicate(),"controls":{},"removed":{},"auto_extend":false}
		piece["untrimmed"]=source.keys.all(func(key):return key.frame>=source.source_in and key.frame<source.source_in+source.length)
		result.pieces.append(piece)
	error=validate(result,duration)
	return result if error.is_empty() else {"error":error}

static func valid_id(id) -> bool:
	return id is String and not id.is_empty() and id.length()<=512 and not id.begins_with("@shape/")

static func valid_value(id: String,value) -> bool:
	return Model.transform_valid(value) and (id!="@root" or Model.scale_valid(value.get("scale")))

static func validate(data, duration: int) -> String:
	if not data is Dictionary or data.get("format")!=FORMAT:return "Invalid body-curve format."
	if not Model.integer(data.get("start_frame"),0,duration) or not Model.integer(data.get("presence_offset"),0,duration) or not Model.pose_valid(data.get("base_pose")) or data.base_pose.has("@root") or not valid_value("@root",data.get("base_transform")):return "Invalid body-curve base."
	if not data.get("starts") is Dictionary:return "Invalid body-curve introductions."
	for id in data.starts:
		if not valid_id(id) or not Model.integer(data.starts[id],0,duration):return "Invalid body-curve introduction."
	if not data.get("pieces") is Array or data.pieces.size()>Clips.MAX_CLIPS:return "Body curves exceed32 pieces."
	var end:=-1;var ids:={};var total:=0
	for piece in data.pieces:
		if not piece is Dictionary or not piece.get("id") is String or piece.id.is_empty() or piece.id.length()>128 or ids.has(piece.id):return "Invalid body-curve piece identity."
		ids[piece.id]=true
		if not Model.integer(piece.get("start"),0,duration) or not Model.integer(piece.get("length"),1,duration+1) or piece.start<end or piece.start+piece.length>duration+1:return "Overlapping or invalid body-curve pieces."
		end=int(piece.start+piece.length)
		if not Model.integer(piece.get("source_in"),0,Clips.MAX_SOURCE_FRAME) or piece.source_in+piece.length-1>Clips.MAX_SOURCE_FRAME or not Model.integer(piece.get("origin"),0,Clips.MAX_SOURCE_FRAME):return "Invalid body-curve source address."
		if not Model.pose_valid(piece.get("base_pose")) or piece.base_pose.has("@root") or not valid_value("@root",piece.get("base_transform")) or not piece.get("auto_extend") is bool:return "Invalid body-curve piece base."
		if piece.has("placeholder") and not piece.placeholder is bool:return "Invalid unrecorded body placeholder."
		if piece.has("untrimmed") and not piece.untrimmed is bool:return "Invalid body source-boundary ownership."
		var key_error:=Model.validate_keys(piece.get("keys"),Clips.MAX_SOURCE_FRAME)
		if not key_error.is_empty():return key_error
		for key in piece.keys:
			if key.pose.has("@root"):return "Root controls must use the root transform field."
		total+=piece.keys.size()
		var rest=piece.get("rest_keys",[])
		if not rest is Array or rest.size()>241:return "Invalid shared recorded rest controls."
		var last_rest:=-1;total+=rest.size()
		for key in rest:
			if not key is Dictionary or not Model.integer(key.get("frame"),0,Clips.MAX_SOURCE_FRAME) or key.frame<=last_rest or not key.get("interpolation") in ["hold","ease","linear"]:return "Invalid recorded rest control."
			last_rest=int(key.frame)
		var placeholder_controls=piece.get("controls",{})
		if piece.get("placeholder",false) and (piece.length!=1 or not piece.keys.is_empty() or not placeholder_controls is Dictionary or not placeholder_controls.is_empty() or not rest.is_empty()):return "An import placeholder cannot contain authored body controls."
		if not piece.get("legacy_channels") is Array or piece.legacy_channels.size()>513 or not piece.get("controls") is Dictionary or piece.controls.size()>513:return "Invalid body-curve channels."
		var parts:={}
		for id in piece.legacy_channels:
			if not valid_id(id) or parts.has(id):return "Duplicate or invalid legacy body channel."
			parts[id]=true
		for id in piece.controls:
			if not valid_id(id) or not piece.controls[id] is Array or piece.controls[id].is_empty() or piece.controls[id].size()>241:return "Invalid body-curve controls."
			total+=piece.controls[id].size();var previous:=-1
			for key in piece.controls[id]:
				if not key is Dictionary or not Model.integer(key.get("frame"),0,Clips.MAX_SOURCE_FRAME) or key.frame<=previous or not key.get("interpolation") in ["hold","ease","linear"] or not valid_value(id,key.get("value")):return "Invalid body-curve control."
				previous=int(key.frame)
		if not piece.get("removed") is Dictionary or piece.removed.size()>513:return "Invalid removed body controls."
		for id in piece.removed:
			if not valid_id(id) or not piece.removed[id] is Array or piece.removed[id].size()>Clips.MAX_TOTAL_KEYS:return "Invalid removed body controls."
			var previous:=-1;total+=piece.removed[id].size()
			var source_frames: Array=piece.keys.map(func(key):return int(key.frame)) if id in piece.legacy_channels else []
			for key in rest:source_frames.append(int(key.frame))
			for frame in piece.removed[id]:
				if not Model.integer(frame,0,Clips.MAX_SOURCE_FRAME) or frame<=previous or not frame in source_frames:return "Invalid removed body-control address."
				previous=int(frame)
	if total>Clips.MAX_TOTAL_KEYS:return "Body curves exceed2048 stored controls."
	if known_channels(data).size()>513:return "Body curves exceed512 bone channels."
	if JSON.stringify(data,"",true,true).to_utf8_buffer().size()>1024*1024:return "Body curves exceed1MiB metadata."
	return ""

static func known_channels(data: Dictionary) -> Array:
	var ids: Array=["@root"]
	for id in data.base_pose:
		if not id in ids:ids.append(id)
	for id in data.starts:
		if not id in ids:ids.append(id)
	for piece in data.pieces:
		for id in piece.legacy_channels+piece.controls.keys():
			if not id in ids:ids.append(id)
	return ids

static func check_bindings(data: Dictionary,bones: Array) -> String:
	for id in known_channels(data):
		if id!="@root" and not id in bones:return "Body curve refers to a missing bone: "+id
	return ""

static func base_value(data: Dictionary,id: String) -> Dictionary:
	return data.base_transform if id=="@root" else data.base_pose.get(id,Model.identity())

static func piece_base(data: Dictionary,piece: Dictionary,id: String) -> Dictionary:
	return piece.base_transform if id=="@root" else piece.base_pose.get(id,base_value(data,id))

static func owns(piece: Dictionary,id: String) -> bool:
	return id in piece.legacy_channels or piece.controls.has(id) or not piece.get("rest_keys",[]).is_empty()

static func points(data: Dictionary,piece: Dictionary,id: String,virtual:=true) -> Array:
	var result: Array=[]
	for key in piece.get("rest_keys",[]):result.append({"frame":int(key.frame),"value":piece_base(data,piece,id),"interpolation":key.interpolation})
	if id in piece.legacy_channels:
		for key in piece.keys:
			Timeline.put_key(result,{"frame":int(key.frame),"value":key.transform if id=="@root" else key.pose.get(id,Model.identity()),"interpolation":key.interpolation})
	for key in piece.controls.get(id,[]):Timeline.put_key(result,key)
	result=result.filter(func(key):return not key.frame in piece.removed.get(id,[]))
	if virtual and not id in piece.legacy_channels and not result.is_empty() and piece.origin<result[0].frame:
		result.push_front({"frame":int(piece.origin),"value":piece_base(data,piece,id),"interpolation":result[0].interpolation})
	return result

static func blend(a: Dictionary,b: Dictionary,t: float,id: String) -> Dictionary:
	return Model.blend_transform(a,b,t) if id=="@root" else Model.blend({id:a},{id:b},t)[id]

static func easing(t: float,mode: String) -> float:
	return 0. if mode=="hold" else t*t*(3.-2.*t) if mode=="ease" else t

static func at_piece(data: Dictionary,piece: Dictionary,frame: float,id: String) -> Dictionary:
	var controls:=points(data,piece,id);var source: float=float(piece.source_in)+frame-float(piece.start)
	if controls.is_empty():return {"value":piece_base(data,piece,id).duplicate(true),"mode":"ease"}
	var pair:=Model.curve_pair(controls,source)
	var mode:="ease"
	for key in controls:
		if key.frame<=source:mode=key.interpolation
	return {"value":blend(pair.a.value,pair.b.value,pair.t,id),"mode":mode}

static func sample_channel(data: Dictionary,frame: float,id: String) -> Dictionary:
	var pieces: Array=[]
	for piece in data.pieces:
		if owns(piece,id):pieces.append(effective_piece(data,piece,id))
	if pieces.is_empty():return base_value(data,id).duplicate(true)
	if frame<pieces[0].start:
		var first:=at_piece(data,pieces[0],float(pieces[0].start),id)
		if data.starts.has(id) and pieces[0].start>data.starts[id]:
			var t:=clampf(float(frame-data.starts[id])/float(pieces[0].start-data.starts[id]),0,1)
			return blend(base_value(data,id),first.value,easing(t,first.mode),id)
		return first.value
	var previous: Dictionary=pieces[0]
	for piece in pieces:
		if frame>=piece.start and frame<piece.start+piece.length:return at_piece(data,piece,frame,id).value
		if piece.start>frame:
			var last: int=int(previous.start)+int(previous.length)-1
			var a:=at_piece(data,previous,last,id);var b:=at_piece(data,piece,float(piece.start),id)
			return blend(a.value,b.value,easing(float(frame-last)/float(piece.start-last),a.mode),id)
		previous=piece
	return at_piece(data,previous,int(previous.start)+int(previous.length)-1,id).value

static func effective_piece(data: Dictionary,piece: Dictionary,id: String) -> Dictionary:
	if not piece.get("untrimmed",false):return piece
	var controls:=points(data,piece,id)
	if controls.is_empty():return piece
	var first:=maxi(int(piece.source_in),int(controls[0].frame));var last:=mini(int(piece.source_in)+int(piece.length)-1,int(controls[-1].frame))
	if first>last:return piece
	var result:=piece.duplicate();result.start=int(piece.start)+first-int(piece.source_in);result.source_in=first;result.length=last-first+1
	return result

static func sample(data: Dictionary,frame: float) -> Dictionary:
	var pose:={}
	for id in known_channels(data):
		if id!="@root":pose[id]=sample_channel(data,frame,id)
	return {"pose":pose,"transform":sample_channel(data,frame,"@root")}

static func index_at(data: Dictionary,frame: int) -> int:
	for i in range(data.pieces.size()):
		if frame>=data.pieces[i].start and frame<data.pieces[i].start+data.pieces[i].length:return i
	return -1

static func can_extend(piece: Dictionary,ids: Array,known: Array=[]) -> bool:
	return piece.auto_extend and piece.get("untrimmed",false)

static func put(data: Dictionary,frame: int,values: Dictionary,mode: String,duration: int) -> Dictionary:
	var error:=validate(data,duration)
	if not error.is_empty():return {"error":error}
	if not Model.integer(frame,0,duration) or values.is_empty() or values.size()>513 or not mode in ["hold","linear","ease"]:return {"error":"Invalid body-curve edit."}
	for id in values:
		if not valid_id(id) or not valid_value(id,values[id]):return {"error":"Invalid body-curve part/value."}
	var result:=data.duplicate(true);var known:=known_channels(data)
	# An unrecorded import placeholder is a base, not a later return-to-rest key.
	# Correcting introduction earlier must not resurrect that placeholder afterward.
	for placeholder in result.pieces:
		if placeholder.start<=frame or not placeholder.keys.is_empty() or not placeholder.controls.is_empty() or not placeholder.get("rest_keys",[]).is_empty():continue
		for id in values:
			if id in placeholder.legacy_channels and not result.starts.has(id):result.starts[id]=int(data.start_frame)
			placeholder.legacy_channels.erase(id)
	result.pieces=result.pieces.filter(func(piece):return piece.get("external_tracks",false) or not piece.legacy_channels.is_empty() or not piece.keys.is_empty() or not piece.controls.is_empty() or not piece.get("rest_keys",[]).is_empty())
	var index:=index_at(result,frame)
	if index>=0 and result.pieces[index].get("placeholder",false):
		var initial: Dictionary=result.pieces[index]
		for id in initial.legacy_channels:
			if not result.starts.has(id):result.starts[id]=int(data.start_frame)
		initial.legacy_channels=[];initial["placeholder"]=false;initial.auto_extend=not initial.get("external_tracks",false)
		initial["untrimmed"]=true
		if initial.auto_extend:initial.source_in=0;initial.origin=0
	for id in values:
		if not id in known:result.starts[id]=int(data.start_frame)
	if index<0:
		var previous:=-1;var following:=-1
		for i in range(result.pieces.size()):
			if result.pieces[i].start<frame:previous=i
			elif following<0:following=i
		if previous>=0 and can_extend(result.pieces[previous],values.keys(),known):
			index=previous;result.pieces[index].length=frame-int(result.pieces[index].start)+1
		elif following>=0 and can_extend(result.pieces[following],values.keys(),known):
			index=following;var next: Dictionary=result.pieces[index];var extension:=int(next.start)-frame
			next.start=frame;next.length=int(next.length)+extension;next.origin=int(next.origin)+extension
			for key in next.keys:key.frame=int(key.frame)+extension
			for key in next.get("rest_keys",[]):key.frame=int(key.frame)+extension
			for id in next.controls:
				for key in next.controls[id]:key.frame=int(key.frame)+extension
			for id in next.removed:
				for i in range(next.removed[id].size()):next.removed[id][i]=int(next.removed[id][i])+extension
		else:
			result.pieces.append({"id":str(ResourceUID.create_id()),"start":frame,"length":1,"source_in":0,"origin":0,"keys":[],"base_pose":data.base_pose.duplicate(true),"base_transform":data.base_transform.duplicate(true),"legacy_channels":[],"controls":{},"removed":{},"untrimmed":true,"auto_extend":true})
			result.pieces.sort_custom(func(a,b):return a.start<b.start);index=index_at(result,frame)
	var piece: Dictionary=result.pieces[index]
	for id in values:
		if not piece.controls.has(id):piece.controls[id]=[]
		var at:=int(piece.source_in)+frame-int(piece.start)
		Timeline.put_key(piece.controls[id],{"frame":at,"value":values[id].duplicate(true),"interpolation":mode})
		if piece.removed.has(id):piece.removed[id].erase(at)
	result.start_frame=mini(int(result.start_frame),frame)
	error=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func frames(data: Dictionary,id: String) -> Array:
	var result:=[]
	for piece in data.pieces:
		for key in points(data,piece,id,false):
			if key.frame>=piece.source_in and key.frame<piece.source_in+piece.length:
				var frame:=int(piece.start)+int(key.frame)-int(piece.source_in)
				if not frame in result:result.append(frame)
	result.sort();return result

static func remove_key(data: Dictionary,frame: int,id: String,duration: int) -> Dictionary:
	var error:=validate(data,duration)
	if not error.is_empty():return {"error":error}
	if not frame in frames(data,id):return {"data":data.duplicate(true)}
	var result:=data.duplicate(true);var piece: Dictionary=result.pieces[index_at(result,frame)]
	var at:=int(piece.source_in)+frame-int(piece.start)
	if piece.controls.has(id):
		piece.controls[id]=piece.controls[id].filter(func(key):return key.frame!=at)
		if piece.controls[id].is_empty():piece.controls.erase(id)
	if id in piece.legacy_channels and piece.keys.any(func(key):return key.frame==at) or piece.get("rest_keys",[]).any(func(key):return key.frame==at):
		if not piece.removed.has(id):piece.removed[id]=[]
		if not at in piece.removed[id]:piece.removed[id].append(at);piece.removed[id].sort()
	piece.auto_extend=false
	error=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func split(data: Dictionary,frame: int,duration: int) -> Dictionary:
	var error:=validate(data,duration)
	if not error.is_empty():return {"error":error}
	var result:=data.duplicate(true);var index:=index_at(result,frame)
	if index<0 or frame==result.pieces[index].start:return {"error":"Choose a frame inside a body block."}
	var left: Dictionary=result.pieces[index];var right:=left.duplicate(true);var length:=frame-int(left.start)
	right.id=str(ResourceUID.create_id());right.start=frame;right.source_in=int(left.source_in)+length;right.length=int(left.length)-length;right.auto_extend=false
	left.length=length;left.auto_extend=false;left["untrimmed"]=false;right["untrimmed"]=false;result.pieces.insert(index+1,right)
	error=validate(result,duration)
	return {"data":result,"right_id":right.id} if error.is_empty() else {"error":error}

static func move(data: Dictionary,id: String,start: int,duration: int) -> Dictionary:
	var error:=validate(data,duration)
	if not error.is_empty():return {"error":error}
	var result:=data.duplicate(true);var index:=-1
	for i in range(result.pieces.size()):
		if result.pieces[i].id==id:index=i;break
	if index<0:return {"error":"Missing body block."}
	result.pieces[index].start=start;result.pieces.sort_custom(func(a,b):return a.start<b.start)
	result.start_frame=clampi(int(result.pieces[0].start)+int(result.presence_offset),0,duration)
	error=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}
