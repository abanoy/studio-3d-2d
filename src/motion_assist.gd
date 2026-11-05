extends RefCounted
# Experimental derived motion, separate from authored controls and project data.
# No normal Model evaluator or serialization is changed by this preview module.
const Model=preload("res://src/model.gd")
const T=Model.Timeline
const FORMAT:="studio_motion_assist_preview_1"
var _main: Array=[]
var _spans: Array=[]
var _helpers: Array=[]
var _duration:=0
var _fingerprint:=""
const PROFILE:=[[0.,0.],[.12,-.12],[.87,.20],[.96,-.04],[1.,0.]]

func build(keys,video: Dictionary,settings: Dictionary={}) -> String:
	return _build(keys,video,settings,240,241)

func build_source(keys,video: Dictionary,settings: Dictionary={}) -> String:
	# Utility domain for retained source controls outside a short visible slice.
	# This never increases the actual project's duration or storage limits.
	return _build(keys,video,settings,Model.Clips.MAX_SOURCE_FRAME,Model.Clips.MAX_TOTAL_KEYS)

func _build(keys,video: Dictionary,settings: Dictionary,maximum: int,key_limit: int) -> String:
	if not keys is Array or keys.is_empty() or keys.size()>key_limit:return "Invalid or excessive motion-preview main keys."
	if not Model.integer(video.get("fps_num"),1,240000) or not Model.integer(video.get("fps_den"),1,100000) or not Model.integer(video.get("duration_frames"),1,maximum):return "Invalid motion-preview frame rate or duration."
	var strength= settings.get("strength",.65);var distance_scale=settings.get("distance_scale",1.);var position_limit=settings.get("position_limit",.08);var rotation_limit=settings.get("rotation_limit",deg_to_rad(12.))
	for value in [strength,distance_scale,position_limit,rotation_limit]:
		if not (value is int or value is float) or not is_finite(float(value)):return "Motion settings must be finite numbers."
	if strength<0 or strength>1 or distance_scale<=0 or distance_scale>100000 or position_limit<0 or position_limit>1000 or rotation_limit<0 or rotation_limit>PI/2:return "Motion settings are outside the supported bounds."
	var duration: int=video.duration_frames;var previous:=-1
	for key in keys:
		if not key is Dictionary or not Model.integer(key.get("frame"),0,duration) or key.frame<=previous or not key.get("interpolation") in ["ease","linear","hold"] or not Model.transform_valid(key.get("value")):return "Invalid or unordered main motion key."
		if key.value.has("scale") and not Model.scale_valid(key.value.scale):return "Invalid main-key scale."
		previous=int(key.frame)
	var main: Array=keys.duplicate(true);var spans:=[];var helpers:=[];var fps: float=float(video.fps_num)/float(video.fps_den)
	for i in range(main.size()-1):
		var a: Dictionary=main[i];var b: Dictionary=main[i+1]
		if a.interpolation=="hold" or float(strength)==0:continue
		var seconds: float=float(b.frame-a.frame)/fps
		# Adjacent/very short controls leave no useful time for extra acting.
		# Preserve that deliberate timing instead of squeezing a bounce into a cut.
		if seconds<.12:continue
		var delta: Vector3=T.vector(b.value.position)-T.vector(a.value.position);var qa:=T.quaternion(a.value.rotation_xyzw);var qb:=T.quaternion(b.value.rotation_xyzw)
		var rotation: Quaternion=qa.inverse()*qb
		if rotation.w<0:rotation=-rotation
		var angle:=rotation.get_angle();var axis:=rotation.get_axis() if angle>.000001 else Vector3.RIGHT
		if delta.length()<.0000001 and angle<.0000001:continue
		var speed: float=delta.length()/float(distance_scale)/seconds+angle/seconds
		var amount: float=float(strength)*(1.-exp(-speed*.65))
		var p_gain: float=amount*minf(1.,float(position_limit)/maxf(.00000001,delta.length()*.2*amount))
		var q_gain: float=amount*minf(1.,float(rotation_limit)/maxf(.00000001,angle*.2*amount))
		var points:=[]
		for point in PROFILE:points.append({"frame":float(a.frame)+(float(b.frame)-float(a.frame))*point[0],"weight":point[1]})
		var span:={"from":float(a.frame),"to":float(b.frame),"delta":delta,"axis":axis,"angle":angle,"position_gain":p_gain,"rotation_gain":q_gain,"points":points,"drivers":[int(a.frame),int(b.frame)]}
		spans.append(span)
		for j in range(1,4):helpers.append({"id":"segment-%d-%d" % [i,j],"frame":points[j].frame,"kind":["anticipation","overshoot","recoil"][j-1],"drivers":span.drivers.duplicate(),"generated":true})
		if i==main.size()-2 and b.frame<duration:
			var finish: float=minf(float(duration),float(b.frame)+fps*.24);var length: float=finish-float(b.frame)
			var tail:=span.duplicate(true);tail.from=float(b.frame);tail.to=finish;tail.points=[{"frame":float(b.frame),"weight":0.},{"frame":float(b.frame)+length*.28,"weight":.04},{"frame":float(b.frame)+length*.60,"weight":-.015},{"frame":finish,"weight":0.}];spans.append(tail)
			for j in range(1,4):helpers.append({"id":"settle-%d-%d" % [i,j],"frame":tail.points[j].frame,"kind":"settle","drivers":span.drivers.duplicate(),"generated":true})
	for helper in helpers:
		var value:=evaluate(main,spans,float(helper.frame),1.)
		if not Model.transform_valid(value):return "Motion preview exceeds the supported coordinate range."
		helper["value"]=value
	# Publish only the complete valid plan; failed rebuilds preserve the old plan.
	_main=main;_spans=spans;_helpers=helpers;_duration=duration;_fingerprint=JSON.stringify({"main":main,"video":video,"settings":settings},"",true,true).sha256_text()
	return ""

static func baseline(main: Array,frame: float) -> Dictionary:
	for key in main:
		if frame==float(key.frame):return key.value.duplicate(true)
	var pair:=Model.curve_pair(main,frame);var value: Dictionary=Model.blend({"part":pair.a.value},{"part":pair.b.value},pair.t).part
	if pair.a.value.has("scale") or pair.b.value.has("scale"):value["scale"]=lerpf(float(pair.a.value.get("scale",1.)),float(pair.b.value.get("scale",1.)),pair.t)
	return value

static func evaluate(main: Array,spans: Array,frame: float,gain: float) -> Dictionary:
	var value:=baseline(main,frame)
	for key in main:
		if frame==float(key.frame):return value
	if gain==0:return value
	for span in spans:
		if frame<=span.from or frame>=span.to:continue
		var weight:=0.
		for i in range(span.points.size()-1):
			var a: Dictionary=span.points[i];var b: Dictionary=span.points[i+1]
			if frame<a.frame or frame>b.frame:continue
			var t: float=(frame-float(a.frame))/(float(b.frame)-float(a.frame));t=t*t*(3.-2.*t);weight=lerpf(float(a.weight),float(b.weight),t)*gain;break
		var p: Vector3=T.vector(value.position)+span.delta*(weight*span.position_gain)
		var q: Quaternion=(T.quaternion(value.rotation_xyzw)*Quaternion(span.axis,span.angle*weight*span.rotation_gain)).normalized()
		value.position=[p.x,p.y,p.z];value.rotation_xyzw=[q.x,q.y,q.z,q.w];break
	return value

func sample(frame: float,gain:=1.) -> Dictionary:
	if _main.is_empty():return {"error":"Build motion preview first."}
	if not is_finite(frame) or frame<0 or frame>_duration or not is_finite(gain) or gain<0 or gain>1:return {"error":"Invalid motion-preview query."}
	var value:=evaluate(_main,_spans,frame,gain)
	return value if Model.transform_valid(value) else {"error":"Motion preview exceeds the supported coordinate range."}

func main_keys() -> Array:return _main.duplicate(true)
func helper_keys() -> Array:return _helpers.duplicate(true)
func fingerprint() -> String:return _fingerprint
func end_frame() -> int:return _duration
