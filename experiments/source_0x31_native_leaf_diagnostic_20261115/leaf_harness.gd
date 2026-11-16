extends SceneTree
# SOURCE-ONLY readiness harness. No registration, GUI, body/fan/Record or saves.
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
const ImportDefinition = preload("res://src/pose_editor.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Bounds = preload("res://src/pose_bounds.gd")
const Adapter = preload("res://leaf_adapter.gd")
const Capture = preload("res://weighted_capture.gd")
const Math = preload("res://leaf_candidate.gd")
const GLB_SHA := "4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"
const PARAM_SHA := "b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed"
const MDL_SHA := "8da09c905227ddc8eef73a3f83594a4eb1c3a6d5304ee41ba5471bef834bc716"
const EPS := 0.00002
const MOTION_MIN := 0.00001
const FRAME := 12
const TICKS := 120
var checks := 0
var failures := 0
var labels: Array[String] = []
var result_path := ""
var lease: Dictionary = {}
var rows: Array = []
var source_pins: Array = []
var model_started := false
var weighted_started := false
var live_started := false
var dynamics_steps := 0

func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		if labels.size() < 32: labels.append(label)
		print("FAIL "+label)

func read_json(path: String, bound: int) -> Dictionary:
	var file := FileAccess.open(path,FileAccess.READ)
	if file == null or file.get_length() > bound: return {"error":"Unavailable/oversized locked JSON"}
	var parser := JSON.new()
	var error := parser.parse(file.get_as_text())
	file.close()
	return {"data":parser.data} if error == OK and parser.data is Dictionary else {"error":"Invalid locked JSON"}

func source_unchanged() -> bool:
	for name in lease.files:
		var pin: Dictionary = lease.files[name]
		if FileAccess.get_sha256(str(pin.path)) != str(pin.sha256): return false
	for pin in source_pins:
		if FileAccess.get_sha256("res://"+str(pin.path)) != str(pin.sha256): return false
	return true

func finish(status: String, reason := "") -> void:
	check(source_unchanged(),"All locked original/source/proof bytes preserved")
	if failures > 0 and status == "PASSED_NATIVE8_LEAF_READINESS_ONLY": status = "FAILED_NATIVE8_READINESS"
	var result := {"format":"has_actual_native8_leaf_readiness_1","status":status,"checks":checks,"failures":failures,"failure_labels":labels,"reason":reason,"cases":rows,
		"native_index":8,"native_parent_index":7,"native_rules_retained":49,"native_bones_retained":69,"source_conversion_scale":0.01905,"source_glb_sha256":GLB_SHA,"parameters_sha256":PARAM_SHA,"dynamics_steps":dynamics_steps,
		"scope":{"actual_Model_load_attempted":model_started,"actual_CPU_weighted_query_exercised":weighted_started,"actual_live_pose_application_attempted":live_started,"GPU_render_fidelity":false,"full_GUI_body_fan_Record_HAS_export_integration":false,
		"external_input":"Temporary synthetic world acceleration, not an actual fan or native Source wind API","SDK_executed":false,"artist_native_motion_fidelity":"UNQUALIFIED","raw_arrays_published":false,"source_metadata_activation_changed":false},
		"gates":{"world_or_basis_boundary":EPS,"meaningful_geometry_displacement_per_root_scale":MOTION_MIN,"unaffected_and_Off":"Exact private-byte/hash equality"}}
	var file := FileAccess.open(result_path,FileAccess.WRITE)
	if file == null: push_error("Cannot write fresh root-owned aggregate result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("NATIVE8_LEAF "+JSON.stringify({"status":status,"checks":checks,"failures":failures,"cases":rows.size()}))
	quit(0 if failures == 0 and status == "PASSED_NATIVE8_LEAF_READINESS_ONLY" else 1)

func quaternion_array(q: Quaternion) -> Array: return [q.x,q.y,q.z,q.w]

func owned_pose(resolution: RefCounted, later: bool) -> Dictionary:
	return {resolution.by_native[7]:{"position":[0.0,0.0,0.0],"rotation_xyzw":quaternion_array(Quaternion(Vector3.RIGHT,-0.11 if later else 0.17))},
		resolution.by_native[8]:{"position":[-0.0003,0.0009,-0.0002] if later else [0.001,-0.0015,0.0007],"rotation_xyzw":quaternion_array(Quaternion(Vector3.UP,0.23 if later else 0.13))},
		resolution.by_native[17]:{"position":[0.0,0.0,0.0],"rotation_xyzw":quaternion_array(Quaternion(Vector3.FORWARD,-0.08 if later else 0.12))}}

func exact_snapshot(actor: RefCounted) -> PackedByteArray:
	# Native arrays/rests remain in memory. Only equality/hash leaves this function.
	var values: Array = [actor.data,actor.authored_keys(),actor.root.transform,actor.root.global_transform]
	for id in actor.order:
		var info: Dictionary = actor.bones[id]
		values.append([id,info.base,info.skeleton.get_bone_rest(info.index),info.skeleton.get_bone_pose(info.index),actor.bone_transform(id)])
	return var_to_bytes(values)

func unrelated_bytes(actor: RefCounted, selected: String) -> PackedByteArray:
	var values: Array = []
	for id in actor.order:
		if id != selected: values.append([id,actor.bone_transform(id)])
	return var_to_bytes(values)

func rotation_error(actual: Transform3D, desired: Array, scale: float) -> float:
	var error := 0.0
	for i in range(3):
		for j in range(3): error = maxf(error,absf(float(actual.basis[i][j])/scale-float(desired[i][j])))
	return error

func simulation(actor: RefCounted, resolution: RefCounted, native_rule: Dictionary, name: String, strength: float, baseline: Dictionary, snap12: PackedByteArray, snap24: PackedByteArray) -> Dictionary:
	var id: String = resolution.by_native[8]
	var binding: RefCounted = resolution.bindings[8]
	actor.live_pose = null
	actor.apply(FRAME,false)
	var authored: Dictionary = actor.sample(FRAME,false).duplicate(true)
	var source_pose := var_to_bytes(authored)
	var unrelated := unrelated_bytes(actor,id)
	var goal_world: Transform3D = actor.bone_transform(id)
	var mapped := Adapter.frame64(goal_world)
	if mapped.has("error"): return mapped
	var prepared := Adapter.parameters_from_rule(native_rule,float(mapped.scale))
	if prepared.has("error"): return prepared
	# Existing source world-Z gravity becomes HAS world-Y, never model-local.
	var made := Math.create({"leaf":prepared.parameters},null,[0.0,-1.0,0.0])
	if made.has("error"): return made
	var runner = made.actor
	var reset: Dictionary = runner.reset({"leaf":mapped.goal})
	if reset.has("error"): return reset
	var axis: Array = mapped.rotation[0]
	var force: Array = Math.v_mul(axis,strength)
	var maximum_basis_error := 0.0
	var maximum_tip_error := 0.0
	var maximum_adapter_error: float = mapped.correction_max
	var maximum_closure_error := 0.0
	var actual_projections := 0
	var last_output: Dictionary = {}
	for tick in range(1,TICKS+1):
		# live_pose is a complete replacement, so re-establish authored goals
		# before solving and preserve every other sampled channel in the overlay.
		actor.live_pose = null
		actor.apply(FRAME,false)
		var current_goal := Adapter.frame64(actor.bone_transform(id))
		if current_goal.has("error"): return current_goal
		var step: Dictionary = runner.step(tick,{"leaf":current_goal.goal},{"leaf":force})
		if step.has("error"): return step
		dynamics_steps += 1
		last_output = step.outputs.leaf
		if last_output.angle_projected: actual_projections += 1
		var overlay := Adapter.overlay(actor,id,authored,last_output.basis)
		if overlay.has("error"): return overlay
		maximum_adapter_error = maxf(maximum_adapter_error,float(overlay.basis_adapter_error))
		maximum_closure_error = maxf(maximum_closure_error,float(overlay.parent_closure_error))
		actor.live_pose = overlay.pose
		live_started = true
		actor.apply(FRAME,false)
		var actual: Transform3D = actor.bone_transform(id)
		var basis_error := rotation_error(actual,last_output.basis,float(mapped.scale))
		var tip: Vector3 = actual*Vector3(0.0,0.0,float(native_rule.parameters.length)*Adapter.SOURCE_SCALE)
		var desired_tip := Vector3(last_output.state.tip[0],last_output.state.tip[1],last_output.state.tip[2])
		var tip_error := tip.distance_to(desired_tip)
		maximum_basis_error = maxf(maximum_basis_error,basis_error)
		maximum_tip_error = maxf(maximum_tip_error,tip_error)
		check(basis_error <= EPS,name+" desired/math versus actual bone orientation")
		check(tip_error <= EPS*float(mapped.scale),name+" native-Z tip transport with scale applied once")
		check(actual.origin.distance_to(goal_world.origin) <= EPS*float(mapped.scale),name+" authored leaf origin retained")
		check(unrelated_bytes(actor,id) == unrelated,name+" all68 unaffected world bones exact")
		check(var_to_bytes(actor.sample(FRAME,false)) == source_pose,name+" authored sample not overwritten")
	var moved := Capture.capture(actor,binding)
	var delta := Capture.difference(baseline,moved,MOTION_MIN*float(mapped.scale))
	if delta.has("error"): return delta
	check(delta.unaffected_exact,name+" zero-weight9509 region exact")
	if strength != 0.0: check(delta.affected_vertices_moved > 0 and delta.affected_max > MOTION_MIN*float(mapped.scale),name+" actual weighted region measurably deforms")
	runner.stop()
	actor.live_pose = null
	actor.apply(24,false)
	check(exact_snapshot(actor) == snap24,name+" Off-style restore at current keyedframe24 exact")
	actor.apply(FRAME,false)
	check(exact_snapshot(actor) == snap12 and actor.live_pose == null and actor.live_world_transform == null,name+" Off-style restore at nonrestframe12 exact")
	var restored := Capture.capture(actor,binding)
	var restoration := Capture.difference(baseline,restored,0.0)
	if restoration.has("error"): return restoration
	check(restoration.all_points_exact,name+" all actual weighted points restore exactly")
	check(Bindings.current(actor,resolution),name+" retained native metadata/bindings stay inactive/current")
	return {"public":{"profile":name,"synthetic_world_acceleration_magnitude":absf(strength),"world_scale":float(mapped.scale),"native_to_world_factor":float(prepared.unit_factor),"ticks":TICKS,
		"basis_error_max":maximum_basis_error,"tip_error_max":maximum_tip_error,"boundary_adapter_error_max":maximum_adapter_error,"parent_local_closure_error_max":maximum_closure_error,"angle_projection_steps":actual_projections,
		"vertices":moved.vertices,"weighted_to_leaf":moved.affected,"shared_influence_vertices":moved.shared,"unaffected_vertices":moved.unaffected,"weighted_vertices_moved":delta.affected_vertices_moved,"weighted_displacement_max":delta.affected_max,
		"unaffected_exact":delta.unaffected_exact,"Off_all_weighted_points_exact":restoration.all_points_exact,"final_weighted_sha256":moved.points_sha256,"restored_weighted_sha256":restored.points_sha256},
		"private_capture":moved,"private_tip":last_output.state.tip,"private_axis":axis}

func root_case(root_scale: float, moved_root: bool, glb: String) -> Dictionary:
	var reader = ImportDefinition.new()
	var prepared: Dictionary = reader.definition(glb)
	reader.free()
	if prepared.has("error"): return prepared
	var decoded: Dictionary = SceneIO.load_glb(glb)
	if decoded.has("error"): return decoded
	model_started = true
	var actor = Model.new()
	actor.root = decoded.scene
	actor.base_root = actor.root.transform
	actor.data = prepared.data
	actor.inventory(actor.root)
	var host := Node3D.new()
	root.add_child(host); host.add_child(actor.root)
	var resolution: RefCounted = Bindings.resolve(actor)
	if resolution.status != "bound_inactive" or resolution.bindings.size() != 69 or resolution.rule_owner_ids.size() != 49: host.free(); return {"error":"Exact69/49 inactive native profile unavailable"}
	var binding: RefCounted = resolution.bindings[8]
	var skeleton: Skeleton3D = binding.skeleton
	var modifier_nodes: Array = skeleton.find_children("*","SkeletonModifier3D",true,false)
	var modifier_classes := PackedStringArray()
	var modifier_details := PackedStringArray()
	for modifier in modifier_nodes:
		var class_name_value := str(modifier.get_class())
		modifier_classes.append(class_name_value)
		var modifier_parent: Node = modifier.get_parent()
		var direct_parent: bool = modifier_parent == skeleton
		var internal_child := false
		if modifier_parent != null:
			internal_child = modifier_parent.get_children(true).has(modifier) and not modifier_parent.get_children(false).has(modifier)
		var active_value: Variant = "property_unavailable"
		for property_row in modifier.get_property_list():
			if str(property_row.name) == "active":
				active_value = modifier.get("active")
				break
		var simulating: Variant = modifier.call("is_simulating_physics") if modifier.has_method("is_simulating_physics") else "method_unavailable"
		var pending: Array = modifier.get_children(true)
		var visited := 0
		var body_descendants := 0
		while not pending.is_empty() and visited < 10000:
			var descendant: Node = pending.pop_back()
			visited += 1
			if descendant.is_class("PhysicalBone3D"): body_descendants += 1
			pending.append_array(descendant.get_children(true))
		var body_count: Variant = body_descendants if pending.is_empty() else "over_10000_nodes"
		modifier_details.append("class="+class_name_value+";internal="+str(internal_child)+";direct_parent="+str(direct_parent)+";active="+str(active_value)+";is_simulating_physics="+str(simulating)+";PhysicalBone3D_descendants="+str(body_count))
	modifier_classes.sort()
	modifier_details.sort()
	var final_pose_count: int = Bounds.final_pose(skeleton).size()
	var first_failing_guard := "none"
	if binding.native_parent_index != 7: first_failing_guard = "native_parent"
	elif skeleton.show_rest_only: first_failing_guard = "show_rest_only"
	elif not modifier_nodes.is_empty(): first_failing_guard = "modifier_presence"
	elif final_pose_count != 0: first_failing_guard = "final_pose_owner"
	var context_diagnostic := {"native_parent_index":binding.native_parent_index,"expected_native_parent_index":7,"show_rest_only":skeleton.show_rest_only,"modifier_count":modifier_nodes.size(),"modifier_classes":",".join(modifier_classes),"modifier_details":" | ".join(modifier_details),"final_pose_count":final_pose_count,"first_failing_guard":first_failing_guard}
	# Same refusal gate: no modifier is exempted. Physical body counts are
	# actual PhysicalBone3D descendants, never the skeleton's69 pose bones.
	if binding.native_parent_index != 7 or skeleton.show_rest_only or not modifier_nodes.is_empty() or final_pose_count != 0:
		var diagnostic_reason := "Unexpected parent/rest/modifier/final-pose context; diagnostic="+JSON.stringify(context_diagnostic,"",true,true)
		host.free()
		return {"error":diagnostic_reason}
	for index in range(skeleton.get_bone_count()):
		if not skeleton.is_bone_enabled(index) or skeleton.get_bone_parent(index) == binding.skeleton_bone_index: host.free(); return {"error":"Exact enabled native8 leaf profile required"}
	var native: Dictionary = actor.data.metadata.native_parameters.native_parameters
	var rule: Dictionary = {}
	for value in native.source_jiggle.rules:
		if int(value.native_bone_index) == 8: rule = value
	if rule.is_empty() or native.bones[8].name != "FrontHair1": host.free(); return {"error":"Retained FrontHair1 rule unavailable"}
	actor.data.position = [0.37,-0.22,0.41] if moved_root else [0.0,0.0,0.0]
	actor.data.rotation_xyzw = quaternion_array(Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)) if moved_root else [0.0,0.0,0.0,1.0]
	actor.data.scale = root_scale
	var transform := {"position":actor.data.position.duplicate(true),"rotation_xyzw":actor.data.rotation_xyzw.duplicate(true),"scale":root_scale}
	actor.data.pose = owned_pose(resolution,false)
	actor.data.draft_frame = 0
	actor.data.pose_keys = [{"frame":0,"pose":owned_pose(resolution,false),"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":owned_pose(resolution,true),"transform":transform.duplicate(true),"interpolation":"linear"}]
	if not Model.validate(actor.data,48).is_empty() or not actor.check_bindings().is_empty(): host.free(); return {"error":"Owned nonrest keyed fixture refused by actual model"}
	actor.apply(24,false)
	await process_frame
	var snap24 := exact_snapshot(actor)
	actor.apply(FRAME,false)
	await process_frame
	var snap12 := exact_snapshot(actor)
	var baseline := Capture.capture(actor,binding)
	if baseline.has("error"): host.free(); return baseline
	weighted_started = true
	if baseline.vertices != 9661 or baseline.affected != 152 or baseline.shared != 144 or baseline.unaffected != 9509 or baseline.surfaces != 4: host.free(); return {"error":"Actual weighted geometry differs from locked profile"}
	var goal := Adapter.frame64(actor.bone_transform(binding.has_id))
	if goal.has("error"): host.free(); return goal
	var roundtrip := Adapter.overlay(actor,binding.has_id,actor.sample(FRAME,false),goal.rotation)
	if roundtrip.has("error"): host.free(); return roundtrip
	actor.live_pose = roundtrip.pose; live_started = true; actor.apply(FRAME,false)
	check(rotation_error(actor.bone_transform(binding.has_id),goal.rotation,float(goal.scale)) <= EPS,"Authored-rest/parent/live rotation roundtrip before dynamics")
	actor.live_pose = null; actor.apply(FRAME,false)
	check(exact_snapshot(actor) == snap12,"Initial roundtrip Off restores complete authored model")
	var results := {}
	for profile in [{"name":"control","strength":0.0},{"name":"positive3","strength":3.0},{"name":"negative3","strength":-3.0},{"name":"positive12","strength":12.0},{"name":"positive50","strength":50.0},{"name":"repeat12","strength":12.0}]:
		var observed := simulation(actor,resolution,rule,str(profile.name),float(profile.strength),baseline,snap12,snap24)
		if observed.has("error"): host.free(); return observed
		rows.append(observed.public)
		results[profile.name] = observed
	var control: Dictionary = results.control
	for name in ["positive3","negative3","positive12","positive50"]:
		var delta := Capture.difference(control.private_capture,results[name].private_capture,MOTION_MIN*root_scale)
		if delta.has("error"): host.free(); return delta
		check(delta.affected_max > MOTION_MIN*root_scale,"External-input weighted effect differs from gravity control "+name)
	var plus := Math.v_dot(Math.v_sub(results.positive3.private_tip,control.private_tip),control.private_axis)
	var minus := Math.v_dot(Math.v_sub(results.negative3.private_tip,control.private_tip),control.private_axis)
	check(plus > MOTION_MIN*root_scale and minus < -MOTION_MIN*root_scale,"Opposite temporary world accelerations move tip oppositely")
	check(results.positive12.public.final_weighted_sha256 == results.repeat12.public.final_weighted_sha256,"Repeated cleared-state cycle produces exact weighted result")
	check(native.source_jiggle.applied == false and native.source_jiggle.full_native_rule_layout_verified == false and native.source_export_crosswalk.native_solver == "not_implemented","Native metadata activation/full-layout flags remain unchanged")
	host.free()
	actor = null
	await process_frame
	return {"ok":true}

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2: push_error("Fresh post-PASS leaf root lease and public result required"); quit(2); return
	var parsed := read_json(args[0],1024*1024)
	if parsed.has("error"): push_error(parsed.error); quit(2); return
	lease = parsed.data
	if lease.get("format") != "has_native8_leaf_readiness_lease_1" or lease.get("phase") != "ROOT_APPROVED_AFTER_FULL_FK_MATH_AND_CLOSURE" or lease.get("full_status") != "PASS" or lease.get("FK_status") != "PASS" or lease.get("math_status") != "PASS" or lease.get("root_closed_all") != true or float(lease.get("expires_unix",0)) <= Time.get_unix_time_from_system(): push_error("Fresh root post-PASS/closure authority required"); quit(2); return
	if DisplayServer.get_name() != "headless" or FileAccess.get_sha256(OS.get_executable_path()) != str(lease.get("engine_sha256","")): push_error("Locked headless engine required"); quit(2); return
	for name in ["candidate","adapter","capture","harness","source_lock","glb","parameters","mdl","vvd","full_receipt","FK_receipt","math_receipt","root_closure"]:
		if not lease.get("files",{}).has(name): push_error("Incomplete leaf lock"); quit(2); return
		var pin: Dictionary = lease.files[name]
		if str(pin.get("sha256","")).length() != 64 or not str(pin.get("path","")).is_absolute_path() or FileAccess.get_sha256(str(pin.path)) != str(pin.sha256): push_error("Changed locked leaf input"); quit(2); return
	if FileAccess.get_sha256("res://leaf_candidate.gd") != str(lease.files.candidate.sha256) or FileAccess.get_sha256("res://leaf_adapter.gd") != str(lease.files.adapter.sha256) or FileAccess.get_sha256("res://weighted_capture.gd") != str(lease.files.capture.sha256) or FileAccess.get_sha256("res://leaf_harness.gd") != str(lease.files.harness.sha256): push_error("Wrong staged leaf sources"); quit(2); return
	var source_lock := read_json(str(lease.files.source_lock.path),1024*1024)
	if source_lock.has("error"): push_error(source_lock.error); quit(2); return
	source_pins = source_lock.data.files
	result_path = args[1]
	if result_path != str(lease.get("public_result","")) or FileAccess.file_exists(result_path): push_error("Exact fresh result path required"); quit(2); return
	var adjacent := str(lease.files.glb.path).replace("\\","/").get_base_dir().path_join("parameters.json").simplify_path().to_lower()
	var supplied_report := str(lease.files.parameters.path).replace("\\","/").simplify_path().to_lower()
	if not source_unchanged() or lease.files.glb.sha256 != GLB_SHA or lease.files.parameters.sha256 != PARAM_SHA or lease.files.mdl.sha256 != MDL_SHA or adjacent != supplied_report: check(false,"Exact source/profile/adjacent report context"); finish("FAILED_PREFLIGHT"); return
	for spec in [{"scale":1.0,"moved":false},{"scale":2.0,"moved":true}]:
		var outcome: Dictionary = await root_case(float(spec.scale),bool(spec.moved),str(lease.files.glb.path))
		if outcome.has("error"): check(false,"Native8 bounded readiness refusal"); finish("FAILED_NATIVE8_READINESS",str(outcome.error)); return
	finish("PASSED_NATIVE8_LEAF_READINESS_ONLY" if failures == 0 else "FAILED_NATIVE8_READINESS")
