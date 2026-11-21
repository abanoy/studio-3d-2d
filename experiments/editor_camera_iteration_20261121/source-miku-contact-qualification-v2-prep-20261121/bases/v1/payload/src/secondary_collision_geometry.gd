extends RefCounted
# Pure measurement, not a collision response or a shader/GLTF binding oracle.
const TOLERANCE = 0.00005
static func finite_nonnegative(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value>=0.0 and value<=100000.0
static func bounded_point(value: Variant) -> bool:
	return value is Vector3 and value.is_finite() and absf(value.x)<=100000.0 and absf(value.y)<=100000.0 and absf(value.z)<=100000.0
static func point_segment(point: Vector3, a: Vector3, b: Vector3) -> float:
	var ab := b-a
	if ab.length_squared()==0.0: return point.distance_to(a)
	return point.distance_to(a+ab*clampf((point-a).dot(ab)/ab.length_squared(),0.0,1.0))
static func segment_segment(a: Vector3,b: Vector3,c: Vector3,d: Vector3) -> float:
	var u := b-a; var v := d-c; var r := a-c
	var uu := u.dot(u); var vv := v.dot(v); var uv := u.dot(v)
	var ur := u.dot(r); var vr := v.dot(r)
	var s := 0.0; var t := 0.0
	if uu<=1e-18 and vv<=1e-18: return a.distance_to(c)
	if uu<=1e-18: t=clampf(vr/vv,0.0,1.0)
	elif vv<=1e-18: s=clampf(-ur/uu,0.0,1.0)
	else:
		var determinant := uu*vv-uv*uv
		if determinant>1e-18: s=clampf((uv*vr-ur*vv)/determinant,0.0,1.0)
		t=(uv*s+vr)/vv
		if t<0.0: t=0.0; s=clampf(-ur/uu,0.0,1.0)
		elif t>1.0: t=1.0; s=clampf((uv-ur)/uu,0.0,1.0)
	return (a+u*s).distance_to(c+v*t)

# Caller must supply genuinely bound current worldJoint*sourceInverseBind
# matrices, calibrated against the imported rest frame. No implicit rest/basis
# repair, weight normalization, shader-equivalence or nearest correspondence.
static func skin_vertex(position: Vector3, indices: Array, weights: Array, matrices: Array) -> Dictionary:
	if not bounded_point(position) or indices.size()!=4 or weights.size()!=4 or matrices.is_empty() or matrices.size()>512: return {"error":"bounded_exact_skin_row_required"}
	var total := 0.0; var point := Vector3.ZERO
	for i in range(4):
		var index: Variant=indices[i]; var weight: Variant=weights[i]
		if not index is int or index<0 or index>=matrices.size() or not finite_nonnegative(weight) or weight>1.0 or not matrices[index] is Transform3D: return {"error":"invalid_skin_weight_or_binding"}
		var matrix: Transform3D=matrices[index]
		if not bounded_point(matrix.origin) or not bounded_point(matrix.basis.x) or not bounded_point(matrix.basis.y) or not bounded_point(matrix.basis.z): return {"error":"nonfinite_skin_frame"}
		total+=float(weight)
		point+=(matrix*position)*float(weight)
	if absf(total-1.0)>0.00002 or not point.is_finite(): return {"error":"skin_weights_or_output_invalid"}
	return {"point":point,"normalization_applied":false}

static func measure(pivots: Array, radii: Array, vertices: Array, capsules: Array) -> Dictionary:
	if pivots.is_empty() or pivots.size()>513 or radii.size()!=pivots.size() or vertices.is_empty() or vertices.size()>20000 or capsules.is_empty() or capsules.size()>2: return {"error":"bounded_nonempty_geometry_required"}
	for i in range(pivots.size()):
		if not bounded_point(pivots[i]) or not finite_nonnegative(radii[i]): return {"error":"invalid_chain_geometry"}
	for vertex in vertices:
		if not bounded_point(vertex): return {"error":"invalid_deformed_vertex"}
	for capsule in capsules:
		if not capsule is Dictionary or capsule.size()!=3 or not capsule.has("start") or not capsule.has("finish") or not capsule.has("radius") or not bounded_point(capsule.start) or not bounded_point(capsule.finish) or not finite_nonnegative(capsule.radius): return {"error":"exact_world_capsule_required"}
	var result := {"format":"has_independent_chain_and_skin_capsule_clearance_1",
		"pivots":pivots.size(),"segments":maxi(0,pivots.size()-1),"vertices":vertices.size(),"colliders":capsules.size(),
		"minimum_particle_clearance":INF,"minimum_segment_clearance":INF,"minimum_skin_vertex_clearance":INF,
		"penetrating_particles":0,"penetrating_segments":0,"penetrating_skin_vertices":0,
		"clearance_tolerance":TOLERANCE,"body_triangle_contact_qualified":false,"swept_contact_qualified":false,
		"skin_shader_binding_qualified":false,"application_adopted":false}
	for capsule in capsules:
		for i in range(pivots.size()):
			var gap: float=point_segment(pivots[i],capsule.start,capsule.finish)-float(radii[i])-float(capsule.radius)
			result.minimum_particle_clearance=minf(result.minimum_particle_clearance,gap)
			if gap < -TOLERANCE: result.penetrating_particles+=1
		for i in range(pivots.size()-1):
			# A max-radius segment envelope is conservative; it is a measurement,
			# not a claim the engine collides whole strands using this envelope.
			var gap: float=segment_segment(pivots[i],pivots[i+1],capsule.start,capsule.finish)-maxf(float(radii[i]),float(radii[i+1]))-float(capsule.radius)
			result.minimum_segment_clearance=minf(result.minimum_segment_clearance,gap)
			if gap < -TOLERANCE: result.penetrating_segments+=1
		for vertex in vertices:
			var gap: float=point_segment(vertex,capsule.start,capsule.finish)-float(capsule.radius)
			result.minimum_skin_vertex_clearance=minf(result.minimum_skin_vertex_clearance,gap)
			if gap < -TOLERANCE: result.penetrating_skin_vertices+=1
	if pivots.size()==1: result.minimum_segment_clearance=null
	return result
