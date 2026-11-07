extends "res://tests/large_project_smoke.gd"
var frames:=0
var max_gap_ms:=0.
var last_tick:=0
var measuring:=false
func _initialize() -> void:
	create_timer(290).timeout.connect(func():push_error("Large background HAS watchdog");quit(2));process_frame.connect(tick);call_deferred("run")
func tick() -> void:
	if not measuring:return
	var now:=Time.get_ticks_usec()
	if last_tick>0:max_gap_ms=maxf(max_gap_ms,float(now-last_tick)/1000.)
	last_tick=now;frames+=1
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var reading:="--read" in args
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if reading else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var target:=folder.path_join("Background400.has")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(target);await wait_job()
		check(app.has_project.path==target and total()==400 and hashes()==expected.pixels,"fresh packed reader restores all400pixel-identical background-saved drawings")
		check(app.palette==expected.palette and app.layers[2].origin.duration==400,"cold reader preserves captured project metadata and extended video ancestry")
		var picture: Image=await app.renderer.capture(app.keys,app.layers,137,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected.png")).get_data(),"cold final scene/video drawing pixels match pre-save capture exactly")
		var memory: Dictionary=app.raster_budget.sample();check(memory.owners==400 and memory.accounted_bytes<=memory.owner_limit_bytes,"cold read stays inside unchanged registered320MiB budget")
		print("HAS_BACKGROUND_LARGE_READ "+JSON.stringify({"checks":checks,"failures":failures,"memory":memory}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var input: String=args[1];var input_sha:=FileAccess.get_sha256(input);app.has_project.open_file(input);await wait_job();check(total()==400,"ordinary Open loads previous actual400prepared-video case")
	var original:=hashes();app.mode.select(0);app.change_mode(0);app.set_frame(137);var picture: Image=await app.renderer.capture(app.keys,app.layers,137,true);picture.save_png(folder.path_join("expected.png"));picture=null
	app.palette=[{"name":"Background snapshot","rgba":"00ffffff"}];app.palette_editor.refresh(true);app.changed();check(DirAccess.copy_absolute(input,target)==OK,"new owned save target starts as exact prior good400drawing HAS")
	var before:=FileAccess.get_sha256(target);measuring=true;last_tick=Time.get_ticks_usec();var started:=Time.get_ticks_msec();app.has_project.save_file(target,"packed");var call_ms:=Time.get_ticks_msec()-started
	check(app.has_project.pid>0 and app.has_project.snapshot_writer.busy() and app.exporting,"manual400drawing Save returns while snapshot and real packer remain active")
	for n in range(20):await process_frame
	check(frames>=20 and FileAccess.get_sha256(target)==before and app.has_project.snapshot_writer.busy(),"old good target remains unchanged while actual UI frames run during PNG preparation")
	root.get_texture().get_image().save_png(folder.path_join("saving400.png"));await wait_job();measuring=false;var total_ms:=Time.get_ticks_msec()-started
	check(FileAccess.file_exists(target) and not app.dirty and app.has_project.path==target and not app.has_project.snapshot_writer.busy(),"background400drawing save completes and marks only captured current revision clean")
	check(FileAccess.get_sha256(target+".backup")==before and FileAccess.get_sha256(input)==input_sha,"verified prior target backup and original input archive stay byte-identical")
	check(frames>100 and hashes()==original,"hundreds of actual app frames run without changing any400source pixels")
	var memory: Dictionary=app.raster_budget.sample();check(memory.owners==400 and memory.accounted_bytes<=memory.owner_limit_bytes,"manual background snapshot retains normal registered drawing admission")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pixels":original,"palette":app.palette}));print("HAS_BACKGROUND_LARGE_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"save_call_ms":call_ms,"snapshot_capture_ms":app.has_project.last_snapshot_capture_ms,"snapshot_worker_ms":app.has_project.last_snapshot_worker_ms,"save_total_ms":total_ms,"app_frames_during_save":frames,"max_observed_frame_gap_ms":max_gap_ms,"memory":memory}));await app.quit_studio();quit(0 if failures==0 else 1)
