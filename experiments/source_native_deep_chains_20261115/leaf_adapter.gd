extends RefCounted
# UNPARSED/UNRUN native8 readiness adapter. No registration or product activation.
# leaf_candidate.gd must be an exact copy of the independently executed math file.
const Math = preload("res://leaf_candidate.gd")
const Model = preload("res://src/model.gd")
const EPS := 0.00002
const SOURCE_SCALE := 0.01905

static func vector64(value: Vector3) -> Array:
	return [float(value.x),float(value.y),float(value.z)]

static func basis_from64(columns: Array) -> Basis:
	return Basis(Vector3(columns[0][0],columns[0][1],columns[0][2]),Vector3(columns[1][0],columns[1][1],columns[1][2]),Vector3(columns[2][0],columns[2][1],columns[2][2]))

static func frame64(value: Transform3D) -> Dictionary:
	if not value.origin.is_finite() or not value.basis.is_finite() or value.basis.determinant() <= 0.0: return {"error":"Finite positive world transform required"}
	var raw: Array = [vector64(value.basis.x),vector64(value.basis.y),vector64(value.basis.z)]
	var scales: Array = [Math.v_length(raw[0]),Math.v_length(raw[1]),Math.v_length(raw[2])]
	var size: float = scales[0]
	if not is_finite(size) or size <= 0.00001: return {"error":"Degenerate world size"}
	for i in range(3):
		if not is_finite(scales[i]) or absf(scales[i]-size) > EPS*size: return {"error":"Nonuniform world transform outside native leaf profile"}
	var unit_columns: Array = [Math.v_mul(raw[0],1.0/scales[0]),Math.v_mul(raw[1],1.0/scales[1]),Math.v_mul(raw[2],1.0/scales[2])]
	for pair in [[0,1],[0,2],[1,2]]:
		if absf(Math.v_dot(unit_columns[pair[0]],unit_columns[pair[1]])) > EPS: return {"error":"Sheared world transform outside native leaf profile"}
	# Scalar64 Gram-Schmidt is an explicit float32 boundary adapter, not a claim
	# that raw Basis columns meet the mathematical candidate's1e-9 goal domain.
	var x: Array = unit_columns[0]
	var yr := Math.normalized(Math.v_sub(raw[1],Math.v_mul(x,Math.v_dot(x,raw[1]))))
	if yr.has("error"): return yr
	var y: Array = yr.value
	var z := Math.v_cross(x,y)
	if Math.v_dot(z,unit_columns[2]) <= 0.0: return {"error":"Reflected boundary orientation"}
	var columns: Array = [x,y,z]
	var reconstruction_error := 0.0
	for i in range(3):
		for j in range(3): reconstruction_error = maxf(reconstruction_error,absf(raw[i][j]/size-columns[i][j]))
	if reconstruction_error > EPS: return {"error":"World basis correction exceeds preregistered2e-5"}
	var made := Math.goal(vector64(value.origin),columns)
	if made.has("error"): return {"error":"Scalar64 boundary failed strict mathematical goal validation"}
	return {"goal":made.goal,"rotation":columns,"scale":size,"correction_max":reconstruction_error}

static func transform_error(actual: Transform3D, expected: Transform3D) -> float:
	var error := actual.origin.distance_to(expected.origin)
	for i in range(3):
		for j in range(3): error = maxf(error,absf(actual.basis[i][j]-expected.basis[i][j]))
	return error

static func parameters_from_rule(rule: Dictionary, world_scale: float) -> Dictionary:
	if float(rule.get("native_bone_index",-1)) != 8.0 or float(rule.get("raw_rule_flags",-1)) != 49.0 or float(rule.get("unknown_rule_flag_bits",-1)) != 0.0 or not rule.get("parameters") is Dictionary: return {"error":"Exact retained native8 flags0x31 required"}
	var values: Dictionary = rule.parameters
	var overrides := {}
	for key in Math.defaults():
		if key == "raw_rule_flags": continue
		if not values.has(key): return {"error":"Missing native parameter "+key}
		overrides[key] = values[key]
	# GLB/rest positions already contain SOURCE_SCALE. Only native rule length
	# and acceleration magnitude need the native-to-world size factor here.
	var factor := SOURCE_SCALE*world_scale
	overrides.length = float(values.length)*factor
	overrides.tip_mass = float(values.tip_mass)*factor
	var made := Math.parameters(overrides)
	if made.has("error"): return made
	return {"parameters":made.parameters,"unit_factor":factor}

static func overlay(actor: RefCounted, id: String, authored: Dictionary, desired_columns: Array) -> Dictionary:
	if not actor.bones.has(id): return {"error":"Missing qualified leaf bone"}
	var info: Dictionary = actor.bones[id]
	var parent: String = actor.parent_id(id)
	if parent == "@root": return {"error":"This bounded native8 profile requires its measured skeleton parent"}
	var parent_world: Transform3D = actor.bone_transform(parent)
	var local: Transform3D = info.skeleton.get_bone_pose(info.index)
	var current: Transform3D = actor.bone_transform(id)
	var parent_frame := frame64(parent_world)
	var base_frame := frame64(info.base)
	var current_frame := frame64(current)
	if parent_frame.has("error"): return parent_frame
	if base_frame.has("error"): return base_frame
	if current_frame.has("error"): return current_frame
	# This independently guards the actual Skeleton pose composition. Refuse
	# rather than inventing a rest correction if the observed contract differs.
	var closure := transform_error(parent_world*local,current)
	if closure > EPS*maxf(1.0,float(current_frame.scale)): return {"error":"Actual parent-world/local-pose composition differs"}
	var desired := basis_from64(desired_columns)
	var desired_frame := frame64(Transform3D(desired,current.origin))
	if desired_frame.has("error"): return desired_frame
	var qb := basis_from64(base_frame.rotation).get_rotation_quaternion().normalized()
	var qp := basis_from64(parent_frame.rotation).get_rotation_quaternion().normalized()
	var qd := basis_from64(desired_frame.rotation).get_rotation_quaternion().normalized()
	# Model.apply sets pose rotation=base_rotation*delta, and the guarded
	# Skeleton contract makes world rotation=parent_world*pose_rotation.
	var delta: Quaternion = (qb.inverse()*qp.inverse()*qd).normalized()
	var result: Dictionary = authored.duplicate(true)
	var original: Dictionary = authored.get(id,Model.identity())
	result[id] = {"position":original.position.duplicate(true),"rotation_xyzw":[delta.x,delta.y,delta.z,delta.w]}
	return {"pose":result,"parent_closure_error":closure,"basis_adapter_error":maxf(float(current_frame.correction_max),maxf(float(parent_frame.correction_max),float(base_frame.correction_max)))}
