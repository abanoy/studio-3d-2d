extends RefCounted
# Immutable per-revision indexes. Untouched legacy parts share compact frame arrays.
const B=preload("res://src/body_curves.gd")
var tracks:={}
var baseline:={}
var starts:={}

func build(data: Dictionary) -> void:
	starts=data.starts
	var ids:=B.known_channels(data)
	for id in ids:tracks[id]=[];baseline[id]=B.base_value(data,id)
	for piece in data.pieces:
		var legacy_frames:=PackedInt32Array();var legacy_indices:=PackedInt32Array()
		for i in range(piece.keys.size()):legacy_frames.append(int(piece.keys[i].frame));legacy_indices.append(i)
		for id in ids:
			if not B.owns(piece,id):continue
			var legacy: bool=id in piece.legacy_channels;var controls: Array=piece.controls.get(id,[])
			var frames:=legacy_frames if legacy else PackedInt32Array();var indices:=legacy_indices if legacy else PackedInt32Array()
			var removed: Array=piece.removed.get(id,[])
			var rest: Array=piece.get("rest_keys",[])
			if not controls.is_empty() or not removed.is_empty() or not rest.is_empty():
				var map:={}
				for i in range(rest.size()):map[int(rest[i].frame)]=-100001-i
				if legacy:
					for i in range(legacy_frames.size()):map[legacy_frames[i]]=i
				for i in range(controls.size()):map[int(controls[i].frame)]=-i-1
				for frame in removed:map.erase(int(frame))
				var ordered: Array=map.keys();ordered.sort();frames=PackedInt32Array();indices=PackedInt32Array()
				for frame in ordered:frames.append(int(frame));indices.append(int(map[frame]))
			var prepared:={"start":int(piece.start),"length":int(piece.length),"source_in":int(piece.source_in),"keys":piece.keys,"controls":controls,"rest":rest,"frames":frames,"indices":indices,"base":B.piece_base(data,piece,id),"virtual_mode":"ease"}
			if not legacy and not frames.is_empty() and piece.origin<frames[0]:
				prepared.virtual_mode=mode(prepared,0);prepared.frames=frames.duplicate();prepared.indices=indices.duplicate()
				prepared.frames.insert(0,int(piece.origin));prepared.indices.insert(0,-100000)
			if piece.get("untrimmed",false) and not prepared.frames.is_empty():
				var first:=maxi(int(piece.source_in),int(prepared.frames[0]));var last:=mini(int(piece.source_in)+int(piece.length)-1,int(prepared.frames[-1]))
				if first<=last:prepared.start=int(piece.start)+first-int(piece.source_in);prepared.source_in=first;prepared.length=last-first+1
			tracks[id].append(prepared)

static func mode(piece: Dictionary,index: int) -> String:
	var source: int=piece.indices[index]
	if source<-100000:return str(piece.rest[-source-100001].interpolation)
	return piece.virtual_mode if source==-100000 else str(piece.keys[source].interpolation) if source>=0 else str(piece.controls[-source-1].interpolation)

static func value(piece: Dictionary,index: int,id: String) -> Dictionary:
	var source: int=piece.indices[index]
	if source<=-100000:return piece.base
	if source<0:return piece.controls[-source-1].value
	return piece.keys[source].transform if id=="@root" else piece.keys[source].pose.get(id,B.Model.identity())

static func at(piece: Dictionary,frame: float,id: String) -> Dictionary:
	var frames: PackedInt32Array=piece.frames
	if frames.is_empty():return {"value":piece.base.duplicate(true),"mode":"ease"}
	var source:=float(piece.source_in)+frame-float(piece.start)
	var a:=0;var b:=frames.size()-1
	if source<=frames[0]:b=0
	elif source>=frames[-1]:a=b
	else:
		var low:=0;var high:=frames.size()
		while low<high:
			var middle: int=(low+high)/2
			if frames[middle]<=source:low=middle+1
			else:high=middle
		a=low-1;b=low
	var t:=0. if a==b else float(source-frames[a])/float(frames[b]-frames[a])
	return {"value":B.blend(value(piece,a,id),value(piece,b,id),B.easing(t,mode(piece,a)),id),"mode":"ease" if source<frames[0] else mode(piece,a)}

func channel(frame: float,id: String) -> Dictionary:
	var pieces: Array=tracks[id]
	if pieces.is_empty():return baseline[id].duplicate(true)
	if frame<pieces[0].start:
		var first:=at(pieces[0],float(pieces[0].start),id)
		if starts.has(id) and pieces[0].start>starts[id]:
			var t:=clampf(float(frame-starts[id])/float(pieces[0].start-starts[id]),0,1)
			return B.blend(baseline[id],first.value,B.easing(t,first.mode),id)
		return first.value
	var previous: Dictionary=pieces[0]
	for piece in pieces:
		if frame>=piece.start and frame<piece.start+piece.length:return at(piece,frame,id).value
		if piece.start>frame:
			var last: int=previous.start+previous.length-1
			var a:=at(previous,last,id);var b:=at(piece,float(piece.start),id)
			return B.blend(a.value,b.value,B.easing(float(frame-last)/float(piece.start-last),a.mode),id)
		previous=piece
	return at(previous,int(previous.start)+int(previous.length)-1,id).value

func sample(frame: float) -> Dictionary:
	var pose:={}
	for id in tracks:
		if id!="@root":pose[id]=channel(frame,id)
	return {"pose":pose,"transform":channel(frame,"@root")}
