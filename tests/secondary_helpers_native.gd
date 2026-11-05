extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Native helper watchdog expired");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await RenderingServer.frame_post_draw
func difference(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"changed":changed,"mean":float(total)/aa.size()}
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-plans.json")))
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("native-recovery");root.add_child(app)
	for i in range(3):await process_frame
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("native-cache")
	var metrics:={}
	for plan in plans:
		app.new_project();var data:=Model.definition(plan.source);data.metadata["native_origin"]={"fixture":plan.label,"source_sha256":plan.sha256};app.append_object(data,"model")
		var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var old_ids: Array=actor.order.duplicate();var before: Dictionary=actor.data.duplicate(true)
		app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		var neutral: Image=await app.renderer.capture(app.keys,app.layers,0,true);neutral.save_png(folder.path_join(plan.label+"-original.png"))
		var world: Dictionary=app.current_world();world.objects[0].source=plan.derived;world.objects[0].sha256=FileAccess.get_sha256(plan.derived);world.objects[0].metadata["generated_helpers"]=plan.report
		var error: String=app.restore_world(world);check(error.is_empty(),"native derived model preserves existing bindings: "+plan.label)
		if not error.is_empty():continue
		actor=app.renderer.world_runtime.instance(id);var same: Image=await app.renderer.capture(app.keys,app.layers,0,true);var delta:=difference(neutral,same)
		check(delta.changed<=384 and delta.mean<.002,"native generated joints preserve actual neutral pixels: "+plan.label)
		check(actor.order.size()==old_ids.size()+4 and old_ids.all(func(b):return actor.bones.has(b)),"original native bone IDs remain intact: "+plan.label)
		var def: Dictionary=actor.root.get_meta("has_secondary_rig");check(def.error.is_empty() and def.chains.size()==1,"native helper descriptor binds exact source nodes: "+plan.label)
		if not def.error.is_empty() or def.chains.is_empty():continue
		var helper: String=def.chains[0].joints[0].binding.id;var q:=Quaternion(Vector3.BACK,.6)
		actor.data.pose[helper]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
		var bent: Image=await app.renderer.capture(app.keys,app.layers,0,true);var deformation:=difference(same,bent);bent.save_png(folder.path_join(plan.label+"-deformed.png"))
		check(deformation.changed>0,"native weighted surface really deforms under a generated joint: "+plan.label)
		var pose: Dictionary=actor.data.pose.duplicate(true);var project: String=folder.path_join(plan.label+"-helpers.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
		app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id)
		var saved_pose: Dictionary=JSON.parse_string(JSON.stringify(pose,"",true,true))
		check(actor!=null and actor.data.pose==saved_pose and actor.data.metadata.native_origin==before.metadata.native_origin and actor.root.get_meta("has_secondary_rig").chains.size()==1,"native pose and source provenance survive packed HAS: "+plan.label)
		if actor!=null and actor.data.pose!=saved_pose:print("POSE_DIAGNOSTIC ",JSON.stringify(pose)," reopened ",JSON.stringify(actor.data.pose))
		check(FileAccess.get_sha256(plan.source)==plan.sha256,"native original remains unchanged: "+plan.label)
		metrics[plan.label]={"bind_difference":delta,"deformation":deformation,"original_bones":old_ids.size()}
	var result:={"checks":checks,"failures":failures,"metrics":metrics};var f:=FileAccess.open(folder.path_join("native-result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("HELPER_NATIVE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
