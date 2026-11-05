extends RefCounted
# Exact visible static triangle geometry. No guessed bounds or physics proxies.
const Shape=preload("res://src/source_shape.gd")
const BUDGET:=200000

static func collect(root: Node3D) -> Dictionary:
	var triangles: Array=[];var count:=0
	var meshes: Array=root.find_children("*","MeshInstance3D",true,false)
	if root is MeshInstance3D:meshes.push_front(root)
	for mesh: MeshInstance3D in meshes:
		if not mesh.mesh or not mesh.is_visible_in_tree():continue
		if mesh.skin!=null:return {"error":"This map has skinned geometry. Keep its size or use the model controls."}
		for surface in range(mesh.mesh.get_surface_count()):
			if mesh.mesh.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES:continue
			var arrays: Array=mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
			var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] is PackedInt32Array else PackedInt32Array()
			var size: int=vertices.size() if indices.is_empty() else indices.size()
			count+=size/3
			if count>BUDGET:return {"error":"This map exceeds the 200,000-triangle measuring budget. Its size stays unchanged."}
			for i in range(0,size-2,3):
				var a: Vector3=mesh.global_transform*vertices[i if indices.is_empty() else indices[i]]
				var b: Vector3=mesh.global_transform*vertices[i+1 if indices.is_empty() else indices[i+1]]
				var c: Vector3=mesh.global_transform*vertices[i+2 if indices.is_empty() else indices[i+2]]
				if not a.is_finite() or not b.is_finite() or not c.is_finite():return {"error":"This map has invalid measuring geometry."}
				triangles.append([a,b,c])
	return {"error":"No visible triangle surfaces to measure." if triangles.is_empty() else "","triangles":triangles}

static func pick(triangles: Array,camera: Camera3D,point: Vector2) -> Variant:
	var origin:=camera.project_ray_origin(point);var direction:=camera.project_ray_normal(point)
	var closest: Variant=null;var distance:=INF
	for triangle in triangles:
		var hit: Variant=Geometry3D.ray_intersects_triangle(origin,direction,triangle[0],triangle[1],triangle[2])
		if hit==null:continue
		var depth: float=-camera.to_local(hit).z
		if depth<camera.near or depth>camera.far:continue
		var length: float=origin.distance_squared_to(hit)
		if length<distance:distance=length;closest=hit
	return closest

static func fit(data: Dictionary,points: Array,target: float) -> Dictionary:
	if points.size()!=2 or not is_finite(target) or target<.1 or target>100:return {"error":"Mark two surfaces and enter a known distance between 0.1 and 100 metres."}
	var distance: float=points[0].distance_to(points[1])
	if not is_finite(distance) or distance<.0001:return {"error":"The marked points are too close. Pick them again."}
	var factor:=target/distance;var scale: float=(Vector3.ONE*(float(data.scale)*factor)).x
	if not preload("res://src/model.gd").scale_valid(scale):return {"error":"The resulting map scale is outside Studio's supported range."}
	# Scale about the first marked point: the chosen floor/base stays in place.
	var position: Vector3=points[0]+(preload("res://src/timeline.gd").vector(data.position)-points[0])*factor
	if not position.is_finite() or maxf(absf(position.x),maxf(absf(position.y),absf(position.z)))>100000:return {"error":"The resulting map position is outside Studio's supported range."}
	var value:=data.duplicate(true);value.scale=scale;value.position=[position.x,position.y,position.z]
	var decimal=func(x):return JSON.stringify(float(x),"",true,true)
	value.metadata["map_reference"]={"format":"studio_map_reference_1","source_sha256":data.sha256,"original_scale":decimal.call(data.scale),"original_position":data.position.map(decimal),"measured_distance":decimal.call(distance),"target_metres":decimal.call(target),"points":points.map(func(p):return [decimal.call(p.x),decimal.call(p.y),decimal.call(p.z)]),"scale_float32_hex":PackedFloat32Array([scale]).to_byte_array().hex_encode()}
	return {"error":"","data":value,"factor":factor,"distance":distance}
