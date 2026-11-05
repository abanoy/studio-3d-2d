extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const T=preload("res://src/timeline.gd")
var app
var checks:=0
var failures:=0
var background_frames:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Expanded fill watchdog");quit(2));call_deferred("run")
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
func button(text: String,node: Node) -> Button:
	for child in node.get_children():
		if child is Button and child.text==text:return child
		var found:=button(text,child)
		if found:return found
	return null
func click_control(control: Control) -> void:
	var p:=control.get_global_rect().get_center();var motion:=InputEventMouseMotion.new();motion.position=p;root.push_input(motion,true)
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=p;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;root.push_input(event,true);await process_frame
	await settle()
func click(point: Vector2) -> void:
	var rect: Rect2=app.canvas.image_rect()
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=rect.position+point/Vector2(1920,1080)*rect.size;event.button_index=MOUSE_BUTTON_LEFT;event.pressed=pressed;app.canvas._gui_input(event)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reader: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-cold" if reader else "recovery");app.recent_path=folder.path_join("recents-cold.json" if reader else "recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reader else "cache")
	var packed:=folder.path_join("Under ink.has")
	if reader:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed);await job()
		check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.flats and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==expected.ink,"cold Open restores exact grown color and untouched translucent ink")
		check(app.fill_editor.expand_edges.value==0 and equal(app.keys,expected.keys) and equal(World.portable(app.current_world()),expected.world),"growth is session-only; world and camera keys persist")
		var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);check(Storage.image_hash(reference)==expected.render and FileAccess.get_sha256(packed)==expected.project_hash,"cold render equals movie input without changing saved HAS")
		print("FILL_EXPAND_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.restore_world(app.current_world()).is_empty(),"standard3D environment is installed")
	app.keys=[T.key(0,Vector3(-1.5,2,5),Quaternion.IDENTITY,60),T.key(48,Vector3(1.5,1.5,3),Quaternion.IDENTITY,52)];app.mode.select(0);app.change_mode(0);app.set_frame(0)
	var ink:=Drawing.blank(1920,1080)
	for r in [Rect2i(700,350,200,1),Rect2i(700,549,200,1),Rect2i(700,350,1,200),Rect2i(899,350,1,200)]:ink.fill_rect(r,Color.BLACK)
	for r in [Rect2i(701,351,198,1),Rect2i(701,548,198,1),Rect2i(701,351,1,198),Rect2i(898,351,1,198)]:ink.fill_rect(r,Color(0,0,0,0.35))
	app.layers[1].cels.clear();Drawing.insert(app.layers[1],0,48,ink);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var ink_hash:=Storage.image_hash(ink);var keys: Array=app.keys.duplicate(true);var world: Dictionary=World.portable(app.current_world());var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	app.tool.select(2);app.fill_editor.refresh();button("Color layer below",app.fill_editor.panel).pressed.emit();app.color.color=Color.CYAN;app.canvas.zoom=1.2;app.canvas.pan=Vector2(17,-9);root.size=Vector2i(1200,760);app.set_advanced(false);await settle()
	check(app.fill_editor.expand_edges.value==0 and not app.fill_editor.expand_edges.is_visible_in_tree(),"Simple mode keeps ordinary zero-growth fill and hides the specific adjustment")
	click(Vector2(800,450));await wait_fill();var cel:=Drawing.cel_at(app.layers[1],0)
	check(not cel.is_empty() and cel.image.get_pixel(701,450).a==0 and app.fill_editor.pending.is_empty(),"zero growth retains old direct-fill pixels and leaves the translucent boundary empty")
	app.undo();app.set_advanced(true);app.fill_editor.expand_edges.value=1;await settle()
	check(app.fill_editor.expand_edges.is_visible_in_tree(),"Advanced reveals Grow under lines")
	var history: int=app.history.size();click(Vector2(800,450));await wait_fill();var worker_ms: float=app.fill_editor.last_result.worker_ms
	check(not app.fill_editor.pending.is_empty() and not app.fill_editor.last_result.edge and app.fill_editor.last_result.region==196*196 and app.fill_editor.last_result.expanded_pixels==198*198-196*196,"one-pixel growth previews the exact discovered region plus its square border")
	check(Drawing.cel_at(app.layers[1],0).is_empty() and app.history.size()==history and Storage.image_hash(ink)==ink_hash,"a small grown fill never auto-commits or changes sampled ink")
	var viewport: Rect2=app.inspector_scroll.get_global_rect()
	check(viewport.encloses(button("Apply fill",app.fill_editor.preview_row).get_global_rect()) and viewport.encloses(button("Cancel",app.fill_editor.preview_row).get_global_rect()),"complete preview actions remain reachable at1200pixels")
	root.get_texture().get_image().save_png(folder.path_join("growth-preview-1200.png"));var before: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	await click_control(button("Cancel",app.fill_editor.preview_row));var cancelled: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(before.get_data()==cancelled.get_data() and Drawing.cel_at(app.layers[1],0).is_empty(),"Cancel preserves artwork and candidate preview stays outside the final renderer")
	click(Vector2(800,450));await wait_fill();await click_control(button("Apply fill",app.fill_editor.preview_row));cel=Drawing.cel_at(app.layers[1],0);var flats: Image=cel.image;var first:=Storage.image_hash(flats)
	check(app.history.size()==history+1 and app.history[-1].type=="cels" and flats.get_pixel(701,450)==Color.CYAN and flats.get_pixel(700,450).a==0,"real Apply grows beneath the translucent edge without going beyond the chosen radius")
	var composite:=Drawing.composite(app.layers,0,1920,1080);var edge:=composite.get_pixel(701,450)
	check(edge.a8==255 and edge.r8==0 and edge.g8>=165 and edge.g8<=167 and edge.b8>=165 and edge.b8<=167,"color beneath translucent ink removes the transparent seam without recoloring ink")
	app.undo();check(Drawing.cel_at(app.layers[1],0).is_empty(),"new grown cel has one complete Undo");app.redo();flats=Drawing.cel_at(app.layers[1],0).image;check(Storage.image_hash(flats)==first,"new-cel Redo restores exact growth pixels")
	app.color.color=Color(1,0,0,0.5);click(Vector2(800,450));await wait_fill();app.fill_editor.apply_pending();var second:=Storage.image_hash(flats)
	check(app.history[-1].type=="pixels" and app.history[-1].bytes<1024*1024 and flats.get_pixel(701,450).to_html()=="ff000080","recolor replaces exact RGBA including grown edges through bounded tile history")
	app.undo();check(Storage.image_hash(flats)==first,"tile Undo restores under-ink pixels");app.redo();check(Storage.image_hash(flats)==second,"tile Redo restores exact alpha color")
	app.color.color=Color.GREEN;click(Vector2(800,450));await wait_fill();app.fill_editor.expand_edges.value=2;app.fill_editor.apply_pending()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"changed radius rejects immediate stale Apply")
	app.fill_editor.expand_edges.value=1;click(Vector2(800,450));app.fill_editor.expand_edges.value=0;await wait_fill()
	check(app.fill_editor.pending.is_empty() and Storage.image_hash(flats)==second,"changed radius while worker runs discards old candidate")
	check(background_frames>3 and app.fill_editor.last_result.background_thread,"expansion runs over detached worker bytes while UI frames continue")
	check(Storage.image_hash(ink)==ink_hash and equal(keys,app.keys) and equal(world,World.portable(app.current_world())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"all fills preserve original ink, common world, camera/view and source geometry")
	app.has_project.save_file(packed,"packed");await job();var manual:=FileAccess.get_sha256(packed);var linked:=folder.path_join("Under ink linked.has");app.has_project.save_file(linked,"linked");await job();app.has_project.open_file(linked);await job()
	check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==second and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==ink_hash,"linked HAS retains exact grown color and separate ink")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.open_project(app.recovery_root.path_join(app.recovery_session)) and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==second and FileAccess.get_sha256(packed)==manual,"recovery retains growth pixels without changing the manual save")
	app.set_frame(0);var reference: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==reference.get_data(),"ordinary MP4 frame equals committed grown fill over the animated3D background")
	var movie: String=app.last_export_folder.path_join("movie.mp4");var expected:={"flats":second,"ink":ink_hash,"keys":keys,"world":world,"render":Storage.image_hash(reference),"project_hash":manual};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	app.mode.select(0);app.change_mode(0);app.tool.select(2);app.fill_editor.expand_edges.value=8;click(Vector2(40,40));var started:=Time.get_ticks_msec();app.new_project();var new_ms:=Time.get_ticks_msec()-started;await wait_fill()
	check(app.layers.size()==2 and Drawing.cel_at(app.layers[1],0).is_empty() and app.fill_editor.pending.is_empty(),"New safely discards a detached expansion worker result")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie,"worker_ms":worker_ms,"background_frames":background_frames,"new_during_worker_ms":new_ms};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("FILL_EXPAND_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
