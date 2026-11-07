extends "res://tests/fill_expand_smoke.gd"
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Fill connections watchdog");quit(2));call_deferred("run")
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var packed:=folder.path_join("Corner colors.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed);await job()
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.flats and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[2],0)))==expected.ink,"cold Open restores both corner-connected color areas and exact original ink")
		check(app.fill_editor.connectivity_choice.get_selected_id()==4 and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"connection choice is session-only; standard world and camera keys persist")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,"cold render equals movie input and manual HAS remains untouched")
		print("FILL_CONNECTIONS_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard3D environment coexists with fill")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)];app.mode.select(0);app.change_mode(0);app.set_frame(0)
	var ink:=Drawing.blank(1920,1080);ink.fill_rect(Rect2i(680,330,260,240),Color.BLACK);ink.fill_rect(Rect2i(700,350,100,100),Color.TRANSPARENT);ink.fill_rect(Rect2i(800,450,100,100),Color.TRANSPARENT)
	app.layers[1].cels.clear();Drawing.insert(app.layers[1],0,48,ink);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var ink_hash:=Storage.image_hash(ink);var keys: Array=app.keys.duplicate(true);var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	app.tool.select(2);app.fill_editor.refresh();button("Color layer below",app.fill_editor.panel).pressed.emit();app.color.color=Color.CYAN;app.canvas.zoom=1.2;app.canvas.pan=Vector2(17,-9);root.size=Vector2i(1200,760);app.set_advanced(false);await settle()
	var choice: OptionButton=app.fill_editor.connectivity_choice
	check(choice.get_selected_id()==4 and not choice.is_visible_in_tree(),"Simple defaults to edges only without exposing specific connection controls")
	click(Vector2(750,400));await wait_fill();var cel:=Drawing.cel_at(app.layers[1],0);var four:=Storage.image_hash(Drawing.image(cel))
	check(app.fill_editor.last_result.connectivity==4 and app.fill_editor.last_result.region==10000 and Drawing.image(cel).get_pixel(750,400)==Color.CYAN and Drawing.image(cel).get_pixel(850,500).a==0,"actual default fill colors only the clicked compartment")
	app.undo();check(Drawing.cel_at(app.layers[1],0).is_empty(),"default fill has one complete cel Undo");app.redo();check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==four,"default cel Redo is byte exact");app.undo()
	app.set_advanced(true);await settle();app.inspector_scroll.ensure_control_visible(choice);await settle()
	check(app.inspector_scroll.get_global_rect().encloses(choice.get_global_rect()),"complete connection dropdown is visible after Advanced layout")
	await click_control(choice)
	var menu:=choice.get_popup();check(menu.visible,"connection dropdown opens from an actual click")
	if not menu.visible:
		root.get_texture().get_image().save_png(folder.path_join("dropdown-failure.png"));print("DROPDOWN_STATE ",choice.get_global_rect()," scroll ",app.inspector_scroll.get_global_rect());app.free();quit(1);return
	menu.set_focused_item(1)
	for pressed in [true,false]:
		# A PopupMenu handles window events before Viewport.push_input. Dispatch
		# through Input with the popup's actual window identity, as the OS does.
		var key:=InputEventKey.new();key.window_id=menu.get_window_id();key.keycode=KEY_ENTER;key.pressed=pressed;Input.parse_input_event(key)
	await settle()
	check(choice.is_visible_in_tree() and choice.get_selected_id()==8 and not menu.visible,"dropdown keyboard selection chooses Edges and corners")
	if choice.get_selected_id()!=8:
		root.get_texture().get_image().save_png(folder.path_join("dropdown-keyboard-failure.png"));app.free();quit(1);return
	var history: int=app.history.size();click(Vector2(750,400));await wait_fill();cel=Drawing.cel_at(app.layers[1],0);var flats: Image=Drawing.image(cel);var first:=Storage.image_hash(flats);var worker_ms: float=app.fill_editor.last_result.worker_ms
	check(app.fill_editor.last_result.connectivity==8 and app.fill_editor.last_result.region==20000 and flats.get_pixel(750,400)==Color.CYAN and flats.get_pixel(850,500)==Color.CYAN and app.fill_editor.pending.is_empty(),"zoomed corner-connected fill joins both enclosed compartments")
	check(app.history.size()==history+1 and Storage.image_hash(ink)==ink_hash and flats.get_pixel(800,449).a==0,"only Flats changes; separating ink pixels remain untouched")
	app.undo();check(Drawing.cel_at(app.layers[1],0).is_empty(),"corner fill has one cel Undo");app.redo();flats=Drawing.image(Drawing.cel_at(app.layers[1],0));check(Storage.image_hash(flats)==first,"corner fill Redo restores both areas exactly")
	app.color.color=Color(1,0,0,0.5);click(Vector2(750,400));await wait_fill();var second:=Storage.image_hash(flats)
	check(app.history[-1].type=="pixels" and app.history[-1].bytes<1024*1024 and flats.get_pixel(750,400).to_html()=="ff000080" and flats.get_pixel(850,500).to_html()=="ff000080","corner recolor uses exact RGBA and bounded tile history")
	app.undo();check(Storage.image_hash(flats)==first,"tile Undo restores both corner-connected colors");app.redo();check(Storage.image_hash(flats)==second,"tile Redo restores both alpha colors")
	app.color.color=Color.GREEN;app.fill_editor.expand_edges.value=1;click(Vector2(750,400));await wait_fill()
	check(not app.fill_editor.pending.is_empty() and app.fill_editor.last_result.region==20000 and app.fill_editor.last_result.expanded_pixels>0,"corner mode composes with previewed under-line growth")
	var viewport: Rect2=app.inspector_scroll.get_global_rect();check(viewport.encloses(button("Apply fill",app.fill_editor.preview_row).get_global_rect()) and viewport.encloses(button("Cancel",app.fill_editor.preview_row).get_global_rect()),"complete preview buttons remain reachable at1200pixels with the new setting")
	root.get_texture().get_image().save_png(folder.path_join("connections-preview-1200.png"));var before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	await click_control(button("Cancel",app.fill_editor.preview_row));var cancelled: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(before.get_data()==cancelled.get_data() and Storage.image_hash(flats)==second,"candidate preview remains outside the final renderer and Cancel changes no artwork")
	click(Vector2(750,400));await wait_fill();choice.select(0);app.fill_editor.apply_pending()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"connection change rejects an immediate stale Apply")
	choice.select(1);click(Vector2(750,400));choice.select(0);await wait_fill()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"connection change during work discards the old candidate")
	choice.select(1);app.fill_editor.expand_edges.value=0
	check(background_frames>3 and app.fill_editor.last_result.background_thread,"corner traversal runs over detached worker bytes while UI frames continue")
	check(Storage.image_hash(ink)==ink_hash and equal(keys,app.keys) and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"corner fills preserve original ink, common world, camera/view and source geometry")
	app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed);var linked:=folder.path_join("Corner colors linked.has");app.has_project.save_file(linked,"linked");await job();app.has_project.open_file(linked);await job()
	check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==second and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[2],0)))==ink_hash,"linked HAS preserves corner-connected color and separate source ink")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.open_project(app.recovery_root.path_join(app.recovery_session)) and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==second and FileAccess.get_sha256(packed)==manual,"recovery preserves exact colors without changing the manual save")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"ordinary MP4 frame exactly matches both colored areas over animated3D")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var expected:={"flats":second,"ink":ink_hash,"keys":keys,"world":world,"render":Storage.image_hash(reference),"project_hash":manual};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	# Deliberately replace only the test fixture after persistence checks: a
	# one-pixel diagonal opening must retain the existing spill protection.
	app.mode.select(0);app.change_mode(0);app.tool.select(2);choice.select(1);app.fill_editor.expand_edges.value=0;app.layers[1].cels.clear();var spill_ink: Image=Drawing.image(Drawing.cel_at(app.layers[2],0))
	for i in range(1,23):spill_ink.set_pixel(700-i,350-i,Color.TRANSPARENT)
	Drawing.touch(spill_ink);app.changed();var spill_hash:=Storage.image_hash(spill_ink);click(Vector2(750,400));await wait_fill()
	check(not app.fill_editor.pending.is_empty() and app.fill_editor.last_result.edge and Drawing.cel_at(app.layers[1],0).is_empty() and Storage.image_hash(spill_ink)==spill_hash,"a diagonal escape to the canvas edge previews instead of filling the canvas automatically")
	app.fill_editor.cancel();click(Vector2(40,40));var started:=Time.get_ticks_msec();app.new_project();var new_ms:=Time.get_ticks_msec()-started;await wait_fill()
	check(app.layers.size()==2 and Drawing.cel_at(app.layers[1],0).is_empty() and app.fill_editor.pending.is_empty(),"New safely discards a detached eight-connected worker result")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie,"worker_ms":worker_ms,"background_frames":background_frames,"new_during_worker_ms":new_ms};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("FILL_CONNECTIONS_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
