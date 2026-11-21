extends RefCounted
## Optional host wrapper. The browser itself can also be embedded in any Control.
const Browser = preload("res://src/discovery/browser.gd")
const StudioTheme = preload("res://src/studio_theme.gd")

static func open(owner: Node, on_local: Callable = Callable()) -> Window:
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
	var browser := Browser.new(); browser.name = "Discovery"; margin.add_child(browser)
	window.set_meta("discovery_panel", browser)
	browser.local_file_selected.connect(func(path):
		if on_local.is_valid():
			browser.cancel(); window.hide(); window.queue_free()
			# Let the window close before the ordinary import pipeline's busy check.
			on_local.call_deferred(path)
		else: browser.status.text = "Selected local filename: " + path)
	window.close_requested.connect(func(): browser.cancel(); window.hide(); window.queue_free())
	window.popup_centered(Vector2i(1200, 820))
	return window
