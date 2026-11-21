extends SceneTree
const Fixture=preload("res://tests/generated_secondary_fixture.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(110).timeout.connect(func():push_error("Generated settling editor watchdog");quit(2))
	call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func settle() -> void:
	for i in range(4):await process_frame
func active() -> RefCounted:return app.renderer.active_model()
func wait_project() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	if args.size()!=1 or DisplayServer.get_name()!="headless":quit(2);return
	var folder: String=args[0];root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json")
	root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var fixture: String=folder.path_join("generated.glb")
	check(Fixture.create(fixture)==OK,"generated-only helper fixture is written")
	var original_sha: String=FileAccess.get_sha256(fixture)
	check(app.pose_editor.add_model(fixture).is_empty(),"ordinary Add model accepts generated helper")
	await settle()
	var ui=app.physics_editor.generated_motion_editor;ui.sync()
	var original_data: Dictionary=active().data.duplicate(true);var original_rig: PackedByteArray=var_to_bytes(active().root.get_meta("has_secondary_rig"))
	check(ui.choice.visible and not ui.choice.disabled and ui.choice.selected==0,"selected generated helper defaults to visible Keep hair shape")
	var history: int=app.history.size();ui.change(1);await settle()
	check(Motion.setting(active().data).get("mode")=="natural" and app.history.size()==history+1,"Natural gravity is one ordinary world-history edit")
	var authored: Dictionary=active().data.duplicate(true);authored.metadata.erase(Motion.KEY)
	check(authored==original_data and var_to_bytes(active().root.get_meta("has_secondary_rig"))==original_rig,"setting preserves model keys source and original helper declaration")
	app.undo();await settle();check(Motion.setting(active().data).mode=="keep_shape","Undo restores absent historical setting")
	app.redo();await settle();check(Motion.setting(active().data).mode=="natural","Redo restores Natural gravity")
	ui.sync();ui.popup_context=ui.context();app.recovery_revision+=1;history=app.history.size();ui.change(0)
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history,"stale popup cannot edit a later world revision")
	ui.sync();app.physics_editor.pending["another-model"]={};ui.change(0);app.physics_editor.pending.clear()
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history,"same-frame pending owner prevents global restore")
	ui.sync();app.physics_editor.simulations["another-model"]=null;ui.change(0);app.physics_editor.simulations.clear()
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history,"another live model cannot be silently disposed by this setting")
	ui.sync();app.source_import.bundle_active=true;ui.change(0);app.source_import.bundle_active=false
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history,"queued character import blocks world replacement")
	ui.sync();app.sequence_editor.installing=true;ui.change(0);app.sequence_editor.installing=false
	check(Motion.setting(active().data).mode=="natural" and app.history.size()==history,"sequence installation blocks stale setting callbacks")
	ui.sync();var profile: Dictionary=active().root.get_meta("has_secondary_rig").duplicate(true);var native_profile: Dictionary=profile.duplicate(true);native_profile.source_family="VRM1";active().root.set_meta("has_secondary_rig",native_profile);ui.sync()
	check(not ui.choice.visible,"native imported physics never exposes generated settling override")
	active().root.set_meta("has_secondary_rig",profile);ui.sync()
	check(ui.choice.size.x>=145 and ui.choice.get_global_rect().end.x<=root.size.x,"ordinary desktop layout retains the complete preset control")
	var packed: String=folder.path_join("settled.has");var expected: Dictionary={"id":active().data.id,"sha":active().data.sha256,"setting":Motion.setting(active().data),"fixture_sha":original_sha}
	app.has_project.save_file(packed,"packed");await wait_project()
	check(FileAccess.file_exists(packed) and FileAccess.get_sha256(fixture)==original_sha,"packed save completes without changing generated source")
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(expected));file.close()
	app.new_project();await settle();app.has_project.open_file(packed);await wait_project()
	check(app.renderer.world_runtime.order.size()==1,"ordinary Open restores packed helper model")
	app.world_selection.select_entity(expected.id,false);await settle();ui.sync()
	check(active()!=null and active().data.sha256==expected.sha and Motion.setting(active().data)==expected.setting,"saved Natural setting survives New and ordinary Open")
	ui.change(0);await settle();check(not active().data.metadata.has(Motion.KEY),"Keep shape removes optional override instead of rewriting stored source tuning")
	print("GENERATED_SECONDARY_EDITOR "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"actual_app":true,"source_preserved":FileAccess.get_sha256(fixture)==original_sha}))
	await app.quit_studio();quit(0 if failures==0 else 1)
