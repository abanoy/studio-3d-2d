extends Node
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(140).timeout.connect(func():push_error("Lesson recovery startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func recovered(result: Dictionary) -> void:
	var app=get_parent();var lesson=app.tutorials;lesson.set_process(false);app.autosave_enabled.button_pressed=false
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var label: String=args[1];var target:=int(args[2]);var attach: bool=args[3]=="yes"
	app.has_project.cache_root=folder.path_join("reader-cache")
	var expected:=Recovery.read_json(folder.path_join("expected.json"));var state: Dictionary=expected.states[str(target)]
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	check(result.restored and not result.cancelled and not app.home.visible and not app.has_dialog(app),"production normal startup restores practice scene quietly")
	check(app.frame==target and app.dirty and app.project_folder.is_empty() and app.has_project.path.is_empty(),"recovery retains exact playhead as unsaved copy without manual identity")
	check(app.layers[1].cels.size()==int(state.cels) and Storage.image_hash(Drawing.cel_at(app.layers[1],target).image)==state.paint,"selected recovery generation restores exact later drawing bytes and cel count")
	check(lesson.active==attach and lesson.panel.visible==attach,"teacher attachment matches validated recovery metadata and available practice session")
	check(FileAccess.get_sha256(expected.manual)==expected.manual_sha256,"automatic startup preserves the last explicitly saved HAS")
	var movie:=""
	if attach and lesson.active:
		check(lesson.course==expected.course and lesson.session==expected.session and lesson.step==1 and not lesson.done,"teacher restores matching course, session and uncompleted step")
		check(canonical(Store.ui(app))==state.ui,"lesson recovery restores exact temporary camera, mode, selection and canvas alignment")
		check(canonical(lesson.baseline)==state.baseline and is_equal_approx(lesson.fov_baseline,float(state.fov_baseline)) and lesson.collapsed==state.collapsed,"teacher restores immutable exercise baseline, lens baseline and card presentation")
		check(not lesson.satisfied(),"unrelated newer paint cannot award the pending arm-pose task")
		check(FileAccess.get_sha256(str(expected.lesson_folder).path_join("progress.json"))==expected.progress_sha256,"reattachment does not rewrite lesson progress during startup")
		lesson.last_signature="%d:%d:%s:%s" % [app.recovery_revision,app.frame,app.world_selection.selected,str(app.advanced_mode)];lesson.last_action=Time.get_ticks_msec()-16000;lesson.next_tick=0;lesson._process(0)
		check(lesson.hint_due and lesson.hint_button.text=="Need a hint?","recovered teacher still offers the quiet idle hint")
		var image: Image=await app.renderer.capture(app.keys,app.layers,target,true)
		check(image.get_data()==Image.load_from_file(folder.path_join("frame%d.png" % target)).get_data(),"fresh recovered practice produces exact prior final composition")
		if label=="newest":
			var error: String=await app.export_movie(folder);movie=app.last_export_folder.path_join("movie.mp4")
			check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png" % (target+1))).get_data()==image.get_data(),"recovered practice exports ordinary MP4 with exact expected frame input")
			var personal:=folder.path_join("Saved recovered practice.has");app.has_project.save_file(personal,"packed")
			while app.has_project.pid>0:await get_tree().process_frame
			check(FileAccess.file_exists(personal) and app.has_project.path==personal and not app.dirty,"explicit Save writes recovered practice to a separately chosen personal HAS")
		check(lesson.save_resume() and lesson.start(expected.course,false,expected.session),"recovered practice can save resume and Continue through ordinary lesson storage")
		check(lesson.active and lesson.step==1 and app.frame==target and canonical(Store.ui(app))==state.ui,"Continue keeps recovered teacher and newer scene edits together")
		lesson.previous()
		check(lesson.active and lesson.step==0 and app.frame==0 and app.layers[1].cels.is_empty() and app.world_selection.selected.is_empty(),"Previous restores whole earlier exercise, removing post-checkpoint paint and selection")
		var session: String=lesson.session
		check(lesson.start(expected.course,true),"Start fresh remains available after recovered Previous")
		while app.has_project.pid>0:await get_tree().process_frame
		check(lesson.session!=session and not lesson.store.progress(expected.course,session).is_empty(),"fresh practice retains recovered prior session")
		check(app.open_project(expected.checkpoint,result.checkpoint.manifest) and not lesson.active,"ordinary Open of selected recovery generation does not activate its embedded teacher context")
	else:
		check(not lesson.active and not lesson.panel.visible,"legacy, invalid or unavailable lesson context leaves recovered scene usable without teacher")
		if label!="legacy":check(app.status.text.contains("lesson context is invalid") or app.status.text.contains("practice history is unavailable"),"nonmodal feedback explains why only the recovered scene is available")
	lesson.active=false;app.recovery_preview.finish()
	check(FileAccess.get_sha256(expected.manual)==expected.manual_sha256,"lesson actions and optional export leave manual HAS unchanged")
	var report:={"checks":checks,"failures":failures,"case":label,"startup":result,"movie":movie}
	FileAccess.open(folder.path_join(label+"-result.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"",true,true))
	print("LESSON_RECOVERY_STARTUP "+JSON.stringify(report));get_tree().quit(0 if failures==0 else 1)
