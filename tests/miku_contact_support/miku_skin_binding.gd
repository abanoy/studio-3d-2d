extends RefCounted
# Root-only exact-source calibration. Private geometry stays in RAM.
const Weights=preload("res://tests/miku_contact_support/godot_skin_weight_conversion.gd")
const Probe=preload("res://tests/miku_contact_support/secondary_collision_probe.gd")
const Binder=preload("res://tests/miku_contact_support/miku_collider_binding.gd")
const Geometry=preload("res://tests/miku_contact_support/secondary_collision_geometry.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
const ALIGNMENT_SHA="6ebf7e4793550a14a29ae569afaeb863cc458582aa07398fa5218948c89b2b7c"
const CALIBRATION_TOLERANCE:=0.00001
static func sha(raw: PackedByteArray) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(raw);return hash.finish().hex_encode()
static func numbers(value,count: int) -> bool:
	if not value is Array or value.size()!=count:return false
	for item in value:
		if not (item is int or item is float) or not is_finite(float(item)) or absf(float(item))>100000.:return false
	return true
static func matrix(value) -> Dictionary:
	if not numbers(value,16):return {"error":"finite_affine_matrix_required"}
	for pair in [[3,0.],[7,0.],[11,0.],[15,1.]]:
		if absf(float(value[pair[0]])-float(pair[1]))>0.000001:return {"error":"source_matrix_not_affine"}
	var transform:=Transform3D(Basis(Vector3(value[0],value[1],value[2]),Vector3(value[4],value[5],value[6]),Vector3(value[8],value[9],value[10])),Vector3(value[12],value[13],value[14]))
	if absf(transform.basis.determinant())<0.000000000001:return {"error":"singular_source_matrix"}
	return {"transform":transform}
static func difference(a: Transform3D,b: Transform3D) -> float:
	return maxf(a.origin.distance_to(b.origin),maxf(a.basis.x.distance_to(b.basis.x),maxf(a.basis.y.distance_to(b.basis.y),a.basis.z.distance_to(b.basis.z))))
static func glb(raw: PackedByteArray) -> Dictionary:
	if raw.size()<28 or raw.size()>134217728 or raw.decode_u32(0)!=0x46546c67 or raw.decode_u32(4)!=2 or raw.decode_u32(8)!=raw.size():return {"error":"exact_bounded_glb_required"}
	var count:=raw.decode_u32(12)
	if count<2 or count>16777216 or count%4 or 20+count+8>raw.size() or raw.decode_u32(16)!=0x4e4f534a:return {"error":"bounded_json_chunk_required"}
	var at:=20+count;var length:=raw.decode_u32(at)
	if raw.decode_u32(at+4)!=0x004e4942 or length%4 or at+8+length!=raw.size():return {"error":"exact_binary_chunk_required"}
	var parser:=JSON.new()
	if parser.parse(raw.slice(20,20+count).get_string_from_utf8())!=OK or not parser.data is Dictionary:return {"error":"source_json_required"}
	var doc: Dictionary=parser.data
	if not doc.get("nodes") is Array or doc.nodes.is_empty() or doc.nodes.size()>100000 or not doc.get("buffers") is Array or doc.buffers.size()!=1:return {"error":"bounded_source_graph_required"}
	if doc.buffers[0].has("uri") or not Binder.whole(doc.buffers[0].get("byteLength"),0,length):return {"error":"embedded_source_buffer_required"}
	return {"doc":doc,"binary":raw.slice(at+8,at+8+length)}
static func joint_component(value) -> Dictionary:
	# Godot JSON stores structural numbers as floats. Admit only exact unsigned
	# glTF enum values; never truncate bools, fractions, signed or other profiles.
	if not Binder.whole(value,5121,5123):return {"error":"unsigned_source_joint_indices_required"}
	var component:=int(value)
	if component not in [5121,5123]:return {"error":"unsigned_source_joint_indices_required"}
	return {"component":component}
static func accessor(decoded: Dictionary,index,kind: String,component: int,limit: int) -> Dictionary:
	var doc: Dictionary=decoded.doc
	if not doc.get("accessors") is Array or not Binder.whole(index,0,doc.accessors.size()-1):return {"error":"source_accessor_missing"}
	var row=doc.accessors[int(index)]
	if not row is Dictionary or row.get("type")!=kind or row.get("componentType")!=component or row.has("sparse") or row.get("normalized",false) or not Binder.whole(row.get("count"),1,limit):return {"error":"exact_dense_accessor_profile_required"}
	if not doc.get("bufferViews") is Array or not Binder.whole(row.get("bufferView"),0,doc.bufferViews.size()-1):return {"error":"source_buffer_view_missing"}
	var view=doc.bufferViews[int(row.bufferView)]
	var width: int={"VEC3":3,"VEC4":4,"MAT4":16}.get(kind,0);var bytes: int=4 if component==5126 else 2 if component==5123 else 1 if component==5121 else 0
	if not view is Dictionary or width==0 or bytes==0 or view.get("buffer",0)!=0:return {"error":"exact_accessor_component_required"}
	var stride=view.get("byteStride",width*bytes);var start=view.get("byteOffset",0);var offset=row.get("byteOffset",0);var size=view.get("byteLength")
	if not Binder.whole(stride,width*bytes,252) or not Binder.whole(start,0,decoded.binary.size()) or not Binder.whole(offset,0,decoded.binary.size()) or not Binder.whole(size,0,decoded.binary.size()) or int(stride)%bytes or int(offset)%bytes or int(start)%bytes or int(start)+int(size)>int(doc.buffers[0].byteLength) or int(offset)+(int(row.count)-1)*int(stride)+width*bytes>int(size):return {"error":"bounded_aligned_accessor_required"}
	var rows: Array=[]
	for i in range(int(row.count)):
		var values: Array=[]
		for j in range(width):
			var position: int=int(start)+int(offset)+i*int(stride)+j*bytes
			var value=decoded.binary.decode_float(position) if component==5126 else decoded.binary.decode_u16(position) if component==5123 else int(decoded.binary[position])
			if not is_finite(float(value)) or absf(float(value))>100000.:return {"error":"finite_source_accessor_required"}
			values.append(value)
		rows.append(values)
	return {"rows":rows}
static func local_frame(node: Dictionary) -> Dictionary:
	if node.has("matrix"):return matrix(node.matrix)
	var t=node.get("translation",[0,0,0]);var q=node.get("rotation",[0,0,0,1]);var s=node.get("scale",[1,1,1])
	if not numbers(t,3) or not numbers(q,4) or not numbers(s,3):return {"error":"finite_source_trs_required"}
	var quaternion:=Quaternion(q[0],q[1],q[2],q[3])
	if absf(quaternion.length()-1.)>0.0001:return {"error":"unit_source_quaternion_required"}
	var transform:=Transform3D(Basis(quaternion)*Basis.from_scale(Vector3(s[0],s[1],s[2])),Vector3(t[0],t[1],t[2]))
	if absf(transform.basis.determinant())<0.000000000001:return {"error":"nonsingular_source_trs_required"}
	return {"transform":transform}
static func source_worlds(doc: Dictionary) -> Dictionary:
	var parents: Dictionary={};var local: Array=[];var world: Dictionary={}
	for index in range(doc.nodes.size()):
		if not doc.nodes[index] is Dictionary:return {"error":"source_node_object_required"}
		var frame:=local_frame(doc.nodes[index])
		if frame.has("error"):return frame
		local.append(frame.transform)
		var children=doc.nodes[index].get("children",[])
		if not children is Array:return {"error":"source_children_required"}
		for child in children:
			if not Binder.whole(child,0,doc.nodes.size()-1) or parents.has(int(child)):return {"error":"source_single_parent_required"}
			parents[int(child)]=index
	for index in range(local.size()):
		var chain: Array=[];var seen: Dictionary={};var at:=index
		while at>=0 and not world.has(at):
			if seen.has(at) or chain.size()>512:return {"error":"acyclic_bounded_source_graph_required"}
			seen[at]=true;chain.append(at);at=parents.get(at,-1)
		var frame: Transform3D=world[at] if at>=0 else Transform3D.IDENTITY
		while not chain.is_empty():
			var item: int=chain.pop_back();frame=frame*local[item];world[item]=frame
	return {"world":world}
static func skin_matrices(actor: RefCounted,cache: Dictionary,rest:=false) -> Dictionary:
	var result: Array=[];var updated: Dictionary={}
	for i in range(cache.source_nodes.size()):
		var id: String=cache.source_ids[i];var info: Dictionary=actor.bones[id];var skeleton: Skeleton3D=info.skeleton
		if not rest and not updated.has(skeleton):skeleton.force_update_all_bone_transforms();updated[skeleton]=true
		var frame: Transform3D=skeleton.get_bone_global_rest(info.index) if rest else skeleton.get_bone_global_pose(info.index)
		result.append(skeleton.global_transform*frame*cache.inverse_binds[i])
	return {"matrices":result}
static func runtime_matrices(cache: Dictionary,rest:=false) -> Dictionary:
	var mesh: MeshInstance3D=cache.mesh;var skeleton: Skeleton3D=mesh.get_node_or_null(mesh.skeleton);var skin: Skin=mesh.skin
	if skeleton==null or skin==null:return {"error":"actual_imported_skin_required"}
	var result: Array=[]
	if not rest:skeleton.force_update_all_bone_transforms()
	var final: Array=Bounds.final_pose(skeleton) if not rest else []
	for i in range(skin.get_bind_count()):
		var name: String=skin.get_bind_name(i);var bone: int=skeleton.find_bone(name) if not name.is_empty() else skin.get_bind_bone(i)
		if bone<0 or bone>=skeleton.get_bone_count():return {"error":"actual_imported_bind_missing"}
		var frame: Transform3D=skeleton.get_bone_global_rest(bone) if rest else final[bone] if not final.is_empty() else skeleton.get_bone_global_pose(bone)
		result.append(mesh.global_transform*frame*skin.get_bind_pose(i))
	return {"matrices":result}
static func converted_vertex(position: Vector3,indices: Array,source_weights: Array,readback_weights: Array,matrices: Array) -> Dictionary:
	# Separate from Geometry.skin_vertex's raw-source unit-sum assumption.
	# Exact source-derived readback admits quantization loss, never renormalizes it.
	var expected:=Weights.expected(source_weights)
	if expected.has("error"):return expected
	if not Weights.four(readback_weights) or expected.source_float32_sum<=0. or readback_weights!=expected.readback_float32_weights:return {"error":"exact_positive_converted_weight_row_required"}
	if not Geometry.bounded_point(position) or indices.size()!=4 or matrices.is_empty() or matrices.size()>512:return {"error":"bounded_exact_skin_row_required"}
	var point:=Vector3.ZERO
	for slot in range(4):
		var index=indices[slot]
		if not index is int or index<0 or index>=matrices.size() or not matrices[index] is Transform3D:return {"error":"invalid_skin_weight_or_binding"}
		var frame: Transform3D=matrices[index]
		if not Geometry.bounded_point(frame.origin) or not Geometry.bounded_point(frame.basis.x) or not Geometry.bounded_point(frame.basis.y) or not Geometry.bounded_point(frame.basis.z):return {"error":"nonfinite_skin_frame"}
		point+=(frame*position)*float(readback_weights[slot])
	if not point.is_finite():return {"error":"skin_weights_or_output_invalid"}
	return {"point":point,"normalization_applied":false,"exact_engine_weight_conversion_matched":true,"shader_equivalence_qualified":false}
static func points(actor: RefCounted,cache: Dictionary,rest:=false,all_rows:=false) -> Dictionary:
	var source:=skin_matrices(actor,cache,rest);var imported:=runtime_matrices(cache,rest)
	if imported.has("error"):return imported
	var result: Array=[];var maximum:=0.
	var rows: Array=cache.rows if all_rows else cache.hair
	for row in rows:
		var a:=converted_vertex(row.position,row.indices,row.raw_source_weights,row.weights,source.matrices)
		var b:=converted_vertex(row.imported_position,row.imported_indices,row.raw_source_weights,row.imported_weights,imported.matrices)
		if a.has("error"):return a
		if b.has("error"):return b
		maximum=maxf(maximum,a.point.distance_to(b.point));result.append(a.point)
	return {"vertices":result,"maximum_palette_disagreement":maximum}
static func float32_hex(value: float) -> String:
	var bytes:=PackedByteArray();bytes.resize(4);bytes.encode_float(0,value);return bytes.hex_encode()
static func influence_failure(context: Dictionary) -> Dictionary:
	# One bounded row only, PRIVATE. Never export this object in public_case.
	var failure: Dictionary={"error":"imported_source_influence_weight_differs"}
	for field in ["source_indices","source_weights","source_joint_ids","imported_indices","imported_weights","imported_joint_ids"]:
		if not context.get(field) is Array or context[field].size()!=4:
			failure["private_diagnostic_error"]="exact_four_slot_diagnostic_required";return failure
	for field in ["source_position","imported_position"]:
		if not numbers(context.get(field),3):
			failure["private_diagnostic_error"]="finite_position_diagnostic_required";return failure
	var record: Dictionary={"private_do_not_publish":true,"slot_count":4,"normalization_applied":false,"coordinate_reorder_applied":false,"conversion_hypothesis_verified":false}
	for field in ["primitive","vertex","failed_bone_id","source_position","imported_position","source_indices","source_weights","source_joint_ids","imported_indices","imported_weights","imported_joint_ids","expected_summed_weights","actual_summed_weights","surface_array_format","runtime_bone_slot_count","runtime_weight_slot_count","runtime_influence_stride","runtime_bones_type","runtime_weights_type","runtime_skin_bind_count","runtime_skeleton_bone_count","source_joint_accessor_component","source_weight_accessor_component","source_weight_accessor_normalized","source_vertex_count","runtime_vertex_count","weight_comparison_tolerance"]:
		if context.has(field):
			var value=context[field];record[field]=value.duplicate(true) if value is Array or value is Dictionary else value
	var source_sum:=0.;var imported_sum:=0.;var source_bits: Array=[];var imported_bits: Array=[]
	for slot in range(4):
		var a=context.source_weights[slot];var b=context.imported_weights[slot]
		if not (a is int or a is float) or not (b is int or b is float) or not is_finite(float(a)) or not is_finite(float(b)):
			failure["private_diagnostic_error"]="finite_weight_diagnostic_required";return failure
		source_sum+=float(a);imported_sum+=float(b);source_bits.append(float32_hex(float(a)));imported_bits.append(float32_hex(float(b)))
	record["source_weight_sum"]=source_sum;record["imported_weight_sum"]=imported_sum
	record["source_float32_little_endian_hex"]=source_bits;record["imported_float32_little_endian_hex"]=imported_bits
	var expected: Dictionary=context.get("expected_summed_weights",{});var actual: Dictionary=context.get("actual_summed_weights",{})
	var differences: Array=[];var maximum:=0.;var same:=expected.size()==actual.size()
	for id in expected:
		var present: bool=actual.has(id);same=same and present
		var gap: float=absf(float(expected[id])-float(actual[id])) if present else 0.
		if present:maximum=maxf(maximum,gap)
		differences.append({"joint_id":id,"source_weight":expected[id],"imported_present":present,"imported_weight":actual.get(id),"absolute_gap":gap if present else null})
	record["same_positive_influence_domain"]=same;record["summed_weight_differences"]=differences;record["maximum_common_weight_gap"]=maximum
	failure["private_influence_diagnostic"]=record
	return failure
static func prepare(actor: RefCounted,input: Dictionary,alignment_raw: PackedByteArray) -> Dictionary:
	if not Weights.engine_supported(Engine.get_version_info()):return {"error":"exact_pinned_engine_weight_profile_required"}
	if sha(alignment_raw)!=ALIGNMENT_SHA:return {"error":"exact_private_alignment_required"}
	var alignment=JSON.parse_string(alignment_raw.get_string_from_utf8())
	if not alignment is Dictionary or alignment.get("format")!="has_private_miku_arm_runtime_alignment_1" or alignment.get("source_asset_sha256")!=Probe.MIKU_SHA or alignment.get("source_project_sha256")!=Binder.PROJECT_SHA:return {"error":"alignment_profile_differs"}
	var raw:=FileAccess.get_file_as_bytes(actor.data.source)
	if sha(raw)!=Probe.MIKU_SHA:return {"error":"exact_loaded_miku_bytes_required"}
	var decoded:=glb(raw)
	if decoded.has("error"):return decoded
	var doc: Dictionary=decoded.doc;var worlds:=source_worlds(doc)
	if worlds.has("error"):return worlds
	if not Binder.whole(input.get("source_mesh_node_index"),0,doc.nodes.size()-1) or not doc.get("skins") is Array or not Binder.whole(input.get("source_skin_index"),0,doc.skins.size()-1):return {"error":"private_mesh_skin_missing"}
	var node: Dictionary=doc.nodes[int(input.source_mesh_node_index)]
	if int(node.get("skin",-1))!=int(input.source_skin_index) or not doc.get("meshes") is Array or not Binder.whole(node.get("mesh"),0,doc.meshes.size()-1):return {"error":"source_mesh_skin_disagrees"}
	var skin: Dictionary=doc.skins[int(input.source_skin_index)];var joints=skin.get("joints")
	if not joints is Array or joints.size()!=156:return {"error":"exact_source_skin_inventory_required"}
	var bind:=accessor(decoded,skin.get("inverseBindMatrices"),"MAT4",5126,512)
	if bind.has("error"):return bind
	if bind.rows.size()!=joints.size():return {"error":"source_inverse_bind_count_differs"}
	var source: Dictionary=actor.root.get_meta("has_source_bones",{});var ids: Array=[];var inverse: Array=[];var bridge:=Transform3D.IDENTITY;var maximum_rest_error:=0.
	for i in range(joints.size()):
		if not Binder.whole(joints[i],0,doc.nodes.size()-1):return {"error":"bounded_source_joint_required"}
		var resolved:=Binder._id_for(actor,source,joints[i])
		if resolved.has("error"):return resolved
		var info: Dictionary=actor.bones[resolved.id];var actual: Transform3D=info.skeleton.global_transform*info.skeleton.get_bone_global_rest(info.index)
		var encoded: Transform3D=worlds.world[int(joints[i])]
		if i==0:bridge=actual*encoded.affine_inverse()
		maximum_rest_error=maxf(maximum_rest_error,difference(actual,bridge*encoded))
		var matrix_result:=matrix(bind.rows[i])
		if matrix_result.has("error"):return matrix_result
		if resolved.id in ids:return {"error":"source_skin_joint_alias"}
		ids.append(resolved.id);inverse.append(matrix_result.transform)
	if maximum_rest_error>CALIBRATION_TOLERANCE:return {"error":"all_joint_rest_bridge_calibration_failed","maximum_rest_error":maximum_rest_error}
	if not alignment.get("source_rest_frames") is Array or alignment.source_rest_frames.size()!=2:return {"error":"private_rest_frame_pair_required"}
	for row in alignment.source_rest_frames:
		for pair in [["node_index","source_world_matrix"],["end_node_index","end_source_world_matrix"]]:
			if not row is Dictionary or not Binder.whole(row.get(pair[0]),0,doc.nodes.size()-1):return {"error":"private_source_frame_index_invalid"}
			var expected:=matrix(row.get(pair[1]))
			if expected.has("error"):return expected
			if difference(expected.transform,worlds.world[int(row[pair[0]])])>CALIBRATION_TOLERANCE:return {"error":"private_encoded_frame_calibration_failed"}
	var meshes: Array=[]
	for row in actor.root.get_meta(Shape.META,{}).get("rows",[]):
		if row.node==input.source_mesh_node_index and row.mesh is MeshInstance3D and not row.mesh in meshes:meshes.append(row.mesh)
	if meshes.is_empty():
		var candidates: Array=actor.root.find_children("*","MeshInstance3D",true,false)
		if actor.root is MeshInstance3D:candidates.push_front(actor.root)
		for candidate in candidates:
			if candidate.get_meta(Shape.NODE_META,-1)==input.source_mesh_node_index:meshes.append(candidate)
	if meshes.size()!=1:return {"error":"exact_source_ordinal_mesh_identity_required"}
	var mesh: MeshInstance3D=meshes[0];var primitives=doc.meshes[int(node.mesh)].get("primitives")
	if not primitives is Array or primitives.size()!=17 or mesh.mesh==null or mesh.mesh.get_surface_count()!=17 or mesh.skin==null:return {"error":"exact_seventeen_source_surfaces_required"}
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{});var hair_nodes: Dictionary={}
	if definition.get("chains",[]).size()!=1 or definition.chains[0].joints.size()!=7:return {"error":"exact_saved_hair_chain_required"}
	for i in range(6):
		var joint: Dictionary=definition.chains[0].joints[i]
		if not Binder.whole(joint.get("source_node"),0,doc.nodes.size()-1) or not source.has(int(joint.source_node)) or source[int(joint.source_node)]!=joint.binding.id:return {"error":"exact_hair_source_identity_required"}
		hair_nodes[int(joint.source_node)]=true
	var cache: Dictionary={"source_nodes":joints.duplicate(),"source_ids":ids,"inverse_binds":inverse,"mesh":mesh,"rows":[],"hair":[]}
	var runtime_sk=mesh.get_node_or_null(mesh.skeleton)
	if not runtime_sk is Skeleton3D:return {"error":"actual_mesh_skeleton_required"}
	for pi in range(primitives.size()):
		var primitive=primitives[pi]
		if not primitive is Dictionary or primitive.get("mode",4)!=4 or primitive.has("extensions") or not primitive.get("attributes") is Dictionary:return {"error":"plain_source_triangles_required"}
		var attributes: Dictionary=primitive.attributes
		if attributes.has("JOINTS_1") or attributes.has("WEIGHTS_1"):return {"error":"exact_four_source_weights_required"}
		var position:=accessor(decoded,attributes.get("POSITION"),"VEC3",5126,20000)
		var source_accessor=doc.accessors[int(attributes.get("JOINTS_0",-1))] if Binder.whole(attributes.get("JOINTS_0"),0,doc.accessors.size()-1) else {}
		var component_profile:=joint_component(source_accessor.get("componentType"))
		if component_profile.has("error"):return component_profile
		var joint_rows:=accessor(decoded,attributes.get("JOINTS_0"),"VEC4",component_profile.component,20000)
		var weights:=accessor(decoded,attributes.get("WEIGHTS_0"),"VEC4",5126,20000)
		for result in [position,joint_rows,weights]:
			if result.has("error"):return result
		var arrays: Array=mesh.mesh.surface_get_arrays(pi)
		var vertices: PackedVector3Array=Shape.vertices(mesh,pi,arrays[Mesh.ARRAY_VERTEX]);var runtime_indices=arrays[Mesh.ARRAY_BONES];var runtime_weights=arrays[Mesh.ARRAY_WEIGHTS]
		if vertices.size()!=position.rows.size() or weights.rows.size()!=vertices.size() or joint_rows.rows.size()!=vertices.size() or not runtime_indices is PackedInt32Array or not runtime_weights is PackedFloat32Array or runtime_indices.size()!=vertices.size()*4 or runtime_weights.size()!=runtime_indices.size():return {"error":"exact_imported_vertex_correspondence_required"}
		for vi in range(vertices.size()):
			var raw_position: Array=position.rows[vi];var point:=Vector3(raw_position[0],raw_position[1],raw_position[2])
			if point.distance_to(vertices[vi])>0.000001:return {"error":"nonneutral_or_reordered_vertex_stream"}
			var source_indices: Array=[];var imported_indices: Array=[];var imported_weights: Array=[];var expected_weights: Dictionary={};var actual_weights: Dictionary={};var touched:=false
			var source_slot_ids: Array=[];var imported_slot_ids: Array=[]
			for k in range(4):
				var index=joint_rows.rows[vi][k];var weight: float=weights.rows[vi][k]
				if not Binder.whole(index,0,joints.size()-1) or weight<0. or weight>1.:return {"error":"bounded_source_influence_required"}
				source_indices.append(int(index));source_slot_ids.append(ids[int(index)])
				if weight>0.:
					expected_weights[ids[int(index)]]=float(expected_weights.get(ids[int(index)],0.))+weight;touched=touched or hair_nodes.has(int(joints[int(index)]))
				var actual_index: int=runtime_indices[vi*4+k];var actual_weight: float=runtime_weights[vi*4+k]
				if actual_index<0 or actual_index>=mesh.skin.get_bind_count() or not is_finite(actual_weight) or actual_weight<0. or actual_weight>1.:return {"error":"bounded_runtime_influence_required"}
				imported_indices.append(actual_index);imported_weights.append(actual_weight)
				var name: String=mesh.skin.get_bind_name(actual_index);var bone: int=runtime_sk.find_bone(name) if not name.is_empty() else mesh.skin.get_bind_bone(actual_index)
				if bone<0 or bone>=runtime_sk.get_bone_count():return {"error":"runtime_skin_identity_missing"}
				var actual_id: String=str(actor.root.get_path_to(runtime_sk))+"::"+str(runtime_sk.get_bone_name(bone))
				imported_slot_ids.append(actual_id)
				if actual_weight>0.:actual_weights[actual_id]=float(actual_weights.get(actual_id,0.))+actual_weight
			var conversion:=Weights.assess(weights.rows[vi],imported_weights,source_slot_ids,imported_slot_ids)
			if conversion.has("error"):
				var source_weight_accessor: Dictionary=doc.accessors[int(attributes.WEIGHTS_0)]
				var failure:=influence_failure({"primitive":pi,"vertex":vi,"failed_bone_id":source_slot_ids[int(conversion.get("slot",0))],
					"source_position":[point.x,point.y,point.z],"imported_position":[vertices[vi].x,vertices[vi].y,vertices[vi].z],
					"source_indices":source_indices,"source_weights":weights.rows[vi],"source_joint_ids":source_slot_ids,
					"imported_indices":imported_indices,"imported_weights":imported_weights,"imported_joint_ids":imported_slot_ids,
					"expected_summed_weights":expected_weights,"actual_summed_weights":actual_weights,
					"surface_array_format":mesh.mesh.surface_get_format(pi),"runtime_bone_slot_count":runtime_indices.size(),"runtime_weight_slot_count":runtime_weights.size(),"runtime_influence_stride":4,
					"runtime_bones_type":type_string(typeof(runtime_indices)),"runtime_weights_type":type_string(typeof(runtime_weights)),
					"runtime_skin_bind_count":mesh.skin.get_bind_count(),"runtime_skeleton_bone_count":runtime_sk.get_bone_count(),
					"source_joint_accessor_component":source_accessor.componentType,"source_weight_accessor_component":source_weight_accessor.componentType,"source_weight_accessor_normalized":source_weight_accessor.get("normalized",false),
					"source_vertex_count":position.rows.size(),"runtime_vertex_count":vertices.size(),"weight_comparison_tolerance":0.0})
				failure["error"]=conversion.error;failure["weight_conversion_failure"]=conversion
				failure["pinned_engine_profile_identified"]=true;failure["weight_comparison_tolerance"]=0.0
				return failure
			var row: Dictionary={"position":point,"indices":source_indices,"weights":imported_weights.duplicate(),"raw_source_weights":weights.rows[vi].duplicate(),"normalized_source_weights":conversion.normalized_float32_weights.duplicate(),"packed_uint16_weights":conversion.packed_uint16_weights.duplicate(),"imported_position":vertices[vi],"imported_indices":imported_indices,"imported_weights":imported_weights,"primitive":pi,"vertex":vi}
			cache.rows.append(row)
			if touched:cache.hair.append(row)
	if cache.rows.size()!=13111 or cache.hair.size()!=989:return {"error":"exact_mesh_and_hair_support_count_required"}
	var rest:=points(actor,cache,true,true)
	if rest.has("error"):return rest
	if rest.maximum_palette_disagreement>CALIBRATION_TOLERANCE:return {"error":"source_runtime_rest_skin_calibration_failed","maximum_palette_disagreement":rest.maximum_palette_disagreement}
	var posed:=points(actor,cache,false,true)
	if posed.has("error"):return posed
	if posed.maximum_palette_disagreement>CALIBRATION_TOLERANCE:return {"error":"source_runtime_saved_pose_skin_calibration_failed","maximum_palette_disagreement":posed.maximum_palette_disagreement}
	cache["calibration"]={"source_runtime_identity_resolved":true,"exact_engine_weight_conversion_matched":true,"weight_conversion_profile":Weights.PROFILE,"engine_source_commit":Weights.COMMIT,"raw_source_bit_identity_claimed":false,"source_imported_slot_identity_matched":true,"private_rest_frames_matched":true,"all_joint_rest_bridge_matched":true,"source_imported_surface_identity_matched":true,"exact_source_inverse_bind_palette_matched":true,"skin_shader_equivalence_qualified":false,"joint_count":joints.size(),"vertex_count":cache.rows.size(),"hair_support_count":cache.hair.size(),"maximum_rest_error":maximum_rest_error,"maximum_rest_palette_error":rest.maximum_palette_disagreement,"maximum_saved_palette_error":posed.maximum_palette_disagreement,"calibration_tolerance":CALIBRATION_TOLERANCE}
	return {"cache":cache}
