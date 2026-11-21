extends RefCounted
# Source-only candidate. Compose current HAS capability with immutable import facts.
const Native = preload("res://src/source_secondary.gd")
const Model = preload("res://src/model.gd")
const FORMAT := "has_import_capability_summary_1"
const MAX_LINES := 128
const MAX_LINE := 800

static func add(lines: Array, value: String) -> void:
	value = value.strip_edges().left(MAX_LINE)
	if lines.size() < MAX_LINES and not value.is_empty() and not lines.has(value): lines.append(value)

static func lines(value: Variant, result: Dictionary) -> Array:
	var out := []
	if not value is Array:
		result.notes_incomplete = true
		return out
	if value.size() > MAX_LINES: result.more_notes_retained = true
	for entry in value.slice(0,MAX_LINES):
		if not entry is String:
			result.notes_incomplete = true
			continue
		if entry.length() > MAX_LINE: result.more_notes_retained = true
		add(out,entry)
	return out

static func dictionary(value: Variant) -> Dictionary:
	return value if value is Dictionary else {}

static func count(value: Variant) -> int:
	return int(value) if ((value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value)) and value >= 0 and value <= 1000000) else 0

static func native_preview(report: Dictionary, actor: RefCounted) -> Dictionary:
	var unavailable := {"supported":false,"owners":0,"reason":""}
	# An imported flag or a forged count cannot qualify a runtime capability.
	if actor == null or actor.get_script() != Model: return unavailable
	var actual: Variant = dictionary(actor.data.get("metadata",{})).get("native_parameters",{})
	if not actual is Dictionary or actual != report or not Native.offered(actor): return unavailable
	if Native.SELECTED_NATIVE_IDS != [8,17,18,26,27]: return unavailable
	# Existing full admission is read-only to the model. Dispose only this probe's
	# independent scratch states; never step or install a live overlay.
	var made: Dictionary = Native.create(actor)
	if made.has("error"):
		unavailable.reason = str(made.error).left(MAX_LINE)
		return unavailable
	var runner: RefCounted = made.get("runner")
	if runner == null: return unavailable
	var supported: bool = runner.chains.size() == 5
	runner.dispose()
	return {"supported":supported,"owners":5 if supported else 0,"reason":""}

static func summarize(report_value: Variant, actor: RefCounted = null) -> Dictionary:
	var result := {"format":FORMAT,"profile":"standard","title":"Import info","supported":[],"retained":[],"limitations":[],"actions":[],"native_motion":{"supported":false,"owners":0,"reason":""},"notes_incomplete":false,"more_notes_retained":false,"force_modal":false}
	if not report_value is Dictionary:
		add(result.supported,"This asset uses the standard HAS representation.")
		return result
	var report: Dictionary = report_value
	var warnings: Array = lines(report.get("warnings",[]),result)
	var limits: Array = lines(report.get("limits",report.get("limitations",[])),result)
	var mounts: Array = lines(report.get("mount_warnings",[]),result)
	var native: Dictionary = dictionary(report.get("native_parameters",{}))
	var counters: Dictionary = dictionary(report.get("counts",{}))
	if report.get("adapter") == "studio_source_1":
		result.profile = "source"
		add(result.supported,"Geometry and available base textures are converted into HAS.")
		if count(counters.get("bones",0)) > 0: add(result.supported,"The imported rig and object hierarchy are retained.")
		add(result.limitations,"Textures and materials approximate the original game's appearance.")
		add(result.limitations,"Original game material programs and dynamic material effects are not run.")
		add(result.limitations,"Separate 3D skybox scenery is not rebuilt.")
		add(result.limitations,"Exporting back to the original game format is not supported.")
		add(result.limitations,"Changing imported outfits or parts requires another import.")
		add(result.limitations,"Native game animations, IK and gameplay are not replayed. HAS posing uses its own controls.")
		add(result.limitations,"HDR, animated and displacement map lighting are not reproduced.")
		var baked: Dictionary = dictionary(native.get("static_brush_lightmaps",{}))
		var baked_faces: int = count(baked.get("faces",0))
		if baked_faces > 0: add(result.supported,"Compatible baked map lighting is retained on %d surfaces." % baked_faces)
		var lights: Variant = native.get("static_entity_lights",[])
		if lights is Array and not lights.is_empty(): add(result.supported,"Compatible static map lights are converted; their brightness is approximate.")
		var jiggle: Dictionary = dictionary(native.get("source_jiggle",{}))
		var rules: Variant = jiggle.get("rules",[])
		if jiggle.get("status") == "retained_inert" and rules is Array and not rules.is_empty():
			add(result.retained,"%d imported motion declarations are stored; they are not all simulated." % rules.size())
		result.native_motion = native_preview(report,actor)
		if result.native_motion.supported:
			add(result.supported,"Five imported joints can use the HAS loose-part preview in the current model setup.")
			add(result.limitations,"Other imported physics remains inactive; original collision bodies and constraints are not applied.")
		else:
			add(result.limitations,"Imported physics is not active in this setup. Use HAS Physics or explicit loose-part setup.")
			if not result.native_motion.reason.is_empty(): add(result.actions,result.native_motion.reason)
		for value in limits:
			if value.contains("all imported variants retained in editable.blend"): add(result.retained,"Other imported appearance choices remain in the editable preparation file.")
			# Retain the original report; replace only known overbroad legacy wording
			# in this current-capability view. Unknown notes are always preserved.
			if value.begins_with("PBR approximation;") or value.begins_with("Default skin/bodygroup") or value.begins_with("One selected static skin/bodygroup") or value.begins_with("No Source physics, IK,"): continue
			add(result.limitations,value)
		for value in warnings:
			if value.begins_with("Static Source entity lights use approximate intensity,"):
				add(result.limitations,"Converted lights approximate native intensity and falloff; animated and HDR styles are not reproduced.")
			else: add(result.limitations,value)
		var materials: Variant = report.get("materials",[])
		if materials is Array:
			for material in materials.slice(0,256):
				if material is Dictionary and material.get("status") == "fallback gray":
					add(result.actions,"Some resources could not be prepared. Restore the listed files or choose dependency folders, then import again.")
	elif report.get("kind") == "mmd_preparation":
		result.profile = "mmd"
		add(result.supported,"Geometry, rig and exportable facial shapes use the shared HAS controls.")
		add(result.retained,"Supported native joint declarations can be used when preparing poses or motions.")
		for value in limits: add(result.limitations,value)
		for value in warnings: add(result.limitations,value)
		var missing: Variant = report.get("missing_textures",[])
		if missing is Array and not missing.is_empty(): add(result.actions,"Restore the named texture files beside the original model, then import again.")
	elif report.get("kind") == "vrm_preparation":
		result.profile = "vrm"
		add(result.supported,"Embedded geometry, rig, textures and facial shapes are retained in HAS.")
		add(result.retained,"Native avatar and spring declarations are retained. Compatible chains can use Hair & clothes.")
		for value in limits: add(result.limitations,value)
		for value in warnings: add(result.limitations,value)
		if actor != null and actor.get_script() == Model and is_instance_valid(actor.root):
			var spring: Variant = actor.root.get_meta("has_secondary_rig",{})
			if spring is Dictionary and spring.get("error","") is String and not spring.error.is_empty(): add(result.actions,spring.error)
	else:
		add(result.supported,"This asset uses the standard HAS representation.")
		for value in limits: add(result.limitations,value)
		for value in warnings: add(result.limitations,value)
	for value in mounts: add(result.actions,value)
	if result.notes_incomplete: add(result.actions,"Some import notes are incomplete. Keep the preparation folder and reimport if a feature is missing.")
	if result.more_notes_retained: add(result.limitations,"More import notes are retained in the original report.")
	result.note_count = result.retained.size()+result.limitations.size()+result.actions.size()
	return result

static func plain_text(summary: Dictionary) -> String:
	var text := ""
	for group in [["supported","Available"],["retained","Stored data"],["limitations","Compatibility notes"],["actions","What you can do"]]:
		var values: Array = summary.get(group[0],[])
		if values.is_empty(): continue
		if not text.is_empty(): text += "\n\n"
		text += str(group[1])+"\n"
		for value in values: text += "• "+str(value)+"\n"
	if summary.get("more_notes_retained",false): text += "\n\nMore notes are kept in the original import report."
	return text.strip_edges()
