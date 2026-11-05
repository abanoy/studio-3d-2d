extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Video import watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_phase(expected: String) -> void:
	while app.video_importer.phase!=expected and not app.video_importer.phase.is_empty():await process_frame
	await settle()
func wait_save() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var source:=folder.path_join("source.mov");var reading: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery-cold" if reading else "recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-cold" if reading else "cache")
	var importer=app.video_importer;var packed:=folder.path_join("Video scene.has")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for path in [packed,folder.path_join("Video scene linked.has")]:
			app.has_project.open_file(path);await wait_save()
			check(app.layers.size()==3 and app.layers[2].cels.size()==2,"cold project restores independent editable video holds")
			check(Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==expected.paint,"cold pixels are exact with no required video source")
			check(JSON.stringify(app.layers[2].origin,"",true,true)==JSON.stringify(expected.origin,"",true,true),"cold source history preserves key settings and rational timing")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,0,true))==expected.render,"cold shared compositor matches original preview")
		print("VIDEO_IMPORT_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"procedural 3D room loads")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);await settle()
	var original:=Drawing.blank(1920,1080);original.fill_rect(Rect2i(50,50,80,80),Color.CYAN);Drawing.insert(app.layers[1],0,48,original);app.changed();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var oldpixels:=Storage.image_hash(original);var keys: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var sha:=FileAccess.get_sha256(source)
	importer.begin(source);await wait_phase("layers")
	check(importer.phase=="layers" and importer.review.visible,"asynchronous real video inspection opens review")
	if importer.phase!="layers":print(app.status.text);app.free();quit(1);return
	app.raster_importer.begin("unrelated.kra");check(app.raster_importer.phase.is_empty(),"Krita import cannot race video review")
	importer.key_enabled.button_pressed=true;importer.prepare();await wait_phase("candidate")
	check(importer.phase=="candidate" and importer.decoded.size()==2,"real FFmpeg produces two complete editable holds")
	if importer.phase!="candidate":print(app.status.text);app.free();quit(1);return
	check(app.layers.size()==2 and app.history.is_empty() and app.keys==keys and app.current_world()==world and Storage.image_hash(original)==oldpixels,"candidate leaves authored scene untouched")
	check(importer.decoded[0].image.get_pixel(10,10).a==0 and importer.decoded[0].image.get_pixel(960,540).r>.99,"keyed background transparent and foreground retained")
	importer.scrub.value=20;await settle();check(app.frame==0,"source preview does not seek scene")
	var job: String=importer.job;importer.commit()
	check(app.layers.size()==3 and app.history.size()==1 and app.layers[2].cels.size()==2,"Add makes one layer and one Undo")
	var paint:=Storage.image_hash(Drawing.cel_at(app.layers[2],0).image);var origin: Dictionary=app.layers[2].origin.duplicate(true)
	app.undo();check(app.layers.size()==2 and Storage.image_hash(original)==oldpixels and app.keys==keys and app.current_world()==world,"Undo preserves existing camera, 3D and ink")
	app.redo();check(app.layers.size()==3 and Storage.image_hash(Drawing.cel_at(app.layers[2],0).image)==paint,"Redo restores exact editable pixels")
	var recovery_error:=preload("res://src/recovery.gd").checkpoint(folder.path_join("import-recovery"),"imported",app.video,app.keys,app.layers,app.source,app.frame,app.audio_document(),"",app.recovery_revision,app.renderer.model_state(),app.renderer.world_state(),app.palette)
	var restored:=Storage.load_project(folder.path_join("import-recovery/imported"))
	check(recovery_error.is_empty() and not restored.has("error") and Storage.image_hash(Drawing.cel_at(restored.layers[2],0).image)==paint,"recovery storage retains video drawings")
	var render: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	app.has_project.save_file(packed,"packed");await wait_save();check(app.has_project.path==packed,"ordinary packed HAS saves import")
	app.has_project.save_file(folder.path_join("Video scene linked.has"),"linked");await wait_save();check(FileAccess.file_exists(folder.path_join("Video scene linked.has")),"linked HAS saves import")
	var error: String=await app.export_movie(folder);check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")).get_data()==render.get_data(),"real MP4 render input equals shared scene preview byte for byte")
	check(FileAccess.get_sha256(source)==sha,"original video remains unchanged")
	app.undo();app.set_frame(0);importer.begin(source);app.set_frame(1);await wait_phase("");check(importer.pid<0 and app.layers.size()==2,"seek cancels worker and prevents late adoption")
	app.set_frame(0);importer.begin(source);await wait_phase("layers");importer.cancel();check(importer.phase.is_empty() and app.layers.size()==2,"review Cancel adds nothing")
	importer.begin(source);app.changed();await wait_phase("");check(importer.pid<0 and app.layers.size()==2,"authored revision invalidates pending worker")
	importer.begin(source);await wait_phase("layers");importer.prepare();importer.cancel();await wait_phase("");check(importer.pid<0 and app.layers.size()==2,"conversion Cancel drains owned worker without late layer")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"paint":paint,"origin":origin,"render":Storage.image_hash(render)},"",true,true))
	print("VIDEO_IMPORT_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"job":job}));app.free();quit(0 if failures==0 else 1)
