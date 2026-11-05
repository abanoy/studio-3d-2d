extends RefCounted
# Schema4 domain data. Every map/model/group uses the existing model contract.
const Model = preload("res://src/model.gd")
const FORMAT := "studio_world_1"
const MAX_OBJECTS := 64

static func empty() -> Dictionary:
	return {"format":FORMAT,"objects":[]}

static func object(path: String, kind := "model", name := "") -> Dictionary:
	var value := Model.definition(path)
	value["kind"] = kind
	value["parent_id"] = ""
	value["start_frame"] = 0
	if not name.is_empty(): value.name = name
	return value

static func identifier(value) -> bool:
	if not value is String or value.is_empty() or value.length()>128: return false
	for character in value:
		if character.unicode_at(0)<32 or character in ["/","\\",":"]: return false
	return true

static func asset_path(digest: String) -> String:
	return "assets/"+digest+".glb"

static func validate(world, duration: int, portable := false) -> String:
	if not world is Dictionary or world.get("format")!=FORMAT or not world.get("objects") is Array or world.objects.size()>MAX_OBJECTS:
		return "Invalid world record or more than64 objects."
	var index := {}
	for row in world.objects:
		var error := Model.validate(row,duration)
		if not error.is_empty() or row.is_empty(): return "Invalid world object: "+error
		if not identifier(row.id) or index.has(row.id): return "Invalid or duplicate world object ID."
		if not row.get("kind") in ["environment","model","group"] or not row.get("parent_id") is String: return "Invalid world object kind/parent."
		var start = row.get("start_frame")
		if not (start is int or start is float) or not is_finite(float(start)) or start!=floor(start) or start<0 or start>duration:
			return "Invalid first presence frame."
		if row.sha256.length()!=64: return "Invalid object asset checksum."
		for character in row.sha256:
			if not character in "0123456789abcdef": return "Invalid object asset checksum."
		if portable:
			if row.get("path")!=asset_path(row.sha256) or row.has("source"): return "Invalid managed world asset path."
		elif not row.get("source") is String or row.source.is_empty(): return "Missing world asset source."
		index[row.id]=row
	for row in world.objects:
		var seen := {}
		var current: String = row.id
		while not current.is_empty():
			if seen.has(current): return "World parent hierarchy contains a cycle."
			if not index.has(current): return "World parent refers to a missing object."
			seen[current]=true
			current=index[current].parent_id
	return ""

static func portable(world: Dictionary) -> Dictionary:
	var result := world.duplicate(true)
	for row in result.objects:
		row["path"]=asset_path(row.sha256)
		row.erase("source")
	return result

static func resolve(world: Dictionary, folder: String) -> Dictionary:
	var result := world.duplicate(true)
	for row in result.objects: row["source"]=folder.path_join(row.path)
	return result

static func from_project(data: Dictionary) -> Dictionary:
	var version=data.get("schema_version")
	if not (version is int or version is float):return {"error":"Unsupported project version."}
	if version==4:
		return data.world.duplicate(true) if data.get("world") is Dictionary else {"error":"Missing world record."}
	if version!=1 and version!=2 and version!=3:return {"error":"Unsupported project version."}
	return from_legacy(data)

static func from_legacy(data: Dictionary) -> Dictionary:
	if data.get("schema_version")==4:return {"error":"Use from_project for an existing multi-object world."}
	var result := empty()
	if not str(data.get("source","")).is_empty():
		var scene: Dictionary = data.get("scene",{})
		var row := object(data.source,"environment",str(scene.get("source_name","Environment")))
		row.id="legacy-scene-"+row.sha256
		if str(data.get("model",{}).get("id",""))==row.id: row.id+="-background"
		row.metadata["legacy_scene"]=scene.duplicate(true)
		result.objects.append(row)
	var model: Dictionary = data.get("model",{})
	if not model.is_empty():
		var row := model.duplicate(true)
		if not identifier(row.id):
			row.metadata["legacy_instance_id"]=row.id
			row.id="legacy-model-"+row.sha256
		row["kind"]="model";row["parent_id"]="";row["start_frame"]=0
		result.objects.append(row)
	return result
