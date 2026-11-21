extends RefCounted
# Source-independent static appearance choices. JSON integers arrive as floats in
# Godot; admit only finite exact integer values, never bools or coercible text.
const FORMAT := "studio_model_variants_1"
const INVENTORY := "studio_variant_asset_inventory_1"
const SELECTION := "studio_variant_selection_1"
const PLAN := "studio_variant_apply_plan_1"
const META := "model_variants"
const FIELD := "variant_selection"
const MAX_BYTES := 256 * 1024

static func fail(code: String) -> Dictionary:
	return {"error":"Invalid model appearance choices: " + code + "."}
static func fields(value: Variant, expected: Array) -> bool:
	if not value is Dictionary or value.size() != expected.size(): return false
	for key in value:
		if not key is String or not key in expected: return false
	return true
static func whole(value: Variant, low: int, high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == floor(float(value)) and value >= low and value <= high
static func bounded(value: Variant, low: int, high: int) -> bool:
	return value is Array and value.size() >= low and value.size() <= high
static func label(value: Variant) -> bool:
	if not value is String or value.length() > 1024 or value.to_utf8_buffer().size() > 4096: return false
	for index in range(value.length()):
		var scalar: int = value.unicode_at(index)
		if scalar < 32 or scalar == 127 or scalar >= 0xd800 and scalar <= 0xdfff: return false
	return true
static func sha(value: Variant) -> bool:
	if not value is String or value.length() != 64: return false
	for character in value:
		if not character in "0123456789abcdef": return false
	return true
static func ascii_json_bytes(value: Variant) -> int:
	# Match the frozen Python planner's ensure_ascii budget, including surrogate
	# pairs for supplementary Unicode. No display-label normalization is applied.
	var encoded: String = JSON.stringify(value,"",true,true)
	var count: int = encoded.to_utf8_buffer().size()
	for index in range(encoded.length()):
		var scalar: int = encoded.unicode_at(index)
		if scalar >= 0x10000: count += 8
		elif scalar >= 0x800: count += 3
		elif scalar >= 0x80: count += 4
	return count
static func manifest(record: Dictionary) -> Dictionary:
	var metadata: Variant = record.get("metadata",{})
	return metadata[META] if metadata is Dictionary and metadata.get(META) is Dictionary else {}

static func canonical(value: Variant, inventory: Dictionary = {}) -> Dictionary:
	if not fields(value,["format","asset_sha256","default_skin","skins","groups","surfaces"]): return fail("declaration fields")
	if not value.format is String or value.format != FORMAT or not sha(value.asset_sha256): return fail("asset identity")
	if not bounded(value.skins,1,64) or not whole(value.default_skin,0,value.skins.size()-1): return fail("skin table")
	var skins: Array = []
	for index in range(value.skins.size()):
		var row: Variant = value.skins[index]
		if not fields(row,["id","name"]) or not whole(row.id,index,index) or not label(row.name): return fail("skin entry")
		skins.append({"id":index,"name":row.name})
	var default_skin: int = int(value.default_skin)
	if not bounded(value.surfaces,1,16384): return fail("surface table")
	var surfaces: Dictionary = {}
	var declared_nodes: Dictionary = {}
	for row in value.surfaces:
		if not fields(row,["node","surface","materials"]) or not whole(row.node,0,99999) or not whole(row.surface,0,255) or not bounded(row.materials,skins.size(),skins.size()): return fail("surface entry")
		var node: int = int(row.node)
		var surface: int = int(row.surface)
		var key: String = str(node)+":"+str(surface)
		if surfaces.has(key): return fail("duplicate surface")
		var materials: Array = []
		for material in row.materials:
			if not whole(material,0,255): return fail("material index")
			materials.append(int(material))
		surfaces[key] = {"node":node,"surface":surface,"materials":materials}
		if not declared_nodes.has(node): declared_nodes[node] = {}
		declared_nodes[node][surface] = materials[default_skin]
	if declared_nodes.size() > 4096: return fail("mesh budget")
	for node in declared_nodes:
		for index in range(declared_nodes[node].size()):
			if not declared_nodes[node].has(index): return fail("surface gap")
	if not bounded(value.groups,0,32): return fail("bodygroup table")
	var groups: Array = []
	var owned: Dictionary = {}
	var total: int = 0
	for group_id in range(value.groups.size()):
		var group: Variant = value.groups[group_id]
		if not fields(group,["id","name","default","choices"]) or not whole(group.id,group_id,group_id) or not label(group.name) or not bounded(group.choices,1,64): return fail("bodygroup entry")
		if not whole(group.default,0,group.choices.size()-1): return fail("default bodygroup")
		var choices: Array = []
		for choice_id in range(group.choices.size()):
			var choice: Variant = group.choices[choice_id]
			if not fields(choice,["id","name","blank","nodes"]) or not whole(choice.id,choice_id,choice_id) or not label(choice.name) or not choice.blank is bool or not bounded(choice.nodes,0,4096): return fail("bodygroup choice")
			if choice.blank != choice.nodes.is_empty(): return fail("blank geometry")
			var nodes: Array = []
			for raw in choice.nodes:
				if not whole(raw,0,99999): return fail("choice node")
				var node: int = int(raw)
				if not declared_nodes.has(node) or owned.has(node): return fail("choice ownership")
				owned[node] = true; nodes.append(node)
			nodes.sort(); choices.append({"id":choice_id,"name":choice.name,"blank":choice.blank,"nodes":nodes})
		total += choices.size()
		if total > 512: return fail("choice budget")
		groups.append({"id":group_id,"name":group.name,"default":int(group.default),"choices":choices})
	if not inventory.is_empty():
		if not fields(inventory,["format","asset_sha256","material_count","mesh_nodes"]) or not inventory.format is String or inventory.format != INVENTORY or not sha(inventory.asset_sha256) or inventory.asset_sha256 != value.asset_sha256 or not whole(inventory.material_count,1,256) or not bounded(inventory.mesh_nodes,1,4096): return fail("actual asset inventory")
		var actual: Dictionary = {}
		for row in inventory.mesh_nodes:
			if not fields(row,["node","parent_mesh","surface_materials"]) or not whole(row.node,0,99999) or not bounded(row.surface_materials,1,256): return fail("actual mesh entry")
			var node: int = int(row.node)
			if actual.has(node) or not declared_nodes.has(node) or row.parent_mesh != null and not whole(row.parent_mesh,0,99999): return fail("actual mesh identity")
			if row.surface_materials.size() != declared_nodes[node].size(): return fail("actual surface coverage")
			for surface in range(row.surface_materials.size()):
				if not whole(row.surface_materials[surface],0,int(inventory.material_count)-1) or int(row.surface_materials[surface]) != declared_nodes[node][surface]: return fail("actual default material")
				for material in surfaces[str(node)+":"+str(surface)].materials:
					if material >= int(inventory.material_count): return fail("actual material domain")
			actual[node] = row
		if actual.size() != declared_nodes.size(): return fail("actual mesh coverage")
		for node in actual:
			var visited: Dictionary = {}
			var parent: Variant = node
			while parent != null:
				if not actual.has(int(parent)) or visited.has(int(parent)): return fail("mesh parent graph")
				visited[int(parent)] = true
				if int(parent) != node and owned.has(int(parent)): return fail("controlled mesh ancestor")
				parent = actual[int(parent)].parent_mesh
	var ordered: Array = surfaces.values()
	ordered.sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return a.node < b.node or a.node == b.node and a.surface < b.surface)
	var result: Dictionary = {"format":FORMAT,"asset_sha256":value.asset_sha256,"default_skin":default_skin,"skins":skins,"groups":groups,"surfaces":ordered}
	if ascii_json_bytes(result) > MAX_BYTES: return fail("metadata budget")
	return {"manifest":result}

static func selection(value: Variant, declared: Dictionary) -> Dictionary:
	if not fields(value,["format","skin","groups"]) or not value.format is String or value.format != SELECTION or not whole(value.skin,0,declared.skins.size()-1) or not value.groups is Dictionary or value.groups.size() != declared.groups.size(): return fail("selection")
	var chosen: Dictionary = {}
	for group in declared.groups:
		var key: String = str(group.id)
		if not value.groups.has(key) or not whole(value.groups[key],0,group.choices.size()-1): return fail("selected bodygroup")
		chosen[key] = int(value.groups[key])
	return {"selection":{"format":SELECTION,"skin":int(value.skin),"groups":chosen}}
static func defaults(declared: Dictionary) -> Dictionary:
	var groups: Dictionary = {}
	for group in declared.groups: groups[str(group.id)] = group.default
	return {"format":SELECTION,"skin":declared.default_skin,"groups":groups}
static func plan(declared: Dictionary, selected: Variant) -> Dictionary:
	var parsed: Dictionary = selection(selected,declared)
	if parsed.has("error"): return parsed
	var current: Dictionary = parsed.selection
	var controlled: Dictionary = {}
	var visible: Dictionary = {}
	for group in declared.groups:
		for choice in group.choices:
			for node in choice.nodes: controlled[node] = true
		for node in group.choices[current.groups[str(group.id)]].nodes: visible[node] = true
	var ids: Array = controlled.keys(); ids.sort()
	var visibility: Array = []
	for node in ids: visibility.append({"node":node,"visible":visible.has(node)})
	var materials: Array = []
	for row in declared.surfaces: materials.append({"node":row.node,"surface":row.surface,"material":row.materials[current.skin]})
	return {"format":PLAN,"asset_sha256":declared.asset_sha256,"selection":current,"visibility":visibility,"materials":materials}
static func record_error(record: Dictionary) -> String:
	var metadata: Variant = record.get("metadata",{})
	var present: bool = metadata is Dictionary and metadata.has(META)
	if not present: return "Variant selection requires declared model appearance choices." if record.has(FIELD) else ""
	if record.get("kind","model") != "model": return "Appearance choices apply only to model actors."
	var checked: Dictionary = canonical(metadata[META])
	if checked.has("error"): return checked.error
	if checked.manifest.asset_sha256 != record.get("sha256"): return "Model appearance choices belong to a different GLB."
	if record.has(FIELD):
		var chosen: Dictionary = selection(record[FIELD],checked.manifest)
		if chosen.has("error"): return chosen.error
	return ""

# Project schema10 is the explicit forward-incompatible capability boundary.
# Legacy validation receives a temporary stripped view; original metadata and
# selections are restored only after all existing payload validation succeeds.
const PROJECT_VERSION := 10
const PROJECT_MARKER := "variant_capability"
const PROJECT_CONTENT := "variant_content_schema_version"
static func _project_actors(document: Dictionary) -> Dictionary:
	var actors: Array = []
	for key in ["model","scene"]:
		var value: Variant = document.get(key,{})
		if value is Dictionary and not value.is_empty(): actors.append(value)
	var world: Variant = document.get("world",{})
	if world is Dictionary and world.has("objects"):
		if not bounded(world.objects,0,64): return fail("project actor budget")
		for actor in world.objects:
			if not actor is Dictionary: return fail("project actor entry")
			actors.append(actor)
	return {"actors":actors}
static func _feature_tree(document: Variant, depth: int = 0) -> bool:
	if not document is Dictionary or depth > 1: return false
	if document.get("schema_version") == PROJECT_VERSION or document.has(PROJECT_MARKER) or document.has(PROJECT_CONTENT): return true
	var collected: Dictionary = _project_actors(document)
	if not collected.has("error"):
		for actor in collected.actors:
			if actor.has(FIELD) or actor.get("metadata") is Dictionary and actor.metadata.has(META): return true
	var graph: Variant = document.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		for asset in graph.assets.slice(0,4):
			if asset is Dictionary and _feature_tree(asset.get("scene"),depth+1): return true
	return false
static func project_view(document: Variant, require_capability: bool = true, drop_fields: bool = true, depth: int = 0) -> Dictionary:
	if not _feature_tree(document,depth): return {"document":document.duplicate(true) if document is Dictionary else document,"required":false}
	if not document is Dictionary or depth > 1 or not whole(document.get("schema_version"),1,PROJECT_VERSION): return fail("project capability version")
	var base: Dictionary = document.duplicate(true)
	var wrapped: bool = int(base.schema_version) == PROJECT_VERSION
	if wrapped:
		if not base.get(PROJECT_MARKER) is String or base[PROJECT_MARKER] != FORMAT or not whole(base.get(PROJECT_CONTENT),3,9): return fail("project capability marker")
		base.schema_version = int(base[PROJECT_CONTENT]); base.erase(PROJECT_MARKER); base.erase(PROJECT_CONTENT)
	elif base.has(PROJECT_MARKER) or base.has(PROJECT_CONTENT): return fail("unwrapped project capability marker")
	var collected: Dictionary = _project_actors(base)
	if collected.has("error"): return collected
	var required: bool = false
	for actor in collected.actors:
		var metadata: Variant = actor.get("metadata",{})
		var has_variants: bool = metadata is Dictionary and metadata.has(META)
		if has_variants or actor.has(FIELD):
			var error: String = record_error(actor)
			if not error.is_empty(): return {"error":error}
			required = true
			if drop_fields: actor.metadata.erase(META); actor.erase(FIELD)
	var graph: Variant = base.get("sequence_graph",{})
	if graph is Dictionary and graph.has("assets"):
		if not bounded(graph.assets,0,4): return fail("sequence appearance budget")
		for asset in graph.assets:
			if not asset is Dictionary or not asset.get("scene") is Dictionary: return fail("sequence appearance entry")
			var child: Dictionary = project_view(asset.scene,require_capability,drop_fields,depth+1)
			if child.has("error"): return child
			asset.scene = child.document; required = required or child.required
	if require_capability and wrapped != required: return fail("appearance choices require project schema10")
	return {"document":base,"required":required}
static func encode_project(document: Dictionary, depth: int = 0) -> Dictionary:
	var view: Dictionary = project_view(document,false,false,depth)
	if view.has("error"): return view
	var result: Dictionary = view.document
	var graph: Variant = result.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		for asset in graph.assets:
			var child: Dictionary = encode_project(asset.scene,depth+1)
			if child.has("error"): return child
			asset.scene = child.document
	if view.required:
		if not whole(result.schema_version,3,9): return fail("appearance project content")
		result[PROJECT_CONTENT] = int(result.schema_version); result[PROJECT_MARKER] = FORMAT; result.schema_version = PROJECT_VERSION
	return {"document":result}
static func restore_project(original: Dictionary, decoded: Dictionary, depth: int = 0) -> Dictionary:
	if depth > 1: return fail("restored sequence appearance depth")
	var result: Dictionary = decoded
	var source_actors: Dictionary = _project_actors(original)
	var target_actors: Dictionary = _project_actors(result)
	if source_actors.has("error") or target_actors.has("error") or source_actors.actors.size() != target_actors.actors.size(): return fail("restored appearance actor coverage")
	for index in range(source_actors.actors.size()):
		var source: Dictionary = source_actors.actors[index]
		var target: Dictionary = target_actors.actors[index]
		var metadata: Variant = source.get("metadata",{})
		if metadata is Dictionary and metadata.has(META):
			if target.get("id") != source.get("id") or target.get("sha256") != source.get("sha256") or not target.get("metadata") is Dictionary: return fail("restored appearance actor identity")
			target.metadata[META] = metadata[META].duplicate(true)
			if source.has(FIELD): target[FIELD] = source[FIELD].duplicate(true)
	var source_graph: Variant = original.get("sequence_graph",{})
	var target_graph: Variant = result.get("sequence_graph",{})
	if source_graph is Dictionary and source_graph.get("assets") is Array:
		if not target_graph is Dictionary or not target_graph.get("assets") is Array or target_graph.assets.size() != source_graph.assets.size(): return fail("restored appearance sequence coverage")
		for index in range(source_graph.assets.size()):
			var source: Dictionary = source_graph.assets[index]
			var target: Dictionary = target_graph.assets[index]
			if source.get("id") != target.get("id"): return fail("restored appearance sequence identity")
			var child: Dictionary = restore_project(source.scene,target.scene,depth+1)
			if child.has("error"): return child
			target.scene = child
	if original.get("schema_version") == PROJECT_VERSION:
		result.schema_version = PROJECT_VERSION; result[PROJECT_MARKER] = FORMAT; result[PROJECT_CONTENT] = original[PROJECT_CONTENT]
	return result
