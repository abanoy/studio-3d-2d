extends SceneTree
const Recovery=preload("res://src/recovery.gd")
const Journal=preload("res://src/recovery_journal.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Recovery schedule watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func wait_job(job) -> void:
	while job.pid>0:await process_frame
	await settled()
func edit_root(app,id: String,value: float) -> void:
	app.world_selection.select_entity(id);app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[0].value=value;app.pose_editor.apply_numeric()
func scheduled(app) -> void:
	var until:=Time.get_ticks_msec()+5000
	while app.autosave_actions>0 and Time.get_ticks_msec()<until:await process_frame
	await settled()
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");root.add_child(app);await settled()
	app.has_project.cache_root=folder.path_join("cache")
	check(app.autosave_enabled.button_pressed and app.autosave_schedule.selected==0 and app.autosave_interval.value==1 and app.autosave_action_limit.value==25,"startup defaults to one-minute protection with a25-edit alternative")
	check(not app.autosave_schedule.is_visible_in_tree(),"Simple keeps scheduling controls hidden")
	app.autosave_enabled.button_pressed=false
	var actor:=folder.path_join("actor.glb");check(SceneIO.make_pose_fixture(actor)==OK and app.pose_editor.add_model(actor).is_empty(),"load original standard pose fixture")
	var id: String=app.last_import_id;var manual:=folder.path_join("manual.has");app.has_project.save_file(manual,"packed");await wait_job(app.has_project)
	check(not app.dirty and app.autosave_actions==0,"manual HAS save starts a fresh action count")
	var manual_hash:=FileAccess.get_sha256(manual)
	app.set_frame(12);app.set_frame(0);app.world_selection.clear();app.world_selection.select_entity(id);app.mode.select(0);app.change_mode(0)
	check(app.autosave_actions==0,"scrub, selection and workspace changes are not edits")
	app.advanced_toggle.button_pressed=true;app.advanced_toggle.pressed.emit();var dirty: bool=app.dirty;var history: int=app.history.size()
	app.autosave_schedule.select(1);app.autosave_schedule.item_selected.emit(1);app.autosave_action_limit.value=2;app.autosave_enabled.button_pressed=true
	check(app.autosave_action_controls.is_visible_in_tree() and not app.autosave_time_controls.visible and app.dirty==dirty and app.history.size()==history,"Advanced routes action scheduling without changing the project")
	app.create_cel(false);app.insert_key()
	check(app.autosave_actions==2,"cel creation and explicit camera key count as completed edits")
	var target: String=app.recovery_root.path_join(app.recovery_session).path_join("project.json")
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.button_mask=MOUSE_BUTTON_MASK_LEFT;press.pressed=true
	app.color.color=Color.CYAN;app.canvas_input(press,Vector2(800,400))
	for i in range(15):
		var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;app.canvas_input(motion,Vector2(810+i*4,410+i*2))
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.drawing and app.autosave_actions==2 and not FileAccess.file_exists(target),"a long unfinished stroke neither counts segments nor checkpoints mid-gesture")
	press.pressed=false;press.button_mask=0;app.canvas_input(press,Vector2(870,440))
	check(not app.drawing and app.autosave_actions==3,"stroke release counts exactly one completed edit")
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	check(FileAccess.file_exists(target) and app.autosave_actions==0 and app.checkpoint_revision==app.recovery_revision and app.dirty,"action threshold saves quietly without waiting for the time deadline or clearing dirty")
	var previous:=FileAccess.get_sha256(target)
	var unchanged_history: int=app.history.size();app.exposure.value=48;app.set_exposure();app.autosave_due=0;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.autosave_actions==0 and app.history.size()==unchanged_history and FileAccess.get_sha256(target)==previous,"same exposure creates no Undo entry and elapsed time does not trigger action-mode recovery")
	app.undo();check(app.autosave_actions==1 and app.history.size()==unchanged_history-1,"Undo reaches the preceding real stroke after a no-op exposure edit")
	app.redo();check(app.autosave_actions==2 and app.history.size()==unchanged_history,"Redo restores that real stroke and counts once")
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	app.layer_visibility.button_pressed=false;app.layer_visibility.button_pressed=true
	check(app.autosave_actions==2 and app.layers[app.active_layer].visible,"real layer visibility changes also count as completed edits")
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();previous=FileAccess.get_sha256(target)
	check(app.autosave_actions==0,"layer edits use the same automatic checkpoint path")
	app.undo();check(app.autosave_actions==1 and not app.layers[app.active_layer].visible,"successful layer visibility Undo counts once")
	app.redo();check(app.autosave_actions==2 and app.layers[app.active_layer].visible,"successful layer visibility Redo counts once")
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();check(app.autosave_actions==0 and FileAccess.get_sha256(target)!=previous,"Undo/Redo threshold produces a new recoverable state")
	app.autosave_action_limit.value=1;edit_root(app,id,0.25);previous=FileAccess.get_sha256(target)
	for property in ["drawing","navigating","playing","exporting"]:
		app.set(property,true);app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"ready action count defers while "+property);app.set(property,false)
	app.pose_editor.dragging=true;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);app.pose_editor.dragging=false
	app.timeline.moving_id=id;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);app.timeline.moving_id=""
	check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"pose and timeline drags retain pending actions")
	var modal:=AcceptDialog.new();app.add_child(modal);modal.popup_centered();app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"open dialog defers a ready edit threshold")
	modal.hide();modal.queue_free();await scheduled(app)
	check(app.autosave_actions==0 and app.checkpoint_revision==app.recovery_revision and FileAccess.get_sha256(target)!=previous and not app.has_dialog(app),"ordinary timer protects pending edits once the app becomes idle")
	app.autosave_enabled.button_pressed=false;edit_root(app,id,0.5);previous=FileAccess.get_sha256(target)
	await create_timer(1.1).timeout
	check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"disabled automatic protection retains rather than consumes pending edits")
	app.autosave_enabled.button_pressed=true;await scheduled(app)
	check(app.autosave_actions==0 and FileAccess.get_sha256(target)!=previous,"re-enabling protects an already reached edit threshold")
	app.autosave_action_limit.value=100;app.autosave_enabled.button_pressed=false;edit_root(app,id,0.75);app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	check(app.autosave_actions==0 and app.checkpoint_revision==app.recovery_revision,"explicit Checkpoint now bypasses disabled scheduling and its threshold")
	app.autosave_enabled.button_pressed=true;app.autosave_action_limit.value=1;edit_root(app,id,1.0);previous=FileAccess.get_sha256(target)
	DirAccess.make_dir_recursive_absolute(target+".tmp");app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);var retry: int=app.autosave_retry_due
	check(app.autosave_actions==1 and retry>Time.get_ticks_msec() and FileAccess.get_sha256(target)==previous,"failed write retains edits and last valid checkpoint with a retry delay")
	app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);check(app.autosave_retry_due==retry and FileAccess.get_sha256(target)==previous,"retry backoff prevents repeated writes every timer tick")
	check("Edits are pending" in app.recovery_status.text and "retry after 30 seconds" in app.status.text,"failed checkpoint explains pending edits and the idle retry")
	DirAccess.remove_absolute(target+".tmp")
	app.autosave_schedule.select(0);app.autosave_due=Time.get_ticks_msec()+600000
	app.autosave_retry_due=Time.get_ticks_msec()-1;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled()
	check(app.autosave_actions==0 and FileAccess.get_sha256(target)!=previous,"successful retry consumes pending edits only after commit")
	dirty=app.dirty;history=app.history.size();app.autosave_schedule.select(0);app.autosave_schedule.item_selected.emit(0);app.autosave_interval.value=0.5
	check(app.autosave_time_controls.visible and not app.autosave_action_controls.visible and absi(app.autosave_due-Time.get_ticks_msec()-30000)<=500 and app.dirty==dirty and app.history.size()==history,"time scheduling exposes minutes and retains project/history state")
	edit_root(app,id,1.25);previous=FileAccess.get_sha256(target);app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"time mode waits for its actual deadline")
	app.autosave_due=0;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();check(app.autosave_actions==0 and FileAccess.get_sha256(target)!=previous,"elapsed timed protection still uses the same valid checkpoint path")
	edit_root(app,id,1.5);app.autosave_schedule.select(1);app.autosave_schedule.item_selected.emit(1);app.autosave_action_limit.value=2;previous=FileAccess.get_sha256(target);app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app)
	check(app.autosave_actions==1 and FileAccess.get_sha256(target)==previous,"changing schedule does not discard pending edit count")
	app.autosave_action_limit.value=1;app.autosave_tick();await preload("res://tests/recovery_wait.gd").checkpoint(app);await settled();check(app.autosave_actions==0,"lower threshold can protect existing pending work")
	app.autosave_action_limit.value=7;app.autosave_interval.value=2;app.new_project();app.has_project.open_file(manual);await wait_job(app.has_project)
	check(app.autosave_actions==0 and app.autosave_schedule.selected==1 and app.autosave_action_limit.value==7 and app.autosave_interval.value==2,"New/Open reset pending actions but preserve in-session scheduling preferences")
	edit_root(app,id,2);app.has_project.save_file(folder.path_join("new-save.has"),"packed");edit_root(app,id,3);await wait_job(app.has_project)
	check(app.dirty and app.autosave_actions==2,"edits made after a save snapshot remain dirty and counted")
	app.has_project.save_current();await wait_job(app.has_project)
	check(not app.dirty and app.autosave_actions==0 and FileAccess.get_sha256(manual)==manual_hash,"successful exact-revision Save resets counts and preserves the original HAS")
	app.autosave_schedule.select(1);app.autosave_schedule.item_selected.emit(1);app.get_window().size=Vector2i(1200,760);await settled();app.inspector_scroll.ensure_control_visible(app.autosave_action_limit);await settled()
	check(app.inspector_scroll.get_global_rect().encloses(app.autosave_schedule.get_global_rect()) and app.inspector_scroll.get_global_rect().encloses(app.autosave_action_limit.get_global_rect()),"schedule and edit threshold remain reachable in a1200px app window")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("schedule-ui.png"))
	var result:={"checks":checks,"failures":failures,"folder":folder,"manual_sha256":manual_hash}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(result));file.close();print("RECOVERY_SCHEDULE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
