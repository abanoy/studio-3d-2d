extends RefCounted
# Model8 stores intent, not generated keys. Every renderer uses the same sampler.
const FORMAT:="studio_model_8"
const SETTINGS:="studio_motion_assist_1"
const Body=preload("res://src/body_animation.gd")
const Tracks=preload("res://src/motion_assist_tracks.gd")

static func validate(data: Dictionary) -> String:
	if data.get("format")!=FORMAT:return "Character assistance requires model version8." if data.has("motion_assist") else ""
	var value=data.get("motion_assist")
	if not value is Dictionary or value.size()!=3 or value.get("format")!=SETTINGS or not value.get("enabled") is bool:return "Invalid character-assistance settings."
	var strength=value.get("strength")
	return "Invalid character-assistance strength." if not (strength is int or strength is float) or not is_finite(float(strength)) or strength<0 or strength>1 else ""

static func configure(data: Dictionary,enabled: bool,strength: float,duration: int) -> Dictionary:
	var result: Dictionary=Body.Model.contact_animation().promote(data,duration)
	if result.has("error"):return result
	result.format=FORMAT;result["motion_assist"]={"format":SETTINGS,"enabled":enabled,"strength":strength}
	var error: String=Body.Model.validate(result,duration)
	return {"error":error} if not error.is_empty() else {"data":result}

static func parts(data: Dictionary) -> Array:
	var view:=Body.view(data);return Body.B.known_channels(view)

static func compile(data: Dictionary,video: Dictionary) -> Dictionary:
	var plan:=Tracks.new();var error: String=plan.build(data,parts(data),video,{"strength":data.motion_assist.strength})
	return {"error":error} if not error.is_empty() else {"plan":plan}
