extends SceneTree
# SOURCE ONLY, UNPARSED/UNRUN. Generated scalar fixtures, no imported artist file.
const Batch = preload("res://src/source_secondary_preview_batch.gd")
const BaseNative = preload("res://src/source_secondary.gd")
const Chains = preload("res://src/source_chain_math.gd")
const Math = preload("res://src/source_jiggle_math.gd")
const Preview = preload("res://src/secondary_live.gd")
const Airflow = preload("res://src/airflow.gd")
const NativeIDs := [8,17,18,26,27]
var failures := 0
var checks := 0

class Resolution extends RefCounted:
	var by_native: Dictionary = {}

class Candidate extends Batch:
	var admission_calls := 0
	var baseline_calls := 0
	var position_calls := 0
	var single_calls := 0
	var admission_failure := ""
	var baseline_failure := ""
	var baseline_fixture: Dictionary = {}
	var positions_fixture: Dictionary = {}
	func _preview_batch_admission() -> Dictionary:
		admission_calls += 1
		return {"ok":true} if admission_failure.is_empty() else {"error":admission_failure}
	func capture_baseline() -> Dictionary:
		baseline_calls += 1
		return baseline_fixture.duplicate(true) if baseline_failure.is_empty() else {"error":baseline_failure}
	func _preview_batch_authored_positions() -> Dictionary:
		position_calls += 1
		return {"positions":positions_fixture.duplicate(true)}
	func step(_delta: float,_wind: Vector3,_forces: Array=[]) -> Dictionary:
		# Only proves the one-tick dispatch. Real direct admission is inherited in
		# the production candidate and remains covered by existing native tests.
		single_calls += 1
		return {"pose":{},"single_dispatch":true}


class PreviewRig extends RefCounted:
	var root := Node3D.new()
	var data := {"marker":"authored untouched"}
	var motion_video := {"fps_num":30,"fps_den":1}
	var live_pose: Variant = null
	var live_world_transform: Variant = null
	var applications := 0
	func apply_current(_frame: int,_editing: bool=false) -> void: applications += 1
	func bone_transform(_id: String) -> Transform3D: return Transform3D(Basis.IDENTITY,Vector3(0.0,0.85,1.0))

class PreviewRunner extends RefCounted:
	var chains: Array = []
	var batch_calls := 0
	var single_calls := 0
	var captured: Array = []
	func _init() -> void:
		for index in [8,17,18,26,27]: chains.append({"ids":["n"+str(index)],"source":{"joints":[{"binding":{"kind":"bone","id":"n"+str(index)}}]}})
	func airflow_error() -> String: return ""
	func output_pose() -> Dictionary:
		var pose := {}
		for chain in chains: pose[chain.ids[0]] = {"position":[0.0,0.0,0.0],"rotation_xyzw":[0.0,0.0,0.0,1.0]}
		return pose
	func preview_batch(input: Array,_recording: bool) -> Dictionary:
		batch_calls += 1; captured = input.duplicate(true)
		return {"pose":output_pose()}
	func step(_delta: float,_wind: Vector3,_forces: Array=[]) -> Dictionary:
		single_calls += 1
		return {"pose":output_pose()}
	func dispose() -> void: pass

func preview_fixture() -> RefCounted:
	var value: RefCounted = Preview.new()
	value.rig = PreviewRig.new(); value.runner = PreviewRunner.new()
	value.native_backend = true; value.initial_frame = 12; value.last_input_time = 12.0
	value.initial_pose = value.runner.output_pose(); value.latest = value.initial_pose.duplicate(true)
	value.age = 1079.123456789; value.start()
	return value

func _initialize() -> void: call_deferred("run")
func check(ok: bool,name: String) -> void:
	checks += 1
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"native_preview_batch."+name)

func fixture(scale: float=1.0,zero_spring: bool=false) -> Candidate:
	var value := Candidate.new()
	var ids := [0,1,2,3,4,5,6,7,8,17,18,25,26,27]
	var parents := {0:null,1:0,2:1,3:2,4:3,5:4,6:5,7:6,8:7,17:7,18:17,25:7,26:25,27:26}
	var bones := {}
	var locals := {}
	var mapping := Resolution.new()
	for index in ids:
		var id: String = "n"+str(index)
		mapping.by_native[index] = id
		var local: Dictionary = Chains.identity_frame()
		bones[id] = {"parent":null if parents[index] == null else "n"+str(parents[index]),"base":local.duplicate(true)}
		locals[id] = local.duplicate(true)
	var p: Dictionary = Math.defaults()
	if zero_spring:
		p.length = 1.0/BaseNative.SOURCE_SCALE; p.tip_mass = 0.0
		p.yaw_stiffness = 0.0; p.yaw_damping = 0.0
		p.pitch_stiffness = 0.0; p.pitch_damping = 0.0
	var parameters := {}
	for index in NativeIDs:
		var id: String = mapping.by_native[index]
		parameters[id] = p.duplicate(true)
		value.positions_fixture[id] = [0.001*float(index),-0.0002,0.0007]
	var prefix: Dictionary = Chains.identity_frame(); prefix.scale = scale
	value.baseline_fixture = {"locals":locals,"prefix":prefix}
	value.resolution = mapping; value._solver_bone_specs = bones
	value._parameters = parameters
	var primary: Dictionary = Chains.create(bones,parameters,BaseNative.SOURCE_SCALE,[0.0,-1.0,0.0])
	var trial: Dictionary = Chains.create(bones,parameters,BaseNative.SOURCE_SCALE,[0.0,-1.0,0.0])
	value._chain = primary.actor; value._trial = trial.actor
	value._chain.reset(locals,prefix); value._trial.reset(locals,prefix)
	value._configuration_stamp = value.configuration_stamp(value._chain)
	value._size_tokens = value._chain.snapshot().sizes.duplicate(true)
	value._tick = 0; value._alive = true
	return value

func samples(count: int,zero_force: bool=false) -> Array:
	var result: Array = []
	for tick in range(count):
		var forces: Array = []
		for i in range(NativeIDs.size()): forces.append(Vector3.ZERO if zero_force else Vector3(float(tick)*0.02+float(i)*0.01,-0.03,0.01))
		result.append({"delta":Math.DT,"wind":Vector3.ZERO,"forces":forces})
	return result

func state_bytes(value: Candidate) -> PackedByteArray:
	return var_to_bytes([value._tick,value._chain.snapshot(),value._trial.snapshot(),value.configuration_stamp(value._chain),value.configuration_stamp(value._trial)])

func scalar_reference(value: Candidate,input: Array) -> Dictionary:
	var made: Dictionary = Chains.create(value._solver_bone_specs,value._parameters,BaseNative.SOURCE_SCALE,[0.0,-1.0,0.0])
	var worker: RefCounted = made.actor
	worker.reset(value.baseline_fixture.locals,value.baseline_fixture.prefix)
	var previous: Dictionary = worker.snapshot()
	var output := {}
	for sample in input:
		var accelerations := {}
		for i in range(NativeIDs.size()):
			var force: Vector3 = sample.forces[i]
			accelerations[value.resolution.by_native[NativeIDs[i]]] = [float(force.x),float(force.y),float(force.z)]
		previous = worker.snapshot()
		output = worker.step(worker._tick+1,value.baseline_fixture.locals,value.baseline_fixture.prefix,accelerations)
		if output.has("error"): return output
	return {"final":worker.snapshot(),"previous":previous,"output":output}

func run() -> void:
	for size in [0.5,1.0,2.0]:
		for count in [2,3,8]:
			var value: Candidate = fixture(float(size))
			var input: Array = samples(count)
			var original: PackedByteArray = var_to_bytes(input)
			var reference: Dictionary = scalar_reference(value,input)
			var old_primary: RefCounted = value._chain
			var old_trial: RefCounted = value._trial
			var actual: Dictionary = value.preview_batch(input,false)
			var label: String = "s"+str(size)+"_n"+str(count)
			check(not actual.has("error") and value._tick == count and var_to_bytes(value._chain.snapshot()) == var_to_bytes(reference.final),label+".exact_every_fixed_tick_state")
			check(var_to_bytes(value._trial.snapshot()) == var_to_bytes(reference.previous),label+".penultimate_trial_state")
			check(value._chain == (old_primary if count%2 == 0 else old_trial) and value._trial == (old_trial if count%2 == 0 else old_primary),label+".same_original_object_parity")
			check(value.admission_calls == 1 and value.baseline_calls == 1 and value.position_calls == 1,label+".one_full_admission_and_baseline")
			check(var_to_bytes(input) == original and actual.pose.size() == 5,label+".input_unchanged_and_complete_pose")
			var positions_ok := true
			for id in actual.pose: positions_ok = positions_ok and actual.pose[id].position == value.positions_fixture[id]
			check(positions_ok,label+".authored_positions_preserved")
	var single: Candidate = fixture()
	var one: Dictionary = single.preview_batch(samples(1),false)
	check(one.get("single_dispatch",false) and single.single_calls == 1 and single.admission_calls == 0 and single.baseline_calls == 0,"single_tick_dispatches_original_method")
	var recorded: Candidate = fixture(); var recorded_before: PackedByteArray = state_bytes(recorded)
	check(recorded.preview_batch(samples(2),true).has("error") and state_bytes(recorded) == recorded_before and recorded.admission_calls == 0,"recording_never_enters_batch")
	for count in [0,9]:
		var value: Candidate = fixture(); var before: PackedByteArray = state_bytes(value)
		check(value.preview_batch(samples(count),false).has("error") and state_bytes(value) == before and value.admission_calls == 0,"bounded_count_"+str(count)+"_before_admission")
	for kind in ["bad_dt","nan_force","large_force","missing_slot","extra_key","wrong_wind"]:
		var value: Candidate = fixture(); var input: Array = samples(3)
		if kind == "bad_dt": input[2].delta = Math.DT*2.0
		elif kind == "nan_force": input[2].forces[4] = Vector3(NAN,0.0,0.0)
		elif kind == "large_force": input[2].forces[4] = Vector3(1000001.0,0.0,0.0)
		elif kind == "missing_slot": input[2].forces.pop_back()
		elif kind == "extra_key": input[2].extra = true
		else: input[2].wind = [0.0,0.0,0.0]
		var before: PackedByteArray = state_bytes(value)
		check(value.preview_batch(input,false).has("error") and state_bytes(value) == before and value.admission_calls == 0,"complete_set_"+kind+"_refuses_before_admission")
	var refused: Candidate = fixture(); refused.admission_failure = "fixture full admission refusal"
	var before_admission: PackedByteArray = state_bytes(refused)
	check(refused.preview_batch(samples(2),false).get("error") == refused.admission_failure and state_bytes(refused) == before_admission and refused.admission_calls == 1 and refused.baseline_calls == 0,"full_admission_refusal_preserved")
	var baseline_refused: Candidate = fixture(); baseline_refused.baseline_failure = "fixture full69 baseline refusal"
	var baseline_before: PackedByteArray = state_bytes(baseline_refused)
	check(baseline_refused.preview_batch(samples(2),false).get("error") == baseline_refused.baseline_failure and state_bytes(baseline_refused) == baseline_before and baseline_refused.position_calls == 0,"full69_baseline_refusal_preserved")
	var tampered: Candidate = fixture(); tampered._trial._source_scale = 2.0
	var tampered_before: PackedByteArray = state_bytes(tampered)
	check(tampered.preview_batch(samples(2),false).has("error") and state_bytes(tampered) == tampered_before,"trial_configuration_mutation_still_refused")
	var invalid_state: Candidate = fixture(); invalid_state._chain._states[invalid_state.resolution.by_native[8]].tip = [NAN,0.0,0.0]
	var invalid_before: PackedByteArray = state_bytes(invalid_state)
	check(invalid_state.preview_batch(samples(2),false).has("error") and state_bytes(invalid_state) == invalid_before,"authoritative_state_mutation_still_refused")
	var late: Candidate = fixture(1.0,true)
	var late_input: Array = samples(2,true)
	late_input[1].forces[4] = Vector3(0.0,0.0,-14400.0)
	var late_before: PackedByteArray = state_bytes(late)
	var late_result: Dictionary = late.preview_batch(late_input,false)
	check(late_result.has("error") and str(late_result.error).contains("Degenerate direction") and state_bytes(late) == late_before,"second_tick_late_child_failure_rolls_back_whole_batch")
	var alias: Candidate = fixture(); var result: Dictionary = alias.preview_batch(samples(2),false)
	var protected: PackedByteArray = state_bytes(alias)
	result.pose[alias.resolution.by_native[8]].position[0] = 999.0
	result.pose[alias.resolution.by_native[8]].rotation_xyzw[0] = 999.0
	check(state_bytes(alias) == protected and alias.positions_fixture[alias.resolution.by_native[8]][0] != 999.0,"returned_pose_cannot_alias_states_or_authored_input")

	var preview: RefCounted = preview_fixture()
	var preview_before: PackedByteArray = var_to_bytes([preview.rig.data,preview.latest])
	var expected_fields: Array = []
	for speed in [3.0,12.0,50.0]:
		var settings: Dictionary = Airflow.defaults(); settings.speed = speed
		var fields: Array = [{"transform":Transform3D.IDENTITY,"settings":settings}]
		expected_fields.append(fields.duplicate(true))
		check(preview.queue_native_preview(Math.DT,12,12.0,fields).is_empty(),"queue.frozen_tick_"+str(int(speed)))
		settings.speed = 0.0
	check(preview.rig.applications == 0 and var_to_bytes([preview.rig.data,preview.latest]) == preview_before,"queue.no_state_or_scene_application_before_drain")
	var expected_age: float = preview.age
	var expected_forces: Array = []
	for fields in expected_fields:
		expected_forces.append(Airflow.unsteady_force(fields,Vector3(0.0,0.85,1.0),expected_age)/0.03)
		expected_age += Math.DT
	var issue: String = preview.flush_native_preview(12,false,null)
	check(issue.is_empty() and preview.runner.batch_calls == 1 and preview.runner.single_calls == 0 and preview.rig.applications == 2,"queue.one_authored_restore_and_final_apply_for_three_ticks")
	var force_equal := preview.runner.captured.size() == 3
	for index in range(preview.runner.captured.size()):
		for force in preview.runner.captured[index].forces: force_equal = force_equal and force == expected_forces[index]
	check(force_equal and preview.age == expected_age,"queue.exact_per_tick_fan_snapshot_and_left_associated_age")
	check(preview._preview_pending.is_empty() and preview.last_input_time == 12.0 and var_to_bytes(preview.rig.data) == var_to_bytes({"marker":"authored untouched"}),"queue.drained_without_authored_data_change")
	var one_preview: RefCounted = preview_fixture()
	one_preview.queue_native_preview(Math.DT,12,12.0,[])
	check(one_preview.flush_native_preview(12,false,null).is_empty() and one_preview.runner.single_calls == 1 and one_preview.runner.batch_calls == 0 and one_preview.rig.applications == 2,"queue.single_visible_tick_keeps_original_advance")
	var record_preview: RefCounted = preview_fixture()
	record_preview.queue_native_preview(Math.DT,12,12.0,[])
	var record_age: float = record_preview.age
	check(not record_preview.flush_native_preview(12,true,null).is_empty() and record_preview._preview_pending.size() == 1 and record_preview.age == record_age and record_preview.rig.applications == 0,"queue.active_record_cannot_consume_unflushed_preview")
	var overflow: RefCounted = preview_fixture()
	var accepted := true
	for i in range(8): accepted = accepted and overflow.queue_native_preview(Math.DT,12,12.0,[]).is_empty()
	check(accepted and not overflow.queue_native_preview(Math.DT,12,12.0,[]).is_empty() and overflow._preview_pending.size() == 8,"queue.overflow_stops_instead_of_dropping_a_tick")
	var seek: RefCounted = preview_fixture()
	check(not seek.queue_native_preview(Math.DT,13,13.0,[]).is_empty() and seek._preview_pending.is_empty(),"queue.seek_rejected_before_enqueue")
	var reversed_queue: RefCounted = preview_fixture()
	reversed_queue.queue_native_preview(Math.DT,12,12.0,[])
	reversed_queue.queue_native_preview(Math.DT,12,14.0,[])
	check(not reversed_queue.queue_native_preview(Math.DT,12,13.0,[]).is_empty() and reversed_queue._preview_pending.size() == 2 and reversed_queue.rig.applications == 0 and reversed_queue.last_input_time == 12.0,"queue.decreasing_later_pending_time_refuses_before_commit")
	var tampered_queue: RefCounted = preview_fixture()
	for input_time in [12.0,14.0,15.0]: tampered_queue.queue_native_preview(Math.DT,12,input_time,[])
	tampered_queue._preview_pending[2].time = 13.0
	var tampered_age: float = tampered_queue.age
	check(not tampered_queue.flush_native_preview(12,false,null).is_empty() and tampered_queue.rig.applications == 0 and tampered_queue.age == tampered_age and tampered_queue.runner.batch_calls == 0 and tampered_queue.last_input_time == 12.0,"queue.post_enqueue_time_mutation_refuses_before_baseline_or_state")
	var recording_source: String = FileAccess.get_file_as_string("res://src/physics_recording.gd")
	check(recording_source.find("editor.flush_native_previews()") >= 0 and recording_source.find("editor.flush_native_previews()") < recording_source.find("previous[id]=read_state(id)"),"record.real_start_flush_precedes_tick_zero_snapshot")
	var owned_previews: Array = [preview,one_preview,record_preview,overflow,seek,reversed_queue,tampered_queue]
	for owned_index in range(owned_previews.size()):
		var owned: RefCounted = owned_previews[owned_index]
		var root_node: Node3D = owned.rig.root
		owned.dispose()
		check(owned._preview_pending.is_empty() and owned.rig.live_pose == null,"off.discards_unrecorded_queue_"+str(owned_index))
		root_node.free()
	print("Native preview batch candidate controls: "+str(checks)+"; failures: "+str(failures))
	quit(0 if failures == 0 else 1)
