extends RefCounted
# Version9 independent root curves, preserving the shared body/contact record.
const Body=preload("res://src/body_animation.gd")
const Adapter=preload("res://src/root_component_clips.gd")
const Model=Body.Model
const FORMAT:="studio_model_9"

static func changed_root_fields(before: Dictionary,after: Dictionary) -> Array:
	var result:=[]
	if Model.Timeline.vector(before.position).distance_squared_to(Model.Timeline.vector(after.position))>1e-12:result.append("position")
	var a:=Model.Timeline.quaternion(before.rotation_xyzw);var b:=Model.Timeline.quaternion(after.rotation_xyzw)
	if a.dot(b)<0:b=-b
	if Vector4(a.x-b.x,a.y-b.y,a.z-b.z,a.w-b.w).length_squared()>1e-12:result.append("rotation_xyzw")
	if absf(float(before.get("scale",1.))-float(after.get("scale",1.)))>1e-7:result.append("scale")
	return result

static func put(data: Dictionary,key: Dictionary,duration: int,prior: Dictionary) -> Dictionary:
	var changed:=promote(prior,duration)
	if changed.has("error"):return changed
	var bones:={};var root_requested:=false
	for id in key.get("authored_channels",["@root"]+key.pose.keys()):
		if str(id).begins_with("@shape/"):continue
		if id=="@root":root_requested=true
		else:bones[id]=key.pose.get(id,Model.identity())
	if bones.is_empty() and not root_requested:return {"error":"Choose a body part to key."}
	if not bones.is_empty():
		changed=put_bones(changed.data,int(key.frame),bones,str(key.interpolation),duration)
		if changed.has("error"):return changed
	if root_requested:
		var fields=key.get("root_component_fields",Adapter.Components.FIELDS)
		if not fields is Array or fields.is_empty():return {"error":"Choose root components to key."}
		for field in fields:
			if not field in Adapter.Components.FIELDS:return {"error":"Unknown root component."}
			changed=put_component(changed.data,int(key.frame),field,key.transform.get(field),str(key.interpolation),duration)
			if changed.has("error"):return changed
	for field in ["pose","position","rotation_xyzw","scale","draft_frame","shape_pose","shape_draft_frame"]:
		if data.has(field):changed.data[field]=data[field].duplicate(true) if data[field] is Array or data[field] is Dictionary else data[field]
	var error:=validate(changed.data,duration)
	return changed if error.is_empty() else {"error":error}

static func remove_pose_key(data: Dictionary,frame: int,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if not Model.integer(frame,0,duration):return {"error":"Invalid pose key frame."}
	var result: Dictionary=promoted.data
	for key in authored_keys(result,duration):
		if key.frame!=frame:continue
		for field in key.root_component_modes:
			var removed:=remove_component(result,frame,field,duration)
			if removed.has("error"):return removed
			result=removed.data
		for id in key.body_modes:
			var removed:=Body.remove_key(legacy_view(result),frame,id,duration)
			if removed.has("error"):return removed
			var tracks: Dictionary=result.root_components
			result=removed.data;result["component_base_format"]=result.format;result.format=FORMAT;result["root_components"]=tracks
	var prepared:=compile(result,duration)
	if prepared.has("error"):return prepared
	var root:=Adapter.compiled_sample(prepared,frame)
	result.pose=Body.compile(legacy_view(result)).sample(frame).pose
	for field in Adapter.Components.FIELDS:result[field]=root[field]
	result.draft_frame=frame
	return {"data":result}

static func remove_part_key(data: Dictionary,frame: int,id: String,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if not Model.integer(frame,0,duration):return {"error":"Invalid pose key frame."}
	var result: Dictionary=promoted.data
	if id=="@root":
		for field in Adapter.Components.FIELDS:
			var removed:=remove_component(result,frame,field,duration)
			if removed.has("error"):return removed
			result=removed.data
	else:
		var removed:=Body.remove_key(legacy_view(result),frame,id,duration)
		if removed.has("error"):return removed
		removed.data["component_base_format"]=removed.data.format;removed.data.format=FORMAT
		removed.data["root_components"]=result.root_components;result=removed.data
	var prepared:=compile(result,duration)
	if prepared.has("error"):return prepared
	var root:=Adapter.compiled_sample(prepared,frame)
	result.pose=Body.compile(legacy_view(result)).sample(frame).pose
	for field in Adapter.Components.FIELDS:result[field]=root[field]
	result.draft_frame=frame
	return {"data":result}

static func authored_keys(data: Dictionary,duration: int) -> Array:
	var prepared:=compile(data,duration)
	if prepared.has("error"):return []
	var old:=legacy_view(data);var by_frame:={};var runtime:=Body.compile(old)
	for key in Body.authored_keys(old):
		var modes: Dictionary=key.body_modes.duplicate(true);modes.erase("@root")
		if not modes.is_empty():by_frame[int(key.frame)]={"body_modes":modes,"root_component_modes":{}}
	for key in controls(data):
		if not by_frame.has(key.frame):by_frame[key.frame]={"body_modes":{},"root_component_modes":{}}
		by_frame[key.frame].root_component_modes=key.components.duplicate(true)
	var times: Array=by_frame.keys();times.sort();var result:=[]
	for at in times:
		var row: Dictionary=by_frame[at];var channels: Array=row.body_modes.keys();channels.sort()
		if not row.root_component_modes.is_empty():channels.push_front("@root")
		var mode: String=row.root_component_modes.values()[0] if channels[0]=="@root" else row.body_modes[channels[0]]
		result.append({"frame":at,"pose":runtime.sample(at).pose,"transform":Adapter.compiled_sample(prepared,at),"authored_channels":channels,"body_modes":row.body_modes,"root_component_modes":row.root_component_modes,"interpolation":mode})
	return result

static func paste_clip(data: Dictionary,piece: Dictionary,components: Dictionary,start: int,duration: int) -> Dictionary:
	# Placement context/contact reanchoring belongs to the editor transaction.
	# Keep the supplied source controls intact, including keys outside a slice.
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if not Model.integer(piece.get("length"),1,duration+1):return {"error":"Invalid copied clip length."}
	var edited:=Model.Clips.paste(legacy_view(promoted.data),piece,start,duration)
	if edited.has("error"):return edited
	var result: Dictionary=edited.data
	result["component_base_format"]=result.format;result.format=FORMAT
	result["root_components"]=promoted.data.root_components.duplicate(true)
	if not components.is_empty():result.root_components[edited.clip_id]=components.duplicate(true)
	else:
		var extracted:=Adapter.extract(Body.view(result))
		if extracted.has(edited.clip_id):result.root_components[edited.clip_id]=extracted[edited.clip_id]
	var error:=validate(result,duration)
	return edited if error.is_empty() else {"error":error}

static func record_pose(data: Dictionary,frame: int,pose: Dictionary,transform: Dictionary,mode: String,duration: int) -> Dictionary:
	# Build a complete candidate before exposing it to the caller's Undo commit.
	if pose.has("@root") or not Model.pose_valid(pose) or not Model.transform_valid(transform):return {"error":"Invalid recorded pose."}
	var changed:=promote(data,duration)
	if changed.has("error"):return changed
	if not pose.is_empty():
		changed=put_bones(changed.data,frame,pose,mode,duration)
		if changed.has("error"):return changed
	for field in Adapter.Components.FIELDS:
		changed=put_component(changed.data,frame,field,transform[field],mode,duration)
		if changed.has("error"):return changed
	changed.data.pose=pose.duplicate(true)
	for field in Adapter.Components.FIELDS:changed.data[field]=transform[field].duplicate(true) if transform[field] is Array else transform[field]
	changed.data.draft_frame=frame
	var error:=validate(changed.data,duration)
	return changed if error.is_empty() else {"error":error}

static func put_bones(data: Dictionary,frame: int,pose: Dictionary,mode: String,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if pose.has("@root") or pose.is_empty() or not Model.pose_valid(pose):return {"error":"Choose valid bone controls."}
	var original: Dictionary=promoted.data;var old:=legacy_view(original)
	var changed:=Body.B.put(Body.view(old),frame,pose,mode,duration)
	if changed.has("error"):return changed
	var result:=Body.install(old,changed.data);result["component_base_format"]=result.format;result.format=FORMAT;result["root_components"]={}
	for piece in result.animation_clips:
		if not original.root_components.has(piece.id):continue
		var index:=Model.Clips.index_id(old,piece.id);var prior: Dictionary=old.animation_clips[index]
		var delta:=int(piece.source_in)-int(prior.source_in)+int(prior.start)-int(piece.start)
		var tracks: Dictionary=original.root_components[piece.id].duplicate(true)
		for field in Adapter.Components.FIELDS:
			for key in tracks[field]:key.frame=int(key.frame)+delta
		result.root_components[piece.id]=tracks
	var error:=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func controls(data: Dictionary) -> Array:
	var frames:={}
	for piece in data.animation_clips:
		for field in Adapter.Components.FIELDS:
			for key in data.root_components.get(piece.id,{}).get(field,[]):
				if not key.get("authored",true) or key.frame<piece.source_in or key.frame>=piece.source_in+piece.length:continue
				var at:=int(piece.start)+int(key.frame)-int(piece.source_in)
				if not frames.has(at):frames[at]={}
				frames[at][field]=key.interpolation
	var times: Array=frames.keys();times.sort();var result:=[]
	for at in times:result.append({"frame":at,"components":frames[at]})
	return result

static func remove_component(data: Dictionary,frame: int,field: String,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if not field in Adapter.Components.FIELDS or not Model.integer(frame,0,duration):return {"error":"Invalid component key."}
	var result: Dictionary=promoted.data;var index:=Model.Clips.index_at(legacy_view(result),frame)
	if index<0:return {"data":result}
	var piece: Dictionary=result.animation_clips[index]
	if not result.root_components.has(piece.id):return {"data":result}
	var source:=int(piece.source_in)+frame-int(piece.start)
	result.root_components[piece.id][field]=result.root_components[piece.id][field].filter(func(key):return key.frame!=source or not key.get("authored",true))
	var body:=Body.view(legacy_view(result));var original_piece: Dictionary=body.pieces[index]
	var authored: Array=Body.B.points(body,original_piece,"@root",false).map(func(key):return int(key.frame))
	if not source in authored:
		for key in Body.B.points(body,original_piece,"@root",true):
			if int(key.frame)!=source:continue
			var fallback: Dictionary=Adapter.Components.split([key])[field][0];fallback["authored"]=false
			Model.Timeline.put_key(result.root_components[piece.id][field],fallback)
	var error:=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func edit_clip(data: Dictionary,operation: String,id: String,frame: int,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	var original: Dictionary=promoted.data;var legacy:=legacy_view(original);var edited: Dictionary
	if operation=="split":edited=Model.Clips.split(legacy,frame)
	elif operation=="move":edited=Model.Clips.move(legacy,id,frame,duration)
	elif operation=="remove":edited=Model.Clips.remove(legacy,id,duration)
	else:return {"error":"Unknown component clip operation."}
	if edited.has("error"):return edited
	var result: Dictionary=edited.data;result["component_base_format"]=result.format;result.format=FORMAT;result["root_components"]=original.root_components.duplicate(true)
	if operation=="split" and result.root_components.has(edited.left_id):result.root_components[edited.right_id]=result.root_components[edited.left_id].duplicate(true)
	if operation=="remove":result.root_components.erase(id)
	var error:=validate(result,duration)
	if not error.is_empty():return {"error":error}
	edited.data=result;return edited

static func put_component(data: Dictionary,frame: int,field: String,value,mode: String,duration: int) -> Dictionary:
	var promoted:=promote(data,duration)
	if promoted.has("error"):return promoted
	if not Model.integer(frame,0,duration):return {"error":"Invalid component frame."}
	var result: Dictionary=promoted.data
	var index:=Model.Clips.index_at(legacy_view(result),frame)
	if index<0:
		var old:=legacy_view(result);var body:=Body.view(old);var flags:={}
		# A new gap point owns only its edited component. Do not extend a peer's
		# source range or shift its source addresses while allocating the clip.
		for row in body.pieces:flags[row.id]=row.auto_extend;row.auto_extend=false
		var prepared:=compile(result,duration)
		var base:=Adapter.compiled_sample(prepared,frame)
		var allocated:=Body.B.put(body,frame,{"@root":base},mode,duration)
		if allocated.has("error"):return allocated
		for row in allocated.data.pieces:
			if flags.has(row.id):row.auto_extend=flags[row.id]
		var tracks_before: Dictionary=result.root_components
		result=Body.install(old,allocated.data);result["component_base_format"]=result.format;result.format=FORMAT;result["root_components"]=tracks_before
		index=Model.Clips.index_at(legacy_view(result),frame)
		result.root_components[result.animation_clips[index].id]=Adapter.Components.split([])
	var piece: Dictionary=result.animation_clips[index]
	var tracks: Dictionary=result.root_components.get(piece.id,{})
	if tracks.is_empty():
		var body:=Body.view(legacy_view(result));tracks=Adapter.Components.split(Body.B.points(body,body.pieces[index],"@root",true))
	var changed:=Adapter.Components.put(tracks,field,int(piece.source_in)+frame-int(piece.start),value,mode)
	if changed.has("error"):return changed
	result.root_components[piece.id]=changed.data
	if piece.get("body_placeholder",false):piece.body_placeholder=false
	var error:=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func compile(data: Dictionary,duration: int) -> Dictionary:
	var error:=validate(data,duration)
	return {"error":error} if not error.is_empty() else Adapter.compile(Body.view(legacy_view(data)),data.root_components,duration)

static func legacy_view(data: Dictionary) -> Dictionary:
	var result:=data.duplicate(true);result.format=result.get("component_base_format","")
	result.erase("component_base_format");result.erase("root_components")
	return result

static func validate(data: Dictionary,duration: int) -> String:
	if data.get("format")!=FORMAT or not data.get("component_base_format") in [Model.BODY_FORMAT,Model.CONTACT_FORMAT,Model.MOTION_FORMAT] or not data.get("root_components") is Dictionary:return "Invalid component model version."
	if JSON.stringify(data).to_utf8_buffer().size()>1024*1024:return "Component model exceeds metadata limit."
	var old:=legacy_view(data);var error:=Model.validate(old,duration)
	if not error.is_empty():return error
	var prepared:=Adapter.compile(Body.view(old),data.root_components,duration)
	if prepared.has("error"):return prepared.error
	var total:=0
	for piece in old.animation_clips:
		total+=piece.keys.size()+piece.get("shape_keys",[]).size()+piece.get("body_rest_keys",[]).size()
		for keys in piece.body_controls.values():total+=keys.size()
		for removed in piece.body_removed.values():total+=removed.size()
	for tracks in data.root_components.values():
		for field in Adapter.Components.FIELDS:total+=tracks[field].size()
	return "Component model exceeds2048 stored controls." if total>Model.Clips.MAX_TOTAL_KEYS else ""

static func promote(data: Dictionary,duration: int) -> Dictionary:
	if data.get("format")==FORMAT:
		var error:=validate(data,duration)
		return {"data":data.duplicate(true)} if error.is_empty() else {"error":error}
	var error:=Model.validate(data,duration)
	if not error.is_empty():return {"error":error}
	var result:=Body.promote(data,duration)
	if result.has("error"):return result
	result["component_base_format"]=result.format;result["root_components"]=Adapter.extract(Body.view(result));result.format=FORMAT
	error=migrate_root_helpers(result)
	if not error.is_empty():return {"error":error}
	error=validate(result,duration)
	return {"data":result} if error.is_empty() else {"error":error}

static func migrate_root_helpers(result: Dictionary) -> String:
	var edits: Dictionary=result.get("motion_assist",{}).get("track_helper_edits",{})
	if not edits.has("@root"):return ""
	var migrated := {}
	var gaps := {}
	for address in edits["@root"]:
		var split_at: int=address.rfind("/")
		var clip: String=address.left(split_at)
		var role: PackedStringArray=address.substr(split_at+1).split("-")
		var connection:=clip.begins_with("gap/")
		if connection and gaps.is_empty():gaps=root_gap_controls(result)
		var owners: Dictionary=gaps if connection else result.root_components
		if not owners.has(clip) or role.size()!=4 or not role[0] in ["segment","settle"] or not role[1].is_valid_int() or not role[2].is_valid_int():
			return "Reset this model movement helper to automatic before separating its position and rotation tracks: "+address
		var matched := false
		for field in ["position","rotation_xyzw"]:
			var keys: Array=owners[clip].get(field,[])
			for i in range(1,keys.size()):
				var start: Dictionary=keys[i-1]
				var finish: Dictionary=keys[i]
				if int(start.frame)!=role[1].to_int() or int(finish.frame)!=role[2].to_int():continue
				var movement: float
				if field=="position":
					movement=Model.Timeline.vector(start.value.position).distance_to(Model.Timeline.vector(finish.value.position))
				else:
					movement=Model.Timeline.quaternion(start.value.rotation_xyzw).angle_to(Model.Timeline.quaternion(finish.value.rotation_xyzw))
				if movement>=.0000001 and start.interpolation!="hold":
					migrated[field+"/"+address]=edits["@root"][address].duplicate(true)
					matched=true
				break
		if not matched:return "The poses that drive a model movement helper have changed. Review its adjustment before separating tracks."
	edits["@root"]=migrated
	return ""

# Use the displayed slice boundaries. A trimmed clip can begin partway through
# its source curve, so its first stored source key is not the end of the gap.
static func root_gap_controls(result: Dictionary) -> Dictionary:
	var body:=Body.view(result)
	var gaps := {}
	for field in ["position","rotation_xyzw"]:
		var view:=Adapter.component_view(body,result.root_components,field)
		var runtime:=Adapter.Runtime.new()
		runtime.build(view)
		var index:=0
		var previous: Dictionary={}
		for owner in view.pieces:
			if not Adapter.B.owns(owner,"@root"):continue
			var piece: Dictionary=runtime.tracks["@root"][index]
			var first: int=piece.start
			var last: int=view.starts.get("@root",first) if previous.is_empty() else previous.start+previous.length-1
			if last<first:
				var finish:=Adapter.Runtime.at(piece,first,"@root")
				var start:=Adapter.Runtime.at(previous,last,"@root") if not previous.is_empty() else {"value":runtime.baseline["@root"],"mode":finish.mode}
				var address: String="gap/"+owner.id
				if not gaps.has(address):gaps[address]={}
				gaps[address][field]=[{"frame":last,"value":start.value,"interpolation":start.mode},{"frame":first,"value":finish.value}]
			previous=piece
			index+=1
	return gaps
