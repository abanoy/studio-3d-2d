extends "res://tests/walking_path_smoke.gd"
const Writer=preload("res://src/has_snapshot_writer.gd")
class HeldWriter extends Writer:
	var entered:=Semaphore.new()
	var release:=Semaphore.new()
	func persist(project: Dictionary,request: Dictionary) -> String:
		entered.post()
		while not release.try_wait() and not FileAccess.file_exists(request.cancel):OS.delay_msec(1)
		return super.persist(project,request)
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Background HAS watchdog");quit(2));call_deferred("run")
func hold() -> HeldWriter:
	var worker:=HeldWriter.new();app.has_project.snapshot_writer=worker;return worker
func entered(worker: HeldWriter) -> void:
	while not worker.entered.try_wait():await process_frame
	await settled()
func paint(color: Color) -> void:
	var image: Image=Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image;image.fill_rect(Rect2i(40,40,80,40),color);Drawing.touch(image);app.changed()
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("reader-recovery" if "--read" in args else "recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	var packed:=folder.path_join("Background.has")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for filename in ["Background.has","Linked.has"]:
			app.has_project.open_file(folder.path_join(filename));await wait_job();check(app.has_project.path==folder.path_join(filename) and Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"cold "+filename+" restores detached snapshot pixels")
			check(Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm and app.palette==expected.palette,"cold "+filename+" preserves snapshot audio and palette references")
		check((await app.renderer.capture(app.keys,app.layers,12,true)).get_data()==Image.load_from_file(folder.path_join("snapshot.png")).get_data(),"cold final picture repeats background snapshot exactly")
		print("HAS_BACKGROUND_READ "+JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	app.new_project();app.show_project_options();await settled();check(app.project_canvas.apply("540p").is_empty(),"native540snapshot fixture uses ordinary canvas setting");app.project_options.hide();app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);paint(Color.RED);app.palette=[{"name":"Captured","rgba":"ff0000ff"}];app.palette_editor.refresh(true);check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"real voice joins independent snapshot pixels")
	app.has_project.save_file(packed,"packed");await wait_job();check(FileAccess.file_exists(packed) and not app.dirty,"normal initial asynchronous Save finishes through existing PID wait API");var original:=FileAccess.get_sha256(packed);var capture_before: Dictionary=app.video.duplicate(true)
	paint(Color.BLUE);var worker:=hold();var began:=Time.get_ticks_msec();app.has_project.save_file(packed,"packed");var call_ms:=Time.get_ticks_msec()-began;await entered(worker);var live_pid: int=app.has_project.pid
	check(live_pid>0 and OS.is_process_running(live_pid) and app.exporting and app.has_project.progress.visible and not FileAccess.file_exists(app.has_project.pending.snapshot_ready),"real packer waits behind unpublished snapshot while progress stays alive")
	var counted:=0
	for n in range(20):await process_frame;counted+=1
	check(counted==20 and FileAccess.get_sha256(packed)==original and app.video==capture_before,"held snapshot processes real frames without replacing old good save")
	var cancel_button: Button
	for button in app.has_project.progress.find_children("*","Button",true,false):
		if button.text=="Cancel":cancel_button=button;break
	await click(cancel_button);await wait_job();check(FileAccess.get_sha256(packed)==original and app.dirty and not app.exporting and not worker.busy(),"actual Cancel drains snapshot and packer while preserving prior good HAS")
	worker=hold();app.has_project.save_file(packed,"packed");await entered(worker);var captured_sha:=Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)));var revision: int=app.recovery_revision
	paint(Color.GREEN);app.palette.append({"name":"Newer","rgba":"00ff00ff"});app.palette_editor.refresh(true);app.changed();worker.release.post();await wait_job()
	check(app.dirty and app.recovery_revision>revision and app.has_project.path==packed,"late save completion retains newer edits as unsaved")
	var loaded:=Storage.load_project(app.has_project.pending.folder);check(not loaded.has("error") and Storage.image_hash(Drawing.image(loaded.layers[1].cels[0]))==captured_sha and loaded.palette.size()==1,"published snapshot retains captured COW pixels/metadata rather than later edits")
	check(FileAccess.get_sha256(packed)!=original and FileAccess.get_sha256(packed+".backup")==original,"completed background save preserves exact prior verified backup")
	# Reopen the captured saved state, then save it as linked through the same worker.
	app.has_project.snapshot_writer=Writer.new();app.has_project.open_file(packed);await wait_job();check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==captured_sha and app.palette.size()==1,"normal Open reads background-saved captured state")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,12,true);picture.save_png(folder.path_join("snapshot.png"));var pcm:=Storage.RasterReader.digest_bytes(app.audio_mix.pcm)
	app.has_project.save_file(folder.path_join("Linked.has"),"linked");await wait_job();check(FileAccess.file_exists(folder.path_join("Linked.has")),"background snapshot publishes required linked audio references")
	var current:=FileAccess.get_sha256(packed);var old_cache: String=app.has_project.cache_root;var blocked:=folder.path_join("blocked-cache");DirAccess.make_dir_recursive_absolute(blocked.path_join("work_%d/project.json.tmp"%OS.get_process_id()));app.has_project.cache_root=blocked;app.changed();app.has_project.save_file(packed,"packed");await wait_job();app.has_project.cache_root=old_cache
	check(FileAccess.get_sha256(packed)==current and app.dirty and not app.exporting and not app.has_project.snapshot_writer.busy(),"failed snapshot refuses before packaging and preserves good target")
	# A programmatic context replacement cannot attach a late old save to New.
	worker=hold();var previous_session: String=app.recovery_session;app.has_project.save_file(folder.path_join("Previous.has"),"packed");await entered(worker);app.exporting=false;app.new_project();var session: String=app.recovery_session;var new_world=app.renderer.world_runtime.root;var status: String=app.status.text;worker.release.post();await wait_job()
	check(session!=previous_session and app.recovery_session==session and app.renderer.world_runtime.root==new_world and app.has_project.path.is_empty() and not app.dirty,"late previous-document save never attaches identity or clears New state")
	check(FileAccess.file_exists(folder.path_join("Previous.has")),"previous captured document still saves independently")
	# Reopen and test actual window-close cancellation while snapshot is held.
	app.has_project.snapshot_writer=Writer.new();app.has_project.open_file(packed);await wait_job();worker=hold();app.has_project.save_file(packed,"packed");await entered(worker);app._notification(Node.NOTIFICATION_WM_CLOSE_REQUEST);await wait_job();check(app.is_inside_tree() and not worker.busy() and FileAccess.get_sha256(packed)==current,"window close cancels and drains active snapshot without losing prior save")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"paint":captured_sha,"pcm":pcm,"palette":[{"name":"Captured","rgba":"ff0000ff"}]}))
	var capture_ms: float=app.has_project.last_snapshot_capture_ms;var worker_ms: float=app.has_project.last_snapshot_worker_ms
	worker=hold();app.has_project.save_file(packed,"packed");await entered(worker);var closing_pid: int=app.has_project.pid;app.queue_free();await settled()
	check(not is_instance_valid(app) and not worker.busy() and FileAccess.get_sha256(packed)==current,"teardown joins cancelled snapshot without touching prior good save")
	var alive:=true;var deadline:=Time.get_ticks_msec()+5000
	while alive and Time.get_ticks_msec()<deadline:alive=OS.is_process_running(closing_pid);await process_frame
	check(not alive,"cancelled private packer exits after snapshot teardown")
	print("HAS_BACKGROUND_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"held_call_ms":call_ms,"capture_ms":capture_ms,"worker_ms":worker_ms}));quit(0 if failures==0 else 1)
