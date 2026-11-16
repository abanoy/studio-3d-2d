extends RefCounted
# Actual imported arrays/skin palettes, held in memory only. Never serialize the
# returned points into public evidence; publish only counts/errors/hashes.
const Shape = preload("res://src/source_shape.gd")
const Bounds = preload("res://src/pose_bounds.gd")
const Compare = preload("res://src/shape_comparison_bounds.gd")

static func digest(bytes: PackedByteArray) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(bytes)
	return h.finish().hex_encode()

static func capture(actor: RefCounted, leaf_binding: RefCounted) -> Dictionary:
	var points := PackedVector3Array()
	var unaffected := PackedVector3Array()
	var mask := PackedByteArray()
	var meshes: Array = actor.root.find_children("*","MeshInstance3D",true,false)
	if actor.root is MeshInstance3D: meshes.push_front(actor.root)
	var context := {"palettes":{},"updated":{},"error":""}
	var array_hash := HashingContext.new()
	array_hash.start(HashingContext.HASH_SHA256)
	var transforms: Array = []
	var affected_count := 0
	var shared_count := 0
	var surfaces := 0
	for mesh: MeshInstance3D in meshes:
		if mesh.mesh == null: continue
		var skeleton = mesh.get_node_or_null(mesh.skeleton)
		if skeleton != leaf_binding.skeleton or not skeleton is Skeleton3D: return {"error":"Unexpected skin skeleton in exact native leaf profile"}
		if not Bounds.final_pose(skeleton).is_empty(): return {"error":"Foreign final-pose owner must not supply this capture"}
		var skin: Skin = mesh.skin
		if skin == null: return {"error":"Exact native profile requires explicit skin bindings"}
		var slot_bones: Array[int] = []
		for slot in range(skin.get_bind_count()):
			var name: StringName = skin.get_bind_name(slot)
			var index: int = skeleton.find_bone(name) if not name.is_empty() else skin.get_bind_bone(slot)
			if index < 0 or index >= skeleton.get_bone_count(): return {"error":"Invalid actual skin bind"}
			slot_bones.append(index)
		var palette := Bounds.palette(mesh,context)
		if not context.error.is_empty(): return {"error":context.error}
		if palette.size() != slot_bones.size(): return {"error":"Incomplete actual skin palette"}
		transforms.append([str(actor.root.get_path_to(mesh)),mesh.global_transform,mesh.mesh.get_instance_id(),skin.get_instance_id()])
		for surface in range(mesh.mesh.get_surface_count()):
			surfaces += 1
			var arrays: Array = mesh.mesh.surface_get_arrays(surface)
			array_hash.update(var_to_bytes(arrays))
			if arrays.size() != Mesh.ARRAY_MAX or not arrays[Mesh.ARRAY_VERTEX] is PackedVector3Array: return {"error":"Unreadable actual mesh arrays"}
			var vertices := Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			var joints = arrays[Mesh.ARRAY_BONES]
			var weights = arrays[Mesh.ARRAY_WEIGHTS]
			if not joints is PackedInt32Array or not weights is PackedFloat32Array: return {"error":"Unexpected actual skin array types"}
			var stride: int = int(joints.size()/vertices.size()) if not vertices.is_empty() else 0
			if stride not in [4,8] or not joints is PackedInt32Array or not weights is PackedFloat32Array or weights.size() != joints.size() or joints.size() != vertices.size()*stride: return {"error":"Unexpected actual skin influence layout"}
			for vertex in range(vertices.size()):
				if points.size() >= 200000: return {"error":"Actual vertex budget exceeded"}
				var leaf_weight := 0.0
				var other_weight := 0.0
				for j in range(stride):
					var slot: int = joints[vertex*stride+j]
					var weight: float = weights[vertex*stride+j]
					if not is_finite(weight) or weight < 0.0: return {"error":"Invalid actual weight"}
					if weight == 0.0: continue
					if slot < 0 or slot >= slot_bones.size(): return {"error":"Missing actual bind slot"}
					if slot_bones[slot] == leaf_binding.skeleton_bone_index: leaf_weight += weight
					else: other_weight += weight
				var world: Vector3 = mesh.global_transform*Compare.skinned(vertices[vertex],vertex,arrays,palette,context)
				if not context.error.is_empty(): return {"error":context.error}
				if not world.is_finite(): return {"error":"Nonfinite actual weighted point"}
				points.append(world)
				mask.append(1 if leaf_weight > 0.0 else 0)
				if leaf_weight > 0.0:
					affected_count += 1
					if other_weight > 0.0: shared_count += 1
				else: unaffected.append(world)
	return {"points":points,"mask":mask,"vertices":points.size(),"affected":affected_count,"shared":shared_count,"unaffected":unaffected.size(),"surfaces":surfaces,
		"points_sha256":digest(points.to_byte_array()),"unaffected_sha256":digest(unaffected.to_byte_array()),"array_sha256":array_hash.finish().hex_encode(),"mesh_transforms_bytes":var_to_bytes(transforms)}

static func difference(before: Dictionary, after: Dictionary, threshold: float) -> Dictionary:
	if before.has("error"): return before
	if after.has("error"): return after
	if before.vertices != after.vertices or before.mask != after.mask or before.array_sha256 != after.array_sha256 or before.mesh_transforms_bytes != after.mesh_transforms_bytes: return {"error":"Actual geometry/binding/mesh transform changed"}
	var maximum := 0.0
	var affected_max := 0.0
	var unaffected_max := 0.0
	var moved := 0
	for i in range(before.vertices):
		var distance: float = before.points[i].distance_to(after.points[i])
		if not is_finite(distance): return {"error":"Nonfinite actual motion distance"}
		maximum = maxf(maximum,distance)
		if before.mask[i] == 1:
			affected_max = maxf(affected_max,distance)
			if distance > threshold: moved += 1
		else: unaffected_max = maxf(unaffected_max,distance)
	return {"maximum":maximum,"affected_max":affected_max,"unaffected_max":unaffected_max,"affected_vertices_moved":moved,
		"unaffected_exact":before.unaffected_sha256 == after.unaffected_sha256,"all_points_exact":before.points_sha256 == after.points_sha256}
