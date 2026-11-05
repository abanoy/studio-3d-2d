extends SceneTree
const Motion=preload("res://src/root_component_motion.gd")
const D=Motion.D
const Model=D.Model
func _initialize() -> void:
	var model:=Model.definition("res://project.godot")
	for at in [0,24,48]:
		var value:=Model.identity();value["scale"]=1.+float(at)/48.;value.position=[sin(float(at)/16.),0.,0.];var q:=Quaternion(Vector3.UP,float(at)/48.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
		model.pose_keys.append({"frame":at,"pose":{},"transform":value,"interpolation":"ease"})
	var edited:=D.put_component(model,12,"position",[.1,.2,.3],"ease",48);var data: Dictionary=edited.data;var baseline:=D.compile(data,48);var motion:=Motion.new();var failures:=0;var checks:=0
	var error:=motion.build(data,{"fps_num":24,"fps_den":1,"duration_frames":48},{"strength":.65});checks+=1
	if not error.is_empty():print(error);quit(1);return
	var exact:=true;var changed:=false
	for half in range(97):
		var at:=float(half)/2.;var original:=D.Adapter.compiled_sample(baseline,at);var assisted:=motion.apply(original,at)
		exact=exact and not assisted.has("error") and assisted.scale==original.scale and motion.apply(original,at,0.)==original;changed=changed or assisted!=original
	checks+=1
	if not exact or not changed:failures+=1
	for at in [0,12,24,48]:
		var original:=D.Adapter.compiled_sample(baseline,at);checks+=1
		if Model.Timeline.vector(motion.apply(original,at).position).distance_to(Model.Timeline.vector(original.position))>0.000001:failures+=1
	checks+=1
	if motion.helper_keys().is_empty() or not motion.apply(D.Adapter.compiled_sample(baseline,0),-1).has("error"):failures+=1
	var saved:=JSON.stringify(data);var first_helpers:=motion.helper_keys()
	for rate in [[24000,1001],[30000,1001],[60,1]]:
		var video:={"fps_num":rate[0],"fps_den":rate[1],"duration_frames":48};checks+=1
		if not motion.build(data,video,{"strength":.65}).is_empty():failures+=1;continue
		exact=true;var samples:=[]
		for half in range(97):samples.append(motion.apply(D.Adapter.compiled_sample(baseline,float(half)/2.),float(half)/2.))
		for half in range(96,-1,-1):exact=exact and samples[half]==motion.apply(D.Adapter.compiled_sample(baseline,float(half)/2.),float(half)/2.)
		for at in [0,12,24,48]:
			var original:=D.Adapter.compiled_sample(baseline,at);exact=exact and Model.Timeline.vector(motion.apply(original,at).position).distance_to(Model.Timeline.vector(original.position))<.000001
		checks+=1
		if not exact or JSON.stringify(data)!=saved:failures+=1
		var helpers:=motion.helper_keys();checks+=1
		if helpers==first_helpers:failures+=1
		checks+=1
		if motion.build(data,{"fps_num":0,"fps_den":1,"duration_frames":48}).is_empty() or motion.helper_keys()!=helpers:failures+=1
	var video := {"fps_num":24,"fps_den":1,"duration_frames":48}
	motion.build(data,video)
	for field in ["position","rotation_xyzw"]:
		var helper: Dictionary={}
		for candidate in motion.helper_keys():
			if candidate.component==field and candidate.kind=="overshoot":
				helper=candidate
				break
		var adjusted := Motion.new()
		checks+=1
		if helper.is_empty():failures+=1;continue
		var settings := {"track_helper_edits":{"@root":{helper.id:{"phase":.75,"amount":0.}}}}
		error=adjusted.build(data,video,settings)
		checks+=1
		if not error.is_empty():print(error);failures+=1;continue
		var peer: String="position" if field=="rotation_xyzw" else "rotation_xyzw"
		exact=true;changed=false
		for half in range(97):
			var at:=float(half)/2.
			var original:=D.Adapter.compiled_sample(baseline,at)
			var automatic:=motion.apply(original,at)
			var tuned:=adjusted.apply(original,at)
			exact=exact and tuned[peer]==automatic[peer] and tuned.scale==original.scale
			changed=changed or tuned[field]!=automatic[field]
		checks+=1
		if not exact or not changed:failures+=1
		var previous:=adjusted.helper_keys()
		checks+=1
		if adjusted.build(data,video,{"track_helper_edits":{"@root":{"scale/unknown":{"phase":.4,"amount":.5}}}}).is_empty() or previous!=adjusted.helper_keys():failures+=1
	print("ROOT_COMPONENT_MOTION "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
