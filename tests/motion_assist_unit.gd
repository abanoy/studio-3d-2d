extends SceneTree
const Assist=preload("res://src/motion_assist.gd")
const Model=Assist.Model
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func value(x: float,angle: float=0.) -> Dictionary:
	var q:=Quaternion(Vector3.UP,angle);return {"position":[x,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w],"scale":1.}
func curve(frames: Array,mode: String="ease") -> Array:
	var result:=[]
	for i in range(frames.size()):result.append({"frame":frames[i],"value":value(float(i),float(i)*.7),"interpolation":mode})
	return result
func _initialize() -> void:
	var video:={"fps_num":24,"fps_den":1,"duration_frames":72};var main:=curve([0,12,24]);var before: Array=main.duplicate(true);var assist:=Assist.new()
	check(assist.build(main,video).is_empty(),"three authored poses compile into a separate derived preview")
	check(main==before and assist.main_keys()==before and assist.helper_keys().size()==9,"generated helpers retain exact main controls and separate identities")
	var exact:=true
	for key in main:exact=exact and assist.sample(float(key.frame))==key.value
	check(exact,"every main key is returned exactly, including raw quaternion/scale values")
	var forward:=[];var reversible:=true
	for half in range(145):forward.append(assist.sample(float(half)/2))
	for half in range(144,-1,-1):reversible=reversible and assist.sample(float(half)/2)==forward[half]
	check(reversible,"arbitrary reverse half-frame sampling is deterministic")
	check(Assist.T.vector(assist.sample(1.44).position).x<0,"fast travel has visible anticipatory counter-motion")
	check(Assist.T.vector(assist.sample(10.44).position).x>1.,"fast travel overshoots before returning to the exact destination pose")
	check(assist.sample(25.6128)!=Assist.baseline(main,25.6128) and assist.sample(30.)==Assist.baseline(main,30.),"last pose has a bounded settling tail then returns to its authored hold")
	var disabled:=Assist.new();check(disabled.build(main,video,{"strength":0.}).is_empty() and disabled.helper_keys().is_empty(),"disabled assistance generates no helpers")
	var off_exact:=true
	for half in range(145):off_exact=off_exact and disabled.sample(float(half)/2)==Assist.baseline(main,float(half)/2) and assist.sample(float(half)/2,0.)==Assist.baseline(main,float(half)/2)
	check(off_exact,"turning assistance off exactly restores original interpolation")
	var doubled:=curve([0,24,48]);var double_assist:=Assist.new();check(double_assist.build(doubled,{"fps_num":48,"fps_den":1,"duration_frames":144}).is_empty(),"same real-time motion builds at twice the frame rate")
	var time_exact:=true
	for half in range(145):time_exact=time_exact and assist.sample(float(half)/2)==double_assist.sample(float(half))
	check(time_exact,"real-time assistance is frame-rate independent")
	var fast:=Assist.new();fast.build(main,video,{"position_limit":.5});var slow:=Assist.new();slow.build(doubled,video,{"position_limit":.5});var fast_delta: float=Assist.T.vector(fast.sample(10.44).position).distance_to(Assist.T.vector(Assist.baseline(main,10.44).position));var slow_delta: float=Assist.T.vector(slow.sample(20.88).position).distance_to(Assist.T.vector(Assist.baseline(doubled,20.88).position))
	check(fast_delta>slow_delta,"unsaturated movement speed changes the derived detail strength")
	check(Assist.T.vector(assist.sample(10.44).position).distance_to(Assist.T.vector(Assist.baseline(main,10.44).position))<=.080001,"fast movement stays inside its configured extra-position bound")
	var angular:=Assist.new();angular.build(main,video,{"rotation_limit":.01});check(Assist.T.quaternion(angular.sample(10.44).rotation_xyzw).angle_to(Assist.T.quaternion(Assist.baseline(main,10.44).rotation_xyzw))<=.01001,"generated rotation respects its separate angular bound")
	var cut:=Assist.new();cut.build(curve([0,1,2]),video);check(cut.helper_keys().is_empty(),"near-adjacent main controls do not squeeze acting into an instant cut")
	var antipodal:=curve([0,12]);antipodal[1].value=antipodal[0].value.duplicate(true);antipodal[1].value.rotation_xyzw=[0,0,0,-1];var equivalent:=Assist.new();equivalent.build(antipodal,video);check(equivalent.helper_keys().is_empty(),"equivalent opposite-sign quaternions do not invent a full rotation")
	var held:=Assist.new();held.build(curve([0,12,24],"hold"),video);check(held.helper_keys().is_empty() and held.sample(11.9)==Assist.baseline(held.main_keys(),11.9),"explicit Hold cuts suppress generated transitions and tails")
	var stationary:=Assist.new();var still:=curve([0,12,24]);for key in still:key.value=value(0)
	stationary.build(still,video);check(stationary.helper_keys().is_empty(),"stationary keys do not invent bouncing")
	var old:=assist.fingerprint();var invalid:=main.duplicate(true);invalid[1].frame=0;check(not assist.build(invalid,video).is_empty() and assist.fingerprint()==old and assist.main_keys()==before,"invalid rebuild preserves the complete prior preview")
	for setting in [{"strength":NAN},{"strength":-1.},{"distance_scale":0.},{"position_limit":-1.},{"rotation_limit":INF}]:check(not assist.build(main,video,setting).is_empty(),"invalid assistance settings refuse atomically")
	var copied:=assist.helper_keys();copied[0].value.position[0]=99;check(assist.helper_keys()[0].value.position[0]!=99,"returned helper data cannot mutate the compiled preview")
	main[1].value.position[0]=99;check(assist.main_keys()==before,"caller mutations cannot change compiled main poses")
	check(assist.sample(NAN).has("error") and assist.sample(-1.).has("error") and assist.sample(73.).has("error"),"invalid sample times refuse explicitly")
	var changed:=before.duplicate(true);changed[1].frame=14;check(assist.build(changed,video).is_empty() and assist.fingerprint()!=old and assist.helper_keys()[0].frame!=copied[0].frame,"moving a main key recalculates the derived helper addresses")
	print("MOTION_ASSIST_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
