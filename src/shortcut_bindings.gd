extends RefCounted
# Personal logical-key shortcuts, independent of project/model data.
const DEFAULTS={"play":KEY_SPACE,"previous":KEY_LEFT,"next":KEY_RIGHT,"first":KEY_HOME,"last":KEY_END,"undo":KEY_MASK_CTRL|KEY_Z,"redo":KEY_MASK_CTRL|KEY_Y,"redo_alternate":KEY_MASK_CTRL|KEY_MASK_SHIFT|KEY_Z,"save":KEY_MASK_CTRL|KEY_S,"pen":KEY_B,"eraser":KEY_E,"fill":KEY_F,"sample":KEY_I,"select":KEY_M,"camera":KEY_K}
const TITLES={"play":"Play / pause","previous":"Previous frame","next":"Next frame","first":"First frame","last":"Last frame","undo":"Undo","redo":"Redo","redo_alternate":"Redo (alternate)","save":"Save project","pen":"Pen","eraser":"Eraser","fill":"Fill","sample":"Pick color","select":"Select drawing area","camera":"Save camera key"}
const MODIFIERS=KEY_MASK_CTRL|KEY_MASK_SHIFT

static func key_error(value) -> String:
	if not value is int:return "Shortcut must be a keyboard key."
	if value==0:return ""
	if value<0 or value & ~(KEY_CODE_MASK|MODIFIERS):return "Use a key with optional Ctrl / Shift. Alt and Windows keys stay reserved."
	var code: int=value & KEY_CODE_MASK
	if code>=KEY_A and code<=KEY_Z or code>=KEY_0 and code<=KEY_9 or code>=KEY_F1 and code<=KEY_F12:return ""
	if code in [KEY_SPACE,KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_HOME,KEY_END,KEY_PAGEUP,KEY_PAGEDOWN,KEY_INSERT,KEY_DELETE,KEY_COMMA,KEY_PERIOD,KEY_SLASH,KEY_BACKSLASH,KEY_BRACKETLEFT,KEY_BRACKETRIGHT,KEY_SEMICOLON,KEY_APOSTROPHE,KEY_MINUS,KEY_EQUAL,KEY_QUOTELEFT]:return ""
	return "Choose a letter, number, F1–F12, navigation key or punctuation. Escape, Tab, Enter and modifier keys stay reserved."

static func error(bindings) -> String:
	if not bindings is Dictionary or bindings.size()!=DEFAULTS.size():return "Invalid shortcut collection."
	var used:={}
	for id in DEFAULTS:
		if not bindings.has(id):return "Missing shortcut: "+TITLES[id]
		var problem:=key_error(bindings[id])
		if not problem.is_empty():return problem
		var value: int=bindings[id]
		if value==0:continue
		if used.has(value):return "%s already uses %s. Clear or change it first." % [TITLES[used[value]],OS.get_keycode_string(value)]
		used[value]=id
	return ""

static func action(bindings: Dictionary,event: InputEventKey) -> String:
	if not event.pressed or event.echo or event.alt_pressed or event.meta_pressed:return ""
	var code: int=event.get_keycode_with_modifiers()
	if code==0:return ""
	for id in DEFAULTS:
		if bindings.get(id,0)==code:return id
	return ""

static func label_for(bindings: Dictionary,id: String) -> String:
	var code: int=bindings.get(id,0)
	return OS.get_keycode_string(code) if code else "Unassigned"
