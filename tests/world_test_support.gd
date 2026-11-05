extends RefCounted
# Test queries across legacy and world documents. Never changes product behavior.
static func rig(app, id := "") -> RefCounted:
	if not app.renderer.world_runtime:return app.renderer.model
	if not id.is_empty():return app.renderer.world_runtime.instance(id)
	var active: RefCounted=app.renderer.active_model()
	if active and active.data.kind=="model":return active
	var rows: Array=app.renderer.world_runtime.data.objects
	for i in range(rows.size()-1,-1,-1):
		if rows[i].kind=="model":return app.renderer.world_runtime.instance(rows[i].id)
	return null

static func select_rig(app, id := "") -> RefCounted:
	var model:=rig(app,id)
	if model:app.world_selection.select_entity(model.data.id if app.renderer.world_runtime else "model")
	return model

static func key(app, model: RefCounted) -> String:
	return model.data.id if app.renderer.world_runtime else "model"

static func keys(data: Dictionary) -> Array:
	var model=preload("res://src/model.gd").new();model.data=data
	return model.authored_keys()

static func same_keys(a: Dictionary,b: Dictionary) -> bool:
	return JSON.parse_string(JSON.stringify(keys(a),"",true,true))==JSON.parse_string(JSON.stringify(keys(b),"",true,true))

static func legacy_model(data: Dictionary) -> Dictionary:
	var result=preload("res://src/model.gd").definition(data.source)
	for field in ["id","name","position","rotation_xyzw","scale","pose","draft_frame","visible","reference_only","metadata","kind","parent_id","start_frame"]:
		if data.has(field):result[field]=data[field].duplicate(true) if data[field] is Array or data[field] is Dictionary else data[field]
	return result

static func set_pose_interpolation(model: RefCounted,frame: int,mode: String,duration:=48) -> void:
	var pose: Dictionary=model.sample(frame);var before: Dictionary=model.data.duplicate(true)
	var error: String=model.put_pose_key({"frame":frame,"pose":pose,"transform":model.sample_transform(frame),"authored_channels":["@root"]+pose.keys(),"interpolation":mode},duration,true,before)
	assert(error.is_empty(),error)
