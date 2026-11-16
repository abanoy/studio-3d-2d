extends RefCounted
# SOURCE ONLY, UNPARSED/UNRUN. Parent-first HAS policy, not SDK client parity.
# Stage the unchanged qualified scalar solver as res://leaf_candidate.gd.
const Math = preload("res://src/source_jiggle_math.gd")
var _bones: Dictionary = {}
var _order: Array = []
var _parameters: Dictionary = {}
var _source_scale := 0.01905
var _gravity: Array = [0.0,-1.0,0.0]
var _states: Dictionary = {}
var _sizes: Dictionary = {}
var _tick := 0
var _active := false

static func identity_frame() -> Dictionary:
	return {"origin":[0.0,0.0,0.0],"basis":[[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]],"scale":1.0}

static func frame_error(frame: Dictionary) -> String:
	if not frame.has("origin") or not frame.has("basis") or not frame.has("scale"): return "Complete scalar64 frame required"
	var error := Math.goal_error({"base":frame.origin,"basis":frame.basis})
	if not error.is_empty(): return error
	if not (typeof(frame.scale) == TYPE_INT or typeof(frame.scale) == TYPE_FLOAT) or not is_finite(float(frame.scale)) or frame.scale < 1e-8 or frame.scale > 1e6: return "Positive bounded uniform scale required"
	return ""

static func mv(columns: Array, v: Array) -> Array:
	var result := [0.0,0.0,0.0]
	for i in range(3):
		for j in range(3): result[i] += float(columns[j][i])*float(v[j])
	return result

static func mm(a: Array, b: Array) -> Array: return [mv(a,b[0]),mv(a,b[1]),mv(a,b[2])]
static func transpose(a: Array) -> Array:
	return [[a[0][0],a[1][0],a[2][0]],[a[0][1],a[1][1],a[2][1]],[a[0][2],a[1][2],a[2][2]]]

static func compose(parent: Dictionary, local: Dictionary) -> Dictionary:
	var frame := {"origin":Math.v_add(parent.origin,Math.v_mul(mv(parent.basis,local.origin),float(parent.scale))),"basis":mm(parent.basis,local.basis),"scale":float(parent.scale)*float(local.scale)}
	var error := frame_error(frame)
	return {"frame":frame} if error.is_empty() else {"error":error}

static func parent_order(bones: Dictionary) -> Dictionary:
	if bones.is_empty() or bones.size() > 1024: return {"error":"Explicit bounded actual hierarchy required"}
	for key in bones:
		if not key is String or key.is_empty() or not bones[key] is Dictionary: return {"error":"Named bone definitions required"}
		var bone: Dictionary = bones[key]
		if not bone.has("parent") or not bone.has("base") or not bone.base is Dictionary: return {"error":"Explicit actual parent and Model base required"}
		if bone.parent != null and (not bone.parent is String or not bones.has(bone.parent)): return {"error":"Missing actual parent"}
		var error := frame_error(bone.base)
		if not error.is_empty(): return {"error":error}
	var pending: Array = bones.keys()
	pending.sort()
	var ordered: Array = []
	while not pending.is_empty():
		var ready: Array = []
		for key in pending:
			if bones[key].parent == null or ordered.has(bones[key].parent): ready.append(key)
		if ready.is_empty(): return {"error":"Cyclic actual parent graph"}
		for key in ready:
			ordered.append(key)
			pending.erase(key)
	return {"order":ordered}

static func create(bones: Dictionary, parameters: Dictionary, source_scale: Variant, gravity: Array = [0.0,-1.0,0.0]) -> Dictionary:
	var ordered := parent_order(bones)
	if ordered.has("error"): return ordered
	if not (typeof(source_scale) == TYPE_INT or typeof(source_scale) == TYPE_FLOAT): return {"error":"Explicit numeric source scale required"}
	if parameters.is_empty() or not is_finite(float(source_scale)) or source_scale <= 0.0 or not Math.vector_ok(gravity) or absf(Math.v_length(gravity)-1.0) > 1e-9: return {"error":"Explicit rule parameters, native units and unit world gravity required"}
	for key in parameters:
		if not bones.has(key) or not parameters[key] is Dictionary: return {"error":"Unknown rule owner"}
		var error := Math.parameter_error(parameters[key])
		if not error.is_empty(): return {"error":error}
	var actor = new()
	actor._bones = bones.duplicate(true)
	actor._order = ordered.order.duplicate(true)
	actor._parameters = parameters.duplicate(true)
	actor._source_scale = source_scale
	actor._gravity = gravity.duplicate(true)
	return {"actor":actor}

func _baseline_error(locals: Dictionary, prefix: Dictionary) -> String:
	var error := frame_error(prefix)
	if not error.is_empty(): return error
	if locals.size() != _bones.size(): return "Complete authored absolute local baseline required"
	for key in _order:
		if not locals.has(key) or not locals[key] is Dictionary: return "Missing authored local"
		error = frame_error(locals[key])
		if not error.is_empty(): return error
		if float(locals[key].scale) != float(_bones[key].base.scale): return "Authored local scale differs from Model base contract"
	return ""

func baseline_worlds(locals: Dictionary, prefix: Dictionary) -> Dictionary:
	var error := _baseline_error(locals,prefix)
	if not error.is_empty(): return {"error":error}
	var worlds := {}
	for key in _order:
		var parent_id: Variant = _bones[key].parent
		var parent: Dictionary = prefix if parent_id == null else worlds[parent_id]
		var result := compose(parent,locals[key])
		if result.has("error"): return result
		worlds[key] = result.frame
	return {"worlds":worlds}

func _scaled_parameters(key: String, size: float) -> Dictionary:
	var p: Dictionary = _parameters[key].duplicate(true)
	# GLB/local positions already contain source scale. Apply it only to the
	# retained native rule length and downward acceleration magnitude.
	var factor := _source_scale*size
	p.length = float(p.length)*factor
	p.tip_mass = float(p.tip_mass)*factor
	var error := Math.parameter_error(p)
	return {"parameters":p} if error.is_empty() else {"error":error}

func reset(locals: Dictionary, prefix: Dictionary) -> Dictionary:
	var baseline := baseline_worlds(locals,prefix)
	if baseline.has("error"): return baseline
	var states := {}
	var sizes := {}
	for key in _parameters:
		var world: Dictionary = baseline.worlds[key]
		var p := _scaled_parameters(key,float(world.scale))
		if p.has("error"): return p
		var tip := Math.tip({"base":world.origin,"basis":world.basis},p.parameters)
		if not Math.vector_ok(tip): return {"error":"Nonfinite initial state"}
		states[key] = {"tip":tip,"velocity":[0.0,0.0,0.0]}
		sizes[key] = world.scale
	_states = states
	_sizes = sizes
	_tick = 0
	_active = true
	return {"ok":true}

func snapshot() -> Dictionary:
	return {"active":_active,"tick":_tick,"states":_states.duplicate(true),"sizes":_sizes.duplicate(true)}

func step(next_tick: Variant, locals: Dictionary, prefix: Dictionary, world_accelerations: Dictionary = {}) -> Dictionary:
	if not _active or typeof(next_tick) != TYPE_INT or next_tick != _tick+1: return {"error":"Sequential120Hz integer ticks required; reset/replay on discontinuity"}
	var error := _baseline_error(locals,prefix)
	if not error.is_empty(): return {"error":error}
	for key in world_accelerations:
		if not _parameters.has(key): return {"error":"Unknown rule acceleration"}
	var forces := {}
	for key in _parameters:
		var force: Variant = world_accelerations.get(key,[0.0,0.0,0.0])
		if not Math.vector_ok(force) or Math.v_length(force) > 1e6: return {"error":"Bounded finite world acceleration required"}
		forces[key] = force.duplicate(true)
	var worlds := {}
	var goals := {}
	var outputs := {}
	var deltas := {}
	for key in _order:
		var parent_id: Variant = _bones[key].parent
		var parent: Dictionary = prefix if parent_id == null else worlds[parent_id]
		var made := compose(parent,locals[key])
		if made.has("error"): return made
		var target: Dictionary = made.frame
		if not _parameters.has(key):
			worlds[key] = target
			continue
		if float(target.scale) != float(_sizes[key]): return {"error":"World size changed; explicit reset required"}
		var p := _scaled_parameters(key,float(target.scale))
		if p.has("error"): return p
		var output := Math.solve_one(p.parameters,{"base":target.origin,"basis":target.basis},_states[key],forces[key],_gravity)
		if output.has("error"): return output
		worlds[key] = {"origin":target.origin.duplicate(true),"basis":output.basis.duplicate(true),"scale":target.scale}
		goals[key] = target
		outputs[key] = output
		deltas[key] = mm(transpose(_bones[key].base.basis),mm(transpose(parent.basis),output.basis))
		error = Math.goal_error({"base":[0.0,0.0,0.0],"basis":deltas[key]})
		if not error.is_empty(): return {"error":error}
	# A late child refusal cannot advance any earlier parent state. Deep copies
	# separate internal states from mutable result/goal/parameter Arrays.
	var committed := {}
	for key in outputs: committed[key] = outputs[key].state.duplicate(true)
	_states = committed
	_tick = next_tick
	return {"worlds":worlds.duplicate(true),"goals":goals.duplicate(true),"outputs":outputs.duplicate(true),"delta_bases":deltas.duplicate(true)}

func stop() -> void:
	_states = {}
	_sizes = {}
	_tick = 0
	_active = false
