extends "res://tests/movement_path_smoke.gd"
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
func _initialize() -> void:
	create_timer(350).timeout.connect(func():push_error("Cold write watchdog");quit(2));call_deferred("run")
func press(point: Vector2,down: bool) -> void:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=down;app.canvas_input(event,point)
func motion(point: Vector2) -> void:
	var event:=InputEventMouseMotion.new();event.button_mask=MOUSE_BUTTON_MASK_LEFT;app.canvas_input(event,point)
func digest(at: int) -> String:return Snapshot.digest(Drawing.image(Drawing.cel_at(app.layers[1],at)).get_data())
func menu(at: int,action: int) -> void:
	var cel:=Drawing.cel_at(app.layers[1],at);app.cel_clipboard.open_menu(app.layers[1].id,cel.get("id",""),at,Vector2i(300,200));app.cel_clipboard.menu.id_pressed.emit(action);await settled()
func select_area(at: int) -> void:
	app.set_frame(at);app.tool.select(4);press(Vector2(420,220),true);motion(Vector2(460,250));press(Vector2(460,250),false);await settled()
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.cold_cel_loading="--adaptive-open" in OS.get_cmdline_user_args();app.cold_cel_min_bytes=0;app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in OS.get_cmdline_user_args() else "writer-cache")
	if "--read" in OS.get_cmdline_user_args():
		app.has_project.open_file(folder.path_join("Cold write.has"));await wait_job();var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		if app.cold_cel_loading:check(app.layers[1].cels.all(func(cel):return cel.has("raster_owner") and not cel.raster_owner.is_pinned()),"fresh normal HAS Open uses adaptive cold owners without fixture injection")
		check(app.layers[1].cels.size()==5 and app.layers[1].cels[4].duration==8,"fresh packed reader restores saved boundaries independently of later recovery edits")
		for at in [0,12,24,36,40]:
			check(digest(at)==expected.art[str(at)],"fresh reader restores exact authored pixels at frame"+str(at))
			var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);check(picture.get_data()==Image.load_from_file(folder.path_join("frame%d.png"%at)).get_data(),"fresh GPU frame matches edited cold-source writer at"+str(at))
		print("CEL_RASTER_WRITE_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original room opens for cold editing and persistence")
	var layer: Dictionary=app.layers[1];var starts: Array=[0,12,24,36,40];var original: Array=[];var snapshots: Array=[];var cache:=Cache.new()
	for i in range(starts.size()):
		var image:=Drawing.blank(1920,1080);image.fill(Color(0,.5,0,0));image.fill_rect(Rect2i(400,200,128,96),Color(float(i+1)/5,.3,.7,1))
		if i==1:image.fill_rect(Rect2i(400,200,120,120),Color.BLACK);image.fill_rect(Rect2i(410,210,100,100),Color(0,.5,0,0))
		var end: int=starts[i+1] if i+1<starts.size() else 48;var cel:=Drawing.insert(layer,starts[i],end,image);var snapshot=Snapshot.capture(image).raster;snapshots.append(snapshot);original.append(snapshot.pixel_sha256())
		if not app.cold_cel_loading:cel.raster_owner=Owner.from_snapshot(snapshot,cache).owner;cel.erase("image")
	layer.opacity=.5
	if app.cold_cel_loading:
		var state: Dictionary=app.project_snapshot();var source_folder:=folder.path_join("source-project")
		var saved_source:=Storage.save_project(source_folder,state.video,state.camera_keys,state.layers,str(state.get("source","")),int(state.editor.frame),state.audio,{},{},true,state.world,{},state.palette)
		check(saved_source.is_empty() and app.open_project(source_folder),"ordinary directory Open adopts cold owners from verified PNGs")
		layer=app.layers[1];cache=layer.cels[0].raster_owner._cache;snapshots=[]
		for cel in layer.cels:snapshots.append(cel.raster_owner._cold)
	app.mode.select(0);app.change_mode(0);app.changed();app.active_layer=1;app.layer_choice.select(1);app.tool.select(0);app.brush_pressure.button_pressed=false;app.color.color=Color.BLUE;app.set_frame(0);await settled()
	app.brush_pressure.button_pressed=true;var idle_decodes:=cache.decodes;var idle_history: int=app.history.size();press(Vector2(700,500),true);press(Vector2(700,500),false);await settled()
	check(not layer.cels[0].raster_owner.is_pinned() and cache.decodes==idle_decodes and app.history.size()==idle_history and digest(0)==original[0],"zero-pressure press on existing cold cel neither pins pixels nor creates history")
	app.brush_pressure.button_pressed=false
	press(Vector2(700,500),true);motion(Vector2(730,510));press(Vector2(730,510),false);await settled();var stroke:=digest(0);var stroke_image:=Drawing.image(layer.cels[0])
	check(stroke!=original[0] and layer.cels[0].raster_owner.is_pinned() and not layer.cels[1].raster_owner.is_pinned(),"actual brush pins only edited cold cel")
	cache.clear();app.undo();await settled();check(digest(0)==original[0] and is_same(Drawing.image(layer.cels[0]),stroke_image),"actual brush Undo retains authoritative identity after cache eviction")
	app.redo();await settled();check(digest(0)==stroke,"actual brush Redo restores edited pixels")
	if "--cool-history" in OS.get_cmdline_user_args():
		check(app.history[-1].has("raster_owner") and not app.history[-1].has("image"),"actual pixel history retains owner rather than hot Image")
		stroke_image=null;var before_cool: Array=layer.cels[0].raster_owner.token();var cooled: Dictionary=layer.cels[0].raster_owner.cool()
		check(cooled.get("cooled",false) and not layer.cels[0].raster_owner.is_pinned() and layer.cels[0].raster_owner.token()==before_cool,"actual edited cel cools with Undo history present and revision unchanged")
		cache.clear();app.undo();await settled();check(digest(0)==original[0],"actual Undo rehydrates cooled edited pixels")
		app.redo();await settled();check(digest(0)==stroke,"actual Redo restores authored pixels after cooling")

	app.set_frame(12);app.tool.select(2);app.color.color=Color.RED;app.fill_editor.sample_visible.button_pressed=false;app.fill_editor.start(Vector2(450,250))
	while app.fill_editor.busy():await process_frame
	await settled();if not app.fill_editor.pending.is_empty():app.fill_editor.apply_pending();await settled()
	var filled:=digest(12);check(filled!=original[1] and Drawing.image(layer.cels[1]).get_pixel(450,250)==Color.RED and layer.cels[1].raster_owner.is_pinned(),"real fill worker pins and edits the existing cold cel")
	app.undo();await settled();check(digest(12)==original[1],"fill Undo restores original cold-source RGBA")
	app.redo();await settled();check(digest(12)==filled and digest(0)==stroke,"fill Redo preserves earlier edited peer")
	await select_area(24);press(Vector2(430,230),true);motion(Vector2(490,280));await settled()
	check(app.canvas.selection_preview!=null and not layer.cels[2].raster_owner.is_pinned() and digest(24)==original[2],"actual move preview keeps cold original unpinned and unchanged")
	press(Vector2(490,280),false);await settled();var moved:=digest(24)
	check(moved!=original[2] and layer.cels[2].raster_owner.is_pinned(),"selection Apply adopts verified borrowed cold image")
	app.undo();await settled();check(digest(24)==original[2],"selection Undo restores exact original RGBA")
	app.redo();await settled();check(digest(24)==moved,"selection Redo restores transformed placement")
	await select_area(36);var transform=app.drawing_selection_editor.transforms;transform.angle.value=20;transform.start()
	while transform.busy():await process_frame
	await settled()
	check(not transform.pending.is_empty(),"transform worker produces a valid pending result before Apply")
	if transform.pending.is_empty():
		print("TRANSFORM_DIAGNOSTIC "+JSON.stringify({"status":app.status.text,"last_result":transform.last_result,"request":transform.request,"selection_valid":app.drawing_selection_editor.valid_context(),"context":str(app.drawing_selection_editor.context)}));await app.quit_studio();quit(1);return
	var transformed_bytes: PackedByteArray=transform.pending.data
	check(app.canvas.selection_preview!=null and not layer.cels[3].raster_owner.is_pinned(),"real transform worker previews cold source without write pin")
	transform.apply_pending();await settled();var transformed:=digest(36)
	check(Drawing.image(layer.cels[3]).get_data()==transformed_bytes and transformed!=original[3],"transform Apply commits exact worker pixels through authoritative owner")
	app.undo();await settled();check(digest(36)==original[3],"transform Undo restores original cold pixels")
	app.redo();await settled();check(digest(36)==transformed,"transform Redo restores exact committed pixels")
	if "--cool-history" in OS.get_cmdline_user_args():check(app.history.filter(func(command):return command.type=="pixels").all(func(command):return command.has("raster_owner") and not command.has("image")),"brush/fill/selection/transform pixel histories all retain logical owners")

	app.set_frame(40);await menu(40,0);check(not layer.cels[4].raster_owner.is_pinned() and Snapshot.digest(Drawing.image(app.cel_clipboard.clipboard).get_data())==original[4],"actual Copy preserves cold owner and freezes exact clipboard pixels")
	await menu(40,1);check(Drawing.cel_at(layer,40).is_empty(),"actual Cut removes cold source through affected-cel history")
	app.undo();await settled();check(digest(40)==original[4] and not layer.cels[4].raster_owner.is_pinned(),"Cut Undo restores exact unpinned cold owner")
	app.redo();await settled();await menu(40,2);check(digest(40)==original[4] and Drawing.cel_at(layer,40).has("raster_owner"),"actual Paste creates independent editable pixels from cold copy")
	app.undo();app.undo();await settled();await menu(44,3);check(layer.cels.size()==6 and not layer.cels[4].raster_owner.is_pinned(),"actual Split preserves cold source and creates independent right half")
	app.undo();await settled();check(layer.cels.size()==5 and layer.cels[4].duration==8 and digest(40)==original[4],"Split Undo restores original cold exposure and pixels")
	var cue:="res://examples/tutorials/Practice cue.wav";var cue_sha:=FileAccess.get_sha256(cue);check(app.import_audio(ProjectSettings.globalize_path(cue),24).is_empty(),"original frame24 sound loads for edited movie")
	var expected: Dictionary={"art":{}}
	for at in starts:
		expected.art[str(at)]=digest(at);var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);picture.save_png(folder.path_join("frame%d.png"%at))
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected))
	var saved:=folder.path_join("Cold write.has");app.has_project.save_file(saved,"packed");await wait_job();var manual_sha:=FileAccess.get_sha256(saved)
	check(app.has_project.path==saved and not app.dirty and not layer.cels[4].raster_owner.is_pinned(),"normal packed Save streams mixed hot/cold art without pinning inactive source")
	var error: String=await app.export_movie(folder);var movie: String=app.last_finished_movie
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==Image.load_from_file(folder.path_join("frame12.png")).get_data(),"edited cold-source movie input matches saved final frame")
	app.set_frame(40);app.exposure.value=7;app.set_exposure();app.autosave_tick(true);await settled();var recovery_folder: String=app.recovery_root.path_join(app.recovery_session);var recovered:=Storage.load_project(recovery_folder)
	check(not recovered.has("error") and recovered.layers[1].cels[4].duration==7 and Storage.image_hash(recovered.layers[1].cels[4].image)==original[4] and not layer.cels[4].raster_owner.is_pinned(),"real checkpoint preserves later exposure and exact cold pixels without pinning")
	check(FileAccess.get_sha256(saved)==manual_sha and FileAccess.get_sha256(cue)==cue_sha,"checkpoint/export preserve manual HAS and original sound")
	var work_manifest:=folder.path_join("writer-cache/work_%d/project.json"%OS.get_process_id());var manifest_sha:=FileAccess.get_sha256(work_manifest);snapshots[4]._payload[0]=snapshots[4]._payload[0]^1;app.has_project.save_file(saved,"packed");await settled()
	check(app.has_project.pid<=0 and FileAccess.get_sha256(saved)==manual_sha and FileAccess.get_sha256(work_manifest)==manifest_sha,"late corrupt cold cel refuses Save and preserves both previous staging manifest and manual HAS")
	print("CEL_RASTER_WRITE_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"movie":movie,"manual_sha256":manual_sha}));await app.quit_studio();quit(0 if failures==0 else 1)
