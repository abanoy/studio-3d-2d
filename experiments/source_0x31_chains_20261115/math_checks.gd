extends RefCounted
# UNPARSED/UNRUN. Root may call new().run() from a separately leased headless
# runner before native probes. Synthetic inputs only; no Model/GPU or file IO.
const Chains = preload("res://chain_solver.gd")
const Math = preload("res://leaf_candidate.gd")
var checks := 0
var failures: Array = []
var maximum_error := 0.0

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok and failures.size() < 32: failures.append(label)

func vector_close(actual: Array, expected: Array, label: String, eps := 1e-12) -> void:
	var error := 0.0
	for i in range(3): error = maxf(error,absf(float(actual[i])-float(expected[i])))
	maximum_error = maxf(maximum_error,error)
	check(error <= eps,label)

func run() -> Dictionary:
	var identity := Chains.identity_frame()
	var child_local := Chains.identity_frame(); child_local.origin = [0.0,0.0,2.0]
	var bones := {"child":{"parent":"parent","base":identity.duplicate(true)},"parent":{"parent":null,"base":identity.duplicate(true)}}
	var locals := {"child":child_local,"parent":identity.duplicate(true)}
	var p: Dictionary = Math.parameters({"length":2.0,"tip_mass":0.0}).parameters
	var made := Chains.create(bones,{"child":p,"parent":p},1.0)
	if made.has("error"): return made
	var actor = made.actor
	var reset: Dictionary = actor.reset(locals,identity)
	if reset.has("error"): return reset
	# Constructor must own independent parameter copies.
	p.length = 99.0
	var first: Dictionary = actor.step(1,locals,identity,{"parent":[3.0,0.0,0.0]})
	if first.has("error"): return first
	# Independent first-step equations: parent impulse a=3/120²=1/4800.
	# f=(a,0,2)/sqrt(a²+4), left=(f.z,0,-f.x). Child base=2f,
	# target=4f, old tip=4Z, hence yaw force=200*f.x*left.
	var a := 1.0/4800.0
	var size := sqrt(a*a+4.0)
	var fx := a/size; var fz := 2.0/size
	var acceleration := [200.0*fx*fz,0.0,-200.0*fx*fx]
	var base := [2.0*fx,0.0,2.0*fz]
	var unconstrained := [acceleration[0]/14400.0,0.0,4.0+acceleration[2]/14400.0]
	var separation := Math.v_sub(unconstrained,base)
	var expected_tip := Math.v_add(base,Math.v_mul(separation,2.0/sqrt(Math.v_dot(separation,separation))))
	vector_close(first.outputs.parent.state.tip,[2.0*fx,0.0,2.0*fz],"rational parent constrained impulse")
	vector_close(first.goals.child.origin,base,"child origin from same-tick solved parent")
	vector_close(first.outputs.child.acceleration,acceleration,"independent child spring force")
	vector_close(first.outputs.child.unconstrained_tip,unconstrained,"independent child Euler position")
	vector_close(first.outputs.child.state.tip,expected_tip,"independent child projected tip")
	check(absf(float(first.outputs.child.acceleration[0])) > 0.01,"stale parent negative control would produce zero")
	var snapshot: Dictionary = actor.snapshot()
	var snapshot_bytes := var_to_bytes(snapshot)
	first.outputs.parent.state.tip[0] = 100000.0
	first.worlds.parent.origin[0] = -100000.0
	first.goals.child.basis[0][0] = 100000.0
	snapshot.states.parent.tip[1] = 100000.0
	check(var_to_bytes(actor.snapshot()) == snapshot_bytes,"mutable returned result/snapshot does not alias internal state")
	var refused: Dictionary = actor.step(2.5,locals,identity)
	check(refused.has("error") and var_to_bytes(actor.snapshot()) == snapshot_bytes,"noninteger clock refused without state advance")
	refused = actor.step(2,locals,identity,{"unknown":[0.0,0.0,0.0]})
	check(refused.has("error") and var_to_bytes(actor.snapshot()) == snapshot_bytes,"unknown force owner refused atomically")
	# Mutating a reused input array deliberately changes the next authored goal,
	# while it cannot retroactively modify prior state or a returned world map.
	locals.child.origin[0] = 0.1
	check(var_to_bytes(actor.snapshot()) == snapshot_bytes,"reused caller local array does not alias states")
	var second: Dictionary = actor.step(2,locals,identity)
	if second.has("error"): return second
	check(second.goals.child.origin != base,"fresh authored local consumed on next tick")
	actor.stop()
	check(actor.step(3,locals,identity).has("error"),"stopped actor refuses continuation")
	# Original zero-cone rounding failure: exact-zero handling, no wider angle
	# tolerance. Test both parent and child through the hierarchy at tilted goals.
	for i in range(1,1001):
		var angle := float(i)*0.0031
		var c := cos(angle); var s := sin(angle)
		var tilted := Chains.identity_frame(); tilted.basis = [[c,0.0,-s],[0.0,1.0,0.0],[s,0.0,c]]
		var zero_parameters: Dictionary = Math.parameters({"length":2.0,"tip_mass":0.0,"angle_limit":0.0}).parameters
		var zero_made := Chains.create(bones,{"parent":zero_parameters,"child":zero_parameters},1.0)
		if zero_made.has("error"): return zero_made
		var zero_actor = zero_made.actor
		var zero_locals := {"parent":tilted,"child":child_local.duplicate(true)}
		var zero_reset: Dictionary = zero_actor.reset(zero_locals,identity)
		if zero_reset.has("error"): return zero_reset
		var output: Dictionary = zero_actor.step(1,zero_locals,identity)
		if output.has("error"): return output
		for key in ["parent","child"]:
			vector_close(output.outputs[key].basis[2],output.goals[key].basis[2],"zero-cone direction at tilted parent",1e-12)
			var target := Math.v_add(output.goals[key].origin,Math.v_mul(output.goals[key].basis[2],2.0))
			vector_close(output.outputs[key].state.tip,target,"zero-cone unchanged rest tip",1e-10)
	return {"status":"PASSED_SYNTHETIC_CHAIN_MATH_ONLY" if failures.is_empty() else "FAILED_SYNTHETIC_CHAIN_MATH","checks":checks,"failures":failures,"maximum_error":maximum_error,
		"SDK_executed":false,"actual_native_chains_exercised":false,"float32_Model_boundary_exercised":false}
