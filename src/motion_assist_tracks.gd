extends RefCounted
# Source-time adapter. Compile retained controls, never resample them into keys.
const Assist=preload("res://src/motion_assist.gd")
const Model=Assist.Model
const B=preload("res://src/body_curves.gd")
const Runtime=preload("res://src/body_curve_runtime.gd")
const T=Model.Timeline
var _tracks:={}
var _helpers:={}
var _duration:=0
var _presence:=0
var _tail:=0.
var _position_limit:=0.
var _rotation_limit:=0.

func build(data: Dictionary,ids: Array,video: Dictionary,settings: Dictionary={}) -> String:
	var validation:=Assist.new();var error:=validation.build([{"frame":0,"value":Model.identity(),"interpolation":"hold"}],video,settings)
	if not error.is_empty():return error
	if ids.is_empty() or ids.size()>513:return "Choose motion-preview parts first."
	var routed := route_edits(settings.get("track_helper_edits", {}), ids)
	if routed.has("error"):return routed.error
	var overrides=settings.get("part_strengths",{})
	if not overrides is Dictionary or overrides.size()>513:return "Invalid per-part motion strengths."
	for id in overrides:
		var amount=overrides[id]
		if not B.valid_id(id) or not (amount is int or amount is float) or not is_finite(float(amount)) or amount<0 or amount>1:return "Invalid per-part motion strength."
	var view:=B.extract(data,int(video.duration_frames))
	if view.has("error"):return view.error
	var runtime:=Runtime.new();runtime.build(view);var tracks:={};var helpers:={};var seen:={}
	var tail: float=float(video.fps_num)/float(video.fps_den)*.24
	for id in ids:
		if not B.valid_id(id) or seen.has(id):return "Invalid or duplicate motion-preview part."
		var part_settings:=settings.duplicate();part_settings.erase("track_helper_edits")
		part_settings.strength=overrides.get(id,settings.get("strength",.65))
		var remaining: Dictionary=routed.parts.get(id,{})
		seen[id]=true;tracks[id]=[];helpers[id]=[]
		var owners:=[]
		for piece in view.pieces:
			if B.owns(piece,id):owners.append(piece)
		var prepared: Array=runtime.tracks.get(id,[])
		for i in range(prepared.size()):
			var piece: Dictionary=prepared[i].duplicate();piece["piece_id"]=owners[i].id
			var keys:=[]
			for j in range(piece.frames.size()):keys.append({"frame":int(piece.frames[j]),"value":Runtime.value(piece,j,id).duplicate(true),"interpolation":Runtime.mode(piece,j)})
			piece["main"]=keys;piece["plan"]=null
			if not keys.is_empty():
				var source_video:=video.duplicate(true);source_video.duration_frames=mini(Model.Clips.MAX_SOURCE_FRAME,maxi(1,maxi(int(keys[-1].frame),int(piece.source_in)+int(piece.length)-1)+ceili(tail)))
				var plan:=Assist.new();error=plan.build_source(keys,source_video,settings_for_owner(part_settings,remaining,piece.piece_id))
				if not error.is_empty():return error
				piece.plan=plan
				for helper in plan.helper_keys():
					var frame: float=float(piece.start)+float(helper.frame)-float(piece.source_in)
					if frame<piece.start or frame>=piece.start+piece.length or frame<float(data.get("start_frame",0)) or frame>video.duration_frames:continue
					helper["source_frame"]=helper.frame;helper.frame=frame;helper["piece_id"]=piece.piece_id;helper.id=piece.piece_id+"/"+helper.id;helpers[id].append(helper)
			# Gap/lead-in plans use actual displayed endpoint values and easing.
			# Their generated offsets add to interpolation of carried slice offsets.
			var previous: Dictionary=tracks[id][-1] if not tracks[id].is_empty() else {}
			var from: int=int(previous.start)+int(previous.length)-1 if not previous.is_empty() else int(view.starts.get(id,piece.start))
			piece["bridge"]=null;piece["bridge_from"]=from
			if from<piece.start:
				var a: Dictionary=Runtime.at(previous,from,id) if not previous.is_empty() else {"value":runtime.baseline.get(id,Model.identity()),"mode":"ease"}
				var b:=Runtime.at(piece,int(piece.start),id);var mode: String=a.mode if not previous.is_empty() else b.mode
				var bridge:=Assist.new();error=bridge.build([{"frame":from,"value":a.value,"interpolation":mode},{"frame":int(piece.start),"value":b.value,"interpolation":mode}],video,settings_for_owner(part_settings,remaining,"gap/"+piece.piece_id))
				if not error.is_empty():return error
				piece.bridge=bridge
				for helper in bridge.helper_keys():
					if helper.frame<=from or helper.frame>=piece.start or helper.frame<float(data.get("start_frame",0)):continue
					helper.id="gap/"+piece.piece_id+"/"+helper.id;helper["piece_id"]=piece.piece_id;helper["connection"]=true;helpers[id].append(helper)
			tracks[id].append(piece)
		if not remaining.is_empty():return "A helper's animation clip or connecting gap has changed. Review its adjustment."
		if not tracks[id].is_empty():
			var last: Dictionary=tracks[id][-1];var end: float=float(last.start)+float(last.length)-1
			if last.plan!=null and float(last.source_in)+float(last.length)-1>=last.main[-1].frame:
				for helper in last.plan.helper_keys():
					var at: float=float(last.start)+float(helper.frame)-float(last.source_in)
					if at<last.start+last.length or at>video.duration_frames or at<float(data.get("start_frame",0)):continue
					helper["source_frame"]=helper.frame;helper.frame=at;helper["piece_id"]=last.piece_id;helper.id=last.piece_id+"/"+helper.id;helpers[id].append(helper)
			elif last.plan!=null and end+tail<=video.duration_frames and piece_offset(last,end,1.)!=Model.identity():
				helpers[id].append({"id":"trim-settle/"+last.piece_id,"frame":end+tail,"kind":"settle","drivers":[],"generated":true,"piece_id":last.piece_id})
	# No partially compiled tracks escape a failed rebuild.
	var candidate: RefCounted=get_script().new();candidate._tracks=tracks;candidate._helpers=helpers;candidate._duration=int(video.duration_frames);candidate._presence=int(data.get("start_frame",0));candidate._tail=tail;candidate._position_limit=float(settings.get("position_limit",.08));candidate._rotation_limit=float(settings.get("rotation_limit",deg_to_rad(12.)))
	for id in helpers:
		helpers[id].sort_custom(func(a,b):return a.id<b.id if a.frame==b.frame else a.frame<b.frame)
		for helper in helpers[id]:
			var original: Dictionary=runtime.channel(float(helper.frame),id) if runtime.tracks.has(id) else B.base_value(view,id)
			var value: Dictionary=candidate.apply(original,id,float(helper.frame))
			if value.has("error"):return value.error
			helper.value=value
	_tracks=tracks;_helpers=helpers;_duration=candidate._duration;_presence=candidate._presence;_tail=tail;_position_limit=candidate._position_limit;_rotation_limit=candidate._rotation_limit
	return ""

# Index once, then consume by exact owner. Multiple parts or clips can have the
# same pair of driving frames, so a bare evaluator ID is not a track address.
static func route_edits(edits, ids: Array) -> Dictionary:
	if not edits is Dictionary or edits.size()>ids.size():
		return {"error":"Invalid helper track adjustments."}
	var parts := {}
	var count := 0
	for id in edits:
		if not id in ids or not edits[id] is Dictionary:
			return {"error":"Unknown helper track."}
		var owners := {}
		for address in edits[id]:
			count += 1
			if count>4096 or not address is String:
				return {"error":"Invalid helper address."}
			var separator: int=address.rfind("/")
			if separator<=0 or separator==address.length()-1:
				return {"error":"A helper adjustment needs its clip and driving poses."}
			var owner: String=address.left(separator)
			if not owners.has(owner):owners[owner]={}
			owners[owner][address.substr(separator+1)]=edits[id][address]
		parts[id]=owners
	return {"parts":parts}

static func settings_for_owner(settings: Dictionary, remaining: Dictionary, owner: String) -> Dictionary:
	if not remaining.has(owner):return settings
	var scoped := settings.duplicate()
	# A muted part keeps its saved choices for when its amount is raised again.
	if settings.get("strength",.65)>0:scoped["helper_edits"]=remaining[owner]
	remaining.erase(owner)
	return scoped

static func difference(plan: RefCounted,main: Array,frame: float,gain: float) -> Dictionary:
	if plan==null:return Model.identity()
	if frame>plan.end_frame():return Model.identity()
	var generated: Dictionary=plan.sample(frame,gain)
	if generated.has("error"):return generated
	var base:=Assist.baseline(main,frame)
	if generated==base:return Model.identity()
	var p: Vector3=T.vector(generated.position)-T.vector(base.position);var q: Quaternion=(T.quaternion(base.rotation_xyzw).inverse()*T.quaternion(generated.rotation_xyzw)).normalized()
	return {"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}

static func piece_offset(piece: Dictionary,frame: float,gain: float) -> Dictionary:
	return difference(piece.plan,piece.main,float(piece.source_in)+frame-float(piece.start),gain)

func delta(frame: float,id: String,gain: float) -> Dictionary:
	var pieces: Array=_tracks.get(id,[])
	if gain==0 or pieces.is_empty() or frame<_presence:return Model.identity()
	var previous:={}
	for piece in pieces:
		if frame>=piece.start and frame<piece.start+piece.length:return piece_offset(piece,frame,gain)
		if frame<piece.start:
			if piece.bridge==null or frame<piece.bridge_from:return Model.identity()
			var a: Dictionary=piece_offset(previous,float(piece.bridge_from),gain) if not previous.is_empty() else Model.identity()
			var b:=piece_offset(piece,float(piece.start),gain);var pair:=Model.curve_pair(piece.bridge.main_keys(),frame)
			if a.has("error"):return a
			if b.has("error"):return b
			var carried: Dictionary=Model.blend({"d":a},{"d":b},pair.t).d
			var extra:=difference(piece.bridge,piece.bridge.main_keys(),frame,gain)
			if extra.has("error"):return extra
			var p: Vector3=T.vector(carried.position)+T.vector(extra.position);var q: Quaternion=T.quaternion(carried.rotation_xyzw)*T.quaternion(extra.rotation_xyzw)
			return {"position":[p.x,p.y,p.z],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
		previous=piece
	# Fully recorded endings keep the original generated settling tail. A trim
	# through moving source data fades its retained offset; no cropped future key
	# is allowed to pull the held final pose into further motion.
	var end: float=float(previous.start)+float(previous.length)-1
	if not previous.main.is_empty() and float(previous.source_in)+float(previous.length)-1>=previous.main[-1].frame:return piece_offset(previous,frame,gain)
	if _tail<=0 or frame>=end+_tail:return Model.identity()
	var t:=clampf((frame-end)/_tail,0.,1.);t=t*t*(3.-2.*t)
	var last:=piece_offset(previous,end,gain)
	return last if last.has("error") else Model.blend({"d":last},{"d":Model.identity()},t).d

func apply(original: Dictionary,id: String,frame: float,gain:=1.) -> Dictionary:
	if not is_finite(frame) or frame<0 or frame>_duration or not is_finite(gain) or gain<0 or gain>1:return {"error":"Invalid source-time motion-preview query."}
	var offset:=delta(frame,id,gain)
	if offset.has("error"):return offset
	if offset==Model.identity():return original
	# Carried slice offsets plus a connecting bounce share one final bound.
	var p: Vector3=T.vector(offset.position).limit_length(_position_limit)
	var rotation:=T.quaternion(offset.rotation_xyzw)
	if rotation.get_angle()>_rotation_limit:rotation=Quaternion(rotation.get_axis(),_rotation_limit)
	var q: Quaternion=(T.quaternion(original.rotation_xyzw)*rotation).normalized();p+=T.vector(original.position)
	var result:=original.duplicate(true);result.position=[p.x,p.y,p.z];result.rotation_xyzw=[q.x,q.y,q.z,q.w]
	return result if Model.transform_valid(result) else {"error":"Derived motion exceeds the supported coordinate range."}

func helper_keys() -> Dictionary:return _helpers.duplicate(true)
func parts() -> Array:return _tracks.keys()
