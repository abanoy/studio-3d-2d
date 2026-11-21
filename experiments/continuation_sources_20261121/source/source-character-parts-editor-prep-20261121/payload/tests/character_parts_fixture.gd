extends RefCounted
const Parts=preload("res://src/character_parts.gd")
const World=preload("res://src/world_document.gd")

static func policy() -> Dictionary:
	return {"origin":"retain_prepared_roots","units_already_in_glb":true,"metres_per_source_unit":0.0254}

static func row(id: String,kind: String="model",source: String="synthetic.glb",sha: String="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") -> Dictionary:
	return {"format":"studio_model_1","id":id,"name":id,"source":source,"sha256":sha,"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.,"visible":true,"reference_only":false,"pose":{},"draft_frame":0,"pose_keys":[],"metadata":{"fixture_owner":id,"opaque_user_data":{"keep":"synthetic"}},"kind":kind,"parent_id":"","start_frame":0}

static func inputs(source: String="synthetic.glb",sha: String="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") -> Dictionary:
	var result:={}
	for role in Parts.ROLES:result[role]={"row":row(role,"model",source,sha),"source_mdl_sha256":Parts.MDL[role],"unit_policy":policy()}
	return result

static func assembled() -> Dictionary:
	return Parts.assemble(World.empty(),row("junko","group"),inputs(),policy(),48)
