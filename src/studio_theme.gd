extends RefCounted
# Original vector artwork and nine-patch gradients, rasterized by Godot itself.
# No downloaded icon pack, native OS artwork, fonts or image-model assets.
static var icons := {}
# Redesign: opt-in dark theme (editor only, off by default). tone() maps the light palette's
# neutrals and text to dark equivalents; saturated accents stay as they are.
static var dark := false

static func tone(c: Color) -> Color:
	if not dark or (c.s > 0.45 and c.v > 0.45): return c
	return Color.from_hsv(c.h, c.s * 0.6, clampf(1.06 - c.v, 0.12, 0.92), c.a)

static func tone_hex(hex: String) -> String:
	return tone(Color(hex)).to_html(false) if dark else hex

static func svg_texture(body: String, width := 32, height := 32) -> ImageTexture:
	var image := Image.new()
	var svg := '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % [width, height, width, height, body]
	var error := image.load_svg_from_string(svg)
	assert(error == OK, "Studio vector artwork failed to render")
	return ImageTexture.create_from_image(image)

static func surface(top: String, bottom: String, edge := "9ca9b3", inset := 7) -> StyleBoxTexture:
	top = tone_hex(top); bottom = tone_hex(bottom); edge = tone_hex(edge)
	var body := '<defs><linearGradient id="g" x2="0" y2="1"><stop stop-color="#%s"/><stop offset="0.48" stop-color="#%s"/><stop offset="1" stop-color="#%s"/></linearGradient></defs><rect x="1" y="1" width="62" height="62" rx="6" fill="url(#g)" stroke="#%s"/><path d="M8 3H56" stroke="white" stroke-opacity="0.65"/>' % [top, top, bottom, edge]
	var style := StyleBoxTexture.new()
	style.texture = svg_texture(body, 64, 64)
	style.set_texture_margin_all(8)
	style.content_margin_left = inset + 3
	style.content_margin_right = inset + 3
	style.content_margin_top = inset
	style.content_margin_bottom = inset
	return style

static func make_theme() -> Theme:
	var result := Theme.new()
	result.default_font_size = 14
	for type in ["Label", "Button", "OptionButton", "CheckButton", "CheckBox", "MenuButton", "LineEdit", "PopupMenu", "SpinBox"]:
		result.set_color("font_color", type, tone(Color("283c51")))
		result.set_color("font_hover_color", type, tone(Color("163854")))
		result.set_color("font_pressed_color", type, tone(Color("163854")))
		result.set_color("font_hover_pressed_color", type, tone(Color("163854")))
		result.set_color("font_disabled_color", type, tone(Color("7f8992")))
		result.set_color("font_focus_color", type, tone(Color("163854")))
	var normal := surface("ffffff", "d6e0e8")
	var hover := surface("ffffff", "bddcf5", "628db9")
	var pressed := surface("bdd7f0", "e5f2fc", "4c7fab")
	var focus := StyleBoxFlat.new()
	focus.bg_color = Color.TRANSPARENT
	focus.set_border_width_all(2)
	focus.border_color = tone(Color("4384bd"))
	focus.set_corner_radius_all(5)
	for type in ["Button", "OptionButton", "MenuButton"]:
		for state in ["normal", "disabled"]: result.set_stylebox(state, type, normal)
		result.set_stylebox("hover", type, hover)
		result.set_stylebox("pressed", type, pressed)
		result.set_stylebox("focus", type, focus)
		result.set_constant("h_separation", type, 6)
		result.set_constant("outline_size", type, 0)
	result.set_stylebox("normal", "LineEdit", surface("ffffff", "f5f8fa", "a0adb9", 6))
	result.set_stylebox("focus", "LineEdit", focus)
	result.set_color("caret_color", "LineEdit", tone(Color("254c74")))
	result.set_color("selection_color", "LineEdit", tone(Color("b5d8f8")))
	result.set_color("font_selected_color", "LineEdit", tone(Color("163854")))
	for type in ["TextEdit","CodeEdit"]:
		result.set_color("font_color",type,tone(Color("283c51")))
		result.set_color("font_selected_color",type,tone(Color("163854")))
		result.set_color("selection_color",type,tone(Color("b5d8f8")))
		result.set_color("caret_color",type,tone(Color("254c74")))
	result.set_color("default_color","RichTextLabel",tone(Color("283c51")))
	result.set_color("font_selected_color","RichTextLabel",tone(Color("163854")))
	result.set_color("selection_color","RichTextLabel",tone(Color("b5d8f8")))
	result.set_color("font_placeholder_color", "LineEdit", tone(Color("6d7f90")))
	result.set_stylebox("panel", "PanelContainer", surface("fafbfd", "e9edf0", "b5c1cb", 10))
	result.set_stylebox("panel", "PopupMenu", surface("ffffff", "e8eff6", "8095a8"))
	result.set_stylebox("hover", "PopupMenu", hover)
	result.set_color("font_hover_color", "PopupMenu", tone(Color("163854")))
	result.set_color("font_color", "TooltipLabel", tone(Color("283c51")))
	result.set_stylebox("panel", "TooltipPanel", surface("fffde7", "fff8cf", "a69a70"))
	result.set_stylebox("panel", "AcceptDialog", surface("fafbfd", "e4eaf0", "8095a8"))
	result.set_stylebox("panel", "ItemList", surface("ffffff", "f1f6fa", "a0adb9", 4))
	result.set_stylebox("selected", "ItemList", hover)
	result.set_stylebox("selected_focus", "ItemList", hover)
	result.set_color("font_color", "ItemList", tone(Color("283c51")))
	result.set_color("font_selected_color", "ItemList", tone(Color("163854")))
	result.set_stylebox("panel", "Tree", surface("ffffff", "f1f6fa", "a0adb9", 4))
	result.set_stylebox("selected", "Tree", hover)
	result.set_stylebox("selected_focus", "Tree", hover)
	result.set_color("font_color", "Tree", tone(Color("283c51")))
	result.set_color("font_selected_color", "Tree", tone(Color("163854")))
	result.set_color("font_color", "CheckButton", tone(Color("283c51")))
	result.set_constant("separation", "VBoxContainer", 7)
	result.set_constant("separation", "HBoxContainer", 7)
	return result

static func icon(kind: String) -> Texture2D:
	if icons.has(kind): return icons[kind]
	var shapes := {
		"fan": '<circle cx="16" cy="13" r="11" fill="url(#blue)" stroke="#315f86"/><path d="M16 12C6 2 5 14 14 15c-10 9 3 13 3 2 10 6 13-7 1-5Z" fill="#f2f7fc" stroke="#668ba5"/><circle cx="16" cy="14" r="2" fill="#3878b6"/><path d="M16 24v5M9 30h14" stroke="#527b97" stroke-width="3"/>',
		"folder": '<path d="M3 9V6h10l3 4h13v17H3Z" fill="url(#gold)" stroke="#987032"/><path d="M3 14h27l-4 13H3Z" fill="url(#gold)" stroke="#987032"/>',
		"save": '<path d="M5 3h21l3 4v22H4V3Z" fill="url(#blue)" stroke="#315f86"/><path d="M10 3h12v10H10Z" fill="#f2f7fc"/><path d="M9 18h15v11H9Z" fill="white" stroke="#7892aa"/><path d="M12 22h9m-9 3h9" stroke="#92a7b8"/>',
		"scene": '<path d="m16 3 13 7v14l-13 6L3 24V10Z" fill="url(#blue)" stroke="#315f86"/><path d="m3 10 13 7 13-7M16 17v13" fill="none" stroke="#f5fbff"/><path d="m16 3 13 7-13 7-13-7Z" fill="#a4ddfa"/>',
		"audio": '<path d="M13 6v17M25 3v17M13 6l12-3v6l-12 3" stroke="#52713d" fill="url(#green)" stroke-width="3"/><ellipse cx="9" cy="25" rx="6" ry="4" fill="url(#green)" stroke="#52713d"/><ellipse cx="21" cy="22" rx="6" ry="4" fill="url(#green)" stroke="#52713d"/>',
		"export": '<rect x="3" y="10" width="26" height="19" rx="3" fill="url(#blue)" stroke="#315f86"/><path d="M13 22V11H7L16 2l9 9h-6v11Z" fill="url(#green)" stroke="#52713d"/>',
		"draw": '<path d="m5 24 3-8L23 2l7 7-15 15-8 4Z" fill="url(#gold)" stroke="#987032"/><path d="m5 24 2 4 8-4-7-8Z" fill="#fff0cc"/><path d="m5 24 2 4 3-1-4-4Z" fill="#354553"/><path d="m20 5 7 7" stroke="white" stroke-width="2"/>',
		# Redesign: original icons for the Simple tool strip, Pose tab, Add menu and layers.
		"eraser": '<path d="m4 20 12-14 12 10-10 12H10Z" fill="#f4b7c2" stroke="#9a4f60"/><path d="m4 20 8-9 10 8-6 7" fill="#fbe3e8"/><path d="M6 29h22" stroke="#7892aa" stroke-width="2"/>',
		"fill": '<path d="m6 14 10-10 11 11-10 10Z" fill="url(#blue)" stroke="#315f86"/><path d="M6 14h21" stroke="#f5fbff"/><path d="M27 18c2 4 3 6 1 8s-4-1-3-3Z" fill="#3878b6"/>',
		"picker": '<path d="M22 3l7 7-4 4-7-7Z" fill="#354553"/><path d="M18 7l7 7-12 12H6v-7Z" fill="#f5fbff" stroke="#315f86" stroke-width="2"/><path d="M6 26l-3 3" stroke="#315f86" stroke-width="3"/>',
		"figure": '<circle cx="16" cy="6" r="4" fill="url(#gold)" stroke="#987032"/><path d="M16 10v10M8 13l8 2 8-2M16 20l-5 9M16 20l5 9" fill="none" stroke="#315f86" stroke-width="3" stroke-linecap="round"/>',
		"add": '<circle cx="16" cy="16" r="13" fill="url(#green)" stroke="#52713d"/><path d="M16 9v14M9 16h14" stroke="white" stroke-width="4" stroke-linecap="round"/>',
		"pause": '<rect x="7" y="4" width="7" height="24" rx="2" fill="url(#green)" stroke="#52713d"/><rect x="18" y="4" width="7" height="24" rx="2" fill="url(#green)" stroke="#52713d"/>',
		"layers": '<path d="m16 4 13 6-13 6-13-6Z" fill="url(#blue)" stroke="#315f86"/><path d="m3 16 13 6 13-6M3 22l13 6 13-6" fill="none" stroke="#315f86" stroke-width="2"/>',
		"camera": '<rect x="3" y="9" width="26" height="19" rx="3" fill="url(#blue)" stroke="#315f86"/><path d="M9 9V4h12v5" fill="#93c4e4" stroke="#315f86"/><circle cx="16" cy="18" r="7" fill="#f5fbff" stroke="#315f86"/><circle cx="16" cy="18" r="4" fill="url(#blue)"/>',
		"play": '<path d="M8 3 29 16 8 29Z" fill="url(#green)" stroke="#52713d"/>',
		"undo": '<path d="M13 5 3 14l10 8v-6c12-3 15 5 11 12 12-11 3-22-11-18Z" fill="url(#blue)" stroke="#315f86"/>',
		"redo": '<g transform="translate(32 0) scale(-1 1)"><path d="M13 5 3 14l10 8v-6c12-3 15 5 11 12 12-11 3-22-11-18Z" fill="url(#blue)" stroke="#315f86"/></g>',
		"key": '<path d="m16 3 13 13-13 13L3 16Z" fill="url(#gold)" stroke="#987032"/><path d="m16 6 9 9H7Z" fill="white" fill-opacity="0.55"/>',
		"cel": '<rect x="5" y="3" width="22" height="27" rx="2" fill="#fff" stroke="#7892aa"/><path d="M10 18h12m-6-6v12" stroke="#4384bd" stroke-width="3"/>',
		"help": '<circle cx="16" cy="16" r="14" fill="url(#blue)" stroke="#315f86"/><path d="M11 11c0-6 12-6 11 1 0 4-6 3-6 8m0 4v2" fill="none" stroke="white" stroke-width="3"/>',
	}
	var defs := '<defs><linearGradient id="blue" x2="0.2" y2="1"><stop stop-color="#c3eeff"/><stop offset="0.45" stop-color="#77b8e8"/><stop offset="1" stop-color="#3878b6"/></linearGradient><linearGradient id="gold" x2="0.2" y2="1"><stop stop-color="#fff7c5"/><stop offset="0.5" stop-color="#f9d276"/><stop offset="1" stop-color="#d4a044"/></linearGradient><linearGradient id="green" x2="0.2" y2="1"><stop stop-color="#e5f8b5"/><stop offset="0.5" stop-color="#a7d77a"/><stop offset="1" stop-color="#679a42"/></linearGradient></defs>'
	icons[kind] = svg_texture(defs + shapes.get(kind, shapes.help))
	return icons[kind]
