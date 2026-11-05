extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Contacts=Ranges.Contact.Contacts
const Secondary=preload("res://src/secondary_live.gd")
var app
var components:=false
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Contact physics watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func rig(id: String) -> RefCounted:return app.renderer.world_runtime.instance(id)
func pinned(data: Dictionary,at: float) -> bool:return not Contacts.active(data.animation_clips,at).is_empty()
func plant(id: String) -> Dictionary:
	app.set_frame(0);app.world_selection.select_entity(id)
	var actor:=rig(id);var track:=Contacts.capture(actor,0,1,"physics-pin-"+id)
	var result:=Ranges.edit(actor.data,0,49,track.segments[0],48)
	check(not result.has("error"),"contact range prepares: "+id)
	if result.has("error"):return {}
	if components:
		var value:=Model.Clips.transform(result.data)
		result=D.put_component(result.data,0,"position",value.position,"ease",48)
		var later: Array=value.position.duplicate();later[1]-=.015
		result=D.put_component(result.data,24,"position",later,"ease",48)
		result=D.put_component(result.data,9,"rotation_xyzw",value.rotation_xyzw,"linear",48)
		result=D.put_component(result.data,10,"scale",value.scale,"hold",48)
	app.renderer.world_runtime.restore_instance(id,result.data);app.set_frame(0)
	return rig(id).data.duplicate(true)
func endpoint_error(actor: RefCounted,at: float) -> float:
	var pose: Dictionary=actor.sample(at);var contact:=Contacts.active(actor.data.animation_clips,at);var error:=0.
	Contacts.apply_pose(actor,pose)
	for foot in contact.get("feet",[]):error=maxf(error,actor.bone_transform(foot.ids[2]).origin.distance_to(Model.Timeline.vector(foot.position)))
	return error
func angular_change(a: Dictionary,b: Dictionary,ids: Array) -> float:
	var value:=0.
	for id in ids:value=maxf(value,Model.Timeline.quaternion(a.get(id,Model.identity()).rotation_xyzw).angle_to(Model.Timeline.quaternion(b.get(id,Model.identity()).rotation_xyzw)))
	return value
func record_bodies(asset: String,all: bool) -> void:
	app.new_project();var world:=World.empty()
	for i in range(2):
		var data:=World.object(asset);data.id="record-"+str(i);data.position=[i*3,0,0];world.objects.append(data)
	app.restore_world(world);var originals:={}
	for data in world.objects:originals[data.id]=plant(data.id)
	app.set_frame(6);var physics=app.physics_editor;var record=physics.recording
	for data in world.objects:app.world_selection.select_entity(data.id);physics.change(true)
	await settled();app.world_selection.select_entity("record-0");record.scope.select(1 if all else 0)
	var history: int=app.history.size();check(record.start(),("World" if all else "Local")+" contact-body recording begins through the normal controller")
	while record.active and record.last_frame<10:await physics_frame
	var last: int=record.last_frame;check(record.finish(),"actual sampled contact-body take commits")
	var states:={};var correct:=true
	for id in originals:
		states[id]=rig(id).data.duplicate(true)
		if all or id=="record-0":
			correct=correct and pinned(states[id],5) and pinned(states[id],last+1)
			for at in range(6,last+1):correct=correct and not pinned(states[id],at)
		else:correct=correct and states[id]==originals[id]
	check(correct and not physics.is_running() and app.history.size()==history+1,"only recorded bodies release their sampled interval; outside and Local peers retain pins in one Undo")
	if components:
		var outside:=true
		for id in originals:
			var original_model:=Model.new();original_model.data=originals[id]
			outside=outside and states[id].format==D.FORMAT
			for at in range(49):
				if at<6 or at>last:outside=outside and rig(id).sample_authored_transform(at)==original_model.sample_authored_transform(at)
		check(outside,"component recording retains model version and exact roots outside its interval")
	app.undo();correct=true
	for id in originals:correct=correct and rig(id).data==originals[id]
	check(correct,"recording Undo restores every target's exact original contacts")
	app.redo();correct=true
	for id in states:correct=correct and rig(id).data==states[id]
	check(correct,"recording Redo restores the exact take and outside contacts")
func run() -> void:
	components="--components" in OS.get_cmdline_user_args()
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var asset:=folder.path_join("figure.glb");preload("res://src/tutorial_assets.gd").figure(asset);var sha:=FileAccess.get_sha256(asset)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var actor:=World.object(asset);actor.id="falling"
	var world:=World.empty();world.objects=[actor];app.restore_world(world)
	var original:=plant(actor.id);var physics=app.physics_editor
	app.set_frame(12);app.world_selection.select_entity(actor.id);var history: int=app.history.size()
	physics.toggle.button_pressed=true;await settled()
	check(physics.body_active(actor.id) and rig(actor.id).data==original and app.history.size()==history,"body simulation starts without consuming authored contacts or recording keys")
	for i in range(90):await physics_frame
	var simulation: RefCounted=physics.simulations[actor.id];var frozen: Dictionary=simulation.pose()
	var changed:=false
	for id in frozen:
		changed=changed or Model.Timeline.vector(frozen[id].position).length()>.1
	check(changed,"actual gravity has moved the live body away from its planted pose")
	physics.toggle.button_pressed=false;await settled()
	var after: Dictionary=rig(actor.id).data.duplicate(true);var sampled: Dictionary=rig(actor.id).sample(12,true)
	check(not physics.active(actor.id) and rig(actor.id).evaluation_error.is_empty() and sampled==frozen,"Physics OFF freezes the actual fallen pose without a planted-foot correction or reach error")
	check(not pinned(after,12) and pinned(after,11) and pinned(after,13),"body OFF releases only the current frame and retains surrounding authored contacts")
	check(app.history.size()==history+1 and rig(actor.id).authored_keys()==(D.authored_keys(original,48) if components else Model.body_animation().authored_keys(original)),"freeze and one-frame release share one Undo and create no simulation keys")
	app.undo();check(rig(actor.id).data==original,"freeze Undo restores the exact original contact record")
	app.redo();check(rig(actor.id).data==after,"freeze Redo restores the exact pose and contact release")
	# A fragmented logical contact can recur after a release inside one recording.
	var released:=Ranges.edit(original,10,11,{},48)
	var slice:=Contacts.slice(released.data.animation_clips,6,20,100)
	check(Contacts.validate(slice).is_empty() and slice.segments.size()==2 and slice.segments[0].from==100 and slice.segments[0].to==104 and slice.segments[1].from==105 and slice.segments[1].to==114,"contact slicing preserves a one-frame release and merges the recurring tail without duplicate IDs")
	await record_bodies(asset,false);await record_bodies(asset,true)
	# Refusing a release that exceeds the piece limit must leave the live solver on.
	app.new_project();world=World.empty();world.objects=[actor];app.restore_world(world);original=plant(actor.id)
	var dense:=original.duplicate(true)
	for boundary in range(2,32):dense=(D.edit_clip(dense,"split","",boundary,48) if components else Model.Clips.split(dense,boundary)).data
	app.renderer.world_runtime.restore_instance(actor.id,dense);app.set_frame(40);app.world_selection.select_entity(actor.id);physics.change(true);await settled();history=app.history.size()
	check(dense.animation_clips.size()==32 and not physics.freeze(actor.id) and physics.body_active(actor.id) and rig(actor.id).data==dense and app.history.size()==history and app.status.text.contains("32 animation pieces"),"over-limit contact release refuses freeze before disposing the live solver or changing history")
	physics.clear()
	# The complete frozen FK draft, not just its small contact-release descriptor,
	# must fit alongside the existing world and editor metadata.
	app.renderer.world_runtime.restore_instance(actor.id,original);app.set_frame(12);app.world_selection.select_entity(actor.id)
	var release:=Ranges.edit(original,12,13,{},48);var budget_world: Dictionary=app.current_world();budget_world.objects[0]=release.data
	var padding: int=1024*1024-app.pose_editor.contacts.metadata_bytes(budget_world)-512
	var near_limit:=original.duplicate(true);near_limit.metadata["budget_probe"]="x".repeat(padding)
	app.renderer.world_runtime.restore_instance(actor.id,near_limit);physics.change(true);await settled();history=app.history.size()
	var release_only:=Ranges.edit(near_limit,12,13,{},48);budget_world=app.current_world();budget_world.objects[0]=release_only.data
	check(app.pose_editor.contacts.metadata_bytes(budget_world)<1024*1024,"the actual pre-freeze world and contact release fit below the project metadata limit")
	check(not physics.freeze(actor.id) and physics.body_active(actor.id) and rig(actor.id).data==near_limit and app.history.size()==history and app.status.text.contains("metadata"),"dense frozen pose overflow refuses before stopping physics or changing authored state")
	physics.clear();app.renderer.world_runtime.restore_instance(actor.id,original)
	# Actual declared VRM springs exercise secondary-only versus combined ownership.
	var native:=preload("res://tests/native_sample_paths.gd").vrm("AvatarSample_A.vrm");var native_tested:=FileAccess.file_exists(native);var peak:=0.
	if native_tested:
		var native_sha:=FileAccess.get_sha256(native);app.new_project();app.pose_editor.add_model(native)
		while app.source_import.pid>0:await process_frame
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		await settled();var native_rig: RefCounted=app.renderer.active_model();var native_id: String=native_rig.data.id
		var before:=plant(native_id)
		var native_foot: Dictionary=Contacts.active(before.animation_clips,0).feet[0];var knee_target: Vector3=rig(native_id).bone_transform(native_foot.ids[0]).origin+Vector3(0,0,-.4)
		before=preload("res://src/contact_correction.gd").edit(before,0,49,0,{"pole":[knee_target.x,knee_target.y,knee_target.z]},48).data;app.renderer.world_runtime.restore_instance(native_id,before)
		var airflow=preload("res://src/airflow.gd");var fan_path:=folder.path_join("fan.glb");airflow.create_asset(fan_path)
		var fan:=Model.definition(fan_path);fan.position=[0,.5,-1];fan.metadata["airflow"]=airflow.defaults();fan.metadata.airflow.speed=30.;fan.metadata.airflow.radius=10.;app.append_object(fan,"model")
		app.set_frame(6);app.world_selection.select_entity(native_id);physics=app.physics_editor;history=app.history.size()
		physics.hair_toggle.button_pressed=true
		while physics.pending.has(native_id):await process_frame
		await settled();check(physics.active(native_id) and not physics.body_active(native_id),"real native VRM Hair & clothes starts with the feet still planted")
		var live: RefCounted=physics.simulations[native_id];var start_pose: Dictionary=live.pose();var hair_ids:=[]
		for chain in live.runner.chains:hair_ids.append_array(chain.ids)
		for i in range(40):await physics_frame
		check(angular_change(start_pose,live.pose(),hair_ids)>.001,"the real fan drives measurable native hair motion while the body remains planted")
		physics.hair_toggle.button_pressed=false;await settled()
		check(rig(native_id).data.animation_clips==before.animation_clips and pinned(rig(native_id).data,6) and rig(native_id).evaluation_error.is_empty(),"secondary-only OFF freezes hair without releasing authored feet")
		app.undo();check(rig(native_id).data==before and app.history.size()==history,"hair freeze and exact contact restoration remain one Undo")
		app.set_frame(6);physics.hair_toggle.button_pressed=true
		while physics.pending.has(native_id):await process_frame
		await settled();var record=physics.recording;record.scope.select(0);check(record.start(),"secondary-only Local Record starts normally")
		while record.active and record.last_frame<18:await physics_frame
		var end: int=record.last_frame;var moving:=angular_change(record.samples[native_id][0].pose,record.samples[native_id][-1].pose,hair_ids)>.001
		check(record.finish() and moving,"secondary-only recorded take commits actual moving hair with planted feet")
		var recorded: Dictionary=rig(native_id).data.duplicate(true);var all_pinned:=true
		for half in range(12,end*2+1):
			var at:=float(half)/2;all_pinned=all_pinned and pinned(recorded,at);peak=maxf(peak,endpoint_error(rig(native_id),at))
		check(all_pinned and peak<.0002 and pinned(recorded,5) and pinned(recorded,end+1),"recorded secondary motion retains exact contact ownership and fractional foot stability inside and outside the take")
		check(Model.Timeline.vector(Contacts.active(recorded.animation_clips,12).feet[0].pole)==knee_target,"secondary-only capture retains version2 world knee targets")
		app.undo();check(rig(native_id).data==before,"secondary-only Record Undo restores the complete original record")
		app.redo();check(rig(native_id).data==recorded,"secondary-only Record Redo restores retained pins")
		app.set_frame(12);physics.change(true);await settled();physics.change_hair(true)
		while physics.pending.has(native_id):await process_frame
		await settled();check(physics.body_active(native_id) and physics.simulations[native_id] is Secondary,"real native combined body/hair solver starts")
		for i in range(40):await physics_frame
		physics.change(false);await settled();check(not pinned(rig(native_id).data,12) and pinned(rig(native_id).data,11) and pinned(rig(native_id).data,13) and rig(native_id).evaluation_error.is_empty(),"combined OFF releases body-owned frame and freezes hair together")
		app.undo();app.set_frame(12);physics.change(true);await settled();physics.change_hair(true)
		while physics.pending.has(native_id):await process_frame
		await settled();check(record.start(),"combined body/hair Record begins")
		while record.active and record.last_frame<16:await physics_frame
		end=record.last_frame;var finished: bool=record.finish();var combined: Dictionary=rig(native_id).data.duplicate(true);var body_owned:=true
		for at in range(12,end+1):body_owned=body_owned and not pinned(combined,at)
		check(finished and body_owned and pinned(combined,11) and pinned(combined,end+1),"combined recorded motion releases precisely the body-owned interval and keeps outside pins")
		app.undo();check(rig(native_id).data==recorded,"combined recording Undo restores exact hair-only take and contacts")
		app.redo();check(rig(native_id).data==combined,"combined recording Redo restores exact body/hair interval")
		var reach_errors:={};var prior_model:=Model.new();prior_model.data=recorded
		for at in range(49):
			rig(native_id).sample(at)
			if not rig(native_id).evaluation_error.is_empty():reach_errors[at]={"error":rig(native_id).evaluation_error,"before_pose":prior_model.sample_body(at),"after_pose":rig(native_id).sample_body(at),"before_root":prior_model.sample_transform(at),"after_root":rig(native_id).sample_transform(at)}
		var diagnosis:=FileAccess.open(folder.path_join("reach-diagnostic.json"),FileAccess.WRITE);diagnosis.store_string(JSON.stringify(reach_errors,"",true,true));diagnosis.close()
		check(reach_errors.is_empty(),"combined take preserves reachable authored contacts at every outside frame")
		app.set_frame(0);app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(130,40),8,Color.CYAN,false);app.changed()
		app.set_frame(14);app.world_selection.select_entity(native_id);app.pose_editor.frame_model();app.keys=[Model.Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
		var has_path:=folder.path_join("contact-physics.has");app.has_project.save_file(has_path,"packed")
		while app.has_project.pid>0:await process_frame
		app.new_project();app.has_project.open_file(has_path)
		while app.has_project.pid>0:await process_frame
		app.set_frame(14);var reference: Image=await app.renderer.capture(app.keys,app.layers,14,true);reference.save_png(folder.path_join("combined-record-frame.png"))
		var export_error: String=await app.export_movie(folder)
		print("CONTACT_EXPORT "+export_error)
		check(export_error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000015.png")).get_data(),"real packed contact/physics take reopens and matches actual MP4 frames with independent paint")
		app.set_meta("contact_test_movie",app.last_export_folder.path_join("movie.mp4"))
		check(FileAccess.get_sha256(native)==native_sha,"original native VRM bytes remain unchanged")
	else:print("SKIP private native VRM secondary/contact case")
	check(FileAccess.get_sha256(asset)==sha,"original standardized model bytes remain unchanged")
	var result:={"checks":checks,"failures":failures,"folder":folder,"native_tested":native_tested,"endpoint_error":peak,"movie":app.get_meta("contact_test_movie","")};var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();app.free();await settled();print("CONTACT_PHYSICS "+JSON.stringify(result));quit(0 if failures==0 else 1)
