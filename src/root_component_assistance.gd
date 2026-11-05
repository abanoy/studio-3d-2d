extends RefCounted
# Experimental composite plan matching the ordinary model motion-plan interface.
const Root=preload("res://src/root_component_motion.gd")
const D=Root.D
var root_plan: RefCounted
var bone_plan: RefCounted

func build(data: Dictionary,video: Dictionary) -> String:
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
	root_plan=staged_root;bone_plan=staged_bones.plan;return ""

func apply(original: Dictionary,id: String,frame: float,gain:=1.) -> Dictionary:
	return root_plan.apply(original,frame,gain) if id=="@root" else bone_plan.apply(original,id,frame,gain)

func parts() -> Array:return bone_plan.parts()

func helper_keys() -> Dictionary:
	var result: Dictionary=bone_plan.helper_keys();result["@root"]=root_plan.helper_keys();return result
