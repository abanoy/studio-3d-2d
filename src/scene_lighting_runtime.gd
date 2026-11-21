extends RefCounted
const Document=preload("res://src/scene_lighting_document.gd")
var root: Node3D
var nodes: Dictionary={}
var stamp:=""
var last_error:=""
var reflection: ReflectionProbe

func setup(parent: Node3D) -> void:
	root=Node3D.new();root.name="AuthoredSceneLights";parent.add_child(root)

func sync(video: Dictionary) -> void:
	var data:=Document.document(video)
	var signature:=JSON.stringify(data)
	if signature!=stamp:
		last_error=Document.error(data)
		if not last_error.is_empty():
			root.hide();return
		stamp=signature
		sync_reflection(data)
		var retained:={}
		for row in data.lights:
			var light: Light3D=nodes.get(row.id)
			if light and light.get_meta("scene_light_type","")!=row.type:
				root.remove_child(light);light.queue_free();nodes.erase(row.id);light=null
			if not light:
				match row.type:
					"directional":light=DirectionalLight3D.new()
					"point":light=OmniLight3D.new()
					"spot":light=SpotLight3D.new()
				root.add_child(light);nodes[row.id]=light
			light.set_meta("scene_light_id",row.id)
			light.set_meta("scene_light_type",row.type)
			light.position=Vector3(row.position[0],row.position[1],row.position[2])
			light.rotation_degrees=Vector3(row.rotation_degrees[0],row.rotation_degrees[1],row.rotation_degrees[2])
			light.light_color=Color(row.color[0],row.color[1],row.color[2]);light.light_energy=row.energy
			light.visible=row.visible;light.shadow_enabled=row.shadows
			if light is OmniLight3D:light.omni_range=row.range
			if light is SpotLight3D:light.spot_range=row.range;light.spot_angle=row.spot_angle
			retained[row.id]=true
		for id in nodes.keys():
			if retained.has(id):continue
			var removed: Light3D=nodes[id];root.remove_child(removed);removed.queue_free();nodes.erase(id)
	root.visible=video.get("lighting_mode","studio")!="unshaded"

func sync_reflection(data: Dictionary) -> void:
	var settings: Dictionary=data.get("reflection",{})
	if not settings.get("enabled",false):
		if reflection:root.remove_child(reflection);reflection.queue_free();reflection=null
		return
	if not reflection:
		reflection=ReflectionProbe.new();reflection.name="RoomReflections"
		# One opt-in live cubemap, not ray tracing. Re-evaluate moving objects in
		# preview and offline frames rather than baking a stale editor snapshot.
		reflection.update_mode=ReflectionProbe.UPDATE_ALWAYS
		reflection.ambient_mode=ReflectionProbe.AMBIENT_DISABLED
		reflection.box_projection=true;reflection.enable_shadows=true
		# Layer 19 holds editor guides; layer 20 holds picking/outline copies.
		reflection.cull_mask=(1<<18)-1
		root.add_child(reflection)
	reflection.position=Vector3(settings.position[0],settings.position[1],settings.position[2])
	reflection.size=Vector3(settings.size[0],settings.size[1],settings.size[2])
	reflection.intensity=settings.intensity

func apply_ambient(video: Dictionary,environment: Environment) -> void:
	# Studio keeps its established ambient light. Lit's fill is explicit and optional.
	if video.get("lighting_mode","studio")=="studio":environment.ambient_light_color=Color("d2e2f2")
	if video.get("lighting_mode","studio")!="lit":return
	var data:=Document.document(video)
	if not Document.error(data).is_empty():return
	environment.ambient_light_color=Color(data.ambient_color[0],data.ambient_color[1],data.ambient_color[2])
	environment.ambient_light_energy=data.ambient_energy

static func material_limits(renderer: Node) -> String:
	var unlit:=0;var custom:=0;var baked:=0
	var inventories: Array=[]
	if renderer.world_runtime:
		for actor in renderer.world_runtime.instances.values():
			if actor.opacity_materials:inventories.append(actor.opacity_materials)
	else:
		if renderer.legacy_materials:inventories.append(renderer.legacy_materials)
		if renderer.model and renderer.model.opacity_materials:inventories.append(renderer.model.opacity_materials)
	for inventory in inventories:
		for mesh in inventory.meshes:
			if not is_instance_valid(mesh) or not mesh.mesh:continue
			for index in range(mesh.mesh.get_surface_count()):
				var material: Material=inventory.authored_material(mesh,index)
				if material is BaseMaterial3D and material.shading_mode==BaseMaterial3D.SHADING_MODE_UNSHADED:unlit+=1
				elif material is ShaderMaterial:custom+=1
				if material and material.has_meta("has_baked_lightmap_base"):baked+=1
	var messages: PackedStringArray=[]
	if unlit:messages.append("%d unlit surfaces cannot receive these lights. Use Unshaded for their intended look, or relink a version authored with lit materials."%unlit)
	if custom:messages.append("%d custom shader surfaces control their own lighting. Check the shader's light response or relink a supported lit-material version."%custom)
	if baked:messages.append("%d baked-lightmap surfaces retain their baked illumination; added lights do not rebake it."%baked)
	return "\n".join(messages)
