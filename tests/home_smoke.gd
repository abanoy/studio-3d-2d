extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Recovery=preload("res://src/recovery.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Recents=preload("res://src/recent_projects.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Home watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(app) -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func prompt(app) -> ConfirmationDialog:
	for child in app.get_children():
		if child is ConfirmationDialog and child.visible:return child
	return null
func recent_button(app,path: String) -> Button:
	for child in app.home.find_children("RecentProject","Button",true,false):
		if str(child.get_meta("path")).to_lower()==path.replace("\\","/").to_lower():return child
	return null
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var fixture:=folder.path_join("actor.glb");check(SceneIO.make_pose_fixture(fixture)==OK and app.pose_editor.add_model(fixture).is_empty(),"original standard rig loads for Home workflow")
	app.create_cel(false);var cel: Dictionary=Drawing.cel_at(app.layers[1],0);Drawing.edit_image(cel).image.fill_rect(Rect2i(0,0,384,216),Color.CYAN);app.changed()
	var a:=folder.path_join("My scene 日本.has");var b:=folder.path_join("Second scene.has")
	app.has_project.save_file(a,"packed");await wait_job(app)
	check(app.home.store.read().size()==1 and not app.dirty,"successful normal Save adds a real HAS to recent projects")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	while app.recovery_preview.busy():await process_frame
	app.has_project.save_current();await wait_job(app)
	var row: Dictionary=app.home.store.read()[0];var preview:=Recents.preview(row,app.recovery_root)
	check(preview!=null and preview.get_pixel(8,8)==Color.CYAN,"matching committed recovery preview supplies a real recent thumbnail")
	var a_hash:=FileAccess.get_sha256(a);var fixture_hash:=FileAccess.get_sha256(fixture)
	app.set_frame(8);Drawing.edit_image(cel).image.fill_rect(Rect2i(0,0,384,216),Color.RED);app.changed();app.has_project.save_file(b,"packed");await wait_job(app)
	check(app.home.store.read().size()==2 and app.home.store.read()[0].path.ends_with("Second scene.has"),"second successful Save orders recent projects newest first")
	var world: Dictionary=app.renderer.world_state();var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var frame: int=app.frame;var history: int=app.history.size();var pixels:=Storage.image_hash(Drawing.image(cel))
	app.home.open_home();await settled()
	check(app.home.visible and app.frame==frame and app.keys==keys and app.renderer.world_state()==world and app.renderer.view_state()==view and app.history.size()==history and Storage.image_hash(Drawing.image(cel))==pixels and not app.dirty,"opening Home preserves complete current edit/view state")
	app._unhandled_key_input(InputEventKey.new());var key:=InputEventKey.new();key.keycode=KEY_SPACE;key.pressed=true;app._input(key)
	check(not app.playing and app.frame==frame,"Home does not send play shortcuts into its covered scene")
	app.get_window().size=Vector2i(1200,760);await settled()
	# With expand stretch, controls report logical canvas units. Compare bounds
	# there, and convert the existing physical-size limits to window pixels.
	var viewport: Rect2=app.get_viewport_rect()
	var pixel_scale:=Vector2(app.get_window().size)/viewport.size
	var panel_pixels: Vector2=app.home.panel.size*pixel_scale
	print("HOME_LAYOUT "+JSON.stringify({"window":str(app.get_window().size),"viewport":str(viewport),"panel":str(app.home.panel.get_global_rect()),"panel_pixels":str(panel_pixels)}))
	check(viewport.encloses(app.home.panel.get_global_rect()) and panel_pixels.x<=1000 and panel_pixels.y<=700,"Home actions and bounded recent list fit a smaller app window")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("home.png"))
	app.home.return_button.pressed.emit();await settled()
	check(not app.home.visible and app.renderer.view_state()==view and app.keys==keys and app.frame==frame,"Return to scene closes Home without changing camera/frame")
	app.home.open_home();key.keycode=KEY_ESCAPE;app._input(key)
	check(not app.home.visible,"Escape returns to the scene")
	app.changed();app.home.open_home();app.home.new_button.pressed.emit();await settled();var confirm:=prompt(app)
	check(confirm!=null and app.home.visible and app.dirty,"Home New protects unsaved work with normal confirmation")
	confirm.get_cancel_button().pressed.emit();await settled()
	check(app.home.visible and app.dirty and app.renderer.world_state()==world,"canceling Home New preserves the complete scene")
	var select:=recent_button(app,a);select.pressed.emit();await settled();confirm=prompt(app)
	check(confirm!=null,"opening a recent project also confirms unsaved replacement")
	confirm.get_cancel_button().pressed.emit();await settled()
	check(app.home.visible and app.dirty and app.frame==frame,"canceling recent Open retains playhead and unsaved work")
	recent_button(app,a).pressed.emit();await settled();prompt(app).get_ok_button().pressed.emit();await wait_job(app)
	check(not app.home.visible and not app.dirty and app.frame==0 and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,"confirmed recent Open uses normal HAS loading and restores editable paint/frame")
	check(app.home.store.read().size()==2 and app.home.store.read()[0].path==a.replace("\\","/"),"successful normal Open promotes the recent row without duplicates")
	app.home.open_home();app.home.open_button.pressed.emit();await settled();var picker: FileDialog
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child
	if picker:print("HOME_PICKER "+JSON.stringify({"title":picker.title,"filters":Array(picker.filters)}))
	check(picker!=null and picker.file_mode==FileDialog.FILE_MODE_OPEN_FILE and str(picker.filters).contains("*.has ; Hybrid Animation Studio project"),"Home Open routes the actual project file picker")
	picker.get_cancel_button().pressed.emit();await settled();check(app.home.visible and not app.dirty,"canceling the file picker keeps Home and the current scene")
	var bad:=folder.path_join("broken.has");var file:=FileAccess.open(bad,FileAccess.WRITE);file.store_string("not a project");file.close();app.home.open_recent(bad);await wait_job(app)
	check(app.home.visible and app.home.notice.text!="Opening broken.has…" and not app.dirty and app.home.store.read().size()==2,"failed project Open stays visible with feedback and is never remembered")
	var b_hash:=FileAccess.get_sha256(b);check(DirAccess.rename_absolute(b,b+".moved")==OK,"move only an owned test project to simulate a missing recent file")
	app.home.refresh();await settled();var missing:=recent_button(app,b)
	check(missing!=null and missing.disabled and missing.text.contains("not found") and app.home.store.read().size()==2,"missing recent projects stay visible and cannot replace the scene")
	var remove: Button
	for child in missing.get_parent().get_children():
		if child is Button and child.text=="Remove":remove=child
	remove.pressed.emit();await settled()
	check(app.home.store.read().size()==1 and FileAccess.get_sha256(b+".moved")==b_hash and FileAccess.get_sha256(a)==a_hash,"Remove changes only the recent list, preserving project bytes")
	check(DirAccess.rename_absolute(b+".moved",b)==OK,"restore the owned missing-file fixture")
	app.home.new_button.pressed.emit();await settled()
	check(not app.home.visible and not app.dirty and app.renderer.world_runtime.instances.is_empty() and app.mode.selected==1 and app.world_selection.selected.is_empty(),"Home New opens a clean empty free-camera world")
	app.has_project.open_file(a);await wait_job(app)
	var staged:=folder.path_join("pending/recovery")
	check(Recovery.checkpoint(staged,"interrupted",app.video,app.keys,app.layers,app.source,12,app.audio_clip,a,123,app.renderer.model_state(),app.renderer.world_state()).is_empty(),"prepare a separate actual restart checkpoint without touching Home recents")
	var unit:=Recents.new();unit.file_path=folder.path_join("unit-recents.json");var paths: Array=[]
	for i in range(14):
		var path:=folder.path_join("unit_%02d.has" % i);paths.append(path);file=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(a));file.close();unit.remember(path,"",-1)
	check(unit.read().size()==12 and unit.read()[0].path.ends_with("unit_13.has") and unit.read()[-1].path.ends_with("unit_02.has"),"recent metadata has bounded twelve-entry retention")
	var normal_store=app.home.store;app.home.store=unit;app.home.open_home();await settled()
	check(app.home.find_children("RecentProject","Button",true,false).size()==12 and app.get_viewport_rect().encloses(app.home.panel.get_global_rect()),"all twelve valid projects stay in a bounded scrolling Home list")
	var last:=recent_button(app,paths[2]);var scroll: ScrollContainer=app.home.recent_list.get_parent();scroll.ensure_control_visible(last);await settled()
	check(scroll.get_global_rect().encloses(last.get_global_rect()),"the last recent project remains reachable without growing the Home panel")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("home-twelve.png"));last.pressed.emit();await wait_job(app)
	check(not app.home.visible and not app.dirty and app.frame==0 and Drawing.image(Drawing.cel_at(app.layers[1],0)).get_pixel(80,80)==Color.CYAN,"last-row project opens through real HAS validation with editable paint")
	app.home.store=normal_store;app.has_project.open_file(a);await wait_job(app)
	unit.remember(str(paths[-1]).to_upper(),"",-1);check(unit.read().size()==12,"Windows case differences do not create duplicate records")
	var previous:=FileAccess.get_sha256(unit.file_path);DirAccess.make_dir_recursive_absolute(unit.file_path+".tmp");check(not unit.remember(paths[0],"",-1) and FileAccess.get_sha256(unit.file_path)==previous,"failed preference write preserves the prior recent list");DirAccess.remove_absolute(unit.file_path+".tmp")
	file=FileAccess.open(unit.file_path,FileAccess.WRITE);file.store_string("{");file.close();check(unit.read().is_empty(),"malformed recent metadata is ignored quietly")
	file=FileAccess.open(unit.file_path,FileAccess.WRITE);file.store_string("x".repeat(65537));file.close();check(unit.read().is_empty(),"oversized recent metadata is refused before parsing")
	check(not Recents.valid_path("https://example.test/model.has") and not Recents.valid_path(a+".backup") and Recents.preview({"preview_folder":folder,"preview":"0".repeat(64)},app.recovery_root)==null,"recent paths and thumbnails cannot request URLs, backups or foreign preview folders")
	check(FileAccess.get_sha256(a)==a_hash and FileAccess.get_sha256(fixture)==fixture_hash,"Home actions preserve original manual project and geometry hashes")
	var expected:={"manual":a,"manual_sha256":a_hash,"fixture":fixture,"fixture_sha256":fixture_hash,"recents_sha256":FileAccess.get_sha256(app.recent_path),"rows":app.home.store.read().size()}
	file=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected));file.close()
	print("HOME_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"folder":folder}));app.free();quit(0 if failures==0 else 1)
