extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Parts=preload("res://src/character_parts.gd")
const Follow=preload("res://src/character_part_follow.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Parts following timeout");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
func joint(actor: RefCounted,name: String) -> String:
	for id in actor.order:
		if actor.bones[id].name==name:return id
	return ""
func pose(value: float) -> Dictionary:
	var q:=Quaternion(Vector3.FORWARD,value)
	return {"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
func settings(root_id: String,part_id: String,body_id: String,enabled: bool) -> Dictionary:
	return Parts.follow_edit(app.current_world(),root_id,{part_id:enabled},body_id,int(app.video.duration_frames))
func apply_edit(edit: Dictionary) -> String:
	if edit.has("error"):return edit.error
	var why: String=app.renderer.world_runtime.restore_instances(edit.after)
	if why.is_empty():app.push_history(edit);app.set_frame(app.frame)
	return why
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/parts-follow/flow-"+str(Time.get_ticks_usec()))
	DirAccess.make_dir_recursive_absolute(folder)
	var body_path:=folder.path_join("body.glb");var dress_path:=folder.path_join("dress.glb")
	check(SceneIO.make_pose_fixture(body_path)==OK and SceneIO.make_pose_fixture(dress_path)==OK,"independent prepared source rigs created")
	var input_pins: Dictionary={body_path:FileAccess.get_sha256(body_path),dress_path:FileAccess.get_sha256(dress_path)}
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json")
	root.gui_embed_subwindows=true;root.size=Vector2i(1500,1000);root.add_child(app);await settle()
	app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("cache");app.new_project()
	check(app.character_parts_editor.install_prepared([{"path":body_path,"role":"body"},{"path":dress_path,"role":"dress"}],{"name":"Follow fixture","fit_height":true,"reference_index":0}).is_empty(),"ordinary parts feature installs generated rigs")
	var runtime: RefCounted=app.renderer.world_runtime;var group_id:="";var body_id:="";var dress_id:=""
	for id in runtime.order:
		var row: Dictionary=runtime.instance(id).data
		if row.kind=="group":group_id=id
		elif row.metadata.character_part.role=="body":body_id=id
		else:dress_id=id
	var body: RefCounted=runtime.instance(body_id);var dress: RefCounted=runtime.instance(dress_id)
	var arm_body:=joint(body,"arm");var arm_dress:=joint(dress,"arm")
	var description: Dictionary=runtime.follow_report(dress_id)
	check(not description.has("error") and description.matched==2 and description.ambiguous==0,"unique source-node/runtime/rest/parent correspondences found")
	var target_data: Dictionary=dress.data.duplicate(true);target_data.pose[arm_dress]=pose(.2)
	check(runtime.restore_instance(dress_id,target_data).is_empty(),"part authored refinement remains independently editable")
	var master_data: Dictionary=body.data.duplicate(true);master_data.pose[arm_body]=pose(.4)
	check(runtime.restore_instance(body_id,master_data).is_empty(),"body authored pose installed")
	runtime.evaluate(0,false,body_id,app.video)
	var independent: Transform3D=dress.bone_transform(arm_dress)
	check(runtime.part_follow.frame_applications==0,"following is Off by default")
	app.character_parts_editor.open(group_id);await settle()
	check(app.character_parts_editor.follow_switches.has(dress_id) and not app.character_parts_editor.follow_switches[dress_id].disabled,"Manage parts exposes the supported opt-in")
	app.character_parts_editor.follow_switches[dress_id].button_pressed=true
	var history: int=app.history.size();app.character_parts_editor.apply_visibility();await settle()
	check(app.history.size()==history+1 and dress.data.metadata.character_part.follow_body,"following is one ordinary Undo edit")
	var followed: Transform3D=dress.bone_transform(arm_dress)
	check(not Follow.same(followed,independent),"body motion changes the actual separate part pose")
	var saved_body: Dictionary=body.data.duplicate(true);var saved_dress: Dictionary=dress.data.duplicate(true)
	for i in range(40):runtime.evaluate(0,false,body_id,app.video)
	check(Follow.same(followed,dress.bone_transform(arm_dress)),"same-frame evaluation does not feed derived poses back")
	check(body.data==saved_body and dress.data==saved_dress and dress.data.pose==target_data.pose,"derived following never rewrites authored poses or expression settings")
	app.undo();check(Follow.same(dress.bone_transform(arm_dress),independent),"Undo following restores exact independent authored pose")
	app.redo();check(Follow.same(dress.bone_transform(arm_dress),followed),"Redo restores derived following")
	check(apply_edit(settings(group_id,dress_id,body_id,false)).is_empty(),"Off is an ordinary scene edit")
	check(Follow.same(dress.bone_transform(arm_dress),independent),"Off immediately restores authored channels")
	check(apply_edit(settings(group_id,dress_id,body_id,true)).is_empty(),"following can be enabled again")
	body.live_pose={};runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error") and Follow.same(dress.bone_transform(arm_dress),independent),"live simulation ownership pauses following without target writes")
	body.live_pose=null;runtime.evaluate(0,false,body_id,app.video)
	check(Follow.same(dress.bone_transform(arm_dress),followed),"following resumes after the live owner releases")
	var sk: Skeleton3D=body.bones[arm_body].skeleton;var index: int=body.bones[arm_body].index
	var user_modifier:=PhysicalBoneSimulator3D.new();sk.add_child(user_modifier);user_modifier.active=false
	runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error") and Follow.same(dress.bone_transform(arm_dress),independent),"explicit user modifier is refused even when empty and inactive")
	user_modifier.free();runtime.evaluate(0,false,body_id,app.video)
	var original_rest: Transform3D=sk.get_bone_rest(index)
	var changed_rest:=original_rest;changed_rest.origin+=Vector3(.1,0,0);sk.set_bone_rest(index,changed_rest)
	runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error"),"a changed rest frame refuses the cached correspondence")
	sk.set_bone_rest(index,original_rest);runtime.evaluate(0,false,body_id,app.video)
	var temporary_parent:=Node3D.new();runtime.root.add_child(temporary_parent)
	dress.root.reparent(temporary_parent);runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error"),"external actor reparent cannot reuse the old common-space plan")
	dress.root.reparent(runtime.instance(group_id).root);temporary_parent.free();runtime.evaluate(0,false,body_id,app.video)
	var override_pose: Transform3D=sk.get_bone_global_pose(index);override_pose.origin+=Vector3(.3,0,0)
	sk.set_bone_global_pose_override(index,override_pose,1.,true);runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error"),"persistent global-only override refuses following")
	sk.clear_bones_global_pose_override();runtime.evaluate(0,false,body_id,app.video)
	var source_map: Dictionary=dress.root.get_meta("has_source_bones").duplicate(true)
	dress.root.set_meta("has_source_bones",{});runtime.evaluate(0,false,body_id,app.video)
	check(runtime.part_follow.reports[dress_id].has("error"),"changed prepared source identity refuses without guessing names")
	dress.root.set_meta("has_source_bones",source_map);runtime.evaluate(0,false,body_id,app.video)
	var preserved: Dictionary=app.current_world().duplicate(true)
	check(Storage.save_project(folder.path_join("snapshot"),app.video,app.keys,[],"",0,{}, {},{},true,preserved).is_empty(),"following and original independent poses save normally")
	var loaded:=Storage.load_project(folder.path_join("snapshot"))
	check(not loaded.has("error") and app.restore_world(loaded.world).is_empty(),"saved following reloads through ordinary WorldRuntime")
	runtime=app.renderer.world_runtime;dress=runtime.instance(dress_id);body=runtime.instance(body_id)
	var expected_pose: Dictionary=JSON.parse_string(JSON.stringify(target_data.pose,"",true,true))
	check(Follow.same(dress.bone_transform(arm_dress),followed) and dress.data.pose==expected_pose,"reload recomputes derived pose without baking it into authored data")
	check(runtime.instance(group_id).data.scale==1. and runtime.instance(group_id).data.metadata.character_parts.height_factor>0.,"shared six-foot reference remains owned by the group")
	check(FileAccess.get_sha256(body_path)==input_pins[body_path] and FileAccess.get_sha256(dress_path)==input_pins[dress_path],"source GLBs stay unchanged")
	malformed_cases(runtime,body_id,dress_id,group_id,arm_dress,independent)
	var args:=OS.get_cmdline_user_args()
	if args.size()>0:await native_case(args[0],folder)
	app.free();await settle()
	print("CHARACTER_PARTS_FOLLOW "+JSON.stringify({"checks":checks,"failures":failures}));quit(1 if failures else 0)

func malformed_cases(runtime: RefCounted,body_id: String,part_id: String,group_id: String,arm_id: String,independent: Transform3D) -> void:
	var part: RefCounted=runtime.instance(part_id);var group: RefCounted=runtime.instance(group_id)
	var saved: Dictionary=part.data.duplicate(true);var saved_group: Dictionary=group.data.duplicate(true)
	var saved_map: Dictionary=part.root.get_meta("has_source_bones").duplicate(true)
	var saved_secondary: Dictionary=part.root.get_meta("has_secondary_rig").duplicate(true)
	var reset: Callable=func():
		part.data=saved.duplicate(true);group.data=saved_group.duplicate(true)
		part.root.set_meta("has_source_bones",saved_map.duplicate(true));part.root.set_meta("has_secondary_rig",saved_secondary.duplicate(true))
		runtime.part_follow.plans.clear();runtime.evaluate(0,false,body_id,app.video)
	var refused: Callable=func():return runtime.part_follow.reports.get(part_id,{}).has("error") and Follow.same(part.bone_transform(arm_id),independent)
	reset.call();var bad:=saved.duplicate(true);bad.metadata.character_part=7
	var accepted: String=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"valid scalar optional part metadata cannot crash or silently enable following")
	reset.call();bad=saved.duplicate(true);bad.metadata.character_part.follow_body="true"
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"nonboolean following metadata is reported and stays independent")
	reset.call();group.data.metadata.character_parts=7;runtime.evaluate(0,false,body_id,app.video)
	check(refused.call() and runtime.follow_report(part_id).has("error"),"scalar group metadata reports an error instead of chained-get crash")
	reset.call();group.data.metadata.character_parts.follow_reference_id=[body_id];runtime.evaluate(0,false,body_id,app.video)
	check(refused.call(),"malformed body reference cannot silently select a body")
	reset.call();bad=saved.duplicate(true);bad.metadata["native_parameters"]=7
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"scalar import declarations safely refuse opt-in")
	reset.call();bad=saved.duplicate(true);bad.metadata["native_parameters"]={"native_parameters":7}
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"scalar nested native declarations safely refuse opt-in")
	reset.call();bad=saved.duplicate(true);bad.metadata["native_parameters"]={"native_parameters":{"bones":7}}
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"scalar native bone catalogue cannot bypass ownership guard")
	reset.call();bad=saved.duplicate(true);bad.metadata["native_parameters"]={"native_parameters":{"bones":[],"source_jiggle":7}}
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	check(accepted.is_empty() and refused.call(),"scalar procedural declaration cannot crash cached following")
	for invalid_count in [{},[],true,1.5]:
		reset.call();bad=saved.duplicate(true)
		bad.metadata["native_parameters"]={"native_parameters":{"bones":[],"source_jiggle":{"declared_jiggle_rule_count":invalid_count,"rules":[],"unsupported":[]}}}
		accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
		check(accepted.is_empty() and refused.call(),"nonintegral or nonnumeric procedural count is refused: "+str(invalid_count))
	reset.call();part.root.set_meta("has_secondary_rig",7);runtime.evaluate(0,false,body_id,app.video)
	check(refused.call(),"scalar secondary declarations safely refuse cached following")
	reset.call();part.root.set_meta("has_secondary_rig",{"error":"","chains":[7]});runtime.evaluate(0,false,body_id,app.video)
	check(refused.call(),"malformed secondary chain entries are reported safely")
	reset.call();var alias:=saved_map.duplicate(true);alias[1000000]=alias.values()[0];part.root.set_meta("has_source_bones",alias)
	runtime.evaluate(0,false,body_id,app.video)
	check(refused.call(),"added duplicate source-map alias invalidates the cached correspondence")
	reset.call();bad=saved.duplicate(true)
	bad.metadata["native_parameters"]={"native_parameters":{"bones":[{"name":"hip","parent":-1},{"name":"arm","parent":0}],"source_jiggle":{"declared_jiggle_rule_count":1,"rules":[{"native_bone_index":1,"native_bone_name":"arm"}],"unsupported":[]}}}
	accepted=runtime.restore_instance(part_id,bad);runtime.evaluate(0,false,body_id,app.video)
	var report: Dictionary=runtime.part_follow.reports.get(part_id,{})
	check(accepted.is_empty() and (report.has("error") or report.get("procedural",0)>0) and Follow.same(part.bone_transform(arm_id),independent) and part.data.pose==saved.pose,"metadata-only procedural ownership changes cannot reuse writable cached links")
	reset.call();part.root.set_meta("has_secondary_rig",{"error":"","chains":[{"joints":[{"binding":{"kind":"bone","id":arm_id}}]}]})
	runtime.evaluate(0,false,body_id,app.video)
	check(refused.call(),"changed declared secondary binding invalidates cached ownership")
	reset.call();group.data.metadata.character_parts.members=7
	check(Parts.describe(app.current_world(),group_id,int(app.video.duration_frames)).has("error"),"malformed member lists are rejected by the actual Parts API")
	reset.call();part.data.metadata.character_part=7
	if is_instance_valid(app.character_parts_editor.dialog):app.character_parts_editor.dialog.hide()
	app.character_parts_editor.open(group_id)
	var editor: Node=app.character_parts_editor
	check(not is_instance_valid(editor.dialog) or not editor.dialog.visible or editor.follow_switches[part_id].disabled,"Manage parts refuses or disables malformed part settings without a crash")
	reset.call();if is_instance_valid(editor.dialog):editor.dialog.hide()

func native_case(snapshot: String,folder: String) -> void:
	var loaded:=Storage.load_project(snapshot)
	check(not loaded.has("error") and app.restore_world(loaded.world).is_empty(),"actual prepared Junko snapshot opens without native conversion or proof gate")
	var runtime: RefCounted=app.renderer.world_runtime;var body_id:="";var dress_id:="";var group_id:=""
	for id in runtime.order:
		var row: Dictionary=runtime.instance(id).data
		if row.kind=="group":group_id=id
		elif row.metadata.character_part.role=="body":body_id=id
		elif row.metadata.character_part.role=="dress":dress_id=id
	var report: Dictionary=runtime.follow_report(dress_id)
	print("NATIVE_FOLLOW_MATCH "+JSON.stringify(report))
	check(not report.has("error") and report.matched>0 and report.procedural>0,"actual body/dress rigs match compatible joints and exclude procedural ownership")
	if report.has("error") or report.matched==0:return
	var plan: Dictionary=runtime.part_follow.plans[report.plan_key]
	var source: RefCounted=runtime.instance(body_id);var target: RefCounted=runtime.instance(dress_id)
	var chosen:=-1
	for index in plan.links:
		if plan.target.parents[index]>=0:chosen=index;break
	if chosen<0:check(false,"actual nonroot matched joint exists");return
	var source_id: String=plan.master.ids[plan.links[chosen]];var target_id: String=plan.target.ids[chosen]
	var before: Transform3D=target.bone_transform(target_id)
	var body_data: Dictionary=source.data.duplicate(true);body_data.pose[source_id]=pose(.25)
	check(runtime.restore_instance(body_id,body_data).is_empty() and apply_edit(settings(group_id,dress_id,body_id,true)).is_empty(),"actual body pose and dress opt-in apply")
	check(not Follow.same(before,target.bone_transform(target_id)) and not runtime.part_follow.reports[dress_id].has("error"),"actual separate dress joint responds to body pose")
	var target_data: Dictionary=target.data.duplicate(true);var followed: Transform3D=target.bone_transform(target_id)
	for i in range(20):runtime.evaluate(0,false,body_id,app.video)
	check(Follow.same(followed,target.bone_transform(target_id)) and target.data==target_data,"actual prepared dress repeats stably without authored pose changes")
	check(apply_edit(settings(group_id,dress_id,body_id,false)).is_empty() and Follow.same(before,target.bone_transform(target_id)),"actual dress Off restores independent native prepared pose")
	check(target.bones.size()==112 and source.bones.size()==145 and runtime.instances.size()==7,"actual six-part skeleton inventories and bundle remain separate")
