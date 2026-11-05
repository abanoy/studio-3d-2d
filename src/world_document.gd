extends RefCounted
# Schema4 domain data. Every map/model/group uses the existing model contract.
const Model = preload("res://src/model.gd")
const FORMAT := "studio_world_1"
const EFFECT_FORMAT := "studio_world_2"
const Particles=preload("res://src/particle_document.gd")
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
	if not world is Dictionary or not world.get("format") in [FORMAT,EFFECT_FORMAT] or not world.get("objects") is Array or world.objects.size()>MAX_OBJECTS:
		return "Invalid world record or more than64 objects."
	if world.format==FORMAT and world.has("effects"):return "Particle effects require world2/project schema5."
	if world.format==EFFECT_FORMAT and (not world.get("effects") is Array or world.effects.size()>Particles.MAX_EFFECTS):return "Invalid particle collection or more than16 effects."
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
	var identities:=index.duplicate()
	for row in world.get("effects",[]):
		var error:=Particles.validate(row,duration,portable)
		if not error.is_empty():return error
		if not identifier(row.get("id")) or identities.has(row.id):return "Invalid or duplicate particle ID."
		identities[row.id]=true
	for row in world.objects:
		var seen := {}
		var current: String = row.id
		while not current.is_empty():
			if seen.has(current): return "World parent hierarchy contains a cycle."
			if not index.has(current): return "World parent refers to a missing object."
			seen[current]=true
			current=index[current].parent_id
	return ""

static func assets(world: Dictionary) -> Array:
	var result:=[]
	for row in world.objects:result.append({"source":row.get("source",""),"path":asset_path(row.sha256),"sha256":row.sha256,"limit":128*1024*1024})
	for row in world.get("effects",[]):result.append_array(Particles.assets(row))
	return result

static func portable(world: Dictionary) -> Dictionary:
	var result := world.duplicate(true)
	for row in result.objects:
		row["path"]=asset_path(row.sha256)
		row.erase("source")
	for row in result.get("effects",[]):
		row["path"]=Particles.asset_path(row.sha256,"json");row["texture_path"]=Particles.asset_path(row.texture_sha256,"png")
		row.erase("source");row.erase("texture_source")
	return result

static func resolve(world: Dictionary, folder: String) -> Dictionary:
	var result := world.duplicate(true)
	for row in result.objects: row["source"]=folder.path_join(row.path)
	for row in result.get("effects",[]):row["source"]=folder.path_join(row.path);row["texture_source"]=folder.path_join(row.texture_path)
	return result

static func from_project(data: Dictionary) -> Dictionary:
	var version=data.get("schema_version")
	if not (version is int or version is float):return {"error":"Unsupported project version."}
	if version==4 or version==5:
		return data.world.duplicate(true) if data.get("world") is Dictionary else {"error":"Missing world record."}
	if version!=1 and version!=2 and version!=3:return {"error":"Unsupported project version."}
	return from_legacy(data)

static func from_legacy(data: Dictionary) -> Dictionary:
	if data.get("schema_version")==4 or data.get("schema_version")==5:return {"error":"Use from_project for an existing multi-object world."}
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
