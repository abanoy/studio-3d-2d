extends SceneTree
const Model=preload("res://src/model.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Ranges=preload("res://src/contact_ranges.gd")
const Correction=preload("res://src/contact_correction.gd")
const Contacts=Ranges.Contact.Contacts
const T=Model.Timeline
const Store=preload("res://src/lesson_store.gd")
var app
var folder: String
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Contact persistence writer watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0 or app.source_import.pid>0:await process_frame
	await settled()
func hash_pose(actor: RefCounted,at: float) -> String:return JSON.stringify(actor.sample(at),"",true,true).sha256_text()
func floor_asset(path: String) -> Error:
	var node:=Node3D.new();node.name="OriginalContactStage";preload("res://src/scene3d.gd").box(node,"Floor",Vector3(0,-.2,0),Vector3(22,.2,8),Color("283d46"))
	var doc:=GLTFDocument.new();var state:=GLTFState.new();var error:=doc.append_from_scene(node,state)
	if error==OK:error=doc.write_to_filesystem(state,path)
	node.free();return error
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var sources:=folder.path_join("sources");DirAccess.make_dir_recursive_absolute(sources)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var rows:=[];var native_hashes:={}
	for label in ["pose-smoke/miku-project","source-smoke/source-project","sfm-smoke/project"]:
		var path:=ProjectSettings.globalize_path("res://output/"+label)
		if not FileAccess.file_exists(path.path_join("project.json")):print("SKIP private "+label);continue
		var loaded:=Storage.load_project(path);var row:=preload("res://tests/world_test_support.gd").legacy_model(World.from_project(loaded).objects[-1]);rows.append(row)
	for name in ["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]:
		var path: String=preload("res://tests/native_sample_paths.gd").vrm(name)
		if not FileAccess.file_exists(path):print("SKIP private "+name);continue
		native_hashes[path]=FileAccess.get_sha256(path);app.new_project();app.pose_editor.add_model(path);await job()
		for node in app.get_children():
			if node is AcceptDialog and node.title=="Imported with limitations":node.hide();node.queue_free()
		rows.append(preload("res://tests/world_test_support.gd").legacy_model(app.renderer.active_model().data))
	check(rows.size()==5,"five actual MMD/GMod/SFM/VRM rigs are available for the combined acceptance fixture")
	if rows.size()!=5:app.free();quit(1);return
	var empty:=sources.path_join("empty.glb");preload("res://src/scene3d.gd").make_empty(empty);var floor_path:=sources.path_join("floor.glb");floor_asset(floor_path)
	var group:=World.object(empty,"group","Contact group");group.id="contact-group";group.position=[-6,0,0];group.scale=1.1;var q:=Quaternion(Vector3.UP,.08);group.rotation_xyzw=[q.x,q.y,q.z,q.w]
	var group_model:=Model.new();group_model.data=group
	for at in [0,24]:
		var value:=Model.Clips.transform(group);value.position[0]+=.005*float(at)/24.;var prior: Dictionary=group_model.data.duplicate(true)
		group_model.put_pose_key({"frame":at,"pose":{},"transform":value,"authored_channels":["@root"],"interpolation":"ease"},48,false,prior)
	group=group_model.data;var world:=World.empty();var floor_row:=World.object(floor_path,"environment","Original stage");floor_row.id="stage";world.objects=[floor_row,group]
	var ids:=[]
	for i in range(rows.size()):
		var row: Dictionary=rows[i];native_hashes[row.source]=FileAccess.get_sha256(row.source);var copy:=sources.path_join("native-%d.glb" % i)
		check(DirAccess.copy_absolute(row.source,copy)==OK,"own a byte-identical native input copy: "+str(i))
		row.source=copy;row.id="native-%d" % i;row.parent_id=group.id;row.start_frame=0;row.pose_keys=[];row.pose={};row.draft_frame=0;row.position[0]=float(i)*3.;row.visible=true;row.reference_only=false;world.objects.append(row);ids.append(row.id)
	app.new_project();check(app.restore_world(world).is_empty(),"five native skins, transformed animated group and map install together")
	for id in ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id);app.set_frame(0);var capture:=Contacts.capture(actor,0,49,"pin-"+id)
		if capture.has("error"):check(false,capture.error);continue
		var foot: Dictionary=capture.segments[0].feet[0];var hip: Vector3=actor.bone_transform(foot.ids[0]).origin;var end:=T.vector(foot.position);var axis: Vector3=(end-hip).normalized();var length: float=hip.distance_to(end)
		var local_delta: Vector3=actor.root.get_parent().global_basis.inverse()*(end-hip)*.12;var initial: Dictionary=actor.sample_transform(0)
		for at in [0,24]:
			var value: Dictionary=initial.duplicate(true);var p:=T.vector(initial.position)+local_delta*float(at)/24.;value.position=[p.x,p.y,p.z];var prior: Dictionary=actor.data.duplicate(true)
			actor.put_pose_key({"frame":at,"pose":{},"transform":value,"authored_channels":["@root"],"interpolation":"ease"},48,false,prior)
		var planted:=Ranges.edit(actor.data,0,49,capture.segments[0],48);var sideways:=Vector3.RIGHT if absf(axis.dot(Vector3.RIGHT))<.8 else Vector3.UP;sideways=(sideways-axis*sideways.dot(axis)).normalized();var pole:=hip+sideways*length
		var corrected:=Correction.edit(planted.data,0,49,0,{"pole":[pole.x,pole.y,pole.z],"flip_bend":true},48)
		var release:=Ranges.edit(corrected.data,30,33,{},48)
		check(not release.has("error") and app.renderer.world_runtime.restore_instance(id,release.data).is_empty(),"native version2 pins and release interval install: "+id)
	app.video.visibility_fade_ms=0;var last: RefCounted=app.renderer.world_runtime.instance(ids[-1]);last.data.visibility_keys=[{"frame":40,"visible":false},{"frame":46,"visible":true}]
	app.set_frame(12);app.world_selection.select_entity(ids[0]);app.frame_3d_scene();await settled()
	var camera: Camera3D=app.renderer.camera;app.keys=[T.key(0,camera.position,camera.quaternion,camera.fov),T.key(24,camera.position+Vector3(.3,.1,0),camera.quaternion,camera.fov)]
	app.set_frame(0);app.active_layer=1;app.create_cel(false);preload("res://src/drawing.gd").stroke(app.layers[1].cels[0].image,Vector2(40,40),Vector2(150,40),9,Color.CYAN,false);app.layers[0]["opacity"]=.4
	check(app.import_audio(folder.path_join("tone.wav")).is_empty(),"actual PCM audio imports into the combined scene")
	app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio();app.changed();app.set_frame(12)
	var samples:={};var timings:={};var error_count:=0
	for id in ids:
		var actor: RefCounted=app.renderer.world_runtime.instance(id);samples[id]=[]
		for half in range(97):samples[id].append(hash_pose(actor,float(half)/2));error_count+=0 if actor.evaluation_error.is_empty() else 1
		var began:=Time.get_ticks_usec()
		for at in range(49):actor.sample(at)
		timings[id]={"sample_49_ms":float(Time.get_ticks_usec()-began)/1000.,"bones":actor.order.size()}
	check(error_count==0,"all native version2 contacts and explicit release intervals are reachable across the complete project")
	var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);reference.save_png(folder.path_join("reference.png"))
	var expected:={"world":World.portable(app.current_world()),"samples":samples,"video":app.video,"keys":app.keys,"audio":{},"paint":Storage.image_hash(app.layers[1].cels[0].image),"ids":ids,"frame":12}
	expected.audio={"sha256":app.audio_clip.source.sha256,"start_frame":app.audio_clip.start_frame,"gain_db":app.audio_clip.gain_db}
	var packed:=folder.path_join("native-packed.has");app.has_project.save_file(packed,"packed");await job();check(FileAccess.file_exists(packed),"normal packed HAS saves the complete native contact world")
	var linked:=folder.path_join("native-linked.has");app.has_project.save_file(linked,"linked");await job();check(FileAccess.file_exists(linked),"normal linked HAS saves the same native contact world")
	var store:=Store.new();store.root=folder.path_join("lessons");check(store.save(app,"basic-pose","1234",1,false,"step_01",{"preview_seen":true}),"normal lesson checkpoint API retains this contact world and editor state")
	expected["lesson_ui"]=Store.ui(app);app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	while app.recovery_preview.busy():await process_frame;app.poll_recovery_preview()
	check(app.checkpoint_revision==app.recovery_revision,"ordinary recovery writes the combined contact world")
	var movie_error: String=await app.export_movie(folder);check(movie_error.is_empty() and reference.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"combined native contacts, camera, paint and audio export through the actual MP4 workflow")
	for path in native_hashes:check(FileAccess.get_sha256(path)==native_hashes[path],"original native/source bytes remain unchanged: "+path.get_file())
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected,"",true,true));file.close()
	var result:={"checks":checks,"failures":failures,"folder":folder,"packed":packed,"linked":linked,"recovery_root":app.recovery_root,"recovery_session":app.recovery_session,"lesson_root":store.root,"movie":app.last_export_folder.path_join("movie.mp4"),"timings":timings,"source_hashes":native_hashes};file=FileAccess.open(folder.path_join("writer-result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result,"",true,true));file.close();app.free();await settled();print("CONTACT_PERSISTENCE_WRITE "+JSON.stringify(result));quit(0 if failures==0 else 1)
