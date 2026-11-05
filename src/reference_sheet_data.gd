extends RefCounted
# Shared bounded PNG loading and the schema7 project reference contract.
const FORMAT="studio_reference_sheet_1"
const MAX_FILE=16*1024*1024
const MAX_PIXELS=4*1024*1024
const MAX_SIDE=8192
static func big32(bytes: PackedByteArray,offset: int) -> int:
	return int(bytes[offset])*16777216+int(bytes[offset+1])*65536+int(bytes[offset+2])*256+int(bytes[offset+3])
static func header_error(bytes: PackedByteArray) -> String:
	if bytes.size()>MAX_FILE:return "Reference PNG exceeds 16 MiB."
	if bytes.size()<33 or bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]) or big32(bytes,8)!=13 or bytes.slice(12,16)!=PackedByteArray([73,72,68,82]):return "Choose a readable PNG reference sheet."
	var width:=big32(bytes,16);var height:=big32(bytes,20)
	if width<1 or height<1 or width>MAX_SIDE or height>MAX_SIDE or width*height>MAX_PIXELS:return "Reference sheet supports up to 4 megapixels and 8192 pixels on either side."
	return ""
static func read_image(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file:return {"error":"Reference PNG is unavailable. The current sheet was kept."}
	if file.get_length()>MAX_FILE:file.close();return {"error":"Reference PNG exceeds 16 MiB. The current sheet was kept."}
	var bytes:=file.get_buffer(MAX_FILE+1);file.close();var why:=header_error(bytes)
	if not why.is_empty():return {"error":why}
	var decoded:=Image.new();var code:=decoded.load_png_from_buffer(bytes)
	if code!=OK:return {"error":"Reference PNG could not be decoded. The current sheet was kept."}
	if decoded.get_width()!=big32(bytes,16) or decoded.get_height()!=big32(bytes,20):return {"error":"Reference dimensions changed. The current sheet was kept."}
	decoded.convert(Image.FORMAT_RGBA8)
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes)
	return {"image":decoded,"sha256":hash.finish().hex_encode(),"bytes":bytes}
static func text(value,limit: int) -> bool:
	if not value is String or value.is_empty() or value.length()>limit:return false
	for c in value:
		var n: int=c.unicode_at(0)
		if n<32 or n==127 or n>=0xd800 and n<=0xdfff:return false
	return true
static func digest(value) -> bool:
	if not value is String or value.length()!=64:return false
	for c in value:
		if not c in "0123456789abcdef":return false
	return true
static func error(value,portable:=false) -> String:
	if not value is Dictionary or value.size()!=4 or value.get("format")!=FORMAT or not text(value.get("name"),200) or not digest(value.get("sha256")):return "Invalid project reference sheet identity."
	if value.name.contains("/") or value.name.contains("\\") or value.name.contains(":"):return "Reference sheet name cannot contain a path."
	var field:="path" if portable else "source"
	if not value.has(field) or not text(value[field],4096):return "Missing reference sheet source."
	if portable and value.path!="references/"+value.sha256+".png":return "Unsafe project reference sheet path."
	return ""
static func unwrap(value: Dictionary) -> Dictionary:
	var version=value.get("content_schema_version")
	if not (version is int or version is float) or not is_finite(float(version)) or float(version)!=floor(float(version)) or not int(version) in [3,4,5,6]:return {"error":"Invalid schema7 content version."}
	var why:=error(value.get("reference_sheet"),true)
	if not why.is_empty():return {"error":why}
	var base:=value.duplicate(true);base.schema_version=int(version);base.erase("content_schema_version");base.erase("reference_sheet")
	return {"base":base,"reference":value.reference_sheet.duplicate(true)}
static func portable(value: Dictionary) -> Dictionary:
	return {"format":FORMAT,"name":value.name,"sha256":value.sha256,"path":"references/"+value.sha256+".png"}
static func cache_image(loaded: Dictionary,folder: String) -> Dictionary:
	if loaded.has("error"):return loaded
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:return {"error":"Cannot create the reference sheet cache."}
	var target:=folder.path_join(str(loaded.sha256)+".png")
	if FileAccess.file_exists(target) and FileAccess.get_sha256(target)==loaded.sha256:return {"source":target}
	var temporary:=target+".%d-%s.tmp" % [OS.get_process_id(),str(ResourceUID.create_id())]
	if FileAccess.file_exists(temporary) or DirAccess.dir_exists_absolute(temporary):return {"error":"Cannot reserve a reference cache file."}
	var file:=FileAccess.open(temporary,FileAccess.WRITE)
	if not file:return {"error":"Cannot cache the reference sheet."}
	file.store_buffer(loaded.bytes);file.flush();var code:=file.get_error();file.close()
	if code!=OK or FileAccess.get_sha256(temporary)!=loaded.sha256 or DirAccess.rename_absolute(temporary,target)!=OK:
		DirAccess.remove_absolute(temporary);return {"error":"Cannot commit the reference sheet cache. The current sheet was kept."}
	return {"source":target}
