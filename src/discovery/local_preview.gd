extends RefCounted
## Explicit, bounded geometry preview. No importer process, network or source writes.
const MAX_BYTES := 8 * 1024 * 1024
const StudioTheme = preload("res://src/studio_theme.gd")

static func integer(value, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value >= 0 and value <= maximum and value == int(value)

static func prepare(path: String) -> Dictionary:
	if path.get_extension().to_lower() != "glb": return {"error":"Geometry preview supports self-contained GLB files only. Use the normal import workflow for other formats."}
	var file := FileAccess.open(path, FileAccess.READ)
	if not file or file.get_length() > MAX_BYTES: return {"error":"Cannot read this preview file, or it exceeds the 8 MiB preview limit."}
	var bytes := file.get_buffer(file.get_length()); file.close()
	if bytes.size() < 28 or bytes.decode_u32(0) != 0x46546c67 or bytes.decode_u32(4) != 2 or bytes.decode_u32(8) != bytes.size() or bytes.decode_u32(16) != 0x4e4f534a:
		return {"error":"Invalid GLB header. No preview was loaded."}
	var count := bytes.decode_u32(12)
	if count > bytes.size() - 28 or count % 4 != 0: return {"error":"Invalid GLB JSON length."}
	var parser := JSON.new()
	if parser.parse(bytes.slice(20, 20 + count).get_string_from_utf8()) != OK or not parser.data is Dictionary: return {"error":"Malformed GLB JSON."}
	var raw: Dictionary = parser.data
	var binary_at := 20 + count
	if binary_at + 8 > bytes.size() or bytes.decode_u32(binary_at + 4) != 0x004e4942 or bytes.decode_u32(binary_at) != bytes.size() - binary_at - 8: return {"error":"Preview requires one embedded GLB binary buffer."}
	if not raw.get("buffers") is Array or raw.buffers.size() != 1 or not raw.buffers[0] is Dictionary or raw.buffers[0].has("uri"): return {"error":"External or encoded GLB buffers are not used by geometry preview."}
	var binary_size := bytes.size() - binary_at - 8
	if not integer(raw.buffers[0].get("byteLength"), binary_size): return {"error":"Invalid preview buffer length."}
	if not raw.get("extensionsRequired", []) is Array or not raw.get("extensionsRequired", []).is_empty(): return {"error":"This GLB requires extensions. Use the ordinary import workflow; geometry preview does not convert them."}
	# A shallow, explicit glTF subset removes images, material graphs, animation,
	# cameras, extras and extensions before Godot sees the preview bytes.
	var clean := {"asset":{"version":"2.0"}}
	var fields := {"scenes":["nodes"], "nodes":["name","mesh","skin","children","matrix","translation","rotation","scale"], "meshes":["name","primitives"], "accessors":["bufferView","byteOffset","componentType","normalized","count","type","max","min","sparse"], "bufferViews":["buffer","byteOffset","byteLength","byteStride","target"], "buffers":["byteLength"], "skins":["inverseBindMatrices","skeleton","joints"]}
	var entries := 0
	var vertices := 0
	var primitives := 0
	for group in fields:
		var items = raw.get(group, [])
		if not items is Array or items.size() > 2000: return {"error":"Preview scene structure exceeds its limits."}
		clean[group] = []
		for item in items:
			entries += 1
			if not item is Dictionary or entries > 8000: return {"error":"Invalid or oversized preview structure."}
			var kept := {}
			for key in fields[group]:
				if item.has(key): kept[key] = item[key]
			if group == "accessors":
				var size = item.get("count", -1)
				if not (size is int or size is float) or size < 0 or size > 250000: return {"error":"Invalid or excessive preview geometry."}
				vertices += int(size)
				if vertices > 250000: return {"error":"Preview exceeds 250,000 accessor elements. Use ordinary import for larger files."}
			if group == "bufferViews":
				if item.get("buffer") != 0 or not integer(item.get("byteOffset", 0), binary_size) or not integer(item.get("byteLength"), binary_size): return {"error":"Invalid preview buffer view."}
				if item.get("byteOffset", 0) + item.byteLength > binary_size: return {"error":"Preview buffer view exceeds embedded data."}
			if group == "bufferViews" and item.has("extensions"): return {"error":"Compressed buffers are unsupported in geometry preview."}
			if group == "skins" and (not item.get("joints") is Array or item.joints.size() > 256): return {"error":"Preview supports at most 256 joints per skin."}
			if group == "meshes":
				if not item.get("primitives") is Array: return {"error":"Invalid preview primitives."}
				kept.primitives = []
				for primitive in item.primitives:
					primitives += 1
					if not primitive is Dictionary or primitive.has("extensions") or primitives > 512: return {"error":"Unsupported or excessive preview primitives."}
					var part := {}
					for key in ["attributes","indices","mode"]:
						if primitive.has(key): part[key] = primitive[key]
					kept.primitives.append(part)
			clean[group].append(kept)
	# Reject cycles/multiple parents before handing a scene graph to the importer.
	var parents: Array = []; parents.resize(clean.nodes.size()); parents.fill(-1)
	for index in clean.nodes.size():
		var children = clean.nodes[index].get("children", [])
		if not children is Array or children.size() > 2000: return {"error":"Invalid preview child list."}
		for child in children:
			if not integer(child, clean.nodes.size() - 1) or parents[int(child)] != -1: return {"error":"Invalid or repeated preview node parent."}
			parents[int(child)] = index
	for index in clean.nodes.size():
		var parent: int = index; var depth := 0
		while parent != -1:
			depth += 1
			if depth > 64: return {"error":"Preview node hierarchy is cyclic or deeper than 64 levels."}
			parent = parents[parent]
	var draws := 0; var instanced_vertices := 0
	for node in clean.nodes:
		if not node.has("mesh"): continue
		var index = node.mesh
		if not (index is int or index is float) or index != int(index) or index < 0 or index >= clean.meshes.size(): return {"error":"Invalid preview mesh reference."}
		for part in clean.meshes[int(index)].primitives:
			draws += 1
			if not part.get("attributes") is Dictionary: return {"error":"Invalid preview vertex attributes."}
			var position = part.attributes.get("POSITION", -1)
			if not (position is int or position is float) or position != int(position) or position < 0 or position >= clean.accessors.size(): return {"error":"Invalid preview position accessor."}
			instanced_vertices += int(clean.accessors[int(position)].count)
			if draws > 512 or instanced_vertices > 250000: return {"error":"Preview instance geometry exceeds its limits. Use ordinary import."}
	if raw.has("scene"): clean.scene = raw.scene
	var json := JSON.stringify(clean).to_utf8_buffer()
	while json.size() % 4: json.append(32)
	var binary := bytes.slice(binary_at)
	var out := PackedByteArray(); out.resize(20)
	out.encode_u32(0, 0x46546c67); out.encode_u32(4, 2); out.encode_u32(8, 20 + json.size() + binary.size()); out.encode_u32(12, json.size()); out.encode_u32(16, 0x4e4f534a)
	out.append_array(json); out.append_array(binary)
	return {"bytes":out}

static func open(owner: Node, path: String) -> Dictionary:
	var prepared := prepare(path)
	if prepared.has("error"): return prepared
	var document := GLTFDocument.new(); var state := GLTFState.new()
	if document.append_from_buffer(prepared.bytes, "", state) != OK: return {"error":"This GLB geometry could not be previewed. The source was not changed."}
	var scene := document.generate_scene(state)
	if not scene: return {"error":"This GLB has no preview scene."}
	scene.process_mode = Node.PROCESS_MODE_DISABLED
	var bounds := AABB(); var found := false
	var stack: Array = [{"node":scene, "transform":Transform3D.IDENTITY}]
	while not stack.is_empty():
		var entry: Dictionary = stack.pop_back(); var node: Node = entry.node
		var transform: Transform3D = entry.transform * node.transform if node is Node3D else entry.transform
		if node is MeshInstance3D and node.mesh:
			var box: AABB = transform * node.mesh.get_aabb()
			bounds = bounds.merge(box) if found else box; found = true
		for child in node.get_children(): stack.append({"node":child, "transform":transform})
	if not found or not bounds.position.is_finite() or not bounds.size.is_finite() or not is_finite(bounds.size.length()) or bounds.size.length() > 1000000: scene.free(); return {"error":"No finite, supported mesh bounds were found for this preview."}
	var window := Window.new(); window.title = "Geometry preview — " + path.get_file(); window.size = Vector2i(720, 560); window.min_size = Vector2i(480, 400); window.theme = StudioTheme.make_theme(); owner.add_child(window)
	var background := Panel.new(); background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee")); window.add_child(background)
	var box := VBoxContainer.new(); box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); window.add_child(box)
	var note := Label.new(); note.text = "Local GLB geometry only • materials and animation are omitted • project unchanged"; note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; box.add_child(note)
	var container := SubViewportContainer.new(); container.stretch = true; container.size_flags_vertical = Control.SIZE_EXPAND_FILL; box.add_child(container)
	var viewport := SubViewport.new(); viewport.size = Vector2i(640, 420); viewport.own_world_3d = true; container.add_child(viewport)
	viewport.add_child(scene)
	var light := DirectionalLight3D.new(); light.rotation_degrees = Vector3(-40, -30, 0); viewport.add_child(light)
	var environment := WorldEnvironment.new(); environment.environment = Environment.new(); environment.environment.background_mode = Environment.BG_COLOR; environment.environment.background_color = Color("171a21"); environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; environment.environment.ambient_light_color = Color.WHITE; environment.environment.ambient_light_energy = 0.7; viewport.add_child(environment)
	var camera := Camera3D.new(); camera.current = true; viewport.add_child(camera)
	var center := bounds.get_center(); var radius := maxf(bounds.size.length() / 2, 0.05)
	var orbit := HSlider.new(); orbit.min_value = -180; orbit.max_value = 180; orbit.value = 30; orbit.tooltip_text = "Turn around the geometry"; box.add_child(orbit)
	var update := func(angle):
		camera.position = center + Vector3(sin(deg_to_rad(angle)) * radius * 3, radius * 1.2, cos(deg_to_rad(angle)) * radius * 3)
		camera.near = maxf(radius / 1000, 0.001); camera.far = maxf(radius * 20, 10); camera.look_at(center)
	orbit.value_changed.connect(update); update.call(orbit.value)
	window.set_meta("preview_viewport", viewport); window.set_meta("preview_camera", camera); window.set_meta("preview_orbit", orbit)
	window.close_requested.connect(window.queue_free); window.popup_centered()
	return {"window":window}
