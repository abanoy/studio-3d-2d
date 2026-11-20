extends SceneTree
# Geometry/validation checks only. Engine/Jolt and editor lifecycle qualification
# live in separate integration tests; passing this file does not certify them.
const Plan = preload("res://src/reference_body_plan.gd")
const IDS: Array[String] = ["upper","lower","tip"]
var checks: int = 0
var failures: int = 0

class Subject extends RefCounted:
	var bones: Dictionary = {}
	func parent_id(id: String) -> String:
		return {"upper":"@root","lower":"upper","tip":"lower"}[id]
	func bone_transform(id: String) -> Transform3D:
		var info: Dictionary = bones[id]
		var sk: Skeleton3D = info.skeleton
		return sk.global_transform*sk.get_bone_global_pose(info.index)

func check(value: bool, label: String) -> void:
	checks += 1
	print(("PASS " if value else "FAIL ")+label)
	if not value:failures += 1

func _initialize() -> void:
	call_deferred("run")

func fixture(raw_unit: float = 1.0) -> Dictionary:
	var subject: Subject = Subject.new()
	var sk: Skeleton3D = Skeleton3D.new()
	sk.transform = Transform3D(Basis.from_euler(Vector3(-0.17,0.31,0.0)).scaled(Vector3.ONE/raw_unit),Vector3(2,3,4))
	root.add_child(sk)
	var offsets: Array[Vector3] = [Vector3.ZERO,Vector3(0.8,0,0),Vector3(0.6,0,0)]
	for index in range(3):
		sk.add_bone(IDS[index])
		if index > 0:sk.set_bone_parent(index,index-1)
		sk.set_bone_rest(index,Transform3D(Basis.IDENTITY,offsets[index]*raw_unit))
		subject.bones[IDS[index]] = {"skeleton":sk,"index":index}
	sk.reset_bone_poses()
	sk.force_update_all_bone_transforms()
	var bounds: Dictionary = {"upper":AABB(Vector3(-0.09,-0.2,-0.1)*raw_unit,Vector3(0.18,0.4,0.2)*raw_unit)}
	return {"actor":subject,"skeleton":sk,"bounds":bounds}

func build(value: Dictionary) -> Dictionary:
	return Plan.build(value.actor,value.skeleton,IDS,{},value.bounds)

func topology(value: Dictionary) -> Dictionary:
	var sk: Skeleton3D = value.skeleton
	var poses: Array[Transform3D] = []
	for index in range(sk.get_bone_count()):poses.append(sk.get_bone_pose(index))
	return {"children":sk.get_children(true),"transform":sk.transform,"poses":poses,"bounds":value.bounds.duplicate(true)}

func run() -> void:
	var standard: Dictionary = fixture()
	var before: Dictionary = topology(standard)
	var result: Dictionary = build(standard)
	check(not result.has("error") and result.bodies.size() == 3,"complete bounded plan exists before allocation")
	check(topology(standard) == before,"planning preserves children, transforms, poses and supplied bounds")
	if result.has("error"):
		standard.skeleton.free()
		quit(1)
		return
	check(absf(result.size-1.4) < 0.00002,"skeleton-axis span is measured in metres")
	check(result.bodies.upper.kind == "box" and result.bodies.lower.kind == "capsule" and result.bodies.tip.kind == "sphere","skin box and both fallback policies remain available")
	var expected_box: Vector3 = Vector3(0.18,0.4,0.2)+Vector3.ONE*1.4*0.003
	check(result.bodies.upper.size.is_equal_approx(expected_box),"box dimensions include metre padding")
	check(absf(result.bodies.lower.radius-0.063) < 0.00002 and absf(result.bodies.lower.height-0.54) < 0.00002,"capsule radius clamp and height use metre lengths")
	check(absf(result.bodies.tip.radius-0.049) < 0.00002,"terminal sphere radius uses metre span")
	for raw_unit in [0.001,1.0,1000.0]:
		var value: Dictionary = fixture(raw_unit)
		var retained: Dictionary = topology(value)
		var other: Dictionary = build(value)
		check(not other.has("error"),"defensive scale-bound representation admits geometry plan: "+str(raw_unit))
		if not other.has("error"):
			check(absf(other.size-1.4) < 0.00002,"equivalent source encodings retain metre span: "+str(raw_unit))
			for id in IDS:
				var description: Dictionary = other.bodies[id]
				var expected: Dictionary = result.bodies[id]
				var world: Transform3D = value.actor.bone_transform(id)
				var offset: Transform3D = description.body_offset
				var body: Transform3D = description.world_frame
				check(description.kind == expected.kind and body.is_equal_approx(expected.world_frame),"equivalent source encoding retains proxy/frame: "+str([raw_unit,id]))
				check((world*offset).is_equal_approx(body) and (body*offset.affine_inverse()).is_equal_approx(world),"inverse offset preserves both rest identities: "+str([raw_unit,id]))
				check(body.basis.get_scale().is_equal_approx(Vector3.ONE) and description.margin > 0.0 and description.margin <= 0.005,"unit physical frame and metre margin: "+str([raw_unit,id]))
				if description.kind == "box":check(description.size.is_equal_approx(expected.size),"source-unit encoding retains fitted box dimensions")
				else:check(absf(description.radius-expected.radius) < 0.00002,"source-unit encoding retains fallback radius")
		check(topology(value) == retained,"representation planning does not mutate fixture: "+str(raw_unit))
		value.skeleton.free()
	for basis in [Basis.IDENTITY.scaled(Vector3(1,2,1)),Basis.IDENTITY.scaled(Vector3(-1,1,1)),Basis(Vector3.RIGHT,Vector3(0.1,1,0),Vector3.BACK),Basis.IDENTITY.scaled(Vector3.ONE*0.0005),Basis.IDENTITY.scaled(Vector3.ONE*2000.0)]:
		var value: Dictionary = fixture()
		value.skeleton.basis = basis
		var retained: Dictionary = topology(value)
		check(build(value).has("error") and topology(value) == retained,"unsupported metric frames refuse without mutation")
		value.skeleton.free()
	for invalid in [AABB(Vector3.ZERO,Vector3(-1,1,1)),AABB(Vector3(INF,0,0),Vector3.ONE),AABB(Vector3.ZERO,Vector3.ONE*20000.0),AABB(Vector3(20000,0,0),Vector3.ONE),"not bounds"]:
		var value: Dictionary = fixture()
		value.bounds.upper = invalid
		var retained: Dictionary = topology(value)
		check(build(value).has("error") and topology(value) == retained,"invalid or oversized bounds refuse atomically")
		value.skeleton.free()
	var flat: Dictionary = fixture()
	flat.bounds.upper = AABB(Vector3(0,-0.2,-0.1),Vector3(0,0.4,0.2))
	var flat_plan: Dictionary = build(flat)
	check(not flat_plan.has("error") and flat_plan.bodies.upper.kind == "box" and absf(flat_plan.bodies.upper.size.x-0.0042) < 0.00002,"zero source box extent receives positive metre padding")
	flat.skeleton.free()
	var tiny: Dictionary = fixture()
	tiny.skeleton.basis = tiny.skeleton.basis.scaled(Vector3.ONE*0.001)
	var tiny_plan: Dictionary = build(tiny)
	check(not tiny_plan.has("error") and absf(tiny_plan.size-0.01) < 0.0000001,"span floor is one centimetre after world conversion")
	tiny.skeleton.free()
	for child_distance in [0.00009,0.00011]:
		var threshold: Dictionary = fixture()
		threshold.bounds.clear()
		threshold.skeleton.set_bone_rest(1,Transform3D(Basis.IDENTITY,Vector3(child_distance,0,0)))
		threshold.skeleton.set_bone_rest(2,Transform3D(Basis.IDENTITY,Vector3(0.001,0,0)))
		threshold.skeleton.reset_bone_poses()
		threshold.skeleton.force_update_all_bone_transforms()
		var threshold_plan: Dictionary = build(threshold)
		check(not threshold_plan.has("error") and (threshold_plan.bodies.upper.length == 0.0 if child_distance < 0.0001 else threshold_plan.bodies.upper.length > 0.0001),"nearest-child cutoff is one tenth millimetre in world geometry")
		threshold.skeleton.free()
	var many_ids: Array[String] = []
	for index in range(49):many_ids.append("id_"+str(index))
	check(Plan.build(standard.actor,standard.skeleton,many_ids,{},standard.bounds).has("error"),"structural body budget refuses before ID traversal")
	var distant: Dictionary = fixture()
	distant.skeleton.position = Vector3(100001,0,0)
	var distant_before: Dictionary = topology(distant)
	check(build(distant).has("error") and topology(distant) == distant_before,"absolute world-origin budget refuses without allocation")
	distant.skeleton.free()
	var duplicate_ids: Array[String] = ["upper","lower","lower"]
	check(Plan.build(standard.actor,standard.skeleton,duplicate_ids,{},standard.bounds).has("error"),"duplicate canonical IDs refuse")
	var short_ids: Array[String] = ["upper","lower"]
	check(Plan.build(standard.actor,standard.skeleton,short_ids,{},standard.bounds).has("error"),"incomplete body set refuses")
	standard.bounds["outside"] = AABB(Vector3.ZERO,Vector3.ONE)
	check(build(standard).has("error"),"bounds cannot invent an unselected owner")
	standard.skeleton.free()
	print("REFERENCE_BODY_PLAN_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures == 0 else 1)
