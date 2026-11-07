extends RefCounted
# Experimental composite plan matching the ordinary model motion-plan interface.
const Root=preload("res://src/root_component_motion.gd")
const D=Root.D
var root_plan: RefCounted
var bone_plan: RefCounted
var walking: RefCounted
var walking_amount:=0.
var walking_parts: Array=[]

func build(data: Dictionary,video: Dictionary,actor: RefCounted=null) -> String:
	var error:=D.validate(data,int(video.duration_frames))
	if not error.is_empty():return error
	if data.component_base_format!=D.Model.MOTION_FORMAT:return "Component assistance needs motion settings."
	var bones: Dictionary=D.Model.motion_animation().settings(data)
	var root_settings := bones.duplicate()
	root_settings.track_helper_edits={}
	if bones.track_helper_edits.has("@root"):
		root_settings.track_helper_edits["@root"]=bones.track_helper_edits["@root"]
		bones.track_helper_edits.erase("@root")
	var staged_root:=Root.new();error=staged_root.build(data,video,root_settings)
	if not error.is_empty():return error
	var staged_bones: Dictionary=D.Model.motion_animation().compile(D.legacy_view(data),video,bones)
	if staged_bones.has("error"):return staged_bones.error
	var staged_walk: RefCounted;var parts: Array=[];var amount:=0.
	if load("res://src/walking_animation.gd").active(data):
		if actor==null:return "Walking needs a prepared model binding."
		staged_walk=load("res://src/path_locomotion.gd").new()
		error=staged_walk.build(actor,data,video,load("res://src/walking_animation.gd").corrections(data))
		if not error.is_empty():return error
		amount=float(data.motion_assist.walking.amount)*float(data.motion_assist.strength)
		for foot in staged_walk._feet:parts.append_array(foot.limb.ids)
	root_plan=staged_root;bone_plan=staged_bones.plan;walking=staged_walk;walking_parts=parts;walking_amount=amount;return ""

func apply(original: Dictionary,id: String,frame: float,gain:=1.) -> Dictionary:
	return apply_editing(original,id,frame,false,gain)

func apply_editing(original: Dictionary,id: String,frame: float,editing: bool,gain:=1.) -> Dictionary:
	if walking!=null and (id=="@root" or id in walking_parts):
		if not is_finite(gain) or gain<0 or gain>1:return {"error":"Invalid walking preview gain."}
		if frame<walking._start or frame>walking._end or editing and walking.draft_conflict(frame):return original
		var result: Dictionary=walking.sample(frame,walking_amount*gain)
		if result.has("error"):return result
		return result.transform if id=="@root" else result.pose.get(id,original)
	return root_plan.apply(original,frame,gain) if id=="@root" else bone_plan.apply(original,id,frame,gain)

func parts() -> Array:
	var result: Array=bone_plan.parts()
	for id in walking_parts:
		if not id in result:result.append(id)
	return result

func helper_keys() -> Dictionary:
	var result: Dictionary=bone_plan.helper_keys();result["@root"]=root_plan.helper_keys()
	if walking!=null:
		result.erase("@root")
		for id in walking_parts:result.erase(id)
	return result
