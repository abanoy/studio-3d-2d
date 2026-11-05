extends SceneTree
const Preview=preload("res://src/recovery_preview.gd")
const Journal=preload("res://src/recovery_journal.gd")
const Recovery=preload("res://src/recovery.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const SceneIO=preload("res://src/scene3d.gd")
class HeldPreview extends Preview:
	var mutex:=Mutex.new()
	var release:=Semaphore.new()
	var entered:=false
	var fail:=false
	func reached() -> bool:
		mutex.lock();var result:=entered;mutex.unlock();return result
	func persist(folder: String,digest: String,image: Image) -> String:
		mutex.lock();var first:=not entered;entered=true;mutex.unlock()
		if first:release.wait()
		return "Injected old preview failure" if fail else super.persist(folder,digest,image)
class FailedPreview extends Preview:
	func persist(folder: String,digest: String,image: Image) -> String:
		var blocked:=folder.path_join(Journal.preview_name(Journal.sha(image.save_png_to_buffer())))+".tmp"
		DirAccess.make_dir_recursive_absolute(blocked)
		var error:=super.persist(folder,digest,image)
		DirAccess.remove_absolute(blocked)
		return error
var checks:=0
var failures:=0
var held: HeldPreview
func _initialize() -> void:
	create_timer(100).timeout.connect(func():if held:held.release.post();push_error("Recovery preview watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func wait_preview(app) -> void:
	await settled()
	var until:=Time.get_ticks_msec()+5000
	while app.recovery_preview.busy() and Time.get_ticks_msec()<until:await process_frame
	check(not app.recovery_preview.busy(),"preview completes without waiting in ordinary app processing")
func wait_gate() -> void:
	var until:=Time.get_ticks_msec()+5000
	while not held.reached() and Time.get_ticks_msec()<until:await process_frame
	check(held.reached() and held.thread.is_alive(),"real worker reaches its controlled file-write boundary")
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var fixture:=folder.path_join("actor.glb")
	check(SceneIO.make_pose_fixture(fixture)==OK and app.pose_editor.add_model(fixture).is_empty(),"load shared standard skinned fixture")
	var fixture_hash:=FileAccess.get_sha256(fixture)
	app.mode.select(0);app.change_mode(0);app.create_cel(false)
	var cel: Dictionary=Drawing.cel_at(app.layers[1],0);cel.image.fill_rect(Rect2i(0,0,384,216),Color.CYAN);app.changed()
	var manual:=folder.path_join("manual.has");app.has_project.save_file(manual,"packed")
	while app.has_project.pid>0:await process_frame
	await settled();var manual_hash:=FileAccess.get_sha256(manual)
	check(not app.dirty and FileAccess.file_exists(manual),"original manual HAS saved independently")
	app.changed();var keys: Array=app.keys.duplicate(true);var world: Dictionary=app.renderer.world_state();var pixels:=Storage.image_hash(cel.image)
	held=HeldPreview.new();app.recovery_preview=held;app.autosave_tick(true);await wait_gate()
	var checkpoint: String=app.recovery_root.path_join(app.recovery_session);var digest:=FileAccess.get_sha256(checkpoint.path_join("project.json"));var revision: int=app.checkpoint_revision
	check(Journal.entries(checkpoint).size()==1 and Journal.entries(checkpoint)[0].preview.is_empty(),"valid checkpoint exists before its slow preview finishes")
	check(app.recovery_preview.start(checkpoint,digest,Image.new(),[])=="A recovery preview is already being prepared.","only one preview writer can own the journal")
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.button_mask=MOUSE_BUTTON_MASK_LEFT;press.pressed=true
	app.color.color=Color.RED;app.canvas_input(press,Vector2(800,400));press.pressed=false;press.button_mask=0;app.canvas_input(press,Vector2(800,400))
	cel.image.fill_rect(Rect2i(0,0,384,216),Color.RED);app.changed();var after:=Storage.image_hash(cel.image)
	app.set_frame(12);var pending: int=app.autosave_actions;app.autosave_tick(true)
	check(not app.drawing and pending>0 and app.recovery_checkpoint_requested and app.checkpoint_revision==revision and FileAccess.get_sha256(checkpoint.path_join("project.json"))==digest and app.autosave_actions==pending,"editing stays usable while an explicit checkpoint queues without consuming edits")
	var frames:=0;var clock:=Time.get_ticks_msec()
	for i in range(20):await process_frame;frames+=1
	await RenderingServer.frame_post_draw
	check(frames==20 and Time.get_ticks_msec()>clock and app.canvas.overlay.get_image().get_pixel(80,80)==Color.RED and held.thread.is_alive(),"actual app frames and updated drawing continue while file work is held")
	app.toggle_play();await create_timer(0.3).timeout;await RenderingServer.frame_post_draw
	check(app.playing and app.frame>12 and held.thread.is_alive(),"real timeline playback advances while the background file boundary is held")
	app.stop();app.set_frame(12)
	check(app.keys==keys and app.renderer.world_state()==world and pixels!=after,"background work never edits camera keys or native model state")
	held.release.post();await wait_preview(app)
	var result: Dictionary=app.recovery_preview_result
	check(result.background_thread and result.error.is_empty(),"resize, blend, PNG and journal commit complete on the background thread")
	check(not app.autosave_enabled.button_pressed and not app.recovery_checkpoint_requested and app.checkpoint_revision==app.recovery_revision and Journal.entries(checkpoint).size()==2,"queued explicit request protects later edits automatically even with automatic recovery off")
	check(Journal.preview(checkpoint,Journal.entries(checkpoint)[-1].preview).get_pixel(8,8)==Color.CYAN and Storage.image_hash(cel.image)==after,"preview uses the captured paint rather than later mutable cel pixels")
	app.recovery_preview=Preview.new();app.autosave_tick(true);await wait_preview(app)
	var records:=Journal.entries(checkpoint)
	check(records.size()==2 and records[0].sha256!=digest and records[1].sha256==digest and Journal.preview(checkpoint,records[0].preview).get_pixel(8,8)==Color.RED,"waiting checkpoint commits afterward without losing the older preview/catalog entry")
	check(app.autosave_actions==0 and app.checkpoint_revision==app.recovery_revision and app.dirty,"pending edits reset only after the next checkpoint succeeds")
	app.recovery_preview=FailedPreview.new();cel.image.fill_rect(Rect2i(0,0,384,216),Color.YELLOW);app.changed();app.autosave_tick(true);await wait_preview(app)
	check(not app.recovery_preview_result.error.is_empty() and app.recovery_status.text=="Recovery saved; preview unavailable" and Storage.load_project(checkpoint).has("video"),"real preview file failure leaves a valid recoverable checkpoint and quiet feedback")
	var capture_ms: float=app.last_recovery_preview_capture_ms;var worker_ms: float=app.last_recovery_preview_worker_ms
	held=HeldPreview.new();held.fail=true;app.recovery_preview=held;app.changed();app.autosave_tick(true);await wait_gate()
	var old_session: String=app.recovery_session;app.new_project();var text: String=app.recovery_status.text;var new_world: Dictionary=app.renderer.world_state();var new_keys: Array=app.keys.duplicate(true)
	check(app.recovery_session!=old_session and not app.dirty and app.recovery_preview.busy(),"New can complete while an older session preview is still working")
	held.release.post();await wait_preview(app)
	check(app.recovery_status.text==text and app.renderer.world_state()==new_world and app.keys==new_keys and not app.dirty,"old-session preview failure cannot replace New state or its footer")
	check(FileAccess.get_sha256(manual)==manual_hash and FileAccess.get_sha256(fixture)==fixture_hash,"worker lifecycle preserves original manual HAS and source geometry")
	var teardown:=Preview.new();var source_image:=Image.create(256,144,false,Image.FORMAT_RGBA8);source_image.fill(Color.CYAN)
	check(teardown.start(checkpoint,digest,source_image,[]).is_empty(),"start a final bounded worker for teardown cleanup")
	app.recovery_preview=teardown;app.free()
	check(not teardown.busy() and Journal.preview(checkpoint,Journal.entries(checkpoint)[-1].preview)!=null,"actual app teardown joins its worker and releases the thread")
	var report:={"checks":checks,"failures":failures,"folder":folder,"capture_ms":capture_ms,"worker_ms":worker_ms,"responsive_frames":frames,"manual_sha256":manual_hash}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("RECOVERY_PREVIEW "+JSON.stringify(report));held=null;quit(0 if failures==0 else 1)
