extends SceneTree
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
var app
var folder: String
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Existing native joint watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func ready(job) -> void:
	while job.pid>0:await process_frame
	await settle()
func difference(a: Image,b: Image) -> Dictionary:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0;var total:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1;total+=absi(int(aa[i])-int(bb[i]))
	return {"changed":changed,"mean":float(total)/aa.size()}
func finish(extra: Dictionary={}) -> void:
	var result:={"checks":checks,"failures":failures};result.merge(extra)
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"",true,true))
	print("EXISTING_NATIVE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
func start_hair(id: String) -> bool:
	app.world_selection.select_entity(id,false);await settle();app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(id):await process_frame
	await settle();return app.physics_editor.active(id)
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var source: String=args[1];var with_ribbon: bool="--with-ribbon" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.pose_editor.add_model(source).is_empty(),"actual native Reimu loads through ordinary Add model")
	await settle();app.physics_editor.clear();var actor=app.renderer.active_model();var id: String=actor.data.id
	var initial_definition: Dictionary=actor.root.get_meta("has_secondary_rig",{});var initial_chains: Array=initial_definition.get("chains",[]).duplicate(true)
	if with_ribbon:
		check(initial_definition.get("error","").is_empty() and initial_chains.size()==1,"explicit composition input retains its checked weighted-ribbon spring")
		var provenance: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("input-provenance.json")))
		actor.data.metadata["generated_helpers"]=provenance.ribbon_report.duplicate(true)
		actor.data.metadata["generated_helper_history"]=[provenance.ribbon_report.duplicate(true)]
	var head: String=actor.root.get_meta("has_source_bones",{}).get(16,"")
	check(not head.is_empty(),"native head binding is available for a non-rest pose")
	if head.is_empty():finish();return
	var q:=Quaternion(Vector3.UP,.23);actor.data.pose[head]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]};app.pose_editor.apply_frame();app.changed();app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)];await settle()
	var original: Dictionary=actor.data.duplicate(true);var old_ids: Array=actor.order.duplicate();var sha:=FileAccess.get_sha256(source);var history: int=app.history.size();var shots: Array=app.keys.duplicate(true)
	var before: Image=await app.renderer.capture(app.keys,app.layers,0,true);before.save_png(folder.path_join("before.png"))
	var helper=app.physics_editor.helper_editor;helper.open(true);await ready(helper)
	var index:=-1
	for i in range(helper.assessment.get("regions",[]).size()):
		var row: Dictionary=helper.assessment.regions[i]
		if int(row.node)==80 and int(row.primitive)==1 and int(row.component)==5:index=i;break
	check(index>=0,"native connected Back hair region is found without substituting the ribbon")
	if index<0:finish();return
	helper.parts.select(index);helper.select_part(index);await ready(helper)
	check(not helper.preview.can_apply and helper.existing_toggle.visible and not helper.existing_toggle.button_pressed,"mixed native Back hair retains old generation refusal and offers explicit existing-joint review")
	check(actor.data==original and app.history.size()==history,"opening the existing-joint option changes no pose, keys or history")
	helper.existing_toggle.button_pressed=true;await ready(helper)
	check(helper.preview.get("mode","")=="existing_joints" and helper.preview.can_apply and not helper.apply_button.disabled,"ordinary opt-in makes actual Back hair configurable")
	check(helper.preview.affected_regions.size()==3 and int(helper.preview.affected_vertices)==1369,"review discloses all three surfaces sharing the native Back hair joints")
	check(helper.preview.existing_chain.joint_nodes==[11.,10.,9.] and app.canvas.review_chain.size()==4 and app.canvas.review_lines.size()>0,"review shows actual native chain and its nondeforming endpoint")
	check(helper.patch_toggle.disabled and helper.anchors.disabled and helper.info.text.contains("3 connected regions"),"review explains shared scope rather than promising patch isolation or arbitrary reattachment")
	helper.window.get_texture().get_image().save_png(folder.path_join("review.png"))
	helper.apply_button.pressed.emit();await ready(helper);actor=app.renderer.world_runtime.instance(id)
	var definition: Dictionary=actor.root.get_meta("has_secondary_rig",{});var derived: Dictionary=actor.data.duplicate(true)
	check(not is_instance_valid(helper.window) and definition.get("error","").is_empty() and definition.get("chains",[]).size()==initial_chains.size()+1,"reviewed native chain installs as a usable source-bound spring")
	if not definition.get("error","").is_empty() or definition.get("chains",[]).size()!=initial_chains.size()+1:finish({"definition":definition});return
	if with_ribbon:
		check(definition.chains[0]==initial_chains[0],"Back hair setup retains the original weighted-ribbon chain exactly")
		check(actor.data.metadata.generated_helper_history.size()==2 and actor.data.metadata.generated_helper_history[0]==original.metadata.generated_helpers,"Back hair setup appends its provenance without overwriting ribbon history")
	check(actor.data.pose==original.pose and actor.authored_keys().is_empty() and app.keys==shots and app.history.size()==history+1,"existing joints preserve non-rest manual pose and camera as one Undo edit")
	check(old_ids.all(func(b):return actor.bones.has(b)) and actor.data.metadata.generated_helpers.changed_vertices==0,"original native bones remain and setup reports zero changed skin vertices")
	var after: Image=await app.renderer.capture(app.keys,app.layers,0,true);var bind_difference:=difference(before,after);after.save_png(folder.path_join("after.png"))
	check(bind_difference.changed<=384 and bind_difference.mean<.002,"adding an endpoint and spring declaration preserves actual non-rest native pixels")
	app.undo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==original,"one Undo restores exact native asset and authored pose")
	app.redo();await settle();actor=app.renderer.world_runtime.instance(id);check(actor.data==derived,"one Redo restores exact reviewed chain and unchanged pose")
	app.world_selection.select_entity(id,false);await settle();app.physics_editor.fan_editor.add_fan();await settle();app.physics_editor.fan_editor.speed.value=12;app.physics_editor.fan_editor.enabled.button_pressed=false;await settle()
	var fan=app.renderer.active_model();var fan_id: String=fan.data.id;actor=app.renderer.world_runtime.instance(id)
	var target: Vector3=actor.bone_transform(definition.chains[-1].joints[1].binding.id).origin
	# Show the actual back hair with a side-blowing fan outside the sightline;
	# auto-Aim intentionally places a fan toward the camera and can occlude it.
	fan.data.position=[target.x+1.5,target.y-.85,target.z];var facing:=Quaternion(Vector3.UP,-PI/2);fan.data.rotation_xyzw=[facing.x,facing.y,facing.z,facing.w]
	app.pose_editor.apply_frame();app.renderer.camera.position=target+Vector3(0,.15,-1.5);app.renderer.camera.look_at(target)
	app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)];app.changed();await settle()
	var world: Dictionary=app.current_world().duplicate(true)
	check(await start_hair(id),"actual existing native joints start through Hair & clothes")
	if not app.physics_editor.active(id):finish();return
	for i in range(120):await physics_frame
	var quiet_pose: Dictionary=app.physics_editor.simulations[id].pose().duplicate(true);var quiet: Image=await app.renderer.capture(app.keys,app.layers,0,false)
	app.physics_editor.clear();check(app.restore_world(world).is_empty(),"fan comparison restores the exact same native starting scene")
	app.world_selection.select_entity(fan_id,false);await settle();app.physics_editor.fan_editor.enabled.button_pressed=true;await settle()
	var expected_off: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(await start_hair(id),"actual existing native joints restart with the fan enabled")
	if not app.physics_editor.active(id):finish();return
	actor=app.renderer.world_runtime.instance(id);var authored: Dictionary=actor.data.duplicate(true)
	for i in range(120):await physics_frame
	var windy: Dictionary=app.physics_editor.simulations[id].pose();var wind_radians:=0.0
	for node in [11,10,9]:
		var bone: String=actor.root.get_meta("has_source_bones",{}).get(node,"")
		if windy.has(bone) and quiet_pose.has(bone):wind_radians=maxf(wind_radians,Timeline.quaternion(windy[bone].rotation_xyzw).angle_to(Timeline.quaternion(quiet_pose[bone].rotation_xyzw)))
	var windy_image: Image=await app.renderer.capture(app.keys,app.layers,0,false);windy_image.save_png(folder.path_join("wind.png"))
	check(wind_radians>.005 and quiet.get_data()!=windy_image.get_data(),"fan changes existing Back hair joints and their actual rendered surfaces")
	check(actor.data==authored,"unrecorded native joint simulation authors no pose or animation")
	app.physics_editor.hair_toggle.button_pressed=false;await settle();actor=app.renderer.world_runtime.instance(id)
	check(not app.physics_editor.active(id) and actor.data==authored,"Hair & clothes off stops this chain without authoring deformation")
	var restored: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(restored.get_data()==expected_off.get_data(),"disabling native Back hair motion restores the non-rest authored composite")
	app.video.duration_frames=24;app.has_project.save_file(folder.path_join("Back hair.has"),"packed");await ready(app.has_project)
	check(not app.has_project.path.is_empty() and not app.dirty,"ordinary Save packs the configured existing chain")
	app.new_project();app.has_project.open_file(folder.path_join("Back hair.has"));await ready(app.has_project);actor=app.renderer.world_runtime.instance(id)
	check(actor!=null and actor.data.metadata.generated_helpers.mode=="existing_joints" and actor.root.get_meta("has_secondary_rig").chains.size()==initial_chains.size()+1,"normal packed reopen restores the native chain setup")
	var error: String=await app.export_movie(folder);check(error.is_empty(),"native existing-joint project exports a real movie")
	check(FileAccess.get_sha256(source)==sha,"native source stays checksum-exact through reviewed setup, fan and Save")
	finish({"bind_difference":bind_difference,"wind_radians":wind_radians,"movie":app.last_finished_movie,"derived":derived.sha256})
