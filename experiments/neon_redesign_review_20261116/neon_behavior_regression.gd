extends SceneTree
# UNPARSED/UNRUN. Root stages under this same experiment path in an isolated project.
# Real UI/input and world lifecycle; only Save/fullscreen actions are counted so a
# broken dispatch cannot touch an external save location or change desktop mode.
const SCRIPT := "res://experiments/neon_redesign_review_20261116/neon_behavior_regression.gd"
const Model = preload("res://src/model.gd")
const Airflow = preload("res://src/airflow.gd")
const StudioTheme = preload("res://src/studio_theme.gd")
class ProbeApp extends "res://src/app.gd":
	var observed_save_calls := 0
	var observed_fullscreen_calls := 0
	func save() -> void: observed_save_calls += 1
	func toggle_fullscreen() -> void: observed_fullscreen_calls += 1

var app
var named: Dictionary = {}
var failures := 0
var pointer_presses := 0
const EXPECTED_CHECKS := 32

func _initialize() -> void:
	create_timer(100).timeout.connect(func(): push_error("Neon behavior regression watchdog"); quit(2))
	call_deferred("run")

func check(name: String, ok: bool) -> void:
	if named.has(name): push_error("Duplicate check name"); quit(3); return
	named[name] = ok
	if not ok: failures += 1
	print(("PASS " if ok else "FAIL ")+"neon_behavior."+name)

func settled() -> void:
	for unused in range(4): await process_frame
	await RenderingServer.frame_post_draw

func click_point(point: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = point
	root.push_input(motion,true)
	for pressed in [true,false]:
		var event := InputEventMouseButton.new()
		event.position = point; event.button_index = MOUSE_BUTTON_LEFT; event.pressed = pressed
		root.push_input(event,true)
		await settled()

func find_button(node: Node, caption: String) -> Button:
	if node is Button and node.text == caption: return node
	for child in node.get_children():
		var found := find_button(child,caption)
		if found: return found
	return null

func count_canvas_press(event: InputEvent, _point: Vector2) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT: pointer_presses += 1

func send_f11(ctrl := false) -> void:
	var event := InputEventKey.new()
	event.pressed = true; event.keycode = KEY_F11; event.ctrl_pressed = ctrl
	app._unhandled_key_input(event)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: push_error("One root-owned regression job required"); quit(2); return
	var job = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not job is Dictionary or job.get("format") != "has_neon_behavior_regression_job_1" or job.get("phase") != "ROOT_APPROVED_NEON_BEHAVIOR" or job.get("root_closed_all") != true or float(job.get("expires_unix",0)) <= Time.get_unix_time_from_system() or job.get("script_sha256") != FileAccess.get_sha256(SCRIPT) or job.get("app_sha256") != FileAccess.get_sha256("res://src/app.gd"):
		push_error("Fresh root closure and exact script/app pins required"); quit(2); return
	var base := ProjectSettings.globalize_path("res://output/").replace("\\","/").trim_suffix("/")+"/"
	var folder: String = str(job.get("folder","")).replace("\\","/")
	if not folder.is_absolute_path() or folder.simplify_path() != folder or not folder.begins_with(base) or folder == base or DirAccess.dir_exists_absolute(folder):
		push_error("Fresh isolated output folder required"); quit(2); return
	DirAccess.make_dir_recursive_absolute(folder)
	root.size = Vector2i(1440,900)
	app = ProbeApp.new()
	app.name = "NeonRegressionStudio"
	app.display_prefs_path = folder.path_join("display.cfg")
	app.recent_path = folder.path_join("recents.json")
	app.recovery_root = folder.path_join("recovery")
	app.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(app)
	await settled()
	app.home.hide(); app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = folder.path_join("cache")
	app.canvas.pointer.connect(count_canvas_press)
	check("default_neon",StudioTheme.is_neon())
	app.set_advanced(false); app.mode.select(2); app.change_mode(2)
	await settled()
	check("idle_simple_pose",not app.advanced_mode and not app.physics_editor.is_running())
	check("actual_physics_visible",app.physics_editor.toggle.is_visible_in_tree())
	check("actual_hair_visible",app.physics_editor.hair_toggle.is_visible_in_tree())
	var fan := find_button(app.physics_bar,"Add fan")
	check("fan_entry_visible",fan != null and fan.is_visible_in_tree())
	check("loose_parts_entry_visible",app.physics_editor.helper_editor.button.is_visible_in_tree())
	check("wind_review_entry_visible",app.local_wind_review.button.is_visible_in_tree())
	check("record_scope_visible",app.physics_editor.recording.scope.is_visible_in_tree())
	check("record_entry_visible",app.physics_editor.recording.button.is_visible_in_tree())
	var before_count: int = app.current_world().objects.size()
	if fan and fan.is_visible_in_tree(): await click_point(fan.get_global_rect().get_center())
	var fans: Array = app.current_world().objects.filter(func(row): return Airflow.is_fan(row))
	check("simple_add_fan_real_click",app.current_world().objects.size() == before_count+1 and fans.size() == 1)
	var fan_id: String = fans[0].id if fans.size() == 1 else ""
	var fixture := ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb")
	var fixture_sha := FileAccess.get_sha256(fixture)
	var error: String = app.append_object(Model.definition(fixture),"model")
	check("included_model_import",error.is_empty())
	var model_id: String = app.last_import_id
	app.world_selection.select_entity(model_id)
	await settled()
	var rows: Dictionary = app.timeline_row_keys()
	check("cache_contains_current_model",rows.has(model_id) and app.timeline_key_cache.has(model_id))
	check("cache_current_identity",is_same(app.timeline_key_cache[model_id][0],app.renderer.active_model().data))
	app.set_frame(3); app.pose_editor.record_key()
	rows = app.timeline_row_keys()
	check("cache_updates_after_authored_key",3 in rows.get(model_id,[]))
	if not fan_id.is_empty(): app.remove_world_object(fan_id)
	rows = app.timeline_row_keys()
	check("deleted_object_cache_evicted",fan_id.is_empty() or not app.timeline_key_cache.has(fan_id))
	check("remaining_model_cache_retained",rows.has(model_id) and app.timeline_key_cache.has(model_id))
	check("cache_bounded_to_live_rows",app.timeline_key_cache.size() == rows.size())
	# Exercise the no-runtime boundary without freeing or altering the actual live world.
	var runtime = app.renderer.world_runtime
	app.renderer.world_runtime = null
	var absent: Dictionary = app.timeline_row_keys()
	check("no_runtime_cache_cleared",absent.is_empty() and app.timeline_key_cache.is_empty())
	app.renderer.world_runtime = runtime
	app.timeline_row_keys()
	check("cache_repopulates_current_world",app.timeline_key_cache.has(model_id))
	check("new_project_succeeds",app.new_project())
	app.timeline_row_keys()
	check("new_project_cache_bounded",app.timeline_key_cache.is_empty())
	var focus := root.gui_get_focus_owner()
	if focus: focus.release_focus()
	check("F11_assignment_accepted",app.keyboard_shortcuts.assign("save",KEY_F11).is_empty())
	var preferences := ConfigFile.new(); preferences.load(app.display_prefs_path)
	check("F11_assignment_persisted",preferences.get_value("shortcuts","keys",{}).get("save") == KEY_F11)
	send_f11()
	check("bound_F11_routes_save",app.observed_save_calls == 1 and app.observed_fullscreen_calls == 0)
	app.observed_save_calls = 0; app.observed_fullscreen_calls = 0
	app.keyboard_shortcuts.assign("save",0)
	send_f11()
	check("unbound_F11_routes_fullscreen",app.observed_save_calls == 0 and app.observed_fullscreen_calls == 1)
	app.observed_save_calls = 0; app.observed_fullscreen_calls = 0
	app.keyboard_shortcuts.assign("save",KEY_MASK_CTRL|KEY_F11)
	send_f11(true)
	check("modified_F11_binding_preserved",app.observed_save_calls == 1 and app.observed_fullscreen_calls == 0)
	app.mode.select(1); app.change_mode(1); app.scene_view.set_setup(true,false)
	app.message("A short transient message.")
	await settled()
	check("toast_displayed_with_tooltip",app.toast.modulate.a == 1.0 and app.toast.tooltip_text == app.status.text)
	await create_timer(6.3).timeout
	await settled()
	check("toast_fades_without_erasing_status",app.status.text == "A short transient message." and app.status_faded and app.toast.modulate.a == 0.0)
	var point: Vector2 = app.toast.get_global_rect().get_center()
	check("old_toast_rect_inside_scene",app.canvas.get_global_rect().has_point(point) and app.canvas.scene_setup)
	var observed := pointer_presses
	await click_point(point)
	check("faded_toast_allows_real_canvas_click",pointer_presses == observed+1)
	app.refresh_workspace(); await settled()
	observed = pointer_presses
	await click_point(app.toast.get_global_rect().get_center())
	check("workspace_refresh_keeps_canvas_clickthrough",pointer_presses == observed+1)
	check("included_source_unchanged",FileAccess.get_sha256(fixture) == fixture_sha)
	app.release_mouse(false)
	app.queue_free(); await settled()
	var result := {"format":"has_neon_behavior_regression_result_1","checks":named.size(),"expected_checks":EXPECTED_CHECKS,"failures":failures,"complete_assertion_set":named.size()==EXPECTED_CHECKS,"named_checks":named,"synthetic_included_assets_only":true,"save_and_fullscreen_actions_instrumented":true,"script_sha256":FileAccess.get_sha256(SCRIPT),"app_sha256":job.app_sha256}
	var file := FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
	if not file: push_error("Cannot write fresh result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	quit(0 if failures == 0 and named.size()==EXPECTED_CHECKS else 1)
