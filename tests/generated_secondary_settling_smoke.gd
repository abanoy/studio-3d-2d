extends SceneTree
const Model=preload("res://src/model.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func make_actor(tilted_center:=false) -> RefCounted:
	var actor:=Model.new();actor.root=Node3D.new();root.add_child(actor.root)
	var sk:=Skeleton3D.new();sk.name="Rig";sk.set_animate_physical_bones(false);actor.root.add_child(sk)
	for name in ["Body","HairA","HairB","HairC","HairEnd"]:sk.add_bone(name)
	for i in range(5):
		sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,Vector3(0,2,0) if i==0 else Vector3(0,0,.25) if i==1 else Vector3(0,-.15,.4)))
		if i>0:sk.set_bone_parent(i,i-1)
	if tilted_center:
		var turn:=Basis(Vector3.RIGHT,PI*.5)
		sk.set_bone_rest(0,Transform3D(turn,Vector3(0,2,0)))
		sk.set_bone_rest(1,Transform3D(turn.inverse(),turn.inverse()*Vector3(0,0,.25)))
	sk.reset_bone_poses()
	actor.data={"format":"studio_model_1","id":"fixture","name":"Diagonal helper","source":"","sha256":"",
		"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.,"visible":true,"reference_only":false,
		"start_frame":0,"parent_id":"","pose":{},"pose_keys":[],"draft_frame":0,"metadata":{}}
	actor.inventory(actor.root)
	var joints: Array=[]
	for name in ["HairA","HairB","HairC","HairEnd"]:joints.append({"binding":{"kind":"bone","id":"Rig::"+name},"stiffness":1.,"drag":.45,"radius":.005,"gravity":0.,"gravity_direction":[0,-1,0]})
	actor.root.set_meta("has_secondary_rig",{"source_family":"HAS","chains":[{"joints":joints,"center":{"kind":"bone","id":"Rig::Body"},"colliders":[],"end_extension":0.}],"colliders":[]})
	return actor
func evaluate(actor: RefCounted,natural: bool,wind:=Vector3(.06,0,0)) -> Dictionary:
	if natural:actor.data.metadata[Motion.KEY]={"format":Motion.FORMAT,"mode":"natural"}
	else:actor.data.metadata.erase(Motion.KEY)
	actor.apply(0,true)
	var original: PackedByteArray=var_to_bytes(actor.root.get_meta("has_secondary_rig"))
	var data: PackedByteArray=var_to_bytes(actor.data)
	var start: Vector3=actor.bone_transform("Rig::HairA").origin;var before: Vector3=actor.bone_transform("Rig::HairEnd").origin
	var attachment: Vector3=actor.bone_transform("Rig::HairB").origin
	var made: Dictionary=Spring.construct(actor)
	if made.has("error"):return made
	var runner: RefCounted=made.runner
	for i in range(4):await process_frame
	var issue:="";var final: Dictionary={}
	for i in range(720):
		actor.live_pose={};actor.apply_current(0,true)
		var step: Dictionary=runner.step(1./120.,Vector3.ZERO)
		if step.has("error"):issue=step.error;break
		final=step.pose;actor.live_pose=final;actor.apply_current(0,true)
	var end: Vector3=actor.bone_transform("Rig::HairEnd").origin
	var distal: Vector3=actor.bone_transform("Rig::HairEnd").origin-actor.bone_transform("Rig::HairC").origin
	var attached: Vector3=actor.bone_transform("Rig::HairB").origin
	var first_length_error: float=absf(attached.distance_to(start)-attachment.distance_to(start))
	var root_fixed: bool=actor.bone_transform("Rig::HairA").origin==start
	var settled: PackedByteArray=var_to_bytes(final);var moved:=false
	for i in range(120):
		actor.live_pose={};actor.apply_current(0,true)
		var step: Dictionary=runner.step(1./120.,wind)
		if step.has("error"):issue=step.error;break
		actor.live_pose=step.pose;actor.apply_current(0,true)
		moved=moved or actor.bone_transform("Rig::HairEnd").origin.distance_to(end)>.001
	var response: Vector3=actor.bone_transform("Rig::HairEnd").origin-end
	runner.dispose();actor.live_pose=null;actor.apply(0,true)
	return {"error":issue,"tip_drop":before.y-end.y,"last_segment_down":distal.normalized().dot(Vector3.DOWN),
		"root_held":root_fixed,"attachment_drift":attached.distance_to(attachment),"first_segment_length_error":first_length_error,
		"restored":actor.bone_transform("Rig::HairEnd").origin.is_equal_approx(before),
		"wind_response":moved,"wind_along_direction":response.dot(wind.normalized()),"settled_pose":settled,"authored_preserved":var_to_bytes(actor.data)==data,
		"source_rig_preserved":var_to_bytes(actor.root.get_meta("has_secondary_rig"))==original}
func run() -> void:
	var actor: RefCounted=make_actor()
	var keep: Dictionary=await evaluate(actor,false)
	check(keep.error.is_empty(),"Keep shape fixed-step simulation completes")
	check(absf(keep.tip_drop)<.0001,"historical zero-gravity diagonal shape stays unchanged")
	var natural: Dictionary=await evaluate(actor,true)
	check(natural.error.is_empty(),"Natural gravity fixed-step simulation completes")
	check(natural.tip_drop>.3 and natural.last_segment_down>.95,"hanging lengths visibly settle down from diagonal rest")
	check(natural.root_held and natural.first_segment_length_error<.0001,"attachment position and segment length stay fixed while the first hair joint relaxes")
	check(natural.wind_response,"naturally settled helper still responds to ordinary airflow")
	check(natural.restored and natural.authored_preserved and natural.source_rig_preserved,"Off restores original pose and preserves authored data and rig declarations")
	var again: Dictionary=await evaluate(actor,true)
	check(again.error.is_empty() and again.settled_pose==natural.settled_pose,"fresh fixed-step settling has exact deterministic FK output")
	actor.release_render_bounds();actor.root.free();await process_frame
	var tilted: RefCounted=make_actor(true);var oriented: Dictionary=await evaluate(tilted,true)
	check(oriented.error.is_empty() and oriented.tip_drop>.3 and oriented.last_segment_down>.95,"gravity stays world-down when imported attachment axes are rotated")
	tilted.release_render_bounds();tilted.root.free();await process_frame
	var front_actor: RefCounted=make_actor(true);var front: Dictionary=await evaluate(front_actor,true,Vector3(0,0,-.06))
	check(front.error.is_empty() and front.wind_along_direction>.01,"front airflow moves hair along world front with rotated attachment axes")
	front_actor.release_render_bounds();front_actor.root.free();await process_frame
	var back_actor: RefCounted=make_actor(true);var back: Dictionary=await evaluate(back_actor,true,Vector3(0,0,.06))
	check(back.error.is_empty() and back.wind_along_direction>.01,"back airflow moves hair along world back with rotated attachment axes")
	back_actor.release_render_bounds();back_actor.root.free();await process_frame
	var metrics: Dictionary=natural.duplicate();metrics.erase("settled_pose")
	print("GENERATED_SECONDARY_SETTLING "+JSON.stringify({"checks":checks,"failures":failures,"metrics":metrics,"user_profile":OS.get_user_data_dir()}));quit(0 if failures==0 else 1)
