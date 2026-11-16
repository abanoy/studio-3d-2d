extends SceneTree
# SOURCE ONLY UNPARSED/UNRUN. Root copies to tests/ after its current lease ends.
# No GUI, fake primary, fabricated final-pose provider, or physics emulation.
# CLI: one JSON job with format=has_source_native_five_state_job_2,
# phase=ROOT_APPROVED_HEADLESS_FIVE_STATE_TEST, folder=fresh absolute owned output,
# glb=qualified READ-ONLY owned input, report=its adjacent parameters.json,
# engine_sha256, expected_script_sha256, source_manifest_sha256, root_closed_all,
# expires_unix. This script modifies ONLY three new copies it creates itself.
# Outputs are assertion names/booleans, counts, hashes and scalar metrics only.
# Preregistered: 3 actual Model instances, 120 fixed120Hz ticks/cycle; strict
# state/key/report/Off equality; existing2e-5 transport domain is unchanged.
# Test artifacts remain under folder/state-owned-inputs for root's later cleanup.
# Same-header/body changes preserving size+mtime are OUTSIDE the continuous
# cryptographic guarantee. Full source authentication occurs on create/reload.
# One actual PhysicalBone3D is only an adversarial refusal context. This does
# not qualify a complete69-bone ragdoll, borrowed primary, or body/hair coupling.
const Model = preload("res://src/model.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Definition = preload("res://src/pose_editor.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Native = preload("res://src/source_secondary.gd")
const Secondary = preload("res://src/secondary_live.gd")
const Math = preload("res://src/source_jiggle_math.gd")
const GLB_SHA := "4e6ac7c2a7a84dea4b46b0bcb5724af68781243f57737e555b4cc82f2628b90d"
const REPORT_SHA := "b807fc82ac1b1d1658b659b41250001e3bdecde99c3d32764122c2add6b51eed"
const FRAME := 12
const TICKS := 120
const PLANNED_ASSERTIONS := 266
const SELECTED := [8,17,18,26,27]
const WRAPPER_INVENTORY_CASES := ["source_missing","joints_empty","binding_shape","count","order"]
const NEGATIVES := ["dt_zero","dt_negative","dt_double","dt_nan","force_nan","force_large","force_multiple",
	"chain_id","cached_index","cached_parent","actor_order","actor_index","actor_base","skeleton_rest","ancestor_parent","import_map","native_report",
	"disabled_bone","show_rest_only","foreign_modifier","physical_body","data_sha","source_path","chain_reorder","chain_source_binding","chain_binding_kind","chain_duplicate","force_slot_0","force_slot_1","force_slot_2","force_slot_3","force_slot_4"]
const CREATE_REFUSALS := ["actor_index","ancestor_parent","import_map","native_report","disabled_bone","show_rest_only","foreign_modifier","physical_body","data_sha"]
var job: Dictionary = {}
var named: Dictionary = {}
var failures := 0
var metrics: Dictionary = {}
var actors: Array = []
var hosts: Array = []
var bindings: Array = []
var snapshots: Array = []
var docs: Array = []
var raw_reports: Array = []
var owned_paths: Array[String] = []
var report_paths: Array[String] = []
var original_bytes := PackedByteArray()
var input_sha := ""
var report_sha := ""
var result_path := ""
var ticks_executed := 0
var native_attempted := false
var wrapper_attempted := false

func _initialize() -> void: call_deferred("run")

func check(ok: bool, name: String) -> void:
	if named.has(name): ok = false
	named[name] = ok
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"source_native_state."+name)

func digest(bytes: PackedByteArray) -> String:
	var hash := HashingContext.new(); hash.start(HashingContext.HASH_SHA256); hash.update(bytes)
	return hash.finish().hex_encode()

func bytes_of(value: Variant) -> PackedByteArray: return var_to_bytes(value)
func report_of(actor: RefCounted) -> Dictionary: return actor.data.metadata.native_parameters
func state_bytes(runner: RefCounted) -> PackedByteArray: return bytes_of([runner._tick,runner._chain.snapshot(),runner.configuration_stamp(runner._chain),runner.configuration_stamp(runner._trial),runner._size_tokens,runner._chain_inventory_stamp])
func document_bytes(actor: RefCounted) -> PackedByteArray:
	return bytes_of([actor.data,actor.authored_keys(),actor.sample(FRAME,false),actor.sample(24,false)])

func model_bytes(actor: RefCounted) -> PackedByteArray:
	var values: Array = [actor.data,actor.authored_keys(),actor.root.transform,actor.root.global_transform]
	for id in actor.order:
		var info: Dictionary = actor.bones[id]
		values.append([id,info.base,info.skeleton.get_bone_rest(info.index),info.skeleton.get_bone_pose(info.index),actor.bone_transform(id)])
	return bytes_of(values)

func selected_ids(resolution: RefCounted) -> Array:
	var ids: Array = []
	for index in SELECTED: ids.append(resolution.by_native[index])
	return ids

func unselected_bytes(actor: RefCounted, ids: Array) -> PackedByteArray:
	var values: Array = []
	for key in actor.order:
		if not ids.has(key): values.append([key,actor.bone_transform(key)])
	return bytes_of(values)

func authored_pose(actor: RefCounted, resolution: RefCounted, later: bool) -> Dictionary:
	var pose := {}
	for id in actor.order: pose[id] = Model.identity()
	for spec in [{"native":7,"axis":Vector3.RIGHT,"a":0.17,"b":-0.11},{"native":8,"axis":Vector3.UP,"a":0.13,"b":0.23},{"native":17,"axis":Vector3.FORWARD,"a":0.12,"b":-0.08}]:
		var q := Quaternion(spec.axis,spec.b if later else spec.a)
		pose[resolution.by_native[spec.native]] = {"position":[-0.0003,0.0009,-0.0002] if later and spec.native == 8 else [0.001,-0.0015,0.0007] if spec.native == 8 else [0.0,0.0,0.0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	return pose

func safe_owned_write(path: String, bytes: PackedByteArray) -> bool:
	# Every mutable path is a new file this script created after asserting its
	# directory absent. Passed inputs and arbitrary/root-installed paths cannot
	# enter this allowlist, even through a malformed mutation test parameter.
	if not owned_paths.has(path): return false
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file == null: return false
	file.store_buffer(bytes); file.flush(); var error := file.get_error(); file.close()
	return error == OK

func restore_owned() -> bool:
	var restored := true
	for path in owned_paths:
		if FileAccess.get_sha256(path) != GLB_SHA:
			if not safe_owned_write(path,original_bytes): restored = false
		if FileAccess.get_sha256(path) != GLB_SHA: restored = false
	return restored

func input_unchanged() -> bool:
	return FileAccess.get_sha256(str(job.glb)) == input_sha and FileAccess.get_sha256(str(job.report)) == report_sha

func fresh_baseline_checks(actor: RefCounted, resolution: RefCounted, name: String) -> void:
	actor.live_pose = null; actor.apply(0,false)
	var saved := model_bytes(actor); var report := bytes_of(report_of(actor))
	var sparse: bool = actor.data.pose_keys.is_empty() and actor.data.pose.size() < 69
	var made: Dictionary = Native.create(actor)
	var rest_ok := not made.has("error")
	if rest_ok:
		var step := native_step(made.runner)
		rest_ok = not step.has("error") and step.pose.size() == 5 and made.runner._chain.snapshot().states.size() == 5
		for id in selected_ids(resolution): rest_ok = rest_ok and step.get("pose",{}).get(id,Model.identity()).position == Model.identity().position
		made.runner.dispose()
	check(sparse and rest_ok and model_bytes(actor) == saved and bytes_of(report_of(actor)) == report,"load."+name+".fresh_rest_null")
	var id: String = resolution.by_native[8]
	actor.live_pose = {id:{"position":[0.001,-0.0015,0.0007],"rotation_xyzw":[0.0,0.0,0.0,1.0]}}; actor.apply(0,false)
	var partial: Dictionary = actor.live_pose.duplicate(true)
	made = Native.create(actor)
	var partial_ok := not made.has("error")
	if partial_ok:
		var step := native_step(made.runner)
		partial_ok = not step.has("error") and step.pose.size() == 5
		for selected in selected_ids(resolution): partial_ok = partial_ok and step.get("pose",{}).get(selected,Model.identity()).position == partial.get(selected,Model.identity()).position
		made.runner.dispose()
	actor.live_pose = null; actor.apply(0,false)
	check(partial_ok and model_bytes(actor) == saved and bytes_of(report_of(actor)) == report,"load."+name+".fresh_partial_dictionary")

func load_actor(index: int) -> bool:
	var name: String = ["a","b","c"][index]
	var folder: String = str(job.folder).path_join("state-owned-inputs").path_join("actor_"+name)
	if DirAccess.dir_exists_absolute(folder): return false
	if DirAccess.make_dir_recursive_absolute(folder) != OK: return false
	var glb := folder.path_join("scene.glb"); var report := folder.path_join("parameters.json")
	var copied := DirAccess.copy_absolute(str(job.glb),glb) == OK and DirAccess.copy_absolute(str(job.report),report) == OK
	check(copied and FileAccess.get_sha256(glb) == GLB_SHA and FileAccess.get_sha256(report) == REPORT_SHA,"load."+name+".copied")
	if not copied: return false
	owned_paths.append(glb); report_paths.append(report)
	var reader = Definition.new(); var prepared: Dictionary = reader.definition(glb); reader.free()
	var decoded: Dictionary = SceneIO.load_glb(glb)
	check(not prepared.has("error") and not decoded.has("error"),"load."+name+".actual_Model_SceneIO")
	if prepared.has("error") or decoded.has("error"): return false
	var actor = Model.new(); actor.root = decoded.scene; actor.base_root = actor.root.transform; actor.data = prepared.data; actor.inventory(actor.root)
	var host := Node3D.new(); root.add_child(host); host.add_child(actor.root); hosts.append(host)
	var resolution: RefCounted = Bindings.resolve(actor)
	check(Native.offered(actor) and resolution.status == "bound_inactive" and resolution.bindings.size() == 69 and resolution.rule_owner_ids.size() == 49,"load."+name+".qualified69_49")
	if resolution.status != "bound_inactive": host.free(); return false
	fresh_baseline_checks(actor,resolution,name)
	actor.data.pose = authored_pose(actor,resolution,false)
	var transform := {"position":[0.0,0.0,0.0],"rotation_xyzw":[0.0,0.0,0.0,1.0],"scale":1.0}
	actor.data.pose_keys = [{"frame":0,"pose":authored_pose(actor,resolution,false),"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":authored_pose(actor,resolution,true),"transform":transform.duplicate(true),"interpolation":"linear"}]
	actor.data.draft_frame = 0
	actor.apply(FRAME,false)
	check(Model.validate(actor.data,48).is_empty() and actor.check_bindings().is_empty() and actor.sample(FRAME,false).size() == 69,"load."+name+".complete_nonrest_baseline")
	check(FileAccess.get_sha256(report) == REPORT_SHA,"load."+name+".raw_report_file_exact")
	actors.append(actor); bindings.append(resolution)
	snapshots.append(model_bytes(actor)); docs.append(document_bytes(actor)); raw_reports.append(bytes_of(report_of(actor)))
	return true

func baseline(actor: RefCounted) -> void:
	actor.live_pose = null; actor.live_world_transform = null; actor.apply(FRAME,false)

func create_native(actor: RefCounted) -> Dictionary:
	native_attempted = true
	baseline(actor)
	actor.live_pose = actor.sample(FRAME,false).duplicate(true); actor.apply(FRAME,false)
	return Native.create(actor)

func native_step(runner: RefCounted, wind := Vector3.ZERO, delta := Math.DT, forces: Array = []) -> Dictionary:
	var before: int = runner._tick
	var value: Dictionary = runner.step(delta,wind,forces)
	if runner._tick == before+1: ticks_executed += 1
	return value

func instance_checks() -> void:
	var runners: Array = []
	for actor in actors:
		var made := create_native(actor)
		if made.has("error"):
			check(false,"instances.create3")
			for runner in runners: runner.dispose()
			return
		runners.append(made.runner)
	check(runners.size() == 3 and runners[0] != runners[1] and runners[1] != runners[2] and runners[0].active() and runners[1].active() and runners[2].active(),"instances.create3")
	var seed := state_bytes(runners[0]); var second_seed := state_bytes(runners[1]); var third_seed := state_bytes(runners[2])
	check(seed == second_seed and seed == third_seed,"instances.equal_seed_different_instances")
	for _i in range(TICKS): native_step(runners[0],Vector3(3.0,0.0,0.0))
	check(runners[0]._tick == TICKS and runners[0].processing_samples == TICKS and runners[1].processing_samples == 0 and runners[2].processing_samples == 0 and state_bytes(runners[1]) == second_seed and state_bytes(runners[2]) == third_seed,"instances.A120_preserves_BC")
	for _i in range(TICKS): native_step(runners[1],Vector3(3.0,0.0,0.0))
	check(state_bytes(runners[0]) == state_bytes(runners[1]) and runners[0].processing_samples == TICKS and runners[1].processing_samples == TICKS and runners[2].processing_samples == 0 and state_bytes(runners[2]) == third_seed,"instances.B120_equals_A_C_unused")
	var documents_ok := true
	for i in range(3): documents_ok = documents_ok and document_bytes(actors[i]) == docs[i] and bytes_of(report_of(actors[i])) == raw_reports[i]
	check(documents_ok,"instances.keys_complete_pose_raw_reports_unchanged")
	for runner in runners: runner.dispose()
	check(not runners[0].active() and not runners[1].active() and not runners[2].active(),"instances.dispose3_inactive")
	var again := create_native(actors[0])
	check(not again.has("error") and again.runner._tick == 0 and state_bytes(again.runner) == seed,"instances.reenable_exact_seed")
	if not again.has("error"): again.runner.dispose()
	for actor in actors: baseline(actor)

func refused_before_commit(runner: RefCounted, label: String, delta: float, wind: Vector3, forces: Array) -> void:
	var saved := state_bytes(runner); var doc := document_bytes(runner.actor)
	var returned := native_step(runner,wind,delta,forces)
	check(returned.has("error"),"negative."+label+".refused")
	check(state_bytes(runner) == saved,"negative."+label+".state_atomic")
	check(document_bytes(runner.actor) == doc,"negative."+label+".keys_report_unchanged")

func negative_case(kind: String) -> void:
	var actor: RefCounted = actors[0]; var resolution: RefCounted = bindings[0]
	var id: String = resolution.by_native[8]; var other: String = resolution.by_native[17]
	var made := create_native(actor)
	if made.has("error"): check(false,"negative."+kind+".seeded"); return
	var runner: RefCounted = made.runner
	var warm := native_step(runner,Vector3(1.0,0.0,0.0))
	check(not warm.has("error") and runner._tick == 1,"negative."+kind+".seeded")
	var original_data: Dictionary = actor.data.duplicate(true)
	var original_map: Dictionary = actor.root.get_meta("has_source_bones",{}).duplicate(true)
	var original_order: Array = actor.order.duplicate()
	var original_info: Dictionary = actor.bones[id].duplicate()
	var sk: Skeleton3D = resolution.bindings[8].skeleton
	var index: int = resolution.bindings[8].skeleton_bone_index
	var ancestor_index: int = resolution.bindings[7].skeleton_bone_index
	var old_rest := sk.get_bone_rest(index); var old_parent := sk.get_bone_parent(ancestor_index)
	var old_enabled := sk.is_bone_enabled(index); var old_show := sk.show_rest_only
	var node: Node = null
	var simulator: PhysicalBoneSimulator3D = null
	var delta: float = Math.DT; var wind := Vector3.ZERO; var forces: Array = []
	match kind:
		"dt_zero": delta = 0.0
		"dt_negative": delta = -Math.DT
		"dt_double": delta = Math.DT*2.0
		"dt_nan": delta = NAN
		"force_nan": wind = Vector3(NAN,0.0,0.0)
		"force_large": wind = Vector3(1000001.0,0.0,0.0)
		"force_multiple": forces = [Vector3.ZERO,Vector3.ZERO]
		"chain_id": runner.chains[0].ids[0] = other
		"chain_reorder": runner.chains.reverse()
		"chain_source_binding": runner.chains[0].source.joints[0].binding.id = other
		"chain_binding_kind": runner.chains[0].source.joints[0].binding.kind = "root"
		"chain_duplicate": runner.chains.append(runner.chains[0].duplicate(true))
		"cached_index": runner.resolution.bindings[8].skeleton_bone_index = actor.bones[other].index
		"cached_parent": runner.resolution.by_native[7] = other
		"actor_order": actor.order.reverse()
		"actor_index": actor.bones[id].index = actor.bones[other].index
		"actor_base":
			var changed: Transform3D = original_info.base; changed.origin.x += 0.01; actor.bones[id].base = changed
		"skeleton_rest":
			var changed := old_rest; changed.origin.y += 0.01; sk.set_bone_rest(index,changed)
		"ancestor_parent": sk.set_bone_parent(ancestor_index,-1)
		"import_map":
			var changed := original_map.duplicate(true); changed[resolution.bindings[8].gltf_node_index] = other; actor.root.set_meta("has_source_bones",changed)
		"native_report":
			for rule in actor.data.metadata.native_parameters.native_parameters.source_jiggle.rules:
				if int(rule.native_bone_index) == 8: rule.parameters.yaw_stiffness = float(rule.parameters.yaw_stiffness)+1.0
		"disabled_bone": sk.set_bone_enabled(index,false)
		"show_rest_only": sk.show_rest_only = true
		"foreign_modifier": node = SpringBoneSimulator3D.new(); sk.add_child(node)
		"physical_body":
			# Actual engine nodes, only to exercise refusal. No complete ragdoll or
			# fabricated body pose is asserted. This added simulator is disposable.
			simulator = PhysicalBoneSimulator3D.new(); sk.add_child(simulator); node = simulator
			var body := PhysicalBone3D.new(); body.set("bone_name",actor.bones[id].name); body.mass = 1.0; body.collision_layer = 0; body.collision_mask = 0; simulator.add_child(body)
			var shape := CollisionShape3D.new(); var sphere := SphereShape3D.new(); sphere.radius = 0.01; shape.shape = sphere; body.add_child(shape)
			simulator.physical_bones_start_simulation()
			await physics_frame
			var body_running: Variant = body.call("is_simulating_physics") if body.has_method("is_simulating_physics") else false
			check(simulator.is_simulating_physics() and body_running is bool and body_running == true,"negative.physical_body.actual_simulating")
		"data_sha": actor.data.sha256 = "0".repeat(64)
		"source_path": actor.data.source = str(job.glb)
	if kind.begins_with("force_slot_"):
		forces = [Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,Vector3.ZERO,Vector3.ZERO]
		forces[int(kind.get_slice("_",2))] = Vector3(NAN,0.0,0.0)
	if CREATE_REFUSALS.has(kind):
		var rejected: Dictionary = Native.create(actor)
		check(rejected.has("error"),"negative."+kind+".create_refused")
		if not rejected.has("error"): rejected.runner.dispose()
	refused_before_commit(runner,kind,delta,wind,forces)
	if simulator != null: simulator.physical_bones_stop_simulation()
	if is_instance_valid(node): node.free()
	actor.data = original_data; actor.order.assign(original_order); actor.bones[id] = original_info; actor.root.set_meta("has_source_bones",original_map)
	sk.set_bone_rest(index,old_rest); sk.set_bone_parent(ancestor_index,old_parent); sk.set_bone_enabled(index,old_enabled); sk.show_rest_only = old_show
	runner.dispose(); baseline(actor)
	check(model_bytes(actor) == snapshots[0] and document_bytes(actor) == docs[0] and bytes_of(report_of(actor)) == raw_reports[0],"negative."+kind+".restored")

func next_second() -> bool:
	var second := int(Time.get_unix_time_from_system()); var until := Time.get_ticks_msec()+2500
	while int(Time.get_unix_time_from_system()) == second and Time.get_ticks_msec() < until: await process_frame
	return int(Time.get_unix_time_from_system()) != second

func file_case(kind: String) -> void:
	var actor: RefCounted = actors[0]; var path: String = owned_paths[0]
	var observed := false; var unchanged_mtime := false; var unchanged_size := false; var attempts := 0
	var runner: RefCounted = null
	# Second-resolution stat isolation is observed, never forged by changing the
	# backend cache or the filesystem timestamp through an external utility.
	for attempt in range(3):
		attempts += 1
		if not await next_second(): continue
		if not safe_owned_write(path,original_bytes): continue
		var made := create_native(actor)
		if made.has("error"): continue
		runner = made.runner
		var warm := native_step(runner,Vector3(1.0,0.0,0.0))
		if warm.has("error") or runner._tick != 1: runner.dispose(); runner = null; continue
		var cached_time: int = runner._source_modified; var cached_size: int = runner._source_length
		if kind == "mtime":
			if not await next_second(): runner.dispose(); runner = null; continue
			if not safe_owned_write(path,original_bytes): runner.dispose(); runner = null; continue
		else:
			var changed := original_bytes.duplicate()
			if kind == "header": changed[0] = int(changed[0]) ^ 1
			else: changed.append_array(PackedByteArray([0,0,0,0]))
			if not safe_owned_write(path,changed): runner.dispose(); runner = null; continue
		var source := FileAccess.open(path,FileAccess.READ)
		var current_size: int = source.get_length() if source != null else -1
		if source != null: source.close()
		unchanged_mtime = FileAccess.get_modified_time(path) == cached_time
		unchanged_size = current_size == cached_size
		observed = (not unchanged_mtime and unchanged_size and FileAccess.get_sha256(path) == GLB_SHA) if kind == "mtime" else (unchanged_mtime and unchanged_size and FileAccess.get_sha256(path) != GLB_SHA) if kind == "header" else (unchanged_mtime and current_size == cached_size+4)
		if observed: break
		runner.dispose(); runner = null
		safe_owned_write(path,original_bytes)
	check(observed,"file."+kind+".isolated_observation")
	metrics["file_"+kind] = {"attempts":attempts,"isolated":observed,"mtime_unchanged":unchanged_mtime,"length_unchanged":unchanged_size}
	if observed and runner != null:
		var before := state_bytes(runner); var doc := document_bytes(actor)
		var returned := native_step(runner)
		check(returned.has("error"),"file."+kind+".refused")
		check(state_bytes(runner) == before,"file."+kind+".state_atomic")
		check(document_bytes(actor) == doc,"file."+kind+".keys_report_unchanged")
		if kind != "mtime":
			var rejected := Native.create(actor)
			check(rejected.has("error"),"file."+kind+".create_refused")
			if not rejected.has("error"): rejected.runner.dispose()
	else:
		# Missing isolated observations are failures, never substituted by a
		# different stat gate or an assertion that simply checks the cached value.
		check(false,"file."+kind+".refused"); check(false,"file."+kind+".state_atomic"); check(false,"file."+kind+".keys_report_unchanged")
		if kind != "mtime": check(false,"file."+kind+".create_refused")
	if runner != null: runner.dispose()
	var restored := safe_owned_write(path,original_bytes)
	baseline(actor)
	check(restored and FileAccess.get_sha256(path) == GLB_SHA and model_bytes(actor) == snapshots[0],"file."+kind+".restored")

func wrapper_checks() -> void:
	wrapper_attempted = true
	var sims: Array = []; var seeds: Array = []
	for actor in actors:
		baseline(actor)
		var made: Dictionary = await Secondary.create(actor,null,FRAME,false)
		if made.has("error"):
			check(false,"wrapper.create3_native")
			for sim in sims: sim.stop(); sim.dispose()
			return
		sims.append(made.physics); seeds.append(state_bytes(made.physics.runner)); made.physics.start()
	check(sims.size() == 3 and sims[0].native_backend and sims[1].native_backend and sims[2].native_backend,"wrapper.create3_native")
	var unselected := unselected_bytes(actors[0],selected_ids(bindings[0]))
	var success := true
	for _i in range(TICKS):
		var error: String = sims[0].advance(Math.DT,FRAME,float(FRAME),false,[],null)
		if not error.is_empty(): success = false; break
		ticks_executed += 1
	check(success and sims[0].runner._tick == TICKS and state_bytes(sims[1].runner) == seeds[1] and state_bytes(sims[2].runner) == seeds[2],"wrapper.A120_preserves_BC")
	var authored: Dictionary = actors[0].sample(FRAME,false)
	var complete: bool = sims[0].latest.size() == authored.size() and sims[0].latest.size() == 69
	for id in authored:
		if not selected_ids(bindings[0]).has(id): complete = complete and sims[0].latest.get(id) == authored[id]
		else: complete = complete and sims[0].latest.get(id,Model.identity()).position == authored.get(id,Model.identity()).position
	check(complete and sims[0].latest[bindings[0].by_native[8]].position == authored[bindings[0].by_native[8]].position,"wrapper.complete_authored_pose_preserved")
	check(unselected_bytes(actors[0],selected_ids(bindings[0])) == unselected,"wrapper.64_unselected_world_bones_exact")
	var before := state_bytes(sims[0].runner); var latest := bytes_of(sims[0].latest); var age: float = sims[0].age
	var invalid: String = sims[0].advance(Math.DT*2.0,FRAME,float(FRAME),false,[],null)
	check(not invalid.is_empty() and state_bytes(sims[0].runner) == before and bytes_of(sims[0].latest) == latest and sims[0].age == age,"wrapper.invalid_dt_no_state_commit")
	var seek: String = sims[0].advance(Math.DT,FRAME+1,float(FRAME+1),false,[],null)
	check(not seek.is_empty() and state_bytes(sims[0].runner) == before and bytes_of(sims[0].latest) == latest,"wrapper.seek_no_state_commit")
	var reverse: String = sims[0].advance(Math.DT,FRAME,float(FRAME)-0.2,true,[],null)
	check(not reverse.is_empty() and state_bytes(sims[0].runner) == before,"wrapper.reverse_no_state_commit")
	var skip: String = sims[0].advance(Math.DT,FRAME,float(FRAME)+0.4,true,[],null)
	check(not skip.is_empty() and state_bytes(sims[0].runner) == before,"wrapper.record_skip_no_state_commit")
	var documents_ok := true
	for i in range(3): documents_ok = documents_ok and document_bytes(actors[i]) == docs[i] and bytes_of(report_of(actors[i])) == raw_reports[i]
	check(documents_ok,"wrapper.keys_raw_reports_immutable")
	var final_state := before
	var stopped_ok := true
	for i in range(3):
		var runner: RefCounted = sims[i].runner
		sims[i].stop(); sims[i].dispose(); baseline(actors[i])
		stopped_ok = stopped_ok and not runner.active() and actors[i].live_pose == null and actors[i].live_world_transform == null and model_bytes(actors[i]) == snapshots[i]
	check(stopped_ok,"wrapper.off_dispose_restore3_exact")
	var reenabled: Dictionary = await Secondary.create(actors[0],null,FRAME,false)
	check(not reenabled.has("error") and state_bytes(reenabled.physics.runner) == seeds[0],"wrapper.reenable_exact_seed")
	if not reenabled.has("error"):
		var again: RefCounted = reenabled.physics; again.start(); success = true
		for _i in range(TICKS):
			var error: String = again.advance(Math.DT,FRAME,float(FRAME),false,[],null)
			if not error.is_empty(): success = false; break
			ticks_executed += 1
		check(success and state_bytes(again.runner) == final_state,"wrapper.reenable_replay_exact")
		again.stop(); again.dispose(); baseline(actors[0])
	else: check(false,"wrapper.reenable_replay_exact")

func wrapper_inventory_case(kind: String) -> void:
	var actor: RefCounted=actors[0]; baseline(actor)
	var made: Dictionary=await Secondary.create(actor,null,FRAME,false)
	if made.has("error"):
		for suffix in ["refused","atomic","visual_exact","restored"]:check(false,"wrapper_inventory."+kind+"."+suffix)
		return
	var sim: RefCounted=made.physics;sim.start()
	var warm: String=sim.advance(Math.DT,FRAME,float(FRAME),false,[],null)
	if warm.is_empty():ticks_executed+=1
	var before:=state_bytes(sim.runner);var latest:=bytes_of(sim.latest);var visual:=model_bytes(actor)
	var age: float=sim.age;var last_time: float=sim.last_input_time;var processed: int=sim.runner.processing_samples
	match kind:
		"source_missing":sim.runner.chains[0].erase("source")
		"joints_empty":sim.runner.chains[0].source.joints=[]
		"binding_shape":sim.runner.chains[0].source.joints[0].binding=[]
		"count":sim.runner.chains.pop_back()
		"order":sim.runner.chains.reverse()
	var error: String=sim.advance(Math.DT,FRAME,float(FRAME),false,[],null)
	check(warm.is_empty() and not error.is_empty(),"wrapper_inventory."+kind+".refused")
	check(state_bytes(sim.runner)==before and bytes_of(sim.latest)==latest and sim.age==age and sim.last_input_time==last_time and sim.runner.processing_samples==processed,"wrapper_inventory."+kind+".atomic")
	check(model_bytes(actor)==visual,"wrapper_inventory."+kind+".visual_exact")
	sim.stop();sim.dispose();baseline(actor)
	check(model_bytes(actor)==snapshots[0] and document_bytes(actor)==docs[0] and bytes_of(report_of(actor))==raw_reports[0],"wrapper_inventory."+kind+".restored")

func direct_null_checks() -> void:
	var actor: RefCounted = actors[0]; baseline(actor)
	var model_before := model_bytes(actor); var document := document_bytes(actor)
	var made: Dictionary = Native.create(actor)
	if made.has("error"):
		check(false,"baseline.direct_nonzero_null_refused"); check(false,"baseline.direct_nonzero_null_atomic"); check(model_bytes(actor) == model_before,"baseline.direct_nonzero_null_pose_exact"); return
	var runner: RefCounted = made.runner; var saved := state_bytes(runner)
	var rejected := native_step(runner)
	check(rejected.has("error") and str(rejected.error).contains("fresh authored pose baseline"),"baseline.direct_nonzero_null_refused")
	check(state_bytes(runner) == saved and runner._tick == 0,"baseline.direct_nonzero_null_atomic")
	check(model_bytes(actor) == model_before and document_bytes(actor) == document,"baseline.direct_nonzero_null_pose_exact")
	runner.dispose(); baseline(actor)

func root_rotation_checks() -> void:
	var actor: RefCounted = actors[0]; var original: Dictionary = actor.data.duplicate(true)
	for spec in [{"name":"half","scale":0.5},{"name":"one","scale":1.0},{"name":"two","scale":2.0}]:
		actor.data = original.duplicate(true); actor.data.scale = spec.scale
		for key in actor.data.pose_keys:
			key.transform.scale = spec.scale
			var q := Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47 if key.frame == 24 else -0.21)
			key.transform.rotation_xyzw = [q.x,q.y,q.z,q.w]
		actor.live_pose = null; actor.live_world_transform = null; actor.apply(0,false)
		var saved := model_bytes(actor); var document := bytes_of(actor.data)
		var made: Dictionary = await Secondary.create(actor,null,0,false)
		var ok := not made.has("error"); var sizes_exact := ok; var drift := 0.0
		var measured_samples:=0;var measured_total_usec:=0;var measured_max_usec:=0;var native_perf: Dictionary={}
		if ok:
			var sim: RefCounted = made.physics; sim.start()
			var sizes := bytes_of(sim.runner._chain.snapshot().sizes)
			for tick in range(1,TICKS+1):
				var time: float = float(tick)*Math.DT*24.0
				var started: int=Time.get_ticks_usec()
				var error: String = sim.advance(Math.DT,int(floor(time)),time,true,[],null)
				var elapsed: int=maxi(0,Time.get_ticks_usec()-started)
				measured_samples+=1;measured_total_usec+=elapsed;measured_max_usec=maxi(measured_max_usec,elapsed)
				if not error.is_empty(): ok = false; break
				ticks_executed += 1
				sizes_exact = sizes_exact and bytes_of(sim.runner._chain.snapshot().sizes) == sizes
				var measured: Dictionary = Native.frame64(sim.runner._skeleton.global_transform)
				if measured.has("error"): ok = false; break
				drift = maxf(drift,absf(float(measured.scale)-sim.runner._prefix_scale))
			ok = ok and sim.runner._tick == TICKS and sim.runner._chain.snapshot().states.size() == 5
			native_perf={"samples":sim.runner.processing_samples,"mean_usec":float(sim.runner.processing_total_usec)/float(maxi(1,sim.runner.processing_samples)),"max_usec":sim.runner.processing_max_usec,"scope":"Successful full Native.step, measured only; no FPS criterion"}
			sim.stop(); sim.dispose(); actor.live_pose = null; actor.live_world_transform = null; actor.apply(0,false)
		check(ok,"rotation."+spec.name+".fixed_ticks")
		check(sizes_exact,"rotation."+spec.name+".sizes_exact")
		check(bytes_of(actor.data) == document and bytes_of(report_of(actor)) == raw_reports[0],"rotation."+spec.name+".authored_preserved")
		check(model_bytes(actor) == saved,"rotation."+spec.name+".Off_exact")
		metrics["rotation_"+spec.name] = {"prefix_scale_residual_max":drift,"logical_scale":spec.scale,"completed":ok,"advance_samples":measured_samples,"advance_mean_usec":float(measured_total_usec)/float(maxi(1,measured_samples)),"advance_max_usec":measured_max_usec,"native_step_processing":native_perf,"FPS_pass_claimed":false}
	actor.data = original; baseline(actor)

func planned_names() -> Array:
	var names: Array = ["instances.create3","instances.equal_seed_different_instances","instances.A120_preserves_BC","instances.B120_equals_A_C_unused","instances.keys_complete_pose_raw_reports_unchanged","instances.dispose3_inactive","instances.reenable_exact_seed",
		"wrapper.create3_native","wrapper.A120_preserves_BC","wrapper.complete_authored_pose_preserved","wrapper.64_unselected_world_bones_exact","wrapper.invalid_dt_no_state_commit","wrapper.seek_no_state_commit","wrapper.reverse_no_state_commit","wrapper.record_skip_no_state_commit","wrapper.keys_raw_reports_immutable","wrapper.off_dispose_restore3_exact","wrapper.reenable_exact_seed","wrapper.reenable_replay_exact",
		"negative.physical_body.actual_simulating","cleanup.owned_sources_restored","cleanup.report_files_untouched","cleanup.passed_inputs_read_only","cleanup.authored3_restored"]
	for name in ["a","b","c"]:
		for suffix in ["copied","actual_Model_SceneIO","qualified69_49","complete_nonrest_baseline","raw_report_file_exact","fresh_rest_null","fresh_partial_dictionary"]: names.append("load."+name+"."+suffix)
	for kind in NEGATIVES:
		for suffix in ["seeded","refused","state_atomic","keys_report_unchanged","restored"]: names.append("negative."+kind+"."+suffix)
		if CREATE_REFUSALS.has(kind): names.append("negative."+kind+".create_refused")
	for kind in ["header","length","mtime"]:
		for suffix in ["isolated_observation","refused","state_atomic","keys_report_unchanged","restored"]: names.append("file."+kind+"."+suffix)
		if kind != "mtime": names.append("file."+kind+".create_refused")
	for suffix in ["refused","atomic","pose_exact"]: names.append("baseline.direct_nonzero_null_"+suffix)
	for root_name in ["half","one","two"]:
		for suffix in ["fixed_ticks","sizes_exact","authored_preserved","Off_exact"]: names.append("rotation."+root_name+"."+suffix)
	for kind in WRAPPER_INVENTORY_CASES:
		for suffix in ["refused","atomic","visual_exact","restored"]:names.append("wrapper_inventory."+kind+"."+suffix)
	names.sort()
	return names

func finish() -> void:
	check(restore_owned(),"cleanup.owned_sources_restored")
	var reports_ok := report_paths.size() == 3
	for path in report_paths: reports_ok = reports_ok and FileAccess.get_sha256(path) == REPORT_SHA
	check(reports_ok,"cleanup.report_files_untouched")
	check(input_unchanged(),"cleanup.passed_inputs_read_only")
	var restored := actors.size() == 3
	for i in range(actors.size()): baseline(actors[i]); restored = restored and model_bytes(actors[i]) == snapshots[i]
	check(restored,"cleanup.authored3_restored")
	var observed: Array = named.keys(); observed.sort(); var planned := planned_names(); var complete := observed == planned and planned.size() == PLANNED_ASSERTIONS
	if not complete: failures += 1
	metrics["completed_native_steps"] = ticks_executed
	metrics["negative_case_count"] = NEGATIVES.size(); metrics["planned_assertions"] = planned.size(); metrics["actors_loaded"] = actors.size()
	var result := {"format":"has_source_native_five_state_result_2","checks":named.size(),"failures":failures,"complete_assertion_set":complete,"named_checks":named,"metrics":metrics,
		"job_sha256":str(job.get("_job_sha256","")),"test_script_sha256":FileAccess.get_sha256(get_script().resource_path),"source_manifest_sha256":job.get("source_manifest_sha256",""),
		"scope":{"actual_Model_instances_loaded":actors.size(),"actual_Native_backend_attempted":native_attempted,"actual_Secondary_wrapper_attempted":wrapper_attempted,"native_rule_index_selected":8,"native_rule_indices_selected":SELECTED,"native_rules_solved":5,"retained_rules":49,"native_conversion_performed":false,
		"actual_single_physical_body_only_adversarial_refusal":true,"same_actor_complete_ragdoll_or_borrowed_primary":"UNQUALIFIED_PARTIAL_SOURCE_RIG","fake_primary_or_physics_emulation":false,"GPU_or_GUI":false,"private_arrays_serialized":false,
		"continuous_file_guard":"Captured GLB header, statmtime, length and cached complete69-bone binding/report stamp; full source authentication on create/reload",
		"unchanged_header_size_mtime_body_edit_detection":"OUTSIDE_CONTINUOUS_CRYPTOGRAPHIC_GUARANTEE_NOT_TESTED_OR_CLAIMED","mutable_original_inputs":false},
		"cleanup":{"owned_copy_hashes_restored":owned_paths.size()==3 and restore_owned(),"passed_input_hashes_preserved":input_unchanged(),"retained_private_artifacts":"Three script-created owned GLBs and adjacent reports only; root removes after verified evidence backup"}}
	var file := FileAccess.open(result_path,FileAccess.WRITE)
	if file == null: push_error("Cannot write owned state result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	for host in hosts:
		if is_instance_valid(host): host.free()
	print("SOURCE_NATIVE_STATE "+JSON.stringify({"checks":named.size(),"failures":failures,"complete_assertion_set":complete}))
	quit(0 if failures == 0 and complete else 1)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: push_error("One fresh root-owned native state job required"); quit(2); return
	var job_path: String = args[0]
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(job_path))
	if not parsed is Dictionary or parsed.get("format") != "has_source_native_five_state_job_2" or parsed.get("phase") != "ROOT_APPROVED_HEADLESS_FIVE_STATE_TEST" or parsed.get("root_closed_all") != true or float(parsed.get("expires_unix",0)) <= Time.get_unix_time_from_system(): push_error("Fresh closed root lease required"); quit(2); return
	job = parsed; job["_job_sha256"] = FileAccess.get_sha256(job_path)
	for field in ["folder","glb","report"]:
		if not job.get(field) is String or not str(job[field]).is_absolute_path(): push_error("Absolute owned job paths required"); quit(2); return
	if DisplayServer.get_name() != "headless" or FileAccess.get_sha256(OS.get_executable_path()) != str(job.get("engine_sha256","")) or FileAccess.get_sha256(get_script().resource_path) != str(job.get("expected_script_sha256","")): push_error("Exact approved headless engine/test source required"); quit(2); return
	var adjacent: String = str(job.glb).get_base_dir().path_join("parameters.json").simplify_path().replace("\\","/").to_lower()
	if adjacent != str(job.report).simplify_path().replace("\\","/").to_lower() or DirAccess.dir_exists_absolute(str(job.folder).path_join("state-owned-inputs")): push_error("Adjacent report and fresh output required"); quit(2); return
	result_path = str(job.folder).path_join("result.json")
	if FileAccess.file_exists(result_path): push_error("Fresh result path required"); quit(2); return
	input_sha = FileAccess.get_sha256(str(job.glb)); report_sha = FileAccess.get_sha256(str(job.report))
	if input_sha != GLB_SHA or report_sha != REPORT_SHA: push_error("Qualified native input hashes required"); quit(2); return
	var file := FileAccess.open(str(job.glb),FileAccess.READ)
	if file == null or file.get_length() > 128*1024*1024: push_error("Bounded owned input required"); quit(2); return
	original_bytes = file.get_buffer(file.get_length()); file.close()
	create_timer(180.0).timeout.connect(func(): restore_owned(); push_error("Native state watchdog; owned originals restored where possible"); quit(2))
	for index in range(3):
		if not load_actor(index): finish(); return
	direct_null_checks()
	instance_checks()
	for kind in NEGATIVES: await negative_case(kind)
	for kind in ["header","length","mtime"]: await file_case(kind)
	await wrapper_checks()
	for kind in WRAPPER_INVENTORY_CASES:await wrapper_inventory_case(kind)
	await root_rotation_checks()
	finish()
