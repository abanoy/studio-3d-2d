extends SceneTree
const Assets=preload("res://src/tutorial_assets.gd")
const Store=preload("res://src/lesson_store.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const Recovery=preload("res://src/recovery.gd")
const IK=preload("res://src/limb_ik.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Tutorial watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func job(app) -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func observe(lesson) -> void:
	lesson.next_tick=0;lesson._process(0);await settled()
func equal(a,b) -> bool:
	return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func dialog(app) -> ConfirmationDialog:
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:return child
	return null
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var lesson=app.tutorials;lesson.set_process(false)
	if "--resume" in OS.get_cmdline_user_args():
		var expected:=Recovery.read_json(folder.path_join("expected.json"))
		check(lesson.start("basic-pose",false),"fresh process Continue opens validated saved practice")
		check(lesson.step==2 and not lesson.done and lesson.session==expected.session and app.frame==24 and app.has_project.path.is_empty() and app.dirty,"Continue restores teacher step, playhead and unsaved copy identity")
		check(equal(Store.ui(app),expected.ui) and Storage.image_hash(Drawing.cel_at(app.layers[1],24).image)==expected.paint,"Continue restores exact editor camera, selection and editable pixels")
		check(app.renderer.world_runtime.instance(Assets.FIGURE_ID).authored_keys().size()==2,"Continue restores real native pose keys in a new engine process")
		lesson.open_catalog();await settled();var catalog: AcceptDialog
		for child in app.get_children():
			if child is AcceptDialog and child.title=="Tutorials":catalog=child
		check(catalog!=null and catalog.find_children("","MenuButton",true,false).size()==1,"catalog exposes earlier saved practices as real choices")
		if catalog:catalog.hide();catalog.queue_free()
		lesson.active=false;app.free();print("TUTORIAL_RESUME "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1);return
	var manifest:=Recovery.read_json(ProjectSettings.globalize_path("res://examples/tutorials/manifest.json"));var original: Dictionary=manifest.files.duplicate(true)
	app.home.tutorials_button.pressed.emit();await settled();var catalog: AcceptDialog
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Tutorials":catalog=child
	check(catalog!=null and Rect2(Vector2.ZERO,Vector2(app.get_window().size)).encloses(catalog.get_visible_rect()),"Home Tutorials opens actual course catalog")
	if catalog:catalog.hide();catalog.queue_free()
	check(lesson.start("basic-pose",true),"included packed practice starts through normal HAS worker");await job(app)
	check(lesson.active and lesson.step==0 and not app.home.visible and app.has_project.path.is_empty() and app.dirty and app.home.store.read().is_empty(),"practice opens editable and unsaved without adding built-in scene to recents")
	var rig: RefCounted=app.renderer.world_runtime.instance(Assets.FIGURE_ID)
	if rig==null:
		print("TUTORIAL_LOAD_DIAGNOSTIC "+JSON.stringify({"error":app.open_project_error,"loading":lesson.loading,"active":lesson.active,"world":app.renderer.world_state()}));app.free();quit(1);return
	check(rig!=null and rig.order.size()==17 and app.renderer.world_state().objects.size()==2,"real bundled map and seventeen-bone original figure share normal world format")
	var hand: String=lesson.bone(rig,"hand.L");var upper: String=lesson.bone(rig,"upper_arm.L")
	check(not IK.chain(rig,hand).is_empty(),"practice figure supports shared natural hand posing")
	var neutral: Image=await app.renderer.capture(app.keys,[],0,true);neutral.save_png(folder.path_join("practice-neutral.png"))
	check(not lesson.satisfied(),"unselected scene cannot complete selection exercise")
	app.world_selection.select_entity(Assets.FIGURE_ID);await observe(lesson)
	check(lesson.step==1 and FileAccess.file_exists(lesson.store.folder(lesson.course,lesson.session).path_join("step_01/project.json")),"actual selection automatically advances and saves whole-scene checkpoint")
	var before: Dictionary=Store.ui(app);var root_before: Dictionary=rig.sample_transform(0)
	lesson.last_signature="%d:%d:%s:%s" % [app.recovery_revision,app.frame,app.world_selection.selected,str(app.advanced_mode)];lesson.last_action=Time.get_ticks_msec()-16000;await observe(lesson)
	check(lesson.hint_due and lesson.hint_button.text=="Need a hint?","quiet hint offered after simulated sixteen seconds stuck")
	lesson.hint_button.pressed.emit();check(equal(Store.ui(app),before) and rig.sample_transform(0)==root_before and lesson.step==1,"requested hint changes instruction without moving or keying anything")
	app.set_frame(24);await settled();check(not lesson.satisfied(),"frame change and neutral pose cannot complete raised-arm task")
	var editor=app.pose_editor;editor.selected=upper;editor.operation.select(0);editor.refresh_values();editor.fields[2].set_value_no_signal(65);editor.apply_numeric();await settled()
	check(rig.authored_keys().size()==2 and lesson.satisfied(),"normal numeric bone edit raises real skinned hand and auto-keys frame24")
	var posed: Image=await app.renderer.capture(app.keys,[],24,true);posed.save_png(folder.path_join("practice-raised.png"));check(posed.get_data()!=neutral.get_data(),"raising tutorial arm actually changes rendered geometry")
	await observe(lesson);check(lesson.step==2,"correct keyed arm automatically advances to independent drawing")
	var checkpoint_ui: Dictionary=Store.ui(app);var checkpoint_world: Dictionary=app.renderer.world_state().duplicate(true);var session: String=lesson.session
	app.active_layer=0;app.refresh_layer();app.create_cel(false);Drawing.cel_at(app.layers[0],24).image.fill_rect(Rect2i(40,40,50,50),Color.RED);app.changed();check(not lesson.satisfied(),"paint on Rough does not complete Ink exercise")
	app.active_layer=1;app.refresh_layer();app.create_cel(false);check(not lesson.satisfied(),"empty Ink cel does not complete drawing exercise")
	Drawing.cel_at(app.layers[1],24).image.fill_rect(Rect2i(80,80,80,40),Color.CYAN);app.changed();app.layers[1].visible=false;check(not lesson.satisfied(),"hidden Ink does not complete visible drawing exercise");app.layers[1].visible=true
	await observe(lesson);check(lesson.done and lesson.step==3,"visible independent drawing completes real practice chapter")
	app.renderer.camera.position+=Vector3(3,2,1);app.renderer.camera.fov=72;app.canvas.zoom=1.4;app.canvas.pan=Vector2(20,30);app.set_frame(5);app.world_selection.clear();app.set_advanced(true)
	lesson.previous();await settled();rig=app.renderer.world_runtime.instance(Assets.FIGURE_ID)
	check(lesson.step==2 and not lesson.done and app.frame==24 and Drawing.cel_at(app.layers[1],24).is_empty(),"Previous restores earlier scene and removes later drawing cels")
	print("PREVIOUS_STATE "+JSON.stringify({"ui_exact":equal(Store.ui(app),checkpoint_ui),"world_exact":equal(World.portable(app.renderer.world_state()),World.portable(checkpoint_world))}))
	check(equal(Store.ui(app),checkpoint_ui) and equal(World.portable(app.renderer.world_state()),World.portable(checkpoint_world)),"Previous restores whole world, pose, exact view, selection, mode and canvas")
	lesson.previous();await settled();rig=app.renderer.world_runtime.instance(Assets.FIGURE_ID)
	check(lesson.step==1 and app.frame==0 and rig.authored_keys().size()==1 and equal(Store.ui(app),before),"Previous again restores neutral arm, playhead and previous editor state")
	app.set_frame(24);editor.selected=upper;editor.operation.select(0);editor.refresh_values();editor.fields[2].set_value_no_signal(65);editor.apply_numeric();await settled();await observe(lesson)
	app.active_layer=1;app.refresh_layer();app.create_cel(false);Drawing.cel_at(app.layers[1],24).image.fill_rect(Rect2i(80,80,80,40),Color.CYAN);app.changed()
	var resume_ui: Dictionary=Store.ui(app);var paint:=Storage.image_hash(Drawing.cel_at(app.layers[1],24).image)
	lesson.leave(true);check(not lesson.active and not lesson.panel.visible and lesson.store.progress("basic-pose").step==2,"Leave stores current partial step and keeps practice editable")
	check(lesson.start("basic-pose",true),"Start fresh permits another independent practice");await job(app)
	check(lesson.session!=session and lesson.store.sessions("basic-pose").size()==2,"Start fresh retains prior saved practice")
	lesson.leave(true);check(lesson.start("basic-pose",false,session),"specific older practice can be continued")
	check(equal(Store.ui(app),resume_ui) and Storage.image_hash(Drawing.cel_at(app.layers[1],24).image)==paint,"Continue restores ungraded edits as well as progress")
	lesson.leave(true)
	var expected:={"session":session,"ui":resume_ui,"paint":paint};write_fixture_json(folder.path_join("expected.json"),expected)
	# Make this retained partial practice latest for the separate-process reader.
	lesson.store.write_json(lesson.store.root.path_join("basic-pose.json"),{"session":session})
	check(lesson.start("advanced-camera",true),"Advanced chapter starts its own real practice scene");await job(app)
	app.set_advanced(false);check(not lesson.satisfied(),"Simple state cannot satisfy Advanced exercise");app.set_advanced(true);await observe(lesson);check(lesson.step==1,"revealing Advanced automatically advances")
	app.set_frame(24);app.renderer.camera.position+=Vector3(.6,.1,0);check(not lesson.satisfied(),"temporary camera navigation does not satisfy explicit camera-key task")
	app.key_dialog();await settled();await observe(lesson);check(lesson.step==2,"explicit changed camera key completes shot task")
	var baseline: float=lesson.fov_baseline;app.renderer.camera.fov=baseline+10;check(not lesson.satisfied(),"temporary FOV without replaced key does not satisfy recorded lens task")
	app.key_dialog();await settled();var confirm:=dialog(app);if confirm:confirm.get_ok_button().pressed.emit()
	await settled();check(lesson.satisfied(),"replacing frame24 key records requested FOV change")
	lesson.leave(true);check(lesson.start("advanced-camera",false) and is_equal_approx(lesson.fov_baseline,baseline) and lesson.satisfied(),"Continue retains original lens baseline even after an ungraded replacement")
	await observe(lesson);check(lesson.done,"Advanced chapter completes through observed recorded camera states")
	lesson.panel.get_viewport().get_texture().get_image().save_png(folder.path_join("tutorial-editor.png"))
	lesson.leave(true);var world: Dictionary=app.renderer.world_state();var identity: String=app.has_project.path
	var broken: String=lesson.store.folder("advanced-camera",lesson.session).path_join("resume/project.json");var content:=Recovery.read_json(broken);content.editor.lesson_ui.basis=[0,0,0,0,0,0,0,0,0];lesson.store.write_json(broken,content)
	check(not lesson.start("advanced-camera",false) and app.renderer.world_state()==world and app.has_project.path==identity,"invalid saved lesson view refuses before replacing live scene")
	var personal:=folder.path_join("My practice.has");app.has_project.save_file(personal,"packed");await job(app);check(FileAccess.file_exists(personal) and not app.dirty,"practice saves as ordinary personal packed HAS")
	app.has_project.open_file(personal);await job(app);app.set_frame(24);var reopened: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var error: String=await app.export_movie(folder);var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==reopened.get_data(),"ordinary saved practice exports MP4 with exact reopened preview pixels")
	for name in original:
		check(FileAccess.get_sha256("res://examples/tutorials/"+name)==original[name].sha256,"built-in sample bytes preserved: "+name)
	app.has_project.save_file(ProjectSettings.globalize_path("res://examples/tutorials/practice"),"packed");check(app.has_project.pid<0 and FileAccess.get_sha256("res://examples/tutorials/practice.has")==original["practice.has"].sha256,"Save refuses built-in practice even without extension")
	var untouched:=folder.path_join("invalid-extra");var save_error:=Storage.save_project(untouched,app.video,app.keys,app.layers,app.source,app.frame,app.audio_clip,{},app.renderer.model_state(),true,app.renderer.world_state(),{"unexpected":{}})
	check(not save_error.is_empty() and not DirAccess.dir_exists_absolute(untouched),"invalid reserved lesson snapshot field is rejected before writes")
	check(not Store.session_ok("../escape") and not Store.valid_ui({}) and lesson.store.folder("unknown","123").is_empty(),"lesson store rejects unsafe addresses and malformed UI")
	var old_world: Dictionary=app.renderer.world_state();lesson.assets_root=folder.path_join("absent-samples")
	check(not lesson.start("basic-pose",true) and app.renderer.world_state()==old_world,"missing included assets refuse without replacing current work");lesson.assets_root="res://examples/tutorials"
	app.changed();lesson.request("basic-pose",true);await settled();check(dialog(app)!=null and not lesson.loading,"starting a lesson protects dirty work with confirmation")
	if dialog(app):dialog(app).get_cancel_button().pressed.emit()
	await settled();check(app.renderer.world_state()==old_world and not lesson.loading,"canceling lesson replacement preserves whole current scene")
	check(lesson.start("basic-pose",false,session),"resume saved basic practice for document lifecycle checks")
	app.new_dialog();await settled();check(dialog(app)!=null and lesson.active,"New confirms before leaving an active unsaved lesson")
	if dialog(app):dialog(app).get_cancel_button().pressed.emit()
	await settled();check(lesson.active and app.renderer.world_runtime.instance(Assets.FIGURE_ID)!=null,"canceling New retains lesson and practice scene")
	app.new_dialog();await settled();if dialog(app):dialog(app).get_ok_button().pressed.emit()
	await settled();check(not lesson.active and app.renderer.world_state().objects.is_empty() and lesson.store.progress("basic-pose",session).current=="resume","confirmed New saves lesson progress before replacing scene")
	# Preserve the same latest partial practice for the fresh reader.
	lesson.store.write_json(lesson.store.root.path_join("basic-pose.json"),{"session":session})
	print("TUTORIAL_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder,"movie":movie}));app.free();quit(0 if failures==0 else 1)

func write_fixture_json(path: String,value: Dictionary) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(value,"",true,true));file.close()
