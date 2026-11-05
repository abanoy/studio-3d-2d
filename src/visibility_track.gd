extends RefCounted
# Visibility is an independent project-time state, never inferred from motion blocks.
const FORMAT:="studio_model_3"

static func validate(data: Dictionary, duration: int) -> String:
	if not data.get("format") in [FORMAT,"studio_model_4","studio_model_5","studio_model_6","studio_model_7","studio_model_8"]:
		return "Visibility animation requires standard model version3." if data.has("visibility_keys") else ""
	if not data.get("visibility_keys") is Array or data.visibility_keys.size()>241:return "Invalid visibility keys."
	var previous:=-1
	for key in data.visibility_keys:
		if not key is Dictionary or not (key.get("frame") is int or key.get("frame") is float) or not is_finite(float(key.frame)) or key.frame!=floor(key.frame) or key.frame<0 or key.frame>duration or key.frame<=previous or not key.get("visible") is bool:return "Invalid or unsorted visibility keys."
		previous=int(key.frame)
	return ""

static func target(data: Dictionary, frame: int) -> bool:
	var result: bool=data.visible
	for key in data.get("visibility_keys",[]):
		if key.frame>frame:break
		result=key.visible
	return result

static func opacity(data: Dictionary, frame: int, video: Dictionary) -> float:
	var result:=1.0 if data.visible else 0.0
	var destination:=result;var initial:=result;var start:=0.0
	var fade:=float(video.get("visibility_fade_ms",300))*float(video.get("fps_num",24))/(1000.0*float(video.get("fps_den",1)))
	for key in data.get("visibility_keys",[]):
		if key.frame>frame:break
		var next:=1.0 if key.visible else 0.0
		if next==destination:continue
		result=lerpf(initial,destination,clampf((float(key.frame)-start)/fade,0,1)) if fade>0 else destination
		initial=result;destination=next;start=float(key.frame)
	return lerpf(initial,destination,clampf((float(frame)-start)/fade,0,1)) if fade>0 else destination

static func put(data: Dictionary, frame: int, value: bool) -> void:
	var keys: Array=data.visibility_keys
	for key in keys:
		if key.frame==frame:key.visible=value;return
	keys.append({"frame":frame,"visible":value});keys.sort_custom(func(a,b):return a.frame<b.frame)
