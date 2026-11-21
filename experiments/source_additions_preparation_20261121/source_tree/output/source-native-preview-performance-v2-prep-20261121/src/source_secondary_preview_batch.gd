extends "res://src/source_secondary.gd"
# SOURCE-ONLY CANDIDATE. The inherited single step() remains unchanged.
# Preview batches keep every fixed120Hz numerical tick; recording never uses this API.
const BaseNative = preload("res://src/source_secondary.gd")
const MAX_PREVIEW_BATCH := 8
const TRANSFER_FIELDS := ["actor","resolution","chains","_chain_inventory_stamp","_source_path","_skeleton","_parameters","_bone_specs","_solver_bone_specs","_capture_configuration_stamp","_baseline_guard","_baseline_guard_stamp","_base_scales","_chain","_trial","_configuration_stamp","_size_tokens","_prefix_scale","_authored_scale_token","_tick","_alive","processing_samples","processing_total_usec","processing_max_usec","_binding_stamp","_source_modified","_source_length","_source_header"]
var preview_batch_count := 0
var preview_batch_ticks := 0
var preview_batch_total_usec := 0
var preview_batch_max_usec := 0
var preview_admission_total_usec := 0
var preview_capture_total_usec := 0
var preview_dispatch_count := 0

static func create_preview(rig: RefCounted) -> Dictionary:
	var made: Dictionary = BaseNative.create(rig)
	if made.has("error"): return made
	var previous: RefCounted = made.runner
	if previous.get_script() != BaseNative:
		previous.dispose()
		return {"error":"The imported hair batch source type changed."}
	var candidate = new()
	# Move the freshly created private ownership; no retained caller has seen it.
	for field in TRANSFER_FIELDS: candidate.set(field,previous.get(field))
	made.runner = candidate
	return made

func _preview_batch_admission() -> Dictionary:
	if not _alive or not is_instance_valid(actor.root) or not is_instance_valid(_skeleton) or not offered(actor) or actor.data.get("source") != _source_path: return {"error":"The imported hair source changed; its preview was stopped."}
	if not FileAccess.file_exists(_source_path) or FileAccess.get_modified_time(_source_path) != _source_modified or binding_stamp() != _binding_stamp: return {"error":"The imported source or joint setup changed; its hair preview was stopped."}
	var source := FileAccess.open(_source_path,FileAccess.READ)
	if source == null: return {"error":"The imported hair source is unavailable."}
	var source_length := source.get_length()
	var source_header := source.get_buffer(12)
	source.close()
	if source_length != _source_length or source_header != _source_header: return {"error":"The imported hair source changed; its preview was stopped."}
	var error := context_error(actor,_skeleton)
	if not error.is_empty(): return {"error":error}
	if chains.size() != SELECTED_NATIVE_IDS.size() or var_to_bytes(chains) != _chain_inventory_stamp: return {"error":"The imported hair chain or airflow bindings changed; its preview was stopped."}
	var scale_token = actor.data.get("scale")
	if not (scale_token is int or scale_token is float) or not is_finite(float(scale_token)) or float(scale_token) != _authored_scale_token: return {"error":"Turn imported hair off before resizing the model."}
	return {"ok":true}

func _preview_batch_authored_positions() -> Dictionary:
	var positions := {}
	for native_index in SELECTED_NATIVE_IDS:
		var id: String = resolution.by_native[native_index]
		var binding: RefCounted = resolution.bindings[native_index]
		if not actor.bones.has(id) or actor.bones[id].skeleton != _skeleton or actor.bones[id].index != binding.skeleton_bone_index or not _skeleton.is_bone_enabled(binding.skeleton_bone_index) or actor.parent_id(id) != resolution.by_native[EXPECTED_PARENTS[native_index]]:
			return {"error":"The imported hair binding changed; its preview was stopped."}
		if not actor.live_pose is Dictionary and _skeleton.get_bone_pose(binding.skeleton_bone_index).origin != actor.bones[id].base.origin:
			return {"error":"Imported hair needs a fresh authored pose baseline before stepping."}
		var authored: Dictionary = actor.live_pose.get(id,Model.identity()) if actor.live_pose is Dictionary else Model.identity()
		if not authored.get("position") is Array or authored.position.size() != 3:
			return {"error":"The imported hair authored translation is incomplete."}
		for value in authored.position:
			if not (value is int or value is float) or not is_finite(float(value)):
				return {"error":"The imported hair authored translation is invalid."}
		positions[id] = authored.position.duplicate(true)
	return {"positions":positions}

func preview_batch(samples: Array, recording: bool) -> Dictionary:
	if recording: return {"error":"Recorded imported hair must use individual fixed ticks."}
	if samples.is_empty() or samples.size() > MAX_PREVIEW_BATCH:
		return {"error":"The imported hair preview batch is outside its bounded fixed clock."}
	# Freeze and validate the complete set before any state can commit.
	var frozen: Array = samples.duplicate(true)
	for sample in frozen:
		if not sample is Dictionary or sample.size() != 3 or not sample.has_all(["delta","wind","forces"]):
			return {"error":"A complete imported hair preview tick is required."}
		var delta: Variant = sample.delta
		if not (delta is int or delta is float) or not is_finite(float(delta)) or absf(float(delta)-Math.DT) > 1e-9:
			return {"error":"Imported hair needs the fixed120Hz simulation clock."}
		if not sample.wind is Vector3 or not sample.wind.is_finite() or not sample.forces is Array:
			return {"error":"Imported hair received an invalid airflow input."}
		if not sample.forces.is_empty() and sample.forces.size() != SELECTED_NATIVE_IDS.size():
			return {"error":"Imported hair needs one airflow input per selected joint."}
		for i in range(SELECTED_NATIVE_IDS.size()):
			var force: Variant = sample.wind if sample.forces.is_empty() else sample.forces[i]
			if not force is Vector3 or not force.is_finite() or force.length() > 1000000.0:
				return {"error":"Imported hair received an invalid airflow input."}
	if frozen.size() == 1:
		return step(float(frozen[0].delta),frozen[0].wind,frozen[0].forces)
	var admission_started: int = Time.get_ticks_usec()
	var admission: Dictionary = _preview_batch_admission()
	if admission.has("error"): return admission
	var admission_elapsed: int = maxi(0,Time.get_ticks_usec()-admission_started)
	var capture_started: int = Time.get_ticks_usec()
	var baseline: Dictionary = capture_baseline()
	if baseline.has("error"): return baseline
	var authored: Dictionary = _preview_batch_authored_positions()
	if authored.has("error"): return authored
	var capture_elapsed: int = maxi(0,Time.get_ticks_usec()-capture_started)
	# No await, signals, scene writes or caller callbacks occur inside the core.
	var result: Dictionary = _preview_batch_core(frozen,baseline,authored.positions)
	if not result.has("error"):
		preview_dispatch_count += 1
		preview_admission_total_usec += admission_elapsed
		preview_capture_total_usec += capture_elapsed
	return result

func _preview_batch_core(samples: Array,baseline: Dictionary,positions: Dictionary) -> Dictionary:
	var started: int = Time.get_ticks_usec()
	var committed: Dictionary = _chain.snapshot()
	if configuration_stamp(_chain) != _configuration_stamp or configuration_stamp(_trial) != _configuration_stamp:
		return {"error":"The imported hair simulation configuration changed."}
	var invalid: String = state_error(committed,_tick)
	if not invalid.is_empty(): return {"error":invalid}
	var made: Dictionary = Chains.create(_solver_bone_specs,_parameters,SOURCE_SCALE,[0.0,-1.0,0.0])
	if made.has("error"): return made
	var work: RefCounted = made.actor
	work._states = committed.states.duplicate(true)
	work._sizes = committed.sizes.duplicate(true)
	work._tick = int(committed.tick); work._active = true
	var previous: Dictionary = committed
	var pose := {}
	for offset in range(samples.size()):
		var sample: Dictionary = samples[offset]
		var accelerations := {}
		for i in range(SELECTED_NATIVE_IDS.size()):
			var id: String = resolution.by_native[SELECTED_NATIVE_IDS[i]]
			var force: Vector3 = sample.wind if sample.forces.is_empty() else sample.forces[i]
			accelerations[id] = vector64(force)
		previous = work.snapshot()
		var next_tick: int = _tick+offset+1
		var solved: Dictionary = work.step(next_tick,baseline.locals,baseline.prefix,accelerations)
		if solved.has("error"): return solved
		invalid = state_error(work.snapshot(),next_tick)
		if not invalid.is_empty(): return {"error":invalid}
		if not solved.get("delta_bases") is Dictionary or solved.delta_bases.size() != _parameters.size():
			return {"error":"The imported hair solver returned an incomplete pose."}
		pose = {}
		for native_index in SELECTED_NATIVE_IDS:
			var id: String = resolution.by_native[native_index]
			if not solved.delta_bases.has(id): return {"error":"The imported hair solver missed a selected joint."}
			var check_goal: Dictionary = Math.goal([0.0,0.0,0.0],solved.delta_bases[id])
			if check_goal.has("error"): return check_goal
			var q: Quaternion = basis64(solved.delta_bases[id]).get_rotation_quaternion().normalized()
			if not is_finite(q.x) or not is_finite(q.y) or not is_finite(q.z) or not is_finite(q.w):
				return {"error":"The imported hair solver returned an invalid rotation."}
			pose[id] = {"position":positions[id].duplicate(true),"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	# Allocate every new state copy before the only authoritative commit.
	var final: Dictionary = work.snapshot()
	var final_states: Dictionary = final.states.duplicate(true)
	var final_sizes: Dictionary = final.sizes.duplicate(true)
	var previous_states: Dictionary = previous.states.duplicate(true)
	var previous_sizes: Dictionary = previous.sizes.duplicate(true)
	if configuration_stamp(work) != _configuration_stamp:
		return {"error":"The imported hair trial configuration changed."}
	var final_owner: RefCounted = _chain if samples.size()%2 == 0 else _trial
	var previous_owner: RefCounted = _trial if samples.size()%2 == 0 else _chain
	final_owner._states = final_states; final_owner._sizes = final_sizes
	final_owner._tick = int(final.tick); final_owner._active = true
	previous_owner._states = previous_states; previous_owner._sizes = previous_sizes
	previous_owner._tick = int(previous.tick); previous_owner._active = true
	_chain = final_owner; _trial = previous_owner; _tick = int(final.tick)
	var elapsed: int = maxi(0,Time.get_ticks_usec()-started)
	preview_batch_count += 1; preview_batch_ticks += samples.size()
	preview_batch_total_usec += elapsed; preview_batch_max_usec = maxi(preview_batch_max_usec,elapsed)
	return {"pose":pose,"batch_ticks":samples.size()}
