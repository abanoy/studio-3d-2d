extends RefCounted
# Experimental root-only assistance. Bone assistance remains in its existing plan.
const D=preload("res://src/root_component_document.gd")
const Tracks=preload("res://src/motion_assist_tracks.gd")
var plans:={}

func build(data: Dictionary,video: Dictionary,settings: Dictionary={}) -> String:
	var error:=D.validate(data,int(video.duration_frames))
	if not error.is_empty():return error
	var component_edits := {"position":{}, "rotation_xyzw":{}}
	var edits = settings.get("track_helper_edits", {})
	if not edits is Dictionary:
		return "Invalid root helper adjustments."
	if not edits.is_empty() and (edits.size()!=1 or not edits.has("@root")):
		return "Independent model movement expects root helper adjustments."
	var root_edits = edits.get("@root", {})
	if not root_edits is Dictionary or root_edits.size()>4096:
		return "Invalid root helper adjustments."
	for address in root_edits:
		if not address is String:return "Invalid root helper address."
		var separator: int = address.find("/")
		var component: String = address.left(separator)
		if separator<=0 or not component_edits.has(component):
			return "Choose a movement or rotation helper."
		component_edits[component][address.substr(separator+1)] = root_edits[address]
	var old:=D.legacy_view(data);var body:=D.Body.view(old);var staged:={}
	for field in ["position","rotation_xyzw"]:
		var view:=D.Adapter.component_view(body,data.root_components,field)
		# A read-only single-component view may have no controls on a piece.
		# It does not own the complete editable body/expression boundary.
		for piece in view.pieces:piece.auto_extend=false
		var model:=D.Body.install(old,view);var plan:=Tracks.new()
		var scoped := settings.duplicate()
		scoped["track_helper_edits"]={"@root":component_edits[field]}
		error=plan.build(model,["@root"],video,scoped)
		if not error.is_empty():return error
		staged[field]=plan
	plans=staged;return ""

func apply(original: Dictionary,frame: float,gain:=1.) -> Dictionary:
	var result:=original.duplicate(true)
	for field in ["position","rotation_xyzw"]:
		var generated: Dictionary=plans[field].apply(original,"@root",frame,gain)
		if generated.has("error"):return generated
		result[field]=generated[field]
	return result

func helper_keys() -> Array:
	var result:=[]
	for field in plans:
		for key in plans[field].helper_keys().get("@root",[]):
			key["component"]=field;key.id=field+"/"+key.id;result.append(key)
	return result
