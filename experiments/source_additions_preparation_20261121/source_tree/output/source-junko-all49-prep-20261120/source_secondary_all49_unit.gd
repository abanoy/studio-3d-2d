extends SceneTree
# Authored/unrun: generated69-frame/49-owner fixtures only; no model/native input.
const All = preload("res://src/source_secondary_all49.gd")
const Legacy = preload("res://src/source_secondary.gd")
const Math = preload("res://src/source_jiggle_math.gd")
const Chains = preload("res://src/source_chain_math.gd")
var failures := 0
var checks := 0

func check(value: bool,label: String) -> void:
	checks += 1
	if not value: failures += 1
	print(("PASS " if value else "FAIL ")+label)

func close_vector(a: Array,b: Array,tolerance: float=1e-10) -> bool:
	if a.size()!=b.size(): return false
	for i in range(a.size()):
		if absf(float(a[i])-float(b[i]))>tolerance: return false
	return true

func identity_basis(value: Array) -> bool:
	return value.size()==3 and close_vector(value[0],[1.0,0.0,0.0]) and close_vector(value[1],[0.0,1.0,0.0]) and close_vector(value[2],[0.0,0.0,1.0])

func fixture() -> Dictionary:
	var bones: Dictionary = {}
	var locals: Dictionary = {}
	var parameters: Dictionary = {}
	var down: Array = [[1.0,0.0,0.0],[0.0,0.0,1.0],[0.0,-1.0,0.0]]
	#20 passive ancestors. Translations zero; only first frame turns+Z to-Y.
	for i in range(20):
		var key: String = "a"+str(i)
		var frame: Dictionary = {"origin":[0.0,0.0,0.0],"basis":down.duplicate(true) if i==0 else [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]],"scale":1.0}
		bones[key]={"parent":null if i==0 else "a"+str(i-1),"base":frame.duplicate(true)}
		locals[key]=frame.duplicate(true)
	var lengths: Array = []
	for i in range(13): lengths.append(1)
	for i in range(5): lengths.append(2)
	for i in range(6): lengths.append(3)
	for i in range(2): lengths.append(4)
	var next: int = 0
	for chain in range(lengths.size()):
		var parent: String = "a"+str(chain%20)
		for depth in range(lengths[chain]):
			var key: String = "j"+str(next)
			var frame: Dictionary = {"origin":[0.0,0.0,0.2],"basis":[[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]],"scale":1.0}
			bones[key]={"parent":parent,"base":frame.duplicate(true)}
			locals[key]=frame.duplicate(true)
			var p: Dictionary = Math.defaults()
			if next<17: p.yaw_stiffness=100.0; p.pitch_stiffness=100.0
			parameters[key]=p;parent=key;next+=1
	var made: Dictionary = Chains.create(bones,parameters,0.01905,[0.0,-1.0,0.0])
	return {"made":made,"bones":bones,"locals":locals,"parameters":parameters,"prefix":Chains.identity_frame()}

func source_rule(index: int) -> Dictionary:
	var p: Dictionary = All.expected_parameters(index)
	p.erase("raw_rule_flags")
	return {"native_bone_index":index,"native_parent_index":All.EXPECTED_PARENTS[index],"raw_rule_flags":49,"unknown_rule_flag_bits":0,"binary_provenance":{"prefix_sha256":All.PREFIX_SHA if index in All.STIFF_NATIVE_IDS else All.CHAIN_PREFIX_SHA},"parameters":p}

func _initialize() -> void: call_deferred("run")

func run() -> void:
	check(Legacy.SELECTED_NATIVE_IDS==[8,17,18,26,27],"legacy.default_five_selection_unchanged")
	check(FileAccess.get_sha256("res://src/source_secondary.gd")=="012d54ce1305b29bb24a1a58a5343f26aa7e7d5b27f2be30fc1975b5981c5b9d","legacy.source_bytes_unchanged")
	var selected: Dictionary = {}
	var ordered: bool = true
	var previous: int = -1
	for index in All.SELECTED_NATIVE_IDS:
		ordered=ordered and index>previous and index>=0 and index<69 and not selected.has(index)
		selected[index]=true;previous=index
	check(ordered and selected.size()==49 and All.STIFF_NATIVE_IDS.size()==17,"profile.exact_sorted_unique49_and17_stiff_family")
	var all_rules_ok: bool = true
	var old_subset: bool = true
	for index in Legacy.SELECTED_NATIVE_IDS: old_subset=old_subset and selected.has(index)
	for index in All.SELECTED_NATIVE_IDS:
		var parsed: Dictionary = All.rule_parameters(source_rule(index),index)
		all_rules_ok=all_rules_ok and not parsed.has("error") and parsed.get("parameters",{})==All.expected_parameters(index)
	check(old_subset and all_rules_ok,"profile.two_existing_families_all_active_coefficients_admitted")
	check(All.EXPECTED_CAPTURE_NATIVE_IDS.size()==69 and All.EXPECTED_CAPTURE_NATIVE_IDS[0]==0 and All.EXPECTED_CAPTURE_NATIVE_IDS[68]==68,"profile.full69_ancestor_closure")
	var roots: int = 0
	var leaves: int = 0
	var depth_counts: Dictionary = {}
	var child_ok: bool = true
	for index in All.SELECTED_NATIVE_IDS:
		if not selected.has(All.EXPECTED_PARENTS[index]): roots+=1
		if All.EXPECTED_CHILDREN[index].is_empty(): leaves+=1
		child_ok=child_ok and All.EXPECTED_CHILDREN[index].size()<=1
		for child in All.EXPECTED_CHILDREN[index]: child_ok=child_ok and selected.has(child) and All.EXPECTED_PARENTS[child]==index
		var depth: int = 1
		var parent: int = All.EXPECTED_PARENTS[index]
		while selected.has(parent) and depth<70:
			depth+=1;parent=All.EXPECTED_PARENTS[parent]
		depth_counts[depth]=int(depth_counts.get(depth,0))+1
	check(child_ok and roots==26 and leaves==26 and depth_counts=={1:26,2:13,3:8,4:2},"profile.owner_chain_topology_26_roots_max_four")
	var index: int = All.SELECTED_NATIVE_IDS[0]
	var rule: Dictionary = source_rule(index)
	var raw_before: PackedByteArray = var_to_bytes(rule)
	All.rule_parameters(rule,index)
	check(var_to_bytes(rule)==raw_before,"profile.parameters_are_read_only")
	var bad: Dictionary = rule.duplicate(true);bad.binary_provenance.prefix_sha256="0".repeat(64)
	check(All.rule_parameters(bad,index).has("error"),"profile.foreign_prefix_refused")
	bad=rule.duplicate(true);bad.native_parent_index=68
	check(All.rule_parameters(bad,index).has("error"),"profile.parent_substitution_refused")
	bad=rule.duplicate(true);bad.raw_rule_flags=50
	check(All.rule_parameters(bad,index).has("error"),"profile.new_flags_refused")
	bad=rule.duplicate(true);bad.unknown_rule_flag_bits=1
	check(All.rule_parameters(bad,index).has("error"),"profile.unknown_flags_refused")
	bad=rule.duplicate(true);bad.parameters.yaw_stiffness=75.0
	check(All.rule_parameters(bad,index).has("error"),"profile_finite_but_wrong_coefficient_refused")
	bad=rule.duplicate(true);bad.parameters.length=true
	check(All.rule_parameters(bad,index).has("error"),"profile_boolean_coefficient_refused")
	bad=rule.duplicate(true);bad.parameters.erase("pitch_damping")
	check(All.rule_parameters(bad,index).has("error"),"profile_missing_active_coefficient_refused")
	check(All.rule_parameters(rule,0).has("error"),"profile_nonowner_refused")
	var f: Dictionary = fixture()
	check(not f.made.has("error") and f.bones.size()==69 and f.parameters.size()==49,"math.real_unchanged_chain_core_accepts69_frames49_owners")
	if f.made.has("error"):
		quit(1);return
	var runner: RefCounted = f.made.actor
	check(not runner.reset(f.locals,f.prefix).has("error") and runner.snapshot().states.size()==49,"math.reset_initializes_every_owner")
	var gravity_aligned: bool = true
	for tick in range(1,121):
		var result: Dictionary = runner.step(tick,f.locals,f.prefix)
		if result.has("error"):
			gravity_aligned=false;break
		gravity_aligned=gravity_aligned and result.worlds.size()==69 and result.delta_bases.size()==49
		for basis in result.delta_bases.values(): gravity_aligned=gravity_aligned and identity_basis(basis)
	check(gravity_aligned and runner.snapshot().tick==120,"math_all49_gravity_aligned_exact_rest_for120_ticks")
	runner.reset(f.locals,f.prefix)
	var force: float = 0.1
	var forced: Dictionary = runner.step(1,f.locals,f.prefix,{"j0":[force,0.0,0.0]})
	var dt: float = 1.0/120.0
	var length: float = 20.0*0.01905
	var vertical: float = -(length+length*dt*dt)
	var lateral: float = force*dt*dt
	var magnitude: float = sqrt(lateral*lateral+vertical*vertical)
	var expected_tip: Array = [length*lateral/magnitude,-0.2+length*vertical/magnitude,0.0]
	check(not forced.has("error") and close_vector(runner.snapshot().states.j0.tip,expected_tip),"math_first_tip_matches_independent_euler_projection")
	var peers_rest: bool = not forced.has("error")
	if peers_rest:
		for id in forced.delta_bases:
			if id!="j0": peers_rest=peers_rest and identity_basis(forced.delta_bases[id])
	check(peers_rest,"math_force_on_one_terminal_owner_leaves_other48_rest")
	var independent: Dictionary = fixture()
	var peer: RefCounted = independent.made.actor
	runner.reset(f.locals,f.prefix);peer.reset(independent.locals,independent.prefix)
	var replay: bool = true
	for tick in range(1,21):
		var left: Dictionary = runner.step(tick,f.locals,f.prefix,{"j0":[force,0.0,0.0]})
		var right: Dictionary = peer.step(tick,independent.locals,independent.prefix,{"j0":[force,0.0,0.0]})
		replay=replay and not left.has("error") and not right.has("error") and var_to_bytes(runner.snapshot())==var_to_bytes(peer.snapshot())
	check(replay,"math_full49_independent_reset_replay_deterministic")
	runner.reset(f.locals,f.prefix)
	runner._states.j48.tip=[NAN,0.0,0.0]
	var before: PackedByteArray = var_to_bytes(runner.snapshot())
	var refused: Dictionary = runner.step(1,f.locals,f.prefix)
	check(refused.has("error") and var_to_bytes(runner.snapshot())==before,"math_late_owner_failure_commits_none_of_earlier_states")
	var profile: RefCounted = All.new()
	var states: Dictionary = {}
	for i in range(49):
		var id: String = "j"+str(i)
		profile._parameters[id]={};profile._size_tokens[id]=1.0;states[id]={"tip":[0.0,0.0,1.0],"velocity":[0.0,0.0,0.0]}
	var snapshot: Dictionary = {"active":true,"tick":0,"states":states,"sizes":profile._size_tokens.duplicate(true)}
	check(profile.state_error(snapshot,0).is_empty(),"runtime_state_guard_accepts_exact49")
	snapshot.states.erase("j48")
	check(not profile.state_error(snapshot,0).is_empty(),"runtime_state_guard_refuses_missing49th")
	profile._alive=true
	for i in range(49):profile.chains.append({"ids":["j"+str(i)],"source":{"joints":[{"binding":{"kind":"bone","id":"j"+str(i)}}]}})
	profile._chain_inventory_stamp=var_to_bytes(profile.chains)
	check(profile.airflow_error().is_empty(),"runtime_airflow_guard_accepts_exact49")
	profile.chains[48].ids=["foreign"]
	check(not profile.airflow_error().is_empty(),"runtime_airflow_guard_refuses_same_count_mutation")
	profile.dispose();runner.stop();peer.stop()
	print("ALL49 authored synthetic checks: "+str(checks)+"; failures: "+str(failures))
	quit(0 if failures==0 else 1)
