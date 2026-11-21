extends RefCounted
# Capability hints only. Every action still enters its existing validated editor.
const Model = preload("res://src/model.gd")
const Expressions = preload("res://src/expression_presets.gd")
const SPECS := [
	["face","Face / expressions","sparkle"],
	["body","Pose / move","joint"],
	["hair","Hair / clothes setup","fan"],
	["parameters","Model parameters","settings"],
	["visibility","Show / hide item","eye"],
	["appearance","Appearance","figure"],
	["materials","Materials","layers"]]

static func model(actor: RefCounted) -> bool:
	return actor != null and actor.get_script() == Model and is_instance_valid(actor.root) and actor.data.get("kind","model") == "model"

static func has_faces(actor: RefCounted) -> bool:
	if not model(actor): return false
	var shape: Variant = actor.root.get_meta(Model.Shape.META,{})
	var rows: Variant = shape.get("rows",[]) if shape is Dictionary else null
	return rows is Array and not rows.is_empty() or Expressions.has_data(actor.root)

static func optional_editor(pose: Node,name: String) -> Node:
	if pose == null: return null
	for descriptor in pose.get_property_list():
		if descriptor.name != name: continue
		var value: Variant = pose.get(name)
		return value if value is Node and is_instance_valid(value) and value.has_method("open") else null
	return null

static func appearance_available(pose: Node,actor: RefCounted) -> bool:
	var editor: Node = optional_editor(pose,"variant_editor")
	if editor == null or not editor.has_method("eligible"): return false
	var available: Variant = editor.eligible(actor)
	return typeof(available) == TYPE_BOOL and available

static func actions(actor: RefCounted,pose: Node,hair_available: bool,live: bool,frame: int) -> Array:
	var ready: bool = model(actor)
	var entries: Array = []
	for spec in SPECS:
		var enabled := ready
		var reason := "" if ready else "Select a model or accessory in World first."
		var title: String = spec[1]
		if spec[0] == "face" and ready and not has_faces(actor):
			enabled = false; reason = "This part has no retained facial controls. Select its head or full model; a hair-only asset may not include expressions."
		elif spec[0] == "hair" and ready and (actor.order.is_empty() or not hair_available or live):
			enabled = false; reason = "Turn this model's Physics and Hair & clothes off before opening setup." if live else "Select a skinned model with joints to review loose parts."
		elif spec[0] == "parameters" and ready:
			reason = "Open the existing model controls in the Pose inspector."
		elif spec[0] == "visibility" and ready:
			title = "Hide item" if actor.visible_at(frame) else "Show item"
			reason = "Change only this object's existing visibility at the current frame. This does not toggle physics or hide individual materials."
		elif spec[0] == "appearance" and ready and not appearance_available(pose,actor):
			enabled = false; reason = "This model has no available runtime appearance editor. Retained import choices remain separate."
		elif spec[0] == "materials":
			enabled = false; reason = "Individual material-surface visibility is a separate saved capability and is not available here yet. Item visibility stays separate."
		entries.append({"id":spec[0],"title":title,"icon":spec[2],"enabled":enabled,"reason":reason})
	return entries
