extends SceneTree
const Bindings=preload("res://src/shortcut_bindings.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Shortcut editor watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func press(code: int,ctrl:=false,shift:=false,alt:=false,window: Window=null) -> void:
	for down in [true,false]:
		var event:=InputEventKey.new();event.keycode=code;event.pressed=down;event.ctrl_pressed=ctrl;event.shift_pressed=shift;event.alt_pressed=alt
		if window:event.window_id=window.get_window_id();Input.parse_input_event(event)
		else:root.push_input(event)
func click(control: Control) -> void:
	var window: Window=control.get_window()
	var position:=control.get_global_rect().get_center()
	if window.is_embedded():position+=Vector2(window.position)
	var target: Window=root if window.is_embedded() else window
	var motion:=InputEventMouseMotion.new();motion.position=position;target.push_input(motion,true)
	for down in [true,false]:
		var e:=InputEventMouseButton.new();e.position=position;e.button_index=MOUSE_BUTTON_LEFT;e.pressed=down;target.push_input(e,true);await process_frame
	await settle()
func release_focus() -> void:
	var focus:=root.gui_get_focus_owner()
	if focus:focus.release_focus()
func wait_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reading: bool="--read" in args;var invalid: bool="--invalid" in args
	if invalid:
		var bad:=ConfigFile.new();var values: Dictionary=Bindings.DEFAULTS.duplicate();values.pen=KEY_E;bad.set_value("shortcuts","version",1);bad.set_value("shortcuts","keys",values);bad.save(folder.path_join("invalid.cfg"))
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("invalid.cfg" if invalid else "personal.cfg");app.recovery_root=folder.path_join("recovery-reader" if reading or invalid else "recovery");app.recent_path=folder.path_join("recent-reader.json" if reading or invalid else "recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-reader" if reading or invalid else "cache")
	var editor=app.keyboard_shortcuts
	if invalid:
		var original:=FileAccess.get_sha256(app.display_prefs_path)
		check(editor.bindings==Bindings.DEFAULTS and not editor.load_error.is_empty(),"conflicting saved profile falls back to complete defaults with explanation")
		editor.open();await settle();check("using defaults" in editor.info.text,"keyboard panel explains invalid saved preferences")
		check(FileAccess.get_sha256(app.display_prefs_path)==original,"fallback does not overwrite invalid or unrelated preference data")
		print("SHORTCUT_EDITOR_INVALID ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	if reading:
		check(editor.bindings.play==KEY_P and editor.bindings.next==KEY_F6 and editor.bindings.camera==(KEY_MASK_CTRL|KEY_J),"fresh process restores custom personal keys")
		app.set_frame(8);release_focus();press(KEY_RIGHT);check(app.frame==8,"old next-frame binding stays inactive after restart");press(KEY_F6);check(app.frame==9,"restored next-frame key dispatches")
		var prefs:=ConfigFile.new();prefs.load(app.display_prefs_path);check(prefs.get_value("unrelated","keep")=="original" and prefs.get_value("display","percent")==100,"keyboard save retains unrelated display preferences")
		var before: Dictionary=editor.bindings.duplicate();app.has_project.open_file(folder.path_join("Keyboard scene.has"));await wait_job();check(editor.bindings==before,"HAS Open does not replace personal keys")
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.pixels and Storage.image_hash(await app.renderer.capture(app.keys,app.layers,0,true))==expected.render,"cold saved project retains independent pixels and authored camera output")
		print("SHORTCUT_EDITOR_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(editor.bindings==Bindings.DEFAULTS,"fresh user has all existing default shortcuts")
	check(app.load_demo_room(),"original independent3D camera example loads")
	app.mode.select(0);app.change_mode(0);app.set_frame(0)
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(800,400,120,100),Color.CYAN);Drawing.insert(app.layers[1],0,48,image);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var pixels:=Storage.image_hash(image);var keys: Array=app.keys.duplicate(true);var source:=FileAccess.get_sha256(app.source);var history: int=app.history.size();var dirty: bool=app.dirty;var revision: int=app.recovery_revision
	var prefs:=ConfigFile.new();prefs.set_value("unrelated","keep","original");prefs.set_value("display","percent",100);prefs.save(app.display_prefs_path)
	root.size=Vector2i(1200,760);app.set_advanced(false);app.show_display_settings();await settle()
	var settings_box: VBoxContainer
	for child in app.display_dialog.get_children():
		if child is VBoxContainer:settings_box=child
	var entry: Button
	for child in settings_box.get_children():
		if child is Button and child.text=="Keyboard shortcuts…":entry=child
	check(entry!=null and entry.is_visible_in_tree(),"Simple Settings exposes keyboard preferences")
	await click(entry);check(editor.dialog!=null and editor.dialog.visible and not editor.dialog.exclusive,"actual Settings click opens nonexclusive shortcut panel")
	if not editor.dialog or not editor.dialog.visible:
		print("SHORTCUT_CLICK_STATE ",entry.get_global_rect()," window ",entry.get_window().position," embedded ",entry.get_window().is_embedded()," visible ",entry.get_window().visible)
		root.get_texture().get_image().save_png(folder.path_join("click-failure.png"));app.free();quit(1);return
	await click(editor.rows.play);check(editor.pending=="play","actual row click arms key capture")
	press(KEY_P,false,false,false,editor.dialog);await settle();check(editor.bindings.play==KEY_P and editor.pending.is_empty() and not app.playing,"dialog receives native-window key and saves without playing")
	await click(editor.rows.next);press(KEY_P,false,false,false,editor.dialog);await settle();check(editor.bindings.next==KEY_RIGHT and editor.pending=="next" and "already uses" in editor.info.text,"duplicate assignment refuses without silently unbinding another action")
	press(KEY_ESCAPE,false,false,false,editor.dialog);await settle();check(editor.pending.is_empty() and editor.dialog.visible and editor.bindings.next==KEY_RIGHT,"Escape cancels capture without changing or closing keyboard panel")
	await click(editor.rows.next);press(KEY_F6,false,false,false,editor.dialog);await settle();check(editor.bindings.next==KEY_F6,"function key remap is saved from actual capture")
	var scroll: ScrollContainer=editor.rows.camera.get_parent().get_parent().get_parent();scroll.ensure_control_visible(editor.rows.camera);await settle();await click(editor.rows.camera);press(KEY_J,true,false,false,editor.dialog);await settle()
	check(editor.bindings.camera==(KEY_MASK_CTRL|KEY_J) and scroll.get_global_rect().encloses(editor.rows.camera.get_parent().get_global_rect()),"last shortcut row is fully scroll-accessible and Ctrl-key capture works")
	editor.begin_capture("pen");press(KEY_R,false,false,true,editor.dialog);await settle();check(editor.bindings.pen==KEY_B and not editor.pending.is_empty(),"Alt shortcut refuses and preserves bone reveal modifier");editor.cancel_capture()
	editor.begin_capture("pen");app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT);check(editor.pending.is_empty(),"main window focus loss cancels unfinished key capture")
	editor.begin_capture("pen");editor.dialog.hide();await settle();check(editor.pending.is_empty(),"hiding dialog cancels unfinished capture")
	app.display_dialog.hide();release_focus();app.set_frame(8);press(KEY_RIGHT);check(app.frame==8,"replaced default key does not dispatch");press(KEY_F6);check(app.frame==9,"custom key dispatches exactly once")
	press(KEY_F6,false,true);check(app.frame==9,"extra modifier does not dispatch a plain binding")
	app.frame_box.get_line_edit().grab_focus();press(KEY_F6);check(app.frame==9,"focused numeric text input blocks custom global shortcut");release_focus()
	press(KEY_P);check(app.playing,"remapped play starts preview");press(KEY_P);check(not app.playing,"remapped play pauses preview");press(KEY_SPACE);check(not app.playing,"old Space no longer toggles after reassignment")
	app.navigating=true;press(KEY_F6);check(app.frame==9,"camera navigation blocks remapped editor commands");app.release_mouse()
	app.exporting=true;press(KEY_F6);check(app.frame==9,"export blocks remapped commands");app.exporting=false
	app.mode.select(1);app.change_mode(1);check(editor.assign("camera",KEY_MASK_CTRL|KEY_J).is_empty(),"camera key shortcut can be reassigned")
	app.set_frame(12);app.renderer.camera.position+=Vector3(.2,0,0);release_focus();press(KEY_K);check(app.keys==keys,"old camera binding cannot author a key");press(KEY_J,true);check(app.keys.size()==keys.size()+1 and app.history.size()==history+1,"new camera binding explicitly authors one current-frame key")
	press(KEY_Z,true);check(app.keys==keys,"default Undo still restores the camera in one step");press(KEY_Z,true,true);check(app.keys.size()==keys.size()+1,"default alternate Redo remains available");press(KEY_Z,true)
	app.mode.select(0);app.change_mode(0);app.set_frame(0);check(editor.assign("pen",KEY_G).is_empty(),"drawing tool key is reassigned");app.tool.select(1);release_focus();press(KEY_B);check(app.tool.selected==1,"old pen binding no longer selects tool");press(KEY_G);check(app.tool.selected==0 and "G" in app.tool.get_item_text(0),"new pen key selects tool and updates its displayed hint")
	editor.open();await settle();scroll.ensure_control_visible(editor.rows.pen);await settle();await click(editor.rows.pen.get_parent().get_child(2));editor.dialog.hide();release_focus()
	check(editor.bindings.pen==0,"actual Clear button unassigns a tool key");app.tool.select(1);press(KEY_G);check(app.tool.selected==1,"cleared shortcut stops dispatching")
	var before: Dictionary=editor.bindings.duplicate();var original_path: String=app.display_prefs_path;app.display_prefs_path=folder.path_join("missing-parent/prefs.cfg");var problem: String=editor.assign("pen",KEY_G);app.display_prefs_path=original_path
	check(not problem.is_empty() and editor.bindings==before,"failed preference write preserves active bindings")
	editor.open();await settle();var restore: Button=editor.info.get_parent().get_child(editor.info.get_index()+1);await click(restore);editor.dialog.hide();release_focus();check(editor.bindings==Bindings.DEFAULTS and app.tool.get_item_text(0)=="Pen [B]","actual restore defaults button updates dispatch and visible hints")
	check(editor.assign("play",KEY_P).is_empty() and editor.assign("next",KEY_F6).is_empty() and editor.assign("camera",KEY_MASK_CTRL|KEY_J).is_empty(),"custom profile prepared for fresh-process verification")
	check(app.keys==keys and Storage.image_hash(image)==pixels and FileAccess.get_sha256(app.source)==source,"keyboard edits do not modify camera/drawing/source assets")
	# Undo/Redo above are real authored edits; profile-only changes must not add history.
	var isolated_history: int=app.history.size();var isolated_revision: int=app.recovery_revision;var isolated_dirty: bool=app.dirty
	editor.open();await settle();await click(editor.rows.play);press(KEY_ESCAPE,false,false,false,editor.dialog);await settle()
	check(app.history.size()==isolated_history and app.recovery_revision==isolated_revision and app.dirty==isolated_dirty,"opening/cancelling preferences leaves scene dirty/history/recovery state untouched")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("shortcuts-1200.png"));press(KEY_ESCAPE,false,false,false,editor.dialog);await settle();check(not editor.dialog.visible,"Escape closes idle keyboard panel");app.display_dialog.hide();app.set_frame(0)
	var rendered: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var packed:=folder.path_join("Keyboard scene.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"ordinary HAS save works with custom personal keys")
	check(editor.assign("save",KEY_F7).is_empty(),"Save project key can be remapped")
	app.changed();release_focus();press(KEY_F7);await wait_job();check(not app.dirty and app.has_project.path==packed,"custom Save key invokes ordinary durable save at existing HAS path")
	var personal: Dictionary=editor.bindings.duplicate();app.new_project();check(editor.bindings==personal,"New scene retains personal shortcut preferences")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pixels":pixels,"render":Storage.image_hash(rendered)}))
	var result:={"checks":checks,"failures":failures};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHORTCUT_EDITOR_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
