extends SceneTree
const Fixture=preload("res://tests/limb_fixture.gd")
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Recording smoke watchdog expired");quit(2))
	call_deferred("run")
func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func wait_record(record) -> void:
	while record.active:await process_frame
	await settled()
func box_asset(path: String) -> Error:
	var node:=Node3D.new();node.name="OriginalRecordingBox"
	var mesh:=MeshInstance3D.new();var box:=BoxMesh.new();box.size=Vector3.ONE*0.8;mesh.mesh=box
	var material:=StandardMaterial3D.new();material.albedo_color=Color("ed9275");mesh.material_override=material
	node.add_child(mesh);mesh.owner=node
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	node.free();return error
func enable(app,id: String) -> void:
	app.world_selection.select_entity(id);app.physics_editor.change(true)
func record_scene(app,box_ids: Array[String],arm_id: String) -> void:
	app.set_frame(0)
	for id in box_ids:enable(app,id)
	enable(app,arm_id);await settled()
	for i in range(180):await physics_frame
func world_samples(app,ids: Array,frame: int) -> Dictionary:
	var result:={}
	for id in ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id)
		result[id]={"pose":actor.sample(frame),"transform":actor.sample_transform(frame)}
	return result
func binding_error(simulation) -> float:
	var actor: RefCounted=simulation.rig;var state: Dictionary=simulation.capture_pose();var globals:={};var error:=0.0
	for id in actor.order:
		var delta: Dictionary=state.get(id,Model.identity());var base: Transform3D=actor.bones[id].base
		var local:=Transform3D(base.basis*Basis(Timeline.quaternion(delta.rotation_xyzw)),base.origin+Timeline.vector(delta.position))
		var parent: String=actor.parent_id(id);globals[id]=globals[parent]*local if globals.has(parent) else local
	for id in simulation.bodies:
		var expected: Transform3D=simulation.bodies[id].global_transform*simulation.bodies[id].body_offset.affine_inverse()
		var actual: Transform3D=actor.bones[id].skeleton.global_transform*globals[id]
		error=maxf(error,actual.origin.distance_to(expected.origin))
	return error
func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/physics-recording/run_%d" % Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(folder)
	var box:=folder.path_join("box.glb");var arm:=folder.path_join("arm.glb");box_asset(box);Fixture.create(arm)
	var source_hashes:={box:FileAccess.get_sha256(box),arm:FileAccess.get_sha256(arm)}
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.load_demo_room();app.mode.select(1);app.change_mode(1)
	app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,0.7,0));app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,60)]
	app.create_cel(false);Drawing.stroke(Drawing.cel_at(app.layers[1],0).image,Vector2(80,80),Vector2(180,80),5,Color.RED,false);app.changed()
	var paint: PackedByteArray=Drawing.cel_at(app.layers[1],0).image.get_data()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav");var audio_tested:=FileAccess.file_exists(wav)
	if audio_tested:app.import_audio(wav);app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	var audio_before: Dictionary=app.audio_clip.duplicate(true);var shots: Array=app.keys.duplicate(true)
	var boxes: Array[String]=[]
	for i in range(3):
		var data:=Model.definition(box);data.position=[0,0.42+i*0.82,0];app.append_object(data,"model");boxes.append(app.last_import_id)
	var data:=Model.definition(arm);data.position=[-2.3,0.2,0];app.append_object(data,"model");var arm_id: String=app.last_import_id
	var physics=app.physics_editor;var record=physics.recording
	check(not app.advanced_mode and record.button.is_visible_in_tree() and record.scope.is_visible_in_tree(),"Record and Local/World controls are visible in Simple")
	check(not record.start(),"recording without live physics gives useful guidance")
	var original: Dictionary=app.renderer.world_state();var history: int=app.history.size()
	await record_scene(app,boxes,arm_id)
	app.world_selection.clear();record.sync()
	check(record.button.disabled and "Select a simulated object" in record.button.tooltip_text,"Local explains why capture requires a selected live actor")
	record.scope.select(1);record.scope.item_selected.emit(1)
	check(not record.button.disabled and "4 simulated objects" in record.button.tooltip_text,"switching to World enables capture without a selected actor")
	app.world_selection.select_entity(arm_id);record.scope.select(0);record.scope.item_selected.emit(0)
	check(not record.button.disabled and physics.simulations[arm_id].rig.data.name in record.button.tooltip_text,"Local preview identifies its selected recording target")
	var live: RefCounted=physics.simulations[arm_id];var physical_bone: String=live.bodies.keys()[0]
	var state: Dictionary=live.capture_pose()
	var actor: RefCounted=live.rig;var globals:={}
	for id in actor.order:
		var delta: Dictionary=state.get(id,Model.identity());var base: Transform3D=actor.bones[id].base
		var local:=Transform3D(base.basis*Basis(Timeline.quaternion(delta.rotation_xyzw)),base.origin+Timeline.vector(delta.position))
		var parent: String=actor.parent_id(id);globals[id]=globals[parent]*local if globals.has(parent) else local
	var predicted: Transform3D=actor.bones[physical_bone].skeleton.global_transform*globals[physical_bone]
	var body_pose: Transform3D=live.bodies[physical_bone].global_transform*live.bodies[physical_bone].body_offset.affine_inverse()
	check(predicted.origin.distance_to(body_pose.origin)<0.0001,"fixed-tick sparse bone capture reconstructs the actual physical body position")
	record.scope.select(0);record.button.pressed.emit()
	check(record.active and record.targets.keys()==[arm_id],"connected Local Record locks capture to the selected live model")
	app.home.open_home()
	check(not app.home.visible and record.active and record.targets.keys()==[arm_id] and "recording" in app.status.text,"Home keeps the actual active capture workspace and Stop controls accessible")
	app.world_selection.select_entity(boxes[0])
	check(record.active and record.targets.keys()==[arm_id],"selecting another model in the tree keeps the original Local capture scope")
	var peer_body: RigidBody3D=physics.simulations[boxes[0]].body;var peer_grab: bool=physics.begin_grab(peer_body,peer_body.global_position)
	check(peer_grab and record.active and record.targets.keys()==[arm_id] and "outside" in app.status.text,"grabbing a peer does not truncate or silently retarget Local recording")
	check(record.scope.get_item_text(0)=="Local · "+str(record.targets[arm_id].name).left(22) and str(record.targets[arm_id].name) in record.scope.tooltip_text,"Local scope still names the recorded actor while another prop is held")
	physics.release_grab()
	for body in live.bodies.values():body.apply_central_impulse(Vector3(8,1,0))
	await wait_record(record)
	print("LOCAL_RECORD_END "+JSON.stringify({"frame":app.frame,"reason":record.last_end_reason,"error":record.last_error,"samples":record.samples.get(arm_id,[]).size()}))
	check(record.last_error.is_empty() and app.frame==48 and not physics.is_running(),"Local recording reaches the exact project end and stops all live proxies")
	check(app.history.size()==history+1 and app.history[-1].type=="world_objects" and app.history[-1].bytes>0,"complete Local take is one memory-accounted Undo command")
	actor=app.renderer.world_runtime.instance(arm_id)
	check(actor.authored_keys().size()==49 and actor.data.animation_clips.size()==1,"Local take contains each project sample including the end boundary")
	var peers_unchanged:=true
	for row in original.objects:
		if row.id!=arm_id:peers_unchanged=peers_unchanged and app.renderer.world_runtime.instance(row.id).data==row
	check(peers_unchanged,"Local capture does not key or freeze unselected impacted props into the project")
	var local_take: Dictionary=actor.data.duplicate(true)
	app.world_selection.select_entity(boxes[0]);app.undo()
	check(app.renderer.world_state()==original and app.renderer.active_instance_id==boxes[0],"Undo restores original motion without changing the peer selection")
	app.redo();check(app.renderer.world_runtime.instance(arm_id).data==local_take,"Redo restores the recorded Local piece with physics off")
	app.undo();await record_scene(app,boxes,arm_id);record.scope.select(1)
	var contacts: Array=[];var starts:={}
	for id in boxes:
		var body: RigidBody3D=physics.simulations[id].body;body.contact_monitor=true;body.max_contacts_reported=16
		body.body_entered.connect(func(other):
			if other is PhysicalBone3D:contacts.append(other.get_instance_id()))
		starts[id]=body.global_position
	history=app.history.size();record.button.pressed.emit();live=physics.simulations[arm_id]
	check(record.scope.get_item_text(1)=="World · 4 objects","World scope shows the four locked recording targets")
	for body in live.bodies.values():body.apply_central_impulse(Vector3(8,1,0))
	await wait_record(record)
	check(record.last_error.is_empty() and record.targets.size()==4 and app.history.size()==history+1,"World records ragdoll and all three dynamic props in one atomic Undo")
	var all_ids: Array=boxes.duplicate();all_ids.append(arm_id);var keyed:=true;var displacement:=0.0
	for id in boxes:
		actor=app.renderer.world_runtime.instance(id);keyed=keyed and actor.authored_keys().size()==49
		for key in actor.authored_keys():
			var offset: Vector3=Timeline.vector(key.transform.position)-starts[id];displacement=maxf(displacement,Vector2(offset.x,offset.z).length())
	check(keyed and not contacts.is_empty() and displacement>0.25,"actual ragdoll impacts produce recorded horizontal box movement")
	var take: Dictionary=app.renderer.world_state();var baseline: Dictionary=world_samples(app,all_ids,24)
	app.set_frame(0);var early: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	app.set_frame(24);var middle: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	check(early.get_data()!=middle.get_data() and world_samples(app,all_ids,24)==baseline and not physics.is_running(),"scrubbing displays saved motion without restarting physics")
	await settled();root.get_texture().get_image().save_png(folder.path_join("recording-editor.png"))
	app.set_frame(0);app.set_frame(47);app.set_frame(24)
	check(world_samples(app,all_ids,24)==baseline,"arbitrary seek order evaluates the same recorded poses and roots")
	check(Drawing.cel_at(app.layers[1],0).image.get_data()==paint and app.audio_clip==audio_before and app.keys==shots,"physics capture preserves independent drawing, WAV timing and explicit camera keys")
	app.undo();check(app.renderer.world_state()==original,"World Undo restores every affected model together")
	app.redo();check(app.renderer.world_state()==take,"World Redo restores every recorded model together")
	var project:=folder.path_join("recording.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	app.new_project();app.has_project.open_file(project);await wait_job(app.has_project)
	var diagnostic:=FileAccess.open(folder.path_join("sample-comparison.json"),FileAccess.WRITE);diagnostic.store_string(JSON.stringify({"original":baseline,"reopened":world_samples(app,all_ids,24)},"",true,true));diagnostic.close()
	check(not physics.is_running() and JSON.stringify(world_samples(app,all_ids,24))==JSON.stringify(baseline),"packed HAS reopens captured root/bone samples without live simulation")
	app.set_frame(24);var reopened: Image=await app.renderer.capture(app.keys,app.layers,24,true);reopened.save_png(folder.path_join("reopened.png"))
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==reopened.get_data(),"recorded motion and independent overlay export with exact reopened preview pixels")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	var directory:=folder.path_join("directory");error=Storage.save_project(directory,app.video,app.keys,app.layers,app.source,app.frame,app.audio_clip,{}, {},false,app.renderer.world_state())
	check(error.is_empty() and FileAccess.get_file_as_bytes(directory.path_join("project.json")).size()<1024*1024,"compact recorded metadata saves inside the unchanged1MiB reader bound")
	# Cancel and early stop use the actual connected controls and key handlers.
	app.new_project();app.load_demo_room();data=Model.definition(box);data.position=[0,3,0];app.append_object(data,"model");var prop_id: String=app.last_import_id
	app.mode.select(0);app.change_mode(0)
	var clean_project:=folder.path_join("before-cancel.has");app.has_project.save_file(clean_project,"packed");await wait_job(app.has_project)
	var untouched: Dictionary=app.renderer.world_state();history=app.history.size();enable(app,prop_id);await settled();app.mode.select(0);app.change_mode(0);record.scope.select(0);record.start()
	check(app.mode.selected==1,"Record from Draw enters the 3D workspace automatically for puppeteering")
	check(app.dirty,"an unfinished recording protects a previously saved project as unsaved work")
	while record.active and record.last_frame<4:await process_frame
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape)
	check(not record.active and not physics.is_running() and app.renderer.world_state()==untouched and app.history.size()==history,"Escape discards a partial recording without altering data or Undo")
	check(not app.dirty,"discarding an unchanged take restores the saved project's clean state")
	enable(app,prop_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	record.button.pressed.emit()
	check(not record.active and app.frame<48 and app.renderer.world_runtime.instance(prop_id).has_animation() and app.history.size()==history+1,"Stop keeps an early take as editable animation")
	app.undo();app.set_frame(0);enable(app,prop_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	var held: RigidBody3D=physics.simulations[prop_id].body;var holding: bool=physics.begin_grab(held,held.global_position)
	app._notification(Control.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	check(holding and record.active and not physics.grabbing(),"focus loss releases a held body without truncating the recording")
	await wait_record(record)
	check(app.frame==48 and record.last_end_reason=="project end" and app.renderer.world_runtime.instance(prop_id).has_animation(),"recording completes to the project end after a focus interruption")
	app.undo();app.set_frame(0);app.video.fps_num=25;app.video.fps_den=2;app.video.duration_frames=12
	enable(app,prop_id);await settled();var body: RigidBody3D=physics.simulations[prop_id].body;body.gravity_scale=0;body.linear_damp_mode=RigidBody3D.DAMP_MODE_REPLACE;body.linear_damp=0;body.linear_velocity=Vector3(1,0,0)
	var origin:=body.global_position;record.start();await wait_record(record)
	actor=app.renderer.world_runtime.instance(prop_id);var end:=Timeline.vector(actor.sample_transform(12).position)
	print("CAPTURE_VELOCITY "+JSON.stringify({"origin":origin,"end":end,"displacement":end-origin,"ticks":record.ticks}))
	check(record.ticks==116 and record.last_frame==12 and actor.authored_keys().size()==13,"non-divisor rational frame rate uses integer tick/frame phase and includes every sample")
	check(absf((end-origin).x-0.96)<0.015,"fractional tick sampling follows actual constant-velocity physics within one fixed step")
	var velocity_error:=absf((end-origin).x-0.96)
	# Preflight, cancellation, stale authoring and bounded recording behavior.
	app.new_project();app.load_demo_room();data=Model.definition(arm);data.position=[0,3,0];app.append_object(data,"model");var limit_id: String=app.last_import_id
	enable(app,limit_id);await settled();record.scope.select(0);record.start();var base_bytes: int=record.last_bytes;record.cancel()
	actor=app.renderer.world_runtime.instance(limit_id);actor.data.metadata["budget_fixture"]="x".repeat(1024*1024-base_bytes-4096)
	var budget_before: Dictionary=actor.data.duplicate(true);history=app.history.size();enable(app,limit_id);await settled()
	var budget_started: bool=record.start();check(budget_started,"a near-capacity project can begin a bounded recording")
	if budget_started:await wait_record(record)
	check(not record.active and "limit" in record.last_error and app.frame<48 and app.frame>0 and app.history.size()==history+1,"metadata limit keeps the longest valid sampled prefix as one Undo step")
	var budget_directory:=folder.path_join("budget-directory")
	error=Storage.save_project(budget_directory,app.video,app.keys,app.layers,app.source,app.frame,{}, {},{},false,app.renderer.world_state())
	check(error.is_empty() and FileAccess.get_file_as_bytes(budget_directory.path_join("project.json")).size()<=1024*1024,"bounded recording result actually saves within the unchanged metadata cap")
	app.undo();check(actor.data==budget_before,"Undo restores even a budget-limited take exactly")
	actor.data.metadata.clear();app.set_frame(0);enable(app,limit_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	history=app.history.size();actor.data.metadata["new_edit"]="keep this edit";var stale: Dictionary=actor.data.duplicate(true)
	check(not record.finish() and actor.data==stale and app.history.size()==history,"recording cannot overwrite authoring that changed while capturing")
	actor.data.metadata.clear();app.set_frame(0);enable(app,limit_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	history=app.history.size();app.undo()
	check(not record.active and app.history.size()==history and not actor.has_animation(),"Undo during capture discards only the unfinished take")
	app.set_frame(0);enable(app,limit_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	app.set_frame(12)
	check(not record.active and not physics.is_running() and app.frame==12 and actor.has_animation(),"manual seek commits the current take before seeking")
	app.undo();app.set_frame(0);enable(app,limit_id);await settled();record.start()
	while record.active and record.last_frame<4:await process_frame
	var interrupted_save:=folder.path_join("save-during-recording.has");app.has_project.save_file(interrupted_save,"packed");await wait_job(app.has_project)
	check(not record.active and FileAccess.file_exists(interrupted_save) and actor.has_animation(),"Save finishes and packages a partial recording instead of losing it")
	# Representative native rigs share this capture path; do not re-run converters.
	var native_ids: Array=[];var native_hashes:={};var native_metrics:={};app.new_project();app.load_demo_room()
	var capture_ms:=0.0;var capture_bytes:=0
	for sample in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+sample)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP optional native recording fixture: "+sample);continue
		var source: Dictionary=World.from_project(Storage.load_project(path)).objects[-1];var source_model:=Model.new();source_model.data=source
		data=Model.definition(source.source);data.metadata=source.metadata.duplicate(true);data.name=source.name;data.position=[native_ids.size()*2.5-2.5,3,0];data.rotation_xyzw=source_model.sample_transform(0).rotation_xyzw;data.scale=source_model.sample_transform(0).scale
		app.append_object(data,"model");native_ids.append(app.last_import_id);native_hashes[source.source]=FileAccess.get_sha256(source.source)
	for id in native_ids:enable(app,id)
	await settled()
	for id in native_ids:
		check(physics.active(id),"native model uses the shared physics capture adapter: "+app.renderer.world_runtime.instance(id).data.name)
		if not physics.active(id):continue
		var simulation: RefCounted=physics.simulations[id];var native_error:=binding_error(simulation)
		check(native_error<0.001,"sparse capture reconstructs every native physical body within one millimeter: "+simulation.rig.data.name)
		native_metrics[id]={"binding_error":native_error,"physical_bodies":simulation.bodies.size(),"source_bones":simulation.rig.order.size()}
	if not native_ids.is_empty():
		record.scope.select(1);record.start();await wait_record(record)
		capture_ms=record.max_sample_ms;capture_bytes=record.last_bytes
		check(record.last_error.is_empty() and app.frame==48,"all native models record a full two-second World take within the metadata budget")
		for id in native_ids:
			actor=app.renderer.world_runtime.instance(id);var sparse:=true
			for key in actor.authored_keys():sparse=sparse and key.pose.size()<=native_metrics[id].physical_bodies
			check(actor.authored_keys().size()==49 and sparse and actor.data.metadata==record.targets[id].metadata,"native recording stores physical bones without duplicating unchanged helpers or losing provenance: "+actor.data.name)
		var native_project:=folder.path_join("native-recording.has");var native_state:=world_samples(app,native_ids,24)
		app.has_project.save_file(native_project,"packed");await wait_job(app.has_project);app.new_project();app.has_project.open_file(native_project);await wait_job(app.has_project)
		check(JSON.stringify(world_samples(app,native_ids,24))==JSON.stringify(native_state),"all native recorded poses survive packed HAS reopen together")
		app.set_frame(24);var native_image: Image=await app.renderer.capture(app.keys,[],24,true);native_image.save_png(folder.path_join("native-capture.png"))
	var vrm_ids: Array=[];var vrm_names: Array=[];app.new_project();app.load_demo_room()
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var source: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(source):print("SKIP optional VRM recording sample: "+name);continue
		native_hashes[source]=FileAccess.get_sha256(source);app.pose_editor.add_model(source);await wait_job(app.source_import)
		for child in app.get_children():
			if child is AcceptDialog and child.title=="Imported with limitations":child.hide();child.queue_free()
		actor=app.renderer.active_model()
		if not actor:check(false,"VRM worker produced a recording-ready model: "+name);continue
		actor.data.position=[vrm_ids.size()*2.5,3,0];actor.apply(0);vrm_ids.append(actor.data.id);vrm_names.append(name)
	for id in vrm_ids:enable(app,id)
	await settled()
	for id in vrm_ids:check(physics.active(id) and binding_error(physics.simulations[id])<0.001,"VRM humanoid rig supports sparse fixed-tick capture: "+app.renderer.world_runtime.instance(id).data.name)
	if not vrm_ids.is_empty():
		record.scope.select(1);record.start();await wait_record(record)
		capture_ms=maxf(capture_ms,record.max_sample_ms);capture_bytes=maxi(capture_bytes,record.last_bytes)
		var vrm_complete: bool=record.last_error.is_empty()
		for id in vrm_ids:vrm_complete=vrm_complete and app.renderer.world_runtime.instance(id).authored_keys().size()==49
		check(vrm_complete,"VRM0/1 complete a full World take through the same native model representation")
	var originals_unchanged:=true
	for path in source_hashes:originals_unchanged=originals_unchanged and FileAccess.get_sha256(path)==source_hashes[path]
	check(originals_unchanged,"recording never modifies original geometry files")
	for path in native_hashes:originals_unchanged=originals_unchanged and FileAccess.get_sha256(path)==native_hashes[path]
	check(originals_unchanged,"native capture never changes source GLBs")
	app.new_project();app.load_demo_room();app.append_object(Model.definition(box),"model");enable(app,app.last_import_id);await settled();record.scope.select(0);record.start()
	while record.active and record.last_frame<2:await process_frame
	check(record.active,"owned application teardown is exercised with an active unfinished recording")
	var result:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":movie,"audio":audio_tested,"world_contacts":contacts.size(),"horizontal_displacement":displacement,"max_sample_ms":capture_ms,"metadata_estimate":capture_bytes,"velocity_error":velocity_error,"native_models":native_ids.size(),"native_metrics":native_metrics,"vrm_samples":vrm_names}
	var output:=FileAccess.open("res://output/physics-recording-result.json",FileAccess.WRITE);output.store_string(JSON.stringify(result));output.close()
	print("PHYSICS_RECORDING "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
