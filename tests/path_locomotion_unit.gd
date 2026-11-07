extends SceneTree
const Walk=preload("res://src/path_locomotion.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=Walk.Model
const Paths=Walk.Paths
const D=Paths.Components
var checks:=0
var failures:=0
var folder: String
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	create_timer(30).timeout.connect(func():push_error("Walking domain watchdog");quit(2));call_deferred("run")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var source:="res://examples/tutorials/Practice figure.glb";var sha:=FileAccess.get_sha256(source);var loaded:=SceneIO.load_glb(source)
	check(not loaded.has("error"),"load original procedural seventeen-bone figure")
	if loaded.has("error"):quit(1);return
	var node: Node3D=loaded.scene;root.add_child(node);var actor:=Model.new();actor.root=node;actor.base_root=node.transform;actor.data=Model.definition(source);actor.inventory(node);actor.apply(0)
	var original: Dictionary=actor.data.duplicate(true);var state:=Walk.capture_state(actor);var video:={"fps_num":24,"fps_den":1,"duration_frames":48};var route: Dictionary=Paths.change(original,0,Vector3.ZERO,48).data;route=Paths.change(route,48,Vector3(0,0,.6),48).data
	var plan:=Walk.new();var error:=plan.build(actor,route,video);check(error.is_empty(),"bounded flat straight candidate builds without changing authored data")
	if not error.is_empty():print("WALK_BUILD_ERROR "+error);node.free();quit(1);return
	var exact:=true;var feet_exact:=true;var changed:=false;var maximum:=0.;var probe:=Model.new();probe.data=route;probe.motion_video=video
	for half in range(97):
		var at:=float(half)/2.;var result:=plan.sample(at);var baseline: Dictionary=probe.sample_authored_transform(at);exact=exact and not result.has("error") and actor.data==original and Walk.capture_state(actor)==state
		if result.has("error"):continue
		exact=exact and result.transform.position[0]==baseline.position[0] and result.transform.position[2]==baseline.position[2] and result.transform.rotation_xyzw==baseline.rotation_xyzw and result.transform.scale==baseline.scale
		changed=changed or result.pose!=probe.sample_body(at)
		actor.root.transform=Transform3D(Basis(Model.Timeline.quaternion(result.transform.rotation_xyzw)).scaled(Vector3.ONE*result.transform.scale),Model.Timeline.vector(result.transform.position))*actor.base_root;Walk.Feet.apply_pose(actor,result.pose)
		for foot in result.targets:
			var difference: float=actor.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position));maximum=maxf(maximum,difference);feet_exact=feet_exact and difference<.0002
		Walk.restore_state(actor,state)
	check(exact and changed,"all97half-frame samples preserve source/root path turn/scale and restore live skeleton exactly")
	check(feet_exact,"all97derived foot targets match actual skeletal positions within0.2mm")
	var forward:=plan.sample(17.5);plan.sample(40);check(plan.sample(17.5)==forward and actor.data==original and Walk.capture_state(actor)==state,"seek order and repeated reads are deterministic without leaking pose state")
	var zero:=plan.sample(17.5,0);check(zero.pose==probe.sample_body(17.5) and zero.transform==probe.sample_authored_transform(17.5) and Walk.capture_state(actor)==state,"zero amount returns exact authored pose/path without IK mutation")
	check(not plan.sample(17.5,.4).has("error") and Walk.capture_state(actor)==state,"partial amount remains solvable and restores state")
	var detached:=plan.sample(17.5);detached.pose.clear();check(not plan.sample(17.5).pose.is_empty(),"caller cannot mutate the cached suggested pose")
	for at in [-1.,49.,NAN]:check(plan.sample(at).has("error"),"out-of-range/nonfinite sample refuses: "+str(at))
	check(plan.sample(12,-.1).has("error") and plan.sample(12,1.1).has("error"),"invalid correction amount refuses")
	var good:=plan.sample(24);check(not plan.build(actor,route,video,{"stride":NAN}).is_empty() and plan.sample(24)==good,"failed build preserves the earlier valid suggestion")
	var json_plan:=Walk.new();var json_route: Dictionary=JSON.parse_string(JSON.stringify(route,"",true,true));var json_video: Dictionary=JSON.parse_string(JSON.stringify(video));check(json_plan.build(actor,json_route,json_video).is_empty(),"whole-valued JSON route/timing numbers keep compatibility")
	var leg: String=actor.contact_legs()[0].ids[0];var keyed: Dictionary=D.put_bones(route,24,{leg:Model.identity()},"ease",48).data
	check(not plan.build(actor,keyed,video).is_empty(),"even an explicit identity leg key refuses replacement")
	var arm: String=""
	for id in actor.order:
		if Walk.Hold.IK.normalized(actor.bones[id].name)=="upperarml":arm=id
	var arm_pose:=Model.identity();var q:=Quaternion(Vector3.FORWARD,.4);arm_pose.rotation_xyzw=[q.x,q.y,q.z,q.w];var upper: Dictionary=D.put_bones(route,24,{arm:arm_pose},"ease",48).data;var upper_plan:=Walk.new();error=upper_plan.build(actor,upper,video);exact=error.is_empty();probe.data=upper
	for at in [0.,12.,24.,37.5,48.]:
		var result:=upper_plan.sample(at);exact=exact and not result.has("error") and result.pose.get(arm,Model.identity())==probe.sample_body(at).get(arm,Model.identity())
	check(exact,"unrelated keyed arm poses survive walking exactly")
	var contact: Dictionary=Model.contact_animation().promote(route,48);contact.animation_clips[0]["foot_contacts"]=Walk.Feet.capture(actor,0,48,"authored-feet")
	check(Model.validate(contact,48).is_empty() and not plan.build(actor,contact,video).is_empty(),"authored planted contacts refuse a competing walking plan")
	var group:=route.duplicate(true);group.parent_id="group";check(not plan.build(actor,group,video).is_empty(),"grouped model refuses unsupported moving-parent inference")
	var turn_base: Dictionary=D.put_component(route,0,"rotation_xyzw",[0,0,0,1],"ease",48).data;var turning: Dictionary=D.put_component(turn_base,48,"rotation_xyzw",[0,sin(.25),0,cos(.25)],"ease",48).data;check(not plan.build(actor,turning,video).is_empty(),"changing authored turn refuses instead of silently steering it")
	var scale_base: Dictionary=D.put_component(route,0,"scale",1.,"ease",48).data;var growing: Dictionary=D.put_component(scale_base,48,"scale",2.,"ease",48).data;check(not plan.build(actor,growing,video).is_empty(),"changing authored scale refuses unsupported stride retargeting")
	var slope: Dictionary=Paths.change(route,48,Vector3(0,.1,.6),48).data;check(not plan.build(actor,slope,video).is_empty(),"non-flat path refuses unimplemented terrain inference")
	var bend_maximum:=0.
	var bend: Dictionary=Paths.change(route,24,Vector3(.08,0,.3),48).data;var bent:=Walk.new();var bent_error:=bent.build(actor,bend,video);check(bent_error.is_empty(),"flat bending path builds without replacing authored facing")
	if not bent_error.is_empty():print("BEND_BUILD_ERROR "+bent_error)
	else:
		probe.data=bend;exact=true;feet_exact=true;var planted:=true;var prior_targets: Array=[];var prior_phases: Array=[]
		for quarter in range(193):
			var at:=float(quarter)/4.;var result:=bent.sample(at);var baseline: Dictionary=probe.sample_authored_transform(at)
			if result.has("error"):exact=false;print(result);continue
			exact=exact and actor.data==original and Walk.capture_state(actor)==state and result.transform.position[0]==baseline.position[0] and result.transform.position[2]==baseline.position[2] and result.transform.rotation_xyzw==baseline.rotation_xyzw and result.transform.scale==baseline.scale
			actor.root.transform=Transform3D(Basis(Model.Timeline.quaternion(result.transform.rotation_xyzw)).scaled(Vector3.ONE*result.transform.scale),Model.Timeline.vector(result.transform.position))*actor.base_root;Walk.Feet.apply_pose(actor,result.pose)
			for foot in result.targets:
				var difference: float=actor.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position));bend_maximum=maxf(bend_maximum,difference);feet_exact=feet_exact and difference<.0002
			Walk.restore_state(actor,state)
			var distance: float=bent.distance_at(at)
			for side in range(2):
				var phase:=fposmod(distance/bent._stride+float(side)*.5,1.)
				if at>=bent._ramp_frames+.25 and not prior_phases.is_empty() and phase<.5 and prior_phases[side]<.5 and phase>=prior_phases[side]:planted=planted and Model.Timeline.vector(result.targets[side].position).distance_to(Model.Timeline.vector(prior_targets[side].position))<.000001
				if prior_phases.size()<2:prior_phases.append(phase)
				else:prior_phases[side]=phase
			prior_targets=result.targets
		check(exact and feet_exact,"all193quarter-frame bend samples preserve root/facing/source/live state and meet derived foot targets")
		check(planted,"bending-route stance targets remain fixed in world space")
		var saved_bend:=bent.sample(17.25);bent.sample(40);check(bent.sample(17.25)==saved_bend,"bending-route reverse seeking reproduces exact poses")
	var wide: Dictionary=Paths.change(route,24,Vector3(.12,0,.3),48).data;var before_refusal:=bent.sample(24);check(not bent.build(actor,wide,video).is_empty() and bent.sample(24)==before_refusal and Walk.capture_state(actor)==state,"unsolved wider bend refuses atomically while preserving earlier usable plan")
	var corrected:=Walk.new();var correction_error:=corrected.build(actor,wide,video,{"stride":.3,"lowering":.05})
	check(correction_error.is_empty(),"wider bend supports explicit shorter stride/body lowering without weakening contact accuracy")
	if not correction_error.is_empty():print("CORRECTED_BEND_ERROR "+correction_error)
	var reverse: Dictionary=Paths.change(route,24,Vector3(0,0,1),48).data;check(not plan.build(actor,reverse,video).is_empty(),"reversing path refuses unsupported backwards gait")
	var jump: Dictionary=D.put_component(route,0,"position",[0,0,0],"hold",48).data;check(not plan.build(actor,jump,video).is_empty(),"Hold jump refuses invented travel between cuts")
	check(not plan.build(actor,original,video).is_empty(),"stationary model refuses a meaningless walking plan")
	var unsupported:=Model.new();unsupported.root=Node3D.new();root.add_child(unsupported.root);unsupported.data=Model.definition(source);unsupported.base_root=Transform3D.IDENTITY
	check(not plan.build(unsupported,unsupported.data,video).is_empty(),"missing leg rig refuses safely");unsupported.root.free()
	var source_copy: Dictionary=actor.data;actor.data=original.duplicate(true);actor.data.name="changed";check(plan.sample(12).has("error"),"changed model refuses a stale suggestion");actor.data=source_copy
	var info: Dictionary=actor.bones[arm];var index: int=info.index;info.index=-1;check(plan.sample(12).has("error"),"changed non-leg bone binding refuses before skeleton access");info.index=index
	check(actor.data==original and Walk.capture_state(actor)==state and FileAccess.get_sha256(source)==sha,"all success/refusal paths preserve authored model/live state/original GLB")
	var result:={"checks":checks,"failures":failures,"maximum_foot_error":maximum,"samples":97,"bend_samples":193,"maximum_bend_foot_error":bend_maximum,"scope":"bounded flat straight/bending walk evaluator on original figure; not native/terrain/artist acceptance"};FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("PATH_LOCOMOTION_UNIT "+JSON.stringify(result));node.free();quit(0 if failures==0 else 1)
