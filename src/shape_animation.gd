extends RefCounted
# Dedicated expression controls share piece source time, never body pose keys.
const FORMAT:="studio_model_5"
const LEGACY_FORMAT:="studio_model_4"
const Clips=preload("res://src/animation_clips.gd")
const Shape=preload("res://src/source_shape.gd")

static func independent(data: Dictionary) -> bool:return data.get("format") in [FORMAT,"studio_model_6","studio_model_7","studio_model_8","studio_model_9"]
static func has_data(data: Dictionary) -> bool:return independent(data) or data.get("format")==LEGACY_FORMAT

static func integer(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=0 and value<=Clips.MAX_SOURCE_FRAME

static func values_valid(values) -> bool:
	return Shape.validate({"format":"studio_source_shape_2","enabled":false,"overrides":values}).is_empty()

static func validate(data: Dictionary) -> String:
	if not has_data(data):
		for field in ["shape_base","shape_pose","shape_names","shape_starts","shape_draft_frame"]:
			if data.has(field):return "Animated shapes require a compatible model version."
		for piece in data.get("animation_clips",[]):
			if piece.has("base_shapes") or piece.has("shape_keys") or piece.has("shape_only") or piece.has("shape_origin"):return "Animated shapes require a compatible model version."
			for key in piece.keys:
				if key.has("shapes"):return "Animated shapes require standard model version4."
		for key in data.pose_keys:
			if key.has("shapes"):return "Animated shapes require standard model version4."
		return ""
	if not values_valid(data.get("shape_base")) or not values_valid(data.get("shape_pose")):return "Invalid animated shape defaults or draft."
	var total:=0
	for piece in data.get("animation_clips",[]):
		if data.format==LEGACY_FORMAT:
			if piece.has("shape_keys") or piece.has("shape_only") or piece.has("shape_origin") or piece.has("shape_leading_hold"):return "Independent shape controls require model version5."
			continue
		if piece.has("shape_only") and (not piece.shape_only is bool or piece.shape_only and not piece.keys.is_empty()):return "Invalid expression-only piece."
		if piece.has("shape_origin") and not integer(piece.shape_origin):return "Invalid shape source origin."
		if piece.has("shape_leading_hold") and not piece.shape_leading_hold is bool:return "Invalid shape leading hold."
		var controls=piece.get("shape_keys",[])
		if not controls is Array or controls.size()>241:return "Invalid or excessive shape controls."
		total+=piece.keys.size()+controls.size();var previous:=-1
		for key in piece.keys:
			if key.has("shapes"):return "Version5 expressions must use their own controls."
		for key in controls:
			if not key is Dictionary or not integer(key.get("frame")) or key.frame<=previous or not key.get("interpolation") in ["hold","linear","ease"] or not values_valid(key.get("shapes")) or key.shapes.is_empty():return "Invalid or unsorted shape controls."
			previous=int(key.frame)
			var modes=key.get("shape_modes",{})
			if not modes is Dictionary:return "Invalid shape interpolation choices."
			for node in modes:
				if not modes[node] is Dictionary or not key.shapes.has(node):return "Invalid shape interpolation identity."
				for index in modes[node]:
					if not key.shapes[node].has(index) or not modes[node][index] in ["hold","linear","ease"]:return "Invalid shape interpolation choice."
		if piece.get("auto_extend",false) and (piece.source_in!=0 or not Clips.complete_range(piece)):return "Authored piece must own its complete control range."
	if total>Clips.MAX_TOTAL_KEYS:return "Animation pieces exceed2048 combined body/expression controls."
	if independent(data) and not integer(data.get("shape_draft_frame")):return "Invalid expression draft frame."
	if independent(data):
		var starts=data.get("shape_starts")
		if not starts is Dictionary:return "Missing expression introduction times."
		for node in starts:
			if not data.shape_base.has(node) or not starts[node] is Dictionary:return "Invalid expression introduction identity."
			for index in starts[node]:
				if not data.shape_base[node].has(index) or not integer(starts[node][index]):return "Invalid expression introduction time."
		for node in data.get("shape_base",{}):
			for index in data.shape_base[node]:
				if not starts.get(node,{}) is Dictionary or not integer(starts.get(node,{}).get(index)):return "Invalid expression introduction time."
	var names=data.get("shape_names",{})
	if not names is Dictionary or names.size()>2048:return "Invalid animated shape labels."
	for node in names:
		if not Shape.index_key(node,100000) or not names[node] is Dictionary:return "Invalid animated shape labels."
		for index in names[node]:
			if not Shape.index_key(index,2048) or not data.shape_base.get(node,{}).has(index) or not names[node][index] is String or names[node][index].length()>200:return "Invalid animated shape label."
	for values in snapshots(data):
		if not values_valid(values):return "Invalid animated shape amounts."
		for node in values:
			for index in values[node]:
				if not data.shape_base.get(node,{}).has(index):return "Animated shape is missing its original base amount."
	return ""

static func snapshots(data: Dictionary) -> Array:
	var result: Array=[data.get("shape_base",{}),data.get("shape_pose",{})]
	for piece in data.get("animation_clips",[]):
		result.append(piece.get("base_shapes",{}))
		for key in piece.keys:result.append(key.get("shapes",{}))
		for key in piece.get("shape_keys",[]):result.append(key.shapes)
	for key in data.pose_keys:result.append(key.get("shapes",{}))
	return result

static func fill(values: Dictionary,base: Dictionary) -> Dictionary:
	var result:=base.duplicate(true)
	for node in values:
		if not result.has(node):result[node]={}
		for index in values[node]:result[node][index]=values[node][index]
	return result

static func blend(a: Dictionary,b: Dictionary,t: float,base: Dictionary) -> Dictionary:
	var aa:=fill(a,base);var bb:=fill(b,base);var result:=base.duplicate(true)
	for node in base:
		for index in base[node]:result[node][index]=lerpf(float(aa[node][index]),float(bb[node][index]),t)
	return result

static func curve(at: Dictionary,base: Dictionary) -> Dictionary:
	var keys: Array=at["keys"]
	if keys.is_empty():return fill(at.get("shapes",{}),base)
	var a: Dictionary=keys[0];var b: Dictionary=keys[-1]
	if at.frame<=a.frame:b=a
	elif at.frame>=b.frame:a=b
	else:
		for i in range(keys.size()-1):
			if at.frame>=keys[i].frame and at.frame<keys[i+1].frame:a=keys[i];b=keys[i+1];break
	var t:=0.0 if a.frame==b.frame else float(at.frame-a.frame)/float(b.frame-a.frame)
	if a.interpolation=="hold":t=0
	elif a.interpolation=="ease":t=t*t*(3-2*t)
	return blend(a.get("shapes",{}),b.get("shapes",{}),t,base)

static func sample(data: Dictionary,frame: float,editing:=false) -> Dictionary:
	if not has_data(data):return {}
	var draft_frame: int=int(data.get("shape_draft_frame",data.draft_frame)) if independent(data) else int(data.draft_frame)
	if editing and draft_frame==frame:return fill(data.shape_pose,data.shape_base)
	if independent(data):return independent_sample(data,frame)
	var at:=Clips.location(data,frame)
	var a:=curve(at.a,data.shape_base)
	return a if at.t==0 else blend(a,curve(at.b,data.shape_base),at.t,data.shape_base)

static func configuration(base: Dictionary,values: Dictionary) -> Dictionary:
	var result:=base.duplicate(true);result.format="studio_source_shape_2"
	result["overrides"]=fill(values,result.get("overrides",{}))
	return result

static func promote(data: Dictionary) -> Dictionary:
	var result:=Clips.promote(data)
	if independent(result):return result
	if result.format==LEGACY_FORMAT:
		result["shape_starts"]={}
		for node in result.shape_base:
			result.shape_starts[node]={}
			for index in result.shape_base[node]:result.shape_starts[node][index]=int(result.start_frame)
		for piece in result.animation_clips:
			var controls:=[]
			for key in piece.keys:
				controls.append({"frame":int(key.frame),"shapes":fill(key.get("shapes",{}),result.shape_base),"interpolation":key.interpolation})
				key.erase("shapes")
			if controls.is_empty() and not result.shape_base.is_empty():controls.append({"frame":int(piece.source_in),"shapes":fill(piece.get("base_shapes",{}),result.shape_base),"interpolation":"ease"})
			piece["shape_keys"]=controls;piece["shape_leading_hold"]=true
		result.format=FORMAT;result["shape_draft_frame"]=int(result.draft_frame)
		return result
	result.format=FORMAT;result["shape_base"]={};result["shape_pose"]={};result["shape_names"]={}
	result["shape_draft_frame"]=int(result.draft_frame)
	result["shape_starts"]={}
	if not result.has("visibility_keys"):result["visibility_keys"]=[]
	return result

static func put_key(data: Dictionary,key: Dictionary,duration: int) -> Dictionary:
	var candidate:=data.duplicate(true);var index:=Clips.index_at(candidate,float(key.frame));var first:=false
	if index>=0:
		var piece: Dictionary=candidate.animation_clips[index]
		if piece.keys.is_empty() and piece.get("shape_keys",[]).is_empty() and piece.get("body_legacy_channels",[]).is_empty() and piece.get("body_controls",{}).is_empty() and piece.get("body_rest_keys",[]).is_empty() and piece.length==1:
			piece.source_in=0;piece["shape_only"]=true;first=true
	var stored:={"frame":key.frame,"shapes":key.shapes.duplicate(true),"interpolation":key.interpolation}
	var result:=Clips.put_key(candidate,stored,duration,true)
	if first:result.animation_clips[Clips.index_at(result,float(key.frame))].auto_extend=true
	return result

static func eased(t: float,mode: String) -> float:
	return 0. if mode=="hold" else t*t*(3.-2.*t) if mode=="ease" else t

static func points(at: Dictionary,base: Dictionary,node: String,index: String) -> Array:
	var result:=[]
	for key in at.get("shape_keys",[]):
		if key.shapes.get(node,{}).has(index):result.append({"frame":key.frame,"value":float(key.shapes[node][index]),"mode":str(key.get("shape_modes",{}).get(node,{}).get(index,key.interpolation))})
	if not result.is_empty() and not at.get("shape_leading_hold",false) and int(at.shape_origin)<result[0].frame:
		result.push_front({"frame":int(at.shape_origin),"value":float(at.shapes.get(node,{}).get(index,base[node][index])),"mode":result[0].mode})
	return result

static func amount_at(at: Dictionary,base: Dictionary,node: String,index: String) -> Dictionary:
	var controls:=points(at,base,node,index)
	if controls.is_empty():return {"value":float(at.shapes.get(node,{}).get(index,base[node][index])),"mode":"ease"}
	var a: Dictionary=controls[0];var b: Dictionary=controls[-1]
	if at.frame<=a.frame:b=a
	elif at.frame>=b.frame:a=b
	else:
		for i in range(controls.size()-1):
			if at.frame>=controls[i].frame and at.frame<controls[i+1].frame:a=controls[i];b=controls[i+1];break
	var t:=0. if a.frame==b.frame else float(at.frame-a.frame)/float(b.frame-a.frame)
	return {"value":lerpf(a.value,b.value,eased(t,a.mode)),"mode":a.mode}

static func independent_sample(data: Dictionary,frame: float) -> Dictionary:
	var base: Dictionary=data.shape_base
	var result:=base.duplicate(true)
	for node in base:
		for index in base[node]:
			var document:=data.duplicate()
			document.animation_clips=data.animation_clips.filter(func(piece):return piece.get("shape_keys",[]).any(func(key):return key.shapes.get(node,{}).has(index)))
			if document.animation_clips.is_empty():continue
			var at:=Clips.location(document,frame,true)
			var a:=amount_at(at.a,base,node,index);var amount: float=a.value
			if at.get("gap",false):
				var b:=amount_at(at.b,base,node,index);amount=lerpf(a.value,b.value,eased(float(at.raw_t),a.mode))
			elif frame<document.animation_clips[0].start:
				var first: int=int(document.animation_clips[0].start);var introduction: int=int(data.shape_starts[node][index])
				if first>introduction:amount=lerpf(float(base[node][index]),amount,eased(clampf(float(frame-introduction)/float(first-introduction),0,1),a.mode))
			result[node][index]=amount
	return result

static func authored_keys(data: Dictionary) -> Array:
	var result:=[]
	for piece in data.get("animation_clips",[]):
		for key in piece.get("shape_keys",piece.keys if data.get("format")==LEGACY_FORMAT else []):
			if not key.has("shapes") or key.frame<piece.source_in or key.frame>=piece.source_in+piece.length:continue
			var projected: Dictionary=key.duplicate(true);projected.frame=int(piece.start)+int(key.frame)-int(piece.source_in);result.append(projected)
	return result

static func has_control(data: Dictionary,frame: int,node: String,index: String) -> bool:
	for key in authored_keys(data):
		if key.frame==frame and key.shapes.get(node,{}).has(index):return true
	return false

static func remove_key(data: Dictionary,frame: int,node: String,index: String) -> Dictionary:
	var result:=promote(data);var piece_index:=Clips.index_at(result,frame)
	if piece_index<0:return result
	var piece: Dictionary=result.animation_clips[piece_index];var at:=int(piece.source_in)+frame-int(piece.start)
	for key in piece.get("shape_keys",[]):
		if key.frame!=at or not key.shapes.get(node,{}).has(index):continue
		key.shapes[node].erase(index)
		if key.shapes[node].is_empty():key.shapes.erase(node)
		if key.get("shape_modes",{}).get(node,{}) is Dictionary:
			var modes: Dictionary=key.get("shape_modes",{});var part: Dictionary=modes.get(node,{})
			part.erase(index)
			if part.is_empty():modes.erase(node)
	piece.shape_keys=piece.get("shape_keys",[]).filter(func(key):return not key.shapes.is_empty())
	if not Clips.complete_range(piece):piece.auto_extend=false
	result.shape_pose=sample(result,frame);result.shape_draft_frame=frame
	return result
