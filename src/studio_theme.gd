extends RefCounted
# Original vector artwork and nine-patch gradients, rasterized by Godot itself.
# No downloaded icon pack, native OS artwork, fonts or image-model assets.
static var icons := {}
# Redesign: opt-in dark theme (editor only, off by default). tone() maps the light palette's
# neutrals and text to dark equivalents; saturated accents stay as they are.
static var dark := false
# Neon Pro port: interface style. "neon" = Midnight Neon (default), "light" = the classic skin
# exactly as before, "dark" = the classic skin re-toned by tone(). Editor chrome only: drawing
# paper, renders, saved projects and movies never depend on it.
static var style := "neon"
const STYLES := ["neon", "light", "dark"]
static var fonts := {}

# Midnight Neon tokens (docs/REDESIGN-PORT.md, neon theme sheet 1.1).
const BG := Color("08090c")
const BAR := Color("0c0d11")
const PANEL := Color("111318")
const RAISE := Color("171a21")
const HOVER := Color("1d2029")
const LINE := Color("22252e")
const LINE2 := Color("2c303b")
const LINE3 := Color("363b48")
const TEXT := Color("f4f6fa")
const TEXT2 := Color("b4bac7")
const TEXT3 := Color("8c93a3")
const BLUE := Color("2e8cff")
const PINK := Color("ff3d9a")
const MID := Color("9c5cff")
const FOCUS := Color("7b5cff")
const STAGE := Color("05060a")
const ON_NEON := Color("07080b")
const FIELD := Color("101218")
const POPUP := Color("101217")
const KBD := Color("13151b")
const TOOL_INNER := Color("171a22")
const SWITCH_INNER := Color("0e1016")
const TRACK := Color("272b35")
# Semantic colours (same meaning everywhere: timeline lanes, onion skin, badges, status).
const DRAWING := Color("4da3ff")  # drawings, onion "before"
const CAMERA := Color("ff5fae")   # camera keys, onion "after"
const MODEL := Color("a98bff")    # model / pose keys
const SAVED := Color("3ddc97")
const PROBLEM := Color("ff5a7a")
const WARNING := Color("ffc24b")
# The mock's `linear-gradient(in oklch, #2E8CFF, #FF3D9A)`; SVG has no oklch interpolation, so
# the ramp is precomputed in oklch and written as sRGB stops.
const NEON_STOPS := [["2e8cff", 0.0], ["8079ff", 0.25], ["b565f8", 0.5], ["df51d2", 0.75], ["ff3d9a", 1.0]]
const UI_FONTS := ["Geist", "Inter", "Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]
const MONO_FONTS := ["Geist Mono", "JetBrains Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono"]

static func set_style(name: String) -> void:
	style = name if name in STYLES else "neon"
	dark = style == "dark"

static func is_neon() -> bool:
	return style == "neon"

static func tone(c: Color) -> Color:
	if style == "neon":
		# Untouched legacy callers (light surfaces, mid-grey edges, dark text) land on neon tokens.
		if c.s > 0.45 and c.v > 0.45: return c
		var out := BAR if c.v > 0.9 else PANEL if c.v > 0.8 else LINE2 if c.v > 0.35 else TEXT
		out.a = c.a
		return out
	if not dark or (c.s > 0.45 and c.v > 0.45): return c
	return Color.from_hsv(c.h, c.s * 0.6, clampf(1.06 - c.v, 0.12, 0.92), c.a)

static func tone_hex(hex: String) -> String:
	return tone(Color(hex)).to_html(false) if dark or style == "neon" else hex

static func hex(c: Color) -> String:
	return "#" + c.to_html(false)

static func svg_texture(body: String, width := 32, height := 32, scale := 1.0) -> ImageTexture:
	var svg := '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % [width, height, width, height, body]
	return svg_image(svg, width, height, scale)

static func svg_image(svg: String, width: int, height: int, scale := 1.0) -> ImageTexture:
	# scale > 1 rasterizes extra pixels (crisp 1.5 px rings and HiDPI) while the texture keeps its
	# logical size, so controls, nine-patch margins and layouts measure exactly as at 1x.
	var image := Image.new()
	var error := image.load_svg_from_string(svg, scale)
	assert(error == OK, "Studio vector artwork failed to render")
	var texture := ImageTexture.create_from_image(image)
	if scale != 1.0: texture.set_size_override(Vector2i(width, height))
	return texture

static func surface(top: String, bottom: String, edge := "9ca9b3", inset := 7) -> StyleBoxTexture:
	var body: String
	if style == "neon":
		# Flat neon surface (no gradient or sheen); same content margins as the classic skin.
		body = '<rect x="0.5" y="0.5" width="63" height="63" rx="8" fill="#%s" stroke="#%s"/>' % [tone_hex(top), tone_hex(edge)]
	else:
		top = tone_hex(top); bottom = tone_hex(bottom); edge = tone_hex(edge)
		body = '<defs><linearGradient id="g" x2="0" y2="1"><stop stop-color="#%s"/><stop offset="0.48" stop-color="#%s"/><stop offset="1" stop-color="#%s"/></linearGradient></defs><rect x="1" y="1" width="62" height="62" rx="6" fill="url(#g)" stroke="#%s"/><path d="M8 3H56" stroke="white" stroke-opacity="0.65"/>' % [top, top, bottom, edge]
	var style_box := StyleBoxTexture.new()
	style_box.texture = svg_texture(body, 64, 64)
	style_box.set_texture_margin_all(8)
	style_box.content_margin_left = inset + 3
	style_box.content_margin_right = inset + 3
	style_box.content_margin_top = inset
	style_box.content_margin_bottom = inset
	return style_box

# ---- Neon building blocks -------------------------------------------------------------

static func neon_defs(id := "neon", vertical := false) -> String:
	var stops := ""
	for stop in NEON_STOPS: stops += '<stop offset="%s" stop-color="#%s"/>' % [stop[1], stop[0]]
	return '<linearGradient id="%s" x1="0" y1="0" x2="%d" y2="%d">%s</linearGradient>' % [id, 0 if vertical else 1, 1 if vertical else 0, stops]

static func flat(bg: Color, border := Color.TRANSPARENT, radius := 8, border_w := 0, pad := Vector4(-1, -1, -1, -1), shadow := Color.TRANSPARENT, shadow_size := 0, shadow_offset := Vector2.ZERO) -> StyleBoxFlat:
	# pad = (left, top, right, bottom); -1 keeps Godot's default for that side.
	var box := StyleBoxFlat.new()
	box.bg_color = bg
	box.border_color = border
	box.set_border_width_all(border_w)
	box.set_corner_radius_all(radius)
	box.corner_detail = 6
	box.content_margin_left = pad.x
	box.content_margin_top = pad.y
	box.content_margin_right = pad.z
	box.content_margin_bottom = pad.w
	box.shadow_color = shadow
	box.shadow_size = shadow_size
	box.shadow_offset = shadow_offset
	box.anti_aliasing = true
	return box

static func _neon_box(body: String, width: int, height: int, margin: float) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = svg_texture(body, width, height, 2.0)
	box.set_texture_margin_all(margin)
	return box

static func neon_ring(radius := 8.0, width := 1.5, inner := TOOL_INNER, wide := true) -> StyleBoxTexture:
	# CSS "padding-box fill + border-box neon": a 1.5 px gradient border around a dark fill.
	# A wide texture keeps the whole ramp in the stretched middle, so wide buttons still read
	# blue → violet → pink; wide=false gives a square texture for round/small controls.
	var h := int(ceil(radius * 2 + 8))
	var w := maxi(128, h) if wide else h
	var half := width / 2.0
	var body := '<defs>%s</defs><rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" fill-opacity="%s" stroke="url(#neon)" stroke-width="%s"/>' % [neon_defs(), half, half, w - width, h - width, maxf(radius - half, 0.0), hex(inner), inner.a, width]
	return _neon_box(body, w, h, radius + 2)

static func neon_fill(radius := 8.0, wide := true) -> StyleBoxTexture:
	var h := int(ceil(radius * 2 + 8))
	var w := maxi(128, h) if wide else h
	return _neon_box('<defs>%s</defs><rect width="%d" height="%d" rx="%s" fill="url(#neon)"/>' % [neon_defs(), w, h, radius], w, h, radius + 2)

static func brand_mark() -> Texture2D:
	# Header brand mark, 28 px: 1.5 px neon ring (radius 9) on the bar colour around a 14 px white
	# glyph at (5.5, 5.5) with its bottom-right corner cut (the mock's clip-path polygon).
	# Classic styles keep the glossy scene icon.
	if style != "neon": return classic_icon("scene")
	var body := '<defs>%s</defs><rect x="0.75" y="0.75" width="26.5" height="26.5" rx="8.25" fill="%s" stroke="url(#neon)" stroke-width="1.5"/><path d="M8.5 5.5H16.5A3 3 0 0 1 19.5 8.5V13.2L13.2 19.5H8.5A3 3 0 0 1 5.5 16.5V8.5A3 3 0 0 1 8.5 5.5Z" fill="%s"/>' % [neon_defs(), hex(BAR), hex(TEXT)]
	return svg_texture(body, 28, 28, 2.0)

static func neon_line(width := 44) -> Texture2D:
	# 2 px horizontal neon bar (active tab underline); stretch it to any width.
	return svg_texture('<defs>%s</defs><rect width="%d" height="2" rx="1" fill="url(#neon)"/>' % [neon_defs(), width], width, 2, 2.0)

static func neon_bar(height := 36) -> Texture2D:
	# 2 px vertical neon bar, blue at the top to pink at the bottom (selected World rail tile).
	return svg_texture('<defs>%s</defs><rect width="2" height="%d" rx="1" fill="url(#neonv)"/>' % [neon_defs("neonv", true), height], 2, height, 2.0)

static func kbd_box() -> StyleBoxFlat:
	# 18 px keycap chip (with the 11 px mono font): #13151B, 1 px #2C303B, radius 5.
	return flat(KBD, LINE2, 5, 1, Vector4(5, 1, 5, 1))

static func focus_box(radius := 10) -> StyleBoxFlat:
	# Keyboard focus: no fill, 2 px violet ring just outside the control plus a soft pink glow
	# (StyleBoxFlat skips the shadow's centre when draw_center is off, so the control stays clear).
	var box := flat(Color.TRANSPARENT, FOCUS, radius, 2, Vector4(-1, -1, -1, -1), Color(1, 0.239, 0.604, 0.45), 8)
	box.draw_center = false
	box.set_expand_margin_all(2)
	return box

static func switch_icon(on: bool, disabled := false) -> ImageTexture:
	# 34x20 switch. ON: 1.5 px neon ring, inner #0E1016, white 14 px knob with a pink glow.
	# OFF: #262A34 track with a 1 px #2C303B edge and a #8C93A3 knob on the left.
	var body: String
	if on:
		body = '<defs>%s<radialGradient id="glow"><stop offset="0.55" stop-color="#ff3d9a" stop-opacity="0.7"/><stop offset="1" stop-color="#ff3d9a" stop-opacity="0"/></radialGradient></defs><rect x="0.75" y="0.75" width="32.5" height="18.5" rx="9.25" fill="#0e1016" stroke="url(#neon)" stroke-width="1.5"/><circle cx="22.5" cy="10" r="10" fill="url(#glow)"/><circle cx="22.5" cy="10" r="7" fill="#ffffff"/>' % neon_defs()
	else:
		body = '<rect x="0.5" y="0.5" width="33" height="19" rx="9.5" fill="#262a34" stroke="#2c303b"/><circle cx="9" cy="10" r="7" fill="#8c93a3"/>'
	if disabled: body = '<g opacity="0.45">%s</g>' % body
	return svg_texture(body, 34, 20, 2.0)

static func check_icon(on: bool, radio := false, disabled := false) -> ImageTexture:
	# 16 px CheckBox: neon fill + white check when on, #101218 with a #363B48 edge when off.
	var rx := 8 if radio else 4
	var body: String
	if on:
		body = '<defs>%s</defs><rect width="16" height="16" rx="%d" fill="url(#neon)"/>' % [neon_defs(), rx]
		body += '<circle cx="8" cy="8" r="3" fill="#ffffff"/>' if radio else '<path d="m4.2 8.3 2.5 2.5 5.1-5.6" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
	else:
		body = '<rect x="0.5" y="0.5" width="15" height="15" rx="%s" fill="#101218" stroke="#363b48"/>' % (rx - 0.5)
	if disabled: body = '<g opacity="0.45">%s</g>' % body
	return svg_texture(body, 16, 16, 2.0)

static func slider_styles() -> Dictionary:
	# 4 px #272B35 track, neon fill up to the grabber, white 18 px grabber with a violet halo.
	var track := flat(TRACK, Color.TRANSPARENT, 2, 0, Vector4(0, 2, 0, 2))
	var fill := neon_fill(2.0)
	fill.set_texture_margin_all(2)
	fill.content_margin_top = 2
	fill.content_margin_bottom = 2
	var grabber := svg_texture('<circle cx="12" cy="12" r="10.5" fill="none" stroke="#7b5cff" stroke-opacity="0.25" stroke-width="3"/><circle cx="12" cy="12" r="9" fill="#ffffff"/>', 24, 24, 2.0)
	var grabber_hover := svg_texture('<circle cx="12" cy="12" r="10.5" fill="none" stroke="#7b5cff" stroke-opacity="0.45" stroke-width="3"/><circle cx="12" cy="12" r="9" fill="#ffffff"/>', 24, 24, 2.0)
	var grabber_off := svg_texture('<circle cx="12" cy="12" r="9" fill="#8c93a3"/>', 24, 24, 2.0)
	return {"track": track, "fill": fill, "grabber": grabber, "grabber_highlight": grabber_hover, "grabber_disabled": grabber_off}

static func font(weight := 400) -> Font:
	# The mock uses Geist, which is not bundled (no downloaded fonts): the closest installed
	# system face is used instead (Inter on the Linux test box, Segoe UI on Windows).
	var key := "ui%d" % weight
	if not fonts.has(key):
		var system := SystemFont.new()
		system.font_names = PackedStringArray(UI_FONTS)
		system.font_weight = weight
		system.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		system.hinting = TextServer.HINTING_LIGHT
		fonts[key] = system
	return fonts[key]

static func mono(weight := 400) -> Font:
	var key := "mono%d" % weight
	if not fonts.has(key):
		var system := SystemFont.new()
		system.font_names = PackedStringArray(MONO_FONTS)
		system.font_weight = weight
		system.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		system.hinting = TextServer.HINTING_LIGHT
		fonts[key] = system
	return fonts[key]

static func label_variation() -> FontVariation:
	# Rail label (e.g. "WORLD"): 11 px / 600, letter-spacing .14em (~1.5 px), written in capitals.
	if not fonts.has("rail"):
		var variation := FontVariation.new()
		variation.base_font = font(600)
		variation.set_spacing(TextServer.SPACING_GLYPH, 2)
		fonts["rail"] = variation
	return fonts["rail"]

static func _set_button_family(result: Theme, type: String, normal: StyleBox, hover: StyleBox, pressed: StyleBox, disabled: StyleBox, focus: StyleBox, text: Color, text_hover: Color, text_pressed: Color, text_disabled := TEXT3) -> void:
	result.set_stylebox("normal", type, normal)
	result.set_stylebox("normal_mirrored", type, normal)
	result.set_stylebox("hover", type, hover)
	result.set_stylebox("hover_mirrored", type, hover)
	result.set_stylebox("pressed", type, pressed)
	result.set_stylebox("pressed_mirrored", type, pressed)
	result.set_stylebox("hover_pressed", type, pressed)
	result.set_stylebox("hover_pressed_mirrored", type, pressed)
	result.set_stylebox("disabled", type, disabled)
	result.set_stylebox("disabled_mirrored", type, disabled)
	result.set_stylebox("focus", type, focus)
	result.set_color("font_color", type, text)
	result.set_color("font_focus_color", type, text)
	result.set_color("font_hover_color", type, text_hover)
	result.set_color("font_pressed_color", type, text_pressed)
	result.set_color("font_hover_pressed_color", type, text_pressed)
	result.set_color("font_disabled_color", type, text_disabled)
	result.set_color("font_outline_color", type, Color.TRANSPARENT)
	result.set_constant("outline_size", type, 0)

static func make_neon_theme() -> Theme:
	var result := Theme.new()
	result.default_font = font(400)
	result.default_font_size = 13
	var focus := focus_box()
	var pad := Vector4(12, 7, 12, 7)
	# Buttons: outline by default; GhostButton, PrimaryButton, NeonButton, TabButton, RailTile and
	# ToolButton are type variations for the header, tabs, rail and tool pill.
	var outline := flat(FIELD, LINE2, 8, 1, pad)
	var outline_hover := flat(Color("21252f"), LINE3, 8, 1, pad)
	var outline_pressed := flat(RAISE, LINE2, 8, 1, pad)
	var outline_disabled := flat(Color("0f1116"), LINE, 8, 1, pad)
	for type in ["Button", "OptionButton", "MenuButton", "ColorPickerButton"]:
		_set_button_family(result, type, outline, outline_hover, outline_pressed, outline_disabled, focus, TEXT, TEXT, Color.WHITE)
		result.set_font("font", type, font(500))
		result.set_constant("h_separation", type, 8)
		for state in ["icon_normal_color", "icon_hover_color", "icon_pressed_color", "icon_hover_pressed_color", "icon_focus_color"]:
			result.set_color(state, type, Color.WHITE)
		result.set_color("icon_disabled_color", type, Color(1, 1, 1, 0.45))
	result.set_icon("arrow", "OptionButton", icon("chevron", TEXT3, 14))
	var clear := flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, pad)
	var ghost_hover := flat(HOVER, Color.TRANSPARENT, 8, 0, pad)
	result.set_type_variation("GhostButton", "Button")
	_set_button_family(result, "GhostButton", clear, ghost_hover, flat(RAISE, Color.TRANSPARENT, 8, 0, pad), clear, focus, TEXT2, TEXT, Color.WHITE)
	result.set_type_variation("PrimaryButton", "Button")
	_set_button_family(result, "PrimaryButton", flat(Color("1a1d25"), LINE3, 8, 1, pad), flat(Color("21252f"), LINE3, 8, 1, pad), flat(RAISE, LINE3, 8, 1, pad), outline_disabled, focus, Color.WHITE, Color.WHITE, Color.WHITE)
	result.set_font("font", "PrimaryButton", font(600))
	result.set_font_size("font_size", "PrimaryButton", 14)
	result.set_type_variation("NeonButton", "Button")
	var neon := neon_fill(8.0)
	neon.content_margin_left = 14; neon.content_margin_right = 10; neon.content_margin_top = 7; neon.content_margin_bottom = 7
	var neon_hover: StyleBoxTexture = neon.duplicate()
	neon_hover.modulate_color = Color(1.08, 1.08, 1.08)
	_set_button_family(result, "NeonButton", neon, neon_hover, neon, neon, focus, ON_NEON, ON_NEON, ON_NEON, Color(0.03, 0.03, 0.04, 0.6))
	result.set_font("font", "NeonButton", font(600))
	result.set_font_size("font_size", "NeonButton", 14)
	var tab_pad := Vector4(14, 7, 14, 7)
	result.set_type_variation("TabButton", "Button")
	_set_button_family(result, "TabButton", flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, tab_pad), flat(HOVER, Color.TRANSPARENT, 7, 0, tab_pad), flat(RAISE, LINE2, 7, 1, tab_pad), flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, tab_pad), focus, TEXT3, TEXT, Color.WHITE)
	var tile_pad := Vector4(2, 6, 2, 5)
	result.set_type_variation("RailTile", "Button")
	_set_button_family(result, "RailTile", flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, tile_pad), flat(HOVER, Color.TRANSPARENT, 8, 0, tile_pad), flat(RAISE, LINE2, 8, 1, tile_pad), flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, tile_pad), focus, TEXT2, TEXT, Color.WHITE)
	result.set_font_size("font_size", "RailTile", 11)
	var tool_pad := Vector4(10, 7, 8, 7)
	var tool_on := neon_ring(8.0, 1.5, TOOL_INNER)
	tool_on.content_margin_left = tool_pad.x; tool_on.content_margin_top = tool_pad.y; tool_on.content_margin_right = tool_pad.z; tool_on.content_margin_bottom = tool_pad.w
	result.set_type_variation("ToolButton", "Button")
	_set_button_family(result, "ToolButton", flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, tool_pad), flat(HOVER, Color.TRANSPARENT, 8, 0, tool_pad), tool_on, flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, tool_pad), focus, TEXT2, TEXT, Color.WHITE)
	# Toggles: plain rows (no box) so a switch reads like the mock's Show / Onion rows.
	var row := flat(Color.TRANSPARENT, Color.TRANSPARENT, 8, 0, Vector4(10, 7, 10, 7))
	var row_hover := flat(HOVER, Color.TRANSPARENT, 8, 0, Vector4(10, 7, 10, 7))
	for type in ["CheckButton", "CheckBox"]:
		_set_button_family(result, type, row, row_hover, row, row, focus, TEXT, TEXT, TEXT)
		result.set_constant("h_separation", type, 10)
	for suffix in ["", "_mirrored"]:
		result.set_icon("checked" + suffix, "CheckButton", switch_icon(true))
		result.set_icon("unchecked" + suffix, "CheckButton", switch_icon(false))
		result.set_icon("checked_disabled" + suffix, "CheckButton", switch_icon(true, true))
		result.set_icon("unchecked_disabled" + suffix, "CheckButton", switch_icon(false, true))
	result.set_icon("checked", "CheckBox", check_icon(true))
	result.set_icon("unchecked", "CheckBox", check_icon(false))
	result.set_icon("checked_disabled", "CheckBox", check_icon(true, false, true))
	result.set_icon("unchecked_disabled", "CheckBox", check_icon(false, false, true))
	result.set_icon("radio_checked", "CheckBox", check_icon(true, true))
	result.set_icon("radio_unchecked", "CheckBox", check_icon(false, true))
	result.set_icon("radio_checked_disabled", "CheckBox", check_icon(true, true, true))
	result.set_icon("radio_unchecked_disabled", "CheckBox", check_icon(false, true, true))
	# Text fields. Selected text keeps Codex's dark #163854 (tests/workspace_controls_smoke checks
	# it), so the selection is a pale neon blue instead of the mock's translucent blue.
	var field := flat(FIELD, LINE2, 8, 1, Vector4(9, 6, 9, 6))
	var field_read := flat(Color("0f1116"), LINE, 8, 1, Vector4(9, 6, 9, 6))
	for type in ["LineEdit", "TextEdit", "CodeEdit"]:
		result.set_stylebox("normal", type, field)
		result.set_stylebox("focus", type, focus)
		result.set_stylebox("read_only", type, field_read)
		result.set_color("font_color", type, TEXT)
		result.set_color("font_readonly_color", type, TEXT2)
		result.set_color("font_uneditable_color", type, TEXT2)
		result.set_color("font_placeholder_color", type, TEXT3)
		result.set_color("caret_color", type, TEXT)
		result.set_color("selection_color", type, Color("b9d7ff"))
		result.set_color("font_selected_color", type, Color("163854"))
		result.set_color("clear_button_color", type, TEXT3)
		result.set_color("clear_button_color_pressed", type, TEXT)
	for type in ["Label", "RichTextLabel"]:
		result.set_color("font_color" if type == "Label" else "default_color", type, TEXT)
	result.set_color("font_selected_color", "RichTextLabel", Color("163854"))
	result.set_color("selection_color", "RichTextLabel", Color("b9d7ff"))
	result.set_color("font_color", "LinkButton", Color("7fb6ff"))
	result.set_color("font_hover_color", "LinkButton", Color("b9d7ff"))
	result.set_color("font_pressed_color", "LinkButton", Color("b9d7ff"))
	result.set_type_variation("RailLabel", "Label")
	result.set_font("font", "RailLabel", label_variation())
	result.set_font_size("font_size", "RailLabel", 11)
	result.set_color("font_color", "RailLabel", TEXT3)
	result.set_type_variation("CaptionLabel", "Label")
	result.set_font_size("font_size", "CaptionLabel", 12)
	result.set_color("font_color", "CaptionLabel", TEXT2)
	result.set_type_variation("MonoLabel", "Label")
	result.set_font("font", "MonoLabel", mono(500))
	result.set_font_size("font_size", "MonoLabel", 12)
	result.set_color("font_color", "MonoLabel", TEXT)
	result.set_type_variation("KbdLabel", "Label")
	result.set_font("font", "KbdLabel", mono(500))
	result.set_font_size("font_size", "KbdLabel", 11)
	result.set_color("font_color", "KbdLabel", TEXT2)
	result.set_stylebox("normal", "KbdLabel", kbd_box())
	# Surfaces. Same content margins as the classic skin so docks keep their size.
	result.set_stylebox("panel", "PanelContainer", flat(BAR, Color.TRANSPARENT, 0, 0, Vector4(13, 10, 13, 10)))
	result.set_stylebox("panel", "Panel", flat(BAR, Color.TRANSPARENT, 0, 0))
	var popup := flat(POPUP, LINE2, 10, 1, Vector4(6, 6, 6, 6), Color(0, 0, 0, 0.8), 12, Vector2(0, 8))
	result.set_stylebox("panel", "PopupMenu", popup)
	result.set_stylebox("panel", "PopupPanel", popup)
	result.set_stylebox("panel", "PopupDialog", popup)
	result.set_stylebox("hover", "PopupMenu", flat(HOVER, Color.TRANSPARENT, 6, 0, Vector4(8, 4, 8, 4)))
	result.set_stylebox("separator", "PopupMenu", line_box(false))
	result.set_stylebox("labeled_separator_left", "PopupMenu", line_box(false))
	result.set_stylebox("labeled_separator_right", "PopupMenu", line_box(false))
	result.set_color("font_color", "PopupMenu", TEXT2)
	result.set_color("font_hover_color", "PopupMenu", TEXT)
	result.set_color("font_disabled_color", "PopupMenu", TEXT3)
	result.set_color("font_separator_color", "PopupMenu", TEXT3)
	result.set_color("font_accelerator_color", "PopupMenu", TEXT3)
	result.set_constant("v_separation", "PopupMenu", 8)
	result.set_stylebox("panel", "TooltipPanel", flat(POPUP, LINE2, 10, 1, Vector4(10, 7, 10, 7), Color(0, 0, 0, 0.8), 12, Vector2(0, 8)))
	result.set_color("font_color", "TooltipLabel", TEXT)
	result.set_font_size("font_size", "TooltipLabel", 12)
	result.set_stylebox("panel", "AcceptDialog", flat(BAR, Color.TRANSPARENT, 0, 0, Vector4(12, 10, 12, 10)))
	for state in ["embedded_border", "embedded_unfocused_border"]:
		var border := flat(BAR, LINE2 if state == "embedded_border" else LINE, 10, 1, Vector4(-1, -1, -1, -1), Color(0, 0, 0, 0.6), 12, Vector2(0, 8))
		border.expand_margin_left = 8; border.expand_margin_top = 32; border.expand_margin_right = 8; border.expand_margin_bottom = 6
		result.set_stylebox(state, "Window", border)
	result.set_color("title_color", "Window", TEXT)
	result.set_font("title_font", "Window", font(600))
	# Lists and trees: chrome background, selected row raised with a hairline.
	var list := flat(BAR, LINE, 8, 1, Vector4(4, 4, 4, 4))
	var selected := flat(RAISE, LINE2, 6, 1)
	var hovered := flat(HOVER, Color.TRANSPARENT, 6, 0)
	var list_focus := flat(Color.TRANSPARENT, LINE3, 8, 1)
	list_focus.draw_center = false
	for type in ["Tree", "ItemList"]:
		result.set_stylebox("panel", type, list)
		result.set_stylebox("focus", type, list_focus)
		result.set_stylebox("selected", type, selected)
		result.set_stylebox("selected_focus", type, selected)
		result.set_stylebox("hovered", type, hovered)
		result.set_stylebox("hovered_selected", type, selected)
		result.set_stylebox("hovered_selected_focus", type, selected)
		result.set_stylebox("cursor", type, list_focus)
		result.set_stylebox("cursor_unfocused", type, StyleBoxEmpty.new())
		result.set_color("font_color", type, TEXT)
		result.set_color("font_selected_color", type, Color.WHITE)
		result.set_color("font_hovered_color", type, TEXT)
		result.set_color("font_hovered_selected_color", type, Color.WHITE)
		result.set_color("guide_color", type, LINE)
	result.set_color("relationship_line_color", "Tree", LINE2)
	result.set_color("parent_hl_line_color", "Tree", LINE3)
	result.set_color("children_hl_line_color", "Tree", LINE2)
	result.set_color("drop_position_color", "Tree", BLUE)
	result.set_color("title_button_color", "Tree", TEXT2)
	result.set_stylebox("title_button_normal", "Tree", flat(PANEL, LINE, 0, 1))
	result.set_stylebox("title_button_hover", "Tree", flat(HOVER, LINE, 0, 1))
	result.set_stylebox("title_button_pressed", "Tree", flat(RAISE, LINE2, 0, 1))
	result.set_stylebox("button_pressed", "Tree", flat(RAISE, LINE2, 4, 1))
	result.set_stylebox("custom_button", "Tree", flat(FIELD, LINE2, 6, 1))
	result.set_stylebox("custom_button_hover", "Tree", flat(Color("21252f"), LINE3, 6, 1))
	result.set_stylebox("custom_button_pressed", "Tree", flat(RAISE, LINE2, 6, 1))
	result.set_color("custom_button_font_highlight", "Tree", Color.WHITE)
	# Sliders: neon fill and white grabber.
	var slider := slider_styles()
	var vtrack := flat(TRACK, Color.TRANSPARENT, 2, 0, Vector4(2, 0, 2, 0))
	for type in ["HSlider", "VSlider"]:
		result.set_stylebox("slider", type, slider.track if type == "HSlider" else vtrack)
		for state in ["grabber_area", "grabber_area_highlight"]:
			result.set_stylebox(state, type, slider.fill)
		for state in ["grabber", "grabber_highlight", "grabber_disabled"]:
			result.set_icon(state, type, slider[state])
	# Progress bars.
	result.set_stylebox("background", "ProgressBar", flat(FIELD, LINE2, 4, 1, Vector4(0, 2, 0, 2)))
	var progress_fill := neon_fill(3.0)
	progress_fill.set_texture_margin_all(3)
	result.set_stylebox("fill", "ProgressBar", progress_fill)
	result.set_color("font_color", "ProgressBar", TEXT)
	result.set_color("font_outline_color", "ProgressBar", BAR)
	# Hairline separators and thin scrollbars.
	result.set_stylebox("separator", "HSeparator", line_box(false))
	result.set_stylebox("separator", "VSeparator", line_box(true))
	for type in ["HScrollBar", "VScrollBar"]:
		var v: bool = type == "VScrollBar"
		var track_pad := Vector4(3, 0, 3, 0) if v else Vector4(0, 3, 0, 3)
		result.set_stylebox("scroll", type, flat(Color.TRANSPARENT, Color.TRANSPARENT, 3, 0, track_pad))
		result.set_stylebox("scroll_focus", type, flat(Color.TRANSPARENT, Color.TRANSPARENT, 3, 0, track_pad))
		result.set_stylebox("grabber", type, flat(LINE2, Color.TRANSPARENT, 3, 0, track_pad))
		result.set_stylebox("grabber_highlight", type, flat(LINE3, Color.TRANSPARENT, 3, 0, track_pad))
		result.set_stylebox("grabber_pressed", type, flat(TEXT3, Color.TRANSPARENT, 3, 0, track_pad))
	# Tabs: selected tab raised with a neon underline; others text-only.
	var tab_selected := StyleBoxTexture.new()
	tab_selected.texture = svg_texture('<defs>%s</defs><rect width="128" height="32" rx="7" fill="#171a21"/><rect x="14" y="30" width="100" height="2" rx="1" fill="url(#neon)"/>' % neon_defs(), 128, 32, 2.0)
	tab_selected.texture_margin_left = 16; tab_selected.texture_margin_right = 16
	tab_selected.texture_margin_top = 8; tab_selected.texture_margin_bottom = 4
	tab_selected.content_margin_left = 12; tab_selected.content_margin_right = 12
	tab_selected.content_margin_top = 6; tab_selected.content_margin_bottom = 6
	var tab_off := flat(Color.TRANSPARENT, Color.TRANSPARENT, 7, 0, Vector4(12, 6, 12, 6))
	var tab_hover := flat(HOVER, Color.TRANSPARENT, 7, 0, Vector4(12, 6, 12, 6))
	for type in ["TabBar", "TabContainer"]:
		result.set_stylebox("tab_selected", type, tab_selected)
		result.set_stylebox("tab_unselected", type, tab_off)
		result.set_stylebox("tab_hovered", type, tab_hover)
		result.set_stylebox("tab_disabled", type, tab_off)
		result.set_stylebox("tab_focus", type, focus)
		result.set_color("font_selected_color", type, Color.WHITE)
		result.set_color("font_unselected_color", type, TEXT3)
		result.set_color("font_hovered_color", type, TEXT)
		result.set_color("font_disabled_color", type, Color(TEXT3, 0.6))
		result.set_color("drop_mark_color", type, BLUE)
	result.set_stylebox("panel", "TabContainer", flat(BAR, LINE, 0, 1))
	result.set_stylebox("tabbar_background", "TabContainer", flat(BAR, Color.TRANSPARENT, 0, 0))
	# Splitters keep their drag area (separation unchanged) but draw no grabber dots.
	var none := ImageTexture.create_from_image(Image.create_empty(2, 2, false, Image.FORMAT_RGBA8))
	for type in ["HSplitContainer", "VSplitContainer", "SplitContainer"]:
		for item in ["grabber", "h_grabber", "v_grabber"]:
			result.set_icon(item, type, none)
	result.set_constant("separation", "VBoxContainer", 7)
	result.set_constant("separation", "HBoxContainer", 7)
	return result

static func line_box(vertical: bool) -> StyleBoxLine:
	var line := StyleBoxLine.new()
	line.color = LINE2
	line.thickness = 1
	line.vertical = vertical
	return line

static func make_theme() -> Theme:
	if style == "neon": return make_neon_theme()
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

# Neon line icons: 24-unit viewBox, 1.7 stroke, round caps/joins, one colour. Paths follow the
# approved mock's inline SVGs; "currentColor" fills are replaced by the icon colour.
const LINE_ICONS := {
	"new": '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5M12 12v6M9 15h6"/>',
	"open": '<path d="M3 7a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v2"/><path d="M3 7v11a1 1 0 0 0 1 1h14l3-8H7l-3 8"/>',
	"folder": '<path d="M3 7a1 1 0 0 1 1-1h5l2 2h8a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z"/>',
	"save": '<path d="M5 4h11l3 3v12a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',
	"add": '<path d="M12 5v14M5 12h14"/>',
	"chevron": '<path d="m6 9 6 6 6-6"/>',
	"more": '<circle cx="5" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="19" cy="12" r="1.3" fill="currentColor"/>',
	"export": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9.5 4.5 2.5-4.5 2.5z" fill="currentColor"/>',
	"draw": '<path d="M4 20l4-1 11-11a2.1 2.1 0 0 0-3-3L5 16z"/><path d="M14 7l3 3"/>',
	"eraser": '<path d="M7 20h13M5.5 15.5l9-9a2 2 0 0 1 2.8 0l1.2 1.2a2 2 0 0 1 0 2.8L11 18H8z"/><path d="m9.5 11.5 4 4"/>',
	"fill": '<path d="m5 11 6-6 7 7-6 6a2 2 0 0 1-2.8 0L5 13.8a2 2 0 0 1 0-2.8z"/><path d="M5 12h13M20 15s1.5 2 1.5 3a1.5 1.5 0 0 1-3 0c0-1 1.5-3 1.5-3z"/>',
	"picker": '<path d="m14 6 4 4M4 20l2-.5L16.5 9 15 7.5 4.5 18z"/><path d="M15 5l1.5-1.5a2.1 2.1 0 0 1 3 3L18 8"/>',
	"select": '<rect x="4" y="4" width="16" height="16" rx="1.5" stroke-dasharray="3 3"/>',
	"camera": '<rect x="3" y="7" width="13" height="11" rx="2"/><path d="m16 11 5-3v9l-5-3"/>',
	"figure": '<circle cx="12" cy="4.5" r="2"/><path d="M12 7v7M7 10l5-1 5 1M9 21l3-7 3 7"/>',
	"building": '<path d="M3 20h18M5 20V10h5v10M10 20V6h6v14M16 20v-8h3v8"/>',
	"runner": '<circle cx="13" cy="4.5" r="2"/><path d="M12 7.5 10 14l4 3 1 4M10 14l-4 6M11 9l-4 1-1 3M12 9l3 3 4-1"/>',
	"sky": '<path d="M3 18h18M7 18a5 5 0 0 1 10 0M12 8V6M5.6 11.6 4.2 10.2M18.4 11.6l1.4-1.4M6 21h12"/>',
	"bird": '<path d="M4 14c3 0 4-5 8-5 3 0 4 2 4 4 0 3-3 5-7 5H6"/><path d="M16 11l4-1-3 3M10 18l-1 3M13 18l1 3"/>',
	"box": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
	"scene": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/>',
	"frame-target": '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="3"/>',
	"panel-unfold": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M13 10l2 2-2 2"/>',
	"panel-fold": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 10l-2 2 2 2"/>',
	"sparkle": '<path d="M12 3.5 13.9 9.1 19.5 11 13.9 12.9 12 18.5 10.1 12.9 4.5 11 10.1 9.1z"/><path d="M18.5 16.5v4M16.5 18.5h4"/>',
	"ruler": '<path d="M3.5 16.5 16.5 3.5l4 4-13 13z"/><path d="m7.5 12.5 2 2M10.5 9.5l1.5 1.5M13.5 6.5l2 2"/>',
	"eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
	"onion": '<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6" stroke-dasharray="2.5 2.5"/>',
	"layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
	"play": '<path d="M7 4.5v15a1 1 0 0 0 1.5.86l12-7.5a1 1 0 0 0 0-1.72l-12-7.5A1 1 0 0 0 7 4.5z" fill="currentColor" stroke="none"/>',
	"pause": '<rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/>',
	"skip-back": '<path d="M6 5v14M18 6l-8 6 8 6z"/>',
	"skip-forward": '<path d="M18 5v14M6 6l8 6-8 6z"/>',
	"diamond": '<path d="M12 3.5 20.5 12 12 20.5 3.5 12z"/>',
	"key": '<path d="M12 3.5 20.5 12 12 20.5 3.5 12z"/><path d="M12 9v6M9 12h6"/>',
	"mouse": '<rect x="6.5" y="3" width="11" height="18" rx="5.5"/><path d="M12 7v3"/>',
	"help": '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.6"/><circle cx="12" cy="17.2" r="0.6" fill="currentColor"/>',
	"check": '<path d="m5 12 5 5 9-10"/>',
	"arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
	"grid": '<rect x="3.5" y="5" width="17" height="14" rx="1.5"/><path d="M9.2 5v14M14.8 5v14M3.5 9.7h17M3.5 14.3h17"/>',
	"path": '<path d="M6 16C10 16 12 8 18 8"/><path d="M6 13 9 16 6 19 3 16z M18 5 21 8 18 11 15 8z" fill="currentColor" stroke="none"/>',
	"reset": '<path d="M4 12a8 8 0 1 0 2.3-5.6"/><path d="M4 4v4.5h4.5"/>',
	"settings": '<path d="M18.1 10.8 20.5 11.1 20.5 12.9 18.1 13.2 17.1 15.5 18.7 17.4 17.4 18.7 15.5 17.1 13.2 18.1 12.9 20.5 11.1 20.5 10.8 18.1 8.5 17.1 6.6 18.7 5.3 17.4 6.9 15.5 5.9 13.2 3.5 12.9 3.5 11.1 5.9 10.8 6.9 8.5 5.3 6.6 6.6 5.3 8.5 6.9 10.8 5.9 11.1 3.5 12.9 3.5 13.2 5.9 15.5 6.9 17.4 5.3 18.7 6.6 17.1 8.5z"/><circle cx="12" cy="12" r="2.6"/>',
	"undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
	"redo": '<path d="m15 14 5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
	"audio": '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
	"fan": '<circle cx="12" cy="11" r="1.6"/><path d="M12 9.4C11 6 11.6 3.5 13.6 3.5c2.3 0 2 3.6-1.6 5.9zM13.4 11.8c3.4.9 5.3 2.7 4.3 4.4-1.1 2-4.1 0-4.3-4.4zM10.6 11.8c-2.5 2.5-5 3.2-6 1.5-1.1-2 2.2-3.5 6-1.5z"/><path d="M12 12.6V21M8.5 21h7"/>',
	"cel": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M12 8v8M8 12h8"/>',
	"joint": '<circle cx="12" cy="12" r="3.4"/><path d="M10 9.2 5.5 3M14 14.8 18.5 21"/><path d="M19 9.5a7.5 7.5 0 0 1-3 9M5 14.5a7.5 7.5 0 0 1 3-9" stroke-opacity="0.6"/>',
	"move": '<path d="M12 3v18M3 12h18M12 3 9.5 5.5M12 3l2.5 2.5M12 21l-2.5-2.5M12 21l2.5-2.5M3 12l2.5-2.5M3 12l2.5 2.5M21 12l-2.5-2.5M21 12l-2.5 2.5"/>',
	"turn": '<path d="M20 12a8 8 0 0 1-14.6 4.5"/><path d="M4 12a8 8 0 0 1 14.6-4.5"/><path d="M19 3.5V8h-4.5M5 20.5V16h4.5"/>',
	"hand": '<path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V10m0-1.5a1.5 1.5 0 0 1 3 0V11m0-1a1.5 1.5 0 0 1 3 0v4.5a6 6 0 0 1-6 6h-1a6 6 0 0 1-4.8-2.4L3.6 14a1.5 1.5 0 0 1 2.3-1.9L9 15"/>',
	"wave": '<path d="M3 8c3 0 3-3 6-3s3 3 6 3 3-3 6-3M3 14c3 0 3-3 6-3s3 3 6 3 3-3 6-3M3 20c3 0 3-3 6-3s3 3 6 3 3-3 6-3"/>',
}
# Aliases so callers can use the names the plan and mock use.
const ICON_ALIASES := {"pen": "draw", "pose": "figure", "key-diamond": "diamond"}

static func line_icon(kind: String, color := TEXT2, size := 16) -> Texture2D:
	var key := "neon|%s|%s|%d" % [kind, color.to_html(), size]
	if icons.has(key): return icons[key]
	var name: String = ICON_ALIASES.get(kind, kind)
	var colour := hex(color)
	var body: String = String(LINE_ICONS.get(name, LINE_ICONS.help)).replace("currentColor", colour)
	var svg := '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 24 24"><g fill="none" stroke="%s" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" opacity="%s">%s</g></svg>' % [size, size, colour, color.a, body]
	icons[key] = svg_image(svg, size, size, 2.0)
	return icons[key]

static func icon(kind: String, color := TEXT2, size := 16) -> Texture2D:
	# Neon: 16 px line icon in `color`. Classic styles: the original glossy 32 px icon (colour and
	# size are ignored there, exactly as before).
	if style == "neon": return line_icon(kind, color, size)
	return classic_icon(kind)

static func app_icon() -> Image:
	# The window/taskbar icon keeps the colourful glossy artwork in every style.
	return classic_icon("scene").get_image()

static func classic_icon(kind: String) -> Texture2D:
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
