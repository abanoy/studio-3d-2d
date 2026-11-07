extends RefCounted
# One save operation retains only digest strings, never decoded validation rasters.
const Reader=preload("res://src/cel_raster_reader.gd")
var verified: Dictionary={}
var reads:=0
var decodes:=0
var hits:=0
func checksum(path: String,width: int,height: int) -> String:
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null:return ""
	var length:=file.get_length()
	if length<33 or length>Reader.MAX_BYTES:file.close();return ""
	var bytes:=file.get_buffer(length);file.close();reads+=1
	if bytes.size()!=length or bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]):return ""
	if Reader.u32(bytes,8)!=13 or bytes.slice(12,16).get_string_from_ascii()!="IHDR" or Reader.u32(bytes,16)!=width or Reader.u32(bytes,20)!=height:return ""
	var fingerprint:=Reader.digest_bytes(bytes)
	if verified.has(fingerprint):hits+=1;return str(verified[fingerprint])
	var image:=Image.new()
	if image.load_png_from_buffer(bytes)!=OK or image.get_width()!=width or image.get_height()!=height:return ""
	image.convert(Image.FORMAT_RGBA8);decodes+=1
	var pixels:=Reader.digest_bytes(image.get_data());verified[fingerprint]=pixels
	return pixels

func matches(path: String,width: int,height: int,expected: String) -> bool:
	var actual:=checksum(path,width,height)
	return not actual.is_empty() and actual==expected

func valid(path: String,width: int,height: int,expected=null) -> bool:
	if expected!=null and not expected is String:return false
	if path.get_extension().to_lower()!="png":
		# Older directory readers also accept their image-loader formats. Keep
		# at most one validation decode, with no retained eager project cache.
		var reader:=Reader.new();var result:=reader.read(path,width,height,expected,expected!=null);reader.entries.clear()
		return not result.has("error")
	var actual:=checksum(path,width,height)
	return not actual.is_empty() and (expected==null or actual==str(expected))
