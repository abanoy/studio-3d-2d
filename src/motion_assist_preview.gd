extends "res://src/model.gd"
# Separate, read-only experiment: derived offsets enter BEFORE the standard
# contact solve. Normal project sampling, storage and editor controls are unchanged.
const Assist=preload("res://src/motion_assist.gd")
var _source: RefCounted
var _plans: Dictionary={}
var gain:=1.
var _duration:=0
var _document_plan: RefCounted
var _preview_error:=""

func configure_document(actor: RefCounted,ids: Array,video: Dictionary,settings: Dictionary={}) -> String:
	if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return "Motion preview needs a live model."
	for id in ids:
		if not id is String or id!="@root" and not actor.bones.has(id):return "Motion preview refers to an unavailable part."
	var plan:=preload("res://src/motion_assist_tracks.gd").new();var error: String=plan.build(actor.data,ids,video,settings)
	if not error.is_empty():return error
	_source=actor;_plans={};_document_plan=plan;data=actor.data.duplicate(true);root=actor.root;base_root=actor.base_root;bones=actor.bones;order=actor.order.duplicate();world_context=actor.world_context;_duration=int(video.duration_frames)
	return ""

func configure(actor: RefCounted,tracks: Dictionary,video: Dictionary,settings: Dictionary={}) -> String:
	if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree():return "Motion preview needs a live model."
	if tracks.is_empty() or tracks.size()>513:return "Choose motion-preview parts first."
	var plans:={}
	for id in tracks:
		if not id is String or id!="@root" and not actor.bones.has(id):return "Motion preview refers to an unavailable part."
		var plan:=Assist.new();var error:=plan.build(tracks[id],video,settings)
		if not error.is_empty():return error
		for key in plan.main_keys():
			var original: Dictionary=actor.sample_transform(float(key.frame)) if id=="@root" else actor.sample_body(float(key.frame)).get(id,identity())
			if key.value!=original:return "Motion preview main keys must match the authored part."
		# This first adapter accepts a complete, matching curve only. Reject a
		# caller that omitted an intervening control or mislabelled a Hold/ease.
		# Do not infer sparse clip ownership from just its endpoint values.
		var main: Array=plan.main_keys()
		for half in range(int(video.duration_frames)*2+1):
			var at:=float(half)/2;var authored: Dictionary=actor.sample_transform(at) if id=="@root" else actor.sample_body(at).get(id,identity())
			if not matching(authored,Assist.baseline(main,at)):return "Motion preview needs the complete original part curve, including Holds and intermediate keys."
		plans[id]=plan
	# Keep a separate data snapshot and only borrow the live skeleton for the
	# existing read-only solver, which restores every temporary transform.
	_source=actor;_plans=plans;_document_plan=null;data=actor.data.duplicate(true);root=actor.root;base_root=actor.base_root;bones=actor.bones;order=actor.order.duplicate();world_context=actor.world_context;_duration=int(video.duration_frames)
	return ""

static func matching(a: Dictionary,b: Dictionary) -> bool:
	return Timeline.vector(a.position).distance_to(Timeline.vector(b.position))<.000001 and absf(Timeline.quaternion(a.rotation_xyzw).dot(Timeline.quaternion(b.rotation_xyzw)))>1.-.000001 and absf(float(a.get("scale",1.))-float(b.get("scale",1.)))<.000001

func evaluate_preview(frame: float) -> Dictionary:
	if _source==null or not is_instance_valid(root) or root!=_source.root or not root.is_inside_tree():return {"error":"Motion preview needs to be rebuilt for this model."}
	if _source.data!=data:return {"error":"The main animation changed; rebuild its generated helpers."}
	if not is_finite(frame) or frame<0 or frame>_duration or not is_finite(gain) or gain<0 or gain>1:return {"error":"Invalid motion-preview frame or strength."}
	_preview_error="";var pose:=sample(frame);var transform:=sample_transform(frame)
	if not _preview_error.is_empty():return {"error":_preview_error}
	if not evaluation_error.is_empty():return {"error":evaluation_error}
	return {"pose":pose,"transform":transform}

func offset(original: Dictionary,id: String,frame: float) -> Dictionary:
	if _document_plan:
		var value: Dictionary=_document_plan.apply(original,id,frame,gain)
		if value.has("error"):_preview_error=value.error;return original
		return value
	if not _plans.has(id) or gain==0:return original
	var plan: RefCounted=_plans[id];var generated: Dictionary=plan.sample(frame,gain)
	if generated.has("error"):_preview_error=generated.error;return original
	var baseline: Dictionary=Assist.baseline(plan.main_keys(),frame)
	# Leave all existing source-slice/gap interpolation and unrelated channels
	# intact. Only the generated translation/rotation DIFFERENCE is applied.
	if generated==baseline:return original
	var value:=original.duplicate(true)
	var p: Vector3=Timeline.vector(original.position)+Timeline.vector(generated.position)-Timeline.vector(baseline.position)
	var q: Quaternion=(Timeline.quaternion(original.rotation_xyzw)*Timeline.quaternion(baseline.rotation_xyzw).inverse()*Timeline.quaternion(generated.rotation_xyzw)).normalized()
	value.position=[p.x,p.y,p.z];value.rotation_xyzw=[q.x,q.y,q.z,q.w]
	return value

func sample_body(frame: float,editing:=false) -> Dictionary:
	var pose: Dictionary=_source.sample_body(frame,editing)
	for id in (_document_plan.parts() if _document_plan else _plans.keys()):
		if id=="@root":continue
		var original: Dictionary=pose.get(id,identity());var value:=offset(original,id,frame)
		if pose.has(id) or value!=original:pose[id]=value
	return pose

func sample_transform(frame: float,editing:=false) -> Dictionary:
	return offset(_source.sample_transform(frame,editing),"@root",frame)

func helper_keys() -> Dictionary:
	if _document_plan:return _document_plan.helper_keys()
	var result:={}
	for id in _plans:result[id]=_plans[id].helper_keys()
	return result
