extends SceneTree
const First=preload("res://src/first_movie_lesson.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Store=preload("res://src/lesson_store.gd")
const World=preload("res://src/world_document.gd")
const Recovery=preload("res://src/recovery.gd")
var app
var lesson
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("First movie watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
	# Keep production card layout/highlights processing while the task observer is
	# manually clocked for deterministic assertions. No early auto-grading.
	for i in range(3):
		if lesson and lesson.active:
			var next: int=lesson.next_tick;lesson.next_tick=Time.get_ticks_msec()+100000;lesson._process(0);lesson.next_tick=next
		await process_frame;await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func advance(at: int) -> bool:
	lesson.next_tick=0;lesson._process(0);await settled();check(lesson.step==at,"observed real task advances to step %d" % at)
	if lesson.step!=at:
		print("FIRST_MOVIE_STATE "+JSON.stringify({"step":lesson.step,"status":app.status.text,"observed":lesson.observed,"world":app.renderer.world_state()}));app.free();quit(1);return false
	return true
func picker() -> FileDialog:
	for child in app.get_children():
		if child is FileDialog and child.visible:return child
	return null
func confirm_key() -> void:
	app.key_dialog();await settled()
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:child.get_ok_button().pressed.emit()
	await settled()
func import_practice(name: String) -> void:
	lesson.action_button.pressed.emit();await settled();var dialog:=picker()
	check(dialog!=null and dialog.current_dir.replace("\\","/").ends_with("examples/tutorials"),"lesson import opens real picker beside offline practice assets")
	if dialog:dialog.file_selected.emit(ProjectSettings.globalize_path("res://examples/tutorials/"+name))
	await settled()
func equal(a,b) -> bool:
	return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");lesson=app.tutorials;lesson.set_process(false)
	if "--resume" in OS.get_cmdline_user_args():
		var expected:=Recovery.read_json(folder.path_join("first-expected.json"));check(lesson.start(First.ID,false,expected.session),"fresh process resumes completed versioned beginner lesson")
		check(lesson.done and lesson.step==11 and lesson.observed.get("physics_seen",false) and lesson.observed.get("preview_seen",false) and lesson.observed.get("export_done",false),"all completed observed events survive fresh process Continue")
		check(equal(Store.ui(app),expected.ui) and equal(World.portable(app.renderer.world_state()),expected.world) and Storage.image_hash(Drawing.cel_at(app.layers[1],24).image)==expected.paint,"fresh process keeps exact whole-scene and editor state")
		lesson.previous();await settled();check(lesson.step==10 and not lesson.done and not lesson.observed.get("export_done",false) and lesson.observed.get("preview_seen",false),"Previous removes later export evidence while retaining earlier real preview")
		check(app.has_project.path.is_empty() and lesson.action_button.visible and lesson.export_button.visible,"resumed final task offers optional Save and normal export without a personal identity")
		lesson.export_button.pressed.emit();await settled();var directory: FileDialog=picker();check(directory!=null and directory.file_mode==FileDialog.FILE_MODE_OPEN_DIR,"unsaved practice export uses actual destination picker")
		if directory:directory.dir_selected.emit(folder)
		while app.exporting:await process_frame
		check(FileAccess.file_exists(app.last_export_folder.path_join("movie.mp4")) and lesson.satisfied() and app.has_project.path.is_empty(),"successful unsaved export completes task without forcing a personal project save")
		if not await advance(11):return
		print("FIRST_MOVIE_RESUME "+JSON.stringify({"checks":checks,"failures":failures}));lesson.active=false;app.free();quit(0 if failures==0 else 1);return
	check(lesson.start(First.ID,true),"beginner course opens real included empty HAS");await job()
	check(lesson.active and lesson.step==0 and app.renderer.world_state().objects.is_empty() and app.world_selection.selected.is_empty() and app.video.world_background=="black","beginner practice starts empty, black and unselected")
	check(not lesson.satisfied(),"empty scene cannot satisfy map import")
	var initial: Dictionary=Store.ui(app);var history: int=app.history.size();lesson.show_hint();await settled()
	check(lesson.marker.visible and lesson.marker.mouse_filter==Control.MOUSE_FILTER_IGNORE and equal(Store.ui(app),initial) and app.history.size()==history,"visual hint outlines the actual import button without edits or input interception")
	root.get_texture().get_image().save_png(folder.path_join("first-movie-empty.png"))
	await import_practice("Practice room.glb");check(First.object(lesson,"environment")!=null and app.renderer.world_state().objects.size()==1,"normal map import creates a real environment in the empty world")
	if not await advance(1):return
	await import_practice("Practice figure.glb");var rig: RefCounted=First.object(lesson,"model")
	if not rig:check(false,"normal practice figure import must succeed");app.free();quit(1);return
	for i in range(20):await physics_frame
	lesson.next_tick=0;lesson._process(0);await settled()
	check(lesson.step==1 and lesson.observed.get("physics_seen",false) and app.physics_editor.body_active(rig.data.id),"actual default-on ragdoll is observed without advancing or freezing it")
	check(rig.authored_keys().is_empty(),"live imported physics creates no recorded motion keys")
	lesson.show_hint();await settled();check(lesson.marker.visible and lesson.marker.get_global_rect().encloses(app.physics_editor.toggle.get_global_rect()),"hint switches to the real Physics control after import")
	app.physics_editor.toggle.button_pressed=false;await settled();check(not app.physics_editor.is_running(),"normal Physics off freezes imported practice figure")
	if not await advance(2):return
	var session: String=lesson.session;lesson.leave(true);check(lesson.start(First.ID,false,session) and lesson.observed.get("physics_seen",false),"Continue retains genuine physics observation with the frozen scene")
	lesson.previous();await settled();check(lesson.step==1 and First.object(lesson,"model")==null and not lesson.observed.has("physics_seen"),"Previous restores map-only scene and removes later simulation evidence")
	await import_practice("Practice figure.glb");rig=First.object(lesson,"model");for i in range(20):await physics_frame
	lesson.next_tick=0;lesson._process(0);app.physics_editor.toggle.button_pressed=false;await settled();if not await advance(2):return
	app.world_selection.select_entity(rig.data.id);app.world_selection.context_action(1);await settled();check(lesson.satisfied(),"ordinary object Reset pose satisfies neutral selected figure task")
	if not await advance(3):return
	check(not lesson.satisfied(),"unchanged camera cannot satisfy navigation task")
	var shots: Array=app.keys.duplicate(true);app.camera_button(MOUSE_BUTTON_LEFT,true,true);app.camera_motion(Vector2(65,0));app.release_mouse();await settled()
	check(lesson.satisfied() and app.keys==shots,"actual Ctrl-left camera gesture changes view without recording a key")
	var nav_view: Dictionary=app.renderer.view_state();lesson.leave(true);check(lesson.start(First.ID,false,session) and lesson.satisfied() and equal(app.renderer.view_state(),nav_view),"Continue retains navigation and original step baseline")
	if not await advance(4):return
	check(not lesson.satisfied(),"old frame0 shot cannot satisfy newly navigated view")
	await confirm_key();check(lesson.satisfied(),"real explicit frame0 camera-key replacement is detected")
	if not await advance(5):return
	rig=First.object(lesson,"model");var upper: String=lesson.bone(rig,"upper_arm.L");app.set_frame(24);app.world_selection.select_entity(rig.data.id);var editor=app.pose_editor;editor.selected=upper;editor.operation.select(0);editor.refresh_values();editor.fields[2].set_value_no_signal(65);editor.apply_numeric();await settled()
	check(lesson.satisfied() and rig.authored_keys().size()==2,"shared body editor auto-keys a real raised arm at24")
	var ui: Dictionary=Store.ui(app);var pose: Dictionary=rig.data.duplicate(true);lesson.show_hint();await settled()
	check(lesson.marker.visible and lesson.marker.size==Vector2(28,28) and equal(Store.ui(app),ui) and rig.data==pose,"requested bone hint marks the projected shoulder without selecting or moving it")
	check(not lesson.panel.get_global_rect().intersects(lesson.marker.get_global_rect()),"guide chooses a corner that leaves the requested shoulder accessible")
	root.get_texture().get_image().save_png(folder.path_join("first-movie-bone-hint.png"))
	app.get_window().size=Vector2i(1200,760);await settled();lesson.collapse_button.pressed.emit();await settled()
	check(lesson.collapsed and not lesson.instruction.visible and Rect2(Vector2.ZERO,Vector2(app.get_window().size)).encloses(lesson.panel.get_global_rect()) and not lesson.panel.get_global_rect().intersects(lesson.marker.get_global_rect()) and equal(Store.ui(app),ui),"collapsed guide fits1200px and keeps shoulder accessible without changing scene/view")
	root.get_texture().get_image().save_png(folder.path_join("first-movie-1200.png"));app.get_window().size=Vector2i(1400,900);lesson.collapse_button.pressed.emit();await settled()
	if not await advance(6):return
	app.mode.select(1);app.change_mode(1);app.renderer.camera.position+=Vector3(.6,.1,0);check(not lesson.satisfied(),"temporary second view does not count before explicit camera key")
	await confirm_key();if not await advance(7):return
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.layer_choice.select(1);app.refresh_layer();app.create_cel(false)
	var world: Dictionary=World.portable(app.renderer.world_state());shots=app.keys.duplicate(true)
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(80,80));var motion:=InputEventMouseMotion.new();app.canvas_input(motion,Vector2(160,80));press.pressed=false;app.canvas_input(press,Vector2(160,80));await settled()
	check(lesson.satisfied() and World.portable(app.renderer.world_state())==world and app.keys==shots,"actual routed drawing creates visible Ink independently of all3D data")
	if not await advance(8):return
	check(not lesson.satisfied(),"paused scene does not count as preview before actual playback")
	app.set_frame(0);app.toggle_play();await settled();lesson.next_tick=0;lesson._process(0);check(lesson.observed.get("preview_seen",false) and lesson.step==8 and app.playing,"actual playback is observed while teacher leaves transport running")
	app.toggle_play();if not await advance(9):return
	rig=First.object(lesson,"model");app.set_frame(12);app.world_selection.select_entity(rig.data.id);var index:=0
	for at in range(app.timeline.object_rows.size()):
		if app.timeline.object_rows[at].id==rig.data.id:index=at
	var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_RIGHT;click.pressed=true;click.position=Vector2(app.timeline.x(12),app.timeline.row_y(index)+12);app.timeline._gui_input(click);await settled();app.timeline.import_menu.id_pressed.emit(10);await settled()
	check(rig.data.animation_clips.size()==2 and not lesson.satisfied(),"real timeline split alone does not satisfy requested move")
	var second: Dictionary=rig.data.animation_clips[1];var start:=Vector2(app.timeline.x(second.start+2),app.timeline.row_y(index)+12)
	click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=start;app.timeline._gui_input(click);var drag:=InputEventMouseMotion.new();drag.position=start+Vector2(app.timeline.x(28)-app.timeline.x(second.start),0);drag.button_mask=MOUSE_BUTTON_MASK_LEFT;app.timeline._gui_input(drag);click.pressed=false;click.position=drag.position;app.timeline._gui_input(click);await settled()
	check(lesson.satisfied() and rig.data.animation_clips[1].start==28 and app.keys==shots and World.portable(app.renderer.world_state()).objects.size()==2,"actual timeline drag retimes source animation without moving camera or removing model")
	if not await advance(10):return
	check(not lesson.satisfied(),"preexisting or absent export cannot complete final task")
	lesson.action_button.pressed.emit();await settled();var save:=picker();check(save!=null and save.file_mode==FileDialog.FILE_MODE_SAVE_FILE,"optional lesson Save opens normal portable HAS dialog")
	var personal:=folder.path_join("My first movie.has");if save:save.file_selected.emit(personal)
	await job();check(app.has_project.path==personal and not app.dirty,"actual optional personal save uses ordinary packed project worker")
	var encoder_path: String=app.encoder_path.text;app.encoder_path.text=folder.path_join("missing-encoder.exe");var error: String=await app.export_movie(folder);check(not error.is_empty() and not lesson.satisfied(),"failed encoder preflight never marks export task complete");app.encoder_path.text=encoder_path
	app.set_frame(40);var expected: Image=await app.renderer.capture(app.keys,app.layers,40,true);var personal_hash:=FileAccess.get_sha256(personal)
	lesson.export_button.pressed.emit();while app.exporting:await process_frame
	check(lesson.satisfied() and app.last_export_folder.get_base_dir()==folder and FileAccess.get_sha256(personal)==personal_hash,"normal Export movie uses saved project folder and records actual success without changing HAS")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000041.png")).get_data()==expected.get_data(),"first-movie export exactly matches animated pose/camera/Ink preview at40")
	if not await advance(11):return
	var movie: String=app.last_export_folder.path_join("movie.mp4");lesson.leave(true);lesson.store.write_json(folder.path_join("first-expected.json"),{"session":session,"ui":Store.ui(app),"world":World.portable(app.renderer.world_state()),"paint":Storage.image_hash(Drawing.cel_at(app.layers[1],24).image)})
	check(not Store.valid_observations({"export_done":"yes"}) and not Store.valid_observations({"other":true}) and not Store.checkpoint_name("basic-pose","step_11") and Store.checkpoint_name(First.ID,"step_11"),"versioned course counts and observation validation preserve old checkpoint contracts")
	print("FIRST_MOVIE_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"movie":movie}));app.free();quit(0 if failures==0 else 1)
