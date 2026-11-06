extends RefCounted
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
		var metadata: Dictionary=cel.duplicate();metadata.erase("image")
		# Conservative UTF-32/string and container allowance; raster resources are
		# counted once per command even when both sides share the original Image.
		bytes+=4*JSON.stringify(metadata,"",true,true).to_utf8_buffer().size()
		var id: int=cel.image.get_instance_id()
		if not images.has(id):images[id]=true;bytes+=cel.image.get_data_size()
	return {"type":"cel_patch","layer_id":layer,"owner":owner,"before":previous,"after":following,"bytes":bytes}

static func same(cel: Dictionary,expected: Dictionary) -> bool:
	var a:=cel.duplicate();var b:=expected.duplicate();a.erase("image");b.erase("image")
	for field in ["start","duration"]:
		if not Timing.integer(a.get(field),0,Timing.MAX_FRAMES) or not Timing.integer(b.get(field),0,Timing.MAX_FRAMES):return false
		a[field]=int(a[field]);b[field]=int(b[field])
	if a!=b or not cel.get("image") is Image or not expected.get("image") is Image:return false
	if is_same(cel.image,expected.image):return true
	return cel.image.get_size()==expected.image.get_size() and cel.image.get_format()==expected.image.get_format() and cel.image.get_data()==expected.image.get_data()

static func apply(cels: Array,command: Dictionary,side: String,frames: int,limit:=32) -> Dictionary:
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
	if result.size()>limit:return {"error":"Restoring this drawing would exceed the global32cel budget."}
	if not result.is_empty():
		var why:=Timing.proposal(result,result[0].id,result[0].start,frames)
		if why.has("error"):return why
	return {"cels":result}
