extends "res://tests/drawing_selection_smoke.gd"
const Transform=preload("res://src/drawing_transform.gd")
var worker_frames:=0
func _initialize() -> void:
	create_timer(210).timeout.connect(func():push_error("Drawing transform watchdog");quit(2));call_deferred("run")
func wait_transform() -> void:
	while app.drawing_selection_editor.transforms.busy():worker_frames+=1;await process_frame
	await settle()
func type_number(spin: SpinBox,value: String) -> void:
	var edit:=spin.get_line_edit();app.inspector_scroll.ensure_control_visible(edit);await settle();await click_control(edit)
	for pressed in [true,false]:
		var key:=InputEventKey.new();key.keycode=KEY_A;key.ctrl_pressed=true;key.pressed=pressed;root.push_input(key,true)
	for character in value:
		for pressed in [true,false]:
			var key:=InputEventKey.new();key.keycode=character.unicode_at(0);key.unicode=character.unicode_at(0);key.pressed=pressed;root.push_input(key,true)
	await settle();check(edit.text==value,"actual numeric keyboard input reaches the focused field: "+value)
	if edit.text!=value:print("TYPING_STATE ",JSON.stringify({"text":edit.text,"expected":value,"focused":edit.has_focus(),"editing":edit.is_editing(),"editable":edit.editable,"visible":edit.is_visible_in_tree()}))
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var packed:=folder.path_join("Rotated drawing.has")
	if "--typing-probe" in args:
		Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));app.changed();app.mode.select(0);app.change_mode(0);app.drawing_selection_editor.arm();root.size=Vector2i(1200,760);app.set_advanced(false);await settle();marquee(Vector2(700,400),Vector2(800,500));var probe: Node=app.drawing_selection_editor.transforms;probe.open();await settle();await type_number(probe.size,"150");await type_number(probe.angle,"-14");probe.flush();check(probe.size.value==150 and probe.angle.value==-14,"only actually typed numeric fields flush to their intended values");print("DRAWING_TRANSFORM_TYPING ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed);await job()
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],12)))==expected.pixels and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[0],12)))==expected.other,"cold Open restores exact transformed raster and independent other drawing")
		check(app.drawing_selection_editor.context.is_empty() and app.canvas.selection_preview==null and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"transient transform is absent while common world/camera stay exact")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,"cold preview equals movie input and leaves saved HAS untouched")
		print("DRAWING_TRANSFORM_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard3D environment is installed")
	var asset:=folder.path_join("limb.glb");check(Limb.create(asset)==OK,"validated original limb fixture is created");var doc: Dictionary=app.current_world().duplicate(true);var actor:=World.object(asset,"model","Practice arm");doc.objects.append(actor);check(app.restore_world(doc).is_empty(),"poseable standard model coexists with drawing transforms")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)];app.set_frame(12)
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(700,400,120,80),Color.CYAN);image.fill_rect(Rect2i(720,420,40,20),Color(1,0,0,0.5));Drawing.insert(app.layers[1],0,48,image);app.layers[1].opacity=.5
	var other:=Drawing.blank(1920,1080);other.fill_rect(Rect2i(680,380,180,140),Color.YELLOW);Drawing.insert(app.layers[0],0,48,other);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	app.world_selection.select_entity(actor.id);app.physics_editor.enable_body(app.renderer.active_model());app.mode.select(0);app.change_mode(0);app.drawing_selection_editor.arm();app.canvas.zoom=1.2;app.canvas.pan=Vector2(17,-9);root.size=Vector2i(1200,760);app.set_advanced(false);await settle()
	var editor: Node=app.drawing_selection_editor;var tx: Node=editor.transforms;var simulation=app.physics_editor.simulations.get(actor.id);var generation: int=app.physics_editor.generation
	var original:=image.get_data();var other_hash:=Storage.image_hash(other);var world: Dictionary=World.portable(app.current_world());var keys: Array=app.keys.duplicate(true);var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	marquee(Vector2(690,390),Vector2(830,490));await settle()
	check(not tx.launch.disabled and app.inspector_scroll.get_global_rect().encloses(tx.launch.get_global_rect()),"Simple Resize/rotate action is reachable for a real selection")
	await click_control(tx.launch);await settle();check(tx.controls.is_visible_in_tree() and tx.size.is_visible_in_tree() and tx.angle.is_visible_in_tree() and not tx.independent.is_visible_in_tree(),"Simple opens only the basic size and angle controls")
	await type_number(tx.size,"150");tx.angle.value=27;await click_control(tx.preview_button);await wait_transform()
	check(not tx.pending.is_empty() and tx.last_result.background_thread and tx.size.value==150,"actual Preview flushes typed size and resamples on a detached worker")
	if tx.pending.is_empty():app.free();quit(1);return
	var pixels: PackedByteArray=tx.pending.data;var bounds: Rect2i=tx.pending.selection;var worker_ms: float=tx.last_result.worker_ms
	check(image.get_data()==original and app.history.is_empty() and app.canvas.selection_preview!=null,"free-angle preview changes neither source bytes nor history")
	var alpha_ok:=false;var preview: Image=app.canvas.selection_preview.get_image()
	for y in range(bounds.position.y,bounds.end.y):
		for x in range(bounds.position.x,bounds.end.x):
			if pixels[(y*1920+x)*4+3]==255 and other.get_pixel(x,y).a==0:alpha_ok=preview.get_pixel(x,y).a8==128;break
		if alpha_ok:break
	check(alpha_ok,"transformed raw alpha stays independent of50percent layer opacity")
	var viewport: Rect2=app.inspector_scroll.get_global_rect();check(viewport.encloses(tx.apply_button.get_global_rect()) and viewport.encloses(button("Cancel",tx.preview_row).get_global_rect()),"whole Apply and Cancel actions fit the1200pixel Properties panel")
	root.get_texture().get_image().save_png(folder.path_join("transform-preview-1200.png"));await click_control(tx.apply_button)
	check(image.get_data()==pixels and app.history.size()==1 and app.history[-1].type=="pixels" and app.history[-1].bytes<2*1024*1024 and editor.selected==bounds,"actual Apply commits exact rotated/scaled pixels with one bounded tile Undo")
	check(app.physics_editor.is_running() and is_same(simulation,app.physics_editor.simulations.get(actor.id)) and app.physics_editor.generation==generation,"preparing/applying transforms preserves live physics identity/generation")
	app.undo();check(image.get_data()==original and app.physics_editor.is_running(),"Undo restores original RGBA without stopping physics");app.redo();check(image.get_data()==pixels,"Redo restores exact transformed raster")
	marquee(Vector2(bounds.position),Vector2(bounds.end));tx.open();tx.size.value=100;tx.angle.value=0;tx.start();await wait_transform();var count: int=app.history.size();tx.apply_pending();check(app.history.size()==count and image.get_data()==pixels,"identity transform is a no-op without opacity buildup")
	app.set_advanced(true);tx.open();tx.independent.button_pressed=true;tx.width_scale.value=75;tx.height_scale.value=125;tx.angle.value=-15;tx.keep_original.button_pressed=true;var settings: Dictionary=tx.settings();app.set_advanced(false);await settle()
	check(tx.settings()==settings and not tx.size.editable and tx.scale_hint.is_visible_in_tree(),"Simple/Advanced switching preserves independent scales and keep-original settings")
	tx.start();await wait_transform();check(not tx.pending.is_empty() and image.get_data()==pixels,"independent stretch/rotation/copy produces a guarded preview without source edits")
	await type_number(tx.angle,"-14");tx.apply_pending();check(tx.pending.is_empty() and image.get_data()==pixels and app.history.size()==count,"typing a new angle rejects the stale candidate before Apply")
	tx.start();tx.width_scale.value=76;await wait_transform();check(tx.pending.is_empty() and image.get_data()==pixels,"parameter change while worker runs discards its old result")
	tx.start();app.tool.select(0);app.color.color=Color.MAGENTA;app.brush_pressure.button_pressed=false;mouse(Vector2(950,800),true);move(Vector2(980,800));mouse(Vector2(980,800),false);var painted:=image.get_data();await wait_transform()
	check(painted!=pixels and image.get_data()==painted and tx.pending.is_empty(),"real intervening brush editing cancels a transform and cannot be overwritten by its worker")
	app.undo();check(image.get_data()==pixels,"intervening brush Undo returns to exact transformed pixels")
	editor.arm();marquee(Vector2(bounds.position),Vector2(bounds.end));tx.open();tx.independent.button_pressed=false;tx.keep_original.button_pressed=false;tx.size.value=110;tx.angle.value=17;tx.start();await settle();await click_control(button("Cancel",tx.preview_row));await wait_transform();check(tx.pending.is_empty() and image.get_data()==pixels,"actual Cancel works during preparation or preview without changing pixels")
	tx.start();await wait_transform();var key:=InputEventKey.new();key.keycode=KEY_ESCAPE;key.pressed=true;tx.angle.get_line_edit().grab_focus();app._input(key);check(tx.pending.is_empty() and editor.selected.has_area() and image.get_data()==pixels,"Escape cancels a transform preview even with numeric text focus")
	app.canvas.grab_focus();app.canvas.zoom=.7;marquee(Vector2(10,10),Vector2(1910,1070));tx.open();tx.size.value=400;tx.angle.value=45;tx.start();await wait_transform();check(tx.pending.is_empty() and tx.last_result.has("error") and "larger than the frame" in app.status.text and image.get_data()==pixels,"oversized transform refuses in the app without cutting source pixels")
	marquee(Vector2(0,300),Vector2(900,600));tx.open();tx.size.value=120;tx.angle.value=25;tx.start();await wait_transform();check(not tx.pending.is_empty() and tx.pending.repositioned and Rect2i(0,0,1920,1080).encloses(tx.pending.selection) and image.get_data()==pixels,"near-edge visible artwork previews wholly inside the frame without cropping")
	check(tx.last_result.background_thread and tx.last_result.ui_frames>2,"large resampling preparation advances actual UI frames throughout its worker lifetime")
	tx.invalidate();check(Storage.image_hash(other)==other_hash and equal(world,World.portable(app.current_world())) and equal(keys,app.keys) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"all transform operations preserve other layer, world, camera/view and original source geometry")
	app.physics_editor.clear();check(app.restore_world(doc).is_empty(),"authored world is restored for deterministic persistence/movie checks");world=World.portable(app.current_world())
	editor.arm();marquee(Vector2(bounds.position),Vector2(bounds.end));tx.open();tx.size.value=110;tx.angle.value=17;tx.start();await wait_transform();var reference: Image=await app.renderer.capture(app.keys,app.layers,12,true);tx.invalidate();var cancelled: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	check(reference.get_data()==cancelled.get_data() and image.get_data()==pixels,"unapplied transform candidate/bounds never enter the final renderer")
	app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed);var linked:=folder.path_join("Rotated drawing linked.has");app.has_project.save_file(linked,"linked");await job();app.has_project.open_file(linked);await job();check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],12)))==Storage.image_hash(image) and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[0],12)))==other_hash,"linked HAS preserves exact transformed pixels and independent drawing")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.open_project(app.recovery_root.path_join(app.recovery_session)) and Drawing.cel_at(app.layers[1],0).id==Drawing.cel_at(app.layers[1],47).id and FileAccess.get_sha256(packed)==manual,"recovery retains held transformed cel without altering manual packed save")
	app.set_frame(12);reference=await app.renderer.capture(app.keys,app.layers,12,true);editor.arm();marquee(Vector2(bounds.position),Vector2(bounds.end));tx.open();tx.size.value=110;tx.angle.value=17;tx.start();await wait_transform();var error: String=await app.export_movie(folder)
	check(error.is_empty() and tx.pending.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==reference.get_data(),"export cancels an uncommitted transform and movie PNG equals committed artwork")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var expected:={"pixels":Storage.image_hash(image),"other":other_hash,"keys":keys,"world":world,"render":Storage.image_hash(reference),"project_hash":manual};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	editor.arm();marquee(Vector2(bounds.position),Vector2(bounds.end));tx.open();tx.size.value=120;tx.angle.value=34;tx.start();var started:=Time.get_ticks_msec();app.new_project();var new_ms:=Time.get_ticks_msec()-started;await wait_transform();check(editor.context.is_empty() and tx.pending.is_empty() and app.canvas.selection_preview==null,"New safely discards detached transform worker data and old references")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie,"worker_ms":worker_ms,"worker_frames":worker_frames,"new_during_worker_ms":new_ms};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("DRAWING_TRANSFORM_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
