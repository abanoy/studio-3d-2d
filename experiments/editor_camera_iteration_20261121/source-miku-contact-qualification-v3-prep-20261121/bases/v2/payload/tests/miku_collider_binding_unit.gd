extends SceneTree
const Binder=preload("res://src/miku_collider_binding.gd")
const Probe=preload("res://src/secondary_collision_probe.gd")
var checks:=0
var failures:=0
class Actor extends RefCounted:
	var root:=Node3D.new()
	var skeleton:=Skeleton3D.new()
	var data: Dictionary={"sha256":Probe.MIKU_SHA,"metadata":{}}
	var order: Array[String]=[]
	var bones: Dictionary={}
	func parent_id(id: String) -> String:
		var info: Dictionary=bones[id]
		var parent: int=info.skeleton.get_bone_parent(info.index)
		return "@root" if parent<0 else str(root.get_path_to(info.skeleton))+"::"+str(info.skeleton.get_bone_name(parent))
	func dispose() -> void:root.free()
func fixture() -> RefCounted:
	var actor:=Actor.new();actor.skeleton.name="Rig";actor.root.add_child(actor.skeleton);root.add_child(actor.root)
	var map: Dictionary={}
	for i in range(4):
		var name: String=["Shoulder_R","UpperArm_R","LowerArm_R","Hand_R"][i]
		actor.skeleton.add_bone(name)
		if i>0:actor.skeleton.set_bone_parent(i,i-1)
		var id: String="Rig::"+name
		actor.order.append(id);actor.bones[id]={"skeleton":actor.skeleton,"index":i,"name":name,"path":"Rig"}
		map[10+i]=id
	actor.root.set_meta("has_source_bones",map)
	return actor
func rows() -> Array:
	return [{"role":"rightUpperArm","source_binding":{"kind":"gltf_skin_joint","node_index":11,"end_node_index":12,"verified_parent_index":10}},
		{"role":"rightLowerArm","source_binding":{"kind":"gltf_skin_joint","node_index":12,"end_node_index":13,"verified_parent_index":11}}]
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+"miku_binding."+label)
func _initialize() -> void:
	create_timer(10).timeout.connect(func():push_error("Miku binding controls watchdog");quit(2));call_deferred("run")
func run() -> void:
	var actor: RefCounted=fixture();var input: Array=rows()
	var before: PackedByteArray=var_to_bytes([actor.data,actor.order,actor.root.get_meta("has_source_bones"),input])
	var result: Dictionary=Binder.resolve_runtime(actor,input)
	check(not result.has("error") and result.bindings.rightUpperArm.id=="Rig::UpperArm_R" and result.bindings.rightLowerArm.id=="Rig::LowerArm_R","source_indices_resolve_exact_runtime_bones")
	check(not result.has("error") and result.source_runtime_identity_resolved and not result.collider_alignment_qualified,"identity_is_not_geometric_alignment")
	check(before==var_to_bytes([actor.data,actor.order,actor.root.get_meta("has_source_bones"),input]),"resolving_preserves_source_map_actor_and_inputs")
	var wire_rows: Array=JSON.parse_string(JSON.stringify(input,"",true,true))
	check(not Binder.resolve_runtime(actor,wire_rows).has("error"),"whole_json_source_indices_keep_identity")
	result.bindings.rightUpperArm.id="foreign"
	check(actor.root.get_meta("has_source_bones")[11]=="Rig::UpperArm_R" and input[0].source_binding.node_index==11,"returned_bindings_are_detached")
	for invalid in [[],["foreign"],["rightUpperArm","rightUpperArm"],[true],null]:
		check(not Binder.roles_error(invalid).is_empty(),"bad_selected_roles_"+str(checks))
	check(Binder.roles_error(["rightUpperArm"]).is_empty() and Binder.roles_error(["rightUpperArm","rightLowerArm"]).is_empty(),"explicit_one_or_two_roles_admitted")
	for kind in ["missing_role","duplicate_role","fractional_index","bool_index","negative_index","foreign_index","missing_parent","disconnected_end"]:
		var bad: Array=rows()
		match kind:
			"missing_role":bad.pop_back()
			"duplicate_role":bad[1].role="rightUpperArm"
			"fractional_index":bad[0].source_binding.node_index=11.5
			"bool_index":bad[0].source_binding.node_index=true
			"negative_index":bad[0].source_binding.node_index=-1
			"foreign_index":bad[0].source_binding.node_index=99
			"missing_parent":bad[0].source_binding.erase("verified_parent_index")
			"disconnected_end":bad[0].source_binding.end_node_index=13
		check(Binder.resolve_runtime(actor,bad).has("error"),"source_role_refusal_"+kind)
	var map: Dictionary=actor.root.get_meta("has_source_bones").duplicate()
	var changed: Dictionary=map.duplicate();changed[13]=map[11];actor.root.set_meta("has_source_bones",changed)
	check(Binder.resolve_runtime(actor,rows()).has("error"),"distinct_source_roles_cannot_alias_runtime_bone")
	actor.root.set_meta("has_source_bones",map);actor.skeleton.set_bone_parent(2,0)
	check(Binder.resolve_runtime(actor,rows()).has("error"),"actual_runtime_parent_drift_refused")
	actor.skeleton.set_bone_parent(2,1);actor.bones["Rig::UpperArm_R"].index=0
	check(Binder.resolve_runtime(actor,rows()).has("error"),"stale_runtime_index_refused")
	actor.bones["Rig::UpperArm_R"].index=1
	actor.skeleton.set_bone_name(1,"Foreign")
	check(Binder.resolve_runtime(actor,rows()).has("error"),"stale_runtime_name_refused")
	actor.skeleton.set_bone_name(1,"UpperArm_R")
	actor.data.sha256="0".repeat(64)
	check(Binder.resolve_runtime(actor,rows()).has("error"),"different_loaded_asset_refused")
	actor.data.sha256=Probe.MIKU_SHA
	check(Binder.from_bytes(actor,PackedByteArray(),["rightUpperArm"],true).has("error"),"empty_private_input_refused")
	check(Binder.from_bytes(actor,"{}".to_utf8_buffer(),["rightUpperArm"],true).has("error"),"substitute_private_input_refused")
	check(Binder.from_bytes(actor,"{}".to_utf8_buffer(),["rightUpperArm"],1).has("error"),"numeric_collision_boolean_refused")
	actor.dispose()
	print("MIKU_BINDING_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"native_asset_tested":false,"private_input_loaded":false,"geometry_or_contact_qualified":false,"application_adopted":false}))
	quit(0 if failures==0 else 1)
