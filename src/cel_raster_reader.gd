extends RefCounted
# Scoped to one project decode, including its children. Duplicate Image resources
# share Godot's lossless pixel storage until written; no cel shares edit identity.
const MAX_BYTES=32*1024*1024
var entries: Dictionary={}
var reads:=0
var png_decodes:=0
var hits:=0
var fallback_decodes:=0
static func digest_bytes(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
static func u32(bytes: PackedByteArray,at: int) -> int:
	return int(bytes[at])*16777216+int(bytes[at+1])*65536+int(bytes[at+2])*256+int(bytes[at+3])
func read(path: String,width: int,height: int,expected=null,require_pixels:=false) -> Dictionary:
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
		return {"image":legacy}
	# Check the fixed canvas before PNG allocation, then let the decoder validate
	# the entire captured buffer. A cache hit still reads/checks its declared file.
	if bytes.size()<33 or u32(bytes,8)!=13 or bytes.slice(12,16).get_string_from_ascii()!="IHDR" or u32(bytes,16)!=width or u32(bytes,20)!=height:return {"error":"Cel image has wrong dimensions or is unreadable."}
	var fingerprint:=digest_bytes(bytes);var entry: Dictionary=entries.get(fingerprint,{})
	if entry.is_empty():
		var decoded:=Image.new()
		if decoded.load_png_from_buffer(bytes)!=OK or decoded.get_width()!=width or decoded.get_height()!=height:return {"error":"Cel image has wrong dimensions or is unreadable."}
		decoded.convert(Image.FORMAT_RGBA8);png_decodes+=1;entry={"image":decoded,"pixel_hash":""}
	else:hits+=1
	if require_pixels:
		if entry.pixel_hash.is_empty():entry.pixel_hash=digest_bytes(entry.image.get_data())
		if not expected is String or entry.pixel_hash!=expected:return {"error":"Cel checksum differs. Try the previous saved copy."}
	entries[fingerprint]=entry
	return {"image":entry.image.duplicate()}
