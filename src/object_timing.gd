extends RefCounted
const Clips=preload("res://src/animation_clips.gd")
# First structural timeline operation: move an object's complete authored take.
# Presence and all pose/root keys travel together; source geometry remains immutable.
static func span(data: Dictionary) -> Vector2i:
	var first:=int(data.get("start_frame",0));var last:=first
	for key in data.pose_keys:
		first=mini(first,int(key.frame));last=maxi(last,int(key.frame))
	if Clips.has_pieces(data):
		for piece in data.animation_clips:first=mini(first,int(piece.start));last=maxi(last,int(piece.start)+int(piece.length)-1)
	return Vector2i(first,last)

static func clamp_delta(data: Dictionary, delta: int, duration: int) -> int:
	var bounds:=span(data)
	return clampi(delta,-bounds.x,duration-bounds.y)

static func move(data: Dictionary, delta: int, duration: int) -> Dictionary:
	var result:=data.duplicate(true)
	delta=clamp_delta(data,delta,duration)
	result.start_frame=int(result.start_frame)+delta
	for key in result.pose_keys:key.frame=int(key.frame)+delta
	if Clips.has_pieces(result):
		for piece in result.animation_clips:piece.start=int(piece.start)+delta
	# Draft is an editing address, not a separate animation or lifetime boundary.
	result.draft_frame=clampi(int(result.draft_frame)+delta,0,duration)
	if result.has("shape_draft_frame"):result.shape_draft_frame=clampi(int(result.shape_draft_frame)+delta,0,duration)
	for node in result.get("shape_starts",{}):
		for index in result.shape_starts[node]:result.shape_starts[node][index]=clampi(int(result.shape_starts[node][index])+delta,0,duration)
	for id in result.get("body_starts",{}):result.body_starts[id]=clampi(int(result.body_starts[id])+delta,0,duration)
	return result
