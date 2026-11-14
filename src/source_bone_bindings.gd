extends RefCounted
# Read-only identity bridge. Retained native rules remain inactive metadata.
const FORMAT = "studio_source_bone_crosswalk_1"
const PROFILE = "junko_hair_mdl49_fe242_blender51_1"
const NATIVE_SHA = "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
const SOURCEIO = "fe24260b97ac03b899d9b5d4f0fd7b34772f3647"
const BONE_COUNT = 69
const RULE_COUNT = 49
const MAX_GLB = 128 * 1024 * 1024
const FIELDS = ["length", "tip_mass", "yaw_stiffness", "yaw_damping", "pitch_stiffness", "pitch_damping", "along_stiffness", "along_damping", "angle_limit", "min_yaw", "max_yaw", "yaw_friction", "yaw_bounce", "min_pitch", "max_pitch", "pitch_friction", "pitch_bounce", "base_mass", "base_stiffness", "base_damping", "base_min_left", "base_max_left", "base_left_friction", "base_min_up", "base_max_up", "base_up_friction", "base_min_forward", "base_max_forward", "base_forward_friction"]

class BoneBinding extends RefCounted:
	var native_index: int
	var native_parent_index: int
	var gltf_node_index: int
	var has_id: String
	var skeleton: Skeleton3D
	var skeleton_bone_index: int

class Resolution extends RefCounted:
	var status := "none"
	var reason := ""
	var source_sha256 := ""
	var proof_sha256 := ""
	var jiggle_wire_sha256 := ""
	var bindings: Array[BoneBinding] = []
	var by_native: Dictionary = {}
	var by_gltf_node: Dictionary = {}
	var rule_owner_ids: Array[String] = []
	var rule_owner_nodes: Array[int] = []
	var skeleton: Skeleton3D

static func _fail(reason: String) -> Resolution:
	var result := Resolution.new()
	result.status = "unavailable"
	result.reason = reason
	return result

static func _whole(value, low: int, high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == floor(float(value)) and value >= low and value <= high

static func _false(value) -> bool:
	return value is bool and value == false

static func _sha(value) -> bool:
	if not value is String or value.length() != 64: return false
	for ch in value:
		if not ch in "0123456789abcdef": return false
	return true

static func _name(value) -> bool:
	if not value is String or value.is_empty() or value.length() >= 63: return false
	for index in value.length():
		if value.unicode_at(index) < 32 or value.unicode_at(index) > 126: return false
	return true

static func _hash(bytes: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(bytes)
	return context.finish().hex_encode()

static func _catalogue(rows: Array) -> Dictionary:
	if rows.size() != BONE_COUNT: return {"error": "native_catalogue_count"}
	var parts := PackedStringArray()
	var names := {}
	for index in rows.size():
		var row = rows[index]
		if not row is Dictionary or row.size() != 2 or not _name(row.get("name")) or names.has(row.name) or not _whole(row.get("parent"), -1, BONE_COUNT - 1) or int(row.parent) == index:
			return {"error": "native_catalogue_row"}
		names[row.name] = true
		# Existing producer catalogue: exact ASCII JSON keys name,parent plus LF.
		var escaped: String = row.name.replace("\\", "\\\\").replace("\"", "\\\"")
		parts.append("{\"name\":\"" + escaped + "\",\"parent\":" + str(int(row.parent)) + "}")
	for index in rows.size():
		var visited := {}
		var at: int = index
		while at >= 0:
			if visited.has(at): return {"error": "native_parent_cycle"}
			visited[at] = true
			at = int(rows[at].parent)
	return {"sha256": _hash(("[" + ",".join(parts) + "]\n").to_ascii_buffer())}

static func _jiggle(value: Dictionary, catalogue: Array) -> Dictionary:
	if value.get("format") != "studio_source_jiggle_metadata_1" or value.get("status") != "retained_inert" or not _false(value.get("applied")) or value.get("runtime_support") != "not_implemented" or value.get("binding_status") != "unattempted" or not _false(value.get("full_native_rule_layout_verified")) or value.get("native_mdl_sha256") != NATIVE_SHA or not _whole(value.get("native_version"), 49, 49) or value.get("sourceio_revision") != SOURCEIO:
		return {"error": "jiggle_inactive_contract"}
	if not _whole(value.get("native_bone_count"), BONE_COUNT, BONE_COUNT) or not _whole(value.get("declared_jiggle_rule_count"), RULE_COUNT, RULE_COUNT) or value.get("source_scale") != 0.01905 or not value.get("rules") is Array or value.rules.size() != RULE_COUNT:
		return {"error": "jiggle_domain"}
	var sorted_rows: Array = value.rules.duplicate()
	for row in sorted_rows:
		if not row is Dictionary or not _whole(row.get("native_bone_index"), 0, BONE_COUNT - 1): return {"error": "jiggle_owner"}
	sorted_rows.sort_custom(func(a, b): return int(a.native_bone_index) < int(b.native_bone_index))
	var wire: String = "studio_source_jiggle_binding_1\nnative_mdl_sha256=" + NATIVE_SHA + "\nnative_bone_count=69\nrule_count=49\n"
	var owners: Array[int] = []
	for row in sorted_rows:
		var index := int(row.native_bone_index)
		if index in owners or row.get("native_bone_name") != catalogue[index].name or not _whole(row.get("native_parent_index"), -1, BONE_COUNT - 1) or int(row.native_parent_index) != int(catalogue[index].parent): return {"error": "jiggle_owner"}
		if not _false(row.get("applied")) or row.get("binding_status") != "unattempted" or not _whole(row.get("native_bone_flags"), 0, 0xffffffff) or not _whole(row.get("native_procedure_type"), 5, 5) or not _whole(row.get("raw_rule_flags"), 0x31, 0x31) or not _whole(row.get("unknown_rule_flag_bits"), 0, 0) or row.get("known_rule_flags") != ["IS_FLEXIBLE", "HAS_ANGLE_CONSTRAINT", "HAS_LENGTH_CONSTRAINT"]:
			return {"error": "jiggle_rule_contract"}
		var provenance = row.get("binary_provenance")
		var parameters = row.get("parameters")
		if not provenance is Dictionary or not parameters is Dictionary or parameters.size() != FIELDS.size() or not provenance.get("float32_words_uint32") is Array or provenance.float32_words_uint32.size() != FIELDS.size() or provenance.get("prefix_bytes") != 120 or not _sha(provenance.get("prefix_sha256")):
			return {"error": "jiggle_binary_provenance"}
		for key in ["bone_record_offset", "bone_relative_rule_offset", "rule_absolute_offset"]:
			if not _whole(provenance.get(key), 0, 16 * 1024 * 1024): return {"error": "jiggle_binary_offset"}
		if int(provenance.bone_record_offset) + int(provenance.bone_relative_rule_offset) != int(provenance.rule_absolute_offset): return {"error": "jiggle_binary_offset"}
		var prefix := PackedByteArray()
		prefix.resize(120)
		prefix.encode_u32(0, int(row.raw_rule_flags))
		var words := PackedStringArray()
		var floating := PackedByteArray()
		floating.resize(4)
		for field in FIELDS.size():
			var word = provenance.float32_words_uint32[field]
			var number = parameters.get(FIELDS[field])
			if not _whole(word, 0, 0xffffffff) or not (number is int or number is float) or not is_finite(float(number)) or absf(float(number)) > 1000000: return {"error": "jiggle_float_word"}
			floating.encode_float(0, float(number))
			# Godot4.6 JSON writing normalizes -0.0 (parsing preserves it).
			# Only numeric zero may match either zero sign; exact original words
			# still supply both the binary prefix and its authenticated wire.
			var json_zero: bool = float(number) == 0.0 and int(word) in [0, 0x80000000]
			if floating.decode_u32(0) != int(word) and not json_zero: return {"error": "jiggle_float_word"}
			prefix.encode_u32(4 + field * 4, int(word))
			words.append(str(int(word)))
		if _hash(prefix) != provenance.prefix_sha256: return {"error": "jiggle_prefix_sha256"}
		wire += "rule=%d\t%d\t%s\t%d\t5\t49\t%s\n" % [index, int(row.native_parent_index), row.native_bone_name, int(row.native_bone_flags), provenance.prefix_sha256]
		wire += "words=" + "\t".join(words) + "\n"
		owners.append(index)
	return {"sha256": _hash(wire.to_ascii_buffer()), "owners": owners}

static func _crosswalk(value: Dictionary, catalogue: Array) -> Dictionary:
	var allowed := ["format", "profile", "status", "applied", "runtime_binding", "native_solver", "original_source_sha256", "native_mdl_sha256", "glb_sha256", "native_bone_catalogue_sha256", "jiggle_wire_sha256", "proof_sha256", "max_rest_matrix_error", "source_scale", "native_bone_count", "bones", "observed_proof_sha256", "sourceio_revision", "sourceio_source_catalogue_sha256", "exporter_source_catalogue_sha256", "scene_container_sha256", "selected_scene", "native_simulation"]
	for key in value:
		if not key in allowed: return {"error": "crosswalk_unknown_field"}
	if value.get("format") != FORMAT or value.get("profile") != PROFILE or value.get("status") != "retained_inert" or not _false(value.get("applied")) or value.get("runtime_binding") != "unattempted" or value.get("native_solver") != "not_implemented" or not _false(value.get("native_simulation", false)):
		return {"error": "crosswalk_inactive_contract"}
	if value.get("native_mdl_sha256") != NATIVE_SHA or value.get("source_scale") != 0.01905 or not _whole(value.get("native_bone_count"), BONE_COUNT, BONE_COUNT) or not value.get("bones") is Array or value.bones.size() != BONE_COUNT:
		return {"error": "crosswalk_domain"}
	for key in ["original_source_sha256", "native_mdl_sha256", "glb_sha256", "native_bone_catalogue_sha256", "jiggle_wire_sha256", "proof_sha256"]:
		if not _sha(value.get(key)): return {"error": "crosswalk_digest"}
	for key in ["observed_proof_sha256", "sourceio_source_catalogue_sha256", "exporter_source_catalogue_sha256", "scene_container_sha256"]:
		if value.has(key) and not _sha(value[key]): return {"error": "crosswalk_digest"}
	if value.has("sourceio_revision") and value.sourceio_revision != SOURCEIO: return {"error": "crosswalk_profile"}
	var error_value = value.get("max_rest_matrix_error")
	if not (error_value is int or error_value is float) or not is_finite(float(error_value)) or error_value < 0 or error_value > 0.00002: return {"error": "crosswalk_rest_metric"}
	var by_index := {}
	var source_nodes := {}
	for row in value.bones:
		if not row is Dictionary or row.size() != 5 or not _whole(row.get("native_index"), 0, BONE_COUNT - 1) or not _whole(row.get("native_parent_index"), -1, BONE_COUNT - 1) or not _whole(row.get("gltf_node_index"), 0, 99999): return {"error": "crosswalk_row"}
		var index := int(row.native_index)
		if by_index.has(index) or source_nodes.has(int(row.gltf_node_index)): return {"error": "crosswalk_duplicate"}
		if row.get("native_name") != catalogue[index].name or int(row.native_parent_index) != int(catalogue[index].parent): return {"error": "crosswalk_catalogue"}
		if not row.get("skin_memberships") is Array or row.skin_memberships.is_empty() or row.skin_memberships.size() > 128: return {"error": "crosswalk_skin_membership"}
		var memberships: Array = []
		var seen := {}
		for membership in row.skin_memberships:
			if not membership is Dictionary or membership.size() != 2 or not _whole(membership.get("skin_index"), 0, 127) or not _whole(membership.get("joint_slot"), 0, BONE_COUNT - 1): return {"error": "crosswalk_skin_membership"}
			var key := "%d:%d" % [int(membership.skin_index), int(membership.joint_slot)]
			if seen.has(key): return {"error": "crosswalk_skin_duplicate"}
			seen[key] = true
			memberships.append({"skin_index": int(membership.skin_index), "joint_slot": int(membership.joint_slot)})
		memberships.sort_custom(func(a, b): return a.skin_index < b.skin_index or a.skin_index == b.skin_index and a.joint_slot < b.joint_slot)
		by_index[index] = {"native_index": index, "native_name": row.native_name, "native_parent_index": int(row.native_parent_index), "gltf_node_index": int(row.gltf_node_index), "skin_memberships": memberships}
		source_nodes[int(row.gltf_node_index)] = true
	var wire: String = "studio_source_bone_crosswalk_binding_1\noriginal_source_sha256=" + value.original_source_sha256 + "\nnative_mdl_sha256=" + value.native_mdl_sha256 + "\nglb_sha256=" + value.glb_sha256 + "\nnative_bone_catalogue_sha256=" + value.native_bone_catalogue_sha256 + "\njiggle_wire_sha256=" + value.jiggle_wire_sha256 + "\nnative_bone_count=69\n"
	var rows: Array = []
	for index in BONE_COUNT:
		var row: Dictionary = by_index[index]
		rows.append(row)
		wire += "bone=%d\t%d\t%d\t%s\t%d\n" % [index, row.native_parent_index, row.gltf_node_index, row.native_name, row.skin_memberships.size()]
		for membership in row.skin_memberships:
			wire += "skin=%d\t%d\n" % [membership.skin_index, membership.joint_slot]
	if _hash(wire.to_ascii_buffer()) != value.proof_sha256: return {"error": "crosswalk_proof_sha256"}
	return {"rows": rows, "source_nodes": source_nodes}

static func _document(path: String, expected_sha: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null: return {"error": "source_unavailable"}
	var size := file.get_length()
	if size < 28 or size > MAX_GLB:
		file.close()
		return {"error": "source_glb_budget"}
	var bytes := file.get_buffer(size)
	file.close()
	if bytes.size() != size or _hash(bytes) != expected_sha: return {"error": "source_sha256"}
	if bytes.decode_u32(0) != 0x46546c67 or bytes.decode_u32(4) != 2 or bytes.decode_u32(8) != size: return {"error": "source_glb_header"}
	var offset := 12
	var chunks: Array = []
	while offset < size:
		if chunks.size() >= 2 or offset + 8 > size: return {"error": "source_glb_chunks"}
		var count := int(bytes.decode_u32(offset))
		var kind := int(bytes.decode_u32(offset + 4))
		if count % 4 != 0 or offset + 8 + count > size: return {"error": "source_glb_chunks"}
		chunks.append({"kind": kind, "start": offset + 8, "count": count})
		offset += 8 + count
	if chunks.size() != 2 or chunks[0].kind != 0x4e4f534a or chunks[1].kind != 0x004e4942 or chunks[0].count > 16 * 1024 * 1024: return {"error": "source_glb_chunks"}
	var parser := JSON.new()
	if parser.parse(bytes.slice(chunks[0].start, chunks[0].start + chunks[0].count).get_string_from_utf8()) != OK or not parser.data is Dictionary: return {"error": "source_glb_json"}
	return {"document": parser.data}

static func _graph(doc: Dictionary, rows: Array, source_nodes: Dictionary) -> Dictionary:
	var nodes = doc.get("nodes")
	var scenes = doc.get("scenes")
	var skins = doc.get("skins")
	var meshes = doc.get("meshes")
	var accessors = doc.get("accessors")
	if not nodes is Array or nodes.is_empty() or nodes.size() > 100000 or not scenes is Array or scenes.is_empty() or scenes.size() > 128 or not _whole(doc.get("scene"), 0, scenes.size() - 1) or not skins is Array or skins.is_empty() or skins.size() > 128 or not meshes is Array or meshes.is_empty() or meshes.size() > 100000 or not accessors is Array or accessors.size() > 100000: return {"error": "source_graph_domain"}
	var parents := {}
	for index in nodes.size():
		var node = nodes[index]
		if not node is Dictionary or not node.get("children", []) is Array: return {"error": "source_graph_node"}
		for child in node.get("children", []):
			if not _whole(child, 0, nodes.size() - 1) or int(child) == index or parents.has(int(child)): return {"error": "source_graph_parent"}
			parents[int(child)] = index
	var queue: Array[int] = []
	for index in nodes.size():
		if not parents.has(index): queue.append(index)
	var cursor := 0
	while cursor < queue.size():
		for child in nodes[queue[cursor]].get("children", []): queue.append(int(child))
		cursor += 1
	if queue.size() != nodes.size(): return {"error": "source_graph_cycle"}
	for scene in scenes:
		if not scene is Dictionary or not scene.get("nodes", []) is Array: return {"error": "source_graph_scene"}
		var seen := {}
		for index in scene.get("nodes", []):
			if not _whole(index, 0, nodes.size() - 1) or parents.has(int(index)) or seen.has(int(index)): return {"error": "source_graph_scene_root"}
			seen[int(index)] = true
	var active := {}
	var pending: Array = scenes[int(doc.scene)].get("nodes", []).duplicate()
	while not pending.is_empty():
		var index := int(pending.pop_back())
		active[index] = true
		pending.append_array(nodes[index].get("children", []))
	for row in rows:
		var index: int = row.gltf_node_index
		if index >= nodes.size() or not active.has(index) or nodes[index].get("name") != row.native_name: return {"error": "source_joint_identity"}
		var at: int = parents.get(index, -1)
		while at >= 0 and not source_nodes.has(at): at = parents.get(at, -1)
		var expected: int = -1 if row.native_parent_index < 0 else rows[row.native_parent_index].gltf_node_index
		if at != expected: return {"error": "source_native_parent"}
	for skin_index in skins.size():
		var skin = skins[skin_index]
		if not skin is Dictionary or not skin.get("joints") is Array or skin.joints.size() != BONE_COUNT or not _whole(skin.get("inverseBindMatrices"), 0, accessors.size() - 1): return {"error": "source_skin_domain"}
		var inverse = accessors[int(skin.inverseBindMatrices)]
		if not inverse is Dictionary or inverse.get("type") != "MAT4" or inverse.get("componentType") != 5126 or not _whole(inverse.get("count"), BONE_COUNT, BONE_COUNT): return {"error": "source_skin_inverse_bind"}
		var joints := {}
		for index in skin.joints:
			if not _whole(index, 0, nodes.size() - 1) or not source_nodes.has(int(index)) or joints.has(int(index)): return {"error": "source_skin_joint"}
			joints[int(index)] = true
		var rendered := false
		for index in active:
			var node: Dictionary = nodes[index]
			if not node.has("skin"): continue
			if not _whole(node.skin, 0, skins.size() - 1) or not _whole(node.get("mesh"), 0, meshes.size() - 1): return {"error": "source_skinned_mesh"}
			if int(node.skin) != skin_index: continue
			var mesh = meshes[int(node.mesh)]
			if not mesh is Dictionary or not mesh.get("primitives") is Array or mesh.primitives.is_empty(): return {"error": "source_skinned_mesh"}
			for primitive in mesh.primitives:
				if not primitive is Dictionary or not primitive.get("attributes") is Dictionary: return {"error": "source_skin_attributes"}
				for key in ["POSITION", "JOINTS_0", "WEIGHTS_0"]:
					if not _whole(primitive.attributes.get(key), 0, accessors.size() - 1): return {"error": "source_skin_attributes"}
				rendered = true
		if not rendered: return {"error": "source_skin_unreachable_mesh"}
	for row in rows:
		if row.skin_memberships.size() != skins.size(): return {"error": "source_skin_membership"}
		for membership in row.skin_memberships:
			if membership.skin_index >= skins.size() or skins[membership.skin_index].joints[membership.joint_slot] != row.gltf_node_index: return {"error": "source_skin_membership"}
	return {"scene": int(doc.scene)}

static func resolve(actor: RefCounted) -> Resolution:
	if actor == null: return _fail("actor_unavailable")
	var root: Node3D = actor.root
	if not is_instance_valid(root) or not actor.data is Dictionary or not actor.bones is Dictionary: return _fail("actor_unavailable")
	var metadata = actor.data.get("metadata", {})
	if not metadata is Dictionary: return _fail("report_metadata")
	var report = metadata.get("native_parameters", {})
	if not report is Dictionary: return _fail("report_metadata")
	var native = report.get("native_parameters", {})
	if not native is Dictionary: return _fail("report_metadata")
	if not native.has("source_export_crosswalk"):
		var missing := Resolution.new()
		missing.reason = "no_crosswalk"
		return missing
	var crosswalk = native.source_export_crosswalk
	if not crosswalk is Dictionary: return _fail("crosswalk_metadata")
	if crosswalk.get("status") != "retained_inert" or crosswalk.get("format") != FORMAT:
		var unsupported := Resolution.new()
		unsupported.reason = "unsupported_crosswalk"
		return unsupported
	if not native.get("bones") is Array or not native.get("source_jiggle") is Dictionary: return _fail("native_metadata")
	var catalogue: Array = native.bones
	var catalogue_result := _catalogue(catalogue)
	if catalogue_result.has("error"): return _fail(catalogue_result.error)
	var normalized := _crosswalk(crosswalk, catalogue)
	if normalized.has("error"): return _fail(normalized.error)
	var jiggle: Dictionary = native.source_jiggle
	if report.get("source_sha256") != crosswalk.original_source_sha256 or jiggle.get("original_source_sha256") != crosswalk.original_source_sha256 or jiggle.get("native_bone_catalogue_sha256") != catalogue_result.sha256 or crosswalk.native_bone_catalogue_sha256 != catalogue_result.sha256 or report.get("scale") != 0.01905: return _fail("native_identity")
	var rules := _jiggle(jiggle, catalogue)
	if rules.has("error"): return _fail(rules.error)
	if rules.sha256 != crosswalk.jiggle_wire_sha256: return _fail("jiggle_wire_sha256")
	if not _sha(actor.data.get("sha256")) or actor.data.sha256 != crosswalk.glb_sha256 or not actor.data.get("source") is String: return _fail("actor_source_identity")
	var source := _document(actor.data.source, actor.data.sha256)
	if source.has("error"): return _fail(source.error)
	var graph := _graph(source.document, normalized.rows, normalized.source_nodes)
	if graph.has("error"): return _fail(graph.error)
	if crosswalk.has("selected_scene") and (not _whole(crosswalk.selected_scene, 0, 127) or int(crosswalk.selected_scene) != graph.scene): return _fail("selected_scene")
	var source_map = root.get_meta("has_source_bones", {})
	if not source_map is Dictionary or source_map.size() != BONE_COUNT or actor.bones.size() != BONE_COUNT: return _fail("importer_map_count")
	for key in source_map:
		if not key is int or not normalized.source_nodes.has(key): return _fail("importer_map_domain")
	var result := Resolution.new()
	var ids := {}
	var physical := {}
	for row in normalized.rows:
		var node_index: int = row.gltf_node_index
		if not source_map.has(node_index) or not source_map[node_index] is String: return _fail("importer_node_missing")
		var id: String = source_map[node_index]
		if id.is_empty() or id.length() > 512 or id == "@root" or ids.has(id) or not actor.bones.has(id): return _fail("importer_id_duplicate_or_missing")
		var info = actor.bones[id]
		if not info is Dictionary or not info.get("skeleton") is Skeleton3D or not is_instance_valid(info.skeleton): return _fail("live_skeleton")
		var skeleton: Skeleton3D = info.skeleton
		if skeleton != root and not root.is_ancestor_of(skeleton): return _fail("foreign_skeleton")
		if result.skeleton != null and result.skeleton != skeleton: return _fail("foreign_skeleton")
		if skeleton.get_bone_count() != BONE_COUNT or not _whole(info.get("index"), 0, BONE_COUNT - 1): return _fail("live_bone_index")
		var bone_index := int(info.index)
		var path := str(root.get_path_to(skeleton))
		var name := str(skeleton.get_bone_name(bone_index))
		if info.get("name") != name or info.get("path") != path or id != path + "::" + name or physical.has(bone_index): return _fail("live_bone_identity")
		var binding := BoneBinding.new()
		binding.native_index = row.native_index
		binding.native_parent_index = row.native_parent_index
		binding.gltf_node_index = node_index
		binding.has_id = id
		binding.skeleton = skeleton
		binding.skeleton_bone_index = bone_index
		result.bindings.append(binding)
		result.by_native[binding.native_index] = id
		result.by_gltf_node[binding.gltf_node_index] = binding
		result.skeleton = skeleton
		ids[id] = true
		physical[bone_index] = true
	for binding in result.bindings:
		var parent: int = binding.native_parent_index
		var expected_id: String = "@root" if parent < 0 else result.by_native[parent]
		var expected_index: int = -1 if parent < 0 else result.bindings[parent].skeleton_bone_index
		if not actor.has_method("parent_id") or actor.parent_id(binding.has_id) != expected_id or binding.skeleton.get_bone_parent(binding.skeleton_bone_index) != expected_index: return _fail("live_parent")
	for index in rules.owners:
		result.rule_owner_ids.append(result.by_native[index])
		result.rule_owner_nodes.append(result.bindings[index].gltf_node_index)
	result.source_sha256 = actor.data.sha256
	result.proof_sha256 = crosswalk.proof_sha256
	result.jiggle_wire_sha256 = crosswalk.jiggle_wire_sha256
	result.status = "bound_inactive"
	return result

static func current(actor: RefCounted, previous: Resolution) -> bool:
	if previous == null or previous.status != "bound_inactive" or previous.bindings.size() != BONE_COUNT or not is_instance_valid(previous.skeleton): return false
	var fresh := resolve(actor)
	if fresh.status != "bound_inactive" or fresh.source_sha256 != previous.source_sha256 or fresh.proof_sha256 != previous.proof_sha256 or fresh.jiggle_wire_sha256 != previous.jiggle_wire_sha256 or fresh.skeleton != previous.skeleton or fresh.by_native != previous.by_native or fresh.rule_owner_ids != previous.rule_owner_ids or fresh.rule_owner_nodes != previous.rule_owner_nodes: return false
	for index in fresh.bindings.size():
		if previous.bindings[index] == null or fresh.bindings[index].skeleton_bone_index != previous.bindings[index].skeleton_bone_index: return false
	return true
