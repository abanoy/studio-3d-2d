extends SceneTree
# UNRUN scalar-only controls. No native model, weights, GUI, Record or Off claim.
const Candidate = preload("res://tests/source_native_twelve_candidate.gd")
const Math = preload("res://src/source_jiggle_math.gd")
const Chains = preload("res://src/source_chain_math.gd")
const IDS := [8,17,18,26,27,35,36,37,60,61,62,63]
const BACK := [35,36,37]
const HAT := [60,61,62,63]
const PARENTS := {0:-1,1:0,2:1,3:2,4:3,5:4,6:5,7:6,8:7,17:7,18:17,25:7,26:25,27:26,34:7,35:34,36:35,37:36,58:6,59:58,60:59,61:60,62:61,63:62}
const CHILDREN := {8:[],17:[18],18:[],26:[27],27:[],35:[36],36:[37],37:[],60:[61],61:[62],62:[63],63:[]}
var named := {}
var duplicate_label := false
var completed_cases := 0
var comparison_rule_evaluations := 0
var replay_rule_evaluations := 0

func check(value: bool, label: String) -> void:
	if named.has(label): duplicate_label = true
	named[label] = value
	print(("PASS " if value else "FAIL ") + label)

func ident() -> Array:
	return [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]

func make_fixture() -> Dictionary:
	var bones := {}
	var locals := {}
	for index in PARENTS:
		var id := "n_" + str(index)
		var origin := [0.0,0.0,0.05] if index != 0 else [0.0,0.0,0.0]
		var basis := ident()
		if index == 35: basis = [[1.0,0.0,0.0],[0.0,0.0,1.0],[0.0,-1.0,0.0]]
		var frame := {"origin":origin,"basis":basis,"scale":1.0}
		bones[id] = {"parent":null if PARENTS[index] < 0 else "n_"+str(PARENTS[index]),"base":frame.duplicate(true)}
		locals[id] = frame.duplicate(true)
	# Authored nonrule back-hair/hat ancestors are retained, not inferred solvers.
	locals.n_34.basis = [[0.0,1.0,0.0],[-1.0,0.0,0.0],[0.0,0.0,1.0]]
	locals.n_59.origin = [0.03,-0.02,0.04]
	var params := {}
	for index in IDS:
		var p: Dictionary = Math.defaults()
		if index in [8,60,61,62,63]:
			p.yaw_stiffness = 100.0; p.pitch_stiffness = 100.0
		params["n_"+str(index)] = p
	return {"bones":bones,"locals":locals,"parameters":params}

func subset(parameters: Dictionary, ids: Array) -> Dictionary:
	var result := {}
	for index in ids: result["n_"+str(index)] = parameters["n_"+str(index)].duplicate(true)
	return result

func mv(columns: Array, vector: Array) -> Array:
	return [float(columns[0][0])*vector[0]+float(columns[1][0])*vector[1]+float(columns[2][0])*vector[2], float(columns[0][1])*vector[0]+float(columns[1][1])*vector[1]+float(columns[2][1])*vector[2], float(columns[0][2])*vector[0]+float(columns[1][2])*vector[1]+float(columns[2][2])*vector[2]]

func mm(a: Array,b: Array) -> Array:
	return [mv(a,b[0]),mv(a,b[1]),mv(a,b[2])]

func error3(a: Array,b: Array) -> float:
	return maxf(absf(float(a[0])-float(b[0])),maxf(absf(float(a[1])-float(b[1])),absf(float(a[2])-float(b[2]))))

func matrix_error(a: Array,b: Array) -> float:
	return maxf(error3(a[0],b[0]),maxf(error3(a[1],b[1]),error3(a[2],b[2])))

func branch_matches(full: Dictionary, branch: Dictionary, ids: Array) -> bool:
	for index in ids:
		var id := "n_"+str(index)
		if var_to_bytes(full.outputs[id]) != var_to_bytes(branch.outputs[id]): return false
		if var_to_bytes(full.worlds[id]) != var_to_bytes(branch.worlds[id]): return false
	return true

func run_case(size: float, label: String) -> void:
	var fixture := make_fixture()
	var authored_wire := var_to_bytes([fixture.bones,fixture.locals,fixture.parameters])
	var prefix := {"origin":[1.25,-0.75,2.0],"basis":[[0.0,0.0,-1.0],[0.0,1.0,0.0],[1.0,0.0,0.0]],"scale":size}
	var made: Dictionary = Chains.create(fixture.bones,fixture.parameters,0.01905,[0.0,-1.0,0.0])
	var made_back: Dictionary = Chains.create(fixture.bones,subset(fixture.parameters,BACK),0.01905,[0.0,-1.0,0.0])
	var made_hat: Dictionary = Chains.create(fixture.bones,subset(fixture.parameters,HAT),0.01905,[0.0,-1.0,0.0])
	check(not made.has("error") and not made_back.has("error") and not made_hat.has("error"),label+".create")
	if made.has("error") or made_back.has("error") or made_hat.has("error"): return
	var actor: RefCounted = made.actor
	var back: RefCounted = made_back.actor
	var hat: RefCounted = made_hat.actor
	var reset: Dictionary = actor.reset(fixture.locals,prefix)
	var reset_back: Dictionary = back.reset(fixture.locals,prefix)
	var reset_hat: Dictionary = hat.reset(fixture.locals,prefix)
	check(not reset.has("error") and not reset_back.has("error") and not reset_hat.has("error"),label+".reset")
	if reset.has("error") or reset_back.has("error") or reset_hat.has("error"): return
	var initial: Dictionary = actor.snapshot()
	var baseline: Dictionary = actor.baseline_worlds(fixture.locals,prefix)
	check(initial.states.size() == 12 and back.snapshot().states.size() == 3 and hat.snapshot().states.size() == 4,label+".independent_state_counts")
	for index in IDS:
		var id := "n_"+str(index)
		var actual: float = Math.v_length(Math.v_sub(initial.states[id].tip,baseline.worlds[id].origin))
		check(absf(actual-20.0*0.01905*size) <= 1e-11*size,label+".native_length_once_"+str(index))
	var force := [0.0,12.0*size,3.0*size]
	var forces := {}
	for index in IDS: forces["n_"+str(index)] = force.duplicate()
	var same_back := true
	var same_hat := true
	var all_steps := true
	var closure_error := 0.0
	var delta_error := 0.0
	var final := {}
	for tick in range(1,121):
		var result: Dictionary = actor.step(tick,fixture.locals,prefix,forces)
		var result_back: Dictionary = back.step(tick,fixture.locals,prefix,subset_forces(forces,BACK))
		var result_hat: Dictionary = hat.step(tick,fixture.locals,prefix,subset_forces(forces,HAT))
		if result.has("error") or result_back.has("error") or result_hat.has("error"):
			all_steps = false; break
		comparison_rule_evaluations += 19
		same_back = same_back and branch_matches(result,result_back,BACK)
		same_hat = same_hat and branch_matches(result,result_hat,HAT)
		for index in [18,27,36,37,61,62,63]:
			var id := "n_"+str(index)
			var parent: Dictionary = result.worlds["n_"+str(PARENTS[index])]
			var shifted: Array = mv(parent.basis,fixture.locals[id].origin)
			var expected_origin: Array = Math.v_add(parent.origin,Math.v_mul(shifted,float(parent.scale)))
			closure_error = maxf(closure_error,error3(result.goals[id].origin,expected_origin))
		for index in IDS:
			var id := "n_"+str(index)
			var parent: Dictionary = result.worlds["n_"+str(PARENTS[index])]
			var recomposed: Array = mm(parent.basis,mm(fixture.bones[id].base.basis,result.delta_bases[id]))
			delta_error = maxf(delta_error,matrix_error(recomposed,result.worlds[id].basis))
		final = result
	check(all_steps and actor.snapshot().tick == 120,label+".all_fixed_ticks")
	if not all_steps: return
	check(same_back,label+".back_branch_independent")
	check(same_hat,label+".hat_branch_independent")
	check(closure_error <= 1e-11,label+".same_tick_child_origins")
	check(delta_error <= 1e-10,label+".base_parent_delta_recomposition")
	check(Math.v_length(Math.v_sub(final.outputs.n_37.state.tip,initial.states.n_37.tip)) > 1e-6*size,label+".back_tip_moves")
	check(Math.v_length(Math.v_sub(final.outputs.n_63.state.tip,initial.states.n_63.tip)) > 1e-6*size,label+".hat_tip_moves")
	check(var_to_bytes([fixture.bones,fixture.locals,fixture.parameters]) == authored_wire,label+".authored_inputs_unchanged")
	var returned: Dictionary = actor.snapshot()
	var state_wire := var_to_bytes(actor.snapshot())
	returned.states.n_63.tip[0] += 99.0
	check(var_to_bytes(actor.snapshot()) == state_wire,label+".returned_snapshot_no_alias")
	var bad_prefix: Dictionary = prefix.duplicate(true); bad_prefix.scale = size*2.0
	var refused: Dictionary = actor.step(121,fixture.locals,bad_prefix,forces)
	check(refused.has("error") and var_to_bytes(actor.snapshot()) == state_wire,label+".resize_refuses_atomically")
	actor.stop()
	check(actor.snapshot() == {"active":false,"tick":0,"states":{},"sizes":{}},label+".stop_clears_scratch_only")
	check(var_to_bytes([fixture.bones,fixture.locals,fixture.parameters]) == authored_wire,label+".stop_keeps_authored_inputs")
	var repeat: Dictionary = actor.reset(fixture.locals,prefix)
	check(not repeat.has("error"),label+".reset_again")
	var replay_ok := true
	for tick in range(1,121):
		var result: Dictionary = actor.step(tick,fixture.locals,prefix,forces)
		if result.has("error"): replay_ok = false; break
		replay_rule_evaluations += 12
	check(replay_ok and var_to_bytes(actor.snapshot()) == state_wire,label+".reset_replay_exact")
	completed_cases += 1

func subset_forces(forces: Dictionary,ids: Array) -> Dictionary:
	var result := {}
	for index in ids: result["n_"+str(index)] = forces["n_"+str(index)].duplicate()
	return result

func late_refusal() -> void:
	var fixture := make_fixture()
	# Identity prefix and rest locals avoid binary32 or native coordinate reads.
	for id in fixture.locals: fixture.locals[id].basis = ident(); fixture.bones[id].base.basis = ident()
	var prefix: Dictionary = Chains.identity_frame()
	var made: Dictionary = Chains.create(fixture.bones,fixture.parameters,0.01905,[0.0,-1.0,0.0])
	check(not made.has("error"),"atomic.create")
	if made.has("error"): return
	var actor: RefCounted = made.actor
	var reset: Dictionary = actor.reset(fixture.locals,prefix)
	check(not reset.has("error"),"atomic.reset")
	if reset.has("error"): return
	var before := var_to_bytes(actor.snapshot())
	var locals: Dictionary = fixture.locals.duplicate(true)
	# A legitimate authored translation makes the last leaf's old tip coincide
	# with its new base. Gravity is countered exactly; zero direction must refuse.
	locals.n_63.origin[2] += 20.0*0.01905
	var forces := {}
	for index in IDS: forces["n_"+str(index)] = [0.0,20.0*0.01905,0.0]
	forces.n_8[0] = 1.0 # An earlier independent branch would advance if committed.
	var authored := var_to_bytes([locals,fixture.bones,fixture.parameters])
	var result: Dictionary = actor.step(1,locals,prefix,forces)
	check(result.has("error"),"atomic.last_leaf_degenerate_refused")
	check(var_to_bytes(actor.snapshot()) == before,"atomic.no_partial_earlier_branch_commit")
	check(var_to_bytes([locals,fixture.bones,fixture.parameters]) == authored,"atomic.authored_inputs_unchanged")
	var invalid: Dictionary = fixture.parameters.duplicate(true)
	invalid.n_63.raw_rule_flags = 0x35
	var unsupported: Dictionary = Chains.create(fixture.bones,invalid,0.01905,[0.0,-1.0,0.0])
	check(unsupported.has("error"),"atomic.new_constraint_not_inferred")

func expected_names() -> Array:
	var result := ["profile.exact_twelve","profile.retains_existing_five","profile.ancestor_closure","profile.parents","profile.descendant_closed","profile.unknown_asset_refused"]
	for label in ["half","one","two"]:
		for suffix in ["create","reset","independent_state_counts"]: result.append(label+"."+suffix)
		for index in IDS: result.append(label+".native_length_once_"+str(index))
		for suffix in ["all_fixed_ticks","back_branch_independent","hat_branch_independent","same_tick_child_origins","base_parent_delta_recomposition","back_tip_moves","hat_tip_moves","authored_inputs_unchanged","returned_snapshot_no_alias","resize_refuses_atomically","stop_clears_scratch_only","stop_keeps_authored_inputs","reset_again","reset_replay_exact"]: result.append(label+"."+suffix)
	for suffix in ["create","reset","last_leaf_degenerate_refused","no_partial_earlier_branch_commit","authored_inputs_unchanged","new_constraint_not_inferred"]: result.append("atomic."+suffix)
	return result

func _initialize() -> void:
	check(Candidate.SELECTED_NATIVE_IDS == IDS,"profile.exact_twelve")
	var kept := true
	for index in [8,17,18,26,27]: kept = kept and Candidate.SELECTED_NATIVE_IDS.has(index)
	check(kept,"profile.retains_existing_five")
	check(Candidate.EXPECTED_CAPTURE_NATIVE_IDS == PARENTS.keys(),"profile.ancestor_closure")
	var parents_ok := true
	var closed := true
	for index in IDS:
		parents_ok = parents_ok and Candidate.EXPECTED_PARENTS[index] == PARENTS[index]
		closed = closed and Candidate.EXPECTED_CHILDREN.get(index,[]) == CHILDREN[index]
	check(parents_ok,"profile.parents")
	check(closed,"profile.descendant_closed")
	check(not Candidate.qualified_asset_data({"sha256":"f".repeat(64)}),"profile.unknown_asset_refused")
	run_case(0.5,"half"); run_case(1.0,"one"); run_case(2.0,"two")
	late_refusal()
	var expected := expected_names()
	var actual: Array = named.keys()
	expected.sort(); actual.sort()
	var failures := 0
	for value in named.values():
		if value != true: failures += 1
	var complete: bool = not duplicate_label and actual == expected and completed_cases == 3
	print("SOURCE_NATIVE_TWELVE_UNIT ",JSON.stringify({"checks":named.size(),"expected_checks":expected.size(),"failures":failures,"complete_assertion_set":complete,"cases":completed_cases,"comparison_rule_evaluations":comparison_rule_evaluations,"replay_rule_evaluations":replay_rule_evaluations,"native_model_loaded":false,"native_runtime_or_GUI_qualified":false}))
	quit(0 if failures == 0 and complete else 1)
