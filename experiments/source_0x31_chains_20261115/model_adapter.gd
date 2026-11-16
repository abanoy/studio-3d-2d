extends RefCounted
# SOURCE ONLY UNPARSED/UNRUN. Exact69-bone Junko pair profile only.
# Root stages qualified leaf_adapter.gd + leaf_candidate.gd unchanged.
const Boundary = preload("res://leaf_adapter.gd")
const Chains = preload("res://chain_solver.gd")
const Math = preload("res://leaf_candidate.gd")
const Model = preload("res://src/model.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const SELECTED := [17,18,26,27]
const EXPECTED_PARENTS := {17:7,18:17,26:25,27:26}
const EPS := 0.00002

static func frame_from_boundary(value: Transform3D) -> Dictionary:
	var mapped := Boundary.frame64(value)
	if mapped.has("error"): return mapped
	return {"frame":{"origin":mapped.goal.base.duplicate(true),"basis":mapped.rotation.duplicate(true),"scale":mapped.scale},"correction_max":mapped.correction_max}

static func construct(actor: RefCounted, resolution: RefCounted) -> Dictionary:
	if resolution.status != "bound_inactive" or resolution.bindings.size() != 69 or resolution.rule_owner_ids.size() != 49 or not Bindings.current(actor,resolution): return {"error":"Exact current69/49 inactive Source profile required"}
	var native: Dictionary = actor.data.metadata.native_parameters.native_parameters
	if native.source_jiggle.applied != false or native.source_jiggle.full_native_rule_layout_verified != false or native.source_export_crosswalk.native_solver != "not_implemented" or float(native.source_jiggle.source_scale) != 0.01905: return {"error":"Retained source metadata must stay inactive and unchanged"}
	var skeleton: Skeleton3D = resolution.bindings[17].skeleton
	if skeleton.get_bone_count() != 69 or actor.bones.size() != 69: return {"error":"Only the exact single69-bone Skeleton profile is admitted"}
	var bones := {}
	var selected := {}
	var parameters := {}
	var correction := 0.0
	for index in range(69):
		var binding: RefCounted = resolution.bindings[index]
		var id: String = binding.has_id
		if binding.skeleton != skeleton or not actor.bones.has(id) or not skeleton.is_bone_enabled(binding.skeleton_bone_index): return {"error":"Mixed/disabled actual Skeleton bindings"}
		var base := frame_from_boundary(actor.bones[id].base)
		if base.has("error"): return base
		correction = maxf(correction,float(base.correction_max))
		var parent_index: int = binding.native_parent_index
		bones[id] = {"parent":null if parent_index < 0 else resolution.by_native[parent_index],"base":base.frame}
		if index in SELECTED:
			if parent_index != EXPECTED_PARENTS[index]: return {"error":"Exact measured native17/18 and26/27 pairs required"}
			selected[index] = id
	# Refuse additional descendants: these selected parents have exactly one
	# direct child, and both selected child bones are leaves in the exact profile.
	for index in SELECTED:
		var children: Array = []
		for child in range(69):
			if resolution.bindings[child].native_parent_index == index: children.append(child)
		var expected: Array = [18] if index == 17 else [27] if index == 26 else []
		if children != expected: return {"error":"Selected native subtree differs from bounded two-pair profile"}
	for rule in native.source_jiggle.rules:
		var index := int(rule.native_bone_index)
		if not SELECTED.has(index): continue
		if int(rule.raw_rule_flags) != 0x31 or int(rule.unknown_rule_flag_bits) != 0 or not rule.parameters is Dictionary: return {"error":"Unsupported native rule flags/parameters"}
		var p := {}
		for key in Math.defaults():
			if key == "raw_rule_flags": p[key] = 0x31
			elif not rule.parameters.has(key): return {"error":"Missing retained native parameter"}
			else: p[key] = rule.parameters[key]
		var error := Math.parameter_error(p)
		if not error.is_empty(): return {"error":error}
		parameters[selected[index]] = p
	if parameters.size() != 4: return {"error":"All four exact retained0x31 rules required"}
	return {"bones":bones,"parameters":parameters,"selected":selected,"skeleton":skeleton,"boundary_correction_max":correction}

static func capture_baseline(actor: RefCounted, profile: Dictionary) -> Dictionary:
	# Caller clears live_pose and applies the current authored frame first.
	# No previously solved transform is sampled as an authored goal.
	if actor.live_pose != null or actor.live_world_transform != null: return {"error":"This first pair probe requires a plain authored baseline, no body/live-world owner"}
	var skeleton: Skeleton3D = profile.skeleton
	var prefix := frame_from_boundary(skeleton.global_transform)
	if prefix.has("error"): return prefix
	var locals := {}
	var correction: float = prefix.correction_max
	var closure := 0.0
	for id in profile.bones:
		var info: Dictionary = actor.bones[id]
		var raw_local: Transform3D = skeleton.get_bone_pose(info.index)
		var local := frame_from_boundary(raw_local)
		if local.has("error"): return local
		var base_size: float = profile.bones[id].base.scale
		if absf(float(local.frame.scale)-base_size) > EPS*base_size: return {"error":"Actual local pose scale differs from Model base contract"}
		# Quaternion-derived float32 bases have tiny length roundoff. Use the
		# immutable measured base scale, with the same preregistered2e-5 guard.
		local.frame.scale = base_size
		locals[id] = local.frame
		correction = maxf(correction,float(local.correction_max))
		var parent: Variant = profile.bones[id].parent
		var parent_world: Transform3D = skeleton.global_transform if parent == null else actor.bone_transform(parent)
		var world: Transform3D = actor.bone_transform(id)
		var actual := frame_from_boundary(world)
		if actual.has("error"): return actual
		var error := Boundary.transform_error(parent_world*raw_local,world)
		if error > EPS*maxf(1.0,float(actual.frame.scale)): return {"error":"Actual parent*absoluteLocal != current bone world; no rest correction guessed"}
		closure = maxf(closure,error)
	return {"locals":locals,"prefix":prefix.frame,"boundary_correction_max":correction,"parent_local_closure_max":closure}

static func overlay(actor: RefCounted, profile: Dictionary, authored: Dictionary, result: Dictionary) -> Dictionary:
	if result.has("error") or not result.has("delta_bases") or result.delta_bases.size() != profile.parameters.size(): return {"error":"Complete computed four-rule result required"}
	var pose := authored.duplicate(true)
	for id in profile.parameters:
		if not result.delta_bases.has(id) or not actor.bones.has(id): return {"error":"Missing actual computed bone overlay"}
		var q := Boundary.basis_from64(result.delta_bases[id]).get_rotation_quaternion().normalized()
		if not is_finite(q.x) or not is_finite(q.y) or not is_finite(q.z) or not is_finite(q.w): return {"error":"Nonfinite desired local rotation"}
		var original: Dictionary = authored.get(id,Model.identity())
		pose[id] = {"position":original.position.duplicate(true),"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	return {"pose":pose}
