extends SceneTree
const Recording=preload("res://src/physics_recording.gd")
const Model=preload("res://src/model.gd")
const Clips=preload("res://src/animation_clips.gd")
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(20).timeout.connect(func():push_error("Recording unit watchdog expired");quit(2))
	call_deferred("run")
func pose_key(at: int,x: float,interpolation: String="linear") -> Dictionary:
	return {"frame":at,"pose":{},"transform":{"position":[x,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.0},"interpolation":interpolation}
func rest(value: Dictionary) -> bool:
	return Model.Timeline.vector(value.position)==Vector3.ZERO and Model.Timeline.quaternion(value.rotation_xyzw)==Quaternion.IDENTITY
func run() -> void:
	DirAccess.make_dir_recursive_absolute("res://output/recording-unit")
	var asset:=ProjectSettings.globalize_path("res://output/recording-unit/empty.glb");SceneIO.make_empty(asset)
	var data:=Model.definition(asset);data["start_frame"]=0;data.pose_keys=[pose_key(0,0,"ease"),pose_key(12,12)]
	var before:=data.duplicate(true);var keys: Array=[pose_key(4,30),pose_key(5,40),pose_key(6,50)]
	var result:=Recording.replace_range(data,keys,4,6,48)
	check(not result.has("error") and data==before,"recording range replacement leaves the original model untouched")
	check(result.data.animation_clips.size()==3 and Model.validate(result.data,48).is_empty(),"middle recording creates independently owned left/take/right pieces")
	var original:=Model.new();original.data=data;var recorded:=Model.new();recorded.data=result.data
	var preserved:=true
	for at in [0,1,2,3,7,8,9,10,11,12,30]:preserved=preserved and recorded.sample_transform(at)==original.sample_transform(at)
	check(preserved,"all original authored-curve samples outside the recording range remain exact")
	check(recorded.sample_transform(4).position==[30.0,0.0,0.0] and recorded.sample_transform(5).position==[40.0,0.0,0.0] and recorded.sample_transform(6).position==[50.0,0.0,0.0],"each captured integer frame owns its exact recorded transform")
	check(result.data.animation_clips[2].source_in==7 and result.data.animation_clips[2].keys==data.pose_keys,"right fragment retains original source-time keys")
	check(result.data.start_frame==0 and result.data.presence_offset==0,"recording preserves independent first presence")
	var moved:=Clips.move(result.data,result.data.animation_clips[1].id,20,48)
	check(not moved.has("error") and moved.data.animation_clips[-1].keys==keys,"recorded motion is an ordinary draggable editable piece")
	data=Clips.promote(data);data.format="studio_model_3";data["visibility_keys"]=[{"frame":2,"visible":false}]
	result=Recording.replace_range(data,keys,4,6,48)
	check(result.data.format=="studio_model_3" and result.data.visibility_keys==data.visibility_keys,"recording preserves persistent visibility independently of motion")
	var static_data:=Model.definition(asset);static_data["start_frame"]=8
	result=Recording.replace_range(static_data,[pose_key(8,3),pose_key(9,4)],8,9,48);recorded.data=result.data
	check(result.data.start_frame==8 and result.data.animation_clips.size()==1 and recorded.sample_transform(30).position==[4.0,0.0,0.0],"a first take preserves introduction and holds its final recorded state")
	var invalid: Array=[pose_key(4,200001)]
	check(Recording.replace_range(data,invalid,4,4,48).has("error") and data.visibility_keys[0].visible==false,"out-of-range captured roots fail without changing source motion or visibility")
	check(Recording.replace_range(data,[pose_key(49,0)],49,49,48).has("error"),"recording cannot extend beyond the project end boundary")
	var independent:=Model.new();independent.data=before.duplicate(true)
	var prior:=independent.data.duplicate(true);var part:=Model.identity();part.position[0]=1.
	var error:=independent.put_pose_key({"frame":8,"pose":{"arm":part},"transform":independent.sample_transform(8),"authored_channels":["arm"],"interpolation":"ease"},48,false,prior)
	result=Recording.replace_range(independent.data,keys,4,6,48)
	check(error.is_empty() and not result.has("error") and result.data.format==Model.BODY_FORMAT and Model.validate(result.data,48).is_empty(),"capture writes compact native snapshots into a valid independent model6")
	recorded.data=result.data;preserved=true
	for half in range(97):
		var at:=float(half)/2
		if at<=3 or at>=7:preserved=preserved and recorded.sample(at)==independent.sample(at) and recorded.sample_transform(at)==independent.sample_transform(at)
	check(preserved and not result.data.animation_clips[0].body_untrimmed and not result.data.animation_clips[2].body_untrimmed,"capture fixes retained slice bounds and preserves every external part/root half-frame")
	var captured_arm: Dictionary=recorded.sample(5).arm
	check(recorded.sample_transform(5).position[0]==40. and Model.Timeline.vector(captured_arm.position)==Vector3.ZERO and Model.Timeline.quaternion(captured_arm.rotation_xyzw)==Quaternion.IDENTITY,"captured source snapshots override the recorded interval without borrowing earlier arm controls")
	# A newly captured hip must not inherit the first fallen snapshot backwards
	# through earlier blocks that never authored that channel (including hair takes).
	var falling_keys: Array=[]
	for at in range(4,7):
		var sample:=pose_key(at,30.+at);var hip:=Model.identity();hip.position[1]=-.8
		sample.pose["new-hip"]=hip;falling_keys.append(sample)
	var unchanged:=independent.data.duplicate(true);result=Recording.replace_range(independent.data,falling_keys,4,6,48);recorded.data=result.data
	var stable:=true
	for half in range(97):
		var at:=float(half)/2
		if at<=3 or at>=7:
			var value: Dictionary=recorded.sample_body(at);var previous_pose: Dictionary=independent.sample_body(at)
			stable=stable and rest(value.get("new-hip",Model.identity())) and recorded.sample_transform(at)==independent.sample_transform(at)
			for id in previous_pose:stable=stable and value[id]==previous_pose[id]
	check(stable and independent.data==unchanged,"new captured bones preserve every outside half-frame and existing channel without leaking their fallen pose backwards")
	check(Model.Timeline.vector(recorded.sample_body(4)["new-hip"].position)==Vector3(0,-.8,0) and Model.Timeline.vector(recorded.sample_body(6)["new-hip"].position)==Vector3(0,-.8,0),"new captured bones retain the exact first and final recorded engine transforms")
	var sparse:=independent.data.duplicate(true);sparse.animation_clips=[]
	result=Recording.replace_range(sparse,falling_keys,4,6,48);recorded.data=result.data
	check(not result.has("error") and Model.validate(result.data,48).is_empty() and rest(recorded.sample_body(0).get("new-hip",Model.identity())) and rest(recorded.sample_body(3).get("new-hip",Model.identity())) and Model.Timeline.vector(recorded.sample_body(4)["new-hip"].position)==Vector3(0,-.8,0),"a first capture after introduction creates a body-only baseline even without an earlier block")
	print("PHYSICS_RECORDING_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
