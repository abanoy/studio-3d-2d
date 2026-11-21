extends RefCounted
# Personal editor geometry only; no model data, expressions or project fields.
static func available(host: Vector2i) -> Vector2i:
	return Vector2i(maxi(1,host.x-32),maxi(1,host.y-64))
static func minimum(host: Vector2i) -> Vector2i:
	var room:=available(host)
	return Vector2i(mini(380,room.x),mini(320,room.y))
static func opening_size(host: Vector2i,remembered:=Vector2i.ZERO) -> Vector2i:
	var wanted:=remembered
	if wanted.x<=0 or wanted.y<=0:
		wanted=Vector2i(clampi(roundi(host.x*.24),480,680),clampi(roundi(host.y*.78),520,900))
	var room:=available(host);var low:=minimum(host)
	return Vector2i(clampi(wanted.x,low.x,room.x),clampi(wanted.y,low.y,room.y))
static func position(host: Vector2i,extent: Vector2i) -> Vector2i:
	return Vector2i(maxi(0,host.x-extent.x-16),clampi(80,0,maxi(0,host.y-extent.y-28)))
