extends RefCounted
# Staged live-cel contract. An edited image stays authoritative and pinned:
# existing pixel Undo commands address that exact Image object.
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
var _cold
var _hot: Image
var _cache
static func from_snapshot(snapshot,cache) -> Dictionary:
	if not snapshot is Snapshot or not cache is Cache:return {"error":"Invalid cold drawing owner."}
	var why: String=snapshot.verify()
	if not why.is_empty():return {"error":why}
	var owner=load("res://src/cel_raster_owner.gd").new();owner._cold=snapshot;owner._cache=cache
	return {"owner":owner}
static func from_image(image: Image) -> Dictionary:
	if image==null or image.is_empty() or image.is_compressed() or image.get_format()!=Image.FORMAT_RGBA8 or image.has_mipmaps() or image.get_width()>1920 or image.get_height()>1080:return {"error":"Invalid editable drawing owner."}
	var owner=load("res://src/cel_raster_owner.gd").new();owner._hot=image
	return {"owner":owner}
func token() -> Array:
	return [get_instance_id(),int(_hot.get_meta("studio_pixels_revision",0)) if _hot!=null else 0]
func read() -> Dictionary:
	if _hot!=null:return {"image":_hot}
	if not _cold is Snapshot or not _cache is Cache:return {"error":"Drawing owner has no pixels."}
	return _cache.read(_cold)
func pin(expected_token: Array=[],borrowed: Image=null) -> Dictionary:
	if not expected_token.is_empty() and expected_token!=token():return {"error":"Drawing pixels changed before editing."}
	if _hot!=null:
		if borrowed!=null and not is_same(borrowed,_hot):return {"error":"Drawing edit image is stale."}
		return {"image":_hot}
	if not _cold is Snapshot:return {"error":"Drawing owner has no pixels."}
	if borrowed!=null:
		# Selection/worker previews may already hold this exact read image. Adopt
		# it only while its token and independent full pixel identity still match.
		var why: String=_cold.verify()
		if not why.is_empty():return {"error":why}
		if expected_token.is_empty() or borrowed.get_size()!=_cold._size or borrowed.get_format()!=Image.FORMAT_RGBA8 or borrowed.has_mipmaps() or Snapshot.digest(borrowed.get_data())!=_cold.pixel_sha256() or int(borrowed.get_meta("studio_pixels_revision",0))!=0:return {"error":"Borrowed drawing pixels changed before editing."}
		_hot=borrowed
	else:
		var result:=read()
		if result.has("error"):return result
		_hot=result.image
	_cold=null;_cache=null
	return {"image":_hot}
func snapshot() -> Dictionary:
	if _hot!=null:return Snapshot.capture(_hot)
	if not _cold is Snapshot:return {"error":"Drawing owner has no pixels."}
	var why: String=_cold.verify()
	return {"raster":_cold} if why.is_empty() else {"error":why}
func retained_bytes() -> int:
	return _hot.get_data_size() if _hot!=null else _cold.storage_bytes() if _cold is Snapshot else 0
func decoded_bytes() -> int:
	return _hot.get_data_size() if _hot!=null else _cold.decoded_bytes() if _cold is Snapshot else 0
func is_pinned() -> bool:return _hot!=null
