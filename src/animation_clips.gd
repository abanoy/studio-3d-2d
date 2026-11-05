extends RefCounted
# Immutable-style document operations. Every piece owns its own original source curve.
const Timeline=preload("res://src/timeline.gd")
const FORMAT:="studio_model_2"
const MAX_CLIPS:=32
const MAX_TOTAL_KEYS:=2048
const MAX_SOURCE_FRAME:=100000

static func has_pieces(data: Dictionary) -> bool:
	return data.get("format") in [FORMAT,"studio_model_3","studio_model_4","studio_model_5","studio_model_6","studio_model_7","studio_model_8","studio_model_9"]

static func transform(data: Dictionary) -> Dictionary:
	return {"position":data.position.duplicate(),"rotation_xyzw":data.rotation_xyzw.duplicate(),"scale":data.scale}

static func clip(data: Dictionary, start: int, length: int, source_in: int, keys: Array) -> Dictionary:
	var result:={"id":str(ResourceUID.create_id()),"start":start,"length":length,"source_in":source_in,"keys":keys.duplicate(true),"base_pose":data.pose.duplicate(true),"base_transform":transform(data),"auto_extend":false}
	if data.get("format") in ["studio_model_4","studio_model_5","studio_model_6","studio_model_7","studio_model_8","studio_model_9"]:result["base_shapes"]=data.shape_pose.duplicate(true)
	if data.get("format") in ["studio_model_5","studio_model_6","studio_model_7","studio_model_8","studio_model_9"]:result["shape_keys"]=[]
	if data.get("format") in ["studio_model_6","studio_model_7","studio_model_8","studio_model_9"]:result["body_origin"]=source_in;result["body_legacy_channels"]=[];result["body_controls"]={};result["body_removed"]={}
	return result

static func promote(data: Dictionary) -> Dictionary:
	var result:=data.duplicate(true)
	if has_pieces(result):return result
	# Legacy single-slot model records predate world first-presence fields.
	if not result.has("start_frame"):result["start_frame"]=0
	var first:=int(result.start_frame);var last:=first
	for key in result.pose_keys:first=mini(first,int(key.frame));last=maxi(last,int(key.frame))
	result.format=FORMAT
	result["animation_clips"]=[clip(result,first,last-first+1,first,result.pose_keys)]
	result["presence_offset"]=int(result.start_frame)-first
	result.pose_keys=[]
	return result

static func index_at(data: Dictionary, frame: float) -> int:
	for i in range(data.animation_clips.size()):
		var piece: Dictionary=data.animation_clips[i]
		if frame>=piece.start and frame<piece.start+piece.length:return i
	return -1

static func index_id(data: Dictionary, id: String) -> int:
	for i in range(data.animation_clips.size()):
		if data.animation_clips[i].id==id:return i
	return -1

static func can_extend_track(piece: Dictionary,shape_key: bool,values: Dictionary={}) -> bool:
	if not piece.get("auto_extend",false):return false
	if not shape_key:return piece.get("shape_keys",[]).is_empty()
	if not piece.get("shape_only",false):return false
	# Growing a block for a different target would move the first/last boundary
	# used to bridge another target's gaps. Give that edit its own piece instead.
	var channels:={}
	for key in piece.get("shape_keys",[]):
		for node in key.shapes:
			if not channels.has(node):channels[node]={}
			for index in key.shapes[node]:channels[node][index]=true
	var requested:={}
	for node in values:
		requested[node]={}
		for index in values[node]:requested[node][index]=true
	return channels==requested

static func update_presence(data: Dictionary, duration: int) -> void:
	data.animation_clips.sort_custom(func(a,b):return a.start<b.start)
	if not data.animation_clips.is_empty():data.start_frame=clampi(int(data.animation_clips[0].start)+int(data.presence_offset),0,duration)

static func split(data: Dictionary, frame: int) -> Dictionary:
	var result:=promote(data)
	if result.animation_clips.size()>=MAX_CLIPS:return {"error":"This object already has32 animation pieces."}
	var index:=index_at(result,frame)
	if index<0 or frame==result.animation_clips[index].start:return {"error":"Choose a frame inside an animation block to split it."}
	var left: Dictionary=result.animation_clips[index]
	var right:=left.duplicate(true);right.id=str(ResourceUID.create_id())
	var length:=frame-int(left.start)
	right.start=frame;right.source_in=int(left.source_in)+length;right.length=int(left.length)-length
	left.length=length;left.auto_extend=false;right.auto_extend=false
	if result.get("format") in ["studio_model_6","studio_model_7","studio_model_8","studio_model_9"]:left["body_untrimmed"]=false;right["body_untrimmed"]=false
	result.animation_clips.insert(index+1,right)
	# Both slices evaluate the retained source curve, including controls outside
	# their visible range. Preserve its tuning on each independent copy.
	var edits: Dictionary=result.get("motion_assist",{}).get("track_helper_edits",{})
	var count:=0
	for part in edits:
		var rows: Dictionary=edits[part]
		for address in rows.keys():
			var prefix: String=""
			if part=="@root":
				for component in ["position/","rotation_xyzw/"]:
					if address.begins_with(component):prefix=component;break
			var source: String=prefix+left.id+"/"
			if address.begins_with(source):
				rows[prefix+right.id+"/"+address.substr(source.length())]=rows[address].duplicate(true)
		count+=rows.size()
		if count>4096:return {"error":"Splitting this clip would exceed the saved helper adjustment limit."}
	return {"data":result,"left_id":left.id,"right_id":right.id}

static func can_place(data: Dictionary, id: String, start: int, length: int, duration: int) -> bool:
	if start<0 or length<1 or start+length>duration+1:return false
	for other in data.animation_clips:
		if other.id!=id and start<other.start+other.length and other.start<start+length:return false
	return true

static func move(data: Dictionary, id: String, start: int, duration: int) -> Dictionary:
	var result:=promote(data);var index:=index_id(result,id)
	if index<0:return {"error":"The animation piece no longer exists."}
	var piece: Dictionary=result.animation_clips[index]
	if not can_place(result,id,start,int(piece.length),duration):return {"error":"Animation pieces cannot overlap or extend beyond the project. Choose a free space."}
	var delta:=start-int(piece.start)
	if result.draft_frame>=piece.start and result.draft_frame<piece.start+piece.length:result.draft_frame=clampi(int(result.draft_frame)+delta,0,duration)
	if result.has("shape_draft_frame") and result.shape_draft_frame>=piece.start and result.shape_draft_frame<piece.start+piece.length:result.shape_draft_frame=clampi(int(result.shape_draft_frame)+delta,0,duration)
	piece.start=start;update_presence(result,duration)
	return {"data":result}

static func remove(data: Dictionary, id: String, duration: int) -> Dictionary:
	var result:=promote(data);var index:=index_id(result,id)
	if index<0:return {"error":"The animation piece no longer exists."}
	result.animation_clips.remove_at(index);update_presence(result,duration)
	var settings: Dictionary=result.get("motion_assist",{})
	var edits: Dictionary=settings.get("track_helper_edits",{})
	if not edits.is_empty():
		for part in edits.keys():
			var rows: Dictionary=edits[part]
			for address in rows.keys():
				var owner: String=address
				if part=="@root":
					owner=owner.trim_prefix("position/").trim_prefix("rotation_xyzw/")
				if owner.begins_with(id+"/") or owner.begins_with("gap/"+id+"/"):rows.erase(address)
			if rows.is_empty():edits.erase(part)
		if edits.is_empty():
			settings.erase("track_helper_edits")
			var motion=load("res://src/motion_animation.gd")
			if settings.part_strengths.is_empty():
				settings.erase("part_strengths")
				settings.format=motion.SETTINGS
			else:settings.format=motion.PART_SETTINGS
	return {"data":result}

static func paste(data: Dictionary, source: Dictionary, start: int, duration: int) -> Dictionary:
	var result:=promote(data)
	if result.animation_clips.size()>=MAX_CLIPS:return {"error":"This object already has32 animation pieces."}
	if not can_place(result,"",start,int(source.length),duration):return {"error":"Choose a free space within the project for this animation piece."}
	var piece:=source.duplicate(true);piece.id=str(ResourceUID.create_id());piece.start=start
	if result.get("format") in ["studio_model_6","studio_model_7","studio_model_8","studio_model_9"]:piece["body_placeholder"]=false
	result.animation_clips.append(piece);update_presence(result,duration)
	return {"data":result,"clip_id":piece.id}

static func put_key(data: Dictionary, key: Dictionary, duration: int, shape_key:=false) -> Dictionary:
	var result:=promote(data);var frame:=int(key.frame);var index:=index_at(result,frame)
	if index<0:
		var previous:=-1;var following:=-1
		for i in range(result.animation_clips.size()):
			if result.animation_clips[i].start<frame:previous=i
			elif following<0:following=i
		if previous>=0 and can_extend_track(result.animation_clips[previous],shape_key,key.get("shapes",{})):
			index=previous;result.animation_clips[index].length=frame-int(result.animation_clips[index].start)+1
		elif following>=0 and can_extend_track(result.animation_clips[following],shape_key,key.get("shapes",{})):
			index=following
			var next: Dictionary=result.animation_clips[index];var extension:=int(next.start)-frame
			next.start=frame;next.length=int(next.length)+extension
			for source_key in next.keys:source_key.frame=int(source_key.frame)+extension
			for source_key in next.get("shape_keys",[]):source_key.frame=int(source_key.frame)+extension
			if next.has("shape_origin"):next.shape_origin=int(next.shape_origin)+extension
			if next.has("body_origin"):next.body_origin=int(next.body_origin)+extension
			for source_key in next.get("body_rest_keys",[]):source_key.frame=int(source_key.frame)+extension
			for id in next.get("body_controls",{}):
				for source_key in next.body_controls[id]:source_key.frame=int(source_key.frame)+extension
			for id in next.get("body_removed",{}):
				for i in range(next.body_removed[id].size()):next.body_removed[id][i]=int(next.body_removed[id][i])+extension
		else:
			# An edit outside a fixed slice must not resurrect its cropped control keys
			# or change its existing interpolation. Give the new authored motion a take.
			var authored:=clip(result,frame,1,0,[]);authored.auto_extend=true
			if shape_key:authored["shape_only"]=true
			result.animation_clips.append(authored);result.animation_clips.sort_custom(func(a,b):return a.start<b.start)
			index=index_at(result,frame)
	var piece: Dictionary=result.animation_clips[index]
	var stored:=key.duplicate(true);stored.frame=int(piece.source_in)+frame-int(piece.start)
	if shape_key:
		if not piece.has("shape_keys"):piece["shape_keys"]=[]
		if not piece.has("shape_origin"):piece["shape_origin"]=int(piece.source_in)
		for previous_key in piece.shape_keys:
			if previous_key.frame!=stored.frame:continue
			var values: Dictionary=previous_key.shapes.duplicate(true)
			var modes: Dictionary=previous_key.get("shape_modes",{}).duplicate(true)
			for node in stored.shapes:
				if not values.has(node):values[node]={}
				if not modes.has(node):modes[node]={}
				for target in stored.shapes[node]:values[node][target]=stored.shapes[node][target];modes[node][target]=stored.interpolation
			stored.shapes=values;stored["shape_modes"]=modes;stored.interpolation=previous_key.interpolation;break
		Timeline.put_key(piece.shape_keys,stored)
	else:
		Timeline.put_key(piece.keys,stored)
		if piece.has("shape_only"):piece.shape_only=false
	if frame<result.start_frame:result.presence_offset=frame-int(result.animation_clips[0].start)
	update_presence(result,duration)
	return result

static func complete_range(piece: Dictionary) -> bool:
	var frames:=[]
	for key in piece.keys:frames.append(int(key.frame))
	for key in piece.get("shape_keys",[]):frames.append(int(key.frame))
	for id in piece.get("body_controls",{}):
		for key in piece.body_controls[id]:frames.append(int(key.frame))
	for key in piece.get("body_rest_keys",[]):frames.append(int(key.frame))
	return not frames.is_empty() and frames.min()==piece.source_in and frames.max()==piece.source_in+piece.length-1

static func delete_key(data: Dictionary, frame: int) -> Dictionary:
	var result:=promote(data);var index:=index_at(result,frame)
	if index>=0:
		var piece: Dictionary=result.animation_clips[index];var at:=int(piece.source_in)+frame-int(piece.start)
		piece.keys=piece.keys.filter(func(key):return key.frame!=at)
		if not complete_range(piece):piece.auto_extend=false
	return result

static func curve(piece: Dictionary, frame: float) -> Dictionary:
	return {"keys":piece.keys,"shape_keys":piece.get("shape_keys",[]),"shape_origin":piece.get("shape_origin",int(piece.source_in)),"shape_leading_hold":piece.get("shape_leading_hold",false),"pose":piece.base_pose,"transform":piece.base_transform,"shapes":piece.get("base_shapes",{}),"frame":int(piece.source_in)+frame-int(piece.start)}

static func location(data: Dictionary, frame: float, include_shape_only:=false) -> Dictionary:
	var pieces: Array=data.animation_clips
	if not include_shape_only:pieces=pieces.filter(func(piece):return not piece.get("shape_only",false))
	if pieces.is_empty():
		var empty:={"keys":[],"pose":data.pose,"transform":transform(data),"shapes":data.get("shape_pose",{}),"frame":0}
		if not data.animation_clips.is_empty():
			empty=curve(data.animation_clips[0],frame);empty["keys"]=[]
		return {"a":empty,"b":empty,"t":0.0}
	var index:=-1
	for i in range(pieces.size()):
		if frame>=pieces[i].start and frame<pieces[i].start+pieces[i].length:index=i;break
	if index>=0:
		var current:=curve(pieces[index],frame)
		return {"a":current,"b":current,"t":0.0}
	if frame<pieces[0].start:
		var first:=curve(pieces[0],int(pieces[0].start))
		return {"a":first,"b":first,"t":0.0}
	var previous: Dictionary=pieces[0]
	for next in pieces:
		if next.start>frame:
			var last_frame:=int(previous.start)+int(previous.length)-1
			var a:=curve(previous,last_frame);var b:=curve(next,int(next.start))
			var raw_t:=float(frame-last_frame)/float(int(next.start)-last_frame);var t:=raw_t
			var interpolation:="ease"
			for key in previous.keys:
				if key.frame<=a.frame:interpolation=key.interpolation
			if interpolation=="hold":t=0
			elif interpolation=="ease":t=t*t*(3-2*t)
			return {"a":a,"b":b,"t":t,"gap":true,"raw_t":raw_t}
		previous=next
	var last:=curve(previous,int(previous.start)+int(previous.length)-1)
	return {"a":last,"b":last,"t":0.0}
