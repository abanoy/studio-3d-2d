extends RefCounted
# Container boundary only. Legacy1/2 have no active-basis representation; the
# qualified current capability domain remains schema3 through9.
const ImportBasis=preload("res://src/import_basis.gd")
const Extended=preload("res://src/extended_timing.gd")
const Reference=preload("res://src/reference_sheet_data.gd")
const MARKERS=["basis_content_schema_version","import_basis_capability"]

static func _actor_basis_fields(actor) -> bool:
	return actor is Dictionary and (actor.has("asset_basis") or actor.get("metadata") is Dictionary and actor.metadata.has("import_basis_lineage"))

static func _legacy_basis_fields(document: Dictionary,depth:=0) -> bool:
	if depth>1 or document.get("schema_version")==9:return true
	for key in MARKERS:
		if document.has(key):return true
	for key in ["model","scene"]:
		var actor=document.get(key,{})
		if _actor_basis_fields(actor):return true
	var world=document.get("world",{})
	if world is Dictionary and world.get("objects") is Array:
		if world.objects.size()>64:return true
		for actor in world.objects:
			if _actor_basis_fields(actor):return true
	var graph=document.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		if graph.assets.size()>4:return true
		for asset in graph.assets:
			if asset is Dictionary and asset.get("scene") is Dictionary and _legacy_basis_fields(asset.scene,depth+1):return true
	return false

static func validation_view(document) -> Dictionary:
	if not document is Dictionary:return {"error":"Invalid project metadata."}
	var version=document.get("schema_version")
	if (version is int or version is float) and (version==1 or version==2):
		if _legacy_basis_fields(document):return {"error":"Import size requires project schema9. Previous project preserved."}
		return {"document":document.duplicate(true)}
	return ImportBasis.legacy_validation_view(document)

static func decoded_content_schema(document) -> int:
	# Called on already decoded runtime data as well as portable manifests. Old
	# readers expose a resolved session reference sheet without retaining schema7;
	# recognize only that exact validated runtime shape for the capability check.
	if not document is Dictionary:return -1
	var version=document.get("schema_version")
	if not (version is int or version is float) or not is_finite(float(version)) or version!=floor(float(version)) or version<1 or version>9:return -1
	version=int(version)
	var candidate: Dictionary=document.duplicate(true)
	if version in [1,2]:
		if candidate.has("timing_content_schema_version") or candidate.has("content_schema_version") or candidate.has("reference_sheet"):return -1
		return int(version) if not validation_view(candidate).has("error") else -1
	if version in [3,4,5,6] and candidate.has("reference_sheet") and not candidate.has("content_schema_version") and not candidate.has("timing_content_schema_version"):
		if not Reference.error(candidate.reference_sheet).is_empty():return -1
		candidate.erase("reference_sheet")
	var admitted:=validation_view(candidate)
	if admitted.has("error"):return -1
	var view: Dictionary=admitted.document
	if view.get("schema_version")==8:
		var timing:=Extended.unwrap(view)
		if timing.has("error"):return -1
		view=timing.base
	if view.get("schema_version")==7:
		var reference_content=view.get("content_schema_version")
		if not (reference_content is int or reference_content is float) or not is_finite(float(reference_content)) or reference_content!=floor(float(reference_content)) or reference_content<3 or reference_content>6:return -1
		var sheet=view.get("reference_sheet")
		if not sheet is Dictionary:return -1
		if not Reference.error(sheet,not sheet.has("source")).is_empty():return -1
		view.schema_version=int(reference_content);view.erase("content_schema_version");view.erase("reference_sheet")
	var effective=view.get("schema_version")
	return int(effective) if (effective is int or effective is float) and is_finite(float(effective)) and effective==floor(float(effective)) and effective>=1 and effective<=6 else -1

static func restore_capabilities(original: Dictionary,decoded: Dictionary) -> Dictionary:
	# Legacy decoders resolve payload paths and historically peel timing/reference
	# wrappers. Active scenes retain their original scene-local capability and
	# wrapper metadata without substituting the portable original for runtime data.
	if original.get("schema_version")==9:
		for key in ["schema_version","basis_content_schema_version","import_basis_capability","timing_content_schema_version","content_schema_version"]:
			if original.has(key):decoded[key]=original[key]
	var graph=original.get("sequence_graph",{})
	if graph is Dictionary and graph.get("assets") is Array:
		var loaded=decoded.get("sequence_graph",{})
		if not loaded is Dictionary or not loaded.get("assets") is Array or loaded.assets.size()!=graph.assets.size():return {"error":"Import-size sequence capability restoration failed. Previous project preserved."}
		for index in range(graph.assets.size()):
			var source=graph.assets[index]
			var target=loaded.assets[index]
			if not source is Dictionary or not source.get("scene") is Dictionary or not target is Dictionary or not target.get("scene") is Dictionary:return {"error":"Invalid import-size sequence capability. Previous project preserved."}
			var child:=restore_capabilities(source.scene,target.scene)
			if child.has("error"):return child
			target.scene=child
	return decoded
