extends SceneTree
const Support=preload("res://tests/world_test_support.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Storage=preload("res://src/storage.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0

func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("World workflow watchdog expired");quit(2))
	call_deferred("run")

func check(ok: bool,text: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+text)
	if not ok:failures+=1

func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw

func wait_job(has) -> void:
	while has.pid>0:await process_frame
	await settled()

func run() -> void:
	var folder:=ProjectSettings.globalize_path("res://output/world-workflow/run_%d" % Time.get_ticks_usec());var inputs:=folder.path_join("inputs");DirAccess.make_dir_recursive_absolute(inputs)
	var map:=inputs.path_join("room.glb");var actor:=inputs.path_join("actor.glb");SceneIO.make_fixture(map);SceneIO.make_pose_fixture(actor)
	var map_hash:=FileAccess.get_sha256(map);var actor_hash:=FileAccess.get_sha256(actor)
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide()
	app.has_project.cache_root=folder.path_join("cache");app.autosave_enabled.button_pressed=false
	check(app.renderer.world_runtime!=null and app.renderer.world_runtime.instances.is_empty() and app.source.is_empty() and app.world_selection.selected.is_empty(),"normal startup creates a genuinely empty multi-object world")
	check(app.load_scene(map).is_empty(),"normal Add scene appends first map")
	var map0: String=app.last_import_id;var map0_state: Dictionary=app.renderer.world_runtime.instance(map0).data.duplicate(true)
	check(app.load_scene(map).is_empty() and app.renderer.world_runtime.instances.size()==2 and app.last_import_id!=map0,"adding same map again creates independent instance instead of replacing it")
	var map1: String=app.last_import_id;var editor=app.pose_editor
	editor.operation.select(1);editor.refresh_values();editor.fields[0].value=20;editor.apply_numeric()
	check(app.renderer.world_runtime.instance(map0).data==map0_state and app.renderer.world_runtime.instance(map1).sample_transform(0).position[0]==20,"map root moves independently through normal pose controls")
	check(editor.add_model(actor).is_empty(),"normal Add model appends beside both maps")
	var actor0: String=app.last_import_id;var rig: RefCounted=app.renderer.active_model();var bone: String=rig.order[1]
	editor.tree_items[bone].select(0);editor.operation.select(0);editor.refresh_values();editor.fields[2].value=25;editor.apply_numeric()
	app.set_frame(24);editor.refresh_values();editor.fields[2].value=65;editor.apply_numeric()
	var first_actor: Dictionary=app.renderer.active_model().data.duplicate(true);var shots:=JSON.stringify(app.keys)
	check(editor.add_model(actor).is_empty() and app.renderer.world_runtime.instances.size()==4 and app.renderer.world_runtime.instance(actor0).data==first_actor,"second model preserves first actor's independent pose keys and both maps")
	var actor1: String=app.last_import_id
	app.world_selection.select_entity(actor0);app.undo()
	check(app.renderer.world_runtime.instances.size()==3 and not app.renderer.world_runtime.instances.has(actor1) and app.world_selection.selected==actor0,"Undo Add removes only added instance and preserves current valid selection")
	app.redo()
	check(app.renderer.world_runtime.instances.size()==4 and app.renderer.world_runtime.instance(actor0).data==first_actor,"Redo Add restores its own instance without overwriting first pose")
	app.world_selection.select_entity(actor1);app.set_frame(0);editor.operation.select(1);editor.refresh_values();editor.fields[0].value=20;editor.apply_numeric();app.set_frame(24)
	app.remove_world_object(map1)
	check(not app.renderer.world_runtime.instances.has(map1) and app.renderer.world_runtime.instances.has(actor0),"normal structural Remove preserves independent models")
	app.undo();check(app.renderer.world_runtime.instances.size()==4,"Undo Remove restores complete map instance")
	check(JSON.stringify(app.keys)==shots,"adding, moving and removing objects never writes camera keys")
	app.world_selection.select_entity(actor0);editor.frame_model();var camera: Camera3D=app.renderer.camera
	app.keys=[Timeline.key(0,camera.position,camera.quaternion,camera.fov),Timeline.key(48,camera.position+Vector3(0.2,0,0),camera.quaternion,camera.fov)]
	app.mode.select(0);app.change_mode(0);app.set_frame(24);app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],24)),Vector2(100,100),Vector2(220,100),6,Color.RED,false);app.changed()
	var wav:=ProjectSettings.globalize_path("res://output/fixtures/voice — тест.wav")
	check(app.import_audio(wav).is_empty(),"normal multi-object world accepts independent WAV audio")
	app.audio_clip.start_frame=24;app.audio_clip.gain_db=-6;app.rebuild_audio()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var saved_world: Dictionary=World.portable(app.renderer.world_state());var saved_transforms:={}
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id);saved_transforms[object_id]={"root":object.root.global_transform,"bones":{}}
		for part in object.order:saved_transforms[object_id].bones[part]=object.bone_transform(part)
	var project:=folder.path_join("world.has");app.has_project.save_file(project,"packed");await wait_job(app.has_project)
	check(app.has_project.path==project and not app.dirty,"ordinary packed HAS Save commits multi-map multi-actor project")
	var moved:=folder.path_join("moved-inputs");DirAccess.rename_absolute(inputs,moved)
	app.has_project.open_file(project);await wait_job(app.has_project)
	check(app.has_project.path==project and app.renderer.world_runtime.instances.size()==4 and app.world_selection.selected.is_empty() and app.frame==24,"ordinary HAS Open restores every object and saved frame with nothing selected")
	check(Support.same_keys(app.renderer.world_runtime.instance(actor0).data,first_actor),"normal Open retains independent actor animation")
	var reopened: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	expected.save_png(folder.path_join("before-open.png"));reopened.save_png(folder.path_join("after-open.png"))
	var old_pixels:=expected.get_data();var new_pixels:=reopened.get_data();var changed_channels:=0;var byte_difference:=0;var locations:=[]
	for i in range(old_pixels.size()):
		if old_pixels[i]!=new_pixels[i]:
			changed_channels+=1;byte_difference+=absi(int(old_pixels[i])-int(new_pixels[i]))
			if locations.size()<20:locations.append([int(i/4)%1920,int(i/4)/1920,i%4,int(old_pixels[i]),int(new_pixels[i])])
	print("PACKED_WORLD_DIFFERENCE "+JSON.stringify({"channels":changed_channels,"mean":float(byte_difference)/old_pixels.size(),"locations":locations}))
	var exact_transforms:=true
	for object_id in app.renderer.world_runtime.order:
		var object: RefCounted=app.renderer.world_runtime.instance(object_id)
		exact_transforms=exact_transforms and object.root.global_transform==saved_transforms[object_id].root
		for part in object.order:exact_transforms=exact_transforms and object.bone_transform(part)==saved_transforms[object_id].bones[part]
	print("PACKED_WORLD_STATE "+JSON.stringify({"transforms_exact":exact_transforms,"data_exact":World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(saved_world,"",true,true))}))
	check(exact_transforms and World.portable(app.renderer.world_state())==JSON.parse_string(JSON.stringify(saved_world,"",true,true)) and changed_channels<=384 and float(byte_difference)/old_pixels.size()<0.002,"packed Open retains exact data/transforms and frame within existing GLB rebuild edge bounds")
	check(app.new_project() and app.renderer.world_runtime.instances.is_empty() and app.history.is_empty() and app.has_project.path.is_empty() and app.audio_clip.is_empty(),"normal New safely replaces a populated world and clears audio/save identity/history")
	app.has_project.open_file(project);await wait_job(app.has_project)
	var before:=World.portable(app.renderer.world_state());var state: RefCounted=app.renderer.world_runtime
	var broken:=folder.path_join("broken.glb");var file:=FileAccess.open(broken,FileAccess.WRITE);file.store_string("broken");file.close()
	check(not app.load_scene(broken).is_empty() and app.renderer.world_runtime==state and World.portable(app.renderer.world_state())==before,"failed normal map import keeps whole world intact")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var checkpoint: String=app.recovery_root.path_join(app.recovery_session)
	app.new_project()
	check(app.restore_checkpoint({"folder":checkpoint}) and app.renderer.world_runtime.instances.size()==4 and app.dirty and app.has_project.path.is_empty(),"ordinary recovery restores all objects as unsaved copy")
	var recovery_preview: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var a:=expected.get_data();var b:=recovery_preview.get_data();var changes:=0;var total:=0.0
	for i in range(a.size()):
		if a[i]!=b[i]:changes+=1;total+=absf(float(a[i])-float(b[i]))
	print("RECOVERED_WORLD_DIFFERENCE ",changes," mean=",total/a.size())
	check(changes<=384 and total/a.size()<0.002,"recovery rebuild preserves world image within established GLB reimport edge tolerance")
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==recovery_preview.get_data(),"ordinary recovered world exports full camera/pose/RGBA movie matching its exact preview")
	# Legacy files still open, then their next normal import appends losslessly.
	var legacy:=folder.path_join("legacy");var video: Dictionary=app.video.duplicate(true)
	var legacy_error:=Storage.save_project(legacy,video,app.keys,app.layers,moved.path_join("room.glb"),24)
	check(legacy_error.is_empty() and app.open_project(legacy) and app.renderer.world_runtime==null,"legacy directory project opens with its original renderer defaults")
	check(editor.add_model(moved.path_join("actor.glb")).is_empty() and app.renderer.world_runtime.instances.size()==2,"normal import into legacy project promotes existing map and appends new model")
	check(FileAccess.get_sha256(moved.path_join("room.glb"))==map_hash and FileAccess.get_sha256(moved.path_join("actor.glb"))==actor_hash,"ordinary workflows preserve original source bytes")
	await settled();root.get_texture().get_image().save_png(folder.path_join("editor.png"))
	var report:={"checks":checks,"failures":failures,"folder":folder,"project":project,"movie":app.last_export_folder.path_join("movie.mp4")}
	file=FileAccess.open("res://output/world-workflow-result.json",FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("WORLD_WORKFLOW_SMOKE "+JSON.stringify(report));quit(0 if failures==0 else 1)
