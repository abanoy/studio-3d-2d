extends RefCounted
# Bounded Source0x31 mathematics. Scalar64 state; fixed120Hz HAS clock.
# Qualified synthetic math lives in docs/benchmarks/native_source_readiness_2026-11-15.json.
# This preserves the retained coefficients, not native SDK/client timing parity.
const FLAGS := 0x31
const FIXED_HZ := 120
const DT := 1.0 / 120.0
var _parameters: Dictionary = {}
var _states: Dictionary = {}
var _raw_metadata: Variant = null
var _gravity: Array = [0.0, 0.0, -1.0]
var _tick := 0
var _active := false

static func vector_ok(value: Variant) -> bool:
	if not value is Array or value.size() != 3: return false
	for v in value:
		if not (typeof(v) == TYPE_INT or typeof(v) == TYPE_FLOAT) or not is_finite(float(v)): return false
	return true

static func v_add(a: Array, b: Array) -> Array:
	return [float(a[0])+float(b[0]), float(a[1])+float(b[1]), float(a[2])+float(b[2])]
static func v_sub(a: Array, b: Array) -> Array:
	return [float(a[0])-float(b[0]), float(a[1])-float(b[1]), float(a[2])-float(b[2])]
static func v_mul(a: Array, scale: float) -> Array:
	return [float(a[0])*scale, float(a[1])*scale, float(a[2])*scale]
static func v_dot(a: Array, b: Array) -> float:
	return float(a[0])*float(b[0])+float(a[1])*float(b[1])+float(a[2])*float(b[2])
static func v_cross(a: Array, b: Array) -> Array:
	return [float(a[1])*float(b[2])-float(a[2])*float(b[1]), float(a[2])*float(b[0])-float(a[0])*float(b[2]), float(a[0])*float(b[1])-float(a[1])*float(b[0])]
static func v_length(a: Array) -> float: return sqrt(v_dot(a, a))
static func normalized(a: Array) -> Dictionary:
	var size := v_length(a)
	if not is_finite(size) or size < 1e-12: return {"error":"Degenerate direction outside candidate subset"}
	return {"value":v_mul(a, 1.0/size)}

static func defaults() -> Dictionary:
	return {"length":20.0,"tip_mass":20.0,"yaw_stiffness":50.0,"yaw_damping":5.0,"pitch_stiffness":50.0,"pitch_damping":5.0,"angle_limit":0.7853981852531433,"along_stiffness":100.0,"along_damping":0.0,"raw_rule_flags":FLAGS}

static func parameter_error(p: Dictionary) -> String:
	var expected := defaults()
	if p.size() != expected.size(): return "Exact parameter fields required"
	for key in expected:
		if not p.has(key): return "Missing parameter "+key
	if typeof(p.raw_rule_flags) != TYPE_INT or p.raw_rule_flags != FLAGS: return "Only exact flags0x31 supported"
	for key in p:
		if key == "raw_rule_flags": continue
		var value: Variant = p[key]
		if not (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) or not is_finite(float(value)) or float(value) < 0: return "Invalid parameter "+key
	if p.length < 1e-8 or p.length > 1e5 or p.angle_limit >= PI/2.0: return "Positive bounded length and cone below90degrees required"
	if p.tip_mass > 1e6: return "Mass acceleration outside prototype bound"
	for key in ["yaw_stiffness","pitch_stiffness","yaw_damping","pitch_damping"]:
		if p[key] > 1e4: return "Active coefficient outside prototype bound"
	return ""

static func parameters(overrides: Dictionary = {}) -> Dictionary:
	var p := defaults()
	for key in overrides:
		if not p.has(key): return {"error":"Unknown parameter "+str(key)}
		p[key] = overrides[key]
	var error := parameter_error(p)
	return {"parameters":p} if error.is_empty() else {"error":error}

static func goal_error(goal: Dictionary) -> String:
	if not goal.has("base") or not goal.has("basis") or not vector_ok(goal.base) or not goal.basis is Array or goal.basis.size() != 3: return "Complete mathematical goal required"
	for column in goal.basis:
		if not vector_ok(column): return "Invalid basis column"
	for i in range(3):
		for j in range(3):
			if absf(v_dot(goal.basis[i], goal.basis[j])-(1.0 if i == j else 0.0)) > 1e-9: return "Positive orthonormal mathematical goal required"
	if v_dot(v_cross(goal.basis[0],goal.basis[1]),goal.basis[2]) < 1.0-1e-9: return "Mirrored mathematical goal refused"
	return ""

static func goal(base: Array = [0.0,0.0,0.0], basis: Array = [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]) -> Dictionary:
	var value := {"base":base.duplicate(true),"basis":basis.duplicate(true)}
	var error := goal_error(value)
	return {"goal":value} if error.is_empty() else {"error":error}

static func tip(goal_value: Dictionary, p: Dictionary) -> Array:
	return v_add(goal_value.base,v_mul(goal_value.basis[2],float(p.length)))

static func create(specs: Dictionary, metadata: Variant = null, gravity: Array = [0.0,0.0,-1.0]) -> Dictionary:
	if specs.is_empty() or not vector_ok(gravity) or absf(v_length(gravity)-1.0) > 1e-9: return {"error":"Explicit parameters and unit global gravity required"}
	for key in specs:
		if not key is String or not specs[key] is Dictionary: return {"error":"Named explicit parameter dictionaries required"}
		var error := parameter_error(specs[key])
		if not error.is_empty(): return {"error":error}
	var actor = new()
	actor._parameters = specs.duplicate(true)
	actor._gravity = gravity.duplicate(true)
	actor._raw_metadata = metadata.duplicate(true) if metadata is Dictionary or metadata is Array else metadata
	return {"actor":actor}

func metadata_copy() -> Variant:
	return _raw_metadata.duplicate(true) if _raw_metadata is Dictionary or _raw_metadata is Array else _raw_metadata
func snapshot() -> Dictionary:
	return {"active":_active,"tick":_tick,"states":_states.duplicate(true)}

func _goals_error(goals: Dictionary) -> String:
	if goals.size() != _parameters.size(): return "Exact complete goal set required"
	for key in _parameters:
		if not goals.has(key) or not goals[key] is Dictionary: return "Missing mathematical goal"
		var error := goal_error(goals[key])
		if not error.is_empty(): return error
	return ""

func reset(goals: Dictionary) -> Dictionary:
	var error := _goals_error(goals)
	if not error.is_empty(): return {"error":error}
	var seeded := {}
	var ids := _parameters.keys()
	ids.sort()
	for key in ids:
		var position := tip(goals[key],_parameters[key])
		if not vector_ok(position): return {"error":"Nonfinite initial position"}
		seeded[key] = {"tip":position,"velocity":[0.0,0.0,0.0]}
	_states = seeded
	_tick = 0
	_active = true
	return {"ok":true}

static func solve_one(p: Dictionary, target_goal: Dictionary, state: Dictionary, external: Array, gravity: Array) -> Dictionary:
	var target := tip(target_goal,p)
	var difference := v_sub(target,state.tip)
	var left: Array = target_goal.basis[0]
	var up: Array = target_goal.basis[1]
	var forward: Array = target_goal.basis[2]
	var lateral: float = float(p.yaw_stiffness)*v_dot(left,difference)-float(p.yaw_damping)*v_dot(left,state.velocity)
	var vertical: float = float(p.pitch_stiffness)*v_dot(up,difference)-float(p.pitch_damping)*v_dot(up,state.velocity)
	# Along-axis coefficients remain inactive under flags0x31.
	var acceleration := v_add(v_add(v_mul(left,lateral),v_mul(up,vertical)),v_add(v_mul(gravity,float(p.tip_mass)),external))
	var velocity := v_add(state.velocity,v_mul(acceleration,DT))
	var position := v_add(state.tip,v_mul(velocity,DT))
	var unprojected_position := position.duplicate(true)
	var unprojected_velocity := velocity.duplicate(true)
	var direction: Array = []
	var constrained := false
	if float(p.angle_limit) == 0.0:
		var zero_direction := normalized(forward)
		if zero_direction.has("error"): return zero_direction
		direction = zero_direction.value
		constrained = position != target
	else:
		var initial_direction := normalized(v_sub(position,target_goal.base))
		if initial_direction.has("error"): return initial_direction
		direction = initial_direction.value
		var cosine := clampf(v_dot(direction,forward),-1.0,1.0)
		var angle := acos(cosine)
		if cosine < 0.0: angle = TAU-angle
		constrained = angle > float(p.angle_limit)
		if constrained:
			var toward := normalized(v_sub(target,position))
			if toward.has("error"): return toward
			position = v_sub(target,v_mul(toward.value,float(p.length)*sin(float(p.angle_limit))))
			var corrected_direction := normalized(v_sub(position,target_goal.base))
			if corrected_direction.has("error"): return corrected_direction
			direction = corrected_direction.value
	position = v_add(target_goal.base,v_mul(direction,float(p.length)))
	velocity = v_sub(velocity,v_mul(direction,v_dot(velocity,direction)))
	var left_result := normalized(v_cross(up,direction))
	if left_result.has("error"): return left_result
	var output_left: Array = left_result.value
	var output_up := v_cross(direction,output_left)
	for value in [position,velocity,acceleration,output_left,output_up,direction]:
		if not vector_ok(value): return {"error":"Nonfinite result refused atomically"}
	return {"state":{"tip":position,"velocity":velocity},"basis":[output_left,output_up,direction],"acceleration":acceleration,"unconstrained_tip":unprojected_position,"unconstrained_velocity":unprojected_velocity,"angle_projected":constrained}

func step(next_tick: Variant, goals: Dictionary, external: Variant = {}) -> Dictionary:
	if not _active or typeof(next_tick) != TYPE_INT or next_tick != _tick+1: return {"error":"Sequential integer ticks required; reset on discontinuity"}
	var error := _goals_error(goals)
	if not error.is_empty(): return {"error":error}
	if not external is Dictionary: return {"error":"Explicit acceleration dictionary required"}
	for key in external:
		if not _parameters.has(key): return {"error":"Unknown external rule"}
	var forces := {}
	for key in _parameters:
		var value: Variant = external.get(key,[0.0,0.0,0.0])
		if not vector_ok(value) or v_length(value) > 1e6: return {"error":"Invalid bounded acceleration"}
		forces[key] = value.duplicate(true)
	var results := {}
	var states := {}
	var ids := _parameters.keys()
	ids.sort()
	for key in ids:
		var result := solve_one(_parameters[key],goals[key],_states[key],forces[key],_gravity)
		if result.has("error"): return result
		results[key] = result
		states[key] = result.state
	# Return values never alias the numerical state owned by this actor.
	_states = states.duplicate(true)
	_tick = next_tick
	return {"outputs":results}

func stop() -> void:
	_states = {}
	_active = false
	_tick = 0
