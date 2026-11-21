extends RefCounted
# Pure mesh-local conservative envelope. No mesh, source data, or weight edits.
static func finite(box: AABB) -> bool:
	return box.position.is_finite() and box.size.is_finite() and box.end.is_finite() and box.size.x>=0 and box.size.y>=0 and box.size.z>=0

static func transform_finite(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.x.is_finite() and value.basis.y.is_finite() and value.basis.z.is_finite()

static func calculate(base: AABB,transforms: Array,sum_min: float,sum_max: float,include_unskinned: bool) -> Dictionary:
	if not finite(base):return {"error":"Invalid intrinsic render bounds."}
	if transforms.is_empty():
		return {"bounds":base} if include_unskinned else {"error":"No weighted or unskinned render geometry."}
	if not is_finite(sum_min) or not is_finite(sum_max) or sum_min<=0 or sum_max<sum_min:return {"error":"Invalid skin weight-sum interval."}
	var union:=AABB();var first:=true
	for value in transforms:
		if not value is Transform3D or not transform_finite(value):return {"error":"Invalid render skin transform."}
		var current: AABB=value*base
		if not finite(current):return {"error":"Non-finite transformed render bounds."}
		union=current if first else union.merge(current);first=false
	# For nonnegative weights, sum(weight*T(point)) = s*convex_average.
	# The average lies in union; s lies in the cached actual [min,max] interval.
	# Scaling both endpoints and merging encloses the complete interval without
	# assuming exact normalization or adding the distant mesh-local origin.
	var low:=AABB(union.position*sum_min,union.size*sum_min)
	var high:=AABB(union.position*sum_max,union.size*sum_max)
	var result:=low.merge(high)
	if include_unskinned:result=result.merge(base)
	return {"bounds":result} if finite(result) else {"error":"Non-finite weighted render bounds."}

static func padding(native_box: AABB,posed_box: AABB) -> Dictionary:
	if not finite(native_box) or not finite(posed_box):return {"error":"Invalid render padding bounds."}
	var lower: Vector3=native_box.position-posed_box.position
	var upper: Vector3=posed_box.end-native_box.end
	var needed:=maxf(0.,maxf(maxf(lower.x,lower.y),maxf(lower.z,maxf(upper.x,maxf(upper.y,upper.z)))))
	# A relative float guard is local to this computed envelope, not a global
	# size-independent culling box. The chosen engine property needs GPU proof.
	var extent:=maxf(posed_box.size.length(),native_box.size.length())
	var guard:=maxf(0.00001,extent*0.00001)
	var margin:=needed+guard
	return {"margin":margin,"geometric_margin":needed,"guard":guard} if is_finite(margin) else {"error":"Non-finite render padding."}
