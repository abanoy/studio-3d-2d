extends "res://tests/large_project_smoke.gd"
const Loader=preload("res://src/has_project_loader.gd")
class HeldLoader extends Loader:
	var entered:=Semaphore.new()
	var release:=Semaphore.new()
	func decode(request: Dictionary) -> Dictionary:
		entered.post();release.wait();return super.decode(request)
var frames:=0
var measuring:=false
var last_tick:=0
var max_gap_ms:=0.
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Background Open watchdog");quit(2));process_frame.connect(tick);call_deferred("run")
func tick() -> void:
	if not measuring:return
	var now:=Time.get_ticks_usec()
	if last_tick>0:max_gap_ms=maxf(max_gap_ms,(now-last_tick)/1000.)
	last_tick=now;frames+=1
func held_open(input: String):
	var loader:=HeldLoader.new();app.has_project.project_loader=loader;app.has_project.open_file(input)
	while not loader.entered.try_wait():await process_frame
	return loader
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var input: String=args[1];var original_sha:=FileAccess.get_sha256(input)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var starting_layers=app.layers;var held=await held_open(input)
	check(app.has_project.pid>0 and app.exporting and is_same(app.layers,starting_layers),"archive extraction starts private decoding without replacing live document")
	for n in range(20):await process_frame
	check(held.busy() and app.has_project.pid>0 and is_same(app.layers,starting_layers),"held decode leaves progress responsive and old document untouched")
	app.has_project.cancel();held.release.post();await wait_job()
	check(is_same(app.layers,starting_layers) and app.has_project.path.is_empty() and not held.busy() and not app.exporting,"Cancel drains decoder and preserves original project identity and layers")
	app.has_project.project_loader=Loader.new();var began:=Time.get_ticks_msec();measuring=true;last_tick=Time.get_ticks_usec();app.has_project.open_file(input);await wait_job();measuring=false;var total_ms:=Time.get_ticks_msec()-began
	check(app.has_project.path==input and total()==400 and not app.exporting,"ordinary Open installs all400validated drawing owners after joining worker")
	check(frames>30 and app.has_project.last_load_worker_ms>0,"actual UI frames advance during400drawing Open")
	var load_ms: float=app.has_project.last_load_worker_ms;var install_ms: float=app.has_project.last_install_ms;var original:=hashes()
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[2]));check(original==expected.pixels,"all400loaded pixel hashes exactly match committed save fixture")
	app.mode.select(0);app.change_mode(0);var picture: Image=await app.renderer.capture(app.keys,app.layers,137,true)
	check(picture.get_data()==Image.load_from_file(args[3]).get_data(),"main-thread runtime installation reproduces exact final GPU composition")
	var before_layers=app.layers;var before_path: String=app.has_project.path
	held=await held_open(input);app.changed();held.release.post();await wait_job()
	check(is_same(app.layers,before_layers) and app.dirty and app.has_project.path==before_path,"newer live revision refuses late Open result without losing edits")
	held=await held_open(input);app.has_project.cancel();held.release.post();await wait_job()
	check(is_same(app.layers,before_layers) and hashes()==original and app.has_project.path==before_path,"Cancel over populated document preserves400owners and identity")
	held=await held_open(input);var cache: String=app.has_project.pending.folder;FileAccess.open(cache.path_join("project.json"),FileAccess.WRITE).store_string("{broken");held.release.post();await wait_job()
	check(is_same(app.layers,before_layers) and hashes()==original and app.has_project.path==before_path,"corrupt staged manifest refuses transaction without altering live project")
	held=await held_open(input);app.exporting=false;app.new_project();var fresh=app.layers;held.release.post();await wait_job()
	check(is_same(app.layers,fresh) and app.has_project.path.is_empty(),"late previous Open cannot install into a new document")
	check(FileAccess.get_sha256(input)==original_sha,"all attempts preserve original archive bytes")
	print("HAS_BACKGROUND_OPEN "+JSON.stringify({"checks":checks,"failures":failures,"total_ms":total_ms,"load_worker_ms":load_ms,"main_install_ms":install_ms,"app_frames":frames,"max_observed_frame_gap_ms":max_gap_ms}));await app.quit_studio();quit(0 if failures==0 else 1)
