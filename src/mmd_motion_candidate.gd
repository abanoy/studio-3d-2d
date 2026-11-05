extends RefCounted
const Model=preload("res://src/model.gd")
const Pose=preload("res://src/mmd_pose_candidate.gd")

static func split_at(data: Dictionary,boundary: int,duration: int) -> Dictionary:
	return preload("res://src/root_component_document.gd").edit_clip(data,"split","",boundary,duration) if data.get("format")=="studio_model_9" else Model.Clips.split(data,boundary)

static func prepare_range(rig: RefCounted,at: int,count: int,duration: int) -> Dictionary:
	var data: Dictionary=rig.body_animation().promote(rig.data,duration)
	if data.has("error"):return data
	var end:=at+count;var overlaps: Array=[];var reservation:=""
	for piece in data.animation_clips:
		if piece.start<end and piece.start+piece.length>at:overlaps.append(piece)
	if overlaps.size()>1:return {"error":"This range crosses existing animation blocks. Choose an empty range or a range inside one block."}
	if overlaps.is_empty():
		if data.animation_clips.size()>=Model.Clips.MAX_CLIPS:return {"error":"This object already has 32 animation pieces."}
		var piece:=Model.Clips.clip(data,at,count,at,[])
		piece["body_untrimmed"]=false;piece["body_placeholder"]=false
		# The shared body writer removes unowned empty takes. Reserve this one
		# until the first imported body/expression controls give it ownership.
		piece["mmd_motion_reservation"]=true;reservation=piece.id
		data.animation_clips.append(piece);data.animation_clips.sort_custom(func(a,b):return a.start<b.start)
	else:
		var piece: Dictionary=overlaps[0]
		if piece.start>at:return {"error":"The selected range begins before an existing block. Choose an empty range or start inside that block."}
		if piece.start+piece.length<end:
			if piece.id!=data.animation_clips[-1].id:return {"error":"The range extends past an existing block. Shorten the range or use an empty part of the timeline."}
			piece.length=end-int(piece.start);piece.auto_extend=false;piece["body_untrimmed"]=false
		for boundary in [at,end]:
			var index: int=Model.Clips.index_at(data,boundary)
			if index>=0 and boundary>data.animation_clips[index].start:
				var split:=split_at(data,boundary,duration)
				if split.has("error"):return split
				data=split.data
	var target: Dictionary=data.animation_clips[Model.Clips.index_at(data,at)]
	target.auto_extend=false;target["body_untrimmed"]=false;target["body_placeholder"]=false
	return {"data":data,"reservation":reservation}

static func start(rig: RefCounted,converted: Dictionary,at: int,duration: int,fps_num: int,fps_den:=1) -> Dictionary:
	if converted.get("format")!="studio_mmd_motion_conversion_1" or converted.get("model_sha256")!=rig.data.sha256:
		return {"error":"This motion preparation belongs to another model."}
	if converted.get("fps_num")!=fps_num or converted.get("fps_den")!=fps_den:return {"error":"The shot frame rate changed. Prepare the motion again."}
	var samples=converted.get("samples")
	if not samples is Array or samples.is_empty() or samples.size()>241 or at<0 or at+samples.size()>duration:
		return {"error":"Choose a motion range that fits inside the shot."}
	var prior_imports=rig.data.metadata.get("animation_imports",[])
	if not prior_imports is Array:return {"error":"This object's motion import metadata has an incompatible format."}
	if prior_imports.size()>=32:return {"error":"This object already records 32 motion imports."}
	var trial:=Model.new()
	var prepared:=prepare_range(rig,at,samples.size(),duration)
	if prepared.has("error"):return prepared
	trial.data=prepared.data;trial.root=rig.root;trial.bones=rig.bones;trial.order=rig.order
	return {"trial":trial,"prepared":prepared,"converted":converted,"samples":samples,"next":0,"summary":{},"at":at,"duration":duration,"fps_num":fps_num,"fps_den":fps_den,"prior_imports":prior_imports.duplicate(true)}

static func step(state: Dictionary,budget_usec:=4000) -> Dictionary:
	# One isolated candidate, shared with the synchronous API. Yield between
	# samples so normal editor input/cancel events can run. A sample is atomic.
	var trial: RefCounted=state.trial;var samples: Array=state.samples
	var began:=Time.get_ticks_usec();var first:=true
	while state.next<samples.size() and (first or Time.get_ticks_usec()-began<budget_usec):
		first=false
		var i: int=state.next
		if not samples[i] is Dictionary or samples[i].get("project_offset")!=i or samples[i].get("sample_interpolation")!="linear":return {"error":"Invalid sampled motion sequence."}
		var proposed:=Pose.candidate(trial,samples[i],state.at+i,state.duration)
		if proposed.has("error"):return {"error":"Motion frame %d: %s" % [state.at+i,proposed.error]}
		trial.data=proposed.data
		if i==0:state.summary={"matched_morphs":proposed.matched_morphs,"skipped_morphs":proposed.skipped_morphs}
		state.next+=1
	if state.next<samples.size():return {"pending":true,"completed":state.next,"total":samples.size()}
	if not state.prepared.reservation.is_empty():
		for piece in trial.data.animation_clips:
			if piece.id==state.prepared.reservation:piece.erase("mmd_motion_reservation")
	var converted: Dictionary=state.converted
	var imports: Array=state.prior_imports.duplicate(true)
	imports.append({"format":"studio_animation_import_1","kind":"mmd_vmd","source_file":str(converted.get("source_file","")).left(200),"source_sha256":converted.get("source_sha256",""),"source_fps":30,"source_start":converted.get("source_start",0),"original_start_frame":state.at,"original_last_frame":state.at+samples.size()-1,"fps_num":state.fps_num,"fps_den":state.fps_den})
	trial.data.metadata["animation_imports"]=imports
	var validation: String=Model.validate(trial.data,state.duration)
	if not validation.is_empty():return {"error":validation}
	return {"data":trial.data,"summary":state.summary,"first_frame":state.at,"last_frame":state.at+samples.size()-1}

static func candidate(rig: RefCounted,converted: Dictionary,at: int,duration: int,fps_num: int,fps_den:=1) -> Dictionary:
	var state:=start(rig,converted,at,duration,fps_num,fps_den)
	if state.has("error"):return state
	while true:
		var result:=step(state)
		if not result.get("pending",false):return result
	return {"error":"Motion preparation did not finish."}
