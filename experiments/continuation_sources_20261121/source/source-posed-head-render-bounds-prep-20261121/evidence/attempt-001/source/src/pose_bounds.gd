extends RefCounted
# On-demand view query only. Bind bounds used by import placement stay separate.
const Shape=preload("res://src/source_shape.gd")
const VERTEX_BUDGET:=200000
const FINAL_META:="has_live_frame_pose_1"

static func final_pose(skeleton: Skeleton3D) -> Array:
	var state=skeleton.get_meta(FINAL_META,{})
	if not state is Dictionary or not state.get("owner") is WeakRef or not is_instance_valid(state.owner.get_ref()):return []
	var poses=state.get("poses",[])
	if not poses is Array or poses.size()!=skeleton.get_bone_count():return []
	for pose in poses:
		if not pose is Transform3D:return []
	return poses

static func clear_final(skeleton,owner) -> void:
	# Teardown can run after the owning scene freed either node. Typed arguments
	# would reject freed instances before this validity guard could run.
	if not is_instance_valid(skeleton):return
	var state=skeleton.get_meta(FINAL_META,{})
	if state is Dictionary and state.get("owner") is WeakRef:
		var provider=state.owner.get_ref()
		if not is_instance_valid(provider) or (is_instance_valid(owner) and provider==owner):skeleton.remove_meta(FINAL_META)

static func finite(bounds: AABB) -> bool:
	return bounds.position.is_finite() and bounds.size.is_finite() and (bounds.position+bounds.size).is_finite()

static func include(context: Dictionary,bounds: AABB) -> void:
	if not finite(bounds):context.error="This model has non-finite framing geometry.";return
	context.bounds=context.bounds.merge(bounds) if context.found else bounds
	context.found=true

static func palette(mesh: MeshInstance3D,context: Dictionary) -> Array:
	var sk=mesh.get_node_or_null(mesh.skeleton)
	if not sk is Skeleton3D:return []
	var weighted:=false
	for surface in range(mesh.mesh.get_surface_count()):weighted=weighted or bool(mesh.mesh.surface_get_format(surface)&Mesh.ARRAY_FORMAT_BONES)
	if not weighted:return []
	var skin: Skin=mesh.skin
	if skin==null and mesh.get_skin_reference()==null:return []
	var key: String=str(sk.get_instance_id())+"/"+(str(skin.get_instance_id()) if skin else "default")
	if context.palettes.has(key):return context.palettes[key]
	if skin==null:skin=sk.create_skin_from_rest_transforms()
	var poses:=final_pose(sk)
	if poses.is_empty() and not context.updated.has(sk):sk.force_update_all_bone_transforms();context.updated[sk]=true
	var count:=skin.get_bind_count()
	if count>512:context.error="This skin exceeds the supported framing bone count.";return []
	var result: Array[Transform3D]=[]
	for i in range(count):
		var name:=skin.get_bind_name(i)
		var bone: int=sk.find_bone(name) if not name.is_empty() else skin.get_bind_bone(i)
		if bone<0 or bone>=sk.get_bone_count():context.error="Some joints in this model cannot be read for framing.";return []
		var transform: Transform3D=poses[bone] if not poses.is_empty() else sk.get_bone_global_pose(bone)
		result.append(transform*skin.get_bind_pose(i))
	context.palettes[key]=result
	return result

static func conservative(mesh: MeshInstance3D,transforms: Array,context: Dictionary) -> void:
	var base:=Shape.mesh_bounds(mesh)
	include(context,mesh.global_transform*base)
	if not transforms.is_empty():
		for transform in transforms:include(context,mesh.global_transform*transform*base)
	context.conservative+=1

static func mesh_bounds(mesh: MeshInstance3D,context: Dictionary) -> void:
	var transforms:=palette(mesh,context)
	if not context.error.is_empty():return
	var shaped:=mesh.has_meta("has_animated_shape_weights")
	if transforms.is_empty() and not shaped:
		include(context,mesh.global_transform*Shape.mesh_bounds(mesh));return
	var count:=0
	for surface in range(mesh.mesh.get_surface_count()):count+=mesh.mesh.surface_get_array_len(surface)
	if count>context.remaining:
		conservative(mesh,transforms,context);return
	context.remaining-=count;context.vertices+=count
	var bounds:=AABB();var found:=false
	for surface in range(mesh.mesh.get_surface_count()):
		var arrays: Array=mesh.mesh.surface_get_arrays(surface)
		if arrays.size()!=Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array:
			context.error="This mesh does not expose valid framing vertices.";return
		var positions:=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
		var joints=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
		var skinning: bool=not transforms.is_empty() and joints is PackedInt32Array and not joints.is_empty()
		var stride:=int(joints.size()/positions.size()) if skinning and not positions.is_empty() else 0
		if skinning and (stride not in [4,8] or not weights is PackedFloat32Array or weights.size()!=joints.size() or joints.size()!=positions.size()*stride):
			context.error="This mesh has invalid skin weights for framing.";return
		for i in range(positions.size()):
			var point: Vector3=positions[i]
			if skinning:
				var skinned:=Vector3.ZERO;var total:=0.
				for j in range(stride):
					var weight: float=weights[i*stride+j];var bind: int=joints[i*stride+j]
					if not is_finite(weight) or weight<0:context.error="This mesh has invalid skin weights for framing.";return
					if weight==0:continue
					if bind<0 or bind>=transforms.size():context.error="This mesh references a missing framing joint.";return
					skinned+=(transforms[bind]*point)*weight;total+=weight
				if absf(total-1.)>.001:context.error="This mesh has unnormalized skin weights for framing.";return
				point=skinned
			point=mesh.global_transform*point
			if not point.is_finite():context.error="This model has non-finite framing geometry.";return
			if not found:bounds=AABB(point,Vector3.ZERO);found=true
			else:bounds=bounds.expand(point)
	if found:include(context,bounds)

static func query(node: Node,vertex_budget:=VERTEX_BUDGET) -> Dictionary:
	var context:={"bounds":AABB(),"found":false,"vertices":0,"conservative":0,"remaining":maxi(0,vertex_budget),"error":"","palettes":{},"updated":{}}
	var queue: Array=[node] if node!=null else [];var visited:=0
	while not queue.is_empty() and context.error.is_empty():
		var current: Node=queue.pop_back();visited+=1
		if visited>100000:context.error="The scene hierarchy exceeds the framing limit.";break
		if current is MeshInstance3D and current.mesh:mesh_bounds(current,context)
		queue.append_array(current.get_children())
	context.erase("palettes");context.erase("updated");context.erase("remaining")
	if not context.found and context.error.is_empty():context.error="No mesh geometry to frame."
	return context
