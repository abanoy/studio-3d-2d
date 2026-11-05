extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
var background_frames:=0
func _initialize() -> void:
	create_timer(200).timeout.connect(func():push_error("Gap fill watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_fill() -> void:
	while app.fill_editor.busy():background_frames+=1;await process_frame
	await settle()
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func click(point: Vector2) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT
	var rect: Rect2=app.canvas.image_rect();event.position=rect.position+point/Vector2(1920,1080)*rect.size
	for pressed in [true,false]:event.pressed=pressed;app.canvas._gui_input(event)
func control(text: String,node: Node) -> Button:
	for child in node.get_children():
		if child is Button and child.text==text:return child
		var found:=control(text,child)
		if found:return found
	return null
func click_control(button: Button) -> void:
	var p:=button.get_global_rect().get_center();var motion:=InputEventMouseMotion.new();motion.position=p;root.push_input(motion,true)
	for pressed in [true,false]:
		var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.position=p;e.pressed=pressed;root.push_input(e,true);await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var packed:=folder.path_join("Gap fill.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed);await job()
		check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.flats and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==expected.ink,"cold packed Open restores separate gap-filled pixels and exact original ink")
		check(app.fill_editor.close_gaps.value==0 and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"fill setting is session-only; standard world and animated shot remain exact")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,"cold render matches committed fill exactly and leaves original HAS untouched")
		print("FILL_GAPS_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"reader":true}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard3D environment coexists with fill")
	app.keys=[Timeline.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),Timeline.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)]
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.layers[1].cels.clear();var ink:=Drawing.blank(1920,1080)
	for rect in [Rect2i(700,350,200,1),Rect2i(700,549,200,1),Rect2i(700,350,1,200),Rect2i(899,350,1,200)]:ink.fill_rect(rect,Color.BLACK)
	ink.fill_rect(Rect2i(789,350,3,1),Color.TRANSPARENT);Drawing.insert(app.layers[1],0,48,ink);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var ink_hash:=Storage.image_hash(ink);var keys: Array=app.keys.duplicate(true);var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	app.tool.select(2);app.fill_editor.refresh();control("Color layer below",app.fill_editor.panel).pressed.emit();app.color.color=Color("55cc88");app.canvas.zoom=1.2;app.canvas.pan=Vector2(17,-9);root.size=Vector2i(1200,760);await settle()
	check(app.fill_editor.close_gaps.value==0 and app.fill_editor.panel.is_visible_in_tree(),"Simple fill defaults to unchanged zero-gap behavior")
	var history: int=app.history.size();click(Vector2(800,450));await wait_fill()
	check(not app.fill_editor.pending.is_empty() and app.fill_editor.last_result.edge and Drawing.cel_at(app.layers[1],0).is_empty(),"the actual three-pixel opening spills at zero and remains an unapplied preview")
	await click_control(control("Cancel",app.fill_editor.preview_row));app.fill_editor.close_gaps.value=2;click(Vector2(800,450));await wait_fill()
	check(app.fill_editor.last_result.edge and not app.fill_editor.pending.is_empty(),"two-pixel closing does not pretend to seal a three-pixel opening");app.fill_editor.cancel()
	app.fill_editor.close_gaps.value=3;click(Vector2(800,450));await wait_fill();var worker_ms: float=app.fill_editor.last_result.worker_ms
	check(not app.fill_editor.pending.is_empty() and not app.fill_editor.last_result.edge and app.fill_editor.last_result.region==198*198 and app.fill_editor.last_result.gap_pixels==3,"zoomed routed fill seals three pixels and previews only the exact interior")
	check(app.history.size()==history and Drawing.cel_at(app.layers[1],0).is_empty() and Storage.image_hash(ink)==ink_hash,"even a small gap-aware fill stays uncommitted and preserves line art")
	check(background_frames>3 and app.fill_editor.last_result.background_thread,"gap filtering and flood traversal run on a real worker while UI frames continue")
	var viewport: Rect2=app.inspector_scroll.get_global_rect()
	check(viewport.encloses(control("Apply fill",app.fill_editor.preview_row).get_global_rect()) and viewport.encloses(control("Cancel",app.fill_editor.preview_row).get_global_rect()),"complete preview buttons are reachable in the narrow Properties panel")
	root.get_texture().get_image().save_png(folder.path_join("gap-preview-1200.png"));var preview_render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	await click_control(control("Cancel",app.fill_editor.preview_row));var cancelled_render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(preview_render.get_data()==cancelled_render.get_data() and Drawing.cel_at(app.layers[1],0).is_empty(),"Cancel leaves artwork unchanged and preview never enters the final renderer")
	click(Vector2(800,450));await wait_fill();await click_control(control("Apply fill",app.fill_editor.preview_row));var cel:=Drawing.cel_at(app.layers[1],0);var flats: Image=cel.image;var first:=Storage.image_hash(flats)
	check(app.history.size()==history+1 and flats.get_pixel(800,450).to_html()=="55cc88ff" and flats.get_pixel(40,40).a==0 and flats.get_pixel(789,350).a==0,"actual Apply fills only Flats, leaves virtual closure unpainted and adds one cel Undo")
	app.undo();check(Drawing.cel_at(app.layers[1],0).is_empty(),"Undo removes the gap-filled cel completely");app.redo();flats=Drawing.cel_at(app.layers[1],0).image;check(Storage.image_hash(flats)==first,"Redo restores every committed gap-fill pixel exactly")
	app.color.color=Color("66aaff");click(Vector2(800,450));await wait_fill();app.fill_editor.apply_pending();var second:=Storage.image_hash(flats)
	check(app.history[-1].type=="pixels" and app.history[-1].bytes<1024*1024 and first!=second,"recolor uses bounded tile Undo on an existing drawing")
	app.undo();check(Storage.image_hash(flats)==first,"tile Undo restores the previous filled color");app.redo();check(Storage.image_hash(flats)==second,"tile Redo restores recolored pixels")
	app.color.color=Color.RED;click(Vector2(800,450));await wait_fill();app.fill_editor.close_gaps.value=4;app.fill_editor.apply_pending()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"changing gap setting rejects an immediate stale Apply before the next process frame")
	app.fill_editor.close_gaps.value=3;click(Vector2(800,450));app.fill_editor.tolerance.value=9;await wait_fill()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"changing tolerance while the worker runs discards its result")
	click(Vector2(800,450));await wait_fill();app.color.color=Color.GREEN;app.fill_editor.apply_pending();check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"color change cannot accidentally commit the old preview")
	app.color.color=Color.RED;click(Vector2(800,450));await wait_fill();app.fill_editor.sample_visible.button_pressed=false;app.fill_editor.apply_pending();check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"sampling-mode change rejects stale preview pixels")
	app.fill_editor.sample_visible.button_pressed=true
	check(Storage.image_hash(ink)==ink_hash and equal(keys,app.keys) and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"all gap fills preserve original ink, standard world, shot/view and source geometry")
	app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed);var linked:=folder.path_join("Gap fill linked.has");app.has_project.save_file(linked,"linked");await job();app.has_project.open_file(linked);await job()
	check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==second and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==ink_hash,"ordinary linked HAS retains separate exact line art and gap-fill pixels")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.open_project(app.recovery_root.path_join(app.recovery_session)) and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==second and FileAccess.get_sha256(packed)==manual,"recovery reopens the fill while preserving the original manual packed save")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"normal movie PNG exactly matches committed fill over the animated3D environment")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var expected:={"flats":second,"ink":ink_hash,"keys":keys,"world":world,"render":Storage.image_hash(reference),"project_hash":manual};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	app.mode.select(0);app.change_mode(0);app.tool.select(2);app.fill_editor.close_gaps.value=8;click(Vector2(40,40));var started:=Time.get_ticks_msec();app.new_project();var new_ms:=Time.get_ticks_msec()-started;await wait_fill()
	check(app.layers.size()==2 and Drawing.cel_at(app.layers[1],0).is_empty() and app.fill_editor.pending.is_empty(),"New during gap computation safely discards detached worker data")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie,"worker_ms":worker_ms,"background_frames":background_frames,"new_during_worker_ms":new_ms};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("FILL_GAPS_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
