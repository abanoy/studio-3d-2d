extends SceneTree
# Real manual SpringBone runners; no graphics or owner inputs.
const Model=preload("res://src/model.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func actor(id: String) -> RefCounted:
	var value:=Model.new();value.root=Node3D.new();root.add_child(value.root)
	var sk:=Skeleton3D.new();sk.name="Rig";sk.set_animate_physical_bones(false);value.root.add_child(sk)
	for name in ["Body","HairA","HairB","HairC","HairEnd"]:sk.add_bone(name)
	for i in range(5):
		sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,Vector3(0,2,0) if i==0 else Vector3(0,0,.25) if i==1 else Vector3(0,-.15,.4)))
		if i>0:sk.set_bone_parent(i,i-1)
	var turn:=Basis(Vector3.RIGHT,PI*.5);sk.set_bone_rest(0,Transform3D(turn,Vector3(0,2,0)));sk.set_bone_rest(1,Transform3D(turn.inverse(),turn.inverse()*Vector3(0,0,.25)));sk.reset_bone_poses()
	value.data={"format":"studio_model_1","id":id,"name":"Preview helper","source":"","sha256":id.repeat(64),"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.,"visible":true,"reference_only":false,"start_frame":0,"parent_id":"","pose":{},"pose_keys":[],"draft_frame":0,"metadata":{}}
	value.inventory(value.root)
	var joints: Array=[]
	for name in ["HairA","HairB","HairC","HairEnd"]:joints.append({"binding":{"kind":"bone","id":"Rig::"+name},"stiffness":1.,"drag":.45,"radius":.005,"gravity":0.,"gravity_direction":[0,-1,0]})
	value.root.set_meta("has_secondary_rig",{"source_family":"HAS","chains":[{"joints":joints,"center":{"kind":"bone","id":"Rig::Body"},"colliders":[],"end_extension":0.}],"colliders":[]})
	return value
func configs(runner: RefCounted) -> Array:
	var result: Array=[]
	for chain in runner.chains:
		for i in range(chain.spring.get_joint_count(0)):result.append([chain.spring.get_joint_stiffness(0,i),chain.spring.get_joint_gravity(0,i),chain.spring.get_joint_drag(0,i),chain.spring.get_joint_radius(0,i)])
	return result
func run() -> void:
	var source: RefCounted=actor("a");var target: RefCounted=actor("b")
	source.data.metadata={Motion.KEY:{"format":Motion.FORMAT,"mode":"natural"},"native_parameters":{"humanoid":{"hips":{"node_name":"Body","other_private_detail":"omit"}},"private_import_detail":[7,9]},"unrelated_report":"omit"}
	var source_bytes: PackedByteArray=var_to_bytes(source.data);var target_bytes: PackedByteArray=var_to_bytes(target.data)
	var definition: Dictionary=target.root.get_meta("has_secondary_rig").duplicate(true)
	var context: Dictionary=Motion.preview_context(source,target,definition)
	check(not context.has("error") and Motion.preview_error(context,target,definition).is_empty(),"checked preview binds its source candidate and exact filtered groups")
	check(context.policy.metadata.size()==2 and not context.policy.metadata.native_parameters.has("private_import_detail") and context.policy.metadata.native_parameters.humanoid.hips.size()==1,"only the selected mode and minimal humanoid flags enter the clone context")
	var space:=SubViewport.new();space.own_world_3d=true;space.render_target_update_mode=SubViewport.UPDATE_DISABLED;root.add_child(space)
	var live: Dictionary=Spring.construct(source);var preview: Dictionary=Spring.construct(target,definition,space,context)
	check(not live.has("error") and not preview.has("error"),"ordinary live and explicitly opted-in filtered preview both construct")
	if live.has("error") or preview.has("error"):quit(1);return
	check(preview.runner.host.get_viewport()==space and space.find_world_3d().space!=source.root.get_world_3d().space,"preview retains its separate disposable physics world")
	check(configs(live.runner)==configs(preview.runner),"preview has exactly the same effective Natural joint settings as live")
	for i in range(4):await process_frame
	var identical:=true
	for i in range(120):
		for value in [source,target]:value.live_pose={};value.apply_current(0,true)
		var first: Dictionary=live.runner.step(1./120.,Vector3(0,0,-.06));var second: Dictionary=preview.runner.step(1./120.,Vector3(0,0,-.06))
		if first.has("error") or second.has("error"):identical=false;break
		identical=identical and first.pose==second.pose
		source.live_pose=first.pose;target.live_pose=second.pose;source.apply_current(0,true);target.apply_current(0,true)
	check(identical,"rotated-center preview and live emit exact matching FK under the same world-front force")
	check(var_to_bytes(source.data)==source_bytes and var_to_bytes(target.data)==target_bytes,"preview leaves original and stripped candidate authored metadata untouched")
	source.data.metadata[Motion.KEY].mode="keep_shape"
	check(preview.runner.step(1./120.,Vector3.ZERO).has("error"),"changing source preset rejects a stale running preview before stepping")
	source.data.metadata[Motion.KEY].mode="natural"
	source.data.metadata.native_parameters.humanoid.hips.node_name="Other"
	check(preview.runner.step(1./120.,Vector3.ZERO).has("error"),"changed core exclusion flags invalidate the preview")
	source.data.metadata.native_parameters.humanoid.hips.node_name="Body"
	var sha: String=source.data.sha256;source.data.sha256="0".repeat(64)
	check(preview.runner.step(1./120.,Vector3.ZERO).has("error"),"source identity replacement cannot borrow an old tuning context")
	source.data.sha256=sha;sha=target.data.sha256;target.data.sha256="0".repeat(64)
	check(preview.runner.step(1./120.,Vector3.ZERO).has("error"),"candidate source replacement cannot use the old tuning context")
	target.data.sha256=sha
	var wrong: Dictionary=context.duplicate(true);wrong.target_root=-1
	check(Spring.construct(target,definition,space,wrong).has("error"),"context for another candidate root refuses before scratch construction")
	var changed: Dictionary=definition.duplicate(true);changed.chains[0].joints[1].stiffness=.2
	check(Spring.construct(target,changed,space,context).has("error"),"changing filtered groups or settings rejects a stale context")
	var unopted: Dictionary=Spring.construct(source,source.root.get_meta("has_secondary_rig"),space)
	check(not unopted.has("error") and not unopted.runner.chains[0].natural_gravity and not unopted.runner.chains[0].world_airflow,"unopted private probes retain original parameters and force semantics")
	if not unopted.has("error"):unopted.runner.dispose()
	source.data.metadata[Motion.KEY]=true
	check(Motion.preview_context(source,target,definition).has("error"),"invalid selected setting cannot enter a wind clone")
	source.data.metadata[Motion.KEY]={"format":Motion.FORMAT,"mode":"natural"}
	check(Motion.preview_context(source,target,{"source_family":"VRM1"}).is_empty(),"imported native preview definitions receive no generated tuning reinterpretation")
	root.remove_child(source.root)
	check(preview.runner.step(1./120.,Vector3.ZERO).has("error"),"detached original owner invalidates the preview")
	root.add_child(source.root)
	live.runner.dispose();preview.runner.dispose();space.free();source.live_pose=null;target.live_pose=null;source.apply(0,true);target.apply(0,true)
	check(var_to_bytes(source.data)==source_bytes and var_to_bytes(target.data)==target_bytes,"stale refusals and disposal preserve both authored owners")
	for value in [source,target]:value.release_render_bounds();value.root.free()
	await process_frame
	print("GENERATED_SECONDARY_PREVIEW "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"graphics_used":false}));quit(0 if failures==0 else 1)
