extends SceneTree
const Curves=preload("res://src/interpolation_lesson.gd")
const Timeline=preload("res://src/timeline.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
const Storage=preload("res://src/storage.gd")
var app
var lesson
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Interpolation lesson watchdog");quit(2));call_deferred("run")
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
func mode(index: int) -> void:
	app.mode.select(index);app.change_mode(index)
func outgoing(index: int) -> void:
	mode(0);app.set_frame(0);mode(1);await save_key(index);mode(0)
func save_key(mode: int) -> void:
	app.interpolation.select(mode);app.key_dialog();await settle()
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:child.get_ok_button().pressed.emit()
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	lesson=app.tutorials;lesson.set_process(false)
	if "--read" in args:
		var expected:=Recovery.read_json(folder.path_join("expected.json"))
		check(lesson.start(Curves.ID,false,expected.session),"cold Continue loads retained interpolation practice")
		check(lesson.step==4 and not lesson.done and app.frame==6 and lesson.key_at(0).interpolation=="linear" and not lesson.satisfied(),"cold practice retains exact incomplete ease task and linear keys")
		check(app.has_project.path.is_empty() and app.dirty and lesson.store.sessions(Curves.ID).size()==2,"Continue stays an unsaved copy and preserves prior session")
		lesson.previous();await settle();check(lesson.step==3 and lesson.key_at(0).interpolation=="hold" and app.frame==12,"cold Previous restores held camera and sample frame")
		lesson.active=false;app.has_project.open_file(folder.path_join("Interpolation.has"));await job()
		check(lesson.key_at(0).interpolation=="ease" and app.keys.size()==2,"ordinary packed HAS retains authored ease and both camera keys")
		check(Timeline.sample(app.keys,6).position.distance_to(Timeline.vector(app.keys[0].position).lerp(Timeline.vector(app.keys[1].position),.15625))<.0001,"cold reopened camera reproduces actual eased sample")
		app.free();print("INTERPOLATION_LESSON_READ ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1);return
	var manifest:=Recovery.read_json("res://examples/tutorials/manifest.json")
	check(Store.COURSES.get("advanced-lighting-v1")==4 and Store.COURSES.get("advanced-camera")==3,"existing course identities and lengths remain unchanged")
	check(lesson.start(Curves.ID,true),"new versioned interpolation chapter opens real bundled HAS");await job()
	check(lesson.active and app.renderer.world_runtime.instances.size()==2,"practice room and skinned figure use normal editable scene")
	app.set_advanced(false);check(not lesson.satisfied(),"Simple does not satisfy Advanced")
	app.set_advanced(true);app.mode.select(1);app.change_mode(1);await observe();check(lesson.step==1,"real Advanced control advances task")
	app.set_frame(24);app.renderer.camera.position+=Vector3(.8,.1,0);check(not lesson.satisfied(),"unrecorded camera navigation does not count as second key")
	await save_key(0);await observe();check(lesson.step==2,"saved distinct frame24 key completes endpoint exercise")
	app.set_frame(12);app.interpolation.select(2);check(not lesson.satisfied(),"changing interpolation menu without recording does not satisfy hold")
	await outgoing(2);check(not lesson.satisfied(),"recorded hold requires seeking requested sample frame")
	app.set_frame(12);lesson.show_hint();await settle();check(lesson.marker.visible and lesson.marker.get_global_rect().encloses(app.interpolation.get_global_rect()),"hint highlights real outgoing interpolation menu")
	var first: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var held: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	check(first.get_data()==held.get_data(),"actual held camera render stays exactly at first view")
	await observe();check(lesson.step==3,"authored hold and frame12 advance automatically")
	await outgoing(1);app.set_frame(6)
	check(lesson.satisfied() and Timeline.sample(app.keys,6).position.distance_to(Timeline.vector(app.keys[0].position).lerp(Timeline.vector(app.keys[1].position),.25))<.0001,"linear uses quarter-distance camera sample")
	var linear: Image=await app.renderer.capture(app.keys,app.layers,6,true)
	await observe();check(lesson.step==4,"actual linear sample advances to ease comparison")
	var session: String=lesson.session;lesson.leave(true);check(lesson.start(Curves.ID,true),"Start fresh opens another practice");await job()
	check(lesson.session!=session and lesson.store.sessions(Curves.ID).size()==2,"fresh practice retains the original checkpoints")
	lesson.leave(true);check(lesson.start(Curves.ID,false,session) and lesson.step==4 and not lesson.satisfied(),"Continue restores original unfinished ease comparison")
	await outgoing(0);app.set_frame(6)
	check(lesson.satisfied(),"saved ease at correct sample frame completes grading")
	var eased: Image=await app.renderer.capture(app.keys,app.layers,6,true)
	check(eased.get_data()!=linear.get_data() and eased.get_data()!=held.get_data(),"actual rendered ease differs from linear and held views")
	check(Timeline.sample(app.keys,24).position==Timeline.vector(app.keys[1].position),"easing preserves exact endpoint camera key")
	app.set_frame(6);var midpoint:=Timeline.key(12,Vector3(1,2,3),Quaternion.IDENTITY,55);app.keys.insert(1,midpoint)
	check(not lesson.satisfied(),"an intervening key cannot masquerade as the requested two-key comparison");app.keys.remove_at(1)
	await observe();check(lesson.done and lesson.step==5,"chapter completes through observed camera motion")
	var personal:=folder.path_join("Interpolation.has");app.has_project.save_file(personal,"packed");await job();check(FileAccess.file_exists(personal),"finished exercise saves as ordinary packed HAS")
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and FileAccess.file_exists(movie) and Image.load_from_file(app.last_export_folder.path_join("frame_000007.png")).get_data()==eased.get_data(),"actual MP4 shares exact eased comparison render")
	lesson.previous();await settle();check(lesson.step==4 and not lesson.done and lesson.key_at(0).interpolation=="linear" and app.frame==6,"Previous restores pre-ease whole checkpoint")
	lesson.leave(true);lesson.store.write_json(folder.path_join("expected.json"),{"session":session})
	var unchanged:=true
	for name in manifest.files:unchanged=unchanged and FileAccess.get_sha256("res://examples/tutorials/"+name)==manifest.files[name].sha256
	check(unchanged,"included original tutorial assets stay byte-identical")
	app.free();print("INTERPOLATION_LESSON_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));quit(0 if failures==0 else 1)
