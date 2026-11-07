extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(400).timeout.connect(func():push_error("App raster measurement watchdog");quit(2));call_deferred("run")
func fixture(target: String) -> void:
	DirAccess.make_dir_recursive_absolute(target);var cels: Array=[]
	for i in range(32):
		var image:=Drawing.blank(1920,1080);image.fill(Color(0,.5,0,0));image.fill_rect(Rect2i(100+i*20,200+i*10,140,80),Color(float(i+1)/32,.7,.2,.5));var name:="unique_%02d.png"%i;image.save_png(target.path_join(name));cels.append({"id":"cel"+str(i),"start":i,"duration":17 if i==31 else 1,"path":name,"pixel_sha256":Storage.image_hash(image)})
	var data:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"world":World.empty(),"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)],"layers":[{"id":"ink","name":"Ink","visible":true,"cels":cels}],"audio":{},"editor":{"frame":0}}
	FileAccess.open(target.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(data))
func statistics(values: Array) -> Dictionary:
	var ordered:=values.duplicate();ordered.sort();var total:=0.0
	for value in values:total+=float(value)
	return {"mean_ms":total/values.size(),"p50_ms":ordered[values.size()/2],"p95_ms":ordered[mini(values.size()-1,ceili(values.size()*.95)-1)],"max_ms":ordered[-1],"samples_ms":values}
func verify_preview(source: String,at: int) -> bool:
	var image:=Image.load_from_file(source.path_join("unique_%02d.png"%at));image.convert(Image.FORMAT_RGBA8)
	var expected:=Drawing.composite([{"visible":true,"cels":[{"start":0,"duration":48,"image":image}]}],0,1920,1080)
	return app.canvas.overlay.get_image().get_data()==expected.get_data()
func one(source: String,adaptive: bool) -> Dictionary:
	app.new_project();await settled();app.cold_cel_loading=adaptive
	var before:=OS.get_static_memory_usage();var started:=Time.get_ticks_usec();var opened: bool=app.open_project(source);var open_ms:=(Time.get_ticks_usec()-started)/1000.
	if not opened:return {"error":app.open_project_error}
	await settled();var ready_ms:=(Time.get_ticks_usec()-started)/1000.;var loaded_bytes:=OS.get_static_memory_usage()-before;var timings: Array=[];var exact:=true
	for at in range(32):
		started=Time.get_ticks_usec();app.set_frame(at)
		for n in range(2):await process_frame
		await RenderingServer.frame_post_draw;timings.append((Time.get_ticks_usec()-started)/1000.)
		exact=exact and verify_preview(source,at)
	var builds: int=app.drawing_overlay_cache.builds;var held: Array=[]
	for at in range(32,42):
		started=Time.get_ticks_usec();app.set_frame(at)
		for n in range(2):await process_frame
		await RenderingServer.frame_post_draw;held.append((Time.get_ticks_usec()-started)/1000.)
	var cold_count:=0;var cache_bytes:=0
	for cel in app.layers[0].cels:
		if cel.has("raster_owner"):cold_count+=1;cache_bytes=cel.raster_owner._cache.retained_bytes
	return {"adaptive":adaptive,"open_call_ms":open_ms,"ready_ms":ready_ms,"tracked_delta_after_ready":loaded_bytes,"all_preview_rgba_exact":exact,"cold_owners":cold_count,"decoded_cache_bytes":cache_bytes,"sequential_seeks":statistics(timings),"held_seeks":statistics(held),"held_builds":app.drawing_overlay_cache.builds-builds}
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];var source:=folder.path_join("source");fixture(source);app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	var runs: Array=[]
	for i in range(3):runs.append({"eager":await one(source,false),"adaptive":await one(source,true)})
	var ok:=runs.all(func(row):return row.eager.get("all_preview_rgba_exact",false) and row.adaptive.get("all_preview_rgba_exact",false) and row.eager.cold_owners==0 and row.adaptive.cold_owners==32 and row.eager.held_builds==0 and row.adaptive.held_builds==0)
	var result:={"ok":ok,"runs":runs,"scope":"Three eager/adaptive ordinary Studio directory Opens and32sequential/10held frame seeks,32distinct sparseHDcels,empty3Dworld,private software GL. Seek times include two UI frames and GPU presentation; pixel checks afterward. Tracked deltas are not peak/RSS/GPU. No hardware/native/dense-noise or artist latency acceptance."}
	FileAccess.open(folder.path_join("verification.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("CEL_RASTER_APP_BENCHMARK "+JSON.stringify(result));await app.quit_studio();quit(0 if ok else 1)
