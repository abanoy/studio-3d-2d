extends RefCounted
# Only suppress proxy shapes that already overlap on nearby connected body parts.
# Other models, maps and later contacts between distant limbs stay collidable.

static func nearby(actor: RefCounted, a: String, b: String) -> bool:
	var ancestors:={};var at:=a
	for distance in range(5):
		if at=="@root":break
		ancestors[at]=distance;at=actor.parent_id(at)
	at=b
	for distance in range(5):
		if at=="@root":break
		if ancestors.has(at):return ancestors[at]+distance<=4
		at=actor.parent_id(at)
	return false

static func overlapping_boxes(a: CollisionShape3D,b: CollisionShape3D) -> bool:
	if not a.shape is BoxShape3D or not b.shape is BoxShape3D:return false
	var ta:=a.global_transform;var tb:=b.global_transform
	var half_a: Vector3=a.shape.size*0.5;var half_b: Vector3=b.shape.size*0.5
	var aa: Array[Vector3]=[ta.basis.x,ta.basis.y,ta.basis.z]
	var bb: Array[Vector3]=[tb.basis.x,tb.basis.y,tb.basis.z]
	var axes: Array[Vector3]=aa.duplicate();axes.append_array(bb)
	for x in aa:
		for y in bb:
			var axis:=x.cross(y)
			if axis.length_squared()>0.0000000001:axes.append(axis)
	var delta:=tb.origin-ta.origin
	for axis in axes:
		var ra:=0.0;var rb:=0.0
		for i in range(3):ra+=half_a[i]*absf(axis.dot(aa[i]));rb+=half_b[i]*absf(axis.dot(bb[i]))
		# Touching alone is not an overlap requiring a permanent exception.
		if absf(delta.dot(axis))>=ra+rb-0.00001*axis.length():return false
	return true

static func segment(shape: CollisionShape3D) -> Array[Vector3]:
	var half: float=maxf(0.0,shape.shape.height*0.5-shape.shape.radius) if shape.shape is CapsuleShape3D else 0.0
	return [shape.global_transform*Vector3(0,-half,0),shape.global_transform*Vector3(0,half,0)]

static func point_box_distance(point: Vector3,half: Vector3) -> float:
	return (point-point.clamp(-half,half)).length_squared()

static func round_box(round_shape: CollisionShape3D,box: CollisionShape3D) -> bool:
	var ends:=segment(round_shape);var inverse:=box.global_transform.affine_inverse()
	var start: Vector3=inverse*ends[0];var direction: Vector3=inverse*ends[1]-start;var half: Vector3=box.shape.size*0.5
	# Distance from a capsule segment to an oriented box is piecewise quadratic.
	# Break at box faces, then minimize each quadratic interval analytically.
	var breaks: Array[float]=[0.0,1.0]
	for i in range(3):
		if absf(direction[i])<0.00000001:continue
		for side in [-1.0,1.0]:
			var t: float=(side*half[i]-start[i])/direction[i]
			if t>0 and t<1:breaks.append(t)
	breaks.sort()
	var closest:=INF
	for i in range(breaks.size()-1):
		var lo: float=breaks[i];var hi: float=breaks[i+1];var middle: Vector3=start+direction*((lo+hi)*0.5)
		var aa:=0.0;var bb:=0.0
		for j in range(3):
			if absf(middle[j])<=half[j]:continue
			aa+=direction[j]*direction[j];bb+=direction[j]*(start[j]-signf(middle[j])*half[j])
		var t:=clampf(-bb/aa,lo,hi) if aa>0.0000000001 else lo
		closest=minf(closest,point_box_distance(start+direction*t,half))
	var radius: float=maxf(0.0,round_shape.shape.radius-0.00001)
	return closest<radius*radius

static func overlapping(a: CollisionShape3D,b: CollisionShape3D) -> bool:
	var box_a: bool=a.shape is BoxShape3D;var box_b: bool=b.shape is BoxShape3D
	if box_a and box_b:return overlapping_boxes(a,b)
	var round_a: bool=a.shape is SphereShape3D or a.shape is CapsuleShape3D
	var round_b: bool=b.shape is SphereShape3D or b.shape is CapsuleShape3D
	if box_a and round_b:return round_box(b,a)
	if box_b and round_a:return round_box(a,b)
	if not round_a or not round_b:return false
	var sa:=segment(a);var sb:=segment(b)
	var points:=Geometry3D.get_closest_points_between_segments(sa[0],sa[1],sb[0],sb[1])
	var radius: float=maxf(0.0,a.shape.radius+b.shape.radius-0.00001)
	return points[0].distance_squared_to(points[1])<radius*radius

static func apply(actor: RefCounted,bodies: Dictionary) -> Array:
	var result: Array=[];var ids: Array=bodies.keys()
	for i in range(ids.size()):
		for j in range(i+1,ids.size()):
			var a: String=ids[i];var b: String=ids[j]
			if actor.parent_id(a)==b or actor.parent_id(b)==a:continue
			if not nearby(actor,a,b) or not overlapping(bodies[a].get_child(0),bodies[b].get_child(0)):continue
			bodies[a].add_collision_exception_with(bodies[b]);result.append([a,b])
	return result
