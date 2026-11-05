extends RefCounted
# Distance-based trailing pointer in canvas pixels. No clock, image or project state.
var distance:=0.0
var raw:=Vector2.ZERO
var position:=Vector2.ZERO
var begun:=false
func reset(point: Vector2) -> Vector2:
	if not point.is_finite():return position
	raw=point;position=point;begun=true;return position
func sample(point: Vector2) -> Vector2:
	if not point.is_finite():return position
	if not begun:return reset(point)
	raw=point
	var amount:=clampf(distance,0,32) if is_finite(distance) else 0.0
	var length:=position.distance_to(point)
	if amount==0:position=point
	elif length>amount:position=point+(position-point)*(amount/length)
	return position
