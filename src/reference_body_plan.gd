extends RefCounted
# Ephemeral geometry only: no nodes, Shape3D resources, authored data or poses
# are changed here. The caller owns source skin/loose-part ownership and joints.
const MAX_BODIES: int = 48
const MIN_WORLD_SCALE: float = 0.001
const MAX_WORLD_SCALE: float = 1000.0
const MAX_WORLD_ORIGIN: float = 100000.0
const MAX_METRE_SPAN: float = 10000.0
const REGULAR_EPS: float = 0.00001
const ERROR: String = "Body Physics cannot safely prepare this reference size. Posing and Hair & clothes are still available."

static func _finite_transform(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.x.is_finite() and value.basis.y.is_finite() and value.basis.z.is_finite()

static func _regular(value: Transform3D) -> bool:
	if not _finite_transform(value) or value.basis.determinant() <= 0.0:
		return false
	var scale: Vector3 = value.basis.get_scale()
	if scale.x < MIN_WORLD_SCALE*(1.0-REGULAR_EPS) or scale.x > MAX_WORLD_SCALE*(1.0+REGULAR_EPS):
		return false
	if absf(scale.x-scale.y) > scale.x*REGULAR_EPS or absf(scale.x-scale.z) > scale.x*REGULAR_EPS:
		return false
	var x: Vector3 = value.basis.x.normalized()
	var y: Vector3 = value.basis.y.normalized()
	var z: Vector3 = value.basis.z.normalized()
	return absf(x.dot(y)) <= REGULAR_EPS and absf(x.dot(z)) <= REGULAR_EPS and absf(y.dot(z)) <= REGULAR_EPS

static func _bounded_origin(value: Vector3) -> bool:
	return value.is_finite() and maxf(absf(value.x),maxf(absf(value.y),absf(value.z))) <= MAX_WORLD_ORIGIN

static func _bounds_in_frame(bounds: AABB, transform: Transform3D) -> Dictionary:
	if not bounds.position.is_finite() or not bounds.size.is_finite() or minf(bounds.size.x,minf(bounds.size.y,bounds.size.z)) < 0.0:
		return {"error":ERROR}
	var minimum: Vector3 = Vector3(INF,INF,INF)
	var maximum: Vector3 = -minimum
	for i in range(8):
		var point: Vector3 = transform*bounds.get_endpoint(i)
		if not point.is_finite() or maxf(absf(point.x),maxf(absf(point.y),absf(point.z))) > MAX_METRE_SPAN:return {"error":ERROR}
		minimum = minimum.min(point)
		maximum = maximum.max(point)
	var span: Vector3 = maximum-minimum
	if not span.is_finite() or span.length() > MAX_METRE_SPAN:return {"error":ERROR}
	return {"bounds":AABB(minimum,span)}

static func build(actor: RefCounted, sk: Skeleton3D, chosen: Array[String], role_ids: Dictionary, weighted_bounds: Dictionary) -> Dictionary:
	if not actor or not is_instance_valid(sk) or not sk.is_inside_tree() or chosen.size() < 3 or chosen.size() > MAX_BODIES or weighted_bounds.size() > MAX_BODIES:
		return {"error":ERROR}
	var skeleton_world: Transform3D = sk.global_transform
	if not _regular(skeleton_world) or not _bounded_origin(skeleton_world.origin):return {"error":ERROR}
	# F retains skeleton axes but removes all scale: its coordinates are metres.
	var frame: Transform3D = skeleton_world.orthonormalized()
	var frame_inverse: Transform3D = frame.affine_inverse()
	var worlds: Dictionary = {}
	var parents: Dictionary = {}
	var minimum: Vector3 = Vector3(INF,INF,INF)
	var maximum: Vector3 = -minimum
	for id in chosen:
		if id.is_empty() or worlds.has(id) or not actor.bones.has(id):return {"error":ERROR}
		var info: Dictionary = actor.bones[id]
		if info.get("skeleton") != sk or not info.get("index") is int:return {"error":ERROR}
		var index: int = info.index
		if index < 0 or index >= sk.get_bone_count():return {"error":ERROR}
		var world: Transform3D = actor.bone_transform(id)
		if not _regular(world) or not _bounded_origin(world.origin):return {"error":ERROR}
		worlds[id] = world
		parents[id] = actor.parent_id(id)
		var point: Vector3 = frame_inverse*world.origin
		minimum = minimum.min(point)
		maximum = maximum.max(point)
	var size: float = maxf((maximum-minimum).length(),0.01)
	if not is_finite(size) or size > MAX_METRE_SPAN:return {"error":ERROR}
	for id in weighted_bounds:
		if not worlds.has(id) or not weighted_bounds[id] is AABB:return {"error":ERROR}
	var result: Dictionary = {}
	for id in chosen:
		var world: Transform3D = worlds[id]
		var unit_world: Transform3D = world.orthonormalized()
		var unit_inverse: Transform3D = unit_world.affine_inverse()
		var direction: Vector3 = Vector3.ZERO
		var nearest: float = INF
		for child in chosen:
			if parents[child] != id:continue
			var child_world: Transform3D = worlds[child]
			var offset: Vector3 = unit_inverse*child_world.origin
			var distance: float = offset.length()
			if distance > 0.0001 and distance < nearest:
				direction = offset
				nearest = distance
		var length: float = direction.length()
		var radius: float = clampf(length*0.16,size*0.012,size*0.045)
		var metric_bounds: AABB = AABB()
		var has_box: bool = false
		if weighted_bounds.has(id):
			var source_bounds: AABB = weighted_bounds[id]
			# Same-origin relative geometry avoids subtracting large world positions.
			var relative: Transform3D = Transform3D(unit_world.basis.transposed()*world.basis,Vector3.ZERO)
			var converted: Dictionary = _bounds_in_frame(source_bounds,relative)
			if converted.has("error"):return converted
			metric_bounds = converted.bounds
			has_box = metric_bounds.size.length() > size*0.005 and metric_bounds.size.length() < size*0.75
		var raw_offset: Transform3D = Transform3D.IDENTITY
		var description: Dictionary
		if has_box:
			var source_bounds: AABB = weighted_bounds[id]
			raw_offset.origin = source_bounds.get_center()
			description = {"kind":"box"}
		elif length > size*0.025:
			# Only orientation/offset use source units. Selection and dimensions use
			# the metre direction above, including locally scaled source bones.
			var raw_direction: Vector3 = world.basis.inverse()*(unit_world.basis*direction)
			if not raw_direction.is_finite() or raw_direction.length_squared() <= 0.0:return {"error":ERROR}
			raw_offset = Transform3D(Basis(Quaternion(Vector3.UP,raw_direction.normalized())),raw_direction*0.45)
			description = {"kind":"capsule","radius":radius,"height":maxf(radius*2.0,length*0.9),"margin":minf(0.005,radius*0.025)}
		else:
			var sphere_radius: float = size*(0.045 if id == role_ids.get("head","") else 0.035)
			description = {"kind":"sphere","radius":sphere_radius,"margin":minf(0.005,sphere_radius*0.025)}
		# W*O is already a unit physical frame; B*O^-1 reconstructs W at rest.
		# The inverse scale in O is intentional and must not be orthonormalized.
		var body_world: Transform3D = (world*raw_offset).orthonormalized()
		var body_offset: Transform3D = world.affine_inverse()*body_world
		if not _finite_transform(body_world) or not _finite_transform(body_offset) or not _bounded_origin(body_world.origin):return {"error":ERROR}
		if has_box:
			var source_bounds: AABB = weighted_bounds[id]
			var body_relative: Transform3D = Transform3D(body_world.basis.transposed()*world.basis,body_world.basis.transposed()*(world.origin-body_world.origin))
			var converted: Dictionary = _bounds_in_frame(source_bounds,body_relative)
			if converted.has("error"):return converted
			var body_bounds: AABB = converted.bounds
			var dimensions: Vector3 = body_bounds.size+Vector3.ONE*size*0.003
			if not dimensions.is_finite() or minf(dimensions.x,minf(dimensions.y,dimensions.z)) <= 0.0:return {"error":ERROR}
			description["size"] = dimensions
			description["margin"] = minf(0.005,minf(dimensions.x,minf(dimensions.y,dimensions.z))*0.025)
		description["body_offset"] = body_offset
		description["world_frame"] = body_world
		description["bone_world"] = world
		description["raw_offset"] = raw_offset
		description["length"] = length
		result[id] = description
	return {"bodies":result,"size":size,"frame":frame}
