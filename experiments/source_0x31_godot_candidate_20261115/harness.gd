extends SceneTree
# UNPARSED/UNRUN. Stage as a separate root-owned headless project only after
# full-default/FK proof and root closure. No global/editor registrations.
const Candidate = preload("res://candidate.gd")
var checks := 0
var failures := 0
var failure_labels: Array[String] = []
var result_path := ""
var oracle_hash := ""
var scalar_max := 0.0
var zero_max := 0.0
var integration_steps := 0
var sample_output_sets := 0
var adapter_rows: Array = []
var context: Dictionary = {}
var math_started := false
var adapter_started := false
var locked_files: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		if failure_labels.size() < 24: failure_labels.append(label)
		print("FAIL "+label)

func read_json(path: String, maximum: int) -> Dictionary:
	var file := FileAccess.open(path,FileAccess.READ)
	if file == null or file.get_length() > maximum: return {"error":"Unavailable or oversized JSON"}
	var parser := JSON.new()
	var error := parser.parse(file.get_as_text())
	file.close()
	if error != OK or not parser.data is Dictionary: return {"error":"Invalid JSON object"}
	return {"data":parser.data}

func compare_vector(actual: Array, expected: Array, gate: float, label: String) -> void:
	var error := Candidate.v_length(Candidate.v_sub(actual,expected))
	scalar_max = maxf(scalar_max,error)
	check(is_finite(error) and error <= gate,label)

func close_result(status: String, extra: Dictionary = {}) -> void:
	for name in locked_files:
		var pin: Dictionary = locked_files[name]
		check(FileAccess.get_sha256(str(pin.path)) == str(pin.sha256),"Locked input unchanged at finish "+str(name))
	if failures > 0 and status == "PASSED_SCALAR64_SYNTHETIC_ENGINE_MATH_ONLY": status = "FAILED_MATHEMATICAL_OR_ADAPTER_CHECKS"
	var record := {"format":"has_source0x31_godot_scalar64_math_result_1","status":status,"checks":checks,"failures":failures,"failure_labels":failure_labels,
		"scalar64_max_vector_error":scalar_max,"zero_cone_max_rest_displacement":zero_max,"integration_steps":integration_steps,"sample_output_sets":sample_output_sets,
		"adapter_rows":adapter_rows,"oracle_sha256":oracle_hash,"candidate_sha256":FileAccess.get_sha256("res://candidate.gd"),"harness_sha256":FileAccess.get_sha256("res://harness.gd"),
		"engine":Engine.get_version_info(),"lease_context":context,
		"scope":{"engine_harness_executed":true,"scalar64_math_attempted":math_started,"actual_Vector3_Basis_boundary_measured":adapter_started,"actual_Model_SceneIO_FK":false,
		"native_SDK_executed":false,"native_geometry_loaded":false,"actual_parent_body_fan_Record_Off_portable_render":"UNRUN_NOT_INTEGRATED","artist_native_parity":"UNQUALIFIED"}}
	record.merge(extra)
	var file := FileAccess.open(result_path,FileAccess.WRITE)
	if file == null: push_error("Cannot save fresh root-owned result"); quit(2); return
	file.store_string(JSON.stringify(record,"",true,true))
	file.close()
	print("SOURCE0X31_GODOT_MATH "+JSON.stringify({"status":status,"checks":checks,"failures":failures,"steps":integration_steps,"scalar_max":scalar_max,"zero_max":zero_max}))
	quit(0 if failures == 0 and status == "PASSED_SCALAR64_SYNTHETIC_ENGINE_MATH_ONLY" else 1)

func sequence_pass(row: Dictionary, gate: float, compare_samples: bool) -> Dictionary:
	var specs := {}
	for id in row.parameters:
		var prepared := Candidate.parameters(row.parameters[id])
		check(not prepared.has("error"),str(row.id)+" parameters "+str(id))
		if prepared.has("error"): return {"error":prepared.error}
		specs[id] = prepared.parameters
	var made := Candidate.create(specs,{"synthetic":true},row.gravity_down)
	if made.has("error"): check(false,str(row.id)+" actor"); return made
	var actor = made.actor
	var reset: Dictionary = actor.reset(row.seed)
	if reset.has("error"): check(false,str(row.id)+" reset"); return reset
	var samples: Array = []
	for frame in row.frames:
		var tick := int(frame.tick)
		var result: Dictionary = actor.step(tick,frame.goals,frame.external)
		integration_steps += 1
		if result.has("error"): check(false,str(row.id)+" tick"+str(tick)+" "+str(result.error)); return result
		for id in result.outputs:
			var output: Dictionary = result.outputs[id]
			var goal: Dictionary = frame.goals[id]
			var p: Dictionary = specs[id]
			var segment := Candidate.v_sub(output.state.tip,goal.base)
			check(absf(Candidate.v_length(segment)-float(p.length)) <= gate,str(row.id)+" fixed length "+str(tick)+"/"+str(id))
			var normal := Candidate.normalized(segment)
			if normal.has("error"): check(false,"Invalid constrained segment"); return normal
			check(absf(Candidate.v_dot(output.state.velocity,normal.value)) <= gate,str(row.id)+" tangent velocity "+str(tick)+"/"+str(id))
			if p.angle_limit > 0:
				var angle := acos(clampf(Candidate.v_dot(normal.value,goal.basis[2]),-1.0,1.0))
				check(angle <= float(p.angle_limit)+gate,str(row.id)+" cone "+str(tick)+"/"+str(id))
		if frame.has("expected"):
			samples.append(result.outputs.duplicate(true))
			if compare_samples:
				for id in frame.expected:
					var actual: Dictionary = result.outputs[id]
					var expected: Dictionary = frame.expected[id]
					for field in ["acceleration","unconstrained_tip","unconstrained_velocity"]:
						compare_vector(actual[field],expected[field],gate,str(row.id)+" "+str(tick)+" "+str(id)+" "+field)
					compare_vector(actual.state.tip,expected.state.tip,gate,str(row.id)+" expected tip "+str(tick)+"/"+str(id))
					compare_vector(actual.state.velocity,expected.state.velocity,gate,str(row.id)+" expected velocity "+str(tick)+"/"+str(id))
					for i in range(3): compare_vector(actual.basis[i],expected.basis[i],gate,str(row.id)+" output column "+str(tick)+"/"+str(id)+"/"+str(i))
					check(actual.angle_projected == expected.angle_projected,str(row.id)+" angular branch "+str(tick)+"/"+str(id))
					sample_output_sets += 1
	return {"snapshot":actor.snapshot(),"sample_bytes":var_to_bytes(samples)}

func make_one(overrides: Dictionary = {}) -> Dictionary:
	var p := Candidate.parameters(overrides)
	if p.has("error"): return p
	return Candidate.create({"r":p.parameters})

func independent_oracles(oracle: Dictionary) -> void:
	math_started = true
	var made := make_one()
	var actor = made.actor
	var goal: Dictionary = Candidate.goal().goal
	actor.reset({"r":goal})
	var result: Dictionary = actor.step(1,{"r":goal},{"r":[3.0,4.0,0.0]})
	if result.has("error"): check(false,"Rational actor refused"); return
	var output: Dictionary = result.outputs.r
	var expected: Dictionary = oracle.independent_rational
	var gate: float = oracle.preregistered_gates.independent_rational_absolute
	compare_vector(output.acceleration,expected.acceleration,gate,"Independent rational force")
	compare_vector(output.unconstrained_velocity,expected.unconstrained_velocity,gate,"Independent rational Euler velocity")
	compare_vector(output.unconstrained_tip,expected.unconstrained_tip,gate,"Independent rational Euler position")
	compare_vector(output.state.tip,expected.constrained_tip,gate,"Independent rational length projection")
	compare_vector(output.state.velocity,expected.constrained_velocity,gate,"Independent rational tangent projection")
	result = actor.step(2,{"r":goal})
	if result.has("error"): check(false,"Second-tick actor refused"); return
	compare_vector(result.outputs.r.acceleration,oracle.independent_damping.damped,gate,"Independent second-tick damping force")
	made = make_one({"yaw_damping":0.0,"pitch_damping":0.0})
	actor = made.actor
	actor.reset({"r":goal})
	actor.step(1,{"r":goal},{"r":[3.0,4.0,0.0]})
	result = actor.step(2,{"r":goal})
	if result.has("error"): check(false,"Undamped actor refused"); return
	compare_vector(result.outputs.r.acceleration,oracle.independent_damping.undamped,gate,"Independent zero-damping control")
	made = make_one({"yaw_stiffness":100.0,"pitch_stiffness":100.0,"along_stiffness":987654.0})
	actor = made.actor
	actor.reset({"r":goal})
	result = actor.step(1,{"r":Candidate.goal([0.1,-0.2,2.0]).goal})
	if result.has("error"): check(false,"Moved-goal actor refused"); return
	compare_vector(result.outputs.r.acceleration,oracle.independent_moved_goal_acceleration,gate,"Independent moved-goal along exclusion")

func zero_cone(oracle: Dictionary) -> void:
	var gate: float = oracle.preregistered_gates.zero_cone_rest_displacement
	for row in oracle.zero_cone_goals:
		var made := make_one({"tip_mass":0.0,"angle_limit":0.0})
		var actor = made.actor
		actor.reset({"r":row.goal})
		var result: Dictionary = actor.step(1,{"r":row.goal})
		if result.has("error"): check(false,"Zero-cone tilted rest refused"); continue
		var displacement := Candidate.v_length(Candidate.v_sub(result.outputs.r.state.tip,row.seeded_tip))
		zero_max = maxf(zero_max,displacement)
		check(is_finite(displacement) and displacement <= gate,"Unchanged zero-cone1e-10 rest gate")
		compare_vector(result.outputs.r.state.tip,row.expected_tip,gate,"Python exact zero-cone ray")
	var made := make_one({"tip_mass":0.0,"angle_limit":0.0})
	var actor = made.actor
	var goal: Dictionary = Candidate.goal().goal
	actor.reset({"r":goal})
	var result: Dictionary = actor.step(1,{"r":goal},{"r":[0.0,0.0,-20.0/(Candidate.DT*Candidate.DT)]})
	check(not result.has("error"),"Zero-cone provisional collapse handled analytically")
	if not result.has("error"):
		compare_vector(result.outputs.r.state.tip,[0.0,0.0,20.0],gate,"Collapsed zero-cone permitted tip")

func refusal_and_state_checks() -> void:
	for flags in [0x01,0x11,0x21,0x33,0x71,0xB1,0x131]: check(Candidate.parameters({"raw_rule_flags":flags}).has("error"),"Unsupported mode refused "+str(flags))
	check(Candidate.parameters({"angle_limit":PI/2.0}).has("error"),"Unsupported wide cone refused")
	check(Candidate.parameters({"length":0.0}).has("error"),"Zero length refused")
	for columns in [[[-1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]],[[2.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]],[[1.0,0.1,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]]:
		check(Candidate.goal([0.0,0.0,0.0],columns).has("error"),"Mirrored/nonuniform/sheared mathematical goal refused")
	var p: Dictionary = Candidate.parameters().parameters
	var source := {"retained":{"opaque":[1,2,3]}}
	var made := Candidate.create({"a":p,"b":p},source)
	var actor = made.actor
	var goal: Dictionary = Candidate.goal().goal
	var goals := {"a":goal,"b":goal}
	actor.reset(goals)
	check(actor.snapshot().active and actor.snapshot().tick == 0 and actor.snapshot().states.size() == 2,"Two-rule refusal setup is actually active")
	var before := var_to_bytes(actor.snapshot())
	check(actor.step(0,goals).has("error") and var_to_bytes(actor.snapshot()) == before,"Repeated tick atomic refusal")
	check(actor.step(2,goals).has("error") and var_to_bytes(actor.snapshot()) == before,"Skipped tick atomic refusal")
	check(actor.step(1,{"a":goal}).has("error") and var_to_bytes(actor.snapshot()) == before,"Missing-rule atomic refusal")
	check(actor.step(1,goals,{"unknown":[1.0,0.0,0.0]}).has("error") and var_to_bytes(actor.snapshot()) == before,"Unknown-force atomic refusal")
	check(actor.step(1,goals,{"b":[NAN,0.0,0.0]}).has("error") and var_to_bytes(actor.snapshot()) == before,"Invalid second-rule force changes no state")
	source.retained.opaque.append(4)
	var returned: Dictionary = actor.metadata_copy()
	returned.retained.opaque.append(5)
	check(actor.metadata_copy().retained.opaque == [1,2,3],"Raw metadata caller/getter isolation")
	var other = Candidate.create({"a":p,"b":p}).actor
	other.reset(goals)
	var other_before := var_to_bytes(other.snapshot())
	var result: Dictionary = actor.step(1,goals,{"a":[10.0,3.0,0.0]})
	check(not result.has("error") and var_to_bytes(other.snapshot()) == other_before,"Separate actor state isolation")
	if not result.has("error"):
		var stable := var_to_bytes(actor.snapshot())
		result.outputs.a.state.tip[0] += 999.0
		check(var_to_bytes(actor.snapshot()) == stable,"Returned output does not alias internal states")
	var active_reset: Dictionary = actor.reset(goals)
	check(not active_reset.has("error") and var_to_bytes(actor.snapshot()) == before,"Reset while running clears numerical history and tick exactly")
	actor.stop()
	check(not actor.snapshot().active and actor.snapshot().states.is_empty() and actor.step(1,goals).has("error"),"Stopped state cannot resurrect")
	actor.reset(goals)
	check(var_to_bytes(actor.snapshot()) == before,"Reset seeds original current-goal state exactly")

func packed_vector(value: Vector3) -> String:
	return PackedVector3Array([value]).to_byte_array().hex_encode()

func alias_boundary_checks() -> void:
	var input_base: Array = [0.0,0.0,0.0]
	var input_basis: Array = [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]
	var prepared_goal: Dictionary = Candidate.goal(input_base,input_basis).goal
	var original_goal := var_to_bytes(prepared_goal)
	input_base[0] = 999.0
	input_basis[2][2] = 2.0
	check(var_to_bytes(prepared_goal) == original_goal,"Goal factory copies nested input arrays")
	var source_parameters: Dictionary = Candidate.parameters().parameters
	var source_specs := {"r":source_parameters}
	var source_gravity: Array = [0.0,0.0,-1.0]
	var actor = Candidate.create(source_specs,null,source_gravity).actor
	var control = Candidate.create(source_specs,null,source_gravity).actor
	source_parameters.yaw_stiffness = 999.0
	source_specs.r.pitch_damping = 888.0
	source_gravity[2] = 1.0
	actor.reset({"r":prepared_goal})
	control.reset({"r":Candidate.goal().goal})
	var stable := var_to_bytes(actor.snapshot())
	var escaped: Dictionary = actor.snapshot()
	escaped.states.r.tip[0] = 777.0
	escaped.states.r.velocity[1] = 666.0
	escaped.states.clear()
	check(var_to_bytes(actor.snapshot()) == stable,"Mutating returned snapshot cannot change internal state")
	prepared_goal.base[0] = 0.1
	check(var_to_bytes(actor.snapshot()) == stable,"Reusing and editing a goal after reset does not alias seeded state")
	var result: Dictionary = actor.step(1,{"r":prepared_goal})
	var reference: Dictionary = control.step(1,{"r":Candidate.goal([0.1,0.0,0.0]).goal})
	check(not result.has("error") and not reference.has("error") and var_to_bytes(result) == var_to_bytes(reference),"Copied params/gravity and newly sampled edited goal match cold control")
	if not result.has("error"):
		stable = var_to_bytes(actor.snapshot())
		result.outputs.r.state.velocity[0] = 555.0
		result.outputs.r.basis[0][0] = 444.0
		result.outputs.r.unconstrained_tip[0] = 333.0
		check(var_to_bytes(actor.snapshot()) == stable,"Mutating nested result arrays cannot change internal state")

func array_from_vector(value: Vector3) -> Array: return [float(value.x),float(value.y),float(value.z)]

func adapter_checks(oracle: Dictionary) -> void:
	adapter_started = true
	for row in oracle.float32_vectors:
		var value := Vector3(float(row.input[0]),float(row.input[1]),float(row.input[2]))
		check(value.is_finite() and packed_vector(value) == row.packed_float32_hex,"Exact Vector3 IEEE754 float32 adapter words")
		adapter_rows.append({"kind":"Vector3","actual_hex":packed_vector(value),"expected_hex":row.packed_float32_hex})
	for row in oracle.float32_bases:
		var columns: Array[Vector3] = []
		for a in row.input_columns: columns.append(Vector3(float(a[0]),float(a[1]),float(a[2])))
		var basis := Basis(columns[0],columns[1],columns[2])
		for i in range(3): check(packed_vector(basis[i]) == row.packed_columns_float32_hex[i],"Exact Basis float32 column "+str(i))
		var determinant := basis.determinant()
		var error := absf(determinant-float(row.rounded_determinant_scalar64))
		check(basis.is_finite() and determinant > 0.0 and error <= float(row.native_float32_determinant_error_bound),"Basis determinant preregistered IEEE754 bound")
		var quantized: Array = [array_from_vector(basis[0]),array_from_vector(basis[1]),array_from_vector(basis[2])]
		var accepts := Candidate.goal([0.0,0.0,0.0],quantized).has("goal")
		check(accepts == row.strict_math_validator_accepts_quantized_columns,"Float32 boundary remains separate from strict scalar64 goal domain")
		adapter_rows.append({"kind":"Basis","actual_determinant":determinant,"scalar64_rounded_reference":row.rounded_determinant_scalar64,"error_bound":row.native_float32_determinant_error_bound,"strict_math_goal_accepts":accepts})

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 3: push_error("Root lease, public oracle and fresh result path required"); quit(2); return
	var lease_result := read_json(args[0],1024*1024)
	if lease_result.has("error"): push_error(lease_result.error); quit(2); return
	var lease: Dictionary = lease_result.data
	if lease.get("format") != "has_source0x31_godot_math_lease_1" or lease.get("phase") != "ROOT_APPROVED_AFTER_FULL_AND_FK_PASS" or lease.get("full_status") != "PASS" or lease.get("FK_status") != "PASS" or lease.get("root_closed_both") != true or float(lease.get("expires_unix",0)) <= Time.get_unix_time_from_system():
		push_error("Fresh root full/FK PASS and closure authority required"); quit(2); return
	if FileAccess.get_sha256(OS.get_executable_path()) != str(lease.get("engine_sha256","")) or DisplayServer.get_name() != "headless":
		push_error("Locked headless engine required"); quit(2); return
	for name in ["candidate","harness","oracle","full_receipt","FK_receipt","root_closure"]:
		if not lease.get("files",{}).has(name): push_error("Incomplete root input lock"); quit(2); return
		var pin: Dictionary = lease.files[name]
		if str(pin.get("sha256","")).length() != 64 or not str(pin.get("path","")).is_absolute_path() or FileAccess.get_sha256(str(pin.get("path",""))) != str(pin.get("sha256","")): push_error("Locked input changed: "+name); quit(2); return
	locked_files = lease.files.duplicate(true)
	if FileAccess.get_sha256("res://candidate.gd") != str(lease.files.candidate.sha256) or FileAccess.get_sha256("res://harness.gd") != str(lease.files.harness.sha256) or FileAccess.get_sha256(args[1]) != str(lease.files.oracle.sha256):
		push_error("Wrong staged source/oracle"); quit(2); return
	result_path = args[2]
	if result_path != str(lease.get("public_result","")) or FileAccess.file_exists(result_path): push_error("Fresh exact root-owned result required"); quit(2); return
	context = {"source_HEAD":lease.get("source_HEAD",""),"full_receipt_sha256":lease.files.full_receipt.sha256,"FK_receipt_sha256":lease.files.FK_receipt.sha256,"closure_sha256":lease.files.root_closure.sha256}
	var input := read_json(args[1],4*1024*1024)
	if input.has("error"): check(false,input.error); close_result("FAILED_ORACLE"); return
	var oracle: Dictionary = input.data
	if oracle.get("format") != "has_public_source0x31_scalar64_oracle_1" or oracle.get("flags_hex") != "0x31" or int(oracle.get("fixed_hz",0)) != 120:
		check(false,"Wrong synthetic oracle schema"); close_result("FAILED_ORACLE"); return
	if oracle.get("reference_sha256") != "dd472f2b4de64adebc83a03c2e812ac2e14805c752b220c26c53dd58bf99519c" or not oracle.get("preregistered_gates",{}).get("declared_before_engine_parse",false) or float(oracle.preregistered_gates.scalar64_trajectory_absolute) != 1e-9 or float(oracle.preregistered_gates.independent_rational_absolute) != 1e-12 or float(oracle.preregistered_gates.zero_cone_rest_displacement) != 1e-10:
		check(false,"Changed reference or preregistered gates"); close_result("FAILED_ORACLE"); return
	oracle_hash = FileAccess.get_sha256(args[1])
	independent_oracles(oracle)
	zero_cone(oracle)
	refusal_and_state_checks()
	alias_boundary_checks()
	adapter_checks(oracle)
	for row in oracle.sequences:
		var result := sequence_pass(row,float(oracle.preregistered_gates.scalar64_trajectory_absolute),true)
		if result.has("error"): close_result("FAILED_SEQUENCE",{"reason":result.error}); return
		if row.id == "known_two_independent_rule_replay":
			var replay := sequence_pass(row,float(oracle.preregistered_gates.scalar64_trajectory_absolute),false)
			check(not replay.has("error") and result.sample_bytes == replay.get("sample_bytes",PackedByteArray()) and var_to_bytes(result.snapshot) == var_to_bytes(replay.get("snapshot",{})),"Independent actor reset/replay exact engine bytes")
	close_result("PASSED_SCALAR64_SYNTHETIC_ENGINE_MATH_ONLY" if failures == 0 else "FAILED_MATHEMATICAL_OR_ADAPTER_CHECKS")
