extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(240).timeout.connect(func():push_error("Particle editor watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS "if ok else"FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for n in range(5):await process_frame
	await RenderingServer.frame_post_draw
func click(control: Control) -> void:
	var viewport:=control.get_viewport();var point: Vector2=control.get_global_transform_with_canvas()*(control.size/2.)
	while viewport is Window and viewport.is_embedded():
		point+=Vector2(viewport.position);viewport=viewport.get_parent().get_viewport()
	var motion:=InputEventMouseMotion.new();motion.position=point;viewport.push_input(motion,true)
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=point;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;viewport.push_input(event,true);await process_frame
	await settled()
func wait_jobs() -> void:
	var deadline:=Time.get_ticks_msec()+70000
	while (app.source_browser.job_pid>0 or app.particle_editor.job_pid>0 or app.has_project.pid>0)and Time.get_ticks_msec()<deadline:await process_frame
	await settled()
func import_file(plan: Dictionary) -> void:
	var browser=app.source_browser;browser.open();await wait_jobs();browser.kind.select(3)
	var index:=-1
	for n in range(browser.source_rows.size()):
		if str(browser.source_rows[n].path).replace("\\","/")==str(plan.provider).replace("\\","/"):index=n
	check(index>=0,"actual installed browser discovers provider "+str(plan.system))
	if index<0:return
	browser.select_source(index);await wait_jobs();browser.filter_assets()
	var file_index:=-1
	for n in range(browser.filtered.size()):
		if browser.filtered[n].path==plan.member:file_index=n
	check(file_index>=0 and browser.filtered[file_index].kind=="particle","particle kind exposes real PCF file "+str(plan.system))
	if file_index<0:return
	browser.entries.select(file_index);browser.select_asset(file_index);await settled()
	print("IMPORT_BUTTON_STATE "+JSON.stringify({"rect":str(browser.import_button.get_global_rect()),"transform":str(browser.import_button.get_global_transform_with_canvas()),"viewport":str(browser.import_button.get_viewport().get_visible_rect()),"class":browser.import_button.get_viewport().get_class(),"disabled":browser.import_button.disabled,"selected":str(browser.entries.get_selected_items()),"job":browser.job_pid}))
	browser.import_button.button_down.connect(func():print("IMPORT_BUTTON_DOWN"),CONNECT_ONE_SHOT);browser.import_button.pressed.connect(func():print("IMPORT_BUTTON_PRESSED"),CONNECT_ONE_SHOT)
	browser.window.get_texture().get_image().save_png(OS.get_cmdline_user_args()[0].path_join("browser-before.png"))
	await click(browser.import_button);await wait_jobs()
	check(is_instance_valid(app.particle_editor.window) and not app.particle_editor.rows.is_empty(),"Import selected opens a modeless named-system chooser")
func choose_system(name: String) -> bool:
	var editor=app.particle_editor
	for n in range(editor.rows.size()):
		if editor.rows[n].name==name:editor.systems_list.select(n);editor.select_system(n);return true
	return false
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var plan=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=folder.path_join("has-cache");app.particle_editor.cache_root=folder.path_join("worker");app.particle_editor.import_root=ProjectSettings.globalize_path("res://output/imports/particle-editor-"+str(Time.get_ticks_usec()));app.particle_editor.dependency_root=plan.sourceio
	if OS.get_cmdline_user_args().size()>1:
		app.has_project.cache_root=folder.path_join("cold-cache");app.has_project.open_file(folder.path_join("packed.has"));await wait_jobs()
		check(app.renderer.world_runtime.effects.size()==2 and app.has_project.path==folder.path_join("packed.has"),"cold ordinary Open restores both browser-imported effects without original inputs")
		var picture: Image=await app.renderer.capture(app.keys,app.layers,13,true)
		check(picture.get_data()==Image.load_from_file(folder.path_join("reference.png")).get_data(),"cold browser scene repeats exact complete picture")
		app.particle_editor.open();app.particle_editor.select_id(app.current_world().effects[0].id);await settled()
		check(app.particle_editor.instances_list.item_count==2 and not app.particle_editor.seed.editable,"cold scene exposes editable instances and preserves prepared variation")
		check(app.particle_editor.window.get_visible_rect().encloses(app.particle_editor.apply_button.get_global_rect()) and app.particle_editor.window.get_visible_rect().encloses(app.particle_editor.remove_button.get_global_rect()),"reopened panel keeps full Apply and Remove buttons visible without scrolling")
		app.particle_editor.close();var previous_advanced: bool=app.advanced_mode;await click(app.advanced_toggle);check(app.advanced_mode!=previous_advanced,"closing effects leaves no freed Advanced controls")
		var result:={"checks":checks,"failures":failures};app.dirty=false;app.queue_free();await settled();var file:=FileAccess.open(folder.path_join("cold.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("PARTICLE_EDITOR "+JSON.stringify(result));quit(0 if failures==0 else 1);return
	var input:=folder.path_join("inputs");DirAccess.make_dir_recursive_absolute(input);var room:=input.path_join("room.glb");SceneIO.make_fixture(room);check(app.load_scene(room).is_empty(),"original procedural room joins ordinary world")
	app.keys=[Timeline.key(0,Vector3(0,1,7),Quaternion.IDENTITY,60)];app.mode.select(0);app.change_mode(0);app.create_cel(false)
	Drawing.stroke(Drawing.image(Drawing.cel_at(app.layers[1],0)),Vector2(72,72),Vector2(180,72),5,Color.CYAN,false);app.changed();app.set_frame(12)
	var ink: PackedByteArray=Drawing.image(Drawing.cel_at(app.layers[1],12)).get_data();var keys:=JSON.stringify(app.keys,"",true,true);var objects: Array=World.portable(app.current_world()).objects
	await import_file(plan.effects[0]);var editor=app.particle_editor
	if not is_instance_valid(editor.window):app.queue_free();await settled();quit(1);return
	check(not editor.window.exclusive,"effects panel keeps the main window clickable")
	app.video.duration_frames=24;await settled()
	check(editor.start.max_value==23 and editor.finish.value==23,"shorter shot clamps the open particle panel to its final frame")
	app.video.duration_frames=48;await settled()
	editor.finish.value=47
	check(editor.start.max_value==47 and editor.finish.value==47,"longer shot makes newly available frames editable without reopening the panel")
	await click(editor.name_edit);editor.name_edit.text="";editor.name_edit.caret_column=0
	var typing_tool: int=app.tool.selected
	for symbol in [[KEY_B,98],[KEY_SPACE,32],[KEY_E,101]]:
		for down in [true,false]:
			var key:=InputEventKey.new();key.keycode=symbol[0];key.physical_keycode=symbol[0];key.unicode=symbol[1];key.pressed=down;root.push_input(key,true);await process_frame
	await settled()
	check(editor.name_edit.text=="b e" and not app.playing and app.tool.selected==typing_tool,"actual embedded-window typing stays in the effect name without triggering main shortcuts")
	if app.playing:app.stop()
	var before_mode: bool=app.advanced_mode;await click(app.advanced_toggle);check(app.advanced_mode!=before_mode and editor.window.visible,"actual main-window Advanced button works while effects panel stays open");await click(app.advanced_toggle)
	var unavailable:=-1
	for n in range(editor.rows.size()):
		if not editor.rows[n].candidate:unavailable=n;break
	check(unavailable>=0,"real system list retains unavailable systems with reasons")
	if unavailable>=0:editor.select_system(unavailable);check(editor.prepare_button.disabled and not editor.notice.text.is_empty(),"unsupported whole systems disable loading and explain why")
	check(choose_system(plan.effects[0].system),"choose exact real SFM flash")
	editor.start.value=12;editor.finish.value=23
	for n in range(3):editor.coordinates[n].value=[-1.6,1.,1.][n]
	await click(editor.prepare_button);await wait_jobs();check(not editor.prepared.is_empty() and not editor.add_button.disabled,"real worker resolves native SFM material and enables explicit Add")
	var prior: int=app.history.size();await click(editor.add_button);check(app.renderer.world_runtime.effects.size()==1 and app.history.size()==prior+1,"actual Add button creates one canonical effect and one Undo action")
	if app.renderer.world_runtime.effects.is_empty():app.queue_free();await settled();quit(1);return
	var identity: String=editor.selected
	check("Frames 12–23" in editor.instances_list.get_item_text(0) and "Frames 12–23" in editor.notice.text and editor.frame_span({"start_frame":47,"end_frame":48})=="Frame 47","particle editor identifies the last included frame, including a one-frame effect")
	editor.start.value=47;editor.finish.value=47;await click(editor.apply_button)
	check(editor.selected_row().start_frame==47 and editor.selected_row().end_frame==48 and editor.instances_list.get_item_text(0).ends_with("Frame 47"),"equal first and last fields set one frame at the end of the shot")
	app.undo();await settled()
	check(editor.start.value==12 and editor.finish.value==23,"undo restores inclusive fields for the original effect")
	check(World.portable(app.current_world()).objects==objects and Drawing.image(Drawing.cel_at(app.layers[1],12)).get_data()==ink and JSON.stringify(app.keys,"",true,true)==keys,"adding effects preserves original room, independent ink and shot keys")
	app.world_selection.select_entity("effect:"+identity);check(editor.selected==identity,"World effect entry reopens exact shared instance controls")
	var history_before: int=app.history.size()
	var runtime_before=app.renderer.world_runtime
	await click(editor.apply_button)
	check(app.history.size()==history_before and app.renderer.world_runtime==runtime_before and "already applied" in editor.notice.text,"applying untouched fields leaves Undo and the running world intact")
	editor.finish.value=11;await click(editor.apply_button)
	check("Last frame must be at least 12" in editor.notice.text and editor.selected_row().end_frame==24 and app.history.size()==history_before and app.renderer.world_runtime==runtime_before,"reversed range reports the first valid end without replacing the scene or creating Undo")
	editor.finish.value=23
	var before: Dictionary=editor.selected_row();editor.coordinates[0].value+=.25;editor.size_value.value=.75;editor.visible.button_pressed=false;editor.name_edit.text="Flash edit";var expected_x: float=editor.coordinates[0].value;await click(editor.apply_button)
	print("APPLIED_EFFECT "+JSON.stringify(editor.selected_row()))
	check(editor.selected_row().position[0]==expected_x and not editor.selected_row().visible and editor.selected_row().scale==.75 and editor.selected_row().name=="Flash edit","actual Apply updates standard placement, size, visibility and name")
	app.undo();await settled();check(editor.selected_row()==before and editor.coordinates[0].value==before.position[0] and editor.visible.button_pressed,"Undo restores canonical state and refreshes its visible fields")
	var precise: Dictionary=before.duplicate(true);precise.position=[.123456789123,.234567891234,.345678912345];precise.scale=.0014;editor.load_instance_fields(precise)
	var unchanged: Dictionary=editor.read_fields(precise.duplicate(true));check(unchanged.position==precise.position and unchanged.scale==precise.scale and unchanged.sha256==precise.sha256,"untouched fields preserve stored precision and tiny valid scale despite Simple display rounding");editor.load_instance_fields(before)
	await click(editor.remove_button);check(app.current_world().format==World.FORMAT and app.renderer.world_runtime.effects.is_empty(),"removing last effect restores ordinary world format")
	app.undo();await settled();check(app.renderer.world_runtime.effects.size()==1,"Undo Remove restores exact effect")
	await import_file(plan.effects[1]);check(choose_system(plan.effects[1].system),"choose exact real Workshop glow");editor.start.value=0;editor.finish.value=47
	for n in range(3):editor.coordinates[n].value=[1.5,1.,1.][n]
	await click(editor.prepare_button);await wait_jobs();check(not editor.prepared.is_empty(),"real Workshop GMA effect prepares through common worker");await click(editor.add_button);check(app.renderer.world_runtime.effects.size()==2,"second native family uses same canonical scene instances")
	editor.close();app.set_frame(13);var expected: Image=await app.renderer.capture(app.keys,app.layers,13,true);expected.save_png(folder.path_join("reference.png"))
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await wait_jobs();check(app.has_project.path==linked,"ordinary linked save includes UI-imported effect data")
	var packed:=folder.path_join("packed.has");app.has_project.save_file(packed,"packed");await wait_jobs();check(app.has_project.path==packed,"ordinary packed save includes UI-imported effect data")
	app.new_project();app.has_project.open_file(packed);await wait_jobs();var reopened: Image=await app.renderer.capture(app.keys,app.layers,13,true)
	check(app.renderer.world_runtime.effects.size()==2 and expected.get_data()==reopened.get_data(),"normal packed Open preserves imported effects and exact complete picture")
	app.particle_editor.open();app.particle_editor.select_id(app.current_world().effects[0].id);await settled();app.particle_editor.window.get_texture().get_image().save_png(folder.path_join("effects-panel.png"));app.particle_editor.close()
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000014.png")).get_data()==expected.get_data(),"ordinary MP4 export matches UI-imported particle preview")
	var result: Dictionary={"checks":checks,"failures":failures,"folder":folder,"packed":packed,"linked":linked,"movie":app.last_export_folder.path_join("movie.mp4"),"import_root":editor.import_root}
	app.dirty=false;app.queue_free();await settled();var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("PARTICLE_EDITOR "+JSON.stringify(result));quit(0 if failures==0 else 1)
