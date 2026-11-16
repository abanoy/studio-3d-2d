extends "res://leaf_harness.gd"
# SOURCE ONLY UNPARSED/UNRUN. Reuses the exact qualified import-context guard,
# snapshots and root source-lock checks. Root alone stages and grants a lease.
const Chains = preload("res://chain_solver.gd")
const Bridge = preload("res://model_adapter.gd")
const ChainCapture = preload("res://chain_capture.gd")
var rule_evaluations := 0

func finish(status: String, reason := "") -> void:
	check(source_unchanged(),"All locked original/source/proof bytes preserved")
	if failures > 0 and status == "PASSED_NATIVE_TWO_PAIR_READINESS_ONLY": status = "FAILED_NATIVE_TWO_PAIR_READINESS"
	var result := {"format":"has_actual_native_two_pair_readiness_1","status":status,"checks":checks,"failures":failures,"failure_labels":labels,"reason":reason,"cases":rows,
		"native_pairs":[[17,18],[26,27]],"native_bones_retained":69,"native_rules_retained":49,"source_scale":0.01905,"source_glb_sha256":GLB_SHA,"parameters_sha256":PARAM_SHA,
		"dynamic_ticks":dynamics_steps,"rule_evaluations":rule_evaluations,
		"scope":{"actual_Model_load_attempted":model_started,"actual_CPU_weighted_query_attempted":weighted_started,"actual_live_pose_attempted":live_started,
		"goal_policy":"Fresh authored absolute-local poses recomposed under same-tick solved parents; unsimulated intermediates preserved",
		"external_input":"Temporary synthetic world acceleration, not actual fan/native wind","SDK_executed":false,"SDK_client_parent_policy_proved":false,"artist_motion_fidelity":"UNQUALIFIED",
		"GPU_render":false,"GUI_body_fan_Record_HAS_export_integration":false,"native_metadata_activation_changed":false,"private_geometry_or_rest_arrays_published":false},
		"gates":{"basis_and_scaled_world_transport":EPS,"meaningful_weighted_motion_per_root_size":MOTION_MIN,"unaffected_Off_repeat":"Exact byte/hash equality"}}
	var file := FileAccess.open(result_path,FileAccess.WRITE)
	if file == null: push_error("Cannot write fresh aggregate chain result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("NATIVE_TWO_PAIR "+JSON.stringify({"status":status,"checks":checks,"failures":failures,"cases":rows.size()}))
	quit(0 if failures == 0 and status == "PASSED_NATIVE_TWO_PAIR_READINESS_ONLY" else 1)

func owned_pose(resolution: RefCounted, later: bool) -> Dictionary:
	var pose := {}
	for spec in [{"native":7,"axis":Vector3.RIGHT,"a":0.17,"b":-0.11},
		{"native":17,"axis":Vector3.UP,"a":0.13,"b":-0.07},{"native":18,"axis":Vector3.FORWARD,"a":0.12,"b":0.23},
		{"native":26,"axis":Vector3.RIGHT,"a":-0.16,"b":0.14},{"native":27,"axis":Vector3.UP,"a":0.2,"b":-0.18},
		{"native":8,"axis":Vector3.UP,"a":0.09,"b":-0.13}]:
		pose[resolution.by_native[spec.native]] = {"position":[0.0004,-0.0007,0.0003] if spec.native in [18,27] else [0.0,0.0,0.0],
			"rotation_xyzw":quaternion_array(Quaternion(spec.axis,spec.b if later else spec.a))}
	return pose

func unselected_bytes(actor: RefCounted, selected: Dictionary) -> PackedByteArray:
	var values: Array = []
	for id in actor.order:
		if not selected.values().has(id): values.append([id,actor.bone_transform(id)])
	return var_to_bytes(values)

func actual_frame_error(actual: Transform3D, desired: Dictionary) -> Dictionary:
	var basis_error := rotation_error(actual,desired.basis,float(desired.scale))
	var expected := Vector3(desired.origin[0],desired.origin[1],desired.origin[2])
	return {"basis":basis_error,"origin":actual.origin.distance_to(expected)}

func chain_simulation(actor: RefCounted, resolution: RefCounted, profile: Dictionary, name: String, strength: float, baseline: Dictionary, pair_baselines: Array, snap12: PackedByteArray, snap24: PackedByteArray) -> Dictionary:
	actor.live_pose = null; actor.apply(FRAME,false)
	var authored: Dictionary = actor.sample(FRAME,false).duplicate(true)
	var authored_bytes := var_to_bytes(authored)
	var unselected := unselected_bytes(actor,profile.selected)
	var captured := Bridge.capture_baseline(actor,profile)
	if captured.has("error"): return captured
	var made := Chains.create(profile.bones,profile.parameters,0.01905,[0.0,-1.0,0.0])
	if made.has("error"): return made
	var runner = made.actor
	var seeded: Dictionary = runner.reset(captured.locals,captured.prefix)
	if seeded.has("error"): return seeded
	var baseline_worlds: Dictionary = runner.baseline_worlds(captured.locals,captured.prefix)
	if baseline_worlds.has("error"): return baseline_worlds
	var forces := {}
	for id in profile.parameters: forces[id] = Math.v_mul(baseline_worlds.worlds[id].basis[0],strength)
	var maximum_basis := 0.0
	var maximum_origin := 0.0
	var maximum_tip := 0.0
	var maximum_boundary: float = captured.boundary_correction_max
	var maximum_closure: float = captured.parent_local_closure_max
	var root_size: float = baseline_worlds.worlds[profile.selected[17]].scale
	# The new scalar hierarchy adapter is checked against every actual bone before
	# dynamics, independently of the already qualified leaf conversion path.
	for id in profile.bones:
		var error := actual_frame_error(actor.bone_transform(id),baseline_worlds.worlds[id])
		check(error.basis <= EPS and error.origin <= EPS*root_size,name+" all69 authored FK scalar boundary")
	for tick in range(1,TICKS+1):
		actor.live_pose = null; actor.apply(FRAME,false)
		var current := Bridge.capture_baseline(actor,profile)
		if current.has("error"): return current
		maximum_boundary = maxf(maximum_boundary,float(current.boundary_correction_max))
		maximum_closure = maxf(maximum_closure,float(current.parent_local_closure_max))
		var output: Dictionary = runner.step(tick,current.locals,current.prefix,forces)
		if output.has("error"): return output
		dynamics_steps += 1; rule_evaluations += 4
		var overlay := Bridge.overlay(actor,profile,authored,output)
		if overlay.has("error"): return overlay
		actor.live_pose = overlay.pose; live_started = true; actor.apply(FRAME,false)
		for id in profile.parameters:
			var actual: Transform3D = actor.bone_transform(id)
			var error := actual_frame_error(actual,output.worlds[id])
			var native_length: float = profile.parameters[id].length
			var actual_tip := actual*Vector3(0.0,0.0,native_length*0.01905)
			var wanted: Array = output.outputs[id].state.tip
			var tip_error := actual_tip.distance_to(Vector3(wanted[0],wanted[1],wanted[2]))
			maximum_basis = maxf(maximum_basis,float(error.basis))
			maximum_origin = maxf(maximum_origin,float(error.origin))
			maximum_tip = maxf(maximum_tip,tip_error)
			check(error.basis <= EPS,name+" four desired/math versus actual bone orientations")
			check(error.origin <= EPS*root_size,name+" same-tick solved-parent authored-local origins")
			check(tip_error <= EPS*root_size,name+" four native+Z tips with source scale once")
		check(unselected_bytes(actor,profile.selected) == unselected,name+" all65 unselected world bones exact")
		check(var_to_bytes(actor.sample(FRAME,false)) == authored_bytes,name+" authored sample exact")
	var bindings: Array = []
	for index in Bridge.SELECTED: bindings.append(resolution.bindings[index])
	var moved := ChainCapture.capture(actor,bindings)
	var delta := ChainCapture.difference(baseline,moved,MOTION_MIN*root_size)
	if delta.has("error"): return delta
	check(delta.unaffected_exact,name+" zero-selected-weight region exact")
	var pair_captures: Array = []
	var pair_rows: Array = []
	for pair_index in range(2):
		var indices: Array = [17,18] if pair_index == 0 else [26,27]
		var capture := ChainCapture.capture(actor,[resolution.bindings[indices[0]],resolution.bindings[indices[1]]])
		var difference := ChainCapture.difference(pair_baselines[pair_index],capture,MOTION_MIN*root_size)
		if difference.has("error"): return difference
		if strength != 0.0: check(difference.affected_max > MOTION_MIN*root_size,name+" each actual pair weighted region measurably deforms")
		pair_captures.append(capture)
		pair_rows.append({"native_pair":indices,"weighted_vertices":capture.affected,"shared_with_other_bones":capture.shared,"moved_vertices":difference.affected_vertices_moved,"maximum_displacement":difference.affected_max,"weighted_points_sha256":capture.points_sha256})
	runner.stop(); actor.live_pose = null; actor.apply(24,false)
	check(exact_snapshot(actor) == snap24,name+" Off restores authored frame24 exactly")
	actor.apply(FRAME,false)
	check(exact_snapshot(actor) == snap12 and actor.live_pose == null and actor.live_world_transform == null,name+" Off restores nonrest frame12 exactly")
	var restored := ChainCapture.capture(actor,bindings)
	var restoration := ChainCapture.difference(baseline,restored,0.0)
	if restoration.has("error"): return restoration
	check(restoration.all_points_exact,name+" Off restores all weighted points exactly")
	check(Bindings.current(actor,resolution),name+" original bindings and inactive source metadata current")
	return {"public":{"profile":name,"synthetic_world_acceleration":strength,"root_size":root_size,"ticks":TICKS,"basis_error_max":maximum_basis,"origin_error_max":maximum_origin,"tip_error_max":maximum_tip,
		"boundary_correction_max":maximum_boundary,"parent_local_closure_max":maximum_closure,"vertices":moved.vertices,"weighted_to_selected":moved.affected,"shared_with_other_bones":moved.shared,
		"unaffected_vertices":moved.unaffected,"unaffected_exact":delta.unaffected_exact,"Off_all_weighted_points_exact":restoration.all_points_exact,"final_weighted_sha256":moved.points_sha256,"pairs":pair_rows},
		"private_capture":moved,"private_pairs":pair_captures}

func root_case(root_scale: float, moved_root: bool, glb: String) -> Dictionary:
	var reader = ImportDefinition.new(); var prepared: Dictionary = reader.definition(glb); reader.free()
	if prepared.has("error"): return prepared
	var decoded: Dictionary = SceneIO.load_glb(glb)
	if decoded.has("error"): return decoded
	model_started = true
	var actor = Model.new(); actor.root = decoded.scene; actor.base_root = actor.root.transform; actor.data = prepared.data; actor.inventory(actor.root)
	var host := Node3D.new(); root.add_child(host); host.add_child(actor.root)
	var resolution: RefCounted = Bindings.resolve(actor)
	var profile := Bridge.construct(actor,resolution)
	if profile.has("error"): host.free(); return profile
	# Native17 has parent7, so its shared-Skeleton context can reuse the exact
	# empty-builtin guard unchanged. Bridge independently checks native26's
	# actual parent25, retained authored/unsimulated in this bounded subset.
	var context := compatible_import_context(actor,profile.skeleton,resolution.bindings[17])
	if context.has("error"): host.free(); return context
	actor.data.position = [0.37,-0.22,0.41] if moved_root else [0.0,0.0,0.0]
	actor.data.rotation_xyzw = quaternion_array(Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)) if moved_root else [0.0,0.0,0.0,1.0]
	actor.data.scale = root_scale
	var transform := {"position":actor.data.position.duplicate(true),"rotation_xyzw":actor.data.rotation_xyzw.duplicate(true),"scale":root_scale}
	actor.data.pose = owned_pose(resolution,false); actor.data.draft_frame = 0
	actor.data.pose_keys = [{"frame":0,"pose":owned_pose(resolution,false),"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":owned_pose(resolution,true),"transform":transform.duplicate(true),"interpolation":"linear"}]
	if not Model.validate(actor.data,48).is_empty() or not actor.check_bindings().is_empty(): host.free(); return {"error":"Owned keyed pair fixture rejected by actual Model"}
	actor.apply(24,false); await process_frame; var snap24 := exact_snapshot(actor)
	actor.apply(FRAME,false); await process_frame; var snap12 := exact_snapshot(actor)
	var bindings := [resolution.bindings[17],resolution.bindings[18],resolution.bindings[26],resolution.bindings[27]]
	var baseline := ChainCapture.capture(actor,bindings)
	if baseline.has("error"): host.free(); return baseline
	if baseline.vertices != 9661 or baseline.affected != 542 or baseline.shared != 340 or baseline.unaffected != 9119 or baseline.surfaces != 4: host.free(); return {"error":"Actual union influence counts differ from immutable CPU profile"}
	weighted_started = true
	var pair_baselines := [ChainCapture.capture(actor,[bindings[0],bindings[1]]),ChainCapture.capture(actor,[bindings[2],bindings[3]])]
	for pair_index in range(2):
		var pair: Dictionary = pair_baselines[pair_index]
		if pair.has("error"): host.free(); return pair
		var expected: Array = [184,118,9477] if pair_index == 0 else [358,222,9303]
		if pair.affected != expected[0] or pair.shared != expected[1] or pair.unaffected != expected[2]: host.free(); return {"error":"Actual pair influence counts differ from immutable CPU profile"}
	var results := {}
	for spec in [{"name":"control","strength":0.0},{"name":"positive3","strength":3.0},{"name":"negative3","strength":-3.0},{"name":"positive12","strength":12.0},{"name":"positive50","strength":50.0},{"name":"repeat12","strength":12.0}]:
		var observed := chain_simulation(actor,resolution,profile,str(spec.name),float(spec.strength),baseline,pair_baselines,snap12,snap24)
		if observed.has("error"): host.free(); return observed
		observed.public["import_context"] = context.summary.duplicate(true); rows.append(observed.public); results[spec.name] = observed
	for name in ["positive3","negative3","positive12","positive50"]:
		for pair_index in range(2):
			var difference := ChainCapture.difference(results.control.private_pairs[pair_index],results[name].private_pairs[pair_index],MOTION_MIN*root_scale)
			if difference.has("error"): host.free(); return difference
			check(difference.affected_max > MOTION_MIN*root_scale,"Each pair external-input response differs from gravity control "+name)
	check(results.positive12.public.final_weighted_sha256 == results.repeat12.public.final_weighted_sha256,"Cleared-state repeat12 produces exact weighted result")
	var final_context := compatible_import_context(actor,profile.skeleton,resolution.bindings[17])
	if final_context.has("error"): host.free(); return final_context
	if var_to_bytes(final_context.summary) != var_to_bytes(context.summary): host.free(); return {"error":"Import context changed during owned pair probe"}
	host.free(); actor = null; await process_frame
	return {"ok":true}

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2: push_error("Fresh root-owned pair lease/result required"); quit(2); return
	var parsed := read_json(args[0],1024*1024)
	if parsed.has("error"): push_error(parsed.error); quit(2); return
	lease = parsed.data
	if lease.get("format") != "has_native_two_pair_readiness_lease_1" or lease.get("phase") != "ROOT_APPROVED_AFTER_FULL_FK_MATH_LEAF_AND_CLOSURE" or lease.get("root_closed_all") != true or float(lease.get("expires_unix",0)) <= Time.get_unix_time_from_system(): push_error("Fresh root post-PASS/closure authority required"); quit(2); return
	for phase in ["full_status","FK_status","math_status","leaf_status"]:
		if lease.get(phase) != "PASS": push_error("Required bounded predecessor PASS missing"); quit(2); return
	if DisplayServer.get_name() != "headless" or FileAccess.get_sha256(OS.get_executable_path()) != str(lease.get("engine_sha256","")): push_error("Exact locked headless engine required"); quit(2); return
	for name in ["candidate","adapter","capture","harness","source_lock","glb","parameters","mdl","vvd","full_receipt","FK_receipt","math_receipt","leaf_receipt","root_closure","chain_solver","model_adapter","chain_capture","chain_harness"]:
		if not lease.get("files",{}).has(name): push_error("Incomplete pair source lock"); quit(2); return
		var pin: Dictionary = lease.files[name]
		if str(pin.get("sha256","")).length() != 64 or not str(pin.get("path","")).is_absolute_path() or FileAccess.get_sha256(str(pin.path)) != str(pin.sha256): push_error("Changed locked pair input"); quit(2); return
	for pair in [["leaf_candidate.gd","candidate"],["leaf_adapter.gd","adapter"],["weighted_capture.gd","capture"],["leaf_harness.gd","harness"],["chain_solver.gd","chain_solver"],["model_adapter.gd","model_adapter"],["chain_capture.gd","chain_capture"],["chain_harness.gd","chain_harness"]]:
		if FileAccess.get_sha256("res://"+pair[0]) != str(lease.files[pair[1]].sha256): push_error("Changed staged pair source"); quit(2); return
	var source_lock := read_json(str(lease.files.source_lock.path),1024*1024)
	if source_lock.has("error"): push_error(source_lock.error); quit(2); return
	source_pins = source_lock.data.files
	result_path = args[1]
	if result_path != str(lease.get("public_result","")) or FileAccess.file_exists(result_path): push_error("Exact fresh pair result path required"); quit(2); return
	var adjacent := str(lease.files.glb.path).replace("\\","/").get_base_dir().path_join("parameters.json").simplify_path().to_lower()
	if not source_unchanged() or lease.files.glb.sha256 != GLB_SHA or lease.files.parameters.sha256 != PARAM_SHA or lease.files.mdl.sha256 != MDL_SHA or adjacent != str(lease.files.parameters.path).replace("\\","/").simplify_path().to_lower(): check(false,"Exact source/profile/adjacent report context"); finish("FAILED_PREFLIGHT"); return
	for spec in [{"scale":1.0,"moved":false},{"scale":2.0,"moved":true}]:
		var outcome: Dictionary = await root_case(float(spec.scale),bool(spec.moved),str(lease.files.glb.path))
		if outcome.has("error"): check(false,"Native two-pair bounded refusal"); finish("FAILED_NATIVE_TWO_PAIR_READINESS",str(outcome.error)); return
	finish("PASSED_NATIVE_TWO_PAIR_READINESS_ONLY" if failures == 0 else "FAILED_NATIVE_TWO_PAIR_READINESS")
