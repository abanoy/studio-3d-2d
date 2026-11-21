extends RefCounted
# Opt-in proposal only: common bundle-space transforms, no Skeleton/data writes.
# Compute every goal from the same pre-follow authored snapshot; then solve local
# transforms against already solved parent frames. Never feed the last goal back.
static func finite_frame(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.x.is_finite() and value.basis.y.is_finite() and value.basis.z.is_finite() and is_finite(value.basis.determinant()) and absf(value.basis.determinant())>0.000000000001

static func goal(master_rest: Transform3D,master_posed: Transform3D,target_authored: Transform3D) -> Dictionary:
	if not finite_frame(master_rest) or not finite_frame(master_posed) or not finite_frame(target_authored):return {"error":"Follow needs finite nonsingular frames in one common bundle coordinate space."}
	var desired: Transform3D=master_posed*master_rest.affine_inverse()*target_authored
	return {"world_goal":desired} if finite_frame(desired) else {"error":"Follow goal is not a supported finite frame."}

static func local_goal(solved_parent: Transform3D,desired: Transform3D) -> Dictionary:
	if not finite_frame(solved_parent) or not finite_frame(desired):return {"error":"Follow needs the current solved parent frame."}
	var local: Transform3D=solved_parent.affine_inverse()*desired
	return {"local_goal":local} if finite_frame(local) else {"error":"Follow local result is not a supported finite frame."}
