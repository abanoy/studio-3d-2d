extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const SceneIO=preload("res://src/scene3d.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(130).timeout.connect(func():push_error("Fill smoke watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_fill() -> void:
	var until:=Time.get_ticks_msec()+15000
	while app.fill_editor.busy() and Time.get_ticks_msec()<until:await process_frame
	await settled();check(not app.fill_editor.busy(),"detached fill worker completes")
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func button(text: String,node: Node=null) -> Button:
	if node==null:node=app
	for child in node.get_children():
		if child is Button and child.text==text:return child
		var found:=button(text,child)
		if found:return found
	return null
func pointer(point: Vector2,pressed: bool) -> void:
	var e:=InputEventMouseButton.new();e.button_index=MOUSE_BUTTON_LEFT;e.pressed=pressed
	var rect: Rect2=app.canvas.image_rect();e.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(e)
func click(point: Vector2) -> void:pointer(point,true);pointer(point,false)
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0)
	var asset:=folder.path_join("rig.glb");SceneIO.make_pose_fixture(asset);check(app.pose_editor.add_model(asset).is_empty(),"real skinned standard model coexists with drawing")
	app.mode.select(0);app.change_mode(0);app.tool.select(0);app.color.color=Color.BLACK;app.radius.value=3;app.canvas.zoom=1.2;app.canvas.pan=Vector2(17,-9)
	app.create_cel(false)
	pointer(Vector2(800,400),true)
	for point in [Vector2(1000,400),Vector2(1000,600),Vector2(800,600),Vector2(800,400)]:
		var event:=InputEventMouseMotion.new();var rect: Rect2=app.canvas.image_rect();event.position=rect.position+point/Vector2(1920,1080)*rect.size;app.canvas._gui_input(event)
	pointer(Vector2(800,400),false);await settled()
	var ink: Dictionary=app.layers[1];var ink_image: Image=Drawing.cel_at(ink,0).image;var ink_hash:=Storage.image_hash(ink_image)
	check(ink_image.get_pixel(800,500).a>.9 and ink_image.get_pixel(900,500).a==0,"routed ordinary pen draws an enclosed ink outline through canvas zoom/pan")
	var keys: Array=app.keys.duplicate(true);var world: Dictionary=World.portable(app.renderer.world_state());var view: Dictionary=app.renderer.view_state();var source_hash:=FileAccess.get_sha256(app.source)
	var legacy:=folder.path_join("two-layers.has");app.has_project.save_file(legacy,"packed");await job()
	check(FileAccess.file_exists(legacy) and app.layers.size()==2,"original two-layer project remains ordinary packed HAS")
	app.tool.select(2);app.fill_editor.refresh();button("Color layer below").pressed.emit();await settled()
	var flats_id: String=app.layers[app.active_layer].id
	check(app.layers.size()==3 and app.active_layer==1 and app.layers[1].name=="Flats" and app.layers[2].id==ink.id,"Simple color layer is beneath the exact original Ink layer")
	app.undo();check(app.layers.size()==2 and app.layers[app.active_layer].id==ink.id,"layer Undo restores order and selection")
	app.undo();check(Storage.image_hash(ink_image)!=ink_hash,"older pixel Undo still targets the retained original layer image")
	app.redo();app.redo();check(app.layers[1].id==flats_id and Storage.image_hash(ink_image)==ink_hash,"Redo preserves earlier stroke history and layer identities")
	var prior: int=app.history.size();var actions: int=app.autosave_actions;app.color.color=Color("e67345");click(Vector2(900,500));await wait_fill()
	var cel:=Drawing.cel_at(app.layers[1],0)
	check(not cel.is_empty() and cel.image.get_pixel(900,500).to_html()=="e67345ff" and cel.image.get_pixel(50,50).a==0,"viewport fill uses visible Ink boundaries and changes only Flats")
	check(app.history.size()==prior+1 and app.autosave_actions==actions+1 and app.fill_editor.pending.is_empty(),"closed fill auto-applies as one meaningful undoable action")
	check(Drawing.cel_at(app.layers[1],24).image==cel.image,"fill edits the held drawing without inventing new frame exposures")
	check(Storage.image_hash(ink_image)==ink_hash and equal(keys,app.keys) and equal(world,World.portable(app.renderer.world_state())) and equal(view,app.renderer.view_state()) and FileAccess.get_sha256(app.source)==source_hash,"fill preserves exact ink, native world, camera keys/view and source bytes")
	app.undo();check(Drawing.cel_at(app.layers[1],0).is_empty(),"one Undo removes a fill-created cel completely")
	app.redo();cel=Drawing.cel_at(app.layers[1],0);var first_hash:=Storage.image_hash(cel.image)
	prior=app.history.size();click(Vector2(900,500));await wait_fill();check(app.history.size()==prior and Storage.image_hash(cel.image)==first_hash,"repeat identical fill creates no history or changed data")
	app.color.color=Color("4a9ce6");click(Vector2(900,500));await wait_fill()
	check(app.history[-1].type=="pixels" and app.history[-1].bytes<1024*1024 and cel.image.get_pixel(900,500).to_html()=="4a9ce6ff","existing cel recolor stores bounded changed tiles")
	app.undo();check(Storage.image_hash(cel.image)==first_hash,"tile Undo restores exact prior fill bytes");app.redo()
	root.size=Vector2i(1200,760);await settled()
	check(root.size==Vector2i(1200,760),"spill preview is exercised in the actual narrow window")
	var filled_hash:=Storage.image_hash(cel.image);prior=app.history.size();click(Vector2(40,40));var frames:=0
	while app.fill_editor.busy():frames+=1;app.canvas.pan.x+=.01;await process_frame
	await settled()
	check(frames>3 and app.fill_editor.last_result.background_thread,"full-HD traversal leaves actual UI frames running on a real worker")
	check(not app.fill_editor.pending.is_empty() and app.canvas.fill_preview!=null and Storage.image_hash(cel.image)==filled_hash and app.history.size()==prior,"edge fill previews without modifying image or history")
	check(app.canvas.fill_preview.get_image().get_pixel(800,500).r<.01 and app.canvas.fill_preview.get_image().get_pixel(40,40).to_html()=="4a9ce6ff","preview composites candidate color beneath unchanged opaque Ink")
	check(app.fill_editor.preview_row.get_global_rect().end.y<=app.inspector_scroll.get_global_rect().end.y,"preview Apply and Cancel remain visible in the inspector")
	root.get_texture().get_image().save_png(folder.path_join("fill-preview.png"))
	var preview_render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape);await settled()
	check(app.fill_editor.pending.is_empty() and app.canvas.fill_preview==null and Storage.image_hash(cel.image)==filled_hash,"Escape discards preview without changing pixels")
	var cancelled_render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(preview_render.get_data()==cancelled_render.get_data(),"unapplied candidate preview never enters the final-render pipeline")
	click(Vector2(40,40));await wait_fill();button("Apply fill").pressed.emit();await settled()
	check(cel.image.get_pixel(40,40).to_html()=="4a9ce6ff" and Storage.image_hash(ink_image)==ink_hash and app.history.size()==prior+1,"explicit Apply commits edge region while preserving line art")
	app.undo();check(Storage.image_hash(cel.image)==filled_hash,"large fill Undo is exact")
	click(Vector2(40,40));app.tool.select(0);click(Vector2(600,300));app.undo();app.tool.select(2);await wait_fill();check(app.fill_editor.pending.is_empty() and Storage.image_hash(cel.image)==filled_hash,"routed painting and Undo remain usable during worker and discard its stale result")
	app.layers[1].visible=false;click(Vector2(900,500));await settled();check(not app.fill_editor.busy() and Storage.image_hash(cel.image)==filled_hash,"hidden active layer cannot be filled");app.layers[1].visible=true
	# Deliberately open the original outline, then verify leak protection.
	var saved_fill: Image=cel.image.duplicate();cel.image.fill(Color.TRANSPARENT)
	var held:=ink_image.get_region(Rect2i(795,480,10,30));ink_image.fill_rect(Rect2i(795,480,10,30),Color.TRANSPARENT);app.changed();app.color.color=Color("66dd99");click(Vector2(900,500));await wait_fill()
	check(not app.fill_editor.pending.is_empty() and app.fill_editor.last_result.edge and cel.image.get_pixel(900,500).a==0,"an actual line gap triggers preview rather than an accidental canvas flood")
	button("Cancel").pressed.emit();ink_image.blit_rect(held,Rect2i(Vector2i.ZERO,held.get_size()),Vector2i(795,480));cel.image.copy_from(saved_fill);app.changed()
	var packed:=folder.path_join("filled.has");app.has_project.save_file(packed,"packed");await job();var manual_hash:=FileAccess.get_sha256(packed)
	app.new_project();app.has_project.open_file(packed);await job()
	check(app.layers.size()==3 and app.layers[1].name=="Flats" and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==filled_hash and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==ink_hash,"packed HAS reopens separate editable ink and fill layers exactly")
	check(equal(keys,app.keys) and equal(world,World.portable(app.renderer.world_state())),"painted HAS preserves complete standard world and camera values")
	var linked:=folder.path_join("filled-linked.has");app.has_project.save_file(linked,"linked");await job();app.new_project();app.has_project.open_file(linked);await job()
	check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==filled_hash,"linked HAS retains editable filled pixels")
	app.changed();app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	var recovery: String=app.recovery_root.path_join(app.recovery_session);check(not Storage.load_project(recovery).has("error") and app.open_project(recovery),"normal recovery checkpoint reopens three-layer drawing")
	check(Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==filled_hash and FileAccess.get_sha256(packed)==manual_hash,"recovery preserves fill and original manual HAS bytes")
	var before: Image=await app.renderer.capture(app.keys,app.layers,0,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==before.get_data(),"reopened filled drawing matches full-HD movie PNG exactly")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.has_project.open_file(legacy);await job();check(app.layers.size()==2 and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==ink_hash,"earlier two-layer HAS keeps its original look and layer identities")
	app.mode.select(0);app.change_mode(0);app.tool.select(2);click(Vector2(40,40));var started:=Time.get_ticks_msec();app.new_project();var reset_ms:=Time.get_ticks_msec()-started
	app.home.open_home();app._input(escape);check(not app.home.visible,"cancelled worker cannot consume Home's Escape action")
	await wait_fill()
	check(app.layers.size()==2 and Drawing.cel_at(app.layers[1],0).is_empty() and app.fill_editor.pending.is_empty(),"New while worker is live leaves no stale fill or preview")
	root.size=Vector2i(1200,760);await settled();app.mode.select(0);app.change_mode(0);app.tool.select(2);await settled();root.get_texture().get_image().save_png(folder.path_join("fill-ui.png"))
	check(app.canvas.size.x>=500 and app.fill_editor.panel.is_visible_in_tree(),"Simple fill controls keep a usable canvas at 1200 pixels")
	click(Vector2(40,40));var worker: Thread=app.fill_editor.thread;var was_live:=worker!=null and worker.is_started();var closing:=Time.get_ticks_msec();app.free();var close_ms:=Time.get_ticks_msec()-closing
	check(was_live and not worker.is_started(),"actual app teardown joins an unfinished byte-only worker")
	print("FILL_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"new_during_worker_ms":reset_ms,"close_during_worker_ms":close_ms,"background_frames":frames,"folder":folder}));quit(0 if failures==0 else 1)
