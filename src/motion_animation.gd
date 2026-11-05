extends RefCounted
# Model8 stores intent, not generated keys. Every renderer uses the same sampler.
const FORMAT:="studio_model_8"
const PART_SETTINGS:="studio_motion_assist_2"
const HELPER_SETTINGS:="studio_motion_assist_3"
const SETTINGS:="studio_motion_assist_1"
const Body=preload("res://src/body_animation.gd")
const Tracks=preload("res://src/motion_assist_tracks.gd")

static func validate(data: Dictionary) -> String:
	if data.get("format")!=FORMAT and not (data.get("format")=="studio_model_9" and data.get("component_base_format")==FORMAT):return "Character assistance requires model version8." if data.has("motion_assist") else ""
	var value=data.get("motion_assist")
	if not value is Dictionary or not value.get("enabled") is bool:return "Invalid character-assistance settings."
	if value.get("format")==SETTINGS:
		if value.size()!=3:return "Invalid character-assistance settings."
	elif value.get("format") in [PART_SETTINGS,HELPER_SETTINGS]:
		var has_edits: bool=value.format==HELPER_SETTINGS
		if value.size()!=(5 if has_edits else 4) or not value.get("part_strengths") is Dictionary or value.part_strengths.size()>513:return "Invalid per-part assistance settings."
		if not has_edits and value.part_strengths.is_empty():return "Missing per-part assistance settings."
		for id in value.part_strengths:
			if not Body.B.valid_id(id) or not valid_strength(value.part_strengths[id]):return "Invalid per-part assistance strength."
		if has_edits:
			var edits=value.get("track_helper_edits")
			if not edits is Dictionary or edits.is_empty() or edits.size()>513:return "Invalid helper adjustments."
			var total := 0
			for part in edits:
				if not Body.B.valid_id(part) or not edits[part] is Dictionary or edits[part].is_empty():return "Invalid helper part."
				for address in edits[part]:
					total+=1
					if total>4096 or not address is String or address.length()>1024 or address.rfind("/")<=0 or address.ends_with("/"):return "Invalid helper address."
					var edit=edits[part][address]
					if not edit is Dictionary or edit.size()!=2 or not valid_strength(edit.get("amount")) or not valid_strength(edit.get("phase")) or edit.phase<=0 or edit.phase>=1:return "Invalid helper timing or amount."
	else:return "Unknown character-assistance settings version."
	return "" if valid_strength(value.get("strength")) else "Invalid character-assistance strength."

static func valid_strength(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=0 and value<=1

static func settings(data: Dictionary) -> Dictionary:
	return {"strength":data.motion_assist.strength,"part_strengths":data.motion_assist.get("part_strengths",{}).duplicate(true),"track_helper_edits":data.motion_assist.get("track_helper_edits",{}).duplicate(true)}

static func configure(data: Dictionary,enabled: bool,strength: float,duration: int,part_strengths=null,helper_edits=null) -> Dictionary:
	var result: Dictionary=Body.Model.contact_animation().promote(data,duration)
	if result.has("error"):return result
	if result.get("format")=="studio_model_9":result.component_base_format=FORMAT
	else:result.format=FORMAT
	result["motion_assist"]={"format":SETTINGS,"enabled":enabled,"strength":strength}
	var overrides=data.get("motion_assist",{}).get("part_strengths",{}) if part_strengths==null else part_strengths
	if not overrides is Dictionary:return {"error":"Invalid per-part assistance settings."}
	if not overrides.is_empty():result.motion_assist.format=PART_SETTINGS;result.motion_assist["part_strengths"]=overrides.duplicate(true)
	var edits=data.get("motion_assist",{}).get("track_helper_edits",{}) if helper_edits==null else helper_edits
	if not edits is Dictionary:return {"error":"Invalid helper adjustments."}
	if not edits.is_empty():
		result.motion_assist.format=HELPER_SETTINGS
		result.motion_assist["part_strengths"]=overrides.duplicate(true)
		result.motion_assist["track_helper_edits"]=edits.duplicate(true)
	var error: String=load("res://src/root_component_document.gd").validate(result,duration) if result.get("format")=="studio_model_9" else Body.Model.validate(result,duration)
	return {"error":error} if not error.is_empty() else {"data":result}

static func parts(data: Dictionary) -> Array:
	var view:=Body.view(data);return Body.B.known_channels(view)

# Removing a pose also removes adjustments driven by that exact source key.
# The editor records this whole model change in a single Undo entry.
static func after_key_removal(before: Dictionary, candidate: Dictionary, frame: int, part: String, duration: int) -> Dictionary:
	var setting: Dictionary=before.get("motion_assist",{})
	var edits: Dictionary=setting.get("track_helper_edits",{}).duplicate(true)
	if not edits.has(part) or candidate==before:return {"data":candidate}
	var index:=Body.Model.Clips.index_at(before,frame)
	if index<0:return {"data":candidate}
	var clip: Dictionary=before.animation_clips[index]
	var at:=int(clip.source_in)+frame-int(clip.start)
	var removed:=false
	for address in edits[part].keys():
		var local: String=address
		if part=="@root" and before.format=="studio_model_9":local=local.substr(local.find("/")+1)
		if local.get_slice("/",0)!=clip.id:continue
		var role:=local.get_slice("/",1).split("-")
		if role.size()==4 and (int(role[1])==at or int(role[2])==at):
			edits[part].erase(address)
			removed=true
	if not removed:return {"data":candidate}
	if edits[part].is_empty():edits.erase(part)
	return configure(candidate,setting.enabled,setting.strength,duration,null,edits)

static func compile(data: Dictionary,video: Dictionary,scoped_settings=null) -> Dictionary:
	var plan:=Tracks.new();var error: String=plan.build(data,parts(data),video,settings(data) if scoped_settings==null else scoped_settings)
	return {"error":error} if not error.is_empty() else {"plan":plan}
