extends RefCounted
# UNRUN opt-in ALL49 candidate. No active Studio/default/12-owner source is changed.
# Same retained0x31/two-prefix profile, full69 closure; native qualification pending.
const Math = preload("res://src/source_jiggle_math.gd")
const Chains = preload("res://src/source_chain_math.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Model = preload("res://src/model.gd")
const Bounds = preload("res://src/pose_bounds.gd")
const GLB_SHA := "4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"
# Exact live bridge result db271160: native normals, actual69-bone/49-rule
# final-SHA publication and private/source/runtime preservation all verified.
const LIVE_GLB_SHA := "b8436dea1d13a7cb4632c37c50b4cab123616ec574720fe4e764b844c5293e71"
const LIVE_CROSSWALK_PROOF_SHA := "fb677e1a5e196f964c3634abba009ff792e7af0ff6dda260abc2e3ee12dacc37"
const LIVE_NATIVE_MDL_SHA := "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
const WIRE_SHA := "34230c89c7cda4417a0f142b375f26fbb5cf15a7faf4d98b5424acd0bec621c2"
const PREFIX_SHA := "945d7fd433ddba7f7e8f90cb1cb2c2e7d4c1e26005684ac4a330b23a3691a3fd"
const SOURCE_SCALE := 0.01905
const EPS := 0.00002
const SELECTED_NATIVE := 8
const SELECTED_NATIVE_IDS := [8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,26,27,29,30,32,33,35,36,37,39,40,41,43,44,45,47,48,49,51,52,53,55,56,57,60,61,62,63,65,66,67,68]
const STIFF_NATIVE_IDS := [8,9,10,11,12,13,14,15,16,60,61,62,63,65,66,67,68]
const EXPECTED_PARENTS := {8:7,9:7,10:7,11:7,12:7,13:7,14:7,15:7,16:7,17:7,18:17,19:7,20:19,21:7,22:7,23:7,24:7,26:25,27:26,29:28,30:29,32:31,33:32,35:34,36:35,37:36,39:38,40:39,41:40,43:42,44:43,45:44,47:46,48:47,49:48,51:50,52:51,53:52,55:54,56:55,57:56,60:59,61:60,62:61,63:62,65:64,66:65,67:66,68:67}
const EXPECTED_CHILDREN := {8:[],9:[],10:[],11:[],12:[],13:[],14:[],15:[],16:[],17:[18],18:[],19:[20],20:[],21:[],22:[],23:[],24:[],26:[27],27:[],29:[30],30:[],32:[33],33:[],35:[36],36:[37],37:[],39:[40],40:[41],41:[],43:[44],44:[45],45:[],47:[48],48:[49],49:[],51:[52],52:[53],53:[],55:[56],56:[57],57:[],60:[61],61:[62],62:[63],63:[],65:[66],66:[67],67:[68],68:[]}
const CHAIN_PREFIX_SHA := "f2add968c86ab5b5d6de6cc60586f1d57ecbbdd61b86b93eb2a90bcfbe0e06ba"
var actor: RefCounted
var resolution: RefCounted
var chains: Array = []
var _chain_inventory_stamp := PackedByteArray()
var _source_path := ""
var _skeleton: Skeleton3D
var _parameters: Dictionary = {}
var _bone_specs: Dictionary = {}
var _solver_bone_specs: Dictionary = {}
var _capture_configuration_stamp := PackedByteArray()
var _baseline_guard: RefCounted
var _baseline_guard_stamp := PackedByteArray()
const EXPECTED_CAPTURE_NATIVE_IDS := [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68]
var _base_scales: Dictionary = {}
var _chain: RefCounted
var _trial: RefCounted
var _configuration_stamp := PackedByteArray()
var _size_tokens: Dictionary = {}
var _prefix_scale := 1.0
var _authored_scale_token := 1.0
var _tick := 0
var _alive := false
var processing_samples := 0
var processing_total_usec := 0
var processing_max_usec := 0
var _binding_stamp := PackedByteArray()
var _source_modified := 0
var _source_length := 0
var _source_header := PackedByteArray()

static func _qualified_sha(value: Variant) -> bool:
	if not value is String or value.length() != 64: return false
	for character in value:
		if not "0123456789abcdef".contains(character): return false
	return true

static func qualified_asset_data(data: Dictionary) -> bool:
	var digest_value: Variant = data.get("sha256")
	if not digest_value is String: return false
	# Preserve the historical exact asset route; ordinary full admission follows.
	if digest_value == GLB_SHA: return true
	if not _qualified_sha(LIVE_GLB_SHA) or not _qualified_sha(LIVE_CROSSWALK_PROOF_SHA) or digest_value != LIVE_GLB_SHA: return false
	var metadata: Variant = data.get("metadata",{})
	if not metadata is Dictionary: return false
	var report: Variant = metadata.get("native_parameters",{})
	if not report is Dictionary: return false
	var native: Variant = report.get("native_parameters",{})
	if not native is Dictionary: return false
	var crosswalk: Variant = native.get("source_export_crosswalk",{})
	if not crosswalk is Dictionary: return false
	return crosswalk.get("format") == "studio_source_bone_crosswalk_1" and crosswalk.get("status") == "retained_inert" and crosswalk.get("profile") == Bindings.PROFILE and crosswalk.get("native_mdl_sha256") == LIVE_NATIVE_MDL_SHA and crosswalk.get("glb_sha256") == LIVE_GLB_SHA and crosswalk.get("proof_sha256") == LIVE_CROSSWALK_PROOF_SHA and crosswalk.get("jiggle_wire_sha256") == WIRE_SHA

static func offered(rig: RefCounted) -> bool:
	# UI capability hint only. Full source hashing/binding validation happens at
	# creation, never once per render/physics tick. Explicit helpers take priority.
	if rig == null or not is_instance_valid(rig.root) or not qualified_asset_data(rig.data): return false
	var secondary = rig.root.get_meta("has_secondary_rig",{})
	if not secondary is Dictionary or not str(secondary.get("error","")).is_empty(): return false
	var generic = secondary.get("chains",[])
	if not generic is Array or not generic.is_empty(): return false
	var metadata = rig.data.get("metadata",{})
	if not metadata is Dictionary: return false
	var report = metadata.get("native_parameters",{})
	if not report is Dictionary or report.get("scale") != SOURCE_SCALE: return false
	var native = report.get("native_parameters",{})
	if not native is Dictionary: return false
	var crosswalk = native.get("source_export_crosswalk",{})
	var jiggle = native.get("source_jiggle",{})
	if not crosswalk is Dictionary or not jiggle is Dictionary: return false
	var bones = crosswalk.get("bones")
	var rules = jiggle.get("rules")
	return bones is Array and bones.size() == 69 and rules is Array and rules.size() == 49 and crosswalk.get("profile") == Bindings.PROFILE and crosswalk.get("glb_sha256") == rig.data.get("sha256") and crosswalk.get("jiggle_wire_sha256") == WIRE_SHA and jiggle.get("applied") is bool and jiggle.applied == false and jiggle.get("full_native_rule_layout_verified") is bool and jiggle.full_native_rule_layout_verified == false

static func anchors(rig: RefCounted) -> Array:
	if not offered(rig): return []
	# Hint only; creation authenticates every numeric crosswalk and binding.
	var report: Dictionary = rig.data.metadata.native_parameters.native_parameters.source_export_crosswalk
	var mapping = rig.root.get_meta("has_source_bones",{})
	if not mapping is Dictionary: return []
	var result: Array = []
	var seen := {}
	for native_index in SELECTED_NATIVE_IDS:
		var matched := false
		for row in report.bones:
			if not row is Dictionary or row.get("native_index") != native_index: continue
			if matched: return []
			matched = true
			var node_index = row.get("gltf_node_index")
			if not (node_index is int or node_index is float) or not is_finite(float(node_index)) or float(node_index) != floor(float(node_index)): return []
			var id = mapping.get(int(node_index),"")
			if not id is String or not rig.bones.has(id) or seen.has(id): return []
			seen[id] = true; result.append({"kind":"bone","id":id})
		if not matched: return []
	return result

static func vector64(value: Vector3) -> Array:
	return [float(value.x),float(value.y),float(value.z)]

static func basis64(columns: Array) -> Basis:
	return Basis(Vector3(columns[0][0],columns[0][1],columns[0][2]),Vector3(columns[1][0],columns[1][1],columns[1][2]),Vector3(columns[2][0],columns[2][1],columns[2][2]))

static func frame64(value: Transform3D) -> Dictionary:
	if not value.origin.is_finite() or not value.basis.is_finite() or value.basis.determinant() <= 0.0: return {"error":"Imported hair needs a finite, positive uniform transform."}
	var raw: Array = [vector64(value.basis.x),vector64(value.basis.y),vector64(value.basis.z)]
	var scales: Array = [Math.v_length(raw[0]),Math.v_length(raw[1]),Math.v_length(raw[2])]
	var size: float = scales[0]
	if not is_finite(size) or size <= 0.00001: return {"error":"Imported hair has a degenerate transform."}
	for i in range(3):
		if not is_finite(scales[i]) or absf(scales[i]-size) > EPS*size: return {"error":"Imported hair currently needs uniform scale."}
	var units: Array = [Math.v_mul(raw[0],1.0/scales[0]),Math.v_mul(raw[1],1.0/scales[1]),Math.v_mul(raw[2],1.0/scales[2])]
	for pair in [[0,1],[0,2],[1,2]]:
		if absf(Math.v_dot(units[pair[0]],units[pair[1]])) > EPS: return {"error":"Imported hair does not support sheared transforms."}
	var x: Array = units[0]
	var yr := Math.normalized(Math.v_sub(raw[1],Math.v_mul(x,Math.v_dot(x,raw[1]))))
	if yr.has("error"): return yr
	var y: Array = yr.value
	var z := Math.v_cross(x,y)
	if Math.v_dot(z,units[2]) <= 0.0: return {"error":"Imported hair does not support mirrored transforms."}
	var columns: Array = [x,y,z]
	var correction := 0.0
	for i in range(3):
		for j in range(3): correction = maxf(correction,absf(raw[i][j]/size-columns[i][j]))
	if correction > EPS: return {"error":"Imported hair transform precision is outside the supported profile."}
	var made := Math.goal(vector64(value.origin),columns)
	if made.has("error"): return made
	return {"goal":made.goal,"rotation":columns,"scale":size}

static func context_error(rig: RefCounted,sk: Skeleton3D) -> String:
	if sk.show_rest_only or not Bounds.final_pose(sk).is_empty(): return "Turn body Physics off before using imported hair motion."
	if sk.get_bone_count() != 69: return "The imported skeleton changed; its hair preview was stopped."
	for index in range(sk.get_bone_count()):
		if not sk.is_bone_enabled(index): return "Imported hair currently needs all source joints enabled."
	var pending: Array = [rig.root]
	var modifiers: Array = []
	var visited := 0
	while not pending.is_empty() and visited < 10000:
		var node: Node = pending.pop_back()
		visited += 1
		if node is PhysicalBone3D: return "Turn body Physics off before using imported hair motion."
		if node is SkeletonModifier3D: modifiers.append(node)
		pending.append_array(node.get_children(true))
	if not pending.is_empty() or modifiers.size() > 1: return "This model already has a different live skeleton modifier."
	if modifiers.size() == 1:
		var modifier: Node = modifiers[0]
		if str(modifier.get_class()) != "PhysicalBoneSimulator3D" or modifier.get_script() != null or modifier.get_parent() != sk or not sk.get_children(true).has(modifier) or sk.get_children(false).has(modifier): return "This model already has a different live skeleton modifier."
		if not modifier.has_method("is_simulating_physics"): return "This skeleton modifier cannot be checked for imported hair."
		var simulating = modifier.call("is_simulating_physics")
		if not simulating is bool or simulating != false: return "Turn body Physics off before using imported hair motion."
	return ""

static func expected_parameters(index: int) -> Dictionary:
	if not index in SELECTED_NATIVE_IDS: return {}
	var p: Dictionary = Math.defaults()
	if index in STIFF_NATIVE_IDS: p.yaw_stiffness = 100.0; p.pitch_stiffness = 100.0
	return p

static func rule_parameters(rule: Dictionary,index: int) -> Dictionary:
	# Full Bindings.resolve has already authenticated all29 F32 words/prefix+wire.
	# This source-specific profile separately freezes the active math inputs.
	if not index in SELECTED_NATIVE_IDS or rule.get("native_bone_index") != index or rule.get("native_parent_index") != EXPECTED_PARENTS[index]: return {"error":"The imported hair owner profile changed."}
	var expected_prefix: String = PREFIX_SHA if index in STIFF_NATIVE_IDS else CHAIN_PREFIX_SHA
	if rule.get("raw_rule_flags") != Math.FLAGS or rule.get("unknown_rule_flag_bits") != 0 or not rule.get("binary_provenance") is Dictionary or rule.binary_provenance.get("prefix_sha256") != expected_prefix or not rule.get("parameters") is Dictionary: return {"error":"Imported hair coefficients do not match the supported profile."}
	var expected: Dictionary = expected_parameters(index)
	var overrides: Dictionary = {}
	for key in expected:
		if key == "raw_rule_flags": continue
		var value: Variant = rule.parameters.get(key)
		if not (value is int or value is float) or not is_finite(float(value)) or float(value) != float(expected[key]): return {"error":"The imported hair active coefficients changed."}
		overrides[key] = value
	return Math.parameters(overrides)

static func create(rig: RefCounted) -> Dictionary:
	if not offered(rig): return {"error":"Imported hair motion is not qualified for this model. Use the loose-part setup instead."}
	var bound: RefCounted = Bindings.resolve(rig)
	if bound.status != "bound_inactive" or bound.bindings.size() != 69 or bound.rule_owner_ids.size() != 49 or bound.source_sha256 != rig.data.get("sha256") or bound.jiggle_wire_sha256 != WIRE_SHA: return {"error":"The imported hair bindings changed. Reopen the original model or use loose-part setup."}
	var sk: Skeleton3D = bound.bindings[SELECTED_NATIVE].skeleton
	var error := context_error(rig,sk)
	if not error.is_empty(): return {"error":error}
	if rig.order.size() != 69 or rig.bones.size() != 69: return {"error":"The imported hair binding inventory is incomplete."}
	var scale_token = rig.data.get("scale")
	if not (scale_token is int or scale_token is float) or not is_finite(float(scale_token)) or float(scale_token) <= 0.0: return {"error":"Imported hair needs a positive authored scale."}
	var prefix := frame64(sk.global_transform)
	if prefix.has("error"): return prefix
	var candidate = new()
	candidate.actor = rig; candidate.resolution = bound; candidate._skeleton = sk
	candidate._source_path = str(rig.data.source)
	candidate._prefix_scale = prefix.scale; candidate._authored_scale_token = float(scale_token)
	for index in range(69):
		var binding: RefCounted = bound.bindings[index]
		var id: String = binding.has_id
		if binding.skeleton != sk or not rig.bones.has(id) or rig.bones[id].skeleton != sk or rig.bones[id].index != binding.skeleton_bone_index: candidate.dispose(); return {"error":"The imported hair skeleton bindings changed."}
		var parent_index: int = binding.native_parent_index
		var expected_parent: String = "@root" if parent_index < 0 else str(bound.by_native[parent_index])
		if rig.parent_id(id) != expected_parent: candidate.dispose(); return {"error":"The imported hair parent mapping changed."}
		var base := frame64(rig.bones[id].base)
		if base.has("error"): candidate.dispose(); return base
		candidate._base_scales[id] = float(base.scale)
		candidate._bone_specs[id] = {"parent":null if parent_index < 0 else bound.by_native[parent_index],"base":{"origin":base.goal.base.duplicate(true),"basis":base.rotation.duplicate(true),"scale":float(base.scale)}}
	for index in SELECTED_NATIVE_IDS:
		var binding: RefCounted = bound.bindings[index]
		if binding.native_parent_index != EXPECTED_PARENTS[index]: candidate.dispose(); return {"error":"The imported hair parent profile changed."}
		var children: Array = []
		for child in range(69):
			if bound.bindings[child].native_parent_index == index: children.append(child)
		var expected: Array = EXPECTED_CHILDREN[index]
		if children != expected: candidate.dispose(); return {"error":"The imported hair subtree no longer matches its bounded profile."}
		var rule: Dictionary = {}
		for entry in rig.data.metadata.native_parameters.native_parameters.source_jiggle.rules:
			if entry.native_bone_index == index: rule = entry
		var parameters: Dictionary = rule_parameters(rule,index)
		if parameters.has("error"): candidate.dispose(); return parameters
		candidate._parameters[binding.has_id] = parameters.parameters.duplicate(true)
		candidate.chains.append({"ids":[binding.has_id],"source":{"joints":[{"binding":{"kind":"bone","id":binding.has_id}}]}})

	# All69 imported bindings/base frames are still authenticated above. Only the
	# exact complete ancestor closure enters the unchanged scalar step core.
	var keep := {}
	for native_index in SELECTED_NATIVE_IDS:
		var current: Variant = bound.by_native[native_index]
		var seen := {}
		while current != null:
			if seen.has(current) or not candidate._bone_specs.has(current): candidate.dispose(); return {"error":"The imported hair ancestor closure changed."}
			seen[current] = true; keep[current] = true
			current = candidate._bone_specs[current].parent
	var observed_native := []
	for native_index in range(69):
		var id: String = bound.by_native[native_index]
		if keep.has(id):
			observed_native.append(native_index)
			candidate._solver_bone_specs[id] = candidate._bone_specs[id].duplicate(true)
	if observed_native != EXPECTED_CAPTURE_NATIVE_IDS: candidate.dispose(); return {"error":"The imported hair ancestor profile changed."}
	candidate._capture_configuration_stamp = var_to_bytes([candidate._bone_specs,candidate._solver_bone_specs,candidate._base_scales])

	# Both runners own independent configuration/state. Only the authoritative
	# runner is committed; the trial absorbs all math/output failures.
	var primary := Chains.create(candidate._solver_bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
	if primary.has("error"): candidate.dispose(); return primary
	var trial := Chains.create(candidate._solver_bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
	if trial.has("error"): candidate.dispose(); return trial
	candidate._chain = primary.actor; candidate._trial = trial.actor
	var guard := Chains.create(candidate._bone_specs,candidate._parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
	if guard.has("error"): candidate.dispose(); return guard
	candidate._baseline_guard = guard.actor
	candidate._baseline_guard_stamp = candidate.configuration_stamp(candidate._baseline_guard)
	var initial := candidate.capture_baseline()
	if initial.has("error"): candidate.dispose(); return initial
	var seeded: Dictionary = candidate._chain.reset(initial.locals,initial.prefix)
	if seeded.has("error"): candidate.dispose(); return seeded
	seeded = candidate._trial.reset(initial.locals,initial.prefix)
	if seeded.has("error"): candidate.dispose(); return seeded
	candidate._size_tokens = candidate._chain.snapshot().sizes.duplicate(true)
	candidate._configuration_stamp = candidate.configuration_stamp(candidate._chain)
	if candidate.configuration_stamp(candidate._trial) != candidate._configuration_stamp: candidate.dispose(); return {"error":"The imported hair trial configuration differs."}
	var source := FileAccess.open(candidate._source_path,FileAccess.READ)
	if source == null: candidate.dispose(); return {"error":"The imported hair source is unavailable."}
	candidate._source_length = source.get_length()
	candidate._source_header = source.get_buffer(12)
	source.close()
	if candidate._source_header.size() != 12: candidate.dispose(); return {"error":"The imported hair source header is unavailable."}
	candidate._source_modified = FileAccess.get_modified_time(candidate._source_path)
	candidate._binding_stamp = candidate.binding_stamp()
	if candidate._binding_stamp.is_empty(): candidate.dispose(); return {"error":"The imported hair binding inventory is incomplete."}
	# The public chain/airflow inventory is mutable for legacy callers. Freeze
	# exact order, ids and source.joints.binding as a separate admission stamp.
	if candidate.chains.size() != SELECTED_NATIVE_IDS.size(): candidate.dispose(); return {"error":"The imported hair airflow inventory is incomplete."}
	candidate._chain_inventory_stamp = var_to_bytes(candidate.chains)
	candidate._alive = true
	return {"runner":candidate}

func binding_stamp() -> PackedByteArray:
	# Only immutable imported bindings/provenance belong here. Authored pose,
	# animation, world placement and solver state are deliberately absent.
	if actor.order.size() != 69 or actor.bones.size() != 69: return PackedByteArray()
	var metadata = actor.data.get("metadata",{})
	var report = metadata.get("native_parameters") if metadata is Dictionary else null
	var values: Array = [actor.order,actor.root.get_meta("has_source_bones",{}),report]
	for index in range(_skeleton.get_bone_count()):
		values.append([_skeleton.get_bone_name(index),_skeleton.get_bone_parent(index),_skeleton.get_bone_rest(index)])
	for id in actor.order:
		var info = actor.bones.get(id)
		if not info is Dictionary: return PackedByteArray()
		var sk = info.get("skeleton")
		values.append([id,info.get("index"),info.get("name"),info.get("path"),info.get("base"),sk.get_instance_id() if is_instance_valid(sk) and sk is Skeleton3D else 0])
	return var_to_bytes(values)

func airflow_error() -> String:
	# Shared internal ABI with SecondaryLive: call before reading public chains.
	if not _alive or chains.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(chains) != _chain_inventory_stamp: return "The imported hair chain or airflow bindings changed; its preview was stopped."
	return ""

func configuration_stamp(value: RefCounted) -> PackedByteArray:
	# Internal immutable configuration only, never solver states or authored data.
	return var_to_bytes([value._bones,value._order,value._parameters,value._source_scale,value._gravity])

func state_error(snapshot: Dictionary, expected_tick: int) -> String:
	if typeof(snapshot.get("active")) != TYPE_BOOL or snapshot.active != true or typeof(snapshot.get("tick")) != TYPE_INT or snapshot.tick != expected_tick or not snapshot.get("states") is Dictionary or not snapshot.get("sizes") is Dictionary: return "The imported hair simulation inventory changed."
	if snapshot.states.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(snapshot.sizes) != var_to_bytes(_size_tokens): return "The imported hair simulation size inventory changed."
	for id in _parameters:
		var state = snapshot.states.get(id)
		if not state is Dictionary or state.size() != 2 or not Math.vector_ok(state.get("tip")) or not Math.vector_ok(state.get("velocity")): return "The imported hair simulation state changed."
	return ""

func capture_baseline() -> Dictionary:
	# Fresh synchronous same-call snapshot, never a previous-tick authored pose.
	if var_to_bytes([_bone_specs,_solver_bone_specs,_base_scales]) != _capture_configuration_stamp: return {"error":"The imported hair capture configuration changed."}
	if configuration_stamp(_baseline_guard) != _baseline_guard_stamp: return {"error":"The imported hair baseline guard configuration changed."}
	var raw_prefix: Transform3D = _skeleton.global_transform
	var observed_prefix := frame64(raw_prefix)
	if observed_prefix.has("error"): return observed_prefix
	if absf(float(observed_prefix.scale)-_prefix_scale) > EPS*_prefix_scale: return {"error":"Turn imported hair off before resizing the model or its parent."}
	var prefix := {"origin":observed_prefix.goal.base.duplicate(true),"basis":observed_prefix.rotation.duplicate(true),"scale":_prefix_scale}
	var locals := {}
	var raw_locals := {}
	var raw_worlds := {}
	var mapped_worlds := {}
	for id in _bone_specs:
		var info: Dictionary = actor.bones[id]
		var local: Transform3D = _skeleton.get_bone_pose(info.index)
		var actual: Transform3D = actor.bone_transform(id)
		var mapped: Dictionary = frame64(local)
		if mapped.has("error"): return mapped
		var actual_frame: Dictionary = frame64(actual)
		if actual_frame.has("error"): return actual_frame
		var stable: float = _base_scales[id]
		if absf(float(mapped.scale)-stable) > EPS*stable: return {"error":"The imported hair local scale changed; turn its preview off."}
		raw_locals[id] = local; raw_worlds[id] = actual; mapped_worlds[id] = actual_frame
		if true:
			locals[id] = {"origin":mapped.goal.base.duplicate(true),"basis":mapped.rotation.duplicate(true),"scale":stable}
	# Retain actual Transform3D parent/local closure for every one of69 bones.
	for id in _bone_specs:
		var parent: Variant = _bone_specs[id].parent
		var parent_world: Transform3D = raw_prefix if parent == null else raw_worlds[parent]
		var actual: Transform3D = raw_worlds[id]
		var composed: Transform3D = parent_world*raw_locals[id]
		if not composed.origin.is_finite() or not composed.basis.is_finite(): return {"error":"The imported hair parent pose changed."}
		var size: float = mapped_worlds[id].scale
		var guard: float = EPS*maxf(1.0,size)
		if composed.origin.distance_to(actual.origin) > EPS*size: return {"error":"The imported hair parent pose changed."}
		for i in range(3):
			for j in range(3):
				if absf(composed.basis[i][j]-actual.basis[i][j]) > guard: return {"error":"The imported hair parent pose changed."}
	# Every local was just validated by unchanged frame64/Math.goal above.
	# Its scale is the stamped base token admitted by the full69 guard config.
	# Keep the prefix check and every unchanged compose/result-frame check;
	# skip only the second identical69-local input validation pass.
	var prefix_error: String = Chains.frame_error(prefix)
	if not prefix_error.is_empty(): return {"error":prefix_error}
	var full_worlds := {}
	for id in _baseline_guard._order:
		var parent: Variant = _baseline_guard._bones[id].parent
		var parent_world: Dictionary = prefix if parent == null else full_worlds[parent]
		var made: Dictionary = Chains.compose(parent_world,locals[id])
		if made.has("error"): return made
		full_worlds[id] = made.frame
	var worlds: Dictionary = {"worlds":full_worlds}
	if worlds.has("error"): return worlds
	for id in _bone_specs:
		var actual: Dictionary = mapped_worlds[id]
		var target: Dictionary = worlds.worlds[id]
		if absf(float(actual.scale)-float(target.scale)) > EPS*float(target.scale): return {"error":"The imported hair world scale changed; turn its preview off."}
		var wanted: Array = target.origin
		var actual_raw: Transform3D = raw_worlds[id]
		if actual_raw.origin.distance_to(Vector3(wanted[0],wanted[1],wanted[2])) > EPS*float(target.scale): return {"error":"The imported hair authored parent chain differs from its supported profile."}
		for i in range(3):
			for j in range(3):
				if absf(float(actual.rotation[i][j])-float(target.basis[i][j])) > EPS: return {"error":"The imported hair authored orientation differs from its supported profile."}
	var selected_locals := {}
	for id in _solver_bone_specs: selected_locals[id] = locals[id]
	return {"locals":selected_locals,"prefix":prefix}

func step(delta: float,wind: Vector3,forces: Array = []) -> Dictionary:
	var processing_started: int = Time.get_ticks_usec()
	if not _alive or not is_instance_valid(actor.root) or not is_instance_valid(_skeleton) or not offered(actor) or actor.data.get("source") != _source_path: return {"error":"The imported hair source changed; its preview was stopped."}
	if not is_finite(delta) or absf(delta-Math.DT) > 1e-9: return {"error":"Imported hair needs the fixed 120 Hz simulation clock."}
	if not FileAccess.file_exists(_source_path) or FileAccess.get_modified_time(_source_path) != _source_modified or binding_stamp() != _binding_stamp: return {"error":"The imported source or joint setup changed; its hair preview was stopped."}
	var source := FileAccess.open(_source_path,FileAccess.READ)
	if source == null: return {"error":"The imported hair source is unavailable."}
	var source_length := source.get_length()
	var source_header := source.get_buffer(12)
	source.close()
	if source_length != _source_length or source_header != _source_header: return {"error":"The imported hair source changed; its preview was stopped."}
	var error := context_error(actor,_skeleton)
	if not error.is_empty(): return {"error":error}
	if chains.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(chains) != _chain_inventory_stamp: return {"error":"The imported hair chain or airflow bindings changed; its preview was stopped."}
	var scale_token = actor.data.get("scale")
	if not (scale_token is int or scale_token is float) or not is_finite(float(scale_token)) or float(scale_token) != _authored_scale_token: return {"error":"Turn imported hair off before resizing the model."}
	if not forces.is_empty() and forces.size() != SELECTED_NATIVE_IDS.size(): return {"error":"Imported hair needs one airflow input per selected joint."}
	var accelerations := {}
	var authored_positions := {}
	for i in range(SELECTED_NATIVE_IDS.size()):
		var index: int = SELECTED_NATIVE_IDS[i]
		var id: String = resolution.by_native[index]
		var binding: RefCounted = resolution.bindings[index]
		if not actor.bones.has(id) or actor.bones[id].skeleton != _skeleton or actor.bones[id].index != binding.skeleton_bone_index or not _skeleton.is_bone_enabled(binding.skeleton_bone_index) or actor.parent_id(id) != resolution.by_native[EXPECTED_PARENTS[index]]: return {"error":"The imported hair binding changed; its preview was stopped."}
		var force = wind if forces.is_empty() else forces[i]
		if not force is Vector3 or not force.is_finite() or force.length() > 1000000.0: return {"error":"Imported hair received an invalid airflow input."}
		accelerations[id] = vector64(force)
		if not actor.live_pose is Dictionary and _skeleton.get_bone_pose(binding.skeleton_bone_index).origin != actor.bones[id].base.origin: return {"error":"Imported hair needs a fresh authored pose baseline before stepping."}
		var authored: Dictionary = actor.live_pose.get(id,Model.identity()) if actor.live_pose is Dictionary else Model.identity()
		if not authored.get("position") is Array or authored.position.size() != 3: return {"error":"The imported hair authored translation is incomplete."}
		for value in authored.position:
			if not (value is int or value is float) or not is_finite(float(value)): return {"error":"The imported hair authored translation is invalid."}
		authored_positions[id] = authored.position.duplicate(true)
	# Snapshot copies include every rule state and exact size/tick/active status.
	# The two configurations were constructed independently from immutable specs.
	var committed: Dictionary = _chain.snapshot()
	if configuration_stamp(_chain) != _configuration_stamp or configuration_stamp(_trial) != _configuration_stamp: return {"error":"The imported hair simulation configuration changed."}
	var invalid := state_error(committed,_tick)
	if not invalid.is_empty(): return {"error":invalid}
	var baseline := capture_baseline()
	if baseline.has("error"): return baseline
	_trial._states = committed.states.duplicate(true)
	_trial._sizes = committed.sizes.duplicate(true)
	_trial._tick = int(committed.tick); _trial._active = true
	var solved: Dictionary = _trial.step(_tick+1,baseline.locals,baseline.prefix,accelerations)
	if solved.has("error"): return solved
	invalid = state_error(_trial.snapshot(),_tick+1)
	if not invalid.is_empty(): return {"error":invalid}
	if not solved.get("delta_bases") is Dictionary or solved.delta_bases.size() != SELECTED_NATIVE_IDS.size(): return {"error":"The imported hair solver returned an incomplete pose."}
	var pose := {}
	for index in SELECTED_NATIVE_IDS:
		var id: String = resolution.by_native[index]
		if not solved.delta_bases.has(id): return {"error":"The imported hair solver missed a selected joint."}
		var check_goal := Math.goal([0.0,0.0,0.0],solved.delta_bases[id])
		if check_goal.has("error"): return check_goal
		var q: Quaternion = basis64(solved.delta_bases[id]).get_rotation_quaternion().normalized()
		if not is_finite(q.x) or not is_finite(q.y) or not is_finite(q.z) or not is_finite(q.w): return {"error":"The imported hair solver returned an invalid rotation."}
		pose[id] = {"position":authored_positions[id].duplicate(true),"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	# This swap is the only state commit. Failure above leaves authoritative
	# states/sizes/tick/status, authored data and visual overlays untouched.
	var previous: RefCounted = _chain
	_chain = _trial; _trial = previous; _tick += 1
	var processing_elapsed: int = maxi(0,Time.get_ticks_usec()-processing_started)
	processing_samples += 1; processing_total_usec += processing_elapsed; processing_max_usec = maxi(processing_max_usec,processing_elapsed)
	return {"pose":pose}

func dispose() -> void:
	_alive = false
	if _chain: _chain.stop(); _chain = null
	if _trial: _trial.stop(); _trial = null
	if _baseline_guard: _baseline_guard.stop(); _baseline_guard = null
	_baseline_guard_stamp.clear(); _capture_configuration_stamp.clear(); _solver_bone_specs.clear()
	_parameters.clear(); _bone_specs.clear(); _base_scales.clear(); _size_tokens.clear(); _configuration_stamp.clear()
	_binding_stamp.clear(); _source_header.clear(); _chain_inventory_stamp.clear(); chains.clear()
	_tick = 0; resolution = null; actor = null; _skeleton = null

func active() -> bool:
	return _alive
