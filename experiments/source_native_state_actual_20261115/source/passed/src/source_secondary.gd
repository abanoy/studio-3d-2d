extends RefCounted
# Imported motion is a bounded HAS backend, separate from the unchanged raw
# source report. The first qualified profile drives FrontHair1 only.
const Math = preload("res://src/source_jiggle_math.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Model = preload("res://src/model.gd")
const Bounds = preload("res://src/pose_bounds.gd")
const GLB_SHA := "4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"
const WIRE_SHA := "34230c89c7cda4417a0f142b375f26fbb5cf15a7faf4d98b5424acd0bec621c2"
const PREFIX_SHA := "945d7fd433ddba7f7e8f90cb1cb2c2e7d4c1e26005684ac4a330b23a3691a3fd"
const SOURCE_SCALE := 0.01905
const EPS := 0.00002
const SELECTED_NATIVE := 8
var actor: RefCounted
var resolution: RefCounted
var chains: Array = []
var _source_path := ""
var _skeleton: Skeleton3D
var _parameters: Dictionary = {}
var _state: Dictionary = {}
var _scale := 1.0
var _tick := 0
var _alive := false
var _binding_stamp := PackedByteArray()
var _source_modified := 0
var _source_length := 0
var _source_header := PackedByteArray()

static func offered(rig: RefCounted) -> bool:
	# UI capability hint only. Full source hashing/binding validation happens at
	# creation, never once per render/physics tick. Explicit helpers take priority.
	if rig == null or not is_instance_valid(rig.root) or rig.data.get("sha256") != GLB_SHA: return false
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
	return bones is Array and bones.size() == 69 and rules is Array and rules.size() == 49 and crosswalk.get("profile") == Bindings.PROFILE and crosswalk.get("glb_sha256") == GLB_SHA and crosswalk.get("jiggle_wire_sha256") == WIRE_SHA and jiggle.get("applied") is bool and jiggle.applied == false and jiggle.get("full_native_rule_layout_verified") is bool and jiggle.full_native_rule_layout_verified == false

static func anchors(rig: RefCounted) -> Array:
	if not offered(rig): return []
	# The importer supplies the numeric glTF-node/HAS identity; never infer it
	# from a display label. This is only for aiming; create() authenticates it.
	var report: Dictionary = rig.data.metadata.native_parameters.native_parameters.source_export_crosswalk
	var mapping = rig.root.get_meta("has_source_bones",{})
	if not mapping is Dictionary: return []
	for row in report.bones:
		if row is Dictionary and row.get("native_index") == SELECTED_NATIVE:
			var node_index = row.get("gltf_node_index")
			if not (node_index is int or node_index is float) or not is_finite(float(node_index)) or float(node_index) != floor(float(node_index)): return []
			var id = mapping.get(int(node_index),"")
			if id is String and rig.bones.has(id): return [{"kind":"bone","id":id}]
	return []

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

static func create(rig: RefCounted) -> Dictionary:
	if not offered(rig): return {"error":"Imported hair motion is not qualified for this model. Use the loose-part setup instead."}
	var bound: RefCounted = Bindings.resolve(rig)
	if bound.status != "bound_inactive" or bound.bindings.size() != 69 or bound.rule_owner_ids.size() != 49 or bound.source_sha256 != GLB_SHA or bound.jiggle_wire_sha256 != WIRE_SHA: return {"error":"The imported hair bindings changed. Reopen the original model or use loose-part setup."}
	var binding: RefCounted = bound.bindings[SELECTED_NATIVE]
	var sk: Skeleton3D = binding.skeleton
	if binding.native_parent_index != 7 or not sk.is_bone_enabled(binding.skeleton_bone_index): return {"error":"The imported front-hair joint is unavailable."}
	for index in range(sk.get_bone_count()):
		if not sk.is_bone_enabled(index): return {"error":"Imported hair currently needs all source joints enabled."}
		if sk.get_bone_parent(index) == binding.skeleton_bone_index: return {"error":"The imported front-hair joint no longer matches its leaf profile."}
	var error := context_error(rig,sk)
	if not error.is_empty(): return {"error":error}
	var native: Dictionary = rig.data.metadata.native_parameters.native_parameters
	var rule: Dictionary = {}
	for entry in native.source_jiggle.rules:
		if entry.native_bone_index == SELECTED_NATIVE: rule = entry
	if rule.is_empty() or rule.raw_rule_flags != Math.FLAGS or rule.unknown_rule_flag_bits != 0 or rule.binary_provenance.prefix_sha256 != PREFIX_SHA: return {"error":"Imported front-hair coefficients do not match the supported profile."}
	var mapped := frame64(rig.bone_transform(binding.has_id))
	if mapped.has("error"): return mapped
	var overrides := {}
	for key in Math.defaults():
		if key != "raw_rule_flags": overrides[key] = rule.parameters[key]
	# GLB positions already contain source conversion. Scale native rule length
	# and acceleration once; the transient HAS world input is already in metres.
	var factor: float = SOURCE_SCALE*float(mapped.scale)
	overrides.length = float(overrides.length)*factor
	overrides.tip_mass = float(overrides.tip_mass)*factor
	var parameters := Math.parameters(overrides)
	if parameters.has("error"): return parameters
	var candidate = new()
	candidate.actor = rig
	candidate.resolution = bound
	candidate._skeleton = sk
	candidate._source_path = str(rig.data.source)
	candidate._parameters = parameters.parameters
	candidate._scale = mapped.scale
	candidate._state = {"tip":Math.tip(mapped.goal,parameters.parameters),"velocity":[0.0,0.0,0.0]}
	candidate.chains = [{"ids":[binding.has_id],"source":{"joints":[{"binding":{"kind":"bone","id":binding.has_id}}]}}]
	var source := FileAccess.open(candidate._source_path,FileAccess.READ)
	if source == null: return {"error":"The imported hair source is unavailable."}
	candidate._source_length = source.get_length()
	candidate._source_header = source.get_buffer(12)
	source.close()
	if candidate._source_header.size() != 12: return {"error":"The imported hair source header is unavailable."}
	candidate._source_modified = FileAccess.get_modified_time(candidate._source_path)
	candidate._binding_stamp = candidate.binding_stamp()
	if candidate._binding_stamp.is_empty(): return {"error":"The imported hair binding inventory is incomplete."}
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

func step(delta: float,wind: Vector3,forces: Array = []) -> Dictionary:
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
	var id: String = chains[0].ids[0]
	if not actor.bones.has(id) or actor.bones[id].skeleton != _skeleton or actor.bones[id].index != resolution.bindings[SELECTED_NATIVE].skeleton_bone_index or not _skeleton.is_bone_enabled(actor.bones[id].index) or actor.parent_id(id) != resolution.by_native[7]: return {"error":"The imported hair binding changed; its preview was stopped."}
	var mapped := frame64(actor.bone_transform(id))
	if mapped.has("error"): return mapped
	if absf(float(mapped.scale)-_scale) > EPS*_scale: return {"error":"Turn imported hair off before resizing the model."}
	var force: Vector3 = forces[0] if forces.size() == 1 else wind
	if not force.is_finite() or force.length() > 1000000.0 or forces.size() > 1: return {"error":"Imported hair received an invalid airflow input."}
	var solved := Math.solve_one(_parameters,mapped.goal,_state,vector64(force),[0.0,-1.0,0.0])
	if solved.has("error"): return solved
	var info: Dictionary = actor.bones[id]
	var parent: String = actor.parent_id(id)
	if parent == "@root": return {"error":"The imported hair parent changed."}
	var parent_world: Transform3D = actor.bone_transform(parent)
	var local: Transform3D = _skeleton.get_bone_pose(info.index)
	var current: Transform3D = actor.bone_transform(id)
	var closure: Transform3D = parent_world*local
	if closure.origin.distance_to(current.origin) > EPS*_scale: return {"error":"The imported hair parent pose changed."}
	for i in range(3):
		for j in range(3):
			if absf(closure.basis[i][j]-current.basis[i][j]) > EPS*maxf(1.0,_scale): return {"error":"The imported hair parent pose changed."}
	var pf := frame64(parent_world)
	var bf := frame64(info.base)
	if pf.has("error"): return pf
	if bf.has("error"): return bf
	var desired := frame64(Transform3D(basis64(solved.basis),current.origin))
	if desired.has("error"): return desired
	var q: Quaternion = (basis64(bf.rotation).get_rotation_quaternion().normalized().inverse()*basis64(pf.rotation).get_rotation_quaternion().normalized().inverse()*basis64(desired.rotation).get_rotation_quaternion().normalized()).normalized()
	var authored: Dictionary = actor.live_pose.get(id,Model.identity()) if actor.live_pose is Dictionary else Model.identity()
	var pose := {id:{"position":authored.position.duplicate(true),"rotation_xyzw":[q.x,q.y,q.z,q.w]}}
	_state = solved.state.duplicate(true)
	_tick += 1
	return {"pose":pose}

func dispose() -> void:
	_alive = false
	_state.clear()
	_parameters.clear()
	_binding_stamp.clear()
	_source_header.clear()
	chains.clear()
	resolution = null
	actor = null
	_skeleton = null

func active() -> bool:
	return _alive
