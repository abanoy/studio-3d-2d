extends SceneTree
const Recovery=preload("res://src/recovery.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Model=preload("res://src/model.gd")
var folder: String
func _initialize() -> void:
	folder=OS.get_cmdline_user_args()[0]
	create_timer(120).timeout.connect(func():push_error("Startup recovery writer watchdog");quit(2));call_deferred("run")
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func require(ok: bool,label: String) -> void:
	if not ok:push_error(label);quit(2)
func portable(data: Dictionary) -> Dictionary:
	var result: Dictionary=JSON.parse_string(JSON.stringify(data,"",false,true))
	for row in result.objects:
		row.erase("source");row.erase("path")
	return result
func run() -> void:
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.tree_exiting.connect(func():
		var closed:=FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE);closed.store_string("scene cleanup ran");closed.close())
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var map:=folder.path_join("map.glb");var actor:=folder.path_join("actor.glb")
	require(SceneIO.make_fixture(map)==OK and SceneIO.make_pose_fixture(actor)==OK,"create original fixtures")
	require(app.load_scene(map).is_empty() and app.pose_editor.add_model(actor).is_empty(),"standard map and skinned actor")
	var actor_id: String=app.last_import_id;var bone: String=app.renderer.active_model().order[1]
	var plans: Array=Recovery.read_json(folder.path_join("plan.json")).native
	for plan in plans:
		var model:=Model.definition(plan.source);model.metadata=plan.metadata.duplicate(true);model.position=[20,0,-20]
		require(app.append_object(model,"model").is_empty(),"native import: "+plan.label)
	app.world_selection.select_entity(actor_id)
	app.import_audio(folder.path_join("voice.wav"));app.audio_start.value=24;app.audio_gain.value=-6;app.apply_audio_settings()
	var manual:=folder.path_join("manual.has");app.has_project.save_file(manual,"packed")
	while app.has_project.pid>0:await process_frame
	require(FileAccess.file_exists(manual) and not app.dirty,"manual packed save")
	var expected:={"manual":manual,"manual_sha256":FileAccess.get_sha256(manual),"states":{},"native_models":plans.size()}
	for at in [12,24]:
		app.set_frame(at);app.pose_editor.selected=bone;app.pose_editor.operation.select(0);app.pose_editor.refresh_values()
		app.pose_editor.fields[2].value=25 if at==12 else 65;app.pose_editor.apply_numeric()
		app.create_cel(false);var cel: Dictionary=Drawing.cel_at(app.layers[1],at)
		cel.image.set_pixel(80,80,Color.CYAN if at==24 else Color.BLUE);app.changed()
		app.renderer.camera.far=12000;app.insert_key();app.autosave_tick(true)
		var checkpoint: String=app.recovery_root.path_join(app.recovery_session)
		require(FileAccess.file_exists(checkpoint.path_join("project.json")),"committed checkpoint")
		var image: Image=await app.renderer.capture(app.keys,app.layers,at,true);image.save_png(folder.path_join("frame%d.png" % at))
		var orders:={};var transforms:={}
		for id in app.renderer.world_runtime.order:
			var rig: RefCounted=app.renderer.world_runtime.instance(id);orders[id]=rig.order.duplicate();transforms[id]=rig.sample_transform(at)
		expected.states[str(at)]={"frame":at,"world":portable(app.renderer.world_state()),"keys":app.keys.duplicate(true),"video":app.video.duplicate(true),"orders":orders,"transforms":transforms,"paint":Storage.image_hash(cel.image)}
	expected["checkpoint"]=app.recovery_root.path_join(app.recovery_session)
	var partial:=FileAccess.open(str(expected.checkpoint).path_join("project.json.tmp"),FileAccess.WRITE);partial.store_string("{unfinished");partial.flush();partial.close()
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected,"",false,true));file.flush();file.close()
	await settled()
	print("RECOVERY_STARTUP_WRITER_READY")
	# Terminate only this test's own engine, bypassing graceful scene cleanup.
	OS.kill(OS.get_process_id())
	var returned:=FileAccess.open(folder.path_join("kill-returned.txt"),FileAccess.WRITE);returned.store_string("self termination returned");returned.close()
	quit(2)
