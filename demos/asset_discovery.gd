extends SceneTree
const Browser = preload("res://src/discovery/browser.gd")
const StudioTheme = preload("res://src/studio_theme.gd")

func _initialize() -> void:
	call_deferred("_open")

func _open() -> void:
	root.title = "Hybrid Animation Studio — Asset discovery demo"
	root.size = Vector2i(1240, 860)
	root.min_size = Vector2i(960, 700)
	root.theme = StudioTheme.make_theme()
	var background := Panel.new(); background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee")); root.add_child(background)
	var margin := MarginContainer.new(); margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "top", "right", "bottom"]: margin.add_theme_constant_override("margin_" + side, 16)
	root.add_child(margin)
	var box := VBoxContainer.new(); margin.add_child(box)
	var styles := OptionButton.new(); styles.add_item("Neon"); styles.add_item("Classic light"); styles.add_item("Classic dark"); box.add_child(styles)
	styles.item_selected.connect(func(index): StudioTheme.set_style(["neon", "light", "dark"][index]); root.theme = StudioTheme.make_theme(); background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee")))
	var browser := Browser.new(); box.add_child(browser)
	browser.local_file_selected.connect(func(path): browser.status.text = "Selected for parent integration: " + path + ". This standalone demo does not import files.")
