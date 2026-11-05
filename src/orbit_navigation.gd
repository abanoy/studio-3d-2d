extends RefCounted
# Temporary editor navigation only; never writes a camera key or model data.
var active:=false
var pivot:=Vector3.ZERO
var action:=""
func begin(camera: Camera3D,point: Vector3,operation: String) -> bool:
	active=false
	if not point.is_finite() or not camera.global_position.is_finite() or operation not in ["orbit","pan","dolly"]:return false
	if camera.global_position.distance_to(point)<maxf(.01,camera.near*2):return false
	pivot=point;action=operation;active=true;return true
func end() -> void:
	active=false;action=""
func motion(camera: Camera3D,relative: Vector2) -> void:
	if not active or not relative.is_finite():return
	var offset:=camera.global_position-pivot;var radius:=offset.length()
	if not is_finite(radius) or radius<.0001:return
	if action=="pan":
		var delta:=(-camera.global_basis.x*relative.x+camera.global_basis.y*relative.y)*radius*.002
		camera.global_position+=delta;pivot+=delta
	elif action=="dolly":
		var distance:=clampf(radius*exp(clampf(relative.y*.01,-1,1)),maxf(.01,camera.near*2),1e12)
		camera.global_position=pivot+offset*(distance/radius)
	else:
		var yaw:=Quaternion(Vector3.UP,-relative.x*.003)
		var pitch:=Quaternion((yaw*camera.global_basis.x).normalized(),clampf(-relative.y*.003,-PI*.45,PI*.45))
		var turn:=pitch*yaw
		# Preserve camera roll and target screen position without a look_at pole.
		# Reject only the pitch component that would cross the vertical limit.
		var initial: Vector3=(yaw*offset).normalized();var candidate: Vector3=(turn*offset).normalized()
		if absf(candidate.y)>.995 or Vector2(initial.x,initial.z).dot(Vector2(candidate.x,candidate.z))<0:turn=yaw
		camera.global_position=pivot+turn*offset
		camera.global_basis=(Basis(turn)*camera.global_basis).orthonormalized()
