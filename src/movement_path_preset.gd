extends RefCounted
const PathData=preload("res://src/movement_path.gd")
const Model=PathData.Model
const Components=PathData.Components
const Timing=preload("res://src/video_timing.gd")
const FORMAT="studio_movement_path_preset_1"
const MAX_BYTES=64*1024
static func fields(value,keys: Array) -> bool:
	if not value is Dictionary or value.size()!=keys.size():return false
	for key in keys:
		if not value.has(key):return false
	return true
static func error(value) -> String:
	if not fields(value,["format","name","fps_num","fps_den","length","coordinate_space","keys"]) or value.format!=FORMAT or value.coordinate_space!="group_offset":return "Unsupported movement path preset."
	if not value.name is String or value.name.strip_edges().is_empty() or value.name.length()>80:return "Path name must contain 1–80 characters."
	for c in value.name:
		var n: int=c.unicode_at(0)
		if n<32 or n==127 or (n>=0xd800 and n<=0xdfff):return "Invalid path name."
	if not Timing.error(value.fps_num,value.fps_den).is_empty() or not Model.integer(value.length,1,240):return "Invalid path timing."
	if not value.keys is Array or value.keys.size()<2 or value.keys.size()>256:return "A saved path needs 2–256 movement points."
	var previous:=-1
	for key in value.keys:
		if not fields(key,["frame","offset","interpolation"]) or not Model.integer(key.frame,0,value.length) or key.frame<=previous or not key.interpolation in ["hold","linear","ease"] or not key.offset is Array or key.offset.size()!=3:return "Invalid movement path point."
		for n in key.offset:
			if not (n is int or n is float) or not is_finite(float(n)) or absf(float(n))>100000:return "Path offsets exceed supported coordinates."
		previous=int(key.frame)
	if value.keys[0].frame!=0 or value.keys[-1].frame!=value.length:return "Path must start at zero offset and end at its declared length."
	for n in value.keys[0].offset:
		if n!=0:return "Path must start at zero offset."
	if JSON.stringify(value,"",true,true).to_utf8_buffer().size()>MAX_BYTES:return "Path preset exceeds 64 KiB."
	return ""
static func sample(value: Dictionary,frame: float) -> Vector3:
	var a: Dictionary=value.keys[0];var b: Dictionary=a
	for key in value.keys:
		if key.frame<=frame:a=key;b=key
		else:b=key;break
	var t:=0.0 if a.frame==b.frame or a.interpolation=="hold" else clampf((frame-a.frame)/(b.frame-a.frame),0,1)
	if a.interpolation=="ease":t=t*t*(3-2*t)
	return Model.Timeline.vector(a.offset).lerp(Model.Timeline.vector(b.offset),t)
static func near(a: Vector3,b: Vector3) -> bool:
	# Godot's standard Vector3 is float32. Allow its coordinate-scale rounding,
	# never a changed curve or silent integer-frame bake of a trimmed interval.
	var magnitude:=maxf(1.0,maxf(a.length(),b.length()))
	return a.distance_to(b)<=maxf(.00001,magnitude*.0000002)
static func capture(data: Dictionary,video: Dictionary,name: String) -> Dictionary:
	if not preload("res://src/extended_timing.gd").video_error(video).is_empty():return {"error":"Invalid project timing for path preset."}
	if data.is_empty():return {"error":"Choose a model before exchanging movement paths."}
	var why:=Model.validate(data,int(video.duration_frames))
	if not why.is_empty():return {"error":why}
	var points:=PathData.controls(data)
	if points.size()<2:return {"error":"Add at least two movement points before saving a path preset."}
	var start:=int(points[0].frame);var origin: Vector3=points[0].position
	var preset:={"format":FORMAT,"name":name.strip_edges(),"fps_num":video.fps_num,"fps_den":video.fps_den,"length":int(points[-1].frame)-start,"coordinate_space":"group_offset","keys":[]}
	for point in points:
		var offset: Vector3=point.position-origin
		preset.keys.append({"frame":int(point.frame)-start,"offset":[offset.x,offset.y,offset.z],"interpolation":point.mode})
	why=error(preset)
	if not why.is_empty():return {"error":why}
	var probe:=Model.new();probe.data=data;probe.motion_video=video.duplicate(true)
	for half in range(int(preset.length)*2+1):
		var frame:=float(half)/2
		if not near(origin+sample(preset,frame),Model.Timeline.vector(probe.sample_authored_transform(start+frame).position)):
			return {"error":"This trimmed or gap curve cannot be exchanged exactly as waypoints. Use an ordinary continuous movement path."}
	return {"preset":preset}
static func assign(data: Dictionary,video: Dictionary,preset: Dictionary,frame: int) -> Dictionary:
	var why:=error(preset)
	if not why.is_empty():return {"error":why}
	if not preload("res://src/extended_timing.gd").video_error(video).is_empty():return {"error":"Invalid project timing for path preset."}
	if data.is_empty():return {"error":"Choose a model before exchanging movement paths."}
	why=Model.validate(data,int(video.duration_frames))
	if not why.is_empty():return {"error":why}
	if int(preset.fps_num)*int(video.fps_den)!=int(video.fps_num)*int(preset.fps_den):return {"error":"Path preset and project must use the same frame rate. No automatic retiming was applied."}
	var start:=int(data.get("start_frame",0));var duration:=int(video.duration_frames)
	if start+int(preset.length)>duration:return {"error":"This path does not fit after the model's introduction. Choose a shorter preset or extend the scene first."}
	var promoted:=Components.promote(data,duration)
	if promoted.has("error"):return promoted
	var result: Dictionary=promoted.data;var before:=Model.new();before.data=data;before.motion_video=video.duplicate(true)
	var anchor:=Model.Timeline.vector(before.sample_authored_transform(start).position)
	# An untouched import owns a one-frame placeholder, not authored motion.
	# Give it one continuous position interval instead of separated one-frame
	# pieces, whose half-frame tails would otherwise interrupt the saved curve.
	if result.animation_clips.size()==1 and result.animation_clips[0].get("body_placeholder",false):
		result.animation_clips[0].body_placeholder=false
		result.animation_clips[0].length=int(preset.length)+1
	# Replace the position channel only. Empty overrides suppress legacy position
	# fallbacks while retaining the exact turn/scale tracks on every existing piece.
	var extracted:=Components.Adapter.extract(Components.Body.view(Components.legacy_view(result)))
	for piece in result.animation_clips:
		var tracks: Dictionary=result.root_components.get(piece.id,extracted.get(piece.id,Components.Adapter.Components.split([]))).duplicate(true)
		tracks.position=[];result.root_components[piece.id]=tracks
	for key in preset.keys:
		var p:=anchor+Model.Timeline.vector(key.offset)
		var changed:=Components.put_component(result,start+int(key.frame),"position",[p.x,p.y,p.z],key.interpolation,duration)
		if changed.has("error"):return changed
		result=changed.data
	var refreshed:=PathData.refresh_draft({"data":result},clampi(frame,0,duration),duration)
	if refreshed.has("error"):return refreshed
	result=refreshed.data;var after:=Model.new();after.data=result;after.motion_video=video.duplicate(true)
	if int(result.start_frame)!=start:return {"error":"This path would change the model's introduction. Existing movement was kept."}
	for half in range(duration*2+1):
		var at:=float(half)/2;var a:=before.sample_authored_transform(at);var b:=after.sample_authored_transform(at)
		if a.rotation_xyzw!=b.rotation_xyzw or a.scale!=b.scale or before.sample_body(at)!=after.sample_body(at) or before.sample_shapes(at)!=after.sample_shapes(at):return {"error":"This path cannot preserve the existing pose/turn/size/expression tracks. Existing movement was kept."}
		if at>=start and not near(Model.Timeline.vector(b.position),anchor+sample(preset,at-start)):return {"error":"This clip layout cannot represent the saved path exactly. Existing movement was kept."}
	return {"data":result}
static func read_file(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>MAX_BYTES:return {"error":"Path preset is unavailable or exceeds 64 KiB."}
	var parser:=JSON.new();var code:=parser.parse(file.get_as_text());file.close()
	if code!=OK:return {"error":"Path preset is not valid JSON."}
	var parsed=parser.data;var why:=error(parsed)
	return {"preset":parsed} if why.is_empty() else {"error":why}
static func canonical(path: String) -> String:
	var value:=ProjectSettings.globalize_path(path).replace("\\","/").simplify_path()
	return value.to_lower() if OS.get_name()=="Windows" else value
static func write_file(path: String,preset: Dictionary,protected: Array=[]) -> String:
	var why:=error(preset)
	if not why.is_empty():return why
	if path.get_extension().to_lower()!="json":return "Choose a separate .haspaths.json preset file."
	for source in protected:
		if not str(source).is_empty() and canonical(path)==canonical(str(source)):return "Choose a separate path preset file; original source files stay unchanged."
	var temporary:=path+".studio-path-%d-%s.tmp" % [OS.get_process_id(),str(ResourceUID.create_id())]
	if FileAccess.file_exists(temporary) or DirAccess.dir_exists_absolute(temporary):return "Cannot reserve a path preset temporary file. Try again."
	var file:=FileAccess.open(temporary,FileAccess.WRITE)
	if not file:return "Cannot write this path preset."
	file.store_string(JSON.stringify(preset,"",true,true));file.flush();var code:=file.get_error();file.close()
	if code!=OK or DirAccess.rename_absolute(temporary,path)!=OK:
		DirAccess.remove_absolute(temporary);return "Cannot commit path preset; the previous file was kept."
	return ""
