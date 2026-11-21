extends SceneTree
const Bindings=preload("res://src/shortcut_bindings.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var defaults: Dictionary=Bindings.DEFAULTS.duplicate()
	check(Bindings.error(defaults).is_empty() and defaults.size()==15,"fifteen default actions are valid and unique")
	for id in defaults:
		var event:=InputEventKey.new();event.keycode=defaults[id]&KEY_CODE_MASK;event.ctrl_pressed=bool(defaults[id]&KEY_MASK_CTRL);event.shift_pressed=bool(defaults[id]&KEY_MASK_SHIFT);event.pressed=true
		check(Bindings.action(defaults,event)==id,"default routes "+id)
		event.echo=true;check(Bindings.action(defaults,event).is_empty(),"repeat ignored "+id)
	check(not Bindings.key_error(KEY_ESCAPE).is_empty() and not Bindings.key_error(KEY_ENTER).is_empty() and not Bindings.key_error(KEY_TAB).is_empty(),"escape and editing/focus keys stay reserved")
	check(not Bindings.key_error(KEY_MASK_ALT|KEY_A).is_empty() and not Bindings.key_error(KEY_MASK_META|KEY_A).is_empty() and not Bindings.key_error(KEY_MASK_CMD_OR_CTRL|KEY_A).is_empty(),"unsupported modifier masks refuse")
	check(not Bindings.key_error(65.0).is_empty() and not Bindings.key_error(true).is_empty() and not Bindings.key_error(-1).is_empty(),"noninteger and negative bindings refuse")
	check(Bindings.key_error(KEY_F12|KEY_MASK_CTRL|KEY_MASK_SHIFT).is_empty() and Bindings.key_error(0).is_empty(),"function keys and unassigned action are supported")
	var duplicate:=defaults.duplicate();duplicate.pen=KEY_E;check(not Bindings.error(duplicate).is_empty(),"conflicting shortcuts refuse")
	duplicate.pen=0;duplicate.eraser=0;check(Bindings.error(duplicate).is_empty(),"several unassigned actions do not conflict")
	duplicate=defaults.duplicate();duplicate.erase("next");check(not Bindings.error(duplicate).is_empty(),"incomplete preferences refuse")
	duplicate=defaults.duplicate();duplicate.unknown=KEY_F12;check(not Bindings.error(duplicate).is_empty(),"unknown preference actions refuse")
	var modified:=InputEventKey.new();modified.keycode=KEY_SPACE;modified.pressed=true;modified.shift_pressed=true;check(Bindings.action(defaults,modified).is_empty(),"modifier matching is exact")
	modified.shift_pressed=false;modified.alt_pressed=true;check(Bindings.action(defaults,modified).is_empty(),"Alt combinations cannot play")
	modified.alt_pressed=false;modified.pressed=false;check(Bindings.action(defaults,modified).is_empty(),"key release cannot dispatch")
	modified.pressed=true;modified.keycode=0;modified.physical_keycode=KEY_SPACE;check(Bindings.action(defaults,modified).is_empty(),"logical shortcuts never silently use physical position")
	print("SHORTCUT_BINDINGS_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
