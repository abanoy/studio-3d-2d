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
var effects: Dictionary={}
var evaluation_error := ""
const Sprite=preload("res://src/particle_sprite.gd")

static func prepare(document: Dictionary, duration: int,incoming_video: Dictionary={}) -> Dictionary:
	var error := Document.validate(document,duration)
	if not error.is_empty():return {"error":error}
	# Hash all inputs before allocating a new world. Never touch the installed world.
	var verified := {}
	for row in Document.assets(document):
		if verified.has(row.source):
			if verified[row.source]!=row.sha256:return {"error":"Conflicting world asset identity."}
			continue
		var file := FileAccess.open(row.source,FileAccess.READ)
		if file==null or file.get_length()>row.limit or FileAccess.get_sha256(row.source)!=row.sha256:
			return {"error":"World asset changed, disappeared or exceeds its size limit."}
		verified[row.source]=row.sha256
	var loaded:=Document.Particles.collection(document)
	if loaded.has("error"):return loaded
	var candidate = new()
	candidate.data=document.duplicate(true)
	candidate.duration=duration
	var walking_video: Dictionary=incoming_video.duplicate(true);walking_video["duration_frames"]=duration
	if not walking_video.has("fps_num"):walking_video["fps_num"]=24
	if not walking_video.has("fps_den"):walking_video["fps_den"]=1
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
		if load("res://src/walking_animation.gd").active(row):instance.motion_video=walking_video.duplicate(true)
		error=instance.check_bindings()
		if not error.is_empty():
			instance.root.free();candidate.dispose();return {"error":error}
		candidate.root.add_child(instance.root)
		candidate.instances[row.id]=instance
	var textures:={}
	for row in candidate.data.get("effects",[]):
		var item: Dictionary=loaded.effects[row.id]
		if row.source_in_seconds>=item.data.duration:candidate.dispose();return {"error":"Particle trim begins beyond the prepared effect duration."}
		if not textures.has(row.texture_sha256):textures[row.texture_sha256]=ImageTexture.create_from_image(item.image)
		var effect:=Sprite.new()
		error=effect.setup(item.data,textures[row.texture_sha256])
		if not error.is_empty():candidate.dispose();return {"error":error}
		var q: Array=row.rotation_xyzw
		effect.root.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3]).normalized()).scaled(Vector3.ONE*row.scale),Vector3(row.position[0],row.position[1],row.position[2]))
		candidate.root.add_child(effect.root);candidate.effects[row.id]=effect
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
	error=load("res://src/walking_animation.gd").preflight_detached(candidate.root,candidate.instances.values(),walking_video)
	if not error.is_empty():candidate.dispose();return {"error":error}
	return {"runtime":candidate}

func evaluate(frame: int, final := false, editing_id := "", video: Dictionary = {}) -> void:
	if video.is_empty():video=video_settings
	evaluation_error=""
	if not effects.is_empty() and not preload("res://src/video_timing.gd").error(video.get("fps_num",24),video.get("fps_den",1)).is_empty():
		evaluation_error="Particle playback requires a valid project frame rate.";return
	current_frame=frame;final_view=final
	video_settings=video
	for id in order:
		var instance: RefCounted=instances[id]
		var parent_alpha: float=instances[instance.data.parent_id].evaluated_opacity if not instance.data.parent_id.is_empty() else 1.0
		instance.apply(frame,id==editing_id,final,video,parent_alpha,editing_id)
		instance.root.visible=instance.root.visible and frame>=instance.data.start_frame
	for row in data.get("effects",[]):
		var effect: RefCounted=effects[row.id]
		effect.root.visible=row.visible and frame>=row.start_frame and frame<row.end_frame
		var seconds: float=row.source_in_seconds+float(frame-row.start_frame)*float(video.get("fps_den",1))/float(video.get("fps_num",24))
		effect.evaluate(seconds if effect.root.visible else -1.)
		if not effect.evaluation_error.is_empty():evaluation_error=effect.evaluation_error

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
		probe.base_root=target.base_root;probe.world_context=target.world_context;probe.motion_video=target.motion_video.duplicate(true);probe.motion_video.duration_frames=duration
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
	root=null;instances.clear();order.clear();effects.clear()
