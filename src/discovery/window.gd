extends RefCounted
## Optional host wrapper. The browser itself can also be embedded in any Control.
const Browser = preload("res://src/discovery/browser.gd")
const StudioTheme = preload("res://src/studio_theme.gd")

static func open(owner: Node, on_local: Callable = Callable(), options: Dictionary = {}) -> Window:
	var window := Window.new()
	window.title = "Asset discovery"
	window.min_size = Vector2i(960, 700)
	window.transient = true; window.exclusive = false
	window.theme = StudioTheme.make_theme()
	owner.add_child(window)
	var background := Panel.new(); background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee")); window.add_child(background)
	var margin := MarginContainer.new(); margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "top", "right", "bottom"]: margin.add_theme_constant_override("margin_" + side, 12)
	window.add_child(margin)
	var browser := Browser.new(); browser.name = "Discovery"
	if options.has("preferences_path"): browser.preferences_path = options.preferences_path
	if options.get("local_import_extensions") is Array: browser.local_import_extensions = options.local_import_extensions
	margin.add_child(browser)
	window.set_meta("discovery_panel", browser)
	browser.local_file_selected.connect(func(path):
		if on_local.is_valid():
			if str(browser.current_local_import().get("path", "")) != path: return
			_finish_close(window, browser, on_local, path)
		else: browser.status.text = "Selected local filename: " + path)
	window.close_requested.connect(func(): _finish_close(window, browser))
	window.popup_centered(Vector2i(1200, 820))
	return window

static func _finish_close(window: Window, browser: Node, on_local: Callable = Callable(), path: String = "") -> void:
	if window.has_meta("discovery_closing"): return
	window.set_meta("discovery_closing", true)
	var tree := window.get_tree()
	browser.cancel(); window.hide()
	# Native requests and the nested service coroutines need a frame to unwind.
	# Freeing their owner within the click callback can leave FunctionState resources.
	await tree.process_frame
	# The file must still be selected/visible when the deferred close commits.
	var accept_local := on_local.is_valid() and is_instance_valid(browser)
	if accept_local: accept_local = str(browser.current_local_import().get("path", "")) == path
	if is_instance_valid(window): window.queue_free()
	await tree.process_frame
	if accept_local and on_local.is_valid(): on_local.call_deferred(path)
