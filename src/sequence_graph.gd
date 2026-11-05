extends RefCounted
const Extended=preload("res://src/extended_timing.gd")
const FORMAT="studio_sequences_1"
const SHADOW_FORMAT="studio_sequences_2"
const MASK_FORMAT="studio_sequences_3"
const CLIP_FIELDS=["id","asset_id","start","duration","source_in","time_in","key_in","loop","visible","muted","gain_db","keys"]
const KEY_FIELDS=["frame","offset","scale","rotation","opacity","interpolation"]
static func number(v,low: float,high: float) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and v>=low and v<=high
static func integer(v,low: float,high: float) -> bool:
	return number(v,low,high) and float(v)==floor(float(v))
static func identity(v) -> bool:
	if not v is String or v.is_empty() or v.length()>128:return false
	for c in v:
		if not c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-":return false
	return true
static func fields(v,required: Array) -> bool:
	if not v is Dictionary or v.size()!=required.size():return false
	for key in required:
		if not v.has(key):return false
	return true
static func error(graph,root) -> String:
	if not fields(graph,["format","assets","clips"]) or not graph.format in [FORMAT,SHADOW_FORMAT,MASK_FORMAT]:return "Unknown editable sequence graph."
	if not graph.assets is Array or graph.assets.is_empty() or graph.assets.size()>4:return "Expected 1–4 editable sequence assets."
	if not root is Dictionary or not root.get("video") is Dictionary:return "Missing parent sequence timing."
	var index:={};var documents: Array=[root];var rate: Dictionary=root.video
	for asset in graph.assets:
		if not fields(asset,["id","name","scene","clips"]) or not identity(asset.id) or index.has(asset.id):return "Invalid or duplicate sequence identity."
		if not asset.name is String or asset.name.is_empty() or asset.name.length()>80:return "Invalid sequence name."
		for c in asset.name:
			var n: int=c.unicode_at(0)
			if n<32 or n==127 or (n>=0xd800 and n<=0xdfff):return "Invalid sequence name."
		var scene=asset.scene
		if not scene is Dictionary or not Extended.child_schema(scene) in [4,5] or scene.has("sequence_graph") or scene.has("scene") or scene.has("model"):return "Sequence scenes require a world document without another embedded graph."
		index[asset.id]=asset;documents.append(scene)
	var cels:=0;var sounds:=0;var objects:=0;var effects:=0
	for position in range(documents.size()):
		var scene: Dictionary=documents[position];var video=scene.get("video")
		if not video is Dictionary or not Extended.video_error(video).is_empty() or position>0 and not integer(video.get("duration_frames"),1,240):return "Invalid parent/local sequence duration."
		if not integer(video.get("width"),1920,1920) or not integer(video.get("height"),1080,1080) or not integer(video.get("fps_num"),1,120000) or not integer(video.get("fps_den"),1,1001) or float(video.fps_num)/video.fps_den>120:return "Invalid sequence canvas/rate."
		for key in ["width","height","fps_num","fps_den"]:
			if video.get(key)!=rate.get(key):return "Sequences must share canvas size and frame rate."
		var layers=scene.get("layers");var world=scene.get("world");var audio=scene.get("audio",{})
		if not layers is Array or layers.size()>4 or not world is Dictionary or not world.get("objects") is Array or not world.get("effects",[]) is Array or not audio is Dictionary:return "Invalid sequence scene tracks."
		for layer in layers:
			if not layer is Dictionary or not layer.get("cels") is Array:return "Invalid sequence drawing track."
			cels+=layer.cels.size()
		var rows=audio.get("clips") if audio.has("clips") else [audio] if not audio.is_empty() else []
		if not rows is Array:return "Invalid sequence audio tracks."
		sounds+=rows.size();objects+=world.objects.size();effects+=world.get("effects",[]).size()
	if cels>32 or sounds>16 or objects>64 or effects>16:return "Sequences exceed the shared drawing/audio/world resource budget."
	var ids:={};var total:=0;var owners: Array=[{"id":"","clips":graph.clips}];owners.append_array(graph.assets)
	for owner in owners:
		if not owner.clips is Array:return "Invalid sequence clips."
		var parent: Dictionary=root if owner.id.is_empty() else index[owner.id].scene
		total+=owner.clips.size()
		if total>8:return "At most8 sequence clips per project."
		for clip in owner.clips:
			var expected: Array=CLIP_FIELDS+(["shadow"] if graph.format!=FORMAT else [])+(["mask"] if graph.format==MASK_FORMAT else [])
			if not fields(clip,expected) or not identity(clip.id) or ids.has(clip.id) or not clip.asset_id is String or not index.has(clip.asset_id):return "Invalid sequence clip identity or missing asset."
			if graph.format!=FORMAT and not shadow_error(clip.shadow).is_empty():return shadow_error(clip.shadow)
			if graph.format==MASK_FORMAT and not mask_error(clip.mask).is_empty():return mask_error(clip.mask)
			ids[clip.id]=true
			var child: Dictionary=index[clip.asset_id].scene.video
			if not integer(clip.start,0,parent.video.duration_frames-1) or not integer(clip.duration,1,parent.video.duration_frames-clip.start) or not integer(clip.source_in,0,child.duration_frames-1):return "Sequence clip exceeds its parent/local range."
			if not integer(clip.time_in,0,1000000) or not integer(clip.key_in,0,1000000):return "Invalid sequence source window."
			if not clip.loop is bool or not clip.visible is bool or not clip.muted is bool or not number(clip.gain_db,-60,12):return "Invalid sequence clip visibility/audio."
			if not clip.loop and clip.source_in+clip.time_in+clip.duration>child.duration_frames:return "Non-looping sequence exceeds its source range."
			if not clip.keys is Array or clip.keys.is_empty() or clip.keys.size()>32:return "Expected 1–32 sequence placement keys."
			var previous:=-1
			for key in clip.keys:
				if not fields(key,KEY_FIELDS) or not integer(key.frame,0,Extended.MAX_PLACEMENT) or key.frame<=previous or (previous<0 and key.frame!=0):return "Invalid sequence placement key timing."
				if not key.offset is Array or key.offset.size()!=2 or not number(key.offset[0],-19200,19200) or not number(key.offset[1],-19200,19200) or not number(key.scale,.01,8) or not number(key.rotation,-36000,36000) or not number(key.opacity,0,1) or not key.interpolation in ["linear","hold","ease"]:return "Invalid sequence placement key."
				previous=int(key.frame)
	for asset in graph.assets:
		var why:=visit(asset.id,index,[])
		if not why.is_empty():return why
	if root.get("editor",{}) is Dictionary and root.get("editor",{}).has("sequence_editor"):
		var why:=context_error(root.editor.sequence_editor,graph)
		if not why.is_empty():return why
	return ""
static func shadow_error(value) -> String:
	if not value is Dictionary:return "Invalid sequence shadow."
	if value.is_empty():return ""
	if not fields(value,["offset","color","softness"]) or not value.offset is Array or value.offset.size()!=2 or not value.color is Array or value.color.size()!=4 or not number(value.softness,0,32):return "Invalid sequence shadow."
	for n in value.offset:
		if not number(n,-2048,2048):return "Sequence shadow offset exceeds2048pixels."
	for n in value.color:
		if not number(n,0,1):return "Invalid sequence shadow color."
	return ""
static func mask_error(value) -> String:
	if not value is Dictionary:return "Invalid sequence picture mask."
	if value.is_empty():return ""
	if not fields(value,["rect","invert"]) or not value.rect is Array or value.rect.size()!=4 or not value.invert is bool:return "Invalid sequence picture mask."
	var r: Array=value.rect
	if not integer(r[0],0,1919) or not integer(r[1],0,1079) or not integer(r[2],1,1920) or not integer(r[3],1,1080) or r[0]+r[2]>1920 or r[1]+r[3]>1080:return "Picture mask must be a whole-pixel rectangle inside the child canvas."
	return ""
static func context_error(value,graph: Dictionary) -> String:
	if not fields(value,["format","asset_id","frame"]) or value.format!="studio_sequence_editor_1" or not value.asset_id is String:return "Invalid sequence editor context."
	for asset in graph.get("assets",[]):
		if asset.id==value.asset_id:return "" if integer(value.frame,0,asset.scene.video.duration_frames) else "Invalid sequence editor frame."
	return "Saved sequence editor asset is missing."
static func visit(owner: String,index: Dictionary,path: Array) -> String:
	if owner in path:return "Cyclic editable sequence reference."
	if path.size()>=4:return "Editable sequence nesting exceeds4levels."
	var next:=path.duplicate();next.append(owner)
	for clip in index[owner].clips:
		var why:=visit(clip.asset_id,index,next)
		if not why.is_empty():return why
	return ""
static func local_frame(clip: Dictionary,frame: int,duration: int) -> int:
	var offset:=frame-int(clip.start)
	if offset<0 or offset>=clip.duration:return -1
	var value:=int(clip.source_in)+int(clip.time_in)+offset
	return value%duration if clip.loop else value if value<duration else -1
static func placement(clip: Dictionary,frame: int) -> Dictionary:
	var at:=frame-int(clip.start)+int(clip.key_in);var left: Dictionary=clip.keys[0];var right:=left
	for key in clip.keys:
		if key.frame<=at:left=key;right=key
		else:right=key;break
	var t:=0. if left.frame==right.frame or left.interpolation=="hold" else clampf(float(at-left.frame)/(right.frame-left.frame),0,1)
	if left.interpolation=="ease":t=t*t*(3-2*t)
	return {"offset":Vector2(left.offset[0],left.offset[1]).lerp(Vector2(right.offset[0],right.offset[1]),t),"scale":lerpf(left.scale,right.scale,t),"rotation":lerpf(left.rotation,right.rotation,t),"opacity":lerpf(left.opacity,right.opacity,t)}
static func key(frame:=0) -> Dictionary:
	return {"frame":frame,"offset":[0,0],"scale":1.0,"rotation":0.0,"opacity":1.0,"interpolation":"linear"}
