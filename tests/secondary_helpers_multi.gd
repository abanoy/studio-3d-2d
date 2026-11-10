extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const Model=preload("res://src/model.gd")
const Timeline=preload("res://src/timeline.gd")
const Airflow=preload("res://src/airflow.gd")
const SecondaryRig=preload("res://src/secondary_rig.gd")
var checks:=0
var failures:=0
var movies: Array=[]
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Multiple helper watchdog expired");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func visible_change(a: Image,b: Image) -> bool:
	var aa:=a.get_data();var bb:=b.get_data();var changed:=0
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changed+=1
		if changed>50:return true
	return false
func add_part(app,label: String,second: bool) -> bool:
	var helper=app.physics_editor.helper_editor;helper.button.pressed.emit();await wait_job(helper)
	check(not helper.preview.is_empty() and not helper.apply_button.disabled,"review can add an unrigged part beside existing chains: "+label)
	if helper.preview.is_empty():helper.close();return false
	if second:check(helper.parts.is_item_disabled(1) and not helper.parts.is_item_disabled(2) and int(helper.request.component)==1,"second review protects the first panel and selects the remaining panel: "+label)
	helper.apply_button.pressed.emit();await wait_job(helper)
	return not is_instance_valid(helper.window)
func sample(app,source: String,label: String,folder: String) -> void:
	app.new_project();app.append_object(Model.definition(source),"model");var actor: RefCounted=app.renderer.active_model();var id: String=actor.data.id;var base_bones: int=actor.order.size()
	app.renderer.camera.position=Vector3(0,1.2,4);app.renderer.camera.look_at(Vector3(0,1.1,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,48)]
	var native: Array=actor.root.get_meta("has_secondary_rig").chains.duplicate(true);var n: int=native.size()
	check(n==(0 if label=="plain" else 1),"fixture retains its original native spring family: "+label)
	if n>0:check(native[0].joints[0].binding.kind=="bone","native fixture declares a genuinely poseable skin joint: "+label)
	if not await add_part(app,label,false):check(false,"first Apply completes: "+label);return
	actor=app.renderer.world_runtime.instance(id);var def: Dictionary=actor.root.get_meta("has_secondary_rig");check(def.error.is_empty() and def.chains.size()==n+1,"first HAS chain coexists with native springs: "+label)
	if def.chains.size()!=n+1:return
	var first: String=def.chains[-1].joints[1].binding.id
	app.world_selection.select_entity(id,false);app.mode.select(2);app.change_mode(2);app.pose_editor.selected=first;app.pose_editor.operation.select(0);app.pose_editor.refresh_values();app.pose_editor.fields[2].value=18;app.pose_editor.apply_numeric();await settled()
	var before: Dictionary=actor.data.duplicate(true);var first_chains: Array=def.chains.duplicate(true);var original_keys: Array=actor.authored_keys().duplicate(true);var history: int=app.history.size();var old_ids: Array=actor.order.duplicate()
	if not await add_part(app,label,true):check(false,"second Apply completes: "+label);return
	actor=app.renderer.world_runtime.instance(id);def=actor.root.get_meta("has_secondary_rig")
	check(def.error.is_empty() and def.chains.size()==n+2 and actor.order.size()==base_bones+8,"one model now contains both independently generated chains: "+label)
	check(old_ids.all(func(b):return actor.bones.has(b)) and actor.authored_keys()==original_keys and app.history.size()==history+1,"second Apply retains first-joint animation/IDs as one Undo: "+label)
	check(def.chains.slice(0,n+1)==first_chains,"existing native and generated chain parameters/bindings remain intact: "+label)
	check(actor.data.metadata.generated_helper_history.size()==2 and actor.data.metadata.generated_helper_history[0].source_sha256==FileAccess.get_sha256(source),"helper revision history retains the original source checksum: "+label)
	var after_sha: String=actor.data.sha256;app.undo();actor=app.renderer.world_runtime.instance(id)
	check(actor.data.sha256==before.sha256 and Support.same_keys(actor.data,before) and actor.root.get_meta("has_secondary_rig").chains.size()==n+1,"Undo removes only the second asset revision: "+label)
	app.redo();actor=app.renderer.world_runtime.instance(id);check(actor.data.sha256==after_sha and actor.root.get_meta("has_secondary_rig").chains.size()==n+2,"Redo restores the second chain: "+label)
	var generated: Array=def.chains.slice(n,n+2).duplicate(true);var baseline: Dictionary=actor.sample(0)
	app.physics_editor.fan_editor.add_fan();var fan: RefCounted=app.renderer.active_model();fan.data.position=[0,1.2,-1.5];fan.data.rotation_xyzw=[0,0,0,1];fan.data.metadata.airflow.speed=10;fan.apply(0)
	app.world_selection.select_entity(id,false);actor=app.renderer.world_runtime.instance(id)
	var hits_both:=true
	for chain in generated:hits_both=hits_both and Airflow.force(Airflow.collect(app.renderer,0,{}),SecondaryRig.binding_transform(actor,chain.joints[0].binding).origin).length()>0.01
	check(hits_both,"aimed fan reaches both generated chain anchors: "+label)
	app.physics_editor.hair_toggle.button_pressed=true
	while app.physics_editor.pending.has(id):await process_frame
	check(app.physics_editor.active(id),"normal live Hair & clothes accepts combined chains: "+label)
	if not app.physics_editor.active(id):print("ACTIVATION_DIAGNOSTIC ",app.status.text);return
	var record=app.physics_editor.recording;record.scope.select(0);record.button.pressed.emit()
	while record.active:await process_frame
	actor=app.renderer.world_runtime.instance(id);check(record.last_error.is_empty() and actor.authored_keys().size()==49,"normal Local Record captures every combined chain: "+label)
	var recorded: Dictionary=actor.sample(24);var both_moved:=true
	for chain in generated:
		var response:=0.0
		for joint in chain.joints:
			var bone: String=joint.binding.id
			response=maxf(response,Timeline.quaternion(recorded.get(bone,Model.identity()).rotation_xyzw).angle_to(Timeline.quaternion(baseline.get(bone,Model.identity()).rotation_xyzw)))
		both_moved=both_moved and response>0.005
	check(both_moved,"each generated chain has real recorded wind response beyond its authored pose: "+label)
	var initial: Image=await app.renderer.capture(app.keys,app.layers,0,true);var blowing: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(visible_change(initial.get_region(Rect2i(500,100,350,900)),blowing.get_region(Rect2i(500,100,350,900))) and visible_change(initial.get_region(Rect2i(1045,100,350,900)),blowing.get_region(Rect2i(1045,100,350,900))),"both separate weighted panels visibly animate in the recorded frames: "+label)
	var saved: Dictionary=actor.data.duplicate(true);var project: String=folder.path_join(label+"-multi.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	# saved is pre-JSON; the reopened document has already been parsed once.
	# Parse only the writer oracle, avoiding an extra lossy tiny-float roundtrip.
	var expected_clips=JSON.parse_string(JSON.stringify(saved.animation_clips,"",true,true))
	var diagnostic:=FileAccess.open(folder.path_join(label+"-before-save.json"),FileAccess.WRITE);diagnostic.store_string(JSON.stringify(saved,"",true,true));diagnostic.close()
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project);actor=app.renderer.world_runtime.instance(id);def=actor.root.get_meta("has_secondary_rig")
	diagnostic=FileAccess.open(folder.path_join(label+"-after-save.json"),FileAccess.WRITE);diagnostic.store_string(JSON.stringify(actor.data,"",true,true));diagnostic.close()
	print("MULTI_BODY_STORAGE "+JSON.stringify({"label":label,"rig_error":def.error,"chains":def.chains.size(),"expected_chains":n+2,"history":actor.data.metadata.generated_helper_history.size(),"same_keys":Support.same_keys(actor.data,saved),"same_stored_clips":actor.data.animation_clips==expected_clips}))
	check(def.error.is_empty() and def.chains.size()==n+2 and Support.same_keys(actor.data,saved) and actor.data.animation_clips==expected_clips and actor.data.metadata.generated_helper_history.size()==2,"packed HAS retains all native/generated chains, history and exact recorded controls: "+label)
	var image: Image=await app.renderer.capture(app.keys,app.layers,24,true);image.save_png(folder.path_join(label+"-multi.png"));app.set_frame(5);app.set_frame(40);app.set_frame(24)
	check((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==image.get_data(),"combined recorded motion seeks deterministically: "+label)
	if label=="plain":
		var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==image.get_data(),"combined helpers export with exact reopened preview pixels");movies.append(app.last_export_folder.path_join("movie.mp4"))
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("multi-recovery");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("multi-cache")
	for i in range(3):await sample(app,args[i+1],["plain","v0","v1"][i],folder)
	app.new_project();app.append_object(Model.definition(args[4]),"model");var old: RefCounted=app.renderer.active_model();var legacy: Dictionary=old.root.get_meta("has_secondary_rig")
	check(legacy.error.is_empty() and legacy.chains.size()==1 and old.order.size()==6,"older generated VRMC asset layout still loads with original joints")
	app.physics_editor.helper_editor.button.pressed.emit();await wait_job(app.physics_editor.helper_editor)
	check(app.physics_editor.helper_editor.parts.is_item_disabled(1),"older generated weights receive the same overlap protection");app.physics_editor.helper_editor.close()
	var result:={"checks":checks,"failures":failures,"movies":movies};var f:=FileAccess.open(folder.path_join("multi-result.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result));f.close();print("HELPER_MULTI "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
