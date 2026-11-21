extends VBoxContainer
## Drop-in discovery panel. Parent supplies any explicit local import action.
signal local_file_selected(path: String)
signal source_page_opened(url: String)
const Catalog = preload("res://src/discovery/catalog.gd")
const Service = preload("res://src/discovery/service.gd")
const LocalScan = preload("res://src/discovery/local_scan.gd")
const Preferences = preload("res://src/discovery/preferences.gd")
const Thumbnail = preload("res://src/discovery/thumbnail.gd")
const LocalPreview = preload("res://src/discovery/local_preview.gd")
const RetrievalNotice = preload("res://src/discovery/retrieval_notice.gd")
var preferences_path := Preferences.DEFAULT_PATH
var local_import_extensions: Array = [] # Empty: parent-defined standalone callbacks.
var import_target_name := "Studio"
var online: Node
var local: Node
var tabs: TabBar
var search: LineEdit
var website: OptionButton
var format_filter: OptionButton
var expand: CheckButton
var network: CheckButton
var search_button: Button
var cancel_button: Button
var more_button: Button
var website_button: Button
var choose_button: Button
var clear_button: Button
var use_button: Button
var preview_button: Button
var geometry_window: Window
var tree: Tree
var status: Label
var activity: ProgressBar
var thumbnails: CheckButton
var preview: TextureRect
var preview_note: Label
var thumbnail: Node
var disclosure: Label
var details: Label
var provider_status: Label
var directory_label: Label
var link_row: HFlowContainer
var link_variant: OptionButton
var picker: FileDialog
var selected := {}
var visible_rows: Array = []
var directories: Array = []
var _site_ids: Array = ["All"]
var _refresh_pending := false
var _render_signature := ""
var _display_keys: Array = []
var _open_error := ""
var _settings_error := ""
var _restoring := true
var _last_tab := 0
var _local_format := "All"
var _online_format := "All"
var _scrollbar: VScrollBar
var _batch_generation := 0
var _batch_check_pending := false
# Tests inject a browser opener, never launch a real browser during automation.
var page_opener: Callable
var retrieval_context: Callable
var retrieval_notice: ConfirmationDialog
var dismissed_notices := {}

func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	online = Service.new(); add_child(online)
	local = LocalScan.new(); add_child(local)
	thumbnail = Thumbnail.new(); add_child(thumbnail)
	retrieval_notice = RetrievalNotice.new(); add_child(retrieval_notice)
	retrieval_notice.source_confirmed.connect(func(url, provider, remember):
		if remember: dismissed_notices[provider] = true; save_preferences()
		_open_source(url); _schedule_refresh())
	thumbnail.changed.connect(func():
		if is_instance_valid(preview): preview.texture = thumbnail.texture; preview_note.text = thumbnail.message
		_schedule_refresh())
	online.changed.connect(_schedule_refresh); local.changed.connect(_schedule_refresh)
	var heading := Label.new(); heading.text = "Asset discovery"; heading.add_theme_font_size_override("font_size", 22); add_child(heading)
	tabs = TabBar.new(); tabs.add_tab("Local"); tabs.add_tab("Online"); add_child(tabs)
	tabs.tab_changed.connect(_tab_changed)
	var filters := HBoxContainer.new(); add_child(filters)
	search = LineEdit.new(); search.placeholder_text = "Search filenames or model names"; search.max_length = 200
	search.size_flags_horizontal = Control.SIZE_EXPAND_FILL; filters.add_child(search)
	search.text_submitted.connect(func(_text): run_search())
	search.text_changed.connect(func(_text):
		if tabs.current_tab == 0: _schedule_refresh())
	website = OptionButton.new(); website.add_item("All websites"); filters.add_child(website)
	for source in Catalog.PROVIDERS: website.add_item(source.name); _site_ids.append(source.id)
	website.item_selected.connect(func(_index): run_search())
	format_filter = OptionButton.new(); filters.add_child(format_filter)
	for value in Catalog.FORMATS: format_filter.add_item("All formats" if value == "All" else value)
	format_filter.tooltip_text = "Metadata/filename labels, not verified import compatibility. Source MDL does not establish SFM or GMod compatibility."
	format_filter.item_selected.connect(func(_index): run_search())
	search_button = _button(filters, "Search", run_search)
	var controls := HFlowContainer.new(); add_child(controls)
	choose_button = _button(controls, "Choose directory…", func(): picker.popup_centered(Vector2i(800, 540)))
	clear_button = _button(controls, "Clear directories", func(): directories.clear(); local.start([]); save_preferences(); _schedule_refresh())
	network = CheckButton.new(); network.text = "Enable online access"; controls.add_child(network)
	network.toggled.connect(func(enabled): _batch_generation += 1; online.set_network(enabled); _update_thumbnail(); _schedule_refresh())
	expand = CheckButton.new(); expand.text = "Expand names"; expand.button_pressed = true; controls.add_child(expand)
	expand.tooltip_text = "Full name, reordered words, documented aliases and individual keywords. No translation service."
	expand.toggled.connect(func(_enabled): run_search())
	cancel_button = _button(controls, "Cancel", cancel)
	more_button = _button(controls, "Load another batch", _next_batch)
	website_button = _button(controls, "Open website search", func(): open_page(Catalog.website_url(_site_ids[website.selected], search.text)))
	website_button.tooltip_text = "Choose a website filter, then open its search page in your default browser."
	thumbnails = CheckButton.new(); thumbnails.text = "Thumbnail preview"; controls.add_child(thumbnails)
	thumbnails.tooltip_text = "Optional selected-item image only. At most 1 MiB per image; no model files. Online access must also be enabled."
	thumbnails.toggled.connect(func(_value): _update_thumbnail())
	directory_label = _label(); add_child(directory_label)
	disclosure = _label(); disclosure.add_theme_font_size_override("font_size", 12); add_child(disclosure)
	status = _label(); add_child(status)
	activity = ProgressBar.new(); activity.indeterminate = true; activity.show_percentage = false
	activity.custom_minimum_size.y = 6; add_child(activity)
	tree = Tree.new(); tree.columns = 4; tree.hide_root = true; tree.column_titles_visible = true
	tree.set_column_title(0, "Title / filename"); tree.set_column_title(1, "Source website / location")
	tree.set_column_title(2, "Format labels"); tree.set_column_title(3, "Access")
	for column in 4: tree.set_column_expand(column, column < 2); tree.set_column_custom_minimum_width(column, [240, 180, 110, 150][column])
	tree.size_flags_vertical = Control.SIZE_EXPAND_FILL; tree.custom_minimum_size.y = 180; add_child(tree)
	tree.item_selected.connect(_select)
	_scrollbar = _find_vertical_scrollbar(tree)
	if _scrollbar: _scrollbar.gui_input.connect(_scroll_intent.bind(true))
	tree.gui_input.connect(func(event):
		_scroll_intent(event)
		if tabs.current_tab != 1: return
		if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed and not event.double_click:
			var item := tree.get_item_at_position(event.position)
			if item:
				selected = item.get_metadata(0); _reconcile_selection(_current_visible_rows())
				if not selected.is_empty(): open_page(selected.get("url", ""))
		elif event is InputEventKey and event.keycode in [KEY_ENTER, KEY_KP_ENTER] and event.pressed and not event.echo: open_selected())
	var detail_row := HBoxContainer.new(); add_child(detail_row)
	details = _label(); details.custom_minimum_size.y = 48; details.size_flags_horizontal = Control.SIZE_EXPAND_FILL; detail_row.add_child(details)
	var preview_box := VBoxContainer.new(); detail_row.add_child(preview_box)
	preview = TextureRect.new(); preview.custom_minimum_size = Vector2(96, 96); preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED; preview_box.add_child(preview)
	preview_note = _label(); preview_note.custom_minimum_size.x = 150; preview_note.add_theme_font_size_override("font_size", 11); preview_box.add_child(preview_note)
	var local_actions := HBoxContainer.new(); add_child(local_actions)
	preview_button = _button(local_actions, "Preview GLB geometry", _preview_local)
	preview_button.tooltip_text = "Explicit local preview only: self-contained GLB up to 8 MiB. Materials and animation are omitted; no conversion or project edit."
	use_button = _button(local_actions, "Use selected local file", _use_local); use_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	use_button.tooltip_text = "Passes the filename to the parent for explicit import. Browsing does not load models."
	var providers_toggle := CheckButton.new(); providers_toggle.text = "Show provider details and website searches"; add_child(providers_toggle)
	var provider_box := VBoxContainer.new(); provider_box.visible = false; add_child(provider_box)
	providers_toggle.toggled.connect(func(enabled): provider_box.visible = enabled)
	link_variant = OptionButton.new(); provider_box.add_child(link_variant)
	link_variant.tooltip_text = "Choose a query variation for website search. SFMLab and VRoid open their home/search UI."
	link_row = HFlowContainer.new(); provider_box.add_child(link_row)
	for source in Catalog.PROVIDERS:
		var id: String = source.id
		var link := _button(link_row, source.name, func():
			var text := search.text
			if link_variant.item_count > 0: text = link_variant.get_item_metadata(link_variant.selected)
			open_page(Catalog.website_url(id, text)))
		link.tooltip_text = source.mode + ": " + source.note
	var scroll := ScrollContainer.new(); scroll.custom_minimum_size.y = 105; scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; provider_box.add_child(scroll)
	provider_status = _label(); provider_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(provider_status)
	picker = FileDialog.new(); picker.title = "Choose a local model directory"; picker.file_mode = FileDialog.FILE_MODE_OPEN_DIR
	picker.access = FileDialog.ACCESS_FILESYSTEM; picker.use_native_dialog = false; add_child(picker)
	picker.dir_selected.connect(add_directory)
	load_preferences()
	_tab_changed(tabs.current_tab)
	_restoring = false
	if tabs.current_tab == 0 and not directories.is_empty(): local.start(directories)

func load_preferences() -> void:
	var result := Preferences.read_file(preferences_path)
	_settings_error = result.get("error", "")
	var data: Dictionary = result.get("data", Preferences.defaults())
	directories = data.directories
	dismissed_notices = data.dismissed_notices
	_local_format = data.local_format; _online_format = data.online_format
	website.select(_site_ids.find(data.website))
	expand.set_pressed_no_signal(data.expand)
	_last_tab = data.tab; tabs.current_tab = data.tab
	format_filter.select(Catalog.FORMATS.find(_local_format if data.tab == 0 else _online_format))

func save_preferences() -> void:
	if _restoring: return
	if tabs.current_tab == 0: _local_format = Catalog.FORMATS[format_filter.selected]
	else: _online_format = Catalog.FORMATS[format_filter.selected]
	_settings_error = Preferences.write_file(preferences_path, {"version":1, "directories":directories, "website":_site_ids[website.selected], "local_format":_local_format, "online_format":_online_format, "expand":expand.button_pressed, "tab":tabs.current_tab, "dismissed_notices":dismissed_notices})

func _label() -> Label:
	var label := Label.new(); label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

func _button(parent: Node, text: String, action: Callable) -> Button:
	var button := Button.new(); button.text = text; button.pressed.connect(action); parent.add_child(button)
	return button

func add_directory(path: String) -> void:
	if directories.size() >= Preferences.MAX_DIRECTORIES and path not in directories:
		_settings_error = "Keep at most 32 local directories. Clear directories to start over."
		_schedule_refresh(); return
	if path not in directories: directories.append(path)
	local.start(directories)
	save_preferences()

func _tab_changed(index: int) -> void:
	if not _restoring and _last_tab != index:
		if _last_tab == 0: _local_format = Catalog.FORMATS[format_filter.selected]
		else: _online_format = Catalog.FORMATS[format_filter.selected]
		format_filter.select(Catalog.FORMATS.find(_local_format if index == 0 else _online_format))
	_last_tab = index
	cancel()
	var is_online := index == 1
	website.visible = is_online; network.visible = is_online; expand.visible = is_online; more_button.visible = is_online
	website_button.visible = is_online
	thumbnails.visible = is_online
	choose_button.visible = not is_online; clear_button.visible = not is_online; use_button.visible = not is_online
	preview_button.get_parent().visible = not is_online
	directory_label.visible = not is_online
	selected = {}; _render_signature = ""; _schedule_refresh()
	_update_thumbnail()
	if not _restoring:
		save_preferences()
		if index == 0 and not directories.is_empty() and local.rows.is_empty(): local.start(directories)
	# Opening the tab alone never opts into networking.

func run_search() -> void:
	if _restoring: return
	_batch_generation += 1
	save_preferences()
	_open_error = ""
	selected = {}; _render_signature = ""
	if tabs.current_tab == 0:
		_schedule_refresh()
	else:
		online.search(search.text, _site_ids[website.selected], Catalog.FORMATS[format_filter.selected], expand.button_pressed)

func cancel() -> void:
	_batch_generation += 1
	if is_instance_valid(retrieval_notice): retrieval_notice.dismiss()
	if is_instance_valid(thumbnail): thumbnail.cancel()
	if is_instance_valid(online): online.cancel()
	if is_instance_valid(local): local.cancel()
	_schedule_refresh()

func _find_vertical_scrollbar(node: Node) -> VScrollBar:
	# Tree owns internal scrollbars in pinned Godot 4.6; no public getter exists.
	# Prefer its own bar over a hidden editor's nested TextEdit scrollbar.
	for child in node.get_children(true):
		if child is VScrollBar: return child
	for child in node.get_children(true):
		var found := _find_vertical_scrollbar(child)
		if found: return found
	return null

func _next_batch() -> void:
	_batch_generation += 1
	online.fetch_more()

func _scroll_intent(event: InputEvent, scrollbar_input := false) -> void:
	if tabs.current_tab != 1 or _batch_check_pending: return
	var scrolling := event is InputEventPanGesture
	if event is InputEventMouseButton:
		scrolling = event.pressed and (event.button_index == MOUSE_BUTTON_WHEEL_DOWN or (scrollbar_input and event.button_index == MOUSE_BUTTON_LEFT))
	elif event is InputEventMouseMotion:
		scrolling = scrollbar_input and event.button_mask & MOUSE_BUTTON_MASK_LEFT != 0
	elif event is InputEventKey:
		scrolling = event.pressed and event.keycode in [KEY_DOWN, KEY_PAGEDOWN, KEY_END]
	if not scrolling: return
	_batch_check_pending = true
	_check_scroll_batch.call_deferred(_batch_generation)

func _check_scroll_batch(generation: int) -> void:
	_batch_check_pending = false
	if generation != _batch_generation or not is_inside_tree() or not is_instance_valid(_scrollbar): return
	if tabs.current_tab != 1 or not online.network_enabled or online.loading or not online.has_more or online.rows.is_empty(): return
	var bottom := _scrollbar.max_value - _scrollbar.page
	# Only explicit scrolling reaches here. Rendering, theme changes and restoring
	# an anchor must never chain requests merely because the list fits the viewport.
	if bottom > 0 and _scrollbar.value >= bottom - 1: _next_batch()

func _schedule_refresh() -> void:
	if _refresh_pending: return
	_refresh_pending = true
	_refresh.call_deferred()

func _current_visible_rows() -> Array:
	var is_online := tabs.current_tab == 1
	var query := search.text.strip_edges()
	var choices := Catalog.variations(query, expand.button_pressed if is_online else false)
	var rows: Array = []
	for row in online.rows if is_online else local.rows:
		# Online rows already belong to the submitted query. Do not refilter them
		# against unsubmitted text and misrepresent the provider request context.
		if is_online or Catalog.matches(row, query, choices, Catalog.FORMATS[format_filter.selected]): rows.append(row)
	return rows

func _reconcile_selection(rows: Array) -> void:
	if selected.is_empty(): return
	var key := Catalog.identity(selected)
	for row in rows:
		if Catalog.identity(row) == key:
			selected = row
			return
	selected = {}
	if is_instance_valid(tree): tree.deselect_all()

func _refresh() -> void:
	_refresh_pending = false
	if not is_inside_tree() or not is_instance_valid(tree): return
	var is_online := tabs.current_tab == 1
	var query := search.text.strip_edges()
	var choices := Catalog.variations(query, expand.button_pressed if is_online else false)
	visible_rows = _current_visible_rows()
	_reconcile_selection(visible_rows)
	var signature := str(visible_rows) + str(is_online)
	if signature != _render_signature:
		_render_signature = signature
		var new_keys: Array = []
		for row in visible_rows: new_keys.append(Catalog.identity(row))
		var append_only := new_keys.size() >= _display_keys.size() and new_keys.slice(0, _display_keys.size()) == _display_keys and tree.get_root() != null
		var anchor := tree.get_item_at_position(Vector2(12, 48))
		var anchor_key := Catalog.identity(anchor.get_metadata(0)) if anchor else ""
		var key := Catalog.identity(selected)
		var first := _display_keys.size() if append_only else 0
		if not append_only: tree.clear(); tree.create_item()
		var root := tree.get_root()
		for row in visible_rows.slice(first):
			var item := tree.create_item(root); item.set_metadata(0, row)
			item.set_text(0, row.title)
			item.set_text(1, Catalog.provider(row.provider).get("name", "Local") if is_online else row.path.get_base_dir())
			item.set_text(2, (", ".join(row.formats) + (" (inferred)" if is_online else "")) if not row.formats.is_empty() else "Unknown")
			item.set_text(3, ", ".join(row.access))
			for column in 4: item.set_tooltip_text(column, row.get("url", "") + "\n" + row.evidence)
			if Catalog.identity(row) == key: item.select(0)
			if not append_only and Catalog.identity(row) == anchor_key: tree.scroll_to_item.call_deferred(item)
		_display_keys = new_keys
	status.text = online.message if is_online else local.message + "  Showing %d." % visible_rows.size()
	if is_online:
		for source in online.statuses:
			var note := str(online.statuses[source])
			if note.contains("retry") or note.contains("Malformed") or note.contains("Rejected"):
				status.text += "\n" + Catalog.provider(source).get("name", source) + ": " + note
	directory_label.text = "Directories: " + ("; ".join(directories) if not directories.is_empty() else "none selected")
	disclosure.text = "Click an online listing to open its source page. No model files are downloaded."
	if is_online:
		disclosure.text += "\nScroll to the bottom for another batch, or use Load another batch."
		disclosure.text += "\nQuery variations: " + (", ".join(online.variants) if not online.variants.is_empty() else "discovery feed")
		if not online.tried.is_empty(): disclosure.text += "\nAPI queries sent: " + "; ".join(online.tried)
		disclosure.text += "\nPoly Haven and BowlRoll match these variations against fetched metadata; BowlRoll covers recent feed entries only."
	else: disclosure.text = "Browsing lists filename extensions. GLB geometry preview is explicit and does not edit the project or start a converter. Source MDL compatibility is Unknown."
	cancel_button.disabled = not (online.loading or local.loading or thumbnail.loading)
	activity.visible = online.loading if is_online else local.loading
	more_button.disabled = online.loading or not online.has_more or not online.network_enabled
	website_button.disabled = website.selected == 0
	if not _open_error.is_empty(): status.text += "\n" + _open_error
	if not _settings_error.is_empty(): status.text += "\n" + _settings_error
	search_button.disabled = false
	var import_error := local_import_error(selected) if not is_online else ""
	use_button.disabled = selected.is_empty() or is_online or not import_error.is_empty()
	use_button.text = import_target_name + " import unavailable" if not import_error.is_empty() else "Use selected local file"
	use_button.tooltip_text = import_error if not import_error.is_empty() else "Passes the filename to the parent for explicit import. Browsing does not load models."
	preview_button.disabled = selected.is_empty() or is_online or str(selected.get("path", "")).get_extension().to_lower() != "glb"
	details.text = "Select a filename for its full path." if not is_online else "Access labels describe source metadata, not a verified download or permission to use the model."
	if not selected.is_empty(): details.text = str(selected.get("path", selected.get("url", ""))) + "\n" + str(selected.get("evidence", ""))
	if not import_error.is_empty(): details.text += "\n" + import_error
	if is_online and not selected.get("formats", []).is_empty(): details.text += "\nFormat hints are inferred from title/tags; file contents were not inspected."
	_update_thumbnail()
	var lines: Array = []
	for source in Catalog.PROVIDERS:
		lines.append(source.name + " — " + source.mode + ": " + str(online.statuses.get(source.id, source.note)))
	provider_status.text = "\n".join(lines)
	var old_variant := link_variant.selected
	link_variant.clear()
	for choice in choices if not choices.is_empty() else [""]:
		link_variant.add_item("Website query: " + (choice if not choice.is_empty() else "directory home"))
		link_variant.set_item_metadata(link_variant.item_count - 1, choice)
	link_variant.select(clampi(old_variant, 0, link_variant.item_count - 1))

func _select() -> void:
	var item := tree.get_selected()
	selected = item.get_metadata(0) if item else {}
	_reconcile_selection(_current_visible_rows())
	_schedule_refresh()

func _update_thumbnail() -> void:
	if not is_instance_valid(preview): return
	_reconcile_selection(_current_visible_rows())
	var enabled := tabs.current_tab == 1 and network.button_pressed and thumbnails.button_pressed
	preview.get_parent().visible = enabled
	thumbnail.set_enabled(enabled)
	if enabled: thumbnail.load_url(str(selected.get("thumbnail_url", "")))

func open_selected() -> void:
	_select()
	if tabs.current_tab == 1 and not selected.is_empty(): open_page(selected.get("url", ""))

func open_page(url: String) -> void:
	if not Catalog.safe_page(url):
		_open_error = "Cannot open this source URL. Only known HTTPS provider pages are allowed."
		status.text = _open_error
		return
	var provider := RetrievalNotice.provider_for_url(url)
	if not provider.is_empty() and not dismissed_notices.get(provider, false):
		var context_text := "Local installation status is Unknown. Studio has not checked your Steam libraries in this browser."
		if retrieval_context.is_valid(): context_text = str(retrieval_context.call(provider))
		retrieval_notice.present(url, provider, context_text)
		return
	_open_source(url)

func _open_source(url: String) -> void:
	if not Catalog.safe_page(url): return
	var error: int = page_opener.call(url) if page_opener.is_valid() else OS.shell_open(url)
	_open_error = "Could not open your default browser (%d)." % error if error != OK else ""
	if error != OK: status.text = _open_error
	else: source_page_opened.emit(url)

func current_local_selection() -> Dictionary:
	_reconcile_selection(_current_visible_rows())
	return selected if tabs.current_tab == 0 else {}

func local_import_error(row: Dictionary) -> String:
	if row.is_empty() or local_import_extensions.is_empty(): return ""
	var extension := str(row.get("path", "")).get_extension().to_lower()
	if extension in local_import_extensions: return ""
	return "%s cannot add .%s files here. Export a supported GLB first." % [import_target_name, extension]

func current_local_import() -> Dictionary:
	var row := current_local_selection()
	return row if local_import_error(row).is_empty() else {}

func _use_local() -> void:
	var row := current_local_import()
	if not row.is_empty(): local_file_selected.emit(row.path)

func _preview_local() -> void:
	var row := current_local_selection()
	if row.is_empty(): return
	if is_instance_valid(geometry_window): geometry_window.queue_free()
	var result := LocalPreview.open(self, str(row.get("path", "")))
	if result.has("error"): _open_error = result.error; status.text = _open_error
	else: geometry_window = result.window; _open_error = ""; _schedule_refresh()

func _exit_tree() -> void:
	if is_instance_valid(thumbnail): thumbnail.set_enabled(false)
	if is_instance_valid(online): online.cancel()
	if is_instance_valid(local): local.cancel()
