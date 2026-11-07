extends SceneTree
const Assets=preload("res://src/tutorial_assets.gd")
const Store=preload("res://src/lesson_store.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Lesson recovery writer watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("writer-cache")
	var lesson=app.tutorials;lesson.set_process(false)
	check(lesson.start("basic-pose",true),"real bundled practice starts through normal unpack worker")
	while app.has_project.pid>0:await process_frame
	await settle();check(lesson.active and lesson.step==0,"practice teacher and original figure are installed")
	var manual:=folder.path_join("Manual practice.has");app.has_project.save_file(manual,"packed")
	while app.has_project.pid>0:await process_frame
	check(FileAccess.file_exists(manual),"ordinary personal packed Save succeeds before later practice edits")
	app.world_selection.select_entity(Assets.FIGURE_ID);lesson.next_tick=0;lesson._process(0);await settle()
	check(lesson.step==1,"selection advances teacher and saves its full Previous checkpoint")
	var expected:={"session":lesson.session,"course":lesson.course,"manual":manual,"manual_sha256":FileAccess.get_sha256(manual),"lesson_folder":lesson.store.folder(lesson.course,lesson.session),"progress_sha256":FileAccess.get_sha256(lesson.store.folder(lesson.course,lesson.session).path_join("progress.json")),"states":{}}
	for at in [12,18]:
		app.mode.select(0);app.change_mode(0);app.active_layer=1;app.layer_choice.select(1);app.set_frame(at);app.create_cel(false)
		Drawing.edit_image(Drawing.cel_at(app.layers[1],at)).image.fill_rect(Rect2i(60+at,90,80,50),Color.CYAN if at==12 else Color.MAGENTA)
		app.canvas.zoom=1.25 if at==12 else 1.5;app.canvas.pan=Vector2(at,at+5);app.renderer.camera.position+=Vector3(.1,0,0);app.changed();await settle()
		lesson.set_collapsed(at==18)
		var image: Image=await app.renderer.capture(app.keys,app.layers,at,true);image.save_png(folder.path_join("frame%d.png" % at))
		while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
		app.autosave_tick(true)
		while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
		check(app.checkpoint_revision==app.recovery_revision,"ordinary autosave protects later practice edit at frame%d" % at)
		expected.states[str(at)]={"ui":Store.ui(app),"paint":Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],at))),"cels":app.layers[1].cels.size(),"baseline":lesson.baseline,"fov_baseline":lesson.fov_baseline,"collapsed":lesson.collapsed}
	expected["checkpoint"]=app.recovery_root.path_join(app.recovery_session)
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("LESSON_RECOVERY_WRITER "+JSON.stringify({"checks":checks,"failures":failures}))
	if failures>0:app.free();quit(1);return
	OS.kill(OS.get_process_id())
	FileAccess.open(folder.path_join("kill-returned.txt"),FileAccess.WRITE).store_string("unexpected");quit(2)
