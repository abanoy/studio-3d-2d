extends "res://tests/movement_path_smoke.gd"
const Assets=preload("res://src/tutorial_assets.gd")
const Store=preload("res://src/lesson_store.gd")
var lesson
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Tutorial catalog watchdog");quit(2));call_deferred("run")
func catalog() -> AcceptDialog:
	for child in app.get_children():
		if child is AcceptDialog and child.title=="Tutorials" and child.visible:return child
	return null
func action(dialog: AcceptDialog,id: String,label: String) -> Button:
	for button in dialog.find_children("","Button",true,false):
		if button.get_meta("course_id","")==id and button.text==label:return button
	return null
func confirmation() -> ConfirmationDialog:
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:return child
	return null
func open_browser() -> AcceptDialog:
	app.home.tutorials_button.pressed.emit();await settled();return catalog()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.get_window().size=Vector2i(1100,700);await settled();app.has_project.cache_root=folder.path_join("cache");lesson=app.tutorials;lesson.set_process(false)
	var hashes:={}
	for name in ["Practice room.glb","Practice figure.glb","practice.has","first-movie.has","manifest.json"]:hashes[name]=FileAccess.get_sha256(lesson.assets_root.path_join(name))
	var browser: AcceptDialog=await open_browser();check(browser!=null,"Home opens actual tutorial browser")
	var tabs: Array=browser.find_children("","TabContainer",true,false);check(tabs.size()==1 and tabs[0].get_tab_count()==2,"browser offers distinct Basic and Advanced sections")
	if "--probe" in OS.get_cmdline_user_args():
		print("TUTORIAL_CATALOG_PROBE "+JSON.stringify({"checks":checks,"failures":failures}));browser.hide();browser.queue_free();await app.quit_studio();quit(0 if failures==0 else 1);return
	check(Rect2(Vector2.ZERO,Vector2(app.get_window().size)).encloses(browser.get_visible_rect()),"course browser fits a1100x700workspace")
	var ids: Array=[]
	for button in browser.find_children("","Button",true,false):
		if button.text=="Start fresh":ids.append(str(button.get_meta("course_id","")))
	ids.sort();var expected: Array=Store.COURSES.keys();expected.sort();check(ids==expected,"all seven existing course IDs remain reachable exactly once")
	browser.get_texture().get_image().save_png(folder.path_join("catalog-basic.png"))
	var levels: TabContainer=tabs[0];check(levels.get_tab_title(0)=="Basic" and levels.get_tab_title(1)=="Advanced" and levels.current_tab==0,"Basic route is first and Advanced remains directly accessible")
	check(action(browser,"first-movie-v1","Start fresh")!=null and action(browser,"basic-pose","Start fresh")!=null,"Basic exposes first-movie path and focused pose/draw practice")
	var titles: Array=[]
	for label in browser.find_children("","Label",true,false):titles.append(label.text)
	check(titles.has("Camera and rendering") and titles.has("Animation and posing") and titles.has("Physics"),"Advanced has named topic subsections")
	var before: Dictionary=app.project_snapshot().duplicate(true);var count: int=app.history.size();levels.current_tab=1;await settled()
	browser.get_texture().get_image().save_png(folder.path_join("catalog-advanced.png"))
	check(app.project_snapshot()==before and app.history.size()==count and not lesson.active,"browsing topics does not replace or edit current scene")
	var jump:=action(browser,"advanced-camera","Start fresh");check(jump!=null and jump.is_visible_in_tree(),"camera topic is an actionable visible Advanced entry")
	jump.pressed.emit();await wait_job();check(lesson.active and lesson.course=="advanced-camera" and lesson.step==0 and app.renderer.world_runtime.instance(Assets.FIGURE_ID)!=null,"topic entry starts existing validated editable practice at its own first task")
	var saved: String=lesson.session;lesson.leave(true);browser=await open_browser();levels=browser.find_children("","TabContainer",true,false)[0];levels.current_tab=1;await settled();jump=action(browser,"advanced-camera","Continue");check(jump!=null,"topic retains Continue action for saved practice")
	jump.pressed.emit();await settled();var prompt:=confirmation();check(prompt!=null and not lesson.active,"Continue respects unsaved replacement confirmation")
	if prompt:prompt.get_cancel_button().pressed.emit()
	await settled();check(not lesson.active and lesson.session==saved,"cancel keeps current scene and saved practice")
	browser=await open_browser();levels=browser.find_children("","TabContainer",true,false)[0];levels.current_tab=1;await settled();action(browser,"advanced-camera","Continue").pressed.emit();await settled();prompt=confirmation()
	if prompt:prompt.confirmed.emit();prompt.hide();prompt.queue_free()
	await settled();check(lesson.active and lesson.course=="advanced-camera" and lesson.session==saved and lesson.step==0,"topic Continue restores same session without shifting step identities")
	lesson.leave(true);app.dirty=false;browser=await open_browser();action(browser,"first-movie-v1","Start fresh").pressed.emit();await wait_job();check(lesson.active and lesson.course=="first-movie-v1" and lesson.step==0,"Basic start follows original beginner route from empty scene")
	check(not lesson.store.progress("advanced-camera",saved).is_empty(),"starting Basic preserves prior Advanced practice")
	var intact:=true
	for name in hashes:intact=intact and FileAccess.get_sha256(lesson.assets_root.path_join(name))==hashes[name]
	check(intact,"browser and practice entry preserve every supplied source asset")
	print("TUTORIAL_CATALOG_SMOKE "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1)
