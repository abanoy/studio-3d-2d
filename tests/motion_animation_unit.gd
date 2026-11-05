extends SceneTree
const Motion=preload("res://src/motion_animation.gd")
const Model=Motion.Body.Model
const Tracks=Motion.Tracks
var checks:=0
var failures:=0
var video:={"fps_num":24,"fps_den":1,"duration_frames":48}
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func value(x: float,root:=false) -> Dictionary:
	var result:=Model.identity();result.position=[x,0,0]
	if root:result["scale"]=1.
	return result
func _initialize() -> void:
	var old:=Model.definition("res://project.godot")
	for at in [0,12,24]:old.pose_keys.append({"frame":at,"pose":{"left":value(1. if at==12 else 0.),"right":value(0.)},"transform":value(.1 if at==12 else 0.,true),"interpolation":"ease"})
	var legacy:=Model.new();legacy.data=old
	var original: Dictionary=old.duplicate(true);var result:=Motion.configure(old,true,.65,48)
	check(not result.has("error") and result.data.format==Model.MOTION_FORMAT and Model.validate(result.data,48).is_empty(),"explicit opt-in promotes to a validated model8 contract")
	check(old==original,"promotion leaves the original model and key data unchanged")
	var actor:=Model.new();actor.data=result.data;actor.motion_video=video
	check(Model.is_body(actor.data) and Model.is_contact(actor.data) and Model.ShapeAnimation.independent(actor.data),"model8 retains independent body/expression/contact capabilities")
	check(actor.sample(10)!=legacy.sample(10) and actor.sample_transform(10)!=legacy.sample_transform(10),"ordinary pose/root sampling includes generated motion")
	check(actor.sample_body(10)==legacy.sample_body(10) and actor.sample_authored_transform(10)==legacy.sample_authored_transform(10),"authored sampling remains separate and exact")
	var exact:=true
	for at in [0,12,24]:exact=exact and actor.sample(at)==legacy.sample(at) and actor.sample_transform(at)==legacy.sample_transform(at)
	check(exact,"ordinary model8 sampling hits all main poses exactly")
	var samples:=[];var reversible:=true
	for half in range(97):samples.append(actor.sample(float(half)/2))
	for half in range(96,-1,-1):reversible=reversible and actor.sample(float(half)/2)==samples[half]
	check(reversible,"ordinary assisted sampling is reverse-seek deterministic")
	var authored: Dictionary=actor.data.duplicate(true);actor.data=Motion.configure(actor.data,false,.65,48).data;exact=true
	for half in range(97):exact=exact and actor.sample(float(half)/2)==legacy.sample(float(half)/2) and actor.sample_transform(float(half)/2)==legacy.sample_transform(float(half)/2)
	check(exact,"saved Off retains exact previous animation")
	actor.data=authored.duplicate(true)
	var roots:=[]
	for half in range(97):roots.append(actor.sample_transform(float(half)/2))
	# Simulate the normal authoring draft at an intermediate assisted frame.
	actor.data.pose=actor.sample_body(10);var root_value:=actor.sample_authored_transform(10);actor.data.position=root_value.position;actor.data.rotation_xyzw=root_value.rotation_xyzw;actor.data.scale=root_value.scale;actor.data.draft_frame=10
	check(actor.sample(10,true)==actor.sample(10,false) and actor.sample_transform(10,true)==actor.sample_transform(10,false),"starting a draft leaves the visible assisted pose unchanged")
	var target: Dictionary=actor.sample(10,true).left.duplicate(true);var p: Vector3=Model.Timeline.vector(target.position)+Vector3(.1,0,0);target.position=[p.x,p.y,p.z];actor.data.pose.left=target
	check(actor.sample(10,true).left==target,"editing a visible body target does not apply its helper offset twice")
	check(actor.sample_transform(10,true)==roots[20] and actor.sample(10,true).right==legacy.sample(10).right,"editing one bone leaves the assisted root and unedited peer alone")
	var key:={"frame":10,"pose":actor.sample_body(10,true),"transform":actor.sample_transform(10,true),"authored_channels":["left"],"interpolation":"ease"}
	check(actor.put_pose_key(key,48,false,authored).is_empty(),"normal body authoring creates one authoritative part control")
	check(actor.data.format==Model.MOTION_FORMAT and actor.data.motion_assist==authored.motion_assist and actor.sample(10,true).left==target and actor.sample(10).left==target,"committing the main key retains model8 and its exact visible target")
	exact=true
	for half in range(97):exact=exact and actor.sample_transform(float(half)/2)==roots[half]
	check(exact and actor.data.animation_clips[0].keys==authored.animation_clips[0].keys,"a new bone main key never bakes helper root or legacy peer snapshots")
	var old_plan: RefCounted=actor.motion_plan();actor.motion_video={"fps_num":48,"fps_den":1,"duration_frames":48};check(actor.motion_plan()!=old_plan,"project frame-rate changes rebuild the helper plan")
	var capture:=[]
	for at in range(4,9):capture.append({"frame":at,"pose":{"left":value(float(at)),"right":value(0.)},"transform":value(float(at)*.01,true),"interpolation":"linear"})
	var recorded: Dictionary=preload("res://src/physics_recording.gd").replace_range(authored,capture,4,8,48);check(not recorded.has("error") and recorded.data.format==Model.MOTION_FORMAT and recorded.data.motion_assist==authored.motion_assist,"recorded takes retain the saved model8 settings and contract")
	var recorded_actor:=Model.new();recorded_actor.data=recorded.data;recorded_actor.motion_video=video;var recorded_exact:=true
	for half in range(8,17):recorded_exact=recorded_exact and recorded_actor.sample(float(half)/2)==recorded_actor.sample_body(float(half)/2) and recorded_actor.sample_transform(float(half)/2)==recorded_actor.sample_authored_transform(float(half)/2)
	check(recorded_exact,"dense captured frames retain exact recorded motion without an added bounce")
	var corrupt:=authored.duplicate(true);corrupt.format=Model.CONTACT_FORMAT;check(not Model.validate(corrupt,48).is_empty(),"earlier model versions cannot hide ignored assistance settings")
	for descriptor in [{},{"format":Motion.SETTINGS,"enabled":true,"strength":NAN},{"format":Motion.SETTINGS,"enabled":true,"strength":2.},{"format":Motion.SETTINGS,"enabled":1,"strength":.65},{"format":Motion.SETTINGS,"enabled":true,"strength":.65,"unknown":1}]:
		corrupt=authored.duplicate(true);corrupt.motion_assist=descriptor;check(not Model.validate(corrupt,48).is_empty(),"invalid assistance descriptor refuses")
	print("MOTION_ANIMATION_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
