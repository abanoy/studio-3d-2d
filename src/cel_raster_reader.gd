extends RefCounted
# Scoped to one project decode, including its children. Duplicate Image resources
# share Godot's lossless pixel storage until written; no cel shares edit identity.
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const MAX_BYTES=32*1024*1024
var entries: Dictionary={}
var adaptive_entries: Dictionary={}
var adaptive_cache=Cache.new()
var cold_cels:=false
var reads:=0
var png_decodes:=0
var hits:=0
var fallback_decodes:=0
static func digest_bytes(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
static func u32(bytes: PackedByteArray,at: int) -> int:
	return int(bytes[at])*16777216+int(bytes[at+1])*65536+int(bytes[at+2])*256+int(bytes[at+3])
func read(path: String,width: int,height: int,expected=null,require_pixels:=false) -> Dictionary:
	return _read(path,width,height,expected,require_pixels,false)
func read_adaptive(path: String,width: int,height: int,expected=null,require_pixels:=false) -> Dictionary:
	return _read(path,width,height,expected,require_pixels,true)
func read_record(path: String,width: int,height: int,expected=null,require_pixels:=false) -> Dictionary:
	return read_adaptive(path,width,height,expected,require_pixels) if cold_cels else read(path,width,height,expected,require_pixels)
func stage(image: Image) -> Dictionary:
	var captured:=Snapshot.capture(image)
	if captured.has("error"):return captured
	var snapshot=captured.raster
	return {"raster":snapshot,"pixel_hash":snapshot.pixel_sha256()} if snapshot._compressed else {"image":image,"pixel_hash":snapshot.pixel_sha256()}
func record(entry: Dictionary) -> Dictionary:
	if entry.has("raster"):
		var adopted:=Owner.from_snapshot(entry.raster,adaptive_cache)
		return adopted if adopted.has("error") else {"raster_owner":adopted.owner}
	var adopted:=Owner.from_image(entry.image.duplicate(),adaptive_cache)
	return adopted if adopted.has("error") else {"raster_owner":adopted.owner}
func _read(path: String,width: int,height: int,expected,require_pixels: bool,adaptive: bool) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null:return {"error":"Cel missing or exceeds 32 MiB."}
	var length:=file.get_length()
	if length>MAX_BYTES:file.close();return {"error":"Cel missing or exceeds 32 MiB."}
	if length==0:file.close();return {"error":"Cel image has wrong dimensions or is unreadable."}
	var bytes:=file.get_buffer(length);file.close();reads+=1
	if bytes.size()!=length:return {"error":"Cel image has wrong dimensions or is unreadable."}
	var png: bool=path.get_extension().to_lower()=="png" and bytes.size()>=8 and bytes.slice(0,8)==PackedByteArray([137,80,78,71,13,10,26,10])
	if not png:
		# Preserve legacy directory readers' other image-loader formats. No cached
		# reuse for this path: each record still has its own freshly loaded Image.
		var legacy:=Image.load_from_file(path);fallback_decodes+=1
		if legacy==null or legacy.get_width()!=width or legacy.get_height()!=height:return {"error":"Cel image has wrong dimensions or is unreadable."}
		legacy.convert(Image.FORMAT_RGBA8)
		if require_pixels and (not expected is String or digest_bytes(legacy.get_data())!=expected):return {"error":"Cel checksum differs. Try the previous saved copy."}
		if not adaptive:return {"image":legacy}
		var staged:=stage(legacy)
		return staged if staged.has("error") else record(staged)
	# Check the fixed canvas before PNG allocation, then let the decoder validate
	# the entire captured buffer. A cache hit still reads/checks its declared file.
	if bytes.size()<33 or u32(bytes,8)!=13 or bytes.slice(12,16).get_string_from_ascii()!="IHDR" or u32(bytes,16)!=width or u32(bytes,20)!=height:return {"error":"Cel image has wrong dimensions or is unreadable."}
	var fingerprint:=digest_bytes(bytes);var cache: Dictionary=adaptive_entries if adaptive else entries;var entry: Dictionary=cache.get(fingerprint,{})
	if entry.is_empty():
		var decoded:=Image.new()
		if decoded.load_png_from_buffer(bytes)!=OK or decoded.get_width()!=width or decoded.get_height()!=height:return {"error":"Cel image has wrong dimensions or is unreadable."}
		decoded.convert(Image.FORMAT_RGBA8);png_decodes+=1
		entry=stage(decoded) if adaptive else {"image":decoded,"pixel_hash":""}
		if entry.has("error"):return entry
	else:hits+=1
	if require_pixels:
		if entry.pixel_hash.is_empty():entry.pixel_hash=digest_bytes(entry.image.get_data())
		if not expected is String or entry.pixel_hash!=expected:return {"error":"Cel checksum differs. Try the previous saved copy."}
	cache[fingerprint]=entry
	return record(entry) if adaptive else {"image":entry.image.duplicate()}
# Opt-in staging API for the upcoming live-cel ownership migration. Existing
# read() and project adoption stay eager. Do not mix eager/cold calls on a reader:
# cold capture releases its validated decode cache after each file.
func read_cold(path: String,width: int,height: int,expected=null,require_pixels:=false) -> Dictionary:
	var decoded:=read(path,width,height,expected,require_pixels)
	if decoded.has("error"):entries.clear();return decoded
	var captured: Dictionary=preload("res://src/cel_raster_snapshot.gd").capture(decoded.image)
	entries.clear()
	return captured
