extends SceneTree
# Anatomical-axis oracles use these authored coordinates, not planner output.
# Tiny raw coordinates and reciprocal skeleton scale encode the same figure.
const Rig = preload("res://src/physics_rig.gd")
const NAMES: Array[String] = ["hips","spine","head","upper_arm.L","forearm.L","hand.L","upper_arm.R","forearm.R","hand.R","thigh.L","shin.L","foot.L","thigh.R","shin.R","foot.R"]
const PARENTS: Array[int] = [-1,0,1,1,3,4,1,6,7,0,9,10,0,12,13]
const POINTS: Array[Vector3] = [Vector3(0,1,0),Vector3(0,1.3,0),Vector3(0,1.7,0),Vector3(.25,1.5,0),Vector3(.55,1.5,0),Vector3(.8,1.5,0),Vector3(-.25,1.5,0),Vector3(-.55,1.5,0),Vector3(-.8,1.5,0),Vector3(.12,.95,0),Vector3(.12,.55,0),Vector3(.12,.15,0),Vector3(-.12,.95,0),Vector3(-.12,.55,0),Vector3(-.12,.15,0)]
var checks: int = 0
var failures: int = 0

class Subject extends RefCounted:
	var root: Node3D
	var data: Dictionary = {"metadata":{}}
	var bones: Dictionary = {}
	var order: Array[String] = []
	func parent_id(id: String) -> String:
		var info: Dictionary = bones[id]
		var sk: Skeleton3D = info.skeleton
		var parent: int = sk.get_bone_parent(info.index)
		return "@root" if parent < 0 else str(sk.get_bone_name(parent))
	func bone_transform(id: String) -> Transform3D:
		var info: Dictionary = bones[id]
		return info.skeleton.global_transform*info.skeleton.get_bone_global_pose(info.index)

func _initialize() -> void:
	call_deferred("run")

func check(value: bool,label: String) -> void:
	checks += 1
	print(("PASS " if value else "FAIL ")+label)
	if not value:failures += 1

func fixture(raw_unit: float) -> Subject:
	var subject: Subject = Subject.new()
	subject.root = Node3D.new()
	# Root forward is +X; the independent left/up body landmarks define +Z.
	subject.root.transform = Transform3D(Basis(Vector3.UP,PI*0.5),Vector3(2,3,-4))
	root.add_child(subject.root)
	var sk: Skeleton3D = Skeleton3D.new();sk.name = "AnatomySkeleton"
	sk.basis = Basis(Vector3.UP,-PI*0.5).scaled(Vector3.ONE/raw_unit)
	subject.root.add_child(sk)
	for index in range(NAMES.size()):
		sk.add_bone(NAMES[index])
		if PARENTS[index] >= 0:sk.set_bone_parent(index,PARENTS[index])
		var offset: Vector3 = POINTS[index]-(POINTS[PARENTS[index]] if PARENTS[index] >= 0 else Vector3.ZERO)
		sk.set_bone_rest(index,Transform3D(Basis.IDENTITY,offset*raw_unit))
		subject.order.append(NAMES[index])
		subject.bones[NAMES[index]] = {"name":NAMES[index],"index":index,"skeleton":sk}
	sk.reset_bone_poses();sk.force_update_all_bone_transforms()
	return subject

func snapshot(subject: Subject) -> Dictionary:
	var sk: Skeleton3D = subject.bones.hips.skeleton
	var poses: Array[Transform3D] = []
	for index in range(sk.get_bone_count()):poses.append(sk.get_bone_pose(index))
	return {"root":subject.root.transform,"skeleton":sk.transform,"poses":poses,"data":var_to_bytes(subject.data),"children":sk.get_children(true)}

func run() -> void:
	var expected_hinges: Dictionary = {"forearm.L":Vector3.DOWN,"forearm.R":Vector3.UP,"shin.L":Vector3.RIGHT,"shin.R":Vector3.RIGHT}
	var expected_limb_axes: Dictionary = {"upper_arm.L":Vector3.RIGHT,"hand.L":Vector3.RIGHT,"upper_arm.R":Vector3.LEFT,"hand.R":Vector3.LEFT,"thigh.L":Vector3.DOWN,"foot.L":Vector3.DOWN,"thigh.R":Vector3.DOWN,"foot.R":Vector3.DOWN}
	var reference: Dictionary = {}
	for raw_unit in [0.001,1.0,1000.0]:
		var subject: Subject = fixture(raw_unit)
		var sk: Skeleton3D = subject.bones.hips.skeleton
		var before: Dictionary = snapshot(subject)
		var metric: Dictionary = Rig.profiles(subject,subject.order,sk,true)
		var legacy: Dictionary = Rig.profiles(subject,subject.order,sk,false)
		check(metric.size() == NAMES.size() and legacy.size() == NAMES.size(),"full humanoid receives four limbs and connecting profiles: "+str(raw_unit))
		check(Rig.profiles(subject,subject.order,sk) == legacy,"default profiles retain the exact legacy path: "+str(raw_unit))
		var actual_forward: Vector3 = subject.root.global_basis.z.normalized()
		check(absf(actual_forward.dot(Vector3.BACK)) < 0.00001,"root forward deliberately differs from landmark anatomical forward")
		for id in expected_hinges:
			var profile: Dictionary = metric[id]
			check(profile.axis.distance_to(expected_hinges[id]) < 0.00002 and absf(profile.axis.length()-1.0) < 0.00002,"metric anatomical hinge axis uses authored body frame: "+str([raw_unit,id]))
			check(absf(float(profile.lower)+150.0) < 0.00002 and absf(float(profile.upper)-5.0) < 0.00002,"straight anatomical hinge retains degree limits: "+id)
		for id in expected_limb_axes:check(metric[id].axis.distance_to(expected_limb_axes[id]) < 0.00002,"metric cone/twist axis follows the authored limb: "+str([raw_unit,id]))
		for id in ["hips","spine","head"]:check(metric[id].part == "connector" and metric[id].axis.distance_to(Vector3.RIGHT) < 0.00002,"metric connector retains original bone orientation: "+id)
		if raw_unit == 0.001:
			# This is the retained legacy behavior, including the raw cross-length
			# threshold and subsequent UP/RIGHT fallback. It must not be retuned.
			check(legacy["forearm.L"].axis.distance_to(Vector3.BACK) < 0.00002 and legacy["forearm.R"].axis.distance_to(Vector3.FORWARD) < 0.00002 and legacy["shin.L"].axis.distance_to(Vector3.BACK) < 0.00002 and legacy["shin.R"].axis.distance_to(Vector3.BACK) < 0.00002,"tiny raw legacy fixture retains its original root/fallback hinge planes")
			check(metric["forearm.L"].axis.distance_to(legacy["forearm.L"].axis) > 1.0,"active metre frame repairs the formerly representation-dependent plane")
			reference = metric.duplicate(true)
		else:
			var equivalent: bool = true
			for id in NAMES:equivalent = equivalent and metric[id].axis.distance_to(reference[id].axis) < 0.00002
			check(equivalent,"equivalent .001/1/1000 raw coordinate encodings retain anatomical axes")
			check(metric == legacy,"ordinary/large legacy source retains its established profile values")
		check(snapshot(subject) == before,"profile preparation does not allocate or mutate source rig state")
		subject.root.free()
	print("REFERENCE_BODY_ANATOMY_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures == 0 else 1)
