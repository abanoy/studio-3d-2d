extends "res://tests/movement_path_smoke.gd"
const Store=preload("res://src/lesson_store.gd")
const Recovery=preload("res://src/recovery.gd")
const Assets=preload("res://src/tutorial_assets.gd")
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Lesson autosave watchdog");quit(2));call_deferred("run")
func idle() -> void:
	await settled()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("writer-cache")
	var lesson=app.tutorials;lesson.set_process(false);check(lesson.start("basic-pose",true),"ordinary bundled practice starts for clean-scene autosave test");await wait_job()
	app.world_selection.select_entity(Assets.FIGURE_ID);lesson.next_tick=0;lesson._process(0);await settled();check(lesson.active and lesson.step==1,"real selection advances to pending arm exercise")
	var manual:=folder.path_join("Manual practice.has");app.has_project.save_file(manual,"packed");await wait_job();var manual_hash:=FileAccess.get_sha256(manual)
	check(not app.dirty and app.has_project.path==manual and app.autosave_actions==0,"manual Save leaves clean scene and zero edit count")
	var revision: int=app.recovery_revision;var history: int=app.history.size();var progress: String=lesson.store.folder(lesson.course,lesson.session).path_join("progress.json");var progress_hash:=FileAccess.get_sha256(progress)
	app.set_frame(12);app.canvas.zoom=1.25;app.canvas.pan=Vector2(12,17);app.renderer.camera.position+=Vector3(.1,0,0);lesson.set_collapsed(true)
	app.autosave_enabled.button_pressed=true;app.autosave_due=0
	var target: String=app.recovery_root.path_join(app.recovery_session).path_join("project.json");var deadline:=Time.get_ticks_msec()+5000
	while not FileAccess.file_exists(target) and Time.get_ticks_msec()<deadline:await process_frame
	await idle();check(FileAccess.file_exists(target),"ordinary timer protects changed lesson UI even when project is clean")
	if "--probe" in OS.get_cmdline_user_args():
		lesson.active=false;print("LESSON_AUTOSAVE_PROBE "+JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	if not FileAccess.file_exists(target):lesson.active=false;app.free();quit(1);return
	var data:=Recovery.read_json(target);var previous:=FileAccess.get_sha256(target)
	check(data.editor.frame==12 and data.editor.recovery.lesson.ui.pan==[12.,17.] and data.editor.recovery.lesson.collapsed,"timed checkpoint captures matching scene frame and full teacher UI")
	check(not app.dirty and app.recovery_revision==revision and app.history.size()==history and app.autosave_actions==0 and app.has_project.path==manual,"lesson-only checkpoint does not dirty scene, create Undo or change personal Save identity")
	app.autosave_due=0;app.autosave_tick();await idle();check(FileAccess.get_sha256(target)==previous,"unchanged teacher state does not create repeated checkpoints")
	app.set_frame(14);app.autosave_due=Time.get_ticks_msec()+600000;app.autosave_tick();await idle();check(FileAccess.get_sha256(target)==previous,"lesson UI changes respect existing minute deadline")
	app.autosave_enabled.button_pressed=false;app.autosave_due=0;app.autosave_tick();await idle();check(FileAccess.get_sha256(target)==previous,"disabled automatic recovery preserves pending lesson changes")
	app.autosave_tick(true);await idle();check(FileAccess.get_sha256(target)!=previous and Recovery.read_json(target).editor.frame==14,"explicit Checkpoint now protects pending lesson despite disabled schedule")
	previous=FileAccess.get_sha256(target);app.set_frame(16);app.autosave_enabled.button_pressed=true;app.autosave_schedule.select(1);app.autosave_action_limit.value=1;app.autosave_due=0;app.autosave_tick();await idle()
	check(app.autosave_actions==0 and FileAccess.get_sha256(target)==previous,"teacher navigation does not count as a scene edit in action-count mode")
	app.autosave_schedule.select(0);app.autosave_due=0
	for property in ["drawing","navigating","playing","exporting"]:
		app.set(property,true);app.autosave_tick(true);app.set(property,false);check(FileAccess.get_sha256(target)==previous,"lesson checkpoint waits while "+property)
	var modal:=AcceptDialog.new();app.add_child(modal);modal.popup_centered();app.autosave_tick(true);check(FileAccess.get_sha256(target)==previous,"lesson checkpoint waits for open dialog");modal.hide();modal.queue_free()
	app.autosave_tick(true);deadline=Time.get_ticks_msec()+5000
	while FileAccess.get_sha256(target)==previous and Time.get_ticks_msec()<deadline:await process_frame
	await idle();print("LESSON_QUEUE_STATE "+JSON.stringify({"frame":app.frame,"saved_frame":Recovery.read_json(target).get("editor",{}).get("frame"),"pending":app.recovery_checkpoint_requested,"dialog":app.has_dialog(app)}))
	check(FileAccess.get_sha256(target)!=previous and Recovery.read_json(target).editor.frame==16,"queued lesson checkpoint runs after interaction guards clear")
	previous=FileAccess.get_sha256(target);app.set_frame(18);app.canvas.pan=Vector2(18,23);app.autosave_due=0
	DirAccess.make_dir_recursive_absolute(target+".tmp");app.autosave_tick();var retry: int=app.autosave_retry_due
	check(retry>Time.get_ticks_msec() and FileAccess.get_sha256(target)==previous,"failed lesson-only write preserves last checkpoint and schedules retry")
	app.autosave_tick();check(app.autosave_retry_due==retry and FileAccess.get_sha256(target)==previous,"unchanged retry backoff avoids repeated lesson writes")
	DirAccess.remove_absolute(target+".tmp");app.autosave_retry_due=Time.get_ticks_msec()-1;app.autosave_tick();await idle()
	check(FileAccess.get_sha256(target)!=previous and Recovery.read_json(target).editor.frame==18,"successful retry captures pending lesson after clean-scene write failure")
	previous=FileAccess.get_sha256(target);lesson.observed["preview_seen"]=true;app.autosave_due=0;app.autosave_tick();await idle()
	check(FileAccess.get_sha256(target)!=previous and Recovery.read_json(target).editor.recovery.lesson.ui.observed.preview_seen,"whitelisted teacher observation alone checkpoints without a scene edit")
	check(not app.dirty and app.recovery_revision==revision and app.history.size()==history and FileAccess.get_sha256(manual)==manual_hash and FileAccess.get_sha256(progress)==progress_hash,"all lesson autosaves preserve manual project, step progress and scene edit state")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,18,true);picture.save_png(folder.path_join("frame18.png"))
	var expected:={"manual":manual,"manual_sha256":manual_hash,"course":lesson.course,"session":lesson.session,"ui":Store.ui(app),"observed":lesson.observed,"progress":progress,"progress_sha256":progress_hash,"checkpoint":target.get_base_dir()}
	var expected_bytes:=JSON.stringify(expected,"",true,true);var expected_file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);expected_file.store_string(expected_bytes);expected_file.flush();var expected_error:=expected_file.get_error();expected_file.close()
	check(expected_error==OK and FileAccess.get_file_as_string(folder.path_join("expected.json"))==expected_bytes,"harness expectation file is flushed and read back before deliberate abrupt termination")
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("LESSON_AUTOSAVE_WRITER "+JSON.stringify({"checks":checks,"failures":failures}))
	if failures>0:lesson.active=false;app.free();quit(1);return
	OS.kill(OS.get_process_id());FileAccess.open(folder.path_join("kill-returned.txt"),FileAccess.WRITE).store_string("unexpected");quit(2)
