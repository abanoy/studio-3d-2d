extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(220).timeout.connect(func():push_error("Idle raster budget watchdog");quit(2));call_deferred("run")
func fixture(target: String) -> Array:
	DirAccess.make_dir_recursive_absolute(target);var cels: Array=[];var hashes: Array=[]
	for i in range(12):
		var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100+i*10,100,100,80),Color(float(i+1)/12,.5,.7,.5));var name:="cel_%02d.png"%i;image.save_png(target.path_join(name));var digest:=Storage.image_hash(image);hashes.append(digest);cels.append({"id":"cel"+str(i),"start":i,"duration":37 if i==11 else 1,"path":name,"pixel_sha256":digest})
	var data:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"world":World.empty(),"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)],"layers":[{"id":"ink","name":"Ink","visible":true,"cels":cels}],"audio":{},"editor":{"frame":0}}
	FileAccess.open(target.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(data));return hashes
func pixel_hash(cel: Dictionary) -> String:return Storage.image_hash(Drawing.image(cel))
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var source:=folder.path_join("source");var original:=fixture(source);var source_sha:=FileAccess.get_sha256(source.path_join("project.json"));app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	check(app.open_project(source),"default ordinary Open installs larger cold project")
	app.mode.select(0);app.change_mode(0);app.active_layer=0;app.layer_choice.select(0);app.tool.select(0);app.brush_pressure.button_pressed=false;app.radius.value=3;app.color.color=Color.RED;app.raster_budget_due=Time.get_ticks_msec()+60000
	var edited: Array=[];var layer: Dictionary=app.layers[0]
	for i in range(12):
		app.set_frame(i);var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(400,300));app.paint_segment(Vector2(420,310));event.pressed=false;app.canvas_input(event,Vector2(420,310));await process_frame;edited.append(pixel_hash(layer.cels[i]))
	await settled();var peak: Dictionary=app.raster_budget.sample();var peak_memory:=OS.get_static_memory_usage();check(peak.hot_owners==12 and peak.hot_bytes>peak.target_bytes and app.history.size()==12,"twelve real brush commands exceed owned-hot soft target without Image pins in history")
	var attempts: int=app.raster_budget.attempts;app.drawing=true;app.raster_budget_due=0;await settled();app.drawing=false
	check(app.raster_budget.attempts==attempts and app.raster_budget.sample().hot_owners==12,"natural process defers idle release during an active gesture")
	app.raster_budget_due=0;var started:=Time.get_ticks_msec()
	while Time.get_ticks_msec()-started<15000:
		var state: Dictionary=app.raster_budget.sample()
		if state.hot_bytes+state.decoded_cache_bytes<=state.target_bytes:break
		await process_frame
	var after: Dictionary=app.raster_budget.sample();var after_memory:=OS.get_static_memory_usage();var idle_ms:=Time.get_ticks_msec()-started
	check(after.hot_bytes+after.decoded_cache_bytes<=after.target_bytes and app.raster_budget.releases>0,"natural idle cadence releases edited inactive cels to owned-hot/cache target")
	check(layer.cels[11].raster_owner.is_pinned() and layer.cels.any(func(cel):return not cel.raster_owner.is_pinned()),"current drawing stays hot while inactive edited owners become cold")
	check(app.history.size()==12 and app.history.all(func(command):return command.has("raster_owner") and not command.has("image")),"idle release preserves all twelve logical pixel Undo commands")
	app.raster_budget_due=Time.get_ticks_msec()+60000;var exact:=true
	for i in range(12):exact=exact and pixel_hash(layer.cels[i])==edited[i]
	check(exact,"all edited RGBA remains exact after automatic idle compression")
	for i in range(11,-1,-1):app.undo();exact=exact and pixel_hash(layer.cels[i])==original[i]
	check(exact and app.history.is_empty() and app.redo_history.size()==12,"actual Undo rehydrates every cooled drawing and restores original pixels")
	for i in range(12):app.redo();exact=exact and pixel_hash(layer.cels[i])==edited[i]
	check(exact and app.history.size()==12,"actual Redo restores every authored stroke after automatic release")
	var cache=app.raster_budget.cache;var current: Array=app.layers;app.exporting=true;var refused: bool=not app.new_project();app.exporting=false
	check(refused and is_same(app.raster_budget.cache,cache) and is_same(app.layers,current),"refused New preserves the installed document and budget context")
	check(FileAccess.get_sha256(source.path_join("project.json"))==source_sha,"idle/edit/history never changes original source manifest")
	app.new_project();await settled();check(app.raster_budget.cache==null,"successful New drops app budget context")
	var proof:={"checks":checks,"failures":failures,"peak":peak,"after_idle":after,"peak_tracked_memory":peak_memory,"after_idle_tracked_memory":after_memory,"tracked_reduction":peak_memory-after_memory,"idle_ms":idle_ms,"scope":"12actual brush-edited sparseHDcels,normal automatic loading and natural1second idle cadence; owned-hot/cache soft target only,not whole RAM/RSS/GPU or noisy/hardware guarantee"}
	FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE).store_string(JSON.stringify(proof));print("CEL_RASTER_BUDGET_SMOKE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
