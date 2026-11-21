extends RefCounted
# Read-only Root probe adapter; this is not a saved-model capability.
const Probe=preload("res://src/secondary_collision_probe.gd")
const IK=preload("res://src/limb_ik.gd")
const INPUT_SHA="e3ada9ac313b21919c3a0d35617d8ec1dbd8cdf6abfe5dec0d8af4f7dd699971"
const PROJECT_SHA="036eb37fcb17d71e6292751bb1af4b73350512c69a0c31a59efb4fa6a4341101"
const INPUT_FORMAT="has_private_measured_miku_arm_collider_input_1"
const ROLES=["rightUpperArm","rightLowerArm"]

static func whole(value,minimum: int,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(float(value)) and value>=minimum and value<=maximum

static func roles_error(roles) -> String:
	if not roles is Array or roles.is_empty() or roles.size()>2:return "one_or_two_explicit_collider_roles_required"
	var seen: Dictionary={}
	for role in roles:
		if not role is String or not role in ROLES or seen.has(role):return "unknown_or_duplicate_collider_role"
		seen[role]=true
	return ""

static func _id_for(rig: RefCounted, source: Dictionary, index) -> Dictionary:
	if not whole(index,0,99999) or not source.has(int(index)):return {"error":"source_node_binding_missing"}
	var id=source[int(index)]
	if not id is String or id.is_empty() or not rig.bones.has(id):return {"error":"runtime_bone_binding_missing"}
	var info=rig.bones[id]
	if not info is Dictionary or not info.get("skeleton") is Skeleton3D or not is_instance_valid(info.skeleton) or not info.get("index") is int or not info.get("name") is String:return {"error":"runtime_bone_record_changed"}
	var skeleton: Skeleton3D=info.skeleton
	if not rig.root.is_ancestor_of(skeleton) or info.index<0 or info.index>=skeleton.get_bone_count():return {"error":"runtime_bone_owner_or_index_changed"}
	var expected: String=str(rig.root.get_path_to(skeleton))+"::"+str(skeleton.get_bone_name(info.index))
	if expected!=id or str(skeleton.get_bone_name(info.index))!=info.name:return {"error":"runtime_bone_name_or_path_changed"}
	return {"id":id,"skeleton":skeleton}

static func resolve_runtime(rig: RefCounted, rows: Array) -> Dictionary:
	if rig==null or not is_instance_valid(rig.root) or not rig.root.is_inside_tree() or rig.data.get("sha256")!=Probe.MIKU_SHA:return {"error":"exact_owned_loaded_miku_required"}
	if not rig.order is Array or rig.order.size()>4096:return {"error":"bounded_runtime_bone_inventory_required"}
	var source=rig.root.get_meta("has_source_bones",{})
	if not source is Dictionary or source.is_empty() or source.size()>100000:return {"error":"computed_source_bone_map_required"}
	if rows.size()!=2:return {"error":"complete_measured_arm_pair_required"}
	var by_role: Dictionary={}
	for row in rows:
		if not row is Dictionary or not row.get("role") is String or not row.role in ROLES or by_role.has(row.role) or not row.get("source_binding") is Dictionary:return {"error":"distinct_measured_arm_roles_required"}
		var binding: Dictionary=row.source_binding
		if binding.get("kind")!="gltf_skin_joint" or not whole(binding.get("node_index"),0,99999) or not whole(binding.get("end_node_index"),0,99999) or not whole(binding.get("verified_parent_index"),-1,99999):return {"error":"bounded_source_arm_bindings_required"}
		by_role[row.role]=row
	var upper: Dictionary=by_role.rightUpperArm.source_binding
	var lower: Dictionary=by_role.rightLowerArm.source_binding
	if upper.end_node_index!=lower.node_index:return {"error":"measured_arm_endpoints_do_not_connect"}
	var ids: Array=[]
	var skeleton: Skeleton3D
	for index in [upper.node_index,lower.node_index,lower.end_node_index]:
		var observed: Dictionary=_id_for(rig,source,index)
		if observed.has("error"):return observed
		if observed.id in ids:return {"error":"source_arm_roles_alias_one_runtime_bone"}
		if skeleton!=null and skeleton!=observed.skeleton:return {"error":"source_arm_roles_cross_skeletons"}
		skeleton=observed.skeleton;ids.append(observed.id)
	for role in ROLES:
		var binding: Dictionary=by_role[role].source_binding
		var observed: Dictionary=_id_for(rig,source,binding.node_index)
		var expected_parent: String="@root"
		if binding.verified_parent_index>=0:
			var parent: Dictionary=_id_for(rig,source,binding.verified_parent_index)
			if parent.has("error"):return parent
			expected_parent=parent.id
		if rig.parent_id(observed.id)!=expected_parent:return {"error":"source_runtime_direct_parent_differs"}
	var limb: Dictionary=IK.chain(rig,ids[2])
	if limb.get("role")!="rightHand" or not limb.get("ids") is Array or limb.ids.size()!=3:return {"error":"independent_right_hand_chain_missing"}
	for i in range(3):
		if limb.ids[i]!=ids[i]:return {"error":"source_nodes_disagree_with_semantic_arm_chain"}
	return {"bindings":{"rightUpperArm":{"kind":"bone","id":ids[0]},"rightLowerArm":{"kind":"bone","id":ids[1]}},"source_runtime_identity_resolved":true,"collider_alignment_qualified":false}

static func from_bytes(rig: RefCounted, raw: PackedByteArray, roles, enabled) -> Dictionary:
	var error: String=roles_error(roles)
	if not error.is_empty():return {"error":error}
	if not enabled is bool:return {"error":"explicit_collision_boolean_required"}
	if raw.is_empty() or raw.size()>65536:return {"error":"bounded_private_input_required"}
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(raw)
	if context.finish().hex_encode()!=INPUT_SHA:return {"error":"exact_measured_private_input_required"}
	var parser:=JSON.new()
	if parser.parse(raw.get_string_from_utf8())!=OK or not parser.data is Dictionary:return {"error":"private_input_json_required"}
	var input: Dictionary=parser.data
	if input.get("format")!=INPUT_FORMAT or input.get("source_project_sha256")!=PROJECT_SHA or input.get("source_asset_sha256")!=Probe.MIKU_SHA or input.get("probe_request_format")!=Probe.REQUEST_FORMAT or input.get("source_coordinates_changed")!=false or input.get("geometry_arrays_written")!=false or not input.get("colliders") is Array:return {"error":"measured_private_input_profile_differs"}
	var resolved: Dictionary=resolve_runtime(rig,input.colliders)
	if resolved.has("error"):return resolved
	var colliders: Array=[]
	for role in ROLES:
		if not role in roles:continue
		for row in input.colliders:
			if row.role!=role:continue
			colliders.append({"binding":resolved.bindings[role].duplicate(true),"shape":row.shape,"offset":row.offset.duplicate(),"tail":row.tail.duplicate(),"radius":row.radius})
	var request: Dictionary={"format":Probe.REQUEST_FORMAT,"source_sha256":Probe.MIKU_SHA,"chain_index":0,"enable_collision":enabled,"colliders":colliders}
	var admitted: Dictionary=Probe.definition_for(rig,request)
	if admitted.has("error"):return admitted
	return {"request":request,"source_runtime_identity_resolved":true,"selected_collider_roles":roles.duplicate(),"input_sha256":INPUT_SHA,"project_binding_qualified":false,"collider_alignment_qualified":false,"actual_contact_qualified":false,"application_adopted":false}
