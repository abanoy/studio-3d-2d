extends RefCounted
# Authored body poses only: no root placement, face, helper tracks or native assets.
const Model=preload("res://src/model.gd")
const Format="studio_body_pose_library_1"
const FIELD="body_pose_library"
const MAX_BYTES=192*1024
const MAX_ENTRIES=16
static func text(value,limit: int) -> bool:
	if not value is String or value.is_empty() or value.length()>limit:return false
	for i in value.length():
		var code: int=value.unicode_at(i)
		if code<32 or code==127 or code>=0xd800 and code<=0xdfff:return false
	return true
static func be32(b: PackedByteArray,at: int) -> int:
	return int(b[at])<<24|int(b[at+1])<<16|int(b[at+2])<<8|int(b[at+3])
static func thumbnail(value) -> Dictionary:
	if not value is String or value.is_empty() or value.length()>32768:return {"error":"Invalid body-pose thumbnail."}
	if value.length()%4!=0:return {"error":"Invalid body-pose thumbnail encoding."}
	var plain: String=value.rstrip("=")
	if value.length()-plain.length()>2 or plain.contains("="):return {"error":"Invalid body-pose thumbnail encoding."}
	for ch in value:
		if not ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=":return {"error":"Invalid body-pose thumbnail encoding."}
	var bytes:=Marshalls.base64_to_raw(value)
	if bytes.size()<33 or bytes.size()>24576 or Marshalls.raw_to_base64(bytes)!=value:return {"error":"Invalid body-pose thumbnail encoding."}
	if bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]) or bytes.slice(12,16).get_string_from_ascii()!="IHDR" or be32(bytes,16)!=96 or be32(bytes,20)!=54 or bytes[24]!=8 or not bytes[25] in [2,6] or bytes[26]!=0 or bytes[27]!=0 or bytes[28]!=0:return {"error":"Body-pose thumbnails must be96×54PNG."}
	var image:=Image.new()
	if image.load_png_from_buffer(bytes)!=OK:return {"error":"Unreadable body-pose thumbnail."}
	return {"image":image}
static func error(value) -> String:
	if not value is Dictionary or value.size()!=4 or value.get("format")!=Format:return "Invalid body-pose library format."
	if not preload("res://src/drawing_origin.gd").digest(value.get("sha256")):return "Invalid body-pose source identity."
	if not value.get("bone_ids") is Array or value.bone_ids.is_empty() or value.bone_ids.size()>512:return "Invalid body-pose rig bindings."
	var bones:={}
	for id in value.bone_ids:
		if not text(id,512) or bones.has(id) or id=="@root":return "Invalid or duplicate body-pose bone binding."
		bones[id]=true
	if not value.get("entries") is Array or value.entries.size()>MAX_ENTRIES:return "Body-pose library supports sixteen saved poses."
	var ids:={};var names:={}
	for entry in value.entries:
		if not entry is Dictionary or entry.size()!=4 or not text(entry.get("id"),128) or ids.has(entry.id) or not text(entry.get("name"),64) or names.has(entry.name.to_lower()):return "Invalid or duplicate saved body pose."
		ids[entry.id]=true;names[entry.name.to_lower()]=true
		if not Model.pose_valid(entry.get("pose")):return "Invalid saved body-pose transforms."
		for id in entry.pose:
			if not bones.has(id) or entry.pose[id].size()!=2:return "Saved body pose refers to an unknown bone or field."
		var picture:=thumbnail(entry.get("thumbnail_png"))
		if picture.has("error"):return picture.error
	if JSON.stringify(value,"",true,true).to_utf8_buffer().size()>MAX_BYTES:return "Body-pose library exceeds192KiB. Use fewer saved poses."
	return ""
static func empty(rig: RefCounted) -> Dictionary:
	return {"format":Format,"sha256":rig.data.sha256,"bone_ids":Array(rig.order),"entries":[]}
static func get_library(rig: RefCounted) -> Dictionary:
	return rig.data.metadata.get(FIELD,empty(rig)).duplicate(true)
static func compatible(value: Dictionary,rig: RefCounted) -> String:
	var why:=error(value)
	if not why.is_empty():return why
	if value.sha256!=rig.data.sha256 or value.bone_ids!=Array(rig.order):return "These body poses belong to a different imported rig. Automatic retargeting is not available."
	return ""
static func unique_name(value: String,entries: Array) -> String:
	var stem:=value.strip_edges().left(58);var result:=stem;var number:=2
	while entries.any(func(e):return e.name.nocasecmp_to(result)==0):result=stem+" "+str(number);number+=1
	return result
static func equivalent(a,b) -> bool:
	return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
