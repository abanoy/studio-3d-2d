extends Node
var app
var window: Window
var sources: ItemList
var entries: ItemList
var search: LineEdit
var source_filter: LineEdit
var kind: OptionButton
var mount: CheckButton
var details: Label
var state: Label
var import_button: Button
var providers: Array = []
var source_rows: Array = []
var assets: Array = []
var filtered: Array = []
var current := {}
var job_pid := -1
var job_result := ""
var job_action := ""
var job_started := 0
var cache_root := "res://output/source-browser"
var discovery := {}
var scan_warnings: Array = []
var truncated := false

func open(as_model := true) -> void:
	if app.exporting or app.source_import.pid > 0: return
	app.stop()
	if is_instance_valid(window): window.popup_centered(Vector2i(1100, 690)); return
	window = Window.new()
	window.title = "Installed Source content"
	window.transient = true
	window.exclusive = false
	window.close_requested.connect(close)
	app.add_child(window)
	var background := Panel.new()
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.add_theme_stylebox_override("panel", preload("res://src/studio_theme.gd").surface("f4f7fb", "dce5ee"))
	window.add_child(background)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + side, 12)
	window.add_child(margin)
	var box := VBoxContainer.new(); margin.add_child(box)
	var heading := HBoxContainer.new(); box.add_child(heading)
	app.label(heading, "Installed models and maps").size_flags_horizontal = Control.SIZE_EXPAND_FILL
	app.button(heading, "Locations…", locations)
	app.button(heading, "Refresh", refresh)
	app.button(heading, "Cancel scan", cancel_scan)
	state = app.label(box, "Discover local content…")
	state.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var split := HSplitContainer.new(); box.add_child(split)
	split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var left := VBoxContainer.new(); split.add_child(left); left.custom_minimum_size.x = 320
	source_filter = LineEdit.new(); source_filter.placeholder_text = "Filter locations / add-on ID…"; left.add_child(source_filter)
	source_filter.text_changed.connect(func(_text): filter_sources())
	sources = ItemList.new(); left.add_child(sources); sources.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sources.item_selected.connect(select_source)
	mount = CheckButton.new(); mount.text = "Use location for dependencies"; left.add_child(mount)
	mount.toggled.connect(toggle_mount)
	var right := VBoxContainer.new(); split.add_child(right); right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var tools := HBoxContainer.new(); right.add_child(tools)
	kind = OptionButton.new(); kind.add_item("Models"); kind.add_item("Maps"); kind.add_item("Models and maps")
	kind.select(0 if as_model else 1); tools.add_child(kind); kind.item_selected.connect(func(_i): filter_assets())
	search = LineEdit.new(); search.placeholder_text = "Search asset paths…"; search.size_flags_horizontal = Control.SIZE_EXPAND_FILL; tools.add_child(search)
	search.text_changed.connect(func(_text): filter_assets())
	search.text_submitted.connect(func(_text): search_all())
	app.button(tools, "Search all", search_all)
	entries = ItemList.new(); entries.size_flags_vertical = Control.SIZE_EXPAND_FILL; right.add_child(entries)
	entries.item_selected.connect(select_asset)
	entries.item_activated.connect(func(index): select_asset(index); import_selected())
	details = app.label(box, "Choose a source, or search all installed assets. No game or addon scripts run.")
	details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	details.custom_minimum_size.y = 64
	var buttons := HBoxContainer.new(); box.add_child(buttons)
	import_button = app.button(buttons, "Import selected", import_selected); import_button.disabled = true
	app.button(buttons, "Open original file location", reveal)
	app.button(buttons, "Close", close)
	window.popup_centered(Vector2i(1100, 690))
	refresh()

func close() -> void:
	cancel_scan()
	if is_instance_valid(window): window.hide(); window.queue_free()
	window = null

func locations() -> void:
	var dialog := ConfirmationDialog.new(); dialog.title = "Local content locations";dialog.exclusive=false;dialog.unresizable=false
	var scroll := ScrollContainer.new(); scroll.custom_minimum_size = Vector2(720, 350); scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; dialog.add_child(scroll)
	var box := VBoxContainer.new(); box.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(box)
	app.label(box, "GMod must be installed. SFM is optional; no games or add-ons are downloaded.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var game: LineEdit = app.source_import.path_field(box, dialog, "Garry's Mod installation", app.source_import.gmod_root)
	var workshop: LineEdit = app.source_import.path_field(box, dialog, "Workshop content / 4000", app.source_import.workshop_root)
	app.label(box, "Additional content directories / VPKs (one per line; optional SFM game or mod folder)")
	var extra := TextEdit.new(); extra.custom_minimum_size.y = 95; extra.text = "\n".join(app.source_import.extra_roots); box.add_child(extra)
	window.add_child(dialog)
	dialog.confirmed.connect(func():
		app.source_import.gmod_root = game.text.strip_edges(); app.source_import.workshop_root = workshop.text.strip_edges()
		app.source_import.extra_roots = []
		for line in extra.text.split("\n"):
			if not line.strip_edges().is_empty(): app.source_import.extra_roots.append(line.strip_edges())
		if app.source_import.save_paths() != OK: app.message("Cannot save content locations")
		dialog.hide(); dialog.queue_free(); refresh())
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered(Vector2i(760, 420))

func begin_job(action: String, data: Dictionary) -> void:
	cancel_scan()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(cache_root))
	var base := ProjectSettings.globalize_path(cache_root).path_join("%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()])
	job_result = base + "-result.json"
	data.merge({"action": action, "gmod": app.source_import.gmod_root, "workshop": app.source_import.workshop_root, "extra": app.source_import.extra_roots, "result": job_result}, true)
	var file := FileAccess.open(base + "-request.json", FileAccess.WRITE)
	if file == null: state.text = "Cannot write browser request"; return
	file.store_string(JSON.stringify(data)); file.close()
	job_action = action; job_started = Time.get_ticks_msec()
	job_pid = OS.create_process(app.source_import.python(), [ProjectSettings.globalize_path("res://tools/source_browser.py"), base + "-request.json"], false)
	state.text = "Discovering local folders…" if action == "discover" else "Scanning asset index… You can cancel this scan."
	import_button.disabled = true
	if job_pid < 0: state.text = "Cannot start Python content browser worker"

func cancel_scan() -> void:
	if job_pid > 0 and OS.is_process_running(job_pid): OS.kill(job_pid)
	job_pid = -1
	if is_instance_valid(state): state.text = "Scan stopped. Existing project is unchanged."

func refresh() -> void:
	begin_job("discover", {})

func filter_sources() -> void:
	sources.clear(); source_rows.clear()
	for provider in providers:
		if not source_filter.text.is_empty() and not (provider.label + " " + provider.path).to_lower().contains(source_filter.text.to_lower()): continue
		source_rows.append(provider)
		var label: String = ("✓ " if provider.enabled else "") + provider.label + (" (missing)" if not provider.present else "")
		sources.add_item(label)
		sources.set_item_tooltip(sources.item_count - 1, provider.path + "\n" + provider.origin)

func select_source(index: int) -> void:
	if index < 0 or index >= source_rows.size(): return
	current = source_rows[index]
	mount.set_pressed_no_signal(current.enabled)
	mount.disabled = not current.present or current.kind == "bin"
	details.text = current.path + "\n" + ("Legacy BIN imports its own resources; share dependencies through a prepared native folder." if current.kind == "bin" else "Own resources first, then the source's game profile and automatic fallbacks. Uncheck to exclude a dependency location.")
	assets.clear(); entries.clear(); filtered.clear()
	begin_job("index", {"provider": current})

func toggle_mount(enabled: bool) -> void:
	if current.is_empty(): return
	current.enabled = enabled
	app.source_import.mount_overrides[current.path] = enabled
	if app.source_import.save_paths() != OK: app.message("Cannot save dependency mount choices")
	# Keep list ordering stable; changing a checkbox does not trigger an asset reload.
	if not sources.get_selected_items().is_empty():
		var index: int = sources.get_selected_items()[0]
		sources.set_item_text(index, ("✓ " if enabled else "") + current.label)

func filter_assets() -> void:
	entries.clear(); filtered.clear(); import_button.disabled = true
	var matches := 0
	for asset in assets:
		if kind.selected == 0 and asset.kind != "model" or kind.selected == 1 and asset.kind != "map": continue
		if not search.text.is_empty() and not (asset.path + " " + str(asset.get("source_title", ""))).to_lower().contains(search.text.to_lower()): continue
		matches += 1
		if filtered.size() >= 2000: continue
		filtered.append(asset)
		entries.add_item(asset.path + ("  [" + str(asset.get("source_title", "")) + "]" if job_action == "search" else ""))
		entries.set_item_tooltip(entries.item_count - 1, str(asset.get("source_title", current.get("label", ""))) + "\n" + asset.path)
	state.text = "%d matching assets • %d source locations" % [matches, providers.size()]
	if matches > filtered.size(): state.text += " • showing first 2000; refine the search"
	if truncated: state.text += " • scan result limit reached"
	if not scan_warnings.is_empty(): state.text += " • %d locations could not be indexed" % scan_warnings.size()

func search_all() -> void:
	begin_job("search", {"providers": providers, "query": search.text})

func select_asset(index: int) -> void:
	if index < 0 or index >= filtered.size(): return
	var asset: Dictionary = filtered[index]
	var provider: Dictionary = asset.get("provider", current)
	details.text = ("Model" if asset.kind == "model" else "Map") + ": " + asset.path + "\n" + str(asset.get("source_title", provider.label)) + " • " + str(asset.bytes) + " bytes\n" + provider.path
	import_button.disabled = false

func import_selected() -> void:
	if job_pid > 0 or entries.get_selected_items().is_empty(): return
	var asset: Dictionary = filtered[entries.get_selected_items()[0]]
	var provider: Dictionary = asset.get("provider", current)
	var path: String = provider.path.path_join(asset.path) if provider.kind == "folder" else provider.path
	var member: String = "" if provider.kind == "folder" else asset.path
	var action := func(): app.source_import.launch(path, member, asset.kind == "model", 0.01905,"",null,"","Y",0,app.import_actions.placement() if asset.kind=="model" else {})
	close()
	action.call_deferred()

func reveal() -> void:
	if entries.get_selected_items().is_empty(): return
	var asset: Dictionary = filtered[entries.get_selected_items()[0]]
	var provider: Dictionary = asset.get("provider", current)
	OS.shell_show_in_file_manager(provider.path.path_join(asset.path) if provider.kind == "folder" else provider.path)

func _process(_delta: float) -> void:
	if job_pid <= 0: return
	if Time.get_ticks_msec() - job_started > 120000: cancel_scan(); state.text = "Scan timed out; narrow the selected locations."; return
	if OS.is_process_running(job_pid): return
	job_pid = -1
	if not is_instance_valid(window): return
	var file := FileAccess.open(job_result, FileAccess.READ)
	var result = JSON.parse_string(file.get_as_text()) if file and file.get_length() <= 64 * 1024 * 1024 else null
	if not result is Dictionary or not result.get("ok", false): state.text = str(result.get("error", "Scan failed")) if result is Dictionary else "Browser worker failed; check the selected paths and Python."; return
	if job_action == "discover":
		discovery = result; providers = result.providers
		for provider in providers:
			if app.source_import.mount_overrides.has(provider.path): provider.enabled = bool(app.source_import.mount_overrides[provider.path]) and provider.present
		filter_sources()
		var status: Array[String] = []
		for game in result.games:
			status.append(game.name + ": " + ("included content in GMod" if game.get("included_in_gmod", false) else "installed" if game.installed else "not installed"))
		for warning in result.get("warnings", []): status.append(str(warning))
		details.text = "\n".join(status)
		state.text = "%d locations. Choose a source or Search all. Dependencies resolve automatically; uncheck to exclude a location." % providers.size()
	else:
		assets = result.assets
		scan_warnings = result.get("warnings", [])
		truncated = result.get("truncated", false)
		if job_action == "index":
			for asset in assets: asset["provider"] = current; asset["source_title"] = result.title
		filter_assets()
		if assets.is_empty(): state.text = "No MDL/BSP models or maps in this location. It may contain only materials, sounds or scripts."

func _exit_tree() -> void:
	cancel_scan()
