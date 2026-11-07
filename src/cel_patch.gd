extends RefCounted
const DrawingLimits=preload("res://src/drawing_limits.gd")
const Drawing=preload("res://src/drawing.gd")
const Timing=preload("res://src/cel_timing.gd")

static func create(layer: String,owner: String,before: Array,after: Array) -> Dictionary:
	var old:={};var newer:={}
	for cel in before:old[cel.id]=cel
	for cel in after:newer[cel.id]=cel
	var previous: Array=[];var following: Array=[]
	for id in old:
		if not newer.has(id) or old[id]!=newer[id]:previous.append(old[id].duplicate(true))
	for id in newer:
		if not old.has(id) or old[id]!=newer[id]:following.append(newer[id].duplicate(true))
	var bytes:=1024;var images:={}
	for cel in previous+following:
		var metadata: Dictionary=cel.duplicate();metadata.erase("image");metadata.erase("raster_owner")
		# Conservative UTF-32/string and container allowance; raster resources are
		# counted once per command even when both sides share the original Image.
		bytes+=4*JSON.stringify(metadata,"",true,true).to_utf8_buffer().size()
		var id: int=Drawing.raster_token(cel)[0]
		if not images.has(id):images[id]=true;bytes+=Drawing.raster_bytes(cel,true)
	return {"type":"cel_patch","layer_id":layer,"owner":owner,"before":previous,"after":following,"bytes":bytes}

static func same(cel: Dictionary,expected: Dictionary) -> bool:
	var a:=cel.duplicate();var b:=expected.duplicate();a.erase("image");b.erase("image");a.erase("raster_owner");b.erase("raster_owner")
	for field in ["start","duration"]:
		if not Timing.integer(a.get(field),0,Timing.MAX_FRAMES) or not Timing.integer(b.get(field),0,Timing.MAX_FRAMES):return false
		a[field]=int(a[field]);b[field]=int(b[field])
	var left:=Drawing.raster_token(cel);var right:=Drawing.raster_token(expected)
	if a!=b or left.is_empty() or right.is_empty():return false
	if left[0]==right[0]:return true
	var image:=Drawing.image(cel);var other:=Drawing.image(expected)
	return image!=null and other!=null and image.get_size()==other.get_size() and image.get_format()==other.get_format() and image.get_data()==other.get_data()

static func apply(cels: Array,command: Dictionary,side: String,frames: int,limit:=DrawingLimits.MAX_CELS) -> Dictionary:
	if not side in ["before","after"]:return {"error":"Invalid drawing history direction."}
	var expected: Array=command["after" if side=="before" else "before"]
	var wanted: Array=command[side];var removed:={};var found:={};var all:={}
	for cel in command.before+command.after:all[cel.id]=true
	for cel in expected:removed[cel.id]=cel
	var result: Array=[]
	for cel in cels:
		if all.has(cel.id):
			if found.has(cel.id) or not removed.has(cel.id) or not same(cel,removed[cel.id]):return {"error":"The drawing history target changed. Current drawings were kept."}
			found[cel.id]=true
		else:result.append(cel)
	if found.size()!=expected.size():return {"error":"The drawing history target is missing. Current drawings were kept."}
	result.append_array(wanted.duplicate(true));result.sort_custom(func(a,b):return a.start<b.start)
	if result.size()>limit:return {"error":"Restoring this drawing would exceed the project drawing limit."}
	if not result.is_empty():
		var why:=Timing.proposal(result,result[0].id,result[0].start,frames)
		if why.has("error"):return why
	return {"cels":result}
