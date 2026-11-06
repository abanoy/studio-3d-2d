extends RefCounted
# Immutable cold pixel ownership. Not yet a replacement for live cel.image.
const MAX_SIZE=Vector2i(1920,1080)
var _size:=Vector2i.ZERO
var _payload:=PackedByteArray()
var _compressed:=false
var _pixel_sha:=""
var _payload_sha:=""
var _seal:=""

static func digest(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
func seal() -> String:
	return digest((str(_size.x)+":"+str(_size.y)+":"+str(_compressed)+":"+_pixel_sha+":"+_payload_sha).to_utf8_buffer())
static func capture(source: Image) -> Dictionary:
	if source==null or source.is_empty() or source.is_compressed():return {"error":"Missing or unsupported cold drawing source."}
	var size:=source.get_size()
	if size.x<1 or size.y<1 or size.x>MAX_SIZE.x or size.y>MAX_SIZE.y:return {"error":"Cold drawing exceeds the supported canvas."}
	var detached: Image=source.duplicate();detached.clear_mipmaps();detached.convert(Image.FORMAT_RGBA8)
	var raw:=detached.get_data();var packed:=raw.compress(FileAccess.COMPRESSION_ZSTD)
	var snapshot=load("res://src/cel_raster_snapshot.gd").new()
	snapshot._size=size;snapshot._pixel_sha=digest(raw)
	# Avoid retaining both raw and compressed copies, or expanding noisy artwork.
	snapshot._compressed=not packed.is_empty() and packed.size()<=raw.size()*7/8
	snapshot._payload=packed if snapshot._compressed else raw
	snapshot._payload_sha=digest(snapshot._payload);snapshot._seal=snapshot.seal()
	return {"raster":snapshot}
func verify() -> String:
	if _size.x<1 or _size.y<1 or _size.x>MAX_SIZE.x or _size.y>MAX_SIZE.y or _pixel_sha.length()!=64 or _payload_sha.length()!=64 or _seal!=seal():return "Invalid cold drawing descriptor."
	if _payload.is_empty() or _payload.size()>_size.x*_size.y*4 or digest(_payload)!=_payload_sha:return "Cold drawing payload checksum differs."
	return ""
func materialize() -> Dictionary:
	var why:=verify()
	if not why.is_empty():return {"error":why}
	var length:=_size.x*_size.y*4
	# A fixed validated allocation limit; never trust a compressed size header.
	var pixels:=_payload.decompress(length,FileAccess.COMPRESSION_ZSTD) if _compressed else _payload
	if pixels.size()!=length or digest(pixels)!=_pixel_sha:return {"error":"Cold drawing pixel checksum differs."}
	return {"image":Image.create_from_data(_size.x,_size.y,false,Image.FORMAT_RGBA8,pixels)}
func storage_bytes() -> int:return _payload.size()
func decoded_bytes() -> int:return _size.x*_size.y*4
func pixel_sha256() -> String:return _pixel_sha
