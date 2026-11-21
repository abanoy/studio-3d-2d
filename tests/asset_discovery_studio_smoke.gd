extends SceneTree
## Runs against a disposable source copy with the reviewable app patch applied.
var checks := 0
var failures: Array = []
var app

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); printerr("FAIL: " + label)

func _initialize() -> void:
	create_timer(45).timeout.connect(func(): quit(2))
	call_deferred("run")

func settle() -> void:
	await process_frame; await process_frame; await process_frame

func find_add(node: Node) -> MenuButton:
	for child in node.get_children():
		if child is MenuButton and child.get_meta("label", child.text) == "Add": return child
		var found := find_add(child)
		if found: return found
	return null

func make_model(path: String) -> void:
	var scene := Node3D.new()
	var mesh := MeshInstance3D.new(); mesh.mesh = BoxMesh.new(); scene.add_child(mesh); mesh.owner = scene
	var state := GLTFState.new(); var document := GLTFDocument.new()
	check(document.append_from_scene(scene, state) == OK and document.write_to_filesystem(state, path) == OK, "generate original synthetic GLB cube")
	scene.free()

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var folder: String = args[0]
	var classic := "--classic" in args
	var prefs := ConfigFile.new(); prefs.set_value("display", "theme", "light" if classic else "neon"); prefs.save(folder.path_join("display.cfg"))
	root.size = Vector2i(1600, 1000); root.gui_embed_subwindows = true
	app = load("res://main.tscn").instantiate()
	app.display_prefs_path = folder.path_join("display.cfg"); app.recovery_root = folder.path_join("recovery"); app.recent_path = folder.path_join("recent.json")
	root.add_child(app); await settle()
	app.home.hide(); app.autosave_enabled.button_pressed = false
	var bridge = app.get_node("AssetDiscoveryBridge")
	check(bridge != null and bridge.button.get_meta("label", bridge.button.text) == "Discover", "patched real Studio installs Discover toolbar button")
	app.set_advanced(false)
	var add := find_add(app)
	check(add != null and add.is_visible_in_tree(), "Simple Add menu remains visible")
	var menu := add.get_popup(); var menu_id := -1
	for i in menu.item_count:
		if menu.get_item_text(i) == "Asset discovery…": menu_id = menu.get_item_id(i)
	check(menu_id >= 0, "patched Simple Add menu contains Asset discovery")
	menu.id_pressed.emit(menu_id); await settle()
	check(is_instance_valid(bridge.window) and bridge.window.visible, "real Simple menu opens browser")
	var panel = bridge.window.get_meta("discovery_panel")
	check(not panel.online.network_enabled, "integrated browser starts offline")
	bridge.window.close_requested.emit(); await settle()
	app.set_advanced(true); await settle()
	check(bridge.button.is_visible_in_tree(), "real Discover toolbar is visible in Advanced")
	bridge.button.pressed.emit(); await settle()
	panel = bridge.window.get_meta("discovery_panel")
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		check(root.get_texture().get_image().save_png(folder.path_join("studio-browser.png")) == OK, "capture actual patched Studio browser layout")
	panel.page_opener = func(_url): return OK
	var before: Dictionary = app.current_world().duplicate(true)
	panel.tabs.current_tab = 1; panel.open_page("https://sketchfab.com/3d-models/test")
	check(app.current_world() == before and app.source_import.pid <= 0, "online source click leaves scene and import pipeline unchanged")
	bridge.window.close_requested.emit(); await settle()
	var path := folder.path_join("cube.glb"); make_model(path)
	var token: Dictionary = bridge.context()
	app.source_import.bundle_active = true
	bridge.accept_local(path, token)
	check(app.current_world() == before and app.status.text.contains("queue"), "bundle queue blocks local callback even without a process")
	app.source_import.bundle_active = false
	app.exporting = true; bridge.accept_local(path, token)
	check(app.current_world() == before, "active project/export operation blocks callback")
	app.exporting = false
	app.recovery_revision += 1; bridge.accept_local(path, token)
	check(app.current_world() == before and app.status.text.contains("changed"), "stale document revision refuses callback")
	app.recovery_revision -= 1
	var selection: String = app.world_selection.selected
	app.world_selection.selected = "earlier-selection"; bridge.accept_local(path, token)
	check(app.current_world() == before, "stale world selection refuses callback")
	app.world_selection.selected = selection
	var joint: String = app.pose_editor.selected
	app.pose_editor.selected = "earlier-joint"; bridge.accept_local(path, token)
	check(app.current_world() == before, "stale joint selection refuses callback")
	app.pose_editor.selected = joint
	app.sequence_editor.generation += 1; bridge.accept_local(path, token)
	check(app.current_world() == before, "stale sequence generation refuses callback")
	app.sequence_editor.generation -= 1
	app.height_review.pending = true; bridge.accept_local(path, token)
	check(app.current_world() == before, "pending height review refuses callback")
	app.height_review.pending = false
	bridge.accept_local(folder.path_join("missing.glb"), token)
	check(app.current_world() == before and app.status.text.contains("missing"), "disappeared local file gives useful error")
	var blend := folder.path_join("source.blend")
	var file := FileAccess.open(blend, FileAccess.WRITE); file.store_string("not executed"); file.close()
	bridge.accept_local(blend, token)
	check(app.current_world() == before and app.status.text.contains("supported GLB"), "unsupported local source does not execute or convert")
	# Ordinary UI selection -> deferred wrapper callback -> real ImportActions.
	bridge.button.pressed.emit(); await settle()
	panel = bridge.window.get_meta("discovery_panel")
	panel.tabs.current_tab = 0; panel.picker.dir_selected.emit(folder)
	while panel.local.loading: await process_frame
	await settle()
	var selected_item: TreeItem = panel.tree.get_root().get_first_child()
	while selected_item and str(selected_item.get_metadata(0).path).simplify_path() != path.simplify_path(): selected_item = selected_item.get_next()
	check(selected_item != null, "integrated local scan finds generated cube")
	if not selected_item:
		printerr("LOCAL_SCAN_DIAGNOSTIC " + JSON.stringify({"message":panel.local.message, "rows":panel.local.rows, "visible":panel.visible_rows, "query":panel.search.text, "format":panel.format_filter.get_item_text(panel.format_filter.selected), "path":path}))
		quit(1); return
	selected_item.select(0); panel.tree.item_selected.emit(); await settle()
	panel.use_button.pressed.emit(); await settle()
	check(not is_instance_valid(bridge.window), "Use closes the browser before the callback")
	check(app.current_world().objects.size() == before.objects.size() + 1, "real ordinary import pipeline adds generated model")
	check(app.source_import.pid <= 0 and not app.source_import.bundle_active, "standard GLB import starts no converter or bundle")
	app.undo(); await settle()
	check(app.current_world() == before, "ordinary Undo removes the imported model")
	var report := {"checks":checks, "failures":failures, "theme":"classic" if classic else "neon", "display_driver":DisplayServer.get_name(), "scope":"Patched real Studio in disposable source copy; synthetic GLB only, no native artwork or online downloads."}
	file = FileAccess.open(folder.path_join("studio-result.json"), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("DISCOVERY_STUDIO " + JSON.stringify(report))
	await app.quit_studio()
	quit(1 if not failures.is_empty() else 0)
