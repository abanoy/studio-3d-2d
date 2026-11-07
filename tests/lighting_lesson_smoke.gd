extends SceneTree
const Light=preload("res://src/lighting_lesson.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
var app
var lesson
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(140).timeout.connect(func():push_error("Lighting lesson watchdog");quit(2));call_deferred("run")
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
func lighting(index: int) -> void:
	app.lighting_choice.select(index);app.lighting_choice.item_selected.emit(index)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	lesson=app.tutorials;lesson.set_process(false)
	if "--read" in args:
		var expected:=Recovery.read_json(folder.path_join("expected.json"))
		check(lesson.start(Light.ID,false,expected.session),"fresh process resumes retained partial lighting chapter")
		check(lesson.step==3 and not lesson.done and not lesson.satisfied() and app.video.lighting_mode=="studio","Continue restores lighting and unfinished export observation")
		check(app.has_project.path.is_empty() and app.dirty and lesson.export_button.is_visible_in_tree(),"continued practice stays unsaved with visible movie task")
		lesson.previous();await settle();check(lesson.step==2 and app.video.lighting_mode=="unshaded","cold Previous restores the earlier project lighting")
		check(lesson.store.sessions(Light.ID).size()==2,"fresh practice did not destroy the older session")
		lesson.active=false;app.free();print("LIGHTING_LESSON_READ ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1);return
	check(Store.COURSES.get("basic-pose")==3 and Store.COURSES.get("advanced-camera")==3 and Store.COURSES.get("first-movie-v1")==11,"existing course lengths and identities remain unchanged")
	var manifest:=Recovery.read_json("res://examples/tutorials/manifest.json")
	check(lesson.start(Light.ID,true),"versioned lighting chapter opens supplied real HAS practice");await job()
	check(lesson.active and app.renderer.world_runtime.instances.size()==2 and lesson.step==0,"included room and skinned figure remain editable")
	app.set_advanced(false);check(not lesson.satisfied(),"Simple does not satisfy Advanced task")
	app.set_advanced(true);await observe();check(lesson.step==1,"Advanced observation advances automatically")
	lighting(1);check(not lesson.satisfied(),"Lit does not satisfy the Unshaded comparison")
	lighting(0);await observe();check(lesson.step==2,"real lighting control completes base-color task")
	lesson.show_hint();await settle();check(lesson.marker.visible and lesson.marker.get_global_rect().encloses(app.lighting_choice.get_global_rect()),"requested hint highlights actual lighting menu")
	lighting(2);await observe();check(lesson.step==3 and lesson.export_button.is_visible_in_tree(),"Studio light advances to visible MP4 task")
	check(not lesson.satisfied(),"reaching export step does not award completion")
	var encoder: String=app.encoder_path.text;app.encoder_path.text=folder.path_join("missing-ffmpeg");var failed: String=await app.export_movie(folder);app.encoder_path.text=encoder
	check(not failed.is_empty() and not lesson.satisfied() and lesson.step==3,"failed encoder preflight preserves unfinished exercise")
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and lesson.satisfied() and FileAccess.file_exists(movie),"actual successful MP4 event completes export criterion")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==image.get_data(),"lesson movie uses exact shared lighting preview pixels")
	await observe();check(lesson.done and lesson.step==4,"teacher marks complete only after movie succeeds")
	lesson.previous();await settle();check(lesson.step==3 and not lesson.done and not lesson.satisfied(),"Previous clears later export observation and requires a new movie")
	var session: String=lesson.session;lesson.leave(true)
	check(lesson.start(Light.ID,true),"Start fresh opens independent practice");await job();check(lesson.session!=session and lesson.store.sessions(Light.ID).size()==2,"Start fresh retains earlier checkpointed session")
	lesson.leave(true);check(lesson.start(Light.ID,false,session) and lesson.step==3 and app.video.lighting_mode=="studio" and not lesson.satisfied(),"Continue restores specified earlier practice and grading context")
	lesson.leave(true);write_fixture_json(folder.path_join("expected.json"),{"session":session})
	var unchanged:=true
	for name in manifest.files:unchanged=unchanged and FileAccess.get_sha256("res://examples/tutorials/"+name)==manifest.files[name].sha256
	check(unchanged,"included sample geometry, audio, HAS files and hashes stay unchanged")
	app.free();print("LIGHTING_LESSON_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}));quit(0 if failures==0 else 1)

func write_fixture_json(path: String,value: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(value,"",true,true));file.close()
