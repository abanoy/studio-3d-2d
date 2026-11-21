extends VBoxContainer
## Drop-in discovery panel. Parent supplies any explicit local import action.
signal local_file_selected(path: String)
signal source_page_opened(url: String)
const Catalog = preload("res://src/discovery/catalog.gd")
const Service = preload("res://src/discovery/service.gd")
const LocalScan = preload("res://src/discovery/local_scan.gd")
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
var choose_button: Button
var clear_button: Button
var use_button: Button
var tree: Tree
var status: Label
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
# Tests inject a browser opener, never launch a real browser during automation.
var page_opener: Callable

func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	online = Service.new(); add_child(online)
	local = LocalScan.new(); add_child(local)
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
	clear_button = _button(controls, "Clear directories", func(): directories.clear(); local.start([]); _schedule_refresh())
	network = CheckButton.new(); network.text = "Enable online access"; controls.add_child(network)
	network.toggled.connect(func(enabled): online.set_network(enabled); _schedule_refresh())
	expand = CheckButton.new(); expand.text = "Expand names"; expand.button_pressed = true; controls.add_child(expand)
	expand.tooltip_text = "Full name, reordered words, documented aliases and individual keywords. No translation service."
	expand.toggled.connect(func(_enabled): run_search())
	cancel_button = _button(controls, "Cancel", cancel)
	more_button = _button(controls, "Load another batch", func(): online.fetch_more())
	directory_label = _label(); add_child(directory_label)
	disclosure = _label(); disclosure.add_theme_font_size_override("font_size", 12); add_child(disclosure)
	status = _label(); add_child(status)
	tree = Tree.new(); tree.columns = 4; tree.hide_root = true; tree.column_titles_visible = true
	tree.set_column_title(0, "Title / filename"); tree.set_column_title(1, "Source website / location")
	tree.set_column_title(2, "Format labels"); tree.set_column_title(3, "Access")
	for column in 4: tree.set_column_expand(column, column < 2); tree.set_column_custom_minimum_width(column, [240, 180, 110, 150][column])
	tree.size_flags_vertical = Control.SIZE_EXPAND_FILL; tree.custom_minimum_size.y = 180; add_child(tree)
	tree.item_selected.connect(_select)
	tree.gui_input.connect(func(event):
		if tabs.current_tab != 1: return
		if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed and not event.double_click:
			var item := tree.get_item_at_position(event.position)
			if item: selected = item.get_metadata(0); open_page(selected.get("url", ""))
		elif event is InputEventKey and event.keycode in [KEY_ENTER, KEY_KP_ENTER] and event.pressed and not event.echo: open_selected())
	details = _label(); details.custom_minimum_size.y = 48; add_child(details)
	use_button = _button(self, "Use selected local file", _use_local)
	use_button.tooltip_text = "Passes the filename to the parent. This panel never loads or converts the model."
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
	_tab_changed(0)

func _label() -> Label:
	var label := Label.new(); label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

func _button(parent: Node, text: String, action: Callable) -> Button:
	var button := Button.new(); button.text = text; button.pressed.connect(action); parent.add_child(button)
	return button

func add_directory(path: String) -> void:
	if path not in directories: directories.append(path)
	local.start(directories)

func _tab_changed(index: int) -> void:
	cancel()
	var is_online := index == 1
	website.visible = is_online; network.visible = is_online; expand.visible = is_online; more_button.visible = is_online
	choose_button.visible = not is_online; clear_button.visible = not is_online; use_button.visible = not is_online
	directory_label.visible = not is_online
	selected = {}; _render_signature = ""; _schedule_refresh()
	# Opening the tab alone never opts into networking.

func run_search() -> void:
	selected = {}; _render_signature = ""
	if tabs.current_tab == 0:
		_schedule_refresh()
	else:
		online.search(search.text, _site_ids[website.selected], Catalog.FORMATS[format_filter.selected], expand.button_pressed)

func cancel() -> void:
	if is_instance_valid(online): online.cancel()
	if is_instance_valid(local): local.cancel()
	_schedule_refresh()

func _schedule_refresh() -> void:
	if _refresh_pending: return
	_refresh_pending = true
	_refresh.call_deferred()

func _refresh() -> void:
	_refresh_pending = false
	if not is_inside_tree() or not is_instance_valid(tree): return
	var is_online := tabs.current_tab == 1
	var query := search.text.strip_edges()
	var choices := Catalog.variations(query, expand.button_pressed if is_online else false)
	visible_rows = []
	for row in online.rows if is_online else local.rows:
		# Online rows already belong to the submitted query. Do not refilter them
		# against unsubmitted text and misrepresent the provider request context.
		if is_online or Catalog.matches(row, query, choices, Catalog.FORMATS[format_filter.selected]): visible_rows.append(row)
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
			item.set_text(2, ", ".join(row.formats) if not row.formats.is_empty() else "Unknown")
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
		disclosure.text += "\nQuery variations: " + (", ".join(online.variants) if not online.variants.is_empty() else "discovery feed")
		if not online.tried.is_empty(): disclosure.text += "\nAPI queries sent: " + "; ".join(online.tried)
		disclosure.text += "\nPoly Haven and BowlRoll match these variations against fetched metadata; BowlRoll covers recent feed entries only."
	else: disclosure.text = "Filename extensions only. No model loading, conversion or execution. Source MDL compatibility is Unknown."
	cancel_button.disabled = not (online.loading or local.loading)
	more_button.disabled = online.loading or not online.has_more or not online.network_enabled
	search_button.disabled = false
	use_button.disabled = selected.is_empty() or is_online
	details.text = "Select a filename for its full path." if not is_online else "Access labels describe source metadata, not a verified download or permission to use the model."
	if not selected.is_empty(): details.text = str(selected.get("path", selected.get("url", ""))) + "\n" + str(selected.get("evidence", ""))
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
	_schedule_refresh()

func open_selected() -> void:
	_select()
	if tabs.current_tab == 1 and not selected.is_empty(): open_page(selected.get("url", ""))

func open_page(url: String) -> void:
	if not Catalog.safe_page(url):
		status.text = "Cannot open this source URL. Only known HTTPS provider pages are allowed."
		return
	var error: int = page_opener.call(url) if page_opener.is_valid() else OS.shell_open(url)
	if error != OK: status.text = "Could not open your default browser (%d)." % error
	else: source_page_opened.emit(url)

func _use_local() -> void:
	if tabs.current_tab == 0 and not selected.is_empty(): local_file_selected.emit(selected.path)

func _exit_tree() -> void:
	if is_instance_valid(online): online.cancel()
	if is_instance_valid(local): local.cancel()
