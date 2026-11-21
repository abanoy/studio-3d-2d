extends SceneTree
const Probe = preload("res://src/secondary_collision_probe.gd")
var checks := 0
var failures := 0
class Actor extends RefCounted:
	var root := Node3D.new()
	var data := {"sha256":Probe.MIKU_SHA}
	var bones := {}
	var transforms := {}
	func bone_transform(id: String) -> Transform3D: return transforms[id]
	func dispose() -> void: root.free()
func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures += 1
	print(("PASS " if value else "FAIL ")+"collision_probe."+label)
func fixture() -> RefCounted:
	var actor := Actor.new()
	var joints: Array = []
	for i in range(6):
		var id: String = "hair"+str(i)
		actor.bones[id] = {}; actor.transforms[id] = Transform3D.IDENTITY
		joints.append({"binding":{"kind":"bone","id":id},"radius":0.005})
	joints.append({"binding":{"kind":"offset","id":"hair5","position":[0,1,0],"rotation_xyzw":[0,0,0,1],"scale":[1,1,1]},"radius":0.005})
	actor.bones.arm = {}; actor.transforms.arm = Transform3D.IDENTITY
	actor.root.set_meta("has_secondary_rig",{"error":"","chains":[{"joints":joints,"colliders":[],"end_extension":0.0}],"colliders":[]})
	return actor
func request() -> Dictionary:
	return {"format":Probe.REQUEST_FORMAT,"source_sha256":Probe.MIKU_SHA,"chain_index":0,"enable_collision":true,
		"colliders":[{"binding":{"kind":"bone","id":"arm"},"shape":"capsule","offset":[0,0,0],"tail":[0,1,0],"radius":0.1}]}
func _initialize() -> void: call_deferred("run")
func run() -> void:
	check(is_equal_approx(Probe.point_segment_distance(Vector3(3,0.5,0),Vector3.ZERO,Vector3.UP),3.0),"perpendicular_capsule_distance")
	check(is_equal_approx(Probe.point_segment_distance(Vector3(0,3,0),Vector3.ZERO,Vector3.UP),2.0),"past_endpoint_clamps_to_cap")
	check(is_equal_approx(Probe.point_segment_distance(Vector3(0,-2,0),Vector3.ZERO,Vector3.UP),2.0),"before_endpoint_clamps_to_cap")
	check(is_equal_approx(Probe.clearance(Vector3(0.3,0.5,0),0.1,Vector3.ZERO,Vector3.UP,0.2),0.0),"two_radii_tangent_clearance")
	check(is_equal_approx(Probe.clearance(Vector3(0.1,0.5,0),0.1,Vector3.ZERO,Vector3.UP,0.2),-0.2),"signed_overlap_is_negative")
	check(is_equal_approx(Probe.clearance(Vector3(0,0,3),0.1,Vector3.ZERO,Vector3.ZERO,0.2),2.7),"sphere_is_degenerate_segment")
	var actor: RefCounted = fixture(); var input: Dictionary = request()
	var before: PackedByteArray = var_to_bytes([actor.data,actor.root.get_meta("has_secondary_rig"),input])
	var result: Dictionary = Probe.definition_for(actor,input)
	check(not result.has("error") and result.definition.colliders.size()==1 and result.definition.chains[0].colliders==[0],"one_explicit_capsule_with_chain_membership")
	check(before==var_to_bytes([actor.data,actor.root.get_meta("has_secondary_rig"),input]),"preflight_does_not_mutate_source_or_request")
	result.definition.colliders[0].radius = 0.4
	check(is_equal_approx(input.colliders[0].radius,0.1) and actor.root.get_meta("has_secondary_rig").colliders.is_empty(),"detached_collider_copy")
	var control: Dictionary = request(); control.enable_collision = false
	result = Probe.definition_for(actor,control)
	check(not result.has("error") and result.definition.colliders.size()==1 and result.definition.chains[0].colliders.is_empty(),"disabled_control_keeps_same_analytic_obstacle")
	var sphere: Dictionary = request(); sphere.colliders[0].shape = "sphere"; sphere.colliders[0].erase("tail")
	check(not Probe.definition_for(actor,sphere).has("error"),"explicit_sphere_admitted")
	var two: Dictionary = request(); two.colliders.append(sphere.colliders[0].duplicate(true))
	check(not Probe.definition_for(actor,two).has("error"),"two_reviewed_shapes_bound")
	for kind in ["missing_field","unknown_field","wrong_source","wrong_index","bool_index","no_shapes","three_shapes","foreign_bone","hair_bone","negative_radius","nonfinite_radius","zero_axis","unknown_shape","linked_group"]:
		var bad: Dictionary = request()
		match kind:
			"missing_field": bad.erase("source_sha256")
			"unknown_field": bad["guess_names"] = true
			"wrong_source": bad.source_sha256 = "0".repeat(64)
			"wrong_index": bad.chain_index = 1
			"bool_index": bad.chain_index = false
			"no_shapes": bad.colliders.clear()
			"three_shapes": bad.colliders.append(bad.colliders[0].duplicate(true)); bad.colliders.append(bad.colliders[0].duplicate(true))
			"foreign_bone": bad.colliders[0].binding.id = "unbound"
			"hair_bone": bad.colliders[0].binding.id = "hair0"
			"negative_radius": bad.colliders[0].radius = -0.1
			"nonfinite_radius": bad.colliders[0].radius = NAN
			"zero_axis": bad.colliders[0].tail = [0,0,0]
			"unknown_shape": bad.colliders[0].shape = "mesh"
			"linked_group": bad.colliders[0]["colliderGroups"] = [0]
		check(Probe.definition_for(actor,bad).has("error"),"atomic_refusal_"+kind)
	actor.transforms.arm = Transform3D(Basis.IDENTITY.scaled(Vector3(-1,1,1)),Vector3.ZERO)
	check(Probe.definition_for(actor,request()).has("error"),"reflected_arm_binding_refused")
	actor.transforms.arm = Transform3D(Basis.IDENTITY.scaled(Vector3(1,2,1)),Vector3.ZERO)
	check(Probe.definition_for(actor,request()).has("error"),"nonuniform_arm_binding_refused")
	actor.transforms.arm = Transform3D(Basis(Vector3.FORWARD,-PI/2).scaled(Vector3.ONE*2),Vector3(3,4,5))
	var observed: Dictionary = Probe._world_collider(actor,{"binding":{"kind":"bone","id":"arm"},"shape":"capsule","offset":[1,0,0],"tail":[1,2,0],"radius":0.1})
	check(observed.start.distance_to(Vector3(3,6,5))<0.00001 and observed.finish.distance_to(Vector3(-1,6,5))<0.00001 and is_equal_approx(observed.radius,0.2),"independent_rotated_scaled_capsule_world_geometry")
	actor.transforms.arm = Transform3D.IDENTITY
	var old: Dictionary = actor.root.get_meta("has_secondary_rig").duplicate(true)
	var malformed: Dictionary = old.duplicate(true); malformed.chains[0].joints.pop_back(); actor.root.set_meta("has_secondary_rig",malformed)
	check(Probe.definition_for(actor,request()).has("error"),"changed_saved_joint_inventory_refused")
	actor.root.set_meta("has_secondary_rig",old); actor.data.sha256 = "0".repeat(64)
	check(Probe.definition_for(actor,request()).has("error"),"current_asset_substitution_refused")
	actor.dispose()
	print("MIKU_COLLISION_PROBE_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_asset_tested":false,"engine_contact_tested":false,"application_adopted":false}))
	quit(0 if failures==0 else 1)
