extends SceneTree
# OUTPUT-ONLY CANDIDATE. Unparsed/unrun until the root releases its runtime lease.
# Uses the actual standard loader/model; never installs an adapter or dynamics.
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
const ImportDefinition = preload("res://src/pose_editor.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
var checks := 0
var failures := 0
var failure_labels: Array[String] = []
var output_path := ""
var maximum_bone_error := 0.0
var maximum_tip_error := 0.0
var maximum_rest_error := 0.0
var case_rows: Array = []
func _initialize() -> void:
	create_timer(120.0).timeout.connect(func(): push_error("Headless transport probe watchdog"); quit(2))
	call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		if failure_labels.size() < 20: failure_labels.append(label)
		print("FAIL " + label)
func vector(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))
func from_matrix(a: Array) -> Transform3D:
	return Transform3D(Basis(Vector3(a[0], a[4], a[8]), Vector3(a[1], a[5], a[9]), Vector3(a[2], a[6], a[10])), Vector3(a[3], a[7], a[11]))
func matrix_error(actual: Transform3D, expected: Transform3D) -> float:
	var result := actual.origin.distance_to(expected.origin)
	for c in 3:
		for r in 3: result = maxf(result, absf(actual.basis[c][r] - expected.basis[c][r]))
	return result
func native_snapshot(actor: RefCounted) -> PackedByteArray:
	var rows: Array = [actor.data, actor.authored_keys(), actor.root.transform]
	for id in actor.order:
		var info: Dictionary = actor.bones[id]
		rows.append([id, info.index, info.base, info.skeleton.get_bone_rest(info.index), info.skeleton.get_bone_pose(info.index)])
	return var_to_bytes(rows)
func save_result(status: String, extra: Dictionary = {}) -> void:
	var result := {"format":"has_actual_standard_model_transport_probe_1", "status":status, "checks":checks, "failures":failures, "failure_labels":failure_labels, "configurations":case_rows.size(), "maximum_bone_matrix_error":maximum_bone_error, "maximum_native_Z_tip_distance":maximum_tip_error,"maximum_skeleton_global_rest_error":maximum_rest_error, "case_rows":case_rows, "scope":{"actual_scene3d_loader":true,"actual_model_inventory_and_apply":true,"full_Studio_GUI_world_or_project_save":false,"posed_skin_vertex_or_render_transport":"UNRUN","source_conversion_scales":[0.01905],"model_root_uniform_scales":[1.0,2.0],"native_dynamics":false}}
	result.merge(extra)
	var file := FileAccess.open(output_path, FileAccess.WRITE)
	if file == null: push_error("Cannot write owned headless result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("NATIVE_COORD_TRANSPORT " + JSON.stringify({"status":status,"checks":checks,"failures":failures,"configurations":case_rows.size(),"bone_max":maximum_bone_error,"tip_max":maximum_tip_error}))
func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2: push_error("Private oracle and fresh result path required"); quit(2); return
	output_path = args[1]
	if FileAccess.file_exists(output_path): push_error("Fresh result path required"); quit(2); return
	var oracle_file := FileAccess.open(args[0],FileAccess.READ)
	if oracle_file == null or oracle_file.get_length() > 16 * 1024 * 1024: push_error("Private oracle unavailable or over16MiB"); quit(2); return
	var parsed := JSON.new()
	if parsed.parse(oracle_file.get_as_text()) != OK or not parsed.data is Dictionary: push_error("Private oracle invalid"); quit(2); return
	oracle_file.close()
	var oracle: Dictionary = parsed.data
	if oracle.get("format") != "has_private_native_transport_oracle_1": push_error("Private oracle format"); quit(2); return
	var source: String = oracle.glb_path
	var before_sha := FileAccess.get_sha256(source)
	check(before_sha == oracle.glb_sha256,"locked actual GLB identity")
	var definition_reader = ImportDefinition.new()
	var definition: Dictionary = definition_reader.definition(source)
	definition_reader.free()
	if definition.has("error"): check(false,"actual import definition refused"); save_result("FAILED_DEFINITION"); quit(1); return
	var decoded: Dictionary = SceneIO.load_glb(source)
	if decoded.has("error"): check(false,"actual standard loader refused"); save_result("FAILED_LOAD"); quit(1); return
	var actor = Model.new()
	actor.root = decoded.scene
	actor.base_root = actor.root.transform
	actor.data = definition.data
	actor.inventory(actor.root)
	var host := Node3D.new()
	host.name = "PrivateCoordinateProbe"
	root.add_child(host)
	host.add_child(actor.root)
	check(actor.check_bindings().is_empty(),"actual standard model binding checks")
	var resolution = Bindings.resolve(actor)
	check(resolution.status == "bound_inactive" and resolution.bindings.size() == 69,"actual69 inactive native identity bindings")
	if resolution.status != "bound_inactive": save_result("FAILED_BINDING",{"reason":resolution.reason}); host.free(); quit(1); return
	actor.apply(0,true)
	await process_frame
	var baseline: Dictionary = actor.data.duplicate(true)
	var neutral_snapshot := native_snapshot(actor)
	var actual_rest_rows: Array = []
	for ni in 69:
		var binding = resolution.bindings[ni]
		actual_rest_rows.append({"native_index":ni,"skeleton_bone_index":binding.skeleton_bone_index,"gltf_node_index":binding.gltf_node_index})
	var rules_by_native := {}
	for row in oracle.rule_lengths: rules_by_native[int(row.native_index)] = float(row.length_scaled)
	check(rules_by_native.size() == 49,"49 private native-Z tip lengths")
	var baseline_checks := checks
	for candidate in oracle.cases:
		actor.data = baseline.duplicate(true)
		actor.data.position = candidate.root.position.duplicate()
		actor.data.rotation_xyzw = candidate.root.rotation_xyzw.duplicate()
		actor.data.scale = candidate.root.scale
		var pose := {}
		for row in candidate.pose:
			var id: String = resolution.by_native[int(row.native_index)]
			pose[id] = {"position":row.position.duplicate(),"rotation_xyzw":row.rotation_xyzw.duplicate()}
		actor.data.pose = pose
		actor.apply(0,true)
		var bone_error := 0.0
		var tip_error := 0.0
		var rest_error := 0.0
		var tolerance: float = 0.00002 * float(candidate.root_scale)
		for ni in 69:
			var id: String = resolution.by_native[ni]
			var actual: Transform3D = actor.bone_transform(id)
			var expected := from_matrix(candidate.expected_world_bones[ni])
			var error := matrix_error(actual,expected)
			bone_error = maxf(bone_error,error)
			check(error <= tolerance,str(candidate.id)+" native="+str(ni)+" FK/rest world")
		for ni in 69:
			var binding = resolution.bindings[ni]
			var actual_rest: Transform3D = binding.skeleton.global_transform * binding.skeleton.get_bone_global_rest(binding.skeleton_bone_index)
			var expected_rest := from_matrix(oracle.rest_by_root_id[str(candidate.root.id)][ni])
			var error := matrix_error(actual_rest,expected_rest)
			rest_error = maxf(rest_error,error)
			check(error <= tolerance,str(candidate.id)+" native="+str(ni)+" skeleton global rest")
		for row in candidate.expected_native_Z_tips:
			var ni := int(row.native_index)
			var id: String = resolution.by_native[ni]
			var actual: Vector3 = actor.bone_transform(id) * Vector3(0,0,rules_by_native[ni])
			var error := actual.distance_to(vector(row.expected_position))
			tip_error = maxf(tip_error,error)
			check(error <= tolerance,str(candidate.id)+" native="+str(ni)+" native-Z world tip")
		maximum_bone_error = maxf(maximum_bone_error,bone_error)
		maximum_tip_error = maxf(maximum_tip_error,tip_error)
		maximum_rest_error = maxf(maximum_rest_error,rest_error)
		case_rows.append({"case":candidate.id,"root_uniform_scale":candidate.root_scale,"bone_world_max_error":bone_error,"skeleton_global_rest_max_error":rest_error,"tip_world_max_distance":tip_error,"tolerance":tolerance})
		actor.data = baseline.duplicate(true)
		actor.apply(0,true)
		check(actor.data == baseline,str(candidate.id)+" authored record reset unchanged")
		check(native_snapshot(actor) == neutral_snapshot,str(candidate.id)+" exact rest/base/pose reset")
	check(Bindings.current(actor,resolution),"inactive identity bindings remain current")
	check(actor.live_pose == null and actor.live_world_transform == null,"no live simulation state")
	check(FileAccess.get_sha256(source) == before_sha,"original actual GLB unchanged after resets")
	var native: Dictionary = actor.data.metadata.native_parameters.native_parameters
	check(native.source_jiggle.applied == false and native.source_jiggle.full_native_rule_layout_verified == false and native.source_export_crosswalk.native_solver == "not_implemented","native metadata remains inert and partial-layout")
	save_result("PASSED" if failures == 0 else "FAILED",{"numeric_native_runtime_joins":actual_rest_rows,"case_check_count":checks-baseline_checks,"authored_source_reset_preserved":native_snapshot(actor)==neutral_snapshot})
	host.free()
	actor = null
	await process_frame
	quit(0 if failures == 0 else 1)
