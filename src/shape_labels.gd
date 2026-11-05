extends RefCounted
# Local presentation estimates only; never rename native targets or bindings.
static var names: Dictionary={}
static func display(name: String,advanced: bool) -> String:
	if advanced:return name
	if names.is_empty():
		var parsed=JSON.parse_string(FileAccess.get_file_as_string("res://data/shape_names.en.json"))
		if parsed is Dictionary:names=parsed
	return str(names[name])+" ≈" if names.has(name) else name

static func part(name: String,index: int,advanced: bool) -> String:
	if advanced:return name
	var lower:=name.to_lower()
	if "face" in lower or "head" in lower:return "Face"
	if "body" in lower:return "Body"
	if "eye" in lower:return "Eyes"
	return "Part "+str(index+1)
