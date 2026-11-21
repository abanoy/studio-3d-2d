extends SceneTree
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
var app
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+label)
func _initialize() -> void:
	create_timer(35).timeout.connect(func():push_error("Easing app CPU watchdog");quit(2))
	call_deferred("run")
func run() -> void:
	var folder:=OS.get_cmdline_user_args()[0]
	var prefs:=ConfigFile.new()
	prefs.set_value("display","theme","light" if "--classic" in OS.get_cmdline_user_args() else "neon")
	prefs.set_value("display","percent",100)
	prefs.save(folder.path_join("prefs.cfg"))
	app=load("res://main.tscn").instantiate()
	app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json")
	root.add_child(app)
	for i in range(3):await process_frame
	app.home.hide();app.autosave_enabled.button_pressed=false
	app.set_advanced("--advanced" in OS.get_cmdline_user_args())
	app.mode.select(1);app.change_mode(1)
	app.keys=[Timeline.key(0,Vector3(0,1,3),Quaternion.IDENTITY,55.,"linear"),Timeline.key(10,Vector3(10,1,3),Quaternion.IDENTITY,55.,"linear"),Timeline.key(20,Vector3(20,1,3),Quaternion.IDENTITY,55.,"linear")]
	app.history.clear();app.redo_history.clear();app.history_bytes=0;app.set_frame(2)
	var editor=app.camera_easing
	check(is_instance_valid(editor) and editor.app==app and editor.panel.get_parent()==app.camera_section,"actual_app_setup_binds_camera_editor")
	check(not editor.details.visible,"recipe_controls_start_collapsed")
	editor.open()
	check(editor.valid_context() and editor.details.visible,"actual_camera_editor_opens_current_scene")
	check(editor.panel.is_visible_in_tree(),"camera_timing_controls_visible_in_requested_workspace")
	var keys: Array=app.keys.duplicate(true);var history: int=app.history.size();var revision: int=app.recovery_revision
	var world: Dictionary=app.current_world().duplicate(true);var layers: PackedByteArray=var_to_bytes(app.layers)
	check(editor.set_controls_at(0,0.,1.).is_empty(),"actual_editor_accepts_recipe")
	check(editor.preview().is_empty() and editor.preview_active(),"actual_editor_starts_temporary_preview")
	check(app.keys==keys and app.history.size()==history and app.recovery_revision==revision,"actual_preview_preserves_keys_history_dirty_revision")
	var expected: Dictionary=editor.sample_preview(keys,2)
	check(app.renderer.camera.position.is_equal_approx(expected.position),"actual_renderer_evaluates_temporary_sampler")
	app.set_frame(3);expected=editor.sample_preview(keys,3)
	check(app.renderer.camera.position.is_equal_approx(expected.position),"scene_mode_set_frame_refreshes_active_recipe")
	app.renderer.evaluate(keys,3,false)
	check(app.renderer.camera.position.is_equal_approx(Timeline.sample(keys,3).position),"explicit_authored_evaluation_bypasses_preview")
	app.exporting=true;app.renderer.evaluate(keys,3);app.exporting=false
	check(app.renderer.camera.position.is_equal_approx(Timeline.sample(keys,3).position),"actual_export_state_bypasses_temporary_sampler")
	editor.discard()
	check(not editor.preview_active() and app.keys==keys and app.history.size()==history and app.renderer.camera.position.is_equal_approx(Timeline.sample(keys,3).position),"discard_restores_actual_authored_camera")
	editor.open();editor.set_controls_at(0,0.,1.);editor.preview()
	check(editor.bake_preview().is_empty() and app.keys.size()==12 and app.history.size()==history+1,"actual_bake_installs_one_history_command")
	var baked: Array=app.keys.duplicate(true);var authored_kept:=true
	for original in keys:
		var matching: Array=app.keys.filter(func(key):return key.frame==original.frame)
		authored_kept=authored_kept and matching.size()==1 and matching[0]==original
	check(authored_kept,"actual_bake_preserves_every_original_key_dictionary")
	check(app.history[-1].type=="keys" and app.history[-1].before==keys and app.history[-1].after==baked,"actual_history_contains_complete_before_after")
	app.undo();check(app.keys==keys,"real_app_undo_restores_original_keys")
	app.redo();check(app.keys==baked,"real_app_redo_restores_baked_keys")
	check(app.current_world()==world and var_to_bytes(app.layers)==layers,"actual_bake_undo_redo_preserve_world_and_cels")
	editor.open();editor.set_controls_at(0,0.,1.);editor.preview();app.keys[1].fov=77.
	check(not editor.preview_active() and editor.sample_preview(app.keys,2).is_empty(),"actual_authored_edit_invalidates_temporary_recipe")
	editor.open();app.playing=true
	check(not editor.set_controls_at(0,0.,1.).is_empty(),"actual_playback_refuses_recipe_edit")
	app.playing=false;editor.discard();app.keys=keys.duplicate(true);app.keys[0].interpolation="hold";editor.open()
	check(not editor.set_controls_at(0,0.,1.).is_empty() and app.keys[0].interpolation=="hold","actual_hold_segment_refuses_nonzero_timing")
	editor.discard();app.keys=keys.duplicate(true);editor.open();editor.set_controls_at(0,0.,1.);editor.preview();app.new_project()
	check(not editor.preview_active() and not editor.valid_context(),"new_project_invalidates_previous_recipe")
	var result:={"checks":checks,"failures":failures,"real_app_undo_tested":true,"headless_only":true,"pixels_or_export_tested":false,"application_adopted":false}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("EASING435_APP_HEADLESS ",JSON.stringify(result))
	await app.quit_studio();quit(0 if failures==0 else 1)
