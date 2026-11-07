extends SceneTree
const Capture=preload("res://src/physics_lesson.gd")
const Assets=preload("res://src/tutorial_assets.gd")
const Store=preload("res://src/lesson_store.gd")
const Recovery=preload("res://src/recovery.gd")
var app
var lesson
var physics
var record
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Physics lesson watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func observe() -> void:
	lesson.next_tick=0;lesson._process(0);await settle()
func current() -> RefCounted:return Capture.rig(lesson)
func take(scope: int,cancel: bool=false) -> void:
	app.set_frame(0);app.world_selection.select_entity(Assets.FIGURE_ID);physics.toggle.button_pressed=true;await settle()
	record.scope.select(scope);record.scope.item_selected.emit(scope);record.button.pressed.emit()
	while record.active and record.last_frame<12:await physics_frame
	if cancel:record.cancel()
	elif record.active:record.button.pressed.emit()
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	lesson=app.tutorials;lesson.set_process(false);physics=app.physics_editor;record=physics.recording
	if "--read" in args:
		var expected:=Recovery.read_json(folder.path_join("expected.json"))
		check(lesson.start(Capture.ID,false,expected.session),"cold Continue opens retained recorded practice")
		check(lesson.step==4 and not lesson.done and not lesson.satisfied() and lesson.observed.get("local_record_seen",false) and Capture.recorded(current()),"cold resume restores actual recorded keys and incomplete export observation")
		check(app.has_project.path.is_empty() and app.dirty and lesson.export_button.is_visible_in_tree() and lesson.store.sessions(Capture.ID).size()==2,"continued physics practice remains unsaved and retains separate sessions")
		lesson.previous();await settle();check(lesson.step==3 and not lesson.observed.get("preview_seen",false) and not lesson.satisfied() and Capture.recorded(current()),"cold Previous keeps take while requiring a new preview")
		lesson.previous();await settle();check(lesson.step==2 and not lesson.observed.get("local_record_seen",false) and not Capture.recorded(current()),"Previous before capture removes later take and completion observation")
		app.free();print("PHYSICS_LESSON_READ ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1);return
	var manifest:=Recovery.read_json("res://examples/tutorials/manifest.json")
	check(Store.valid_observations({"physics_seen":true,"preview_seen":false,"export_done":false,"local_record_seen":true}) and not Store.valid_observations({"local_record_seen":1}) and not Store.valid_observations({"any_record":true}),"persisted capture observations remain narrowly typed and bounded")
	lesson.open_catalog();await settle();var catalog: AcceptDialog
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Tutorials":catalog=child
	check(catalog!=null and catalog.size.y<=root.size.y and not catalog.find_children("","ScrollContainer",true,false).is_empty(),"growing course catalog scrolls within the actual window")
	if catalog:catalog.hide();catalog.queue_free();await settle()
	check(lesson.start(Capture.ID,true),"new versioned physics course opens real HAS scene");await job()
	app.set_advanced(true);app.world_selection.select_entity(Assets.FIGURE_ID);app.mode.select(2);app.change_mode(2);await observe();check(lesson.step==1,"actual selected rig and Advanced Pose advance setup")
	check(not lesson.satisfied(),"already frozen figure cannot satisfy live motion exercise")
	physics.toggle.button_pressed=true;await settle();await observe();check(physics.body_active(Assets.FIGURE_ID) and lesson.observed.get("physics_seen",false) and lesson.step==1,"real running simulation is observed without prematurely advancing")
	for i in range(12):await physics_frame
	physics.toggle.button_pressed=false;await settle();check(not Capture.recorded(current()),"unrecorded live motion does not produce dense capture keys")
	await observe();check(lesson.step==2,"freeze after actual simulation advances to explicit capture")
	lesson.show_hint();await settle();check(lesson.marker.visible and lesson.marker.get_global_rect().encloses(record.button.get_global_rect()),"capture hint highlights actual Record control")
	await take(0,true);check(not lesson.observed.get("local_record_seen",false) and not lesson.satisfied() and not Capture.recorded(current()),"cancelled Local take does not award capture or author keys")
	await take(1);check(Capture.recorded(current()) and not lesson.observed.get("local_record_seen",false) and not lesson.satisfied(),"World take is real animation but does not satisfy specifically requested Local exercise")
	app.undo();await settle();check(not Capture.recorded(current()),"one capture Undo restores prior undensified motion")
	await take(0);check(Capture.recorded(current()) and lesson.observed.get("local_record_seen",false) and lesson.satisfied() and not physics.is_running(),"successful Local commit awards actual sampled take with Physics off")
	await observe();check(lesson.step==3,"committed take advances to playback task")
	check(not lesson.satisfied(),"recording alone does not award preview")
	app.set_frame(0);app.toggle_play();await observe();check(app.playing and lesson.observed.get("preview_seen",false) and lesson.step==3,"actual playback is observed while teacher waits for pause")
	app.stop();await observe();check(lesson.step==4 and lesson.export_button.is_visible_in_tree() and not lesson.satisfied(),"paused recorded playback advances to visible unfinished movie task")
	var session: String=lesson.session;lesson.leave(true);check(lesson.start(Capture.ID,true),"fresh physics practice starts independently");await job()
	check(lesson.session!=session and lesson.store.sessions(Capture.ID).size()==2,"Start fresh retains prior captured session")
	lesson.leave(true);check(lesson.start(Capture.ID,false,session) and lesson.step==4 and Capture.recorded(current()) and not lesson.satisfied(),"Continue restores captured keys and unfinished export")
	var encoder: String=app.encoder_path.text;app.encoder_path.text=folder.path_join("missing-encoder");var failed: String=await app.export_movie(folder);app.encoder_path.text=encoder
	check(not failed.is_empty() and not lesson.satisfied(),"failed MP4 leaves physics chapter incomplete")
	var captured: Image=await app.renderer.capture(app.keys,app.layers,6,true)
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and lesson.satisfied() and Image.load_from_file(app.last_export_folder.path_join("frame_000007.png")).get_data()==captured.get_data(),"actual MP4 uses exact saved take pixels and awards export")
	await observe();check(lesson.done and lesson.step==5,"chapter completes only after recorded practice exports")
	lesson.previous();await settle();check(lesson.step==4 and not lesson.done and not lesson.satisfied() and Capture.recorded(current()),"Previous clears export completion while retaining recorded animation")
	lesson.leave(true);write_fixture_json(folder.path_join("expected.json"),{"session":session})
	var unchanged:=true
	for name in manifest.files:unchanged=unchanged and FileAccess.get_sha256("res://examples/tutorials/"+name)==manifest.files[name].sha256
	check(unchanged,"original room, figure, audio and tutorial HAS files stay unchanged")
	app.free();print("PHYSICS_LESSON_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));quit(0 if failures==0 else 1)

func write_fixture_json(path: String,value: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(value,"",true,true));file.close()
