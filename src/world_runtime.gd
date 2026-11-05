extends RefCounted
# Owns one prepared world. No source-specific rendering or posing branches.
const Document = preload("res://src/world_document.gd")
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
var root: Node3D
var data := {}
var instances := {}
var order: Array[String] = []
var current_frame := 0
var final_view := false
var duration := 0
var video_settings: Dictionary={}

static func prepare(document: Dictionary, duration: int) -> Dictionary:
	var error := Document.validate(document,duration)
	if not error.is_empty():return {"error":error}
	# Hash all inputs before allocating a new world. Never touch the installed world.
	var verified := {}
	for row in document.objects:
		if verified.has(row.source):
			if verified[row.source]!=row.sha256:return {"error":"Conflicting world asset identity."}
			continue
		var file := FileAccess.open(row.source,FileAccess.READ)
		if file==null or file.get_length()>128*1024*1024 or FileAccess.get_sha256(row.source)!=row.sha256:
			return {"error":"World asset changed, disappeared or exceeds128MiB: "+row.name}
		verified[row.source]=row.sha256
	var candidate = new()
	candidate.data=document.duplicate(true)
	candidate.duration=duration
	candidate.root=Node3D.new();candidate.root.name="StudioWorld"
	for row in candidate.data.objects:
		var decoded := SceneIO.load_glb(row.source)
		if decoded.has("error"):
			candidate.dispose();return {"error":decoded.error}
		var instance := Model.new()
		instance.world_context=weakref(candidate)
		instance.root=decoded.scene
		instance.base_root=instance.root.transform
		instance.data=row
		# Inventory before attaching other instances: a parent's rig cannot absorb a child's.
		instance.inventory(instance.root)
		# Capture mesh ownership before parent/child instances are attached.
		instance.opacity_materials=Model.Opacity.new();instance.opacity_materials.inventory(instance.root)
		error=instance.check_bindings()
		if not error.is_empty():
			instance.root.free();candidate.dispose();return {"error":error}
		candidate.root.add_child(instance.root)
		candidate.instances[row.id]=instance
	# Topological order, independent of serialization order, also gives deterministic evaluation.
	var pending: Array = candidate.data.objects.duplicate()
	while not pending.is_empty():
		for i in range(pending.size()-1,-1,-1):
			var row: Dictionary=pending[i]
			if not row.parent_id.is_empty() and not row.parent_id in candidate.order:continue
			var instance: RefCounted=candidate.instances[row.id]
			if not row.parent_id.is_empty():
				candidate.root.remove_child(instance.root)
				candidate.instances[row.parent_id].root.add_child(instance.root)
			candidate.order.append(row.id);pending.remove_at(i)
	return {"runtime":candidate}

func evaluate(frame: int, final := false, editing_id := "", video: Dictionary = {}) -> void:
	current_frame=frame;final_view=final
	video_settings=video
	for id in order:
		var instance: RefCounted=instances[id]
		var parent_alpha: float=instances[instance.data.parent_id].evaluated_opacity if not instance.data.parent_id.is_empty() else 1.0
		instance.apply(frame,id==editing_id,final,video,parent_alpha,editing_id)
		instance.root.visible=instance.root.visible and frame>=instance.data.start_frame

func instance(id: String) -> RefCounted:
	return instances.get(id)

func snapshot() -> Dictionary:
	var result:=data.duplicate(true)
	for i in range(result.objects.size()):result.objects[i]=instances[result.objects[i].id].data.duplicate(true)
	return result

func restore_instance(id: String, value: Dictionary) -> String:
	return restore_instances({id:value})

func restore_instances(values: Dictionary) -> String:
	var document:=snapshot()
	for id in values:
		if not values[id] is Dictionary:return "Invalid world edit value."
		var value: Dictionary=values[id]
		var validation:=Model.validate(value,duration)
		if not validation.is_empty():return validation
		if not instances.has(id) or value.get("id")!=id:return "World edit refers to a missing instance."
		var target: RefCounted=instances[id]
		for field in ["source","sha256","kind","parent_id"]:
			if target.data.get(field)!=value.get(field):return "This edit cannot replace an asset or reparent an instance."
		var probe:=Model.new();probe.data=value;probe.order=target.order;probe.bones=target.bones;probe.root=target.root
		var binding_error:=probe.check_bindings()
		if not binding_error.is_empty():return binding_error
		for i in range(document.objects.size()):
			if document.objects[i].id==id:document.objects[i]=value.duplicate(true)
	var error:=Document.validate(document,duration)
	if not error.is_empty():return error
	for id in values:instances[id].data=values[id].duplicate(true)
	return ""

func dispose() -> void:
	if is_instance_valid(root):
		if root.get_parent():root.get_parent().remove_child(root)
		root.free()
	root=null;instances.clear();order.clear()
