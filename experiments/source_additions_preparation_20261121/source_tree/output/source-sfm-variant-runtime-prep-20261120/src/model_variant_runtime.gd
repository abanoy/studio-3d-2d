extends RefCounted
# Per-actor reference binding and synchronous static variant transaction. Shared
# Mesh/Material resources are never modified; only owned MeshInstance overrides
# and self visibility change. No timeline, native parser, name guessing or IO.
const Schema = preload("res://src/model_variants.gd")
const Opacity = preload("res://src/model_opacity.gd")
const META := "has_model_variant_runtime_1"
const NODE_META := "has_shape_source_node"
var actor: WeakRef
var root: Node3D
var declared: Dictionary = {}
var inventory: Dictionary = {}
var material_refs: Array = []
var nodes: Dictionary = {}
var mesh_refs: Dictionary = {}
var base_materials: Dictionary = {}
var expected_overrides: Dictionary = {}
var expected_visibility: Dictionary = {}
var current: Dictionary = {}
var declaration_bytes := PackedByteArray()
var failed := false
var surface_counts: Dictionary = {}
var retained_material_ids: Array = []
var retained_node_ids: Dictionary = {}
var retained_mesh_ids: Dictionary = {}
var retained_parents: Dictionary = {}
var retained_skins: Dictionary = {}
var retained_skeleton_paths: Dictionary = {}
var inventory_bytes := PackedByteArray()
var manifest_bytes := PackedByteArray()

static func fail(message: String) -> Dictionary:
	return {"error":message}
static func capture(document: Dictionary, state: GLTFState, scene: Node3D, asset_sha: String, manifest: Dictionary) -> Dictionary:
	# Called before another actor can be parented to this scene. SourceShape.mark
	# has already transferred exact source-node metadata onto generated nodes.
	var source_nodes: Array = state.get_nodes()
	var source_meshes: Array = state.get_meshes()
	var materials: Array = state.get_materials()
	var raw_nodes: Variant = document.get("nodes",[])
	var raw_meshes: Variant = document.get("meshes",[])
	if not raw_nodes is Array or raw_nodes.size() != source_nodes.size() or not raw_meshes is Array or materials.is_empty() or materials.size() > 256: return fail("Invalid retained variant GLB tables.")
	for material in materials:
		if not material is Material: return fail("Retained variant material is unavailable.")
	var scenes: Variant = document.get("scenes",[])
	var scene_id: Variant = document.get("scene",0)
	if not scenes is Array or not Schema.whole(scene_id,0,scenes.size()-1) or not scenes[int(scene_id)] is Dictionary or not scenes[int(scene_id)].get("nodes") is Array: return fail("Invalid retained variant scene.")
	var active: Dictionary = {}
	var parents: Dictionary = {}
	var pending: Array = []
	for id in scenes[int(scene_id)].nodes: pending.append({"id":id,"parent":null})
	while not pending.is_empty():
		var item: Dictionary = pending.pop_back()
		if not Schema.whole(item.id,0,raw_nodes.size()-1): return fail("Invalid retained variant scene node.")
		var id: int = int(item.id)
		if active.has(id): return fail("Retained variant scene repeats a node.")
		active[id] = true; parents[id] = item.parent
		if not raw_nodes[id] is Dictionary or not raw_nodes[id].get("children",[]) is Array: return fail("Invalid retained variant node children.")
		for child in raw_nodes[id].get("children",[]): pending.append({"id":child,"parent":id})
	var generated: Array = scene.find_children("*","MeshInstance3D",true,false)
	if scene is MeshInstance3D: generated.push_front(scene)
	var bindings: Dictionary = {}
	var actual_rows: Array = []
	var claimed: Dictionary = {}
	for id in active:
		var source: GLTFNode = source_nodes[id]
		if source.mesh < 0: continue
		if source.mesh >= source_meshes.size() or source.mesh >= raw_meshes.size(): return fail("Invalid retained variant mesh index.")
		var expected: ArrayMesh = source_meshes[source.mesh].mesh.get_mesh()
		var matches: Array = []
		for candidate in generated:
			if candidate.mesh == expected and candidate.get_meta(NODE_META,-1) == id: matches.append(candidate)
		if matches.size() != 1 or claimed.has(matches[0]): return fail("Cannot bind a retained variant to its exact imported mesh.")
		var node: MeshInstance3D = matches[0]
		if node == scene: return fail("Retained variants require an independent actor root.")
		if node.material_override != null: return fail("Retained variants require per-surface materials.")
		claimed[node] = true; bindings[id] = node
		var primitives: Variant = raw_meshes[source.mesh].get("primitives",[])
		if not primitives is Array or primitives.size() != node.mesh.get_surface_count() or primitives.is_empty(): return fail("Retained variant primitive order changed during import.")
		var defaults: Array = []
		for surface in range(primitives.size()):
			var primitive: Variant = primitives[surface]
			if not primitive is Dictionary or not Schema.whole(primitive.get("material"),0,materials.size()-1): return fail("Retained variant surface material is missing.")
			var material_id: int = int(primitive.material)
			if node.mesh.surface_get_material(surface) != materials[material_id] or node.get_surface_override_material(surface) != null: return fail("Retained variant imported material reference changed.")
			defaults.append(material_id)
		var parent: Variant = parents[id]
		while parent != null and not bindings.has(int(parent)) and source_nodes[int(parent)].mesh < 0: parent = parents[int(parent)]
		actual_rows.append({"node":id,"parent_mesh":parent,"surface_materials":defaults})
	if claimed.size() != generated.size(): return fail("Retained variant mesh coverage is incomplete.")
	actual_rows.sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return a.node < b.node)
	var actual: Dictionary = {"format":Schema.INVENTORY,"asset_sha256":asset_sha,"material_count":materials.size(),"mesh_nodes":actual_rows}
	var checked: Dictionary = Schema.canonical(manifest,actual)
	if checked.has("error"): return checked
	return {"descriptor":{"root":scene,"manifest":checked.manifest,"inventory":actual,"materials":materials.duplicate(),"nodes":bindings}}

static func attach(owner_actor: RefCounted) -> Dictionary:
	var record_error: String = Schema.record_error(owner_actor.data)
	if not record_error.is_empty(): return fail(record_error)
	var manifest: Dictionary = Schema.manifest(owner_actor.data)
	if manifest.is_empty(): return {"runtime":null}
	var descriptor: Variant = owner_actor.root.get_meta(META,{})
	if not descriptor is Dictionary or descriptor.get("root") != owner_actor.root or descriptor.get("manifest") != Schema.canonical(manifest).get("manifest",{}): return fail("Model appearance choices are not bound to the loaded GLB.")
	var result: RefCounted = new()
	result.actor = weakref(owner_actor); result.root = owner_actor.root
	result.declared = descriptor.manifest.duplicate(true); result.inventory = descriptor.inventory.duplicate(true)
	result.declaration_bytes = var_to_bytes(manifest)
	result.material_refs = descriptor.materials.duplicate(); result.nodes = descriptor.nodes.duplicate()
	result.inventory_bytes = var_to_bytes(result.inventory); result.manifest_bytes = var_to_bytes(result.declared)
	for material in result.material_refs: result.retained_material_ids.append(material.get_instance_id())
	for id in result.nodes:
		var node: MeshInstance3D = result.nodes[id]
		result.mesh_refs[id] = node.mesh
		result.surface_counts[id] = node.mesh.get_surface_count()
		result.retained_node_ids[id] = node.get_instance_id(); result.retained_mesh_ids[id] = node.mesh.get_instance_id()
		result.retained_parents[id] = node.get_parent(); result.retained_skins[id] = node.skin; result.retained_skeleton_paths[id] = node.skeleton
		result.expected_visibility[id] = node.visible
		for surface in range(node.mesh.get_surface_count()):
			var key: String = str(id)+":"+str(surface)
			result.base_materials[key] = node.mesh.surface_get_material(surface)
			result.expected_overrides[key] = node.get_surface_override_material(surface)
	var error: String = result.sync_record(owner_actor.data,null)
	if not error.is_empty(): return fail(error)
	for id in result.nodes: result.nodes[id].set_meta("has_variant_runtime_owner",weakref(result))
	return {"runtime":result}

static func hidden_for_bounds(mesh: MeshInstance3D) -> bool:
	var owner: Variant = mesh.get_meta("has_variant_runtime_owner",{})
	if not owner is WeakRef: return false
	var runtime: RefCounted = owner.get_ref()
	if runtime == null or runtime.get_script() != load("res://src/model_variant_runtime.gd"): return false
	var id: Variant = mesh.get_meta(NODE_META,-1)
	return runtime.nodes.get(id) == mesh and runtime.expected_visibility.get(id,true) == false and not mesh.visible

func _opacity_error(opacity: RefCounted) -> String:
	if opacity == null: return ""
	if opacity.get_script() != Opacity or opacity.originals.size() != opacity.copies.size(): return "The model appearance compositor changed."
	return ""
func _override_error(node: MeshInstance3D, surface: int, expected: Material, opacity: RefCounted) -> String:
	if opacity != null:
		var found: int = -1
		for index in range(opacity.originals.size()):
			var row: Dictionary = opacity.originals[index]
			if row.mesh == node and row.surface == surface:
				if found >= 0: return "The model appearance override is ambiguous."
				found = index
		if found >= 0:
			if opacity.originals[found].material != expected or node.get_surface_override_material(surface) != opacity.copies[found].material: return "A temporary model material changed."
			return ""
	return "" if node.get_surface_override_material(surface) == expected else "A model material override changed."
func check_record(value: Dictionary, opacity: RefCounted = null) -> String:
	var owner: RefCounted = actor.get_ref() if actor != null else null
	if failed or not is_instance_valid(root) or owner == null or owner.root != root: return "The model appearance binding is unavailable."
	if var_to_bytes(inventory) != inventory_bytes or var_to_bytes(declared) != manifest_bytes: return "The retained appearance declaration changed."
	var error: String = Schema.record_error(value)
	if not error.is_empty(): return error
	if value.get("sha256") != declared.asset_sha256 or var_to_bytes(Schema.manifest(value)) != declaration_bytes: return "An edit cannot replace the model appearance declaration."
	error = _opacity_error(opacity)
	if not error.is_empty(): return error
	if material_refs.size() != retained_material_ids.size() or nodes.keys() != retained_node_ids.keys() or mesh_refs.keys() != retained_mesh_ids.keys(): return "The model appearance reference inventory changed."
	for index in range(material_refs.size()):
		var material: Material = material_refs[index]
		if not is_instance_valid(material) or material.get_instance_id() != retained_material_ids[index]: return "A model appearance material was released or replaced."
	for id in nodes:
		var raw_node: Variant = nodes[id]
		if not is_instance_valid(raw_node) or not raw_node is MeshInstance3D: return "A model appearance mesh was released."
		var node: MeshInstance3D = raw_node
		if not is_instance_valid(node) or not root.is_ancestor_of(node) and node != root or node.get_instance_id() != retained_node_ids[id] or node.mesh != mesh_refs[id] or node.mesh.get_instance_id() != retained_mesh_ids[id] or node.get_meta(NODE_META,-1) != id or node.material_override != null or node.get_parent() != retained_parents[id] or node.skin != retained_skins[id] or node.skeleton != retained_skeleton_paths[id]: return "A model appearance mesh binding changed."
		if node.mesh.get_surface_count() != surface_counts[id]: return "A model appearance surface count changed."
		if node.visible != expected_visibility[id]: return "A model part changed outside its appearance selection."
		for surface in range(node.mesh.get_surface_count()):
			var key: String = str(id)+":"+str(surface)
			if node.mesh.surface_get_material(surface) != base_materials[key]: return "A shared model material was replaced."
			error = _override_error(node,surface,expected_overrides[key],opacity)
			if not error.is_empty(): return error
	return ""
func prepare(value: Dictionary, opacity: RefCounted = null) -> Dictionary:
	var error: String = check_record(value,opacity)
	if not error.is_empty(): return fail(error)
	var chosen: Variant = value.get(Schema.FIELD,Schema.defaults(declared))
	return Schema.plan(declared,chosen)
func sync_record(value: Dictionary, opacity: RefCounted = null) -> String:
	var prepared: Dictionary = prepare(value,opacity)
	if prepared.has("error"): return prepared.error
	if current == prepared.selection: return ""
	# The retained-reference writes are synchronous with no await or callbacks.
	# Opacity may rebuild its own temporary copies around them; source Mesh and
	# Material resources remain untouched. Refuse the full plan before first write.
	var error: String = check_record(value,opacity)
	if not error.is_empty(): return error
	var token: Dictionary = {}
	if opacity != null:
		token = {"alpha":opacity.last_alpha,"flat":opacity.unshaded}
		opacity.set_appearance(1.0,false)
	var old_overrides: Dictionary = expected_overrides.duplicate()
	var old_visibility: Dictionary = expected_visibility.duplicate()
	for row in prepared.materials:
		var node: MeshInstance3D = nodes[row.node]
		node.set_surface_override_material(row.surface,material_refs[row.material])
	for row in prepared.visibility: nodes[row.node].visible = row.visible
	var matched: bool = true
	for row in prepared.materials:
		if nodes[row.node].get_surface_override_material(row.surface) != material_refs[row.material]: matched = false
	for row in prepared.visibility:
		if nodes[row.node].visible != row.visible: matched = false
	if not matched:
		for key in old_overrides:
			var parts: PackedStringArray = key.split(":")
			nodes[parts[0].to_int()].set_surface_override_material(parts[1].to_int(),old_overrides[key])
		for id in old_visibility: nodes[id].visible = old_visibility[id]
	else:
		for row in prepared.materials: expected_overrides[str(row.node)+":"+str(row.surface)] = material_refs[row.material]
		for row in prepared.visibility: expected_visibility[row.node] = row.visible
		current = prepared.selection.duplicate(true)
	if opacity != null and token.alpha >= 0.0: opacity.set_appearance(float(token.alpha),bool(token.flat))
	return "" if matched else "The appearance transaction could not be applied; the previous selection was restored."
