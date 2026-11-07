extends Node
const Store=preload("res://src/lesson_store.gd")
const Recovery=preload("res://src/recovery.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(90).timeout.connect(func():push_error("Lesson autosave startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false;app.tutorials.set_process(false)
	var folder: String=OS.get_cmdline_user_args()[0];var expected:=Recovery.read_json(folder.path_join("expected.json"));var lesson=app.tutorials
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	check(result.restored and result.get("lesson_restored",false) and not result.cancelled and not app.home.visible,"ordinary startup automatically restores clean-scene lesson-only recovery")
	check(lesson.active and lesson.course==expected.course and lesson.session==expected.session and lesson.step==1,"recovered teacher keeps original course/session and pending arm task")
	check(lesson.observed==expected.observed and not lesson.satisfied(),"teacher-only observation survives without falsely completing the unrelated pending task")
	check(app.frame==18 and canonical(Store.ui(app))==expected.ui and lesson.collapsed,"latest protected temporary camera, canvas, mode and collapsed card restore exactly")
	check(app.dirty and app.has_project.path.is_empty() and app.project_folder.is_empty(),"recovery remains unsaved copy despite writer scene having been clean")
	check(FileAccess.get_sha256(expected.manual)==expected.manual_sha256 and FileAccess.get_sha256(expected.progress)==expected.progress_sha256,"crash restoration preserves manual HAS and separate step-progress bytes")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,18,true)
	check(picture.get_data()==Image.load_from_file(folder.path_join("frame18.png")).get_data(),"cold restored practice has exact protected final composition")
	app.has_project.cache_root=folder.path_join("reader-cache");app.has_project.save_file(folder.path_join("Recovered practice.has"),"packed")
	while app.has_project.pid>0:await get_tree().process_frame
	app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	for i in range(5):await get_tree().process_frame
	while app.recovery_preview.busy():app.poll_recovery_preview();await get_tree().process_frame
	var target: String=app.recovery_root.path_join(app.recovery_session).path_join("project.json")
	check(not app.dirty and Recovery.read_json(target).editor.recovery.has("lesson"),"new document recovery session starts with its own protected teacher fingerprint")
	var teacher: Dictionary=lesson.recovery_context();lesson.leave(true);app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	for i in range(5):await get_tree().process_frame
	while app.recovery_preview.busy():app.poll_recovery_preview();await get_tree().process_frame
	check(not app.dirty and not Recovery.read_json(target).editor.recovery.has("lesson") and app.checkpoint_lesson_signature.is_empty(),"leaving a clean lesson checkpoints removal of teacher context without dirtying scene")
	check(lesson.restore_recovery_context(teacher).is_empty() and lesson.active,"valid local teacher can reattach after clean lesson removal")
	lesson.previous()
	check(lesson.active and lesson.step==0 and app.frame==0 and app.world_selection.selected.is_empty(),"whole-scene Previous still works after teacher-only crash recovery")
	lesson.active=false
	var report:={"checks":checks,"failures":failures,"startup":result}
	FileAccess.open(folder.path_join("startup-result.json"),FileAccess.WRITE).store_string(JSON.stringify(report));print("LESSON_AUTOSAVE_STARTUP "+JSON.stringify(report));get_tree().quit(0 if failures==0 else 1)
