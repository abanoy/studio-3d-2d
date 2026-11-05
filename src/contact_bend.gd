extends RefCounted
# Capture-time hint only: old contacts and explicitly corrected poles retain their data.
static func hints(legs: Array) -> Array:
	if legs.size()!=2:return []
	var lateral: Vector3=legs[0][0]-legs[1][0]
	var up: Vector3=(legs[0][0]+legs[1][0]-legs[0][2]-legs[1][2])*0.5
	if lateral.length()<0.00001 or up.length()<0.00001:return []
	var forward:=lateral.normalized().cross(up.normalized())
	if forward.length()<0.5:return []
	forward=forward.normalized()
	var result:=[]
	for leg in legs:
		var hip: Vector3=leg[0];var knee: Vector3=leg[1];var ankle: Vector3=leg[2]
		var total:=hip.distance_to(knee)+knee.distance_to(ankle)
		if total<0.00001 or hip.distance_to(ankle)<total*0.5:return []
		var axis: Vector3=(ankle-hip).normalized()
		var bend: Vector3=knee-hip; bend-=axis*bend.dot(axis)
		# A clear authored bend is authoritative. Tiny rest-rig offsets are not
		# enough to decide whether a deeply crouched knee should turn sideways.
		if bend.length()>=total*0.02:result.append(null);continue
		var direction:=forward-axis*forward.dot(axis)
		result.append((hip+ankle)*0.5+direction.normalized()*total if direction.length()>0.5 else null)
	return result
