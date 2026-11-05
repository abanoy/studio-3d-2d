extends RefCounted
# One source-independent model contract. Native adapters supply GLB + metadata;
# instances and poses never edit that GLB or require PMD/Source-specific UI code.
const Clips=preload("res://src/animation_clips.gd")
const Visibility=preload("res://src/visibility_track.gd")
const Opacity=preload("res://src/model_opacity.gd")
const Timeline = preload("res://src/timeline.gd")
const Airflow=preload("res://src/airflow.gd")
const Shape=preload("res://src/source_shape.gd")
const ShapeAnimation=preload("res://src/shape_animation.gd")
var root: Node3D
var base_root := Transform3D.IDENTITY
var data := {}
var bones := {}
var order: Array[String] = []
var opacity_materials: RefCounted
var evaluated_opacity:=1.0
# Transient world-evaluation context for live pose updates; never serialized.
var _appearance_video: Dictionary={}
var _appearance_parent_opacity:=1.0
var preview_pose: Dictionary={}
var preview_transform: Dictionary={}
var live_world_transform=null
var live_pose=null
var preview_frame:=-1
const BODY_FORMAT:="studio_model_6"
const CONTACT_FORMAT:="studio_model_7"
const MOTION_FORMAT:="studio_model_8"
var motion_video: Dictionary={"fps_num":24,"fps_den":1,"duration_frames":240}
var _motion_source: Dictionary={}
var _motion_rate:=""
var _motion_plan: RefCounted
var _motion_error:=""
var world_context: WeakRef
var evaluation_error:=""
var contact_binding_builds:=0
var _contact_cache_ready:=false
var _contact_cache_root:=0
var _contact_cache_order: Array=[]
var _contact_cache_humanoid: Dictionary={}
var _contact_cache_rows: Array=[]
var _contact_cache_legs: Array=[]
static func is_body(value: Dictionary) -> bool:return value.get("format") in [BODY_FORMAT,CONTACT_FORMAT,MOTION_FORMAT,"studio_model_9"]
static func is_contact(value: Dictionary) -> bool:return value.get("format") in [CONTACT_FORMAT,MOTION_FORMAT] or value.get("format")=="studio_model_9" and value.get("component_base_format") in [CONTACT_FORMAT,MOTION_FORMAT]
static func motion_animation():return load("res://src/motion_animation.gd")
static func contact_animation():return load("res://src/contact_animation.gd")
static func body_animation():return load("res://src/body_animation.gd")
var _body_source: Dictionary={}
var _body_runtime: RefCounted
var _body_frame:=INF
var _body_state: Dictionary={}
var _body_authored_source: Dictionary={}
var _body_authored: Array=[]

func body_state(frame: float) -> Dictionary:
	if not _body_runtime or not is_same(_body_source,data):
		_body_source=data;_body_frame=INF
		if data.get("format")=="studio_model_9":
			_body_runtime=load("res://src/root_component_runtime.gd").new()
			var error: String=_body_runtime.configure(data,int(motion_video.duration_frames))
			if not error.is_empty():
				evaluation_error=error;_body_runtime=null
				return {"pose":{},"transform":Clips.transform(data)}
		else:_body_runtime=body_animation().compile(data)
	if _body_frame!=frame:_body_state=_body_runtime.sample(frame);_body_frame=frame
	return _body_state

static func identity() -> Dictionary:
	return {"position": [0, 0, 0], "rotation_xyzw": [0, 0, 0, 1]}

static func definition(path: String) -> Dictionary:
	return {"format": "studio_model_1", "id": str(ResourceUID.create_id()), "name": path.get_file(), "source": path, "sha256": FileAccess.get_sha256(path), "position": [0, 0, 0], "rotation_xyzw": [0, 0, 0, 1], "scale": 1.0, "visible": true, "reference_only": false, "pose": {}, "draft_frame": 0, "pose_keys": [], "metadata": {}}

static func numbers(value, count: int) -> bool:
	if not value is Array or value.size() != count: return false
	for v in value:
		if not (v is int or v is float) or not is_finite(float(v)) or absf(float(v)) > 100000: return false
	return true

static func transform_valid(value) -> bool:
	if not value is Dictionary or not numbers(value.get("position"), 3) or not numbers(value.get("rotation_xyzw"), 4): return false
	var q: Array = value.rotation_xyzw
	return Vector4(q[0], q[1], q[2], q[3]).length() > 0.001

static func pose_valid(value) -> bool:
	if not value is Dictionary or value.size() > 512: return false
	for key in value:
		if not key is String or key.length() > 512 or not transform_valid(value[key]): return false
	return true

static func scale_valid(value) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and value >= 0.001 and value <= 10000

static func validate(value, duration: int) -> String:
	if not value is Dictionary: return "Invalid model record."
	if value.is_empty(): return ""
	if value.get("format")=="studio_model_9":return load("res://src/root_component_document.gd").validate(value,duration)
	if not value.get("format") in ["studio_model_1",Clips.FORMAT,Visibility.FORMAT,ShapeAnimation.LEGACY_FORMAT,ShapeAnimation.FORMAT,BODY_FORMAT,CONTACT_FORMAT,MOTION_FORMAT] or not value.get("id") is String or not value.get("name") is String or not value.get("sha256") is String or not value.get("visible") is bool or not value.get("reference_only") is bool or not transform_valid(value): return "Invalid standard model identity/transform."
	var motion_error: String=motion_animation().validate(value)
	if not motion_error.is_empty():return motion_error
	var visibility_error:=Visibility.validate(value,duration)
	if not visibility_error.is_empty():return visibility_error
	if not scale_valid(value.get("scale")): return "Invalid model scale."
	if not pose_valid(value.get("pose")) or not value.get("metadata") is Dictionary or not value.get("pose_keys") is Array or value.pose_keys.size() > 241: return "Invalid model pose data."
	if value.metadata.has("body_pose_library"):
		var library_error: String=load("res://src/pose_library.gd").error(value.metadata.body_pose_library)
		if not library_error.is_empty():return library_error
		if value.metadata.body_pose_library.sha256!=value.sha256:return "Saved body poses belong to a different model source."
	if value.metadata.has("airflow"):
		var fan_error:=Airflow.validate(value.metadata.airflow)
		if not fan_error.is_empty():return fan_error
	if value.metadata.has("source_shape"):
		var shape_error:=Shape.validate(value.metadata.source_shape)
		if not shape_error.is_empty():return shape_error
	if not (value.get("draft_frame") is int or value.get("draft_frame") is float) or value.draft_frame != floor(value.draft_frame) or value.draft_frame < 0 or value.draft_frame > duration: return "Invalid pose draft frame."
	if Clips.has_pieces(value):
		if not integer(value.get("start_frame"),0,duration) or not value.pose_keys.is_empty() or not value.get("animation_clips") is Array or value.animation_clips.size()>Clips.MAX_CLIPS or not integer(value.get("presence_offset"),0,duration):return "Invalid animation piece ownership or presence offset."
		var ids:={};var end:=-1;var total:=0
		for piece in value.animation_clips:
			if not piece is Dictionary or not piece.get("id") is String or piece.id.is_empty() or piece.id.length()>128 or ids.has(piece.id):return "Invalid or duplicate animation piece ID."
			ids[piece.id]=true
			if not integer(piece.get("start"),0,duration) or not integer(piece.get("length"),1,duration+1) or piece.start+piece.length>duration+1 or piece.start<end:return "Invalid, overlapping or unsorted animation pieces."
			end=int(piece.start+piece.length)
			if not integer(piece.get("source_in"),0,Clips.MAX_SOURCE_FRAME) or piece.source_in+piece.length-1>Clips.MAX_SOURCE_FRAME:return "Invalid animation source range."
			if not pose_valid(piece.get("base_pose")) or not transform_valid(piece.get("base_transform")) or not scale_valid(piece.base_transform.get("scale")):return "Invalid animation piece base pose."
			var error:=validate_keys(piece.get("keys"),Clips.MAX_SOURCE_FRAME)
			if not error.is_empty():return error
			if piece.has("auto_extend") and not piece.auto_extend is bool:return "Invalid authored-piece extension flag."
			if not ShapeAnimation.independent(value) and piece.get("auto_extend",false) and (piece.source_in!=0 or piece.keys.is_empty() or piece.keys[0].frame!=0 or piece.keys[-1].frame!=piece.length-1):return "Authored piece must own its complete key range."
			total+=piece.keys.size()
		if total>Clips.MAX_TOTAL_KEYS:return "Animation pieces exceed2048 source keys."
	elif value.has("animation_clips"):return "Animation pieces require standard model version2."
	var keys_error:=validate_keys(value.pose_keys,duration)
	if not keys_error.is_empty():return keys_error
	if ShapeAnimation.independent(value) and not integer(value.get("shape_draft_frame"),0,duration):return "Invalid expression draft frame."
	if ShapeAnimation.independent(value) and value.get("shape_starts") is Dictionary:
		for node in value.shape_starts:
			if not value.shape_starts[node] is Dictionary:return "Invalid expression introduction times."
			for index in value.shape_starts[node]:
				if not integer(value.shape_starts[node][index],0,duration):return "Invalid expression introduction frame."
	var body_error: String=body_animation().validate(value,duration)
	if not body_error.is_empty():return body_error
	var shape_error:=ShapeAnimation.validate(value)
	return shape_error if not shape_error.is_empty() else contact_animation().validate(value)

static func integer(value, minimum: int, maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=minimum and value<=maximum

static func validate_keys(keys, maximum: int) -> String:
	if not keys is Array or keys.size()>241:return "Invalid or excessive model pose keys."
	var last:=-1
	for key in keys:
		if not key is Dictionary or not integer(key.get("frame"),0,maximum) or key.frame<=last or not key.get("interpolation") in ["hold","linear","ease"] or not pose_valid(key.get("pose")):return "Invalid or unsorted model pose keys."
		if key.has("authored_channels"):
			if not key.authored_channels is Array or key.authored_channels.size()>513:return "Invalid authored channel hints."
			var seen:={}
			for id in key.authored_channels:
				if not id is String or id.length()>512 or id.is_empty() or seen.has(id):return "Invalid authored channel identity."
				seen[id]=true
		if not transform_valid(key.get("transform")) or not scale_valid(key.transform.get("scale")):return "Invalid model root pose key."
		last=int(key.frame)
	return ""

func inventory(node: Node) -> void:
	if node==root:_contact_cache_ready=false
	if node is Skeleton3D:
		for i in range(node.get_bone_count()):
			var id := str(root.get_path_to(node)) + "::" + str(node.get_bone_name(i))
			bones[id] = {"skeleton": node, "index": i, "name": str(node.get_bone_name(i)), "base": node.get_bone_pose(i), "path": str(root.get_path_to(node))}
			order.append(id)
	for child in node.get_children(): inventory(child)

func contact_legs() -> Array:
	# Bone identities are immutable between inventories, but verify exact cached
	# metadata/order and the six live parent/index bindings before reusing a plan.
	var parameters=data.get("metadata",{}).get("native_parameters",{})
	var humanoid: Dictionary=parameters.get("humanoid",{}) if parameters is Dictionary and parameters.get("humanoid",{}) is Dictionary else {}
	var root_id: int=root.get_instance_id() if is_instance_valid(root) else 0
	var valid: bool=_contact_cache_ready and _contact_cache_root==root_id and _contact_cache_order==order and _contact_cache_humanoid==humanoid
	if valid:
		for saved in _contact_cache_rows:
			if not bones.has(saved.id):valid=false;break
			var info: Dictionary=bones[saved.id]
			if not is_instance_valid(info.skeleton) or info.index<0 or info.index>=info.skeleton.get_bone_count() or info.skeleton!=saved.skeleton or info.index!=saved.index or info.name!=saved.name or str(info.skeleton.get_bone_name(info.index))!=saved.name or parent_id(saved.id)!=saved.parent:valid=false;break
	if not valid:
		for id in order:
			if not bones.has(id):_contact_cache_ready=false;return []
			var info: Dictionary=bones[id]
			if not is_instance_valid(info.skeleton) or info.index<0 or info.index>=info.skeleton.get_bone_count() or str(info.skeleton.get_bone_name(info.index))!=info.name:_contact_cache_ready=false;return []
		_contact_cache_legs=contact_animation().Contacts.Hold.chains(self)
		_contact_cache_root=root_id;_contact_cache_order=order.duplicate();_contact_cache_humanoid=humanoid.duplicate(true);_contact_cache_rows=[];_contact_cache_ready=not _contact_cache_legs.is_empty();contact_binding_builds+=1
		for leg in _contact_cache_legs:
			for id in leg.ids:
				var info: Dictionary=bones[id]
				_contact_cache_rows.append({"id":id,"skeleton":info.skeleton,"index":info.index,"name":info.name,"parent":parent_id(id)})
	return _contact_cache_legs.duplicate(true)

func check_bindings() -> String:
	if data.metadata.has("body_pose_library"):
		var library_error: String=load("res://src/pose_library.gd").compatible(data.metadata.body_pose_library,self)
		if not library_error.is_empty():return library_error
	if is_body(data):
		var body_error: String=body_animation().B.check_bindings(body_animation().view(data),order)
		if not body_error.is_empty():return body_error
	if is_contact(data):
		var contact_error: String=contact_animation().check_bindings(self)
		if not contact_error.is_empty():return contact_error
	if root:
		var shape_error:=Shape.check(root,Shape.setting(data))
		if not shape_error.is_empty():return shape_error
		if ShapeAnimation.has_data(data):
			# Validate all stored amounts and a conservative union budget before an
			# edit/load replaces live state; cached target arrays are immutable.
			var union: Dictionary={}
			for values in ShapeAnimation.snapshots(data):
				var config:=ShapeAnimation.configuration(Shape.setting(data),ShapeAnimation.fill(values,data.shape_base))
				var plan:=Shape.dynamic_plan(root,config)
				if plan.has("error"):return plan.error
				for node in config.overrides:
					if not union.has(node):union[node]={}
					for index in config.overrides[node]:
						if config.overrides[node][index]!=0:union[node][index]=.000001
			var budget:=Shape.dynamic_plan(root,ShapeAnimation.configuration(Shape.setting(data),union))
			if budget.has("error"):return budget.error
	if order.size() > 512: return "Model exceeds prototype limit of 512 bones."
	var poses: Array = [data.pose]
	for key in data.pose_keys: poses.append(key.pose)
	if Clips.has_pieces(data):
		for piece in data.animation_clips:
			poses.append(piece.base_pose)
			for key in piece.keys:poses.append(key.pose)
	for pose in poses:
		for id in pose:
			if not bones.has(id): return "Stored pose refers to a missing bone: " + id
	var curves: Array=[data.pose_keys]
	if Clips.has_pieces(data):
		for piece in data.animation_clips:curves.append(piece.keys)
	for curve in curves:
		for key in curve:
			for id in key.get("authored_channels",[]):
				if id!="@root" and not bones.has(id) and not shape_channel_valid(id):return "Stored channel hint refers to a missing bone or shape: "+id
	return ""

func shape_channel_valid(id: String) -> bool:
	var parts:=id.split("/")
	return ShapeAnimation.has_data(data) and parts.size()==3 and parts[0]=="@shape" and data.shape_base.get(parts[1],{}).has(parts[2])

func sample_shapes(frame: float,editing:=false) -> Dictionary:
	return ShapeAnimation.sample(data,frame,editing)

static func blend(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var result := {}
	var ids := a.keys()
	for id in b:
		if not id in ids: ids.append(id)
	for id in ids:
		var aa: Dictionary = a.get(id, identity())
		var bb: Dictionary = b.get(id, identity())
		var p := Timeline.vector(aa.position).lerp(Timeline.vector(bb.position), t)
		var q := Timeline.quaternion(aa.rotation_xyzw).slerp(Timeline.quaternion(bb.rotation_xyzw), t)
		result[id] = {"position": [p.x, p.y, p.z], "rotation_xyzw": [q.x, q.y, q.z, q.w]}
	return result

static func curve_pair(keys: Array, frame: float) -> Dictionary:
	var a: Dictionary=keys[0];var b: Dictionary=keys[-1]
	if frame<=a.frame:b=a
	elif frame>=b.frame:a=b
	else:
		for i in range(keys.size()-1):
			if frame>=keys[i].frame and frame<keys[i+1].frame:a=keys[i];b=keys[i+1];break
	var t: float=0 if a.frame==b.frame else float(frame-a.frame)/(b.frame-a.frame)
	if a.interpolation=="hold":t=0
	elif a.interpolation=="ease":t=t*t*(3-2*t)
	return {"a":a,"b":b,"t":t}

func key_pair(frame: float) -> Dictionary:
	return curve_pair(data.pose_keys,frame)

static func curve_pose(curve: Dictionary) -> Dictionary:
	if curve["keys"].is_empty():return curve.pose.duplicate(true)
	var pair:=curve_pair(curve["keys"],float(curve.frame))
	return blend(pair.a.pose,pair.b.pose,pair.t)

static func curve_transform(curve: Dictionary) -> Dictionary:
	if curve["keys"].is_empty():return curve.transform.duplicate(true)
	var pair:=curve_pair(curve["keys"],float(curve.frame))
	return blend_transform(pair.a.transform,pair.b.transform,pair.t)

static func blend_transform(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
	var result: Dictionary=blend({"root":a},{"root":b},t).root
	result["scale"]=lerpf(a.scale,b.scale,t)
	return result

func sample(frame: float, editing := false,editing_ancestor: String="") -> Dictionary:
	evaluation_error=""
	var pose:=sample_body(frame,editing)
	if motion_enabled():
		var baseline:=sample_body(frame,false)
		var compiled:=motion_plan();var ids: Array=compiled.parts() if compiled else []
		for id in ids:
			if id=="@root":continue
			var original: Dictionary=pose.get(id,identity())
			# The draft contains the user's visible edited target. Do not add the
			# generated offset twice; unchanged draft peers still receive it once.
			if editing and data.draft_frame==frame and original!=baseline.get(id,identity()):continue
			var value:=motion_value(original,id,frame)
			if pose.has(id) or value!=original:pose[id]=value
	if not evaluation_error.is_empty() or not is_contact(data) or frame<float(data.start_frame):return pose
	var result: Dictionary=contact_animation().sample(self,frame,editing,pose,editing_ancestor)
	if evaluation_error.is_empty():evaluation_error=result.get("error","")
	return result.get("pose",pose)

func motion_enabled() -> bool:return (data.get("format")==MOTION_FORMAT or data.get("format")=="studio_model_9" and data.get("component_base_format")==MOTION_FORMAT) and data.get("motion_assist",{}).get("enabled",false)

func motion_plan() -> RefCounted:
	var runtime: RefCounted=world_context.get_ref() if world_context else null
	if runtime and runtime.video_settings.has_all(["fps_num","fps_den","duration_frames"]):motion_video={"fps_num":runtime.video_settings.fps_num,"fps_den":runtime.video_settings.fps_den,"duration_frames":runtime.video_settings.duration_frames}
	var rate: String="%s/%s/%s" % [motion_video.fps_num,motion_video.fps_den,motion_video.duration_frames]
	if not is_same(_motion_source,data) or _motion_rate!=rate:
		_motion_source=data;_motion_rate=rate;_motion_plan=null;_motion_error=""
		if data.get("format")=="studio_model_9":
			var plan: RefCounted=load("res://src/root_component_assistance.gd").new()
			_motion_error=plan.build(data,motion_video)
			if _motion_error.is_empty():_motion_plan=plan
		else:
			var compiled: Dictionary=motion_animation().compile(data,motion_video)
			_motion_error=compiled.get("error","");_motion_plan=compiled.get("plan")
	if not _motion_error.is_empty():evaluation_error=_motion_error
	return _motion_plan

func motion_value(original: Dictionary,id: String,frame: float) -> Dictionary:
	var plan:=motion_plan()
	if plan==null:return original
	var value: Dictionary=plan.apply(original,id,frame)
	if value.has("error"):evaluation_error=value.error;return original
	return value

func sample_body(frame: float, editing := false) -> Dictionary:
	if editing and data.draft_frame==frame:return data.pose.duplicate(true)
	if is_body(data):return body_state(frame).pose.duplicate(true)
	if Clips.has_pieces(data):
		var at:=Clips.location(data,frame);var a:=curve_pose(at.a)
		return a if at.t==0 else blend(a,curve_pose(at.b),at.t)
	if data.pose_keys.is_empty():return data.pose.duplicate(true)
	var pair:=key_pair(frame)
	return blend(pair.a.pose,pair.b.pose,pair.t)

func sample_transform(frame: float, editing := false) -> Dictionary:
	var original:=sample_authored_transform(frame,editing)
	if not motion_enabled():return original
	if editing and data.draft_frame==frame and original!=sample_authored_transform(frame,false):return original
	return motion_value(original,"@root",frame)

func sample_authored_transform(frame: float, editing := false) -> Dictionary:
	if editing and data.draft_frame==frame:return Clips.transform(data)
	if is_body(data):return body_state(frame).transform.duplicate(true)
	if Clips.has_pieces(data):
		var at:=Clips.location(data,frame);var a:=curve_transform(at.a)
		return a if at.t==0 else blend_transform(a,curve_transform(at.b),at.t)
	if data.pose_keys.is_empty():return Clips.transform(data)
	var pair:=key_pair(frame)
	return blend_transform(pair.a.transform,pair.b.transform,pair.t)

func authored_keys() -> Array:
	if is_body(data):
		if not is_same(_body_authored_source,data):
			_body_authored=load("res://src/root_component_document.gd").authored_keys(data,int(motion_video.duration_frames)) if data.get("format")=="studio_model_9" else body_animation().authored_keys(data)
			_body_authored_source=data
		return _body_authored.duplicate(true)
	if not Clips.has_pieces(data):return data.pose_keys
	var result: Array=[]
	for piece in data.animation_clips:
		for key in piece.keys:
			if key.frame<piece.source_in or key.frame>=piece.source_in+piece.length:continue
			var projected: Dictionary=key.duplicate(true);projected.frame=int(piece.start)+int(key.frame)-int(piece.source_in)
			result.append(projected)
	return result

func has_animation() -> bool:
	if data.get("format")=="studio_model_9":return not load("res://src/animated_channels.gd").describe(data,false).is_empty()
	if not Clips.has_pieces(data):return not data.pose_keys.is_empty()
	for piece in data.animation_clips:
		if not piece.keys.is_empty() or not piece.get("shape_keys",[]).is_empty():return true
		for id in piece.get("body_controls",{}):
			if not piece.body_controls[id].is_empty():return true
	return false

func authored_shape_keys() -> Array:return ShapeAnimation.authored_keys(data)

func put_pose_key(key: Dictionary, duration: int, include_shapes:=false,body_prior=null) -> String:
	key=key.duplicate(true)
	if data.get("format")==ShapeAnimation.LEGACY_FORMAT and not key.has("shapes"):key["shapes"]=sample_shapes(float(key.frame),true)
	var candidate:=data.duplicate(true)
	if body_prior is Dictionary or is_body(data):
		var changed: Dictionary=body_animation().put(data,key,duration,body_prior if body_prior is Dictionary else data)
		if changed.has("error"):return changed.error
		candidate=changed.data
	elif Clips.has_pieces(data):candidate=Clips.put_key(data,key,duration)
	else:
		Timeline.put_key(candidate.pose_keys,key)
		if candidate.has("start_frame"):candidate.start_frame=mini(int(candidate.start_frame),int(key.frame))
	if is_body(candidate) and include_shapes:body_animation().record_rest(candidate,int(key.frame),str(key.interpolation))
	if ShapeAnimation.independent(candidate) and include_shapes and not candidate.shape_base.is_empty():
		candidate=ShapeAnimation.put_key(candidate,{"frame":key.frame,"shapes":sample_shapes(float(key.frame),true),"interpolation":key.interpolation},duration)
	var error:=validate(candidate,duration)
	if error.is_empty():data=candidate
	return error

func remove_pose_key(frame: int, duration: int,part: String="") -> String:
	var candidate:=data.duplicate(true)
	if is_body(data) or not part.is_empty():
		var promoted: Dictionary=body_animation().promote(data,duration)
		if promoted.has("error"):return promoted.error
		var id: String="@root" if part.is_empty() else part
		if data.get("format")!="studio_model_9" and not frame in body_animation().B.frames(body_animation().view(promoted),id):return ""
		var changed: Dictionary=body_animation().remove_key(promoted,frame,id,duration)
		if changed.has("error"):return changed.error
		changed=motion_animation().after_key_removal(data,changed.data,frame,id,duration)
		if changed.has("error"):return changed.error
		candidate=changed.data
	elif Clips.has_pieces(data):candidate=Clips.delete_key(data,frame)
	else:candidate.pose_keys=candidate.pose_keys.filter(func(key):return key.frame!=frame)
	var error:=validate(candidate,duration)
	if error.is_empty():data=candidate
	return error

func visible_at(frame: int) -> bool:
	return Visibility.target(data,frame)

func apply_opacity(alpha: float,unshaded:=false) -> void:
	if not opacity_materials:
		opacity_materials=Opacity.new();opacity_materials.inventory(root)
	evaluated_opacity=alpha;opacity_materials.set_appearance(alpha,unshaded)

func apply_current(frame: int, editing := false) -> void:
	apply(frame,editing,false,_appearance_video,_appearance_parent_opacity)

func apply(frame: int, editing := false, final := false, video: Dictionary = {}, parent_opacity := 1.0,editing_ancestor: String="") -> void:
	_appearance_video=video;_appearance_parent_opacity=parent_opacity
	if video.has("fps_num") and video.has("fps_den") and video.has("duration_frames"):motion_video={"fps_num":video.fps_num,"fps_den":video.fps_den,"duration_frames":video.duration_frames}
	if ShapeAnimation.has_data(data):Shape.apply_dynamic(root,Shape.setting(data),sample_shapes(frame,editing))
	else:Shape.apply(root,Shape.setting(data))
	var transform := sample_transform(frame, editing)
	if not final and preview_frame==frame and not preview_transform.is_empty():transform=preview_transform
	root.transform = Transform3D(Basis(Timeline.quaternion(transform.rotation_xyzw)).scaled(Vector3.ONE * transform.scale), Timeline.vector(transform.position)) * base_root
	if not final and live_world_transform is Transform3D:root.global_transform=live_world_transform
	var alpha:=Visibility.opacity(data,frame,video)*parent_opacity
	apply_opacity(alpha,video.get("lighting_mode")=="unshaded")
	root.visible = alpha>0 and not (final and data.reference_only) and (not Clips.has_pieces(data) or not data.animation_clips.is_empty() and frame>=int(data.start_frame))
	evaluation_error=""
	var pose := sample_body(frame,editing) if not final and live_pose is Dictionary else sample(frame,editing,editing_ancestor if not final else "")
	if not final and preview_frame==frame:pose=preview_pose
	if not final and live_pose is Dictionary:pose=live_pose
	for id in order:
		var info: Dictionary = bones[id]
		var base: Transform3D = info.base
		var delta: Dictionary = pose.get(id, identity())
		info.skeleton.set_bone_pose_position(info.index, base.origin + Timeline.vector(delta.position))
		info.skeleton.set_bone_pose_rotation(info.index, base.basis.get_rotation_quaternion() * Timeline.quaternion(delta.rotation_xyzw))
		info.skeleton.set_bone_pose_scale(info.index, base.basis.get_scale())
	var updated := []
	for id in order:
		var skeleton: Skeleton3D = bones[id].skeleton
		if not skeleton in updated:
			skeleton.force_update_all_bone_transforms()
			updated.append(skeleton)

func bone_transform(id: String) -> Transform3D:
	if id == "@root": return root.global_transform
	var info: Dictionary = bones[id]
	return info.skeleton.global_transform * info.skeleton.get_bone_global_pose(info.index)

func parent_id(id: String) -> String:
	var info: Dictionary = bones[id]
	var parent: int = info.skeleton.get_bone_parent(info.index)
	return "@root" if parent < 0 else info.path + "::" + str(info.skeleton.get_bone_name(parent))
