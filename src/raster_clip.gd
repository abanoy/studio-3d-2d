extends RefCounted
const Origin=preload("res://src/drawing_origin.gd")
static func be32(b: PackedByteArray,at: int) -> int:
	return (int(b[at])<<24)|(int(b[at+1])<<16)|(int(b[at+2])<<8)|int(b[at+3])
static func validate(v,folder: String,video: Dictionary,at: int,remaining: int,source_sha: String) -> Dictionary:
	if not v is Dictionary or not v.get("format") in ["studio_raster_clip_1","studio_raster_clip_2"]:return {"error":"Unknown prepared artwork format."}
	if not v.get("source") is Dictionary or v.source.get("kind")!=("video" if v.format=="studio_raster_clip_2" else "krita") or not v.source.get("path") is String or v.source.get("sha256")!=source_sha:return {"error":"Prepared source identity changed."}
	for key in ["width","height","fps_num","fps_den"]:
		if v.get(key)!=video.get(key):return {"error":"Prepared artwork does not match this movie."}
	if not Origin.integer(v.get("duration_frames"),1,int(video.duration_frames)-at) or not v.get("holds") is Array or v.holds.is_empty() or v.holds.size()>remaining:return {"error":"Prepared artwork exceeds available frames or drawings."}
	if not v.get("fit") is Dictionary or not v.source.get("layer_visibility",{}) is Dictionary:return {"error":"Invalid prepared fit/layer choices."}
	for key in ["width","height","x","y"]:
		if not v.fit.has(key):return {"error":"Incomplete drawing fit."}
	for key in ["width","height"]:
		if not v.source.has(key):return {"error":"Incomplete original dimensions."}
	var origin:=Origin.from_clip(v,at);var why:=Origin.error(origin)
	if not why.is_empty():return {"error":why}
	var cursor:=0;var total:=0;var unique:={};var holds:=[]
	for row in v.holds:
		if not row is Dictionary or not Origin.integer(row.get("start"),cursor,cursor) or not Origin.integer(row.get("duration"),1,int(v.duration_frames)-cursor):return {"error":"Prepared drawing timing is not contiguous."}
		if not Origin.digest(row.get("sha256")) or row.get("path")!="images/"+str(row.get("sha256"))+".png" or not Origin.integer(row.get("bytes"),33,32*1024*1024):return {"error":"Invalid prepared drawing reference."}
		var path:=folder.path_join(row.path);var file:=FileAccess.open(path,FileAccess.READ)
		if file==null or file.get_length()!=int(row.bytes):return {"error":"Prepared drawing is missing or changed."}
		var head:=file.get_buffer(33);file.close()
		if head.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]) or head.slice(12,16).get_string_from_ascii()!="IHDR" or be32(head,16)!=int(video.width) or be32(head,20)!=int(video.height) or head[24]!=8 or head[25]!=6:return {"error":"Prepared drawing must be full-frame RGBA8 PNG."}
		if FileAccess.get_sha256(path)!=row.sha256:return {"error":"Prepared drawing checksum changed."}
		if not unique.has(row.sha256):unique[row.sha256]=true;total+=int(row.bytes)
		if total>256*1024*1024:return {"error":"Prepared artwork exceeds its byte budget."}
		holds.append({"start":int(row.start),"duration":int(row.duration),"path":path});cursor+=int(row.duration)
	if cursor!=int(v.duration_frames):return {"error":"Prepared drawing range is incomplete."}
	return {"origin":origin,"holds":holds,"duration":cursor}
