extends RefCounted
# Personal logical-key shortcuts, independent of project/model data.
const DEFAULTS={"play":KEY_SPACE,"previous":KEY_LEFT,"next":KEY_RIGHT,"first":KEY_HOME,"last":KEY_END,"undo":KEY_MASK_CTRL|KEY_Z,"redo":KEY_MASK_CTRL|KEY_Y,"redo_alternate":KEY_MASK_CTRL|KEY_MASK_SHIFT|KEY_Z,"save":KEY_MASK_CTRL|KEY_S,"pen":KEY_B,"eraser":KEY_E,"fill":KEY_F,"sample":KEY_I,"select":KEY_M,"camera":KEY_K,"character_tools":KEY_C}
const TITLES={"play":"Play / pause","previous":"Previous frame","next":"Next frame","first":"First frame","last":"Last frame","undo":"Undo","redo":"Redo","redo_alternate":"Redo (alternate)","save":"Save project","pen":"Pen","eraser":"Eraser","fill":"Fill","sample":"Pick color","select":"Select drawing area","camera":"Save camera key","character_tools":"Character tools"}
const VERSION := 2
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


# Every inspected version1 review has the complete15-action collection.
# Unknown or incomplete layouts are refused; existing remaps are never guessed.
static func migrate(saved: Variant,version: Variant) -> Dictionary:
	if typeof(version) != TYPE_INT or version not in [1,VERSION]:
		return {"error":"Unknown keyboard preferences; using defaults."}
	if version == VERSION:
		var current_error: String = error(saved)
		return {"bindings":saved.duplicate(),"migrated":false,"note":""} if current_error.is_empty() else {"error":current_error}
	if not saved is Dictionary or saved.size() != 15: return {"error":"Invalid legacy shortcut collection."}
	var expected: Array = DEFAULTS.keys(); expected.erase("character_tools")
	if saved.size() != expected.size(): return {"error":"Invalid legacy shortcut collection."}
	var used := {}
	for id in expected:
		if not saved.has(id): return {"error":"Missing legacy shortcut: "+TITLES[id]}
		var key_problem: String = key_error(saved[id])
		if not key_problem.is_empty(): return {"error":key_problem}
		var value: int = saved[id]
		if value != 0:
			if used.has(value): return {"error":"Conflicting legacy shortcuts."}
			used[value] = id
	var candidate: Dictionary = saved.duplicate()
	var unassigned: Array[String] = []
	for id in ["character_tools"]:
		if candidate.has(id): continue
		var wanted: int = DEFAULTS[id]
		candidate[id] = 0 if used.has(wanted) else wanted
		if candidate[id] == 0: unassigned.append(TITLES[id])
		else: used[wanted] = id
	var complete_error: String = error(candidate)
	if not complete_error.is_empty(): return {"error":complete_error}
	var note: String = "New shortcuts added; existing personal bindings were preserved."
	if not unassigned.is_empty(): note += " "+", ".join(unassigned)+" is unassigned because its default key is already used."
	return {"bindings":candidate,"migrated":true,"note":note}
