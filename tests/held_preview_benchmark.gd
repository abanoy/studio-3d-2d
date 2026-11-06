extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
func _initialize() -> void:
	create_timer(120).timeout.connect(func():push_error("Held overlay benchmark watchdog");quit(2));call_deferred("run")
func run() -> void:
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.set_process(false)
	app.show_project_options();app.project_options.hide();check(app.project_timing.apply_duration(240).is_empty(),"240frame baseline scene prepares")
	for at in [0,120]:
		var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100+at,100,100,100),Color(.2,.7,.8,.5));Drawing.touch(image);Drawing.insert(app.layers[1],at,240,image)
	app.changed();var runs:=[]
	for repetition in range(3):
		app.set_frame(0);app._process(0);var before=app.get("drawing_overlay_cache");var prior_builds: int=before.builds if before!=null else 0;var prior_hits: int=before.hits if before!=null else 0
		var started:=Time.get_ticks_usec()
		for at in range(240):app.set_frame(at);app._process(0)
		var elapsed:=(Time.get_ticks_usec()-started)/1000.0
		var overlay: Image=app.canvas.overlay.get_image();var expected:=Drawing.composite(app.layers,239,1920,1080)
		check(overlay.get_data()==expected.get_data(),"actual preview texture matches uncached reference after240seeks")
		var cache=app.get("drawing_overlay_cache")
		runs.append({"milliseconds":elapsed,"cache_builds":cache.builds-prior_builds if cache!=null else -1,"cache_hits":cache.hits-prior_hits if cache!=null else -1})
	print("HELD_PREVIEW_BENCHMARK ",JSON.stringify({"checks":checks,"failures":failures,"runs":runs,"frames":240,"raster":[1920,1080],"actual_gpu_texture":true,"scope":"three same-process loops of set_frame+ordinary _process; automatic app _process disabled; frame0 warmup excluded; not pointer comfort or full-render performance"}));await app.quit_studio();quit(0 if failures==0 else 1)
