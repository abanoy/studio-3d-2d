extends SceneTree
# UNRUN. Run only in a successor checkout after the source patch is reviewed.
# Uses the included synthetic Practice figure; writes scalar receipts only.
const World = preload("res://src/world_document.gd")
var app
var ws
var folder := ""
var checks := 0
var failures := 0
var selection := ""
var original_world: Dictionary = {}
var original_tree_id := 0

func _initialize() -> void:
	create_timer(100).timeout.connect(func(): push_error("Rail placement watchdog expired"); quit(2))
	call_deferred("run")

func settled() -> void:
	for i in range(10): await process_frame
	await RenderingServer.frame_post_draw

func check(ok: bool, label: String) -> void:
	checks += 1
	print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1

func retained(label: String) -> void:
	check(app.world_selection.selected == selection and app.renderer.active_instance_id == selection and app.timeline.selected_id == selection, label + " retains the selected model")
	check(app.world_selection.tree.get_instance_id() == original_tree_id and World.portable(app.current_world()) == original_world, label + " retains the live Tree and world document")

func list_mode(label: String) -> void:
	print("RAIL_STATE ",JSON.stringify({"label":label,"workspace_mode":ws.world_rail,"selection_mode":app.world_selection.rail_mode,"tree_visible":app.world_selection.tree.visible,"layout_active":ws.world_mode_active,"selection_active":app.world_selection.rail_ui_active,"panel_inside":ws.panels.world.is_inside_tree(),"tree_inside":app.world_selection.tree.is_inside_tree(),"holder_inside":app.world_selection.tree.get_parent().is_inside_tree(),"help_inside":app.world_selection.help_label.is_inside_tree(),"rail_inside":app.world_selection.rail.is_inside_tree(),"floating":ws.floating.has("world")}))
	check(not ws.world_rail and not app.world_selection.rail_mode and app.world_selection.tree.visible, label + " uses the full hierarchy list")
	check(not ws.world_unfold.visible, label + " does not offer an unsupported left-dock fold action")
	retained(label)

func left_width(width: float) -> void:
	ws.horizontal.clamp_split_offset()
	ws.horizontal.split_offset += int(roundf(width - ws.slots.left.size.x))
	ws.horizontal.clamp_split_offset()
	await settled()

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1:
		push_error("Provide one fresh owned output folder")
		quit(2)
		return
	folder = ProjectSettings.globalize_path(args[0]).simplify_path()
	var output_root := ProjectSettings.globalize_path("res://output").simplify_path().trim_suffix("/") + "/"
	if not folder.begins_with(output_root) or DirAccess.dir_exists_absolute(folder):
		push_error("Fresh output beneath this checkout's output directory required")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(folder)
	app = load("res://main.tscn").instantiate()
	app.recovery_root = folder.path_join("recovery")
	app.recent_path = folder.path_join("recent.json")
	app.display_prefs_path = folder.path_join("prefs.cfg")
	root.add_child(app)
	await settled()
	app.home.hide()
	app.autosave_enabled.button_pressed = false
	root.size = Vector2i(1600, 1000)
	app.apply_theme_style("neon")
	app.set_advanced(false)
	await settled()
	ws = app.workspace_layout
	ws.path = folder.path_join("layout.json")
	var placement: Dictionary = app.import_actions.placement()
	placement.physics_on_import = false
	var imported: String = app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"), 0, placement)
	check(imported.is_empty() and app.current_world().objects.size() == 1, "included synthetic rig opens for rail checks")
	if not imported.is_empty() or app.current_world().objects.size() != 1:
		app.free()
		quit(1)
		return
	selection = app.last_import_id
	app.world_selection.select_entity(selection)
	await settled()
	original_world = World.portable(app.current_world())
	original_tree_id = app.world_selection.tree.get_instance_id()

	ws.reset()
	await settled()
	await left_width(64.0)
	check(ws.want_full_left() and ws.world_rail and app.world_selection.rail_mode and not app.world_selection.tree.visible, "solitary narrow left World uses its icon rail")
	check(ws.world_unfold.visible, "supported left rail exposes its unfold button")
	retained("left rail")
	ws.world_unfold.pressed.emit()
	await settled()
	check(not ws.world_rail and app.world_selection.tree.visible and ws.world_unfold.visible and absf(ws.slots.left.size.x - ws.LIST_WIDTH) < 3.0, "left unfold button reveals a 232 px list")
	ws.world_unfold.pressed.emit()
	await settled()
	check(ws.world_rail and ws.slots.left.size.x < ws.RAIL_LIMIT, "left fold button returns to the supported rail")
	retained("left fold and unfold")

	# Placement changes must work without the test calling refresh_world_mode().
	# Empty the right edge explicitly so its former inspector minimum cannot affect this fixture.
	ws.tab_panel("properties", "timeline")
	await settled()
	ws.dock("world", "right")
	await settled()
	check(ws.groups.right == ["world"], "narrow-right fixture gives World a solitary dock")
	list_mode("World moved to the right")
	ws.right_split.clamp_split_offset()
	ws.right_split.split_offset += int(roundf(ws.slots.right.size.x - 110.0))
	ws.right_split.clamp_split_offset()
	await settled()
	check(ws.panels.world.size.x < ws.RAIL_LIMIT, "right-dock regression reaches a sub-140 px World panel")
	list_mode("narrow right World")

	ws.reset()
	await settled()
	await left_width(64.0)
	ws.split_panel("timeline", "world", "right")
	await settled()
	var world_book: TabContainer = ws.dock_tree.book_for("world")
	var nested: SplitContainer = world_book.get_parent() as SplitContainer
	check(nested != null and world_book.get_index() == 0 and ws.groups.left.size() == 2, "nested regression places World beside Timeline inside the left edge")
	if nested:
		nested.clamp_split_offset()
		nested.split_offset += int(roundf(110.0 - world_book.size.x))
		nested.clamp_split_offset()
		await settled()
	check(ws.panels.world.size.x < ws.RAIL_LIMIT, "nested regression reaches a sub-140 px World leaf")
	list_mode("narrow nested World")
	var before_unsupported: Dictionary = ws.state().duplicate(true)
	ws.unfold_world()
	await settled()
	check(ws.state() == before_unsupported, "unsupported nested fold call leaves every dock offset unchanged")

	# Restore the real nested tree, offsets and selection through the persisted format.
	ws.timer.stop()
	ws.save()
	var nested_state: Dictionary = ws.state().duplicate(true)
	ws.reset()
	ws.timer.stop()
	await settled()
	check(ws.load_layout(), "nested World layout reloads from disk")
	await settled()
	check(ws.state() == nested_state, "nested layout restoration preserves exact serialized state")
	list_mode("restored nested World")

	ws.reset()
	await settled()
	ws.tab_panel("properties", "world")
	await settled()
	world_book = ws.dock_tree.book_for("world")
	world_book.current_tab = ws.panels.world.get_index()
	await settled()
	check(world_book.tabs_visible and ws.groups.left.size() == 2, "tab regression shares World with Properties")
	list_mode("tabbed left World")

	ws.reset()
	await settled()
	await left_width(64.0)
	ws.float_panel("world")
	await settled()
	check(ws.floating.has("world"), "World detaches into its own window")
	list_mode("floating World")
	ws.dock("world", "left")
	await settled()
	await left_width(64.0)
	check(ws.want_full_left() and ws.world_rail and ws.world_unfold.visible, "returning from a floating window restores the supported left rail")
	retained("redocked left rail")

	ws.timer.stop()
	var result := {"format":"has_neon_rail_placement_regression_1", "checks":checks, "failures":failures, "synthetic_fixture_only":true, "screenshots_written":false}
	var receipt := FileAccess.open(folder.path_join("result.json"), FileAccess.WRITE)
	receipt.store_string(JSON.stringify(result))
	receipt.close()
	print("NEON_RAIL_PLACEMENT " + JSON.stringify(result))
	app.free()
	quit(1 if failures else 0)
