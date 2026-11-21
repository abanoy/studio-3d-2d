extends RefCounted
# Root-only probe. No project/asset mutation or generated-helper parser change.
const Spring = preload("res://src/secondary_spring.gd")
const Live = preload("res://src/secondary_live.gd")
const Definition = preload("res://src/secondary_rig.gd")
const IK = preload("res://src/limb_ik.gd")
const MIKU_SHA = "cc040e35f47280599ea083ac78d36855c99861791b0e66a28e091c12655c5aaf"
const REQUEST_FORMAT = "has_private_miku_body_collider_probe_1"
const MAX_TICKS = 1200
const CLEARANCE_TOLERANCE = 0.00005
var actor: RefCounted
var live: RefCounted
var tap: RefCounted
var private_definition: Dictionary = {}
var frame := 0
var ticks := 0
var authored_stamp := PackedByteArray()
var metrics: Dictionary = {}
var alive := false

class Tap extends RefCounted:
	var delegate: RefCounted
	var chains: Array = []
	var last_result: Dictionary = {}
	var captured: Array = []
	func _capture(sk: Skeleton3D, points: Array) -> void:
		for index in range(1,sk.get_bone_count()):
			points.append(sk.global_transform*sk.get_bone_global_pose(index))
	func step(delta: float, wind: Vector3, forces: Array = []) -> Dictionary:
		captured.clear()
		for chain in chains:
			var points: Array = []
			captured.append(points)
			var callback: Callable = _capture.bind(chain.scratch,points)
			chain.spring.modification_processed.connect(callback,CONNECT_ONE_SHOT)
		var result: Dictionary = delegate.step(delta,wind,forces)
		last_result = result.duplicate(true)
		return result
	func dispose() -> void:
		if delegate: delegate.dispose()
		delegate = null; chains.clear(); captured.clear(); last_result.clear()

static func exact_keys(value: Variant, keys: Array) -> bool:
	if not value is Dictionary or value.size()!=keys.size(): return false
	for key in keys:
		if not value.has(key): return false
	return true

static func finite_vector(value: Variant) -> bool:
	if not value is Array or value.size()!=3: return false
	for item in value:
		if not (item is int or item is float) or not is_finite(float(item)) or absf(float(item))>100.0: return false
	return true

static func vector(value: Array) -> Vector3:
	return Vector3(value[0],value[1],value[2])

static func definition_for(rig: RefCounted, request: Dictionary) -> Dictionary:
	if rig==null or not is_instance_valid(rig.root) or rig.data.get("sha256")!=MIKU_SHA: return {"error":"exact_saved_miku_asset_required"}
	if not exact_keys(request,["format","source_sha256","chain_index","enable_collision","colliders"]): return {"error":"exact_probe_request_required"}
	if request.format!=REQUEST_FORMAT or request.source_sha256!=MIKU_SHA or not request.chain_index is int or request.chain_index!=0 or not request.enable_collision is bool: return {"error":"probe_profile_differs"}
	if not request.colliders is Array or request.colliders.is_empty() or request.colliders.size()>2: return {"error":"one_or_two_reviewed_arm_colliders_required"}
	var source: Variant = rig.root.get_meta("has_secondary_rig",{})
	if not source is Dictionary or not source.get("error","").is_empty() or not source.get("chains") is Array or source.chains.size()!=1 or not source.get("colliders") is Array or not source.colliders.is_empty(): return {"error":"saved_zero_collider_definition_required"}
	var def: Dictionary = source.duplicate(true)
	var chain: Dictionary = def.chains[0]
	if not chain.get("joints") is Array or chain.joints.size()!=7 or not chain.get("colliders") is Array or not chain.colliders.is_empty() or float(chain.get("end_extension",-1))!=0.0: return {"error":"saved_six_joint_and_real_tail_required"}
	var owned := {}
	for i in range(6):
		var joint: Variant = chain.joints[i]
		if not joint is Dictionary or not joint.get("binding") is Dictionary or joint.binding.get("kind")!="bone" or not joint.binding.get("id") is String or not rig.bones.has(joint.binding.id) or owned.has(joint.binding.id): return {"error":"exact_distinct_existing_joints_required"}
		owned[joint.binding.id] = true
	var terminal: Variant = chain.joints[6].get("binding")
	if not terminal is Dictionary or terminal.get("kind")!="offset" or not owned.has(terminal.get("id")): return {"error":"existing_unweighted_tail_binding_required"}
	var reviewed: Array = []
	for item in request.colliders:
		if not item is Dictionary: return {"error":"reviewed_collider_required"}
		var kind: Variant = item.get("shape")
		var keys: Array = ["binding","shape","offset","radius","tail"] if kind=="capsule" else ["binding","shape","offset","radius"]
		if not exact_keys(item,keys) or not kind is String or not kind in ["sphere","capsule"]: return {"error":"exact_sphere_or_capsule_required"}
		if not exact_keys(item.binding,["kind","id"]) or item.binding.kind!="bone" or not item.binding.id is String or item.binding.id.is_empty() or item.binding.id.length()>512 or not rig.bones.has(item.binding.id) or owned.has(item.binding.id): return {"error":"exact_non_hair_arm_bone_required"}
		if not finite_vector(item.offset) or not (item.radius is int or item.radius is float) or not is_finite(float(item.radius)) or item.radius<=0.0 or item.radius>1.0: return {"error":"bounded_positive_collider_required"}
		if kind=="capsule" and (not finite_vector(item.tail) or vector(item.tail).distance_to(vector(item.offset))<0.000001): return {"error":"nonzero_capsule_axis_required"}
		if not IK.regular(Definition.binding_transform(rig,item.binding).basis): return {"error":"positive_uniform_collider_binding_required"}
		reviewed.append(item.duplicate(true))
	def.colliders = reviewed
	chain.colliders = range(reviewed.size()) if request.enable_collision else []
	return {"definition":def,"enabled":request.enable_collision,"reviewed_colliders":reviewed.duplicate(true)}

static func point_segment_distance(point: Vector3, a: Vector3, b: Vector3) -> float:
	var axis := b-a
	if axis.length_squared()==0.0: return point.distance_to(a)
	return point.distance_to(a+axis*clampf((point-a).dot(axis)/axis.length_squared(),0.0,1.0))

static func clearance(point: Vector3, joint_radius: float, start: Vector3, finish: Vector3, collider_radius: float) -> float:
	return point_segment_distance(point,start,finish)-joint_radius-collider_radius

static func _world_collider(rig: RefCounted, row: Dictionary) -> Dictionary:
	var t: Transform3D = Definition.binding_transform(rig,row.binding)
	if not IK.regular(t.basis): return {"error":"collider_transform_changed"}
	var size: float = t.basis.get_scale().x
	var start: Vector3 = t*vector(row.offset)
	var finish: Vector3 = t*vector(row.tail) if row.shape=="capsule" else start
	return {"start":start,"finish":finish,"radius":float(row.radius)*size}

static func begin(rig: RefCounted, at_frame: int, request: Dictionary, owner: Node) -> Dictionary:
	var prepared: Dictionary = definition_for(rig,request)
	if prepared.has("error"): return prepared
	if rig.live_pose!=null or rig.live_world_transform!=null or not rig.root.is_inside_tree() or not is_instance_valid(owner) or not owner.is_inside_tree(): return {"error":"idle_owned_model_and_host_required"}
	var probe = new()
	probe.actor = rig; probe.frame = at_frame
	probe.private_definition = prepared.definition.duplicate(true)
	probe.authored_stamp = var_to_bytes([rig.data,rig.order])
	var initial: Dictionary = rig.sample(at_frame,false)
	# Match SecondaryLive.create: construct from the requested authored sample.
	rig.live_pose = initial.duplicate(true); rig.apply_current(at_frame,false)
	var result: Dictionary = Spring.construct(rig,probe.private_definition,owner)
	if result.has("error"):
		rig.live_pose = null; rig.apply_current(at_frame,false); return result
	probe.tap = Tap.new(); probe.tap.delegate = result.runner; probe.tap.chains = result.runner.chains
	probe.live = Live.new(); probe.live.rig = rig; probe.live.runner = probe.tap
	probe.live.initial_frame = at_frame; probe.live.last_input_time = float(at_frame)
	probe.live.initial_pose = initial.duplicate(true); probe.live.latest = initial.duplicate(true)
	probe.live.initial_world = rig.root.global_transform; probe.live.native_backend = false
	probe.metrics = {"format":"has_miku_body_collision_probe_summary_1","collision_enabled":prepared.enabled,
		"reviewed_collider_count":prepared.reviewed_colliders.size(),"ticks":0,
		"solver_particle_min_clearance":INF,"raw_fk_particle_min_clearance":INF,"visible_particle_min_clearance":INF,
		"solver_penetrating_samples":0,"raw_fk_penetrating_samples":0,"visible_penetrating_samples":0,
		"maximum_raw_fk_pivot_error":0.0,"maximum_visible_vs_solver_pivot_error":0.0,
		"clearance_tolerance":CLEARANCE_TOLERANCE,"skin_or_segment_nonpenetration_qualified":false,
		"actual_saved_case_reproduced":false,"application_adopted":false}
	# Same engine initialization boundary as Spring.create; no eager tick zero.
	await rig.root.get_tree().process_frame
	await RenderingServer.frame_post_draw
	if not is_instance_valid(rig.root) or not rig.root.is_inside_tree() or var_to_bytes([rig.data,rig.order])!=probe.authored_stamp:
		probe.live.dispose()
		if is_instance_valid(rig.root): rig.apply_current(at_frame,false)
		return {"error":"model_changed_during_probe_setup"}
	probe.live.start(); probe.alive = true
	return {"probe":probe}

func _points() -> Array:
	var result: Array = []
	for joint in private_definition.chains[0].joints:
		result.append(Definition.binding_transform(actor,joint.binding).origin)
	return result

func _measure(points: Array, key: String, counter: String, colliders: Array, size: float) -> void:
	var joints: Array = private_definition.chains[0].joints
	for i in range(points.size()):
		var radius: float = float(joints[mini(i,joints.size()-1)].radius)*size
		for collider in colliders:
			var gap: float = clearance(points[i],radius,collider.start,collider.finish,collider.radius)
			metrics[key] = minf(metrics[key],gap)
			if gap < -CLEARANCE_TOLERANCE: metrics[counter] += 1

func _failed(code: String) -> Dictionary:
	dispose()
	return {"error":code}

func advance(fields: Array, runtime: RefCounted) -> Dictionary:
	if not alive: return {"error":"probe_not_running"}
	if ticks>=MAX_TICKS or var_to_bytes([actor.data,actor.order])!=authored_stamp: return _failed("probe_lifetime_or_authored_state_changed")
	var error: String = live.advance(1.0/120.0,frame,float(frame),false,fields,runtime)
	if not error.is_empty(): return _failed(error)
	if tap.last_result.has("error") or tap.captured.size()!=1 or tap.captured[0].size()!=7: return _failed("complete_actual_modifier_capture_required")
	var solved: Array = []
	for transform in tap.captured[0]: solved.append(transform.origin)
	var visible: Array = _points()
	var first: Dictionary = private_definition.chains[0].joints[0]
	var size: float = Definition.binding_transform(actor,first.binding).basis.get_scale().x
	var obstacles: Array = []
	for row in private_definition.colliders:
		var observed: Dictionary = _world_collider(actor,row)
		if observed.has("error"): return _failed(observed.error)
		obstacles.append(observed)
	# Temporarily apply the REAL returned raw pose to test reconstruction, then
	# restore the REAL SecondaryLive blended pose. No duplicate blend algorithm.
	var final_pose: Dictionary = live.latest.duplicate(true)
	var raw_pose: Dictionary = live.initial_pose.duplicate(true)
	for id in tap.last_result.pose: raw_pose[id] = tap.last_result.pose[id].duplicate(true)
	actor.live_pose = raw_pose; actor.apply_current(frame)
	var raw_fk: Array = _points()
	actor.live_pose = final_pose; actor.apply_current(frame)
	for i in range(7):
		if not solved[i].is_finite() or not raw_fk[i].is_finite() or not visible[i].is_finite(): return _failed("nonfinite_probe_geometry")
		metrics.maximum_raw_fk_pivot_error = maxf(metrics.maximum_raw_fk_pivot_error,solved[i].distance_to(raw_fk[i]))
		metrics.maximum_visible_vs_solver_pivot_error = maxf(metrics.maximum_visible_vs_solver_pivot_error,solved[i].distance_to(visible[i]))
	_measure(solved,"solver_particle_min_clearance","solver_penetrating_samples",obstacles,size)
	_measure(raw_fk,"raw_fk_particle_min_clearance","raw_fk_penetrating_samples",obstacles,size)
	_measure(visible,"visible_particle_min_clearance","visible_penetrating_samples",obstacles,size)
	ticks += 1; metrics.ticks = ticks
	if var_to_bytes([actor.data,actor.order])!=authored_stamp: return _failed("probe_mutated_authored_state")
	return {"ok":true}

func summary() -> Dictionary:
	var result: Dictionary = metrics.duplicate(true)
	result.authored_state_unchanged = actor!=null and var_to_bytes([actor.data,actor.order])==authored_stamp
	result.probe_finished = not alive
	# A zero-tick setup is not a finite contact measurement.
	if ticks==0:
		for key in ["solver_particle_min_clearance","raw_fk_particle_min_clearance","visible_particle_min_clearance"]: result[key] = null
	return result

func dispose() -> void:
	if live: live.dispose()
	alive = false
	if actor!=null and is_instance_valid(actor.root): actor.apply_current(frame)
