extends RefCounted
# Original HAS timing design. This module contains no Stop Motion Helper code.
const Timeline=preload("res://src/timeline.gd")
const FORMAT:="studio_camera_easing_preview_1"
const MAX_KEYS:=241 # Existing camera-key reader limit; this does not raise it.
const MAX_FRAME:=1000000

static func whole(value,minimum: int,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(float(value)) and value>=minimum and value<=maximum

static func number(value,minimum: float,maximum: float) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=minimum and value<=maximum

static func numeric_array(value,length: int) -> bool:
	if not value is Array or value.size()!=length:return false
	for item in value:
		if not number(item,-1e12,1e12):return false
	return true

static func digest(value) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256)
	context.update(var_to_bytes(value));return context.finish().hex_encode()

static func keys_error(keys,duration) -> String:
	if not whole(duration,1,MAX_FRAME):return "Camera easing needs a bounded whole scene length."
	if not keys is Array or keys.is_empty() or keys.size()>MAX_KEYS:return "Camera easing needs 1–241 camera keys."
	var previous:=-1
	for key in keys:
		if not key is Dictionary or not whole(key.get("frame"),0,int(duration)) or key.frame<=previous:return "Camera keys must have unique ordered whole frames inside the scene."
		if not numeric_array(key.get("position"),3) or not numeric_array(key.get("rotation_xyzw"),4):return "Camera easing needs finite position and quaternion values."
		var q: Array=key.rotation_xyzw
		if Vector4(q[0],q[1],q[2],q[3]).length()<0.001 or not number(key.get("fov"),1.,179.):return "Camera rotation or field of view is invalid."
		if key.get("interpolation") not in ["hold","linear","ease"]:return "Unknown camera interpolation."
		previous=int(key.frame)
	return Timeline.range_error(keys)

# Endpoint derivatives in [0,1] give a bounded monotone Hermite time map.
# Zero controls are exactly the old time parameter; full controls give smoothstep.
static func warp(t: float,leave: float,arrive: float) -> float:
	if t<=0.:return 0.
	if t>=1.:return 1.
	if leave==0. and arrive==0.:return t
	var a:=1.-leave;var b:=1.-arrive
	return ((a+b-2.)*t+(3.-2.*a-b))*t*t+a*t

static func compile(keys,controls,duration) -> Dictionary:
	var error:=keys_error(keys,duration)
	if not error.is_empty():return {"error":error}
	if not controls is Array or controls.size()>MAX_KEYS:return {"error":"Too many easing controls."}
	var by_frame:={};var copied: Array=[]
	for row in controls:
		if not row is Dictionary or row.size()!=3 or not row.has("frame") or not row.has("arrive") or not row.has("leave"):return {"error":"An easing control needs frame, arrive and leave only."}
		if not whole(row.frame,0,int(duration)) or by_frame.has(int(row.frame)) or not number(row.arrive,0.,1.) or not number(row.leave,0.,1.):return {"error":"Use unique camera-key frames and easing amounts from 0 to 100%."}
		var found:=false
		for key in keys:
			if key.frame==row.frame:found=true;break
		if not found:return {"error":"Easing controls must belong to actual camera keys."}
		var copy:={"frame":int(row.frame),"arrive":float(row.arrive),"leave":float(row.leave)}
		by_frame[copy.frame]=copy;copied.append(copy)
	copied.sort_custom(func(a,b):return a.frame<b.frame)
	var segments: Array=[]
	for index in range(keys.size()-1):
		var leave:=float(by_frame.get(int(keys[index].frame),{}).get("leave",0.))
		var arrive:=float(by_frame.get(int(keys[index+1].frame),{}).get("arrive",0.))
		if leave==0. and arrive==0.:continue
		if keys[index].interpolation=="hold":return {"error":"A Hold segment cannot ease. Choose Linear or Ease on its starting key first."}
		segments.append({"left":index,"right":index+1,"leave":leave,"arrive":arrive})
	var plan:={"format":FORMAT,"source_keys":keys.duplicate(true),"controls":copied,"segments":segments,"duration":int(duration),"source_sha256":digest(keys)}
	plan["plan_sha256"]=digest(plan);return plan

static func plan_error(plan) -> String:
	if not plan is Dictionary or plan.size()!=7 or plan.get("format")!=FORMAT:return "Unknown easing preview."
	if not plan.get("source_keys") is Array or not plan.get("controls") is Array or not plan.get("segments") is Array or not plan.get("source_sha256") is String or not plan.get("plan_sha256") is String:return "Invalid easing preview."
	var error:=keys_error(plan.source_keys,plan.get("duration"))
	if not error.is_empty():return error
	if digest(plan.source_keys)!=plan.source_sha256:return "Authored camera data changed inside this preview."
	var checked: Dictionary=plan.duplicate(true);checked.erase("plan_sha256")
	if digest(checked)!=plan.plan_sha256:return "The easing preview changed. Recalculate it."
	return ""

static func matches(plan,keys,duration) -> bool:
	return plan_error(plan).is_empty() and duration==plan.duration and digest(keys)==plan.source_sha256 and keys==plan.source_keys

static func sample(plan,frame) -> Dictionary:
	var error:=plan_error(plan)
	if not error.is_empty():return {"error":error}
	if not whole(frame,0,plan.duration):return {"error":"Camera preview needs a whole frame inside the scene."}
	var keys: Array=plan.source_keys
	for segment in plan.segments:
		var a: Dictionary=keys[segment.left];var b: Dictionary=keys[segment.right]
		if frame<=a.frame or frame>=b.frame:continue
		var t:=warp(float(frame-a.frame)/float(b.frame-a.frame),segment.leave,segment.arrive)
		if a.interpolation=="ease":t=t*t*(3.-2.*t)
		return {"position":Timeline.vector(a.position).lerp(Timeline.vector(b.position),t),"rotation":Timeline.quaternion(a.rotation_xyzw).slerp(Timeline.quaternion(b.rotation_xyzw),t),"fov":lerpf(float(a.fov),float(b.fov),t),"near":lerpf(float(a.get("near",Timeline.DEFAULT_NEAR)),float(b.get("near",Timeline.DEFAULT_NEAR)),t),"far":lerpf(float(a.get("far",Timeline.DEFAULT_FAR)),float(b.get("far",Timeline.DEFAULT_FAR)),t)}
	return Timeline.sample(keys,int(frame))

static func bake(plan) -> Dictionary:
	var error:=plan_error(plan)
	if not error.is_empty():return {"error":error}
	var total: int=plan.source_keys.size()
	for segment in plan.segments:
		total+=int(plan.source_keys[segment.right].frame-plan.source_keys[segment.left].frame)-1
	if total>MAX_KEYS:return {"error":"This bake would exceed the existing 241 camera-key limit. Use fewer or shorter selected segments."}
	var result: Array=plan.source_keys.duplicate(true);var added:=0
	for segment in plan.segments:
		for frame in range(int(plan.source_keys[segment.left].frame)+1,int(plan.source_keys[segment.right].frame)):
			var value:=sample(plan,frame)
			if value.has("error"):return value
			var row:=Timeline.key(frame,value.position,value.rotation,value.fov,"linear")
			row["near"]=value.near;row["far"]=value.far;result.append(row);added+=1
	result.sort_custom(func(a,b):return a.frame<b.frame)
	return {"keys":result,"added_keys":added,"source_sha256":plan.source_sha256,"integer_frames_sampled":true,"subframe_equality_qualified":false,"authored_keys_preserved":true}
