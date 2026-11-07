extends "res://tests/movement_path_smoke.gd"
const Writer=preload("res://src/recovery_writer.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
class HeldWriter extends Writer:
 var gate:=Semaphore.new()
 var mutex:=Mutex.new()
 var calls:=0
 func persist(project: Dictionary,request: Dictionary) -> String:
  mutex.lock();calls+=1;mutex.unlock();gate.wait();return super.persist(project,request)
 func reached(count: int) -> bool:
  mutex.lock();var ok:=calls>=count;mutex.unlock();return ok
func _initialize() -> void:
 create_timer(120).timeout.connect(func():push_error("Recovery writer app watchdog");quit(2));call_deferred("run")
func wait_gate(held: HeldWriter,count: int) -> void:
 while not held.reached(count):await process_frame
func wait_recovery() -> void:
 while app.recovery_writer.busy() or app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
 await settled()
func run() -> void:
 folder=OS.get_cmdline_user_args()[0];app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.mode.select(0);app.change_mode(0);app.create_cel(false)
 var cel: Dictionary=Drawing.cel_at(app.layers[1],0);Drawing.edit_image(cel).image.fill(Color.CYAN);app.changed();var before:=Storage.image_hash(Drawing.image(cel));var manual:=folder.path_join("manual.has");app.has_project.save_file(manual,"packed");await wait_job();var manual_sha:=FileAccess.get_sha256(manual)
 app.changed();app.autosave_actions=3;var revision: int=app.recovery_revision;var held:=HeldWriter.new();app.recovery_writer=held;var started:=Time.get_ticks_usec();app.autosave_tick(true);var capture_ms:=(Time.get_ticks_usec()-started)/1000.0;await wait_gate(held,1)
 check(held.thread.is_alive() and app.checkpoint_revision!=revision and capture_ms<1000,"Checkpoint now returns while actual checkpoint file work is held in a background worker")
 var ticks:=0;var deadline:=Time.get_ticks_msec()+200
 while Time.get_ticks_msec()<deadline:ticks+=1;await process_frame
 check(ticks>=2 and held.thread.is_alive(),"actual application process/render frames continue during checkpoint serialization")
 var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.color.color=Color.RED;app.radius.value=8;app.canvas_input(press,Vector2(300,200));app.paint_segment(Vector2(330,200));press.pressed=false;app.canvas_input(press,Vector2(330,200));await settled();var edited:=Storage.image_hash(Drawing.image(cel));var pending: int=app.autosave_actions
 check(edited!=before and app.recovery_revision>revision and pending>3,"routed live brush editing remains usable while checkpoint worker owns its frozen image")
 app.set_frame(12);app.autosave_tick(true);check(app.recovery_checkpoint_requested and held.reached(1),"second explicit request queues protection without another concurrent writer")
 held.gate.post();await wait_gate(held,2)
 var checkpoint: String=app.recovery_root.path_join(app.recovery_session);var original:=Storage.load_project(checkpoint)
 check(not original.has("error") and Storage.image_hash(Drawing.image(original.layers[1].cels[0]))==before and original.editor.frame==0,"first background checkpoint retains exact captured pre-brush pixels and playhead")
 check(app.checkpoint_revision==revision and app.autosave_actions==pending-3 and held.thread.is_alive(),"first completion consumes only captured actions and preserves newer pending edits")
 held.gate.post();await wait_recovery();var newest:=Storage.load_project(checkpoint)
 check(app.checkpoint_revision==app.recovery_revision and app.autosave_actions==0 and newest.editor.frame==12 and Storage.image_hash(Drawing.image(newest.layers[1].cels[0]))==edited,"queued manual request protects newer drawing/playhead even with automatic recovery off")
 check(FileAccess.get_sha256(manual)==manual_sha and app.dirty,"background recovery never rewrites manual HAS or clears unsaved scene edits")
 held=HeldWriter.new();app.recovery_writer=held;app.changed();app.autosave_actions=2;app.autosave_tick(true);await wait_gate(held,1);var prior_checkpoint: int=app.checkpoint_revision;app.has_project.save_file(manual,"packed");await wait_job();app.changed();app.autosave_actions=1;held.gate.post();await wait_recovery()
 var resolved: Dictionary=preload("res://src/recovery.gd").read_json(checkpoint.path_join("resolved.json"))
 check(app.autosave_actions==1 and app.checkpoint_revision==prior_checkpoint and app.dirty and resolved.get("sha256")==FileAccess.get_sha256(checkpoint.path_join("project.json")),"manual Save during checkpoint resolves the late obsolete generation without consuming newer edits")
 manual_sha=FileAccess.get_sha256(manual)
 var previous:=FileAccess.get_sha256(checkpoint.path_join("project.json"));DirAccess.make_dir_absolute(checkpoint.path_join("project.json.tmp"));app.recovery_writer=Writer.new();app.changed();app.autosave_actions=1;app.autosave_tick(true);await wait_recovery()
 check(not app.recovery_writer_result.error.is_empty() and app.autosave_actions==1 and app.autosave_retry_due>Time.get_ticks_msec() and FileAccess.get_sha256(checkpoint.path_join("project.json"))==previous,"real blocked temporary preserves previous checkpoint and pending edits with retry feedback")
 DirAccess.remove_absolute(checkpoint.path_join("project.json.tmp"));held=HeldWriter.new();app.recovery_writer=held;app.autosave_tick(true);await wait_gate(held,1);DirAccess.make_dir_absolute(checkpoint.path_join("project.json.tmp"));app.new_project();await settled();var footer: String=app.recovery_status.text;held.gate.post();await wait_recovery()
 check(not app.recovery_writer_result.error.is_empty() and app.recovery_status.text==footer and app.checkpoint_revision==-1 and app.autosave_actions==0,"old session failure after New cannot alter the new document footer, checkpoint revision or schedule")
 DirAccess.remove_absolute(checkpoint.path_join("project.json.tmp"));app.create_cel(false);app.changed();held=HeldWriter.new();app.recovery_writer=held;app.autosave_tick(true);await wait_gate(held,1);app.has_project.save_file(manual,"packed");await wait_job();var final_checkpoint: String=app.recovery_root.path_join(app.recovery_session);await app.sequence_editor.finish();var releaser:=Thread.new();releaser.start(func():OS.delay_msec(100);held.gate.post());app.free();releaser.wait_to_finish()
 check(not held.busy(),"actual app teardown joins its owned checkpoint writer before freeing state")
 var final_resolved: Dictionary=preload("res://src/recovery.gd").read_json(final_checkpoint.path_join("resolved.json"))
 check(final_resolved.get("sha256")==FileAccess.get_sha256(final_checkpoint.path_join("project.json")),"closing after manual Save also resolves a late obsolete checkpoint after joining its writer")
 print("RECOVERY_WRITER_SMOKE "+JSON.stringify({"checks":checks,"failures":failures,"capture_ms":capture_ms,"heartbeat_frames":ticks}));quit(0 if failures==0 else 1)
