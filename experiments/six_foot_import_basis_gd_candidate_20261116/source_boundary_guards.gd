extends RefCounted
# UNPARSED/UNRUN fail-closed port draft. This is NOT wired into current HAS.
# No runtime-ready token or import/classifier activation is exposed here.
const MESSAGE := "This HAS build does not support an active import basis yet. The current model and project were kept."
const STEPS := ["renderer_prepare_model","world_prepare","initial_placement","shape_comparison_preview","wind_preview","helper_import","helper_apply"]

static func model_error(value) -> String:
	return MESSAGE if value is Dictionary and value.has("asset_basis") else ""

static func project_error(value) -> String:
	if not value is Dictionary: return ""
	if value.get("schema_version") == 9 or value.has("basis_content_schema_version") or value.has("import_basis_capability"): return MESSAGE
	if not model_error(value.get("model",{})).is_empty(): return MESSAGE
	var scene = value.get("scene",{})
	if scene is Dictionary and scene.has("asset_basis"): return MESSAGE
	var world = value.get("world",{})
	if world is Dictionary and world.get("objects") is Array:
		for row in world.objects:
			if not model_error(row).is_empty(): return MESSAGE
	var graph = value.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		# Existing sequence domain permits4 assets and no nested child graphs.
		# Refuse malformed/oversized graphs here instead of traversing unbounded data.
		if graph.assets.size() > 4: return MESSAGE
		for asset in graph.assets:
			if not asset is Dictionary: return MESSAGE
			var child = asset.get("scene",{})
			if child is Dictionary and child.has("sequence_graph"): return MESSAGE
			if not project_error(child).is_empty(): return MESSAGE
	return ""

static func before_step(step: String,data,continuation: Callable) -> Dictionary:
	# Testable proposed early guard: validate before load/binding/placement/helper.
	# App integration should put model_error directly at each recorded source anchor.
	if not step in STEPS: return {"error":"Unknown import-basis boundary"}
	var error := model_error(data)
	if not error.is_empty(): return {"error":error}
	if not continuation.is_valid(): return {"error":"Missing legacy continuation"}
	var result = continuation.call()
	return result if result is Dictionary else {"error":"Invalid legacy continuation result"}
