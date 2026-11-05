extends SceneTree
const Tracks=preload("res://src/motion_assist_tracks.gd")
const Model=Tracks.Model
const B=Tracks.B
const Body=preload("res://src/body_animation.gd")
const C=Model.Clips
const T=Model.Timeline
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
func model(mode: String="ease") -> Dictionary:
	var data:=Model.definition("res://project.godot")
	for at in [0,12,24]:data.pose_keys.append({"frame":at,"pose":{"left":value(1. if at==12 else 0.),"right":value(0.)},"transform":value(.1 if at==12 else 0.,true),"interpolation":mode})
	return Body.promote(data,48)
func original(data: Dictionary,frame: float,id: String) -> Dictionary:
	var actor:=Model.new();actor.data=data
	return actor.sample_transform(frame) if id=="@root" else actor.sample_body(frame).get(id,Model.identity())
func sampled(plan: RefCounted,data: Dictionary,frame: float,id: String="left",gain:=1.) -> Dictionary:return plan.apply(original(data,frame,id),id,frame,gain)
func _initialize() -> void:
	create_timer(40).timeout.connect(func():push_error("Motion tracks watchdog");quit(2));call_deferred("run")
func run() -> void:
	var data:=model();var before:=data.duplicate(true);var plan:=Tracks.new()
	check(plan.build(data,["left","@root"],video).is_empty(),"compile actual independent part records without supplied endpoint guesses")
	check(data==before and plan.parts()==["left","@root"],"compilation retains all authored records and requested channel identities")
	var main_exact:=true;var baseline_exact:=true;var changed:=false;var samples:=[]
	for half in range(97):
		var at:=float(half)/2;samples.append(sampled(plan,data,at));changed=changed or samples[-1]!=original(data,at,"left");baseline_exact=baseline_exact and sampled(plan,data,at,"left",0.)==original(data,at,"left")
	for at in [0,12,24]:main_exact=main_exact and sampled(plan,data,at)==original(data,at,"left") and sampled(plan,data,at,"@root")==original(data,at,"@root")
	check(main_exact and changed,"native main controls stay exact while intermediate motion gains detail")
	check(baseline_exact,"Off returns exact existing part interpolation at every half frame")
	var reverse_exact:=true
	for half in range(96,-1,-1):reverse_exact=reverse_exact and sampled(plan,data,float(half)/2)==samples[half]
	check(reverse_exact,"source-time detail seeks backwards identically")
	var split:=C.split(data,8);var split_plan:=Tracks.new();check(not split.has("error") and split_plan.build(split.data,["left","@root"],video).is_empty(),"compile a split inside a moving source span")
	var split_exact:=true
	for half in range(97):split_exact=split_exact and sampled(split_plan,split.data,float(half)/2)==samples[half]
	check(split_exact,"splitting a block preserves helper phase at every half frame")
	var moved:=C.move(split.data,split.right_id,20,48);var moved_plan:=Tracks.new();check(not moved.has("error") and moved_plan.build(moved.data,["left","@root"],video).is_empty(),"compile a moved source slice and its connecting gap")
	var relative_exact:=true
	for half in range(33):relative_exact=relative_exact and sampled(moved_plan,moved.data,20.+float(half)/2)==sampled(plan,data,8.+float(half)/2)
	check(relative_exact,"moving a split carries the exact relative generated motion")
	var gap:=sampled(moved_plan,moved.data,15.);check(Model.transform_valid(gap) and gap!=original(moved.data,15.,"left"),"recorded gap has bounded derived connection rather than an erased object")
	var bounded:=true
	for half in range(97):
		var at:=float(half)/2;bounded=bounded and T.vector(sampled(moved_plan,moved.data,at).position).distance_to(T.vector(original(moved.data,at,"left").position))<=.080001
	check(bounded,"carried slice offsets and a gap bounce share one final distance bound")
	var held:=model("hold");var held_plan:=Tracks.new();check(held_plan.build(held,["left"],video).is_empty() and held_plan.helper_keys().left.is_empty(),"deliberate source Holds generate no helpers")
	var holds_exact:=true
	for half in range(97):holds_exact=holds_exact and sampled(held_plan,held,float(half)/2)==original(held,float(half)/2,"left")
	check(holds_exact,"Hold timing stays exact through every source transition and final hold")
	var removed:=Body.remove_key(data,12,"left",48);var removed_plan:=Tracks.new()
	check(not removed.has("error") and removed_plan.build(removed.data,["left"],video).is_empty() and removed_plan.helper_keys().left.is_empty(),"removing the only moving control recalculates away its generated acting")
	var peer_view:=B.put(Body.view(data),18,{"new":value(2.)},"linear",48);var peer:=Body.install(data,peer_view.data);var peer_plan:=Tracks.new();peer_plan.build(peer,["left"],video);var peer_exact:=true
	for half in range(97):peer_exact=peer_exact and sampled(peer_plan,peer,float(half)/2)==samples[half]
	check(peer_exact,"another part's sparse control does not restart or change this part's helpers")
	var shifted:=C.move(data,data.animation_clips[0].id,12,48);var late:=Tracks.new();late.build(shifted.data,["left"],video)
	check(sampled(late,shifted.data,10.)==original(shifted.data,10.,"left") and shifted.data.start_frame==12,"helpers never anticipate before the object's first presence")
	check(sampled(late,shifted.data,22.)==sampled(plan,data,10.),"moving the whole block retains relative helper timing")
	var high:=data.duplicate(true)
	for piece in high.animation_clips:
		piece.source_in+=90000;piece.body_origin+=90000;piece.auto_extend=false
		for key in piece.keys:key.frame+=90000
		for id in piece.body_controls:
			for key in piece.body_controls[id]:key.frame+=90000
	var high_plan:=Tracks.new();var high_error:=high_plan.build(high,["left"],video);print("HIGH_SOURCE_DIAGNOSTIC "+high_error);check(high_error.is_empty(),"retained source controls near90000 compile without expanding project duration")
	var high_exact:=true
	for half in range(97):high_exact=high_exact and sampled(high_plan,high,float(half)/2)==samples[half]
	check(high_exact,"high source addresses preserve the same phase and movement speed")
	var helpers:=plan.helper_keys();var tail_found:=false
	for helper in helpers.left:tail_found=tail_found or helper.frame>24.
	check(tail_found and sampled(plan,data,31.)==original(data,31.,"left"),"inspectable generated tail settles back to the exact held final pose")
	var inspected:=true;var chronological:=true;var last_frame:=-1.;var helper_ids:={}
	for helper in moved_plan.helper_keys().left:
		inspected=inspected and helper.value==sampled(moved_plan,moved.data,helper.frame);chronological=chronological and helper.frame>=last_frame and not helper_ids.has(helper.id);helper_ids[helper.id]=true;last_frame=helper.frame
	check(inspected and chronological,"source/gap helper records report actual bounded values in stable chronological order")
	var copy:=plan.helper_keys();copy.left[0].value.position[0]=99.;check(plan.helper_keys().left[0].value.position[0]!=99.,"returned source helper records cannot change a compiled plan")
	check(not plan.build(data,["left","left"],video).is_empty() and plan.helper_keys()==helpers,"invalid rebuild keeps the complete previous source-time plan")
	var bad:=data.duplicate(true);bad.animation_clips[0].body_controls={"left":[{"frame":0,"value":value(NAN),"interpolation":"ease"}]}
	check(not plan.build(bad,["left"],video).is_empty() and plan.helper_keys()==helpers,"invalid native part data refuses before replacing the preview")
	check(plan.apply(value(0.),"left",NAN).has("error") and plan.apply(value(0.),"left",49.).has("error") and plan.apply(value(0.),"left",10.,NAN).has("error"),"source-time adapter explicitly refuses invalid query times and strength")
	var trimmed:=data.duplicate(true);trimmed.animation_clips[0].length=9;trimmed.animation_clips[0].auto_extend=false;trimmed.animation_clips[0].body_untrimmed=false;var trimmed_plan:=Tracks.new();trimmed_plan.build(trimmed,["left"],video)
	check(sampled(trimmed_plan,trimmed,15.)==original(trimmed,15.,"left") and sampled(trimmed_plan,trimmed,20.)==original(trimmed,20.,"left"),"cropped future controls cannot pull the final held pose after its short offset settles")
	var hold_split:=C.split(held,8);var hold_gap:=C.move(hold_split.data,hold_split.right_id,20,48);var hold_gap_plan:=Tracks.new();hold_gap_plan.build(hold_gap.data,["left"],video)
	check(hold_gap_plan.helper_keys().left.is_empty() and sampled(hold_gap_plan,hold_gap.data,15.)==original(hold_gap.data,15.,"left"),"deliberate Hold also suppresses inferred gap acting")
	var ordinary:=Tracks.Assist.new();check(not ordinary.build([{"frame":0,"value":value(0.),"interpolation":"ease"}],{"fps_num":24,"fps_den":1,"duration_frames":90024}).is_empty(),"source-space utility does not increase the project-space preview limit")
	var adjusted := Tracks.new()
	var source_helper: Dictionary=helpers.left[1]
	var source_settings := {"track_helper_edits":{"left":{source_helper.id:{"phase":.75,"amount":.5}}}}
	var authored := data.duplicate(true)
	check(adjusted.build(data,["left","@root"],video,source_settings).is_empty() and sampled(adjusted,data,9.)!=sampled(plan,data,9.),"clip-owned helper edit changes the selected source span")
	check(data==authored and sampled(adjusted,data,12.)==sampled(plan,data,12.) and sampled(adjusted,data,9.,"@root")==sampled(plan,data,9.,"@root"),"main pose and peer root retain their exact values")
	var preserved: Dictionary=adjusted.helper_keys()
	check(not adjusted.build(data,["left","@root"],video,{"track_helper_edits":{"left":{"missing/segment-0-12-2":{"phase":.7,"amount":.5}}}}).is_empty() and adjusted.helper_keys()==preserved,"unresolved owner refuses without replacing the valid plan")
	var gap_helper: Dictionary={}
	for helper in moved_plan.helper_keys().left:
		if helper.get("connection",false) and helper.kind=="overshoot":gap_helper=helper;break
	check(not gap_helper.is_empty(),"moved source slices expose an owned connecting helper")
	if not gap_helper.is_empty():
		var gap_settings := {"track_helper_edits":{"left":{gap_helper.id:{"phase":gap_helper.phase,"amount":0.}}}}
		check(adjusted.build(moved.data,["left","@root"],video,gap_settings).is_empty() and sampled(adjusted,moved.data,gap_helper.frame)!=sampled(moved_plan,moved.data,gap_helper.frame),"gap adjustment changes its own evaluated motion")
		check(sampled(adjusted,moved.data,22.)==sampled(moved_plan,moved.data,22.),"editing a gap leaves the following source clip exact")
	print("MOTION_ASSIST_TRACKS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
