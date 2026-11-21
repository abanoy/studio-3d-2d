extends SceneTree
# Source-only/unrun. Root must use an owned private GPU desktop and an owned morph fixture.
const Shape=preload("res://src/source_shape.gd")
var checks:=0
var failures:=0
var app
var resize_cases: Array=[]
func _initialize() -> void:
	create_timer(90).timeout.connect(func():push_error("Face window layout watchdog");quit(2))
	call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1
	if not value:failures+=1
	print(("PASS " if value else "FAIL ")+"face_window."+label)
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func native_resize_settled() -> void:
	# Allow deferred engine/native resize notifications to reach the controller.
	for i in range(15):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2:push_error("Expected owned output folder and generated morph GLB");quit(2);return
	var folder: String=args[0];var fixture: String=args[1]
	root.size=Vector2i(1600,1000)
	check(FileAccess.file_exists(fixture),"owned_morph_fixture_exists")
	if not FileAccess.file_exists(fixture):quit(1);return
	var source_sha:=FileAccess.get_sha256(fixture)
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false
	app.set_advanced(false)
	var context: Dictionary=app.import_actions.placement();context.physics_on_import=false
	check(app.pose_editor.add_model(fixture,0,context).is_empty(),"normal_model_import_preserves_fixture")
	app.mode.select(2);app.change_mode(2);await settled()
	var editor=app.pose_editor;var actor: RefCounted=editor.active_rig()
	check(actor!=null and not actor.root.get_meta(Shape.META,{"rows":[]}).rows.is_empty(),"ordinary_imported_model_has_real_shape_controls")
	if actor==null or actor.root.get_meta(Shape.META,{"rows":[]}).rows.is_empty():app.free();quit(1);return
	var authored:=var_to_bytes([actor.data,app.keys,app.history])
	editor.open_shapes();await settled()
	var window: Window=editor.shape_window;var shapes: ItemList=editor.animated_shapes.shapes
	check(window.visible and not window.unresizable and window.keep_title_visible,"resizable_expression_window_keeps_its_title_accessible")
	check(window.size.x>=480 and window.size.y>520 and window.min_size.x>0 and window.min_size.y>0,"first_open_uses_practical_bounded_dimensions")
	check(shapes.item_count>0 and shapes.size_flags_vertical==Control.SIZE_EXPAND_FILL and editor.animated_shapes.panel.size_flags_vertical==Control.SIZE_EXPAND_FILL,"real_control_list_can_use_the_remaining_height")
	window.size=Vector2i(600,620);await settled();var short_list:=shapes.size.y
	window.size=Vector2i(600,880);await settled();var tall_list:=shapes.size.y
	check(tall_list>short_list+100.,"widening_the_usable_window_height_grows_the_actual_list")
	var selected: int=shapes.get_selected_items()[0] if not shapes.get_selected_items().is_empty() else -1
	var previous_search: String=editor.animated_shapes.search.text
	window.hide();editor.open_shapes();await settled()
	check(window.size==Vector2i(600,880),"closing_and_reopening_keeps_the_user_resize")
	check(editor.animated_shapes.search.text==previous_search and (shapes.get_selected_items()[0] if not shapes.get_selected_items().is_empty() else -1)==selected,"reopening_does_not_reset_the_filter_or_selected_control")
	check(editor.animated_shapes.amount.min_value==-100. and editor.animated_shapes.amount.max_value==100. and editor.animated_shapes.amount.step==.001,"layout_change_does_not_reinterpret_or_clamp_shape_amounts")
	check(editor.shape_close.is_visible_in_tree() and editor.animated_shapes.apply_button.is_visible_in_tree() and editor.animated_shapes.reset_all.is_visible_in_tree(),"Close_and_existing_shape_commands_remain_available")
	app.set_advanced(true);await settled()
	check(editor.animated_shapes.organize.is_visible_in_tree() and shapes.size.y>=160.,"Advanced_organization_remains_available_with_scroll_fallback")
	app.set_advanced(false);await settled()
	check(not editor.animated_shapes.organize.is_visible_in_tree(),"Simple_mode_keeps_the_existing_organization_visibility")
	check(authored==var_to_bytes([actor.data,app.keys,app.history]),"opening_resizing_and_mode_switching_do_not_modify_authored_data")
	check(FileAccess.get_sha256(fixture)==source_sha,"original_fixture_bytes_remain_unchanged")
	# Exercise controller memory through real popup/resize signals, not only pure sizing math.
	for ui in [1.,1.5]:
		root.size=Vector2i(3440,1440);root.content_scale_factor=ui;await native_resize_settled()
		editor.open_shapes();await native_resize_settled()
		var large:=Vector2i(650,800);window.size=large;await native_resize_settled()
		check(window.size==large and editor.shape_user_size==large,"manual_large_resize_is_remembered_at_interface_scale_"+str(ui))
		window.hide();root.size=Vector2i(960,600);await native_resize_settled()
		var compact_host:=Vector2i(app.get_viewport_rect().size)
		var expected_clamp: Vector2i=preload("res://src/shape_window_layout.gd").opening_size(compact_host,large)
		editor.open_shapes()
		# Deterministically exercise a late notification as well as real queued resize events.
		window.call_deferred("emit_signal","size_changed")
		await native_resize_settled()
		var observed_clamp:=window.size;var observed_preference: Vector2i=editor.shape_user_size
		check(window.size==expected_clamp and editor.shape_user_size==large,"late_programmatic_clamp_does_not_replace_user_size_at_interface_scale_"+str(ui))
		window.hide();root.size=Vector2i(3440,1440);await native_resize_settled();editor.open_shapes();await native_resize_settled()
		check(window.size==large and editor.shape_user_size==large,"restoring_parent_restores_original_user_size_at_interface_scale_"+str(ui))
		window.hide();root.size=Vector2i(960,600);await native_resize_settled();editor.open_shapes();await native_resize_settled()
		var manual:=Vector2i(maxi(window.min_size.x,window.size.x-40),maxi(window.min_size.y,window.size.y-40))
		window.size=manual;await native_resize_settled()
		check(window.size==manual and editor.shape_user_size==manual,"genuine_compact_manual_resize_is_not_ignored_at_interface_scale_"+str(ui))
		window.hide();root.size=Vector2i(3440,1440);await native_resize_settled();editor.open_shapes();await native_resize_settled()
		check(window.size==manual and editor.shape_user_size==manual,"latest_manual_resize_survives_parent_restore_at_interface_scale_"+str(ui))
		app.set_advanced(true);await settled()
		var shape_scroll: ScrollContainer=editor.animated_shapes.panel.get_parent().get_parent() as ScrollContainer
		check(editor.animated_shapes.organize.is_visible_in_tree() and editor.shape_close.is_visible_in_tree() and shape_scroll.get_v_scroll_bar().is_visible_in_tree(),"compact_Advanced_controls_keep_scroll_and_Close_at_interface_scale_"+str(ui))
		app.set_advanced(false);await settled()
		check(not editor.animated_shapes.organize.is_visible_in_tree() and editor.animated_shapes.apply_button.is_visible_in_tree() and editor.shape_close.is_visible_in_tree(),"compact_Simple_controls_remain_accessible_at_interface_scale_"+str(ui))
		resize_cases.append({"interface_scale":ui,"compact_host":str(compact_host),"expected_clamp":str(expected_clamp),"observed_clamp":str(observed_clamp),"preference_after_clamp":str(observed_preference),"manual_size":str(manual),"controlled_late_size_signal":true})
	check(authored==var_to_bytes([actor.data,app.keys,app.history]) and FileAccess.get_sha256(fixture)==source_sha,"DPI_and_parent_resize_cases_preserve_all_authored_state_and_original_skin")
	# Actual detached-but-valid Canvas lifecycle: the same state reached while
	# wind/setup child owners stop during app.free(). No error suppression.
	var live_canvas: Control=app.canvas;var canvas_parent: Node=live_canvas.get_parent();var canvas_index:=live_canvas.get_index()
	canvas_parent.remove_child(live_canvas)
	check(is_instance_valid(live_canvas) and not live_canvas.is_inside_tree() and live_canvas.get_viewport()==null,"detached_real_canvas_has_no_live_viewport")
	check(editor.handle_metrics().is_empty(),"detached_canvas_exposes_no_handle_geometry")
	editor.handles=[{"lifecycle_sentinel":true}];editor.joints=[{"lifecycle_sentinel":true}]
	app.local_wind_review.stop_preview("Lifecycle regression")
	app.physics_editor.helper_editor.pending_preview.player.stop("Lifecycle regression")
	app.physics_editor.helper_editor.close()
	check(editor.handles.is_empty() and editor.joints.is_empty() and authored==var_to_bytes([actor.data,app.keys,app.history]),"ordinary_wind_and_setup_cleanup_clears_derived_handles_without_authored_changes")
	canvas_parent.add_child(live_canvas);canvas_parent.move_child(live_canvas,canvas_index);await native_resize_settled();editor.update_gizmo()
	check(app.canvas==live_canvas and live_canvas.is_inside_tree() and not editor.handle_metrics().is_empty(),"reattached_canvas_recovers_real_handle_measurement")
	# No yield while the private app field points to a deliberately freed dummy.
	var freed_canvas:=Control.new();app.canvas=freed_canvas;freed_canvas.free()
	editor.handles=[{"lifecycle_sentinel":true}];editor.joints=[{"lifecycle_sentinel":true}]
	var freed_metrics: Dictionary=editor.handle_metrics();editor.update_gizmo()
	var freed_ok: bool=freed_metrics.is_empty() and editor.handles.is_empty() and editor.joints.is_empty()
	app.canvas=live_canvas
	check(freed_ok,"freed_canvas_reference_has_no_handle_geometry_and_clears_derived_caches")
	editor.update_gizmo()
	check(not editor.handle_metrics().is_empty() and authored==var_to_bytes([actor.data,app.keys,app.history]) and FileAccess.get_sha256(fixture)==source_sha,"lifecycle_checks_restore_live_canvas_and_preserve_authored_state_and_source")
	var report:={"checks":checks,"failures":failures,"list_heights":[short_list,tall_list],"resize_cases":resize_cases,"lifecycle_checks":6,"application_adopted":false,"owner_layout_acceptance":false}
	var out:=FileAccess.open(folder.path_join("face-window-layout-result.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report));out.close()
	print("FACE_WINDOW_LAYOUT "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
