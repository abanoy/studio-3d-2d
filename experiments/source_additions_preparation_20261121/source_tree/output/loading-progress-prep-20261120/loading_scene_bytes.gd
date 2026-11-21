extends RefCounted
# Unrun: exact current decoder body after bounded byte acquisition.
# All returned nodes/resources are fresh, unattached and unpublished until join.
const SceneIO=preload("res://src/scene3d.gd")
static func from_bytes(bytes: PackedByteArray) -> Dictionary:
	if bytes.size() < 20 or bytes.slice(0, 4).get_string_from_ascii() != "glTF":
		return {"error": "Not a valid binary glTF file."}
	if bytes.decode_u32(4) != 2 or bytes.decode_u32(8) != bytes.size() or bytes.decode_u32(16) != 0x4e4f534a:
		return {"error": "Invalid GLB version, length, or JSON chunk."}
	# Only self-contained GLBs. Prevent external resource traversal/network references.
	var json_size := bytes.decode_u32(12)
	if json_size > bytes.size() - 20:
		return {"error": "Broken GLB JSON chunk."}
	var parser := JSON.new()
	if parser.parse(bytes.slice(20, 20 + json_size).get_string_from_utf8()) != OK:
		return {"error": "Invalid GLB JSON."}
	var data = parser.data
	if not data is Dictionary:
		return {"error": "Invalid GLB JSON."}
	var required_error:=SceneIO.required_extensions_error(data)
	if not required_error.is_empty():return {"error":required_error}
	for group in [data.get("buffers", []), data.get("images", [])]:
		if not group is Array:
			return {"error": "Invalid GLB resource list."}
		for item in group:
			if not item is Dictionary or item.has("uri") and not item.uri is String:
				return {"error": "Invalid GLB resource entry."}
			if item.has("uri") and not str(item.uri).begins_with("data:"):
				return {"error": "External GLB resources unsupported. Embed textures and buffers when exporting."}
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var error := doc.append_from_buffer(bytes, "", state)
	if error != OK:
		return {"error": "GLB importer failed: %s" % error_string(error)}
	var shapes=preload("res://src/source_shape.gd")
	shapes.mark(state)
	# Godot4.6 ignores emissiveTexture.texCoord when building BaseMaterial3D.
	# Restore the declared standard channel on each scene-owned imported material.
	var imported: Array=state.get_materials();var definitions=data.get("materials",[])
	if definitions is Array:
		for i in range(mini(imported.size(),definitions.size())):
			if not imported[i] is BaseMaterial3D or not definitions[i] is Dictionary:continue
			var texture=definitions[i].get("emissiveTexture",{})
			if not texture is Dictionary:continue
			var channel=texture.get("texCoord",0)
			var transform=texture.get("extensions",{}).get("KHR_texture_transform",{}) if texture.get("extensions",{}) is Dictionary else {}
			if transform is Dictionary:channel=transform.get("texCoord",channel)
			if (channel is int or channel is float) and (channel==0 or channel==1):imported[i].emission_on_uv2=channel==1
			# KHR_materials_specular zero means no dielectric reflection. Godot's
			# importer otherwise keeps its default0.5, adding light to baked surfaces.
			var extensions=definitions[i].get("extensions",{})
			var specular=extensions.get("KHR_materials_specular",{}) if extensions is Dictionary else {}
			if specular is Dictionary and specular.get("specularFactor",1)==0:imported[i].metallic_specular=0
			var extras=definitions[i].get("extras",{})
			if extras is Dictionary and extras.get("has_static_source_lightmap")=="studio_source_lightmaps_1":
				var base: BaseMaterial3D=imported[i].duplicate();base.emission_enabled=false
				imported[i].set_meta("has_baked_lightmap_base",base)
				var color: Color=imported[i].albedo_color;imported[i].albedo_color=Color(0,0,0,color.a)
	SceneIO.stable_opaque_order(state.get_materials())
	var scene := doc.generate_scene(state)
	if scene == null:
		return {"error": "GLB contains no usable scene."}
	scene.set_meta(shapes.META,shapes.capture(data,state,scene))
	var expressions=preload("res://src/expression_presets.gd")
	scene.set_meta(expressions.META,expressions.capture(data,scene.get_meta(shapes.META).rows))
	scene.set_meta("has_secondary_rig",preload("res://src/secondary_rig.gd").from_gltf(data,state,scene))
	var source_bones:={}
	var source_nodes:=state.get_nodes();var source_skeletons:=state.get_skeletons()
	for i in range(source_nodes.size()):
		var item: GLTFNode=source_nodes[i]
		if item.skeleton<0 or item.skeleton>=source_skeletons.size():continue
		var skeleton: Skeleton3D=source_skeletons[item.skeleton].get_godot_skeleton()
		if skeleton.find_bone(item.resource_name)>=0:source_bones[i]=str(scene.get_path_to(skeleton))+"::"+item.resource_name
	scene.set_meta("has_source_bones",source_bones)
	var asset=data.get("asset",{})
	if asset is Dictionary and asset.get("extras",{}) is Dictionary:
		scene.set_meta(preload("res://src/joint_constraints.gd").META,asset.get("extras",{}).get("studio_ik_constraints",{}))
	return {"scene": scene, "warning": "Static environment only; embedded animation is not played. Unsupported material extensions may render differently."}
