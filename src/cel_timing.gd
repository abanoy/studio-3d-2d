extends RefCounted
const DrawingLimits=preload("res://src/drawing_limits.gd")
# Same-layer timing edits retain raster identity; collisions refuse.
const MAX_FRAMES=preload("res://src/extended_timing.gd").MAX_FRAMES
static func integer(value,low: int,high: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=low and value<=high
static func proposal(cels,id: String,start,frames,length=null) -> Dictionary:
	if not integer(frames,1,MAX_FRAMES) or not integer(start,0,int(frames)-1) or not cels is Array or cels.size()>DrawingLimits.MAX_CELS:return {"error":"Choose a whole drawing start inside the scene."}
	var index:=-1;var previous_end:=0;var ids:={}
	for i in range(cels.size()):
		var cel=cels[i]
		if not cel is Dictionary or not cel.get("id") is String or cel.id.is_empty() or ids.has(cel.id) or not integer(cel.get("start"),0,int(frames)-1) or not integer(cel.get("duration"),1,int(frames)) or cel.start<previous_end or cel.start+cel.duration>frames:return {"error":"Drawing exposure identities or ranges are invalid. Existing drawings stay unchanged."}
		ids[cel.id]=true;previous_end=int(cel.start+cel.duration)
		if cel.id==id:index=i
	if index<0:return {"error":"The drawing no longer exists."}
	var target: Dictionary=cels[index]
	if length==null:length=target.duration
	if not integer(length,1,int(frames)):return {"error":"Choose a whole drawing exposure of at least one frame."}
	if start+length>frames:return {"error":"Keep the complete drawing exposure inside the scene."}
	for i in range(cels.size()):
		if i!=index and start<cels[i].start+cels[i].duration and cels[i].start<start+length:return {"error":"This drawing would overlap another exposure. Choose a free range on the same layer."}
	return {"index":index,"before":int(target.start),"after":int(start),"duration":int(target.duration),"after_duration":int(length),"changed":start!=target.start or length!=target.duration}
