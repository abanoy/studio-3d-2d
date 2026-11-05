extends RefCounted
# Camera focus only. Reuses the standard shape decoder and skin palette;
# never evaluates or changes the document's authored poses.
const Shape=preload("res://src/source_shape.gd")
const Bounds=preload("res://src/pose_bounds.gd")

static func skinned(point: Vector3,vertex: int,arrays: Array,palette: Array,context: Dictionary) -> Vector3:
	if palette.is_empty():return point
	var joints=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
	var count: int=arrays[Mesh.ARRAY_VERTEX].size()
	var stride:=int(joints.size()/count) if joints is PackedInt32Array and count>0 else 0
	if stride not in [4,8] or not weights is PackedFloat32Array or weights.size()!=joints.size() or joints.size()!=count*stride:context.error="Unsupported comparison skin weights.";return Vector3.ZERO
	var result:=Vector3.ZERO;var total:=0.
	for j in range(stride):
		var weight: float=weights[vertex*stride+j];var bind: int=joints[vertex*stride+j]
		if not is_finite(weight) or weight<0:context.error="Invalid comparison skin weights.";return Vector3.ZERO
		if weight==0:continue
		if bind<0 or bind>=palette.size():context.error="Missing comparison skin joint.";return Vector3.ZERO
		result+=(palette[bind]*point)*weight;total+=weight
	if absf(total-1.)>.001:context.error="Unnormalized comparison skin weights."
	return result

static func query(row: Dictionary,target: int,amount: float) -> Dictionary:
	var mesh: MeshInstance3D=row.mesh;var context:={"palettes":{},"updated":{},"error":""}
	var palette:=Bounds.palette(mesh,context)
	if not context.error.is_empty():return context
	var weights: Array=row.weights.duplicate();weights.fill(0.);weights[target]=1.
	var epsilon:=maxf(mesh.mesh.get_aabb().size.length()*1e-6,1e-10)
	var bounds:=AABB();var found:=false;var moved:=0;var vertices:=0
	for surface in range(mesh.mesh.get_surface_count()):
		var arrays: Array=mesh.mesh.surface_get_arrays(surface);vertices+=arrays[Mesh.ARRAY_VERTEX].size()
		if vertices>Bounds.VERTEX_BUDGET:return {"error":"This comparison exceeds the 200,000 vertex focus budget."}
		var raw:=Shape.dynamic_surface(row,surface,weights)
		if raw.has("error"):return raw
		var base: PackedVector3Array=raw.base;var positions: PackedVector3Array=raw.targets[target]
		for i in range(base.size()):
			var delta: Vector3=positions[i]-base[i] if mesh.mesh.blend_shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED else positions[i]
			if delta.length_squared()<=epsilon*epsilon:continue
			moved+=1
			for local in [base[i],base[i]+delta*amount]:
				var point: Vector3=mesh.global_transform*skinned(local,i,arrays,palette,context)
				if not context.error.is_empty():return context
				if not point.is_finite():return {"error":"Invalid comparison focus geometry."}
				bounds=bounds.expand(point) if found else AABB(point,Vector3.ZERO);found=true
	if not found:return {"error":"No measured positional change in this control. Other native effects are not evaluated here."}
	return {"bounds":bounds.grow(maxf(bounds.size.length()*.2,.002)),"moved":moved,"vertices":vertices,"error":""}
