extends SceneTree
# Source-only/unrun. Root must use an owned private GPU desktop and an owned morph fixture.
const Shape=preload("res://src/source_shape.gd")
var checks:=0
var failures:=0
var app
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
	var report:={"checks":checks,"failures":failures,"list_heights":[short_list,tall_list],"application_adopted":false,"owner_layout_acceptance":false}
	var out:=FileAccess.open(folder.path_join("face-window-layout-result.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report));out.close()
	print("FACE_WINDOW_LAYOUT "+JSON.stringify(report));app.free();quit(0 if failures==0 else 1)
