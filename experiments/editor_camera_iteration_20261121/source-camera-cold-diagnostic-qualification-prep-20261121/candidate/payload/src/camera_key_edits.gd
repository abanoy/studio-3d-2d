extends RefCounted
# Pure camera-key edits. Existing dictionaries and legacy off-scene keys are kept.
const Timeline=preload("res://src/timeline.gd")
const MAX_KEYS=241
const MAX_SCENE_FRAMES=7200 # Existing ExtendedTiming.MAX_FRAMES.
static func whole(value,minimum: int,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(float(value)) and value>=minimum and value<=maximum
static func numeric_array(value,length: int) -> bool:
	if not value is Array or value.size()!=length:return false
	for item in value:
		if not (item is int or item is float) or not is_finite(float(item)):return false
	return true
static func error(keys,duration) -> String:
	if not whole(duration,1,MAX_SCENE_FRAMES):return "Camera editing needs a valid scene duration."
	if not keys is Array or keys.is_empty() or keys.size()>MAX_KEYS:return "Keep 1–241 camera keys."
	var previous:=-1
	for key in keys:
		if not key is Dictionary or not whole(key.get("frame"),0,maxi(240,int(duration))) or key.frame<=previous:return "Camera keys must have unique ordered whole frames."
		if not numeric_array(key.get("position"),3) or not numeric_array(key.get("rotation_xyzw"),4):return "Camera key position or rotation is invalid."
		var fov=key.get("fov")
		if not (fov is int or fov is float) or not is_finite(float(fov)) or fov<1. or fov>179.:return "Camera field of view is invalid."
		var q: Array=key.rotation_xyzw
		if Vector4(q[0],q[1],q[2],q[3]).length()<.001 or not key.get("interpolation") in ["hold","linear","ease"]:return "Camera rotation or interpolation is invalid."
		previous=int(key.frame)
	return Timeline.range_error(keys)
static func index_at(keys: Array,frame: int) -> int:
	for i in range(keys.size()):
		if keys[i].frame==frame:return i
	return -1
static func retime(keys,source_frame,target_frame,duration) -> Dictionary:
	var why:=error(keys,duration)
	if not why.is_empty():return {"error":why}
	if not whole(source_frame,0,maxi(240,int(duration))) or not whole(target_frame,0,int(duration)):return {"error":"Choose a whole frame inside this scene."}
	var source:=index_at(keys,int(source_frame))
	if source<0:return {"error":"That camera key changed. Select it again."}
	if source_frame==target_frame:return {"keys":keys.duplicate(true),"changed":false,"selected_frame":int(source_frame)}
	if index_at(keys,int(target_frame))>=0:return {"error":"A camera key already exists there. Choose an empty frame."}
	var result: Array=keys.duplicate(true)
	result[source].frame=int(target_frame)
	result.sort_custom(func(a,b):return a.frame<b.frame)
	return {"keys":result,"changed":true,"selected_frame":int(target_frame)}
static func toggle(keys,at_frame,duration,capture: Dictionary={}) -> Dictionary:
	var why:=error(keys,duration)
	if not why.is_empty():return {"error":why}
	if not whole(at_frame,0,int(duration)):return {"error":"Choose a whole frame inside this scene."}
	var existing:=index_at(keys,int(at_frame))
	var result: Array=keys.duplicate(true)
	if existing>=0:
		if keys.size()==1:return {"error":"Keep at least one camera key. Add another before removing this one."}
		result.remove_at(existing)
		return {"keys":result,"changed":true,"selected_frame":-1,"removed":true}
	if keys.size()>=MAX_KEYS:return {"error":"This scene already has 241 camera keys."}
	var value: Dictionary=capture.duplicate(true);value.frame=int(at_frame)
	why=error([value],duration)
	if not why.is_empty():return {"error":why}
	result.append(value);result.sort_custom(func(a,b):return a.frame<b.frame)
	return {"keys":result,"changed":true,"selected_frame":int(at_frame),"removed":false}
static func digest(value) -> String:
	var hashing:=HashingContext.new();hashing.start(HashingContext.HASH_SHA256);hashing.update(var_to_bytes(value));return hashing.finish().hex_encode()
