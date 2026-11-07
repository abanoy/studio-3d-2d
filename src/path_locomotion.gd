extends RefCounted
# Bounded flat walking evaluator. Authored movement/facing stay authoritative.
# Sampling borrows a rig for IK; generated poses never replace source keys.
const Model=preload("res://src/model.gd")
const Paths=preload("res://src/movement_path.gd")
const Feet=preload("res://src/foot_contacts.gd")
const Hold=preload("res://src/foot_hold.gd")
const T=Model.Timeline
const DEFAULTS={"stride":.36,"lift":.08,"lowering":.03}
var _actor: WeakRef
var _source: Dictionary={}
var _probe: RefCounted
var _root_id:=0
var _order: Array=[]
var _bindings: Array=[]
var _lower: Array=[]
var _ramp_frames:=1.
const DRAFT_FIELDS=["pose","position","rotation_xyzw","scale","draft_frame","shape_pose","shape_draft_frame"]
var _root_base:=Transform3D.IDENTITY
var _parent:=Transform3D.IDENTITY
var _feet: Array=[]
var _start:=0
var _end:=0
var _origin:=Vector3.ZERO
var _direction:=Vector3.ZERO
var _length:=0.
var _route: Array=[]
var _straight:=true
var _turning:=false
var _first_rotation:=Quaternion.IDENTITY
var _pivot:=Vector3.ZERO
var _stride:=0.
var _lift:=0.
var _lowering:=0.
var _last_frame:=INF
var _last_amount:=-1.
var _last: Dictionary={}

static func settings_error(settings: Dictionary) -> String:
	for key in settings:
		if not DEFAULTS.has(key):return "Unknown walking correction."
	for key in DEFAULTS:
		var value=settings.get(key,DEFAULTS[key])
		if not (value is int or value is float) or not is_finite(float(value)):return "Walking corrections must be finite numbers."
	if settings.get("stride",.36)<.1 or settings.get("stride",.36)>.6 or settings.get("lift",.08)<0 or settings.get("lift",.08)>.15 or settings.get("lowering",.03)<0 or settings.get("lowering",.03)>.12:return "Walking corrections exceed this prototype's bounds."
	return ""

func build(actor: RefCounted,data: Dictionary,video: Dictionary,settings: Dictionary={}) -> String:
	var staged=load("res://src/path_locomotion.gd").new();var error: String=staged._build(actor,data,video,settings)
	if not error.is_empty():return error
	# Only a fully checked plan replaces an earlier usable experiment.
	for field in ["_actor","_source","_probe","_root_id","_order","_bindings","_lower","_ramp_frames","_root_base","_parent","_feet","_start","_end","_origin","_direction","_length","_route","_straight","_turning","_first_rotation","_pivot","_stride","_lift","_lowering"]:set(field,staged.get(field))
	_last={};_last_frame=INF;_last_amount=-1.;return ""

func _build(actor: RefCounted,data: Dictionary,video: Dictionary,settings: Dictionary,structure_only:=false) -> String:
	var why:=settings_error(settings)
	if not why.is_empty():return why
	if actor==null or not is_instance_valid(actor.root) or not structure_only and not actor.root.is_inside_tree():return "Walking needs a live supported model."
	if not Model.integer(video.get("duration_frames"),1,240):return "This walking experiment supports up to240frames."
	why=preload("res://src/video_timing.gd").error(video.get("fps_num"),video.get("fps_den"))
	if not why.is_empty():return why
	why=Model.validate(data,int(video.duration_frames))
	if not why.is_empty():return why
	if data.get("id")!=actor.data.get("id") or data.get("sha256")!=actor.data.get("sha256"):return "Walking candidate belongs to another model."
	if not str(data.get("parent_id","")).is_empty():return "This walking experiment needs an ungrouped character."
	var legs: Array=actor.contact_legs()
	if legs.size()!=2:return "Walking needs two validated leg chains. Use manual posing for this rig."
	for piece in data.get("animation_clips",[]):
		if not piece.get("foot_contacts",{}).get("segments",[]).is_empty():return "Release planted-foot ranges before trying walking."
	var lower: Array=[]
	for limb in legs:
		for id in limb.ids:
			if not lower.has(id):lower.append(id)
		var ancestor: String=actor.parent_id(limb.ids[0])
		while ancestor!="@root":
			if not lower.has(ancestor):lower.append(ancestor)
			ancestor=actor.parent_id(ancestor)
	var body: Dictionary=Model.body_animation().B.extract(data,int(video.duration_frames))
	if body.has("error"):return body.error
	var authored: Array=Model.body_animation().B.known_channels(body);var first_frame:=int(data.get("start_frame",0))
	for id in lower:
		if not authored.has(id) and not data.pose.has(id):continue
		# A neutral starting pose is common after Reset pose. Keep that exact
		# anchor and ease into the suggestion; later/nonneutral keys stay protected.
		if not neutral(Model.body_animation().B.sample_channel(body,first_frame,id)) or data.pose.has(id) and not neutral(data.pose[id]):return "Walking needs neutral starting legs and no later leg/hip keys. Keep your keys and use manual motion, or try a neutral practice figure."
		for piece in body.pieces:
			for point in Model.body_animation().B.points(body,piece,id,false):
				if int(piece.start)+int(point.frame)-int(piece.source_in)!=first_frame or not neutral(point.value):return "Walking will not replace later or nonneutral leg/hip keys. Turn walking off to edit those poses."
	_actor=weakref(actor);_root_id=actor.root.get_instance_id();_order=actor.order.duplicate();_source=actor.data.duplicate(true);_lower=lower.duplicate()
	if _source.get("format")=="studio_model_9":
		for field in DRAFT_FIELDS:_source.erase(field)
	_root_base=actor.base_root
	for id in _order:
		var bone: Dictionary=actor.bones[id];_bindings.append({"id":id,"skeleton":weakref(bone.skeleton),"index":int(bone.index),"name":str(bone.name),"base":bone.base,"parent":bone.skeleton.get_bone_parent(bone.index)})
	_parent=actor.root.get_parent().global_transform if actor.root.is_inside_tree() and actor.root.get_parent() is Node3D else Transform3D.IDENTITY
	if not Hold.IK.regular(_parent.basis) or _parent.basis.y.normalized().dot(Vector3.UP)<.99999:return "Walking needs a positive uniform, upright parent transform."
	_probe=Model.new();_probe.data=data.duplicate(true);_probe.motion_video=video.duplicate(true);_start=int(data.get("start_frame",0));_end=int(video.duration_frames)
	_ramp_frames=maxf(1.,minf(float(video.fps_num)/float(video.fps_den)*.15,float(_end-_start)/2.))
	var first: Dictionary=_probe.sample_authored_transform(_start);var last: Dictionary=_probe.sample_authored_transform(_end)
	_origin=T.vector(first.position);var delta: Vector3=_parent.basis*(T.vector(last.position)-_origin);_length=delta.length()
	if _length<.0001 or absf(delta.y)>.0001:return "Walking needs a moving flat path."
	_direction=delta.normalized();_first_rotation=T.quaternion(first.rotation_xyzw);_pivot=_parent*_origin
	var previous:=0.
	for point in Paths.controls(data):
		if point.mode=="hold":
			var later: Array=Paths.controls(data).filter(func(value):return value.frame>point.frame)
			if not later.is_empty() and later[0].position!=point.position:return "Walking does not infer steps across a Hold jump."
	var rotations: Array=Paths.Components.controls(data).filter(func(point):return point.components.has("rotation_xyzw")) if data.get("format")=="studio_model_9" else []
	if data.get("format")!="studio_model_9":
		for point in Paths.controls(data):rotations.append({"frame":point.frame,"components":{"rotation_xyzw":point.mode}})
	for i in range(rotations.size()-1):
		if rotations[i].components.rotation_xyzw=="hold" and absf(T.quaternion(_probe.sample_authored_transform(rotations[i].frame).rotation_xyzw).dot(T.quaternion(_probe.sample_authored_transform(rotations[i+1].frame).rotation_xyzw)))<.999999:return "Walking cannot plant feet across a Hold turn. Use a smooth turn or disable walking."
	var transforms:=[];var last_offset:=Vector3.ZERO;var travelled:=0.;var last_turn:=Quaternion.IDENTITY;var stopped_turn:=0.
	for half in range(_start*2,_end*2+1):
		var at:=float(half)/2.;var value: Dictionary=_probe.sample_authored_transform(at);var offset: Vector3=_parent.basis*(T.vector(value.position)-_origin);var distance:=offset.dot(_direction)
		if absf(float(value.scale)-float(first.scale))>.000001:return "Walking needs a fixed scale; author size changes separately for now."
		var turn:=relative_turn(value.rotation_xyzw)
		if turn.dot(last_turn)<0:turn=Quaternion(-turn.x,-turn.y,-turn.z,-turn.w)
		if Basis(turn).y.dot(Vector3.UP)<.99999:return "Walking supports upright yaw turns, not changing root tilt."
		if absf(turn.dot(last_turn))<cos(deg_to_rad(5.)/2.):return "Slow down the authored turn before trying walking."
		var changed_turn: bool=Vector3(turn.x-last_turn.x,turn.y-last_turn.y,turn.z-last_turn.z).length()>.000001
		# Component clip boundaries can dwell for one frame. Keep stance fixed
		# through that authored pause, but do not invent a stationary turn cycle.
		stopped_turn=stopped_turn+.5 if changed_turn and offset.distance_to(last_offset)<.0000001 else 0.
		if stopped_turn>1.:return "Walking needs travel during a turn at frame "+str(at)+"; use manual posing for a pivot in place."
		if Vector3(turn.x,turn.y,turn.z).length()>.000001:_turning=true
		if absf(offset.y)>.0001 or distance<previous-.00001:return "Walking needs a flat path without reversals."
		if (offset-_direction*distance).length()>.0001:_straight=false
		travelled+=offset.distance_to(last_offset);_route.append({"distance":travelled,"offset":offset,"turn":turn});last_offset=offset;last_turn=turn
		previous=distance;transforms.append(value)
	if not _straight:_length=travelled
	if structure_only:return ""
	var state:=capture_state(actor);var value: Dictionary=first
	actor.root.transform=Transform3D(Basis(T.quaternion(value.rotation_xyzw)).scaled(Vector3.ONE*value.scale),T.vector(value.position))*actor.base_root;Feet.apply_pose(actor,_probe.sample_body(_start))
	var captured:=Hold.capture(actor,"@root");var leg_length:=INF
	if not captured.has("error"):
		for limb in legs:
			var a: Vector3=actor.bone_transform(limb.ids[0]).origin;var b: Vector3=actor.bone_transform(limb.ids[1]).origin;var c: Vector3=actor.bone_transform(limb.ids[2]).origin;leg_length=minf(leg_length,a.distance_to(b)+b.distance_to(c))
	restore_state(actor,state)
	if captured.has("error"):return captured.error
	if not is_finite(leg_length) or leg_length<.0001:return "Walking needs nonzero leg lengths."
	_feet=captured.feet;_stride=leg_length*float(settings.get("stride",.36));_lift=leg_length*float(settings.get("lift",.08));_lowering=leg_length*float(settings.get("lowering",.03))
	if _length/_stride>64:return "This walking experiment supports up to64strides. Shorten the path or increase stride."
	previous=0.
	for i in range(transforms.size()):
		var distance: float=_route[i].distance if not _straight else (_parent.basis*(T.vector(transforms[i].position)-_origin)).dot(_direction)
		if distance-previous>_stride*.5:return "Slow down the path or shorten it before trying walking."
		previous=distance
	for half in range(_start*2,_end*2+1):
		var sampled:=sample(float(half)/2.)
		if sampled.has("error"):return sampled.error+" At frame "+str(float(half)/2.)+". Reduce stride/lift or adjust lowering."
	return ""

static func capture_state(actor: RefCounted) -> Dictionary:
	var bones:=[];var skeletons: Array=[]
	for id in actor.order:
		var bone: Dictionary=actor.bones[id];bones.append([bone.skeleton.get_bone_pose_position(bone.index),bone.skeleton.get_bone_pose_rotation(bone.index),bone.skeleton.get_bone_pose_scale(bone.index)])
		if not skeletons.has(bone.skeleton):skeletons.append(bone.skeleton)
	return {"root":actor.root.transform,"bones":bones,"skeletons":skeletons}
static func restore_state(actor: RefCounted,state: Dictionary) -> void:
	actor.root.transform=state.root
	for i in range(actor.order.size()):
		var bone: Dictionary=actor.bones[actor.order[i]];bone.skeleton.set_bone_pose_position(bone.index,state.bones[i][0]);bone.skeleton.set_bone_pose_rotation(bone.index,state.bones[i][1]);bone.skeleton.set_bone_pose_scale(bone.index,state.bones[i][2])
	for skeleton in state.skeletons:skeleton.force_update_all_bone_transforms()

static func neutral(value: Dictionary) -> bool:
	return T.vector(value.position).length()<.000001 and absf(T.quaternion(value.rotation_xyzw).dot(Quaternion.IDENTITY))>.999999

func source_matches(data: Dictionary) -> bool:
	if _source.get("format")!="studio_model_9":return data==_source
	var count:=0
	for field in data:
		if field in DRAFT_FIELDS:continue
		if not _source.has(field) or data[field]!=_source[field]:return false
		count+=1
	return count==_source.size()

func draft_conflict(frame: float) -> bool:
	var actor=_actor.get_ref() if _actor!=null else null
	if actor==null or actor.data.get("draft_frame",-1)!=frame:return false
	var baseline: Dictionary=_probe.sample_body(frame)
	for id in _lower:
		if actor.data.pose.get(id,Model.identity())!=baseline.get(id,Model.identity()):return true
	var shown:=Model.Clips.transform(actor.data);var authored: Dictionary=_probe.sample_authored_transform(frame)
	return T.vector(shown.position).distance_to(T.vector(authored.position))>.000001 or absf(T.quaternion(shown.rotation_xyzw).dot(T.quaternion(authored.rotation_xyzw)))<.999999 or absf(float(shown.scale)-float(authored.scale))>.000001

# Position interpolation follows the authored route exactly within each half-frame
# interval. Arc length controls phase; feet stay fixed during stance. Extending the
# last tangent keeps the last partial step identical to straight-route behavior.
func distance_at(frame: float) -> float:
	var offset: Vector3=_parent.basis*(T.vector(_probe.sample_authored_transform(frame).position)-_origin)
	if _straight:return offset.dot(_direction)
	var index:=clampi(int(floor((frame-_start)*2.)),0,_route.size()-1)
	return float(_route[index].distance)+offset.distance_to(_route[index].offset)

func path_offset(distance: float) -> Vector3:
	if _straight:return _direction*distance
	for i in range(1,_route.size()):
		var a: Dictionary=_route[i-1];var b: Dictionary=_route[i];var span: float=b.distance-a.distance
		if span>.00000001 and distance<=b.distance:return a.offset.lerp(b.offset,clampf((distance-a.distance)/span,0,1))
	for i in range(_route.size()-1,0,-1):
		var delta: Vector3=_route[i].offset-_route[i-1].offset
		if delta.length()>.00000001:return _route[-1].offset+delta.normalized()*maxf(0,distance-_length)
	return Vector3.ZERO

func relative_turn(rotation: Array) -> Quaternion:
	var parent_rotation:=_parent.basis.get_rotation_quaternion()
	return (parent_rotation*T.quaternion(rotation)*_first_rotation.inverse()*parent_rotation.inverse()).normalized()

func turn_at(distance: float) -> Quaternion:
	for i in range(1,_route.size()):
		var a: Dictionary=_route[i-1];var b: Dictionary=_route[i];var span: float=b.distance-a.distance
		if span>.00000001 and distance<=b.distance:return a.turn.slerp(b.turn,clampf((distance-a.distance)/span,0,1))
	return _route[-1].turn

func sample(frame: float,amount:=1.) -> Dictionary:
	if _actor==null:return {"error":"Build a walking plan first."}
	var actor=_actor.get_ref()
	if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree() or actor.root.get_instance_id()!=_root_id or actor.order!=_order or not source_matches(actor.data):return {"error":"The walking model changed; rebuild the suggestion."}
	if actor.base_root!=_root_base:return {"error":"The walking model binding changed; rebuild the suggestion."}
	for saved in _bindings:
		if not actor.bones.has(saved.id):return {"error":"A walking bone disappeared; rebuild the suggestion."}
		var bone: Dictionary=actor.bones[saved.id];var skeleton=saved.skeleton.get_ref()
		if skeleton==null or not is_instance_valid(skeleton) or bone.skeleton!=skeleton or bone.index!=saved.index or bone.name!=saved.name or bone.base!=saved.base or saved.index<0 or saved.index>=skeleton.get_bone_count() or skeleton.get_bone_name(saved.index)!=saved.name or skeleton.get_bone_parent(saved.index)!=saved.parent:return {"error":"A walking bone binding changed; rebuild the suggestion."}
	var parent: Transform3D=actor.root.get_parent().global_transform if actor.root.get_parent() is Node3D else Transform3D.IDENTITY
	if parent!=_parent:return {"error":"The walking parent changed; rebuild the suggestion."}
	if not is_finite(frame) or frame<_start or frame>_end or not is_finite(amount) or amount<0 or amount>1:return {"error":"Invalid walking frame or amount."}
	if frame==_last_frame and amount==_last_amount:return _last.duplicate(true)
	var requested:=amount
	var ramp:=clampf((frame-float(_start))/_ramp_frames,0,1);amount*=ramp*ramp*(3.-2.*ramp)
	var transform: Dictionary=_probe.sample_authored_transform(frame);var pose: Dictionary=_probe.sample_body(frame)
	var distance:=distance_at(frame);var offset: Vector3=_parent.basis*(T.vector(transform.position)-_origin);var targets:=[]
	for side in range(2):
		var foot: Dictionary=_feet[side];var shift:=float(side)*.5;var q:=distance/_stride+shift;var cycle:=floorf(q);var phase:=q-cycle;var previous:=maxf(0,(cycle-shift)*_stride);var following:=(cycle+1-shift)*_stride;var at:=previous;var height:=0.
		if phase>=.5:
			var u:=(phase-.5)*2.;at=lerpf(previous,following,u*u*(3.-2.*u));height=sin(PI*u)*_lift
		var rest: Vector3=foot.position+offset;var landing: Vector3=foot.position+path_offset(at)+Vector3.UP*height;var rotation: Quaternion=foot.rotation
		if _turning:
			var current_turn:=relative_turn(transform.rotation_xyzw);var from_turn:=turn_at(previous);var to_turn:=turn_at(following);var swing:=0.
			if phase>=.5:
				var u:=(phase-.5)*2.;swing=u*u*(3.-2.*u)
			var landing_turn:=from_turn.slerp(to_turn,swing)
			rest=_pivot+offset+current_turn*(foot.position-_pivot)
			landing=_pivot+path_offset(at)+landing_turn*(foot.position-_pivot)+Vector3.UP*height
			rotation=(current_turn*foot.rotation).slerp(landing_turn*foot.rotation,amount)
		var target: Vector3=rest.lerp(landing,amount)
		targets.append({"ids":foot.limb.ids.duplicate(),"position":[target.x,target.y,target.z],"rotation_xyzw":[rotation.x,rotation.y,rotation.z,rotation.w]})
	transform=transform.duplicate(true);transform.position[1]-=_lowering*amount/_parent.basis.y.length()
	if amount==0:
		_last={"pose":pose,"transform":transform,"targets":targets};_last_frame=frame;_last_amount=requested;return _last.duplicate(true)
	var state:=capture_state(actor);actor.root.transform=Transform3D(Basis(T.quaternion(transform.rotation_xyzw)).scaled(Vector3.ONE*transform.scale),T.vector(transform.position))*actor.base_root
	var solved:=Feet.resolve(actor,pose,{"id":"walking-preview","from":0,"to":_end+1,"feet":targets});restore_state(actor,state)
	if solved.has("error"):return solved
	_last={"pose":solved.pose,"transform":transform,"targets":targets};_last_frame=frame;_last_amount=requested;return _last.duplicate(true)
