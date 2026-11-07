extends RefCounted
# Soft owned-hot + decoded-cache target. Legacy/raw fallback/derived/GPU/tile
# storage is outside this counter; never use this as a whole-process RAM bound.
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const DEFAULT_BYTES=64*1024*1024
var target: int
var cache
var releases:=0
var attempts:=0
var _cursor:=0
func _init(bytes: int=DEFAULT_BYTES) -> void:target=clampi(bytes,0,DEFAULT_BYTES)
func install(value) -> void:cache=value if value is Cache else null
func registered() -> Array:
	var result: Array=[];var seen:={}
	if not cache is Cache:return result
	for i in range(cache.owners.size()-1,-1,-1):
		var owner=cache.owners[i].get_ref()
		if owner==null:cache.owners.remove_at(i)
		elif owner is Owner and not seen.has(owner.get_instance_id()):seen[owner.get_instance_id()]=true;result.append(owner)
	return result
func sample() -> Dictionary:
	var hot:=0;var cold:=0;var pinned:=0;var unique:={};var owners:=registered()
	for owner in owners:
		if owner.is_pinned():hot+=owner.decoded_bytes();pinned+=1
		elif owner._cold!=null and not unique.has(owner._cold.get_instance_id()):unique[owner._cold.get_instance_id()]=true;cold+=owner.retained_bytes()
	return {"owners":owners.size(),"hot_owners":pinned,"hot_bytes":hot,"cold_payload_bytes":cold,"decoded_cache_bytes":cache.retained_bytes if cache is Cache else 0,"target_bytes":target}
func step(protected: Array=[],idle:=true) -> Dictionary:
	var before:=sample()
	if not idle:return {"released":false,"reason":"busy","before":before,"after":before}
	if before.hot_bytes+before.decoded_cache_bytes<=target:return {"released":false,"reason":"within_target","before":before,"after":before}
	# At most one full-HD compression attempt per scheduled idle step. Callers
	# decide cadence and protect visible/current work; external Image refs guard
	# remaining live users independently of this list.
	var owners:=registered()
	for offset in range(owners.size()):
		var index:=(_cursor+offset)%owners.size();var owner=owners[index]
		if not owner.is_pinned() or protected.has(owner):continue
		_cursor=(index+1)%owners.size();attempts+=1;var result: Dictionary=owner.cool()
		if result.has("error"):return {"released":false,"error":result.error,"before":before,"after":sample()}
		if result.get("cooled",false):releases+=1;return {"released":true,"before":before,"after":sample()}
		return {"released":false,"reason":result.get("reason","blocked"),"before":before,"after":sample()}
	return {"released":false,"reason":"protected","before":before,"after":sample()}
