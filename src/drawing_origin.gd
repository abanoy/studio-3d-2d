extends RefCounted
# Descriptive ancestry only. These fields never resolve external resources.
static func integer(v,low: int,high: int) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and float(v)==floor(float(v)) and v>=low and v<=high
static func text(v,limit: int) -> bool:
	if not v is String or v.is_empty() or v.length()>limit:return false
	for i in v.length():
		var code: int=v.unicode_at(i)
		if code<32 or code==127 or (code>=0xd800 and code<=0xdfff):return false
	return true
static func digest(v) -> bool:
	if not v is String or v.length()!=64:return false
	for ch in v:
		if not ch in "0123456789abcdef":return false
	return true
static func error(v) -> String:
	if not v is Dictionary or v.size()!=13:return "Invalid drawing source history."
	for key in ["format","kind","name","sha256","width","height","fps","range","visibility","fit","rate","at","duration"]:
		if not v.has(key):return "Incomplete drawing source history."
	if v.format!="studio_drawing_origin_1" or v.kind!="krita":return "Unknown drawing source history."
	if not text(v.name,200) or v.name.contains("/") or v.name.contains("\\") or v.name.contains(":") or not digest(v.sha256):return "Invalid drawing source identity."
	if not integer(v.width,1,32768) or not integer(v.height,1,32768) or v.width*v.height>16777216 or not integer(v.fps,0,1000):return "Invalid original drawing dimensions/timing."
	if not v.range is Array or not v.range.size() in [0,2]:return "Invalid original drawing range."
	if v.range.size()==2 and (not integer(v.range[0],0,10000000) or not integer(v.range[1],int(v.range[0]),10000000)):return "Invalid original drawing range."
	if not v.visibility is Dictionary or v.visibility.size()>128:return "Invalid original layer choices."
	for key in v.visibility:
		if not text(key,128) or not v.visibility[key] is bool:return "Invalid original layer choice."
	if not v.fit is Array or v.fit.size()!=4:return "Invalid drawing fit."
	if not integer(v.fit[0],1,1920) or not integer(v.fit[1],1,1080) or not integer(v.fit[2],0,1920-int(v.fit[0])) or not integer(v.fit[3],0,1080-int(v.fit[1])):return "Invalid drawing fit."
	if not v.rate is Array or v.rate.size()!=2:return "Invalid import rate."
	if not integer(v.rate[0],1,120000) or not integer(v.rate[1],1,1001) or float(v.rate[0])/v.rate[1]>120:return "Invalid import rate."
	if not integer(v.at,0,239) or not integer(v.duration,1,240) or v.at+v.duration>240:return "Invalid original drawing placement."
	if JSON.stringify(v).to_utf8_buffer().size()>32768:return "Drawing source history exceeds its limit."
	return ""
static func layers_error(layers: Array) -> String:
	for layer in layers:
		if layer is Dictionary and layer.has("origin"):
			var why:=error(layer.origin)
			if not why.is_empty():return why
	return ""
static func from_clip(clip: Dictionary,at: int) -> Dictionary:
	var source: Dictionary=clip.source
	var native_range: Array=[]
	if source.get("range") is Dictionary:native_range=[source.range.get("start"),source.range.get("end_inclusive")]
	return {"format":"studio_drawing_origin_1","kind":"krita","name":str(source.path).get_file(),"sha256":source.sha256,"width":source.width,"height":source.height,"fps":source.get("fps",0) if source.get("fps")!=null else 0,"range":native_range,"visibility":source.get("layer_visibility",{}).duplicate(true),"fit":[clip.fit.width,clip.fit.height,clip.fit.x,clip.fit.y],"rate":[clip.fps_num,clip.fps_den],"at":at,"duration":clip.duration_frames}
