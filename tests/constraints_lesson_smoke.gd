extends SceneTree
const Pins=preload("res://src/constraints_lesson.gd")
const Assets=preload("res://src/tutorial_assets.gd")
const Recovery=preload("res://src/recovery.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var lesson
var editor
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Constraint lesson watchdog");quit(2));call_deferred("run")
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
func current() -> RefCounted:return Pins.rig(lesson)
func pin(at: int) -> Dictionary:return Pins.contact(current(),at)
func range_edit(first: int,last: int,plant: bool) -> void:
	app.set_frame(first);editor.contacts.control.pressed.emit();await settle();editor.contacts.end_frame.value=last
	if plant:editor.contacts.plant_button.pressed.emit()
	else:editor.contacts.release_button.pressed.emit()
	await settle()
func numeric(y: float) -> void:
	editor.selected="@root";editor.operation.select(1);editor.refresh_values();editor.fields[1].value=y;editor.apply_numeric()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	lesson=app.tutorials;lesson.set_process(false);editor=app.pose_editor
	if "--read" in args:
		var expected:=Recovery.read_json(folder.path_join("expected.json"))
		check(lesson.start(Pins.ID,false,expected.session),"cold Continue opens retained constraints practice")
		check(lesson.step==4 and not lesson.done and app.frame==12 and not pin(12).is_empty() and not lesson.satisfied(),"cold resume retains planted feet and unfinished release task")
		check(app.has_project.path.is_empty() and app.dirty and lesson.store.sessions(Pins.ID).size()==2,"continued constraints practice is an unsaved independent copy")
		lesson.previous();await settle();check(lesson.step==3 and current().sample_transform(12).position[1]==0 and not pin(12).is_empty(),"cold Previous restores planted range before lowering body")
		lesson.active=false;app.has_project.open_file(folder.path_join("Constraints.has"));await job();app.world_selection.select_entity(Assets.FIGURE_ID);app.set_frame(12)
		check(not pin(0).is_empty() and pin(12).is_empty() and current().sample_transform(12).position[1]<-.015,"ordinary HAS retains editable root key and precise released range")
		app.free();print("CONSTRAINTS_LESSON_READ ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1);return
	var manifest:=Recovery.read_json("res://examples/tutorials/manifest.json")
	check(lesson.start(Pins.ID,true),"focused constraint chapter opens real practice HAS");await job()
	app.set_advanced(true);check(not lesson.satisfied(),"Advanced alone does not select the rig or Pose mode")
	app.world_selection.select_entity(Assets.FIGURE_ID);app.mode.select(2);app.change_mode(2);await observe();check(lesson.step==1,"actual selected rig in Pose mode advances")
	app.set_frame(24);check(not lesson.satisfied(),"neutral rig cannot complete the keyed arm exercise")
	editor.selected=lesson.bone(current(),"upper_arm.L");editor.operation.select(0);editor.refresh_values();editor.fields[2].value=65;editor.apply_numeric();await settle();await observe()
	check(lesson.step==2 and lesson.raised_arm(current()),"actual bone edit auto-keys and deforms the included figure")
	app.set_frame(0);editor.hold_feet.button_pressed=true;check(not lesson.satisfied(),"temporary Hold feet while posing does not count as a saved playback constraint");editor.hold_feet.button_pressed=false
	lesson.show_hint();await settle();check(lesson.marker.visible and lesson.marker.get_global_rect().encloses(editor.contacts.control.get_global_rect()),"hint highlights the actual planted range control")
	await range_edit(0,24,true);check(not pin(0).is_empty() and not pin(24).is_empty() and pin(25).is_empty(),"actual Plant button saves inclusive0–24 range")
	await observe();check(lesson.step==3,"saved range advances to body move task")
	app.set_frame(12);check(not lesson.satisfied(),"unchanged body does not satisfy lowering exercise")
	var before: Dictionary=current().data.duplicate(true);numeric(10);await settle();check(current().data==before and not lesson.satisfied(),"unreachable move refuses without corrupting lesson or constraints")
	numeric(-.03);await settle();check(lesson.satisfied(),"small auto-keyed root move satisfies actual planted foot positions")
	var planted: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	await observe();check(lesson.step==4,"authored constrained body move advances automatically")
	var session: String=lesson.session;lesson.leave(true);check(lesson.start(Pins.ID,true),"another fresh practice can start");await job()
	check(lesson.session!=session and lesson.store.sessions(Pins.ID).size()==2,"fresh practice retains earlier constraints session")
	lesson.leave(true);check(lesson.start(Pins.ID,false,session) and lesson.step==4 and not lesson.satisfied() and not pin(12).is_empty(),"Continue restores incomplete release and exact planted motion")
	await range_edit(12,24,false);check(lesson.satisfied() and not pin(11).is_empty() and pin(12).is_empty(),"actual Release button changes only requested latter range")
	app.undo();check(not lesson.satisfied() and not pin(12).is_empty(),"Release Undo restores persistent pin and incomplete task")
	app.redo();check(lesson.satisfied() and pin(12).is_empty(),"Release Redo restores exact ranged change")
	await observe();check(lesson.done and lesson.step==5,"constraints chapter finishes only after real partial release")
	app.has_project.save_file(folder.path_join("Constraints.has"),"packed");await job()
	var released: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and FileAccess.file_exists(movie) and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==released.get_data(),"real exported MP4 retains exact released pose render")
	lesson.previous();await settle();check(lesson.step==4 and not lesson.done and not pin(12).is_empty() and not lesson.satisfied(),"Previous restores whole pre-release constrained scene")
	var restored: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	check(restored.get_data()==planted.get_data(),"Previous restores identical constrained geometry pixels")
	lesson.leave(true);lesson.store.write_json(folder.path_join("expected.json"),{"session":session})
	var unchanged:=true
	for name in manifest.files:unchanged=unchanged and FileAccess.get_sha256("res://examples/tutorials/"+name)==manifest.files[name].sha256
	check(unchanged,"bundled original assets and sample HAS bytes stay unchanged")
	app.free();print("CONSTRAINTS_LESSON_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));quit(0 if failures==0 else 1)
