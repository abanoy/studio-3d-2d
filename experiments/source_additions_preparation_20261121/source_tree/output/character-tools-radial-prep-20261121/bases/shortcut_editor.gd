extends Node
const Bindings=preload("res://src/shortcut_bindings.gd")
var app
var bindings: Dictionary=Bindings.DEFAULTS.duplicate()
var load_error:=""
var dialog: AcceptDialog
var info: Label
var rows:={}
var pending:=""
var decorated: Array=[]

func setup(owner_app: Control) -> void:
	app=owner_app
	var prefs:=ConfigFile.new();var code:=prefs.load(app.display_prefs_path)
	if code==OK and prefs.has_section("shortcuts"):
		var saved=prefs.get_value("shortcuts","keys",{})
		if prefs.get_value("shortcuts","version",0)!=1:load_error="Unknown keyboard preferences; using defaults."
		else:
			load_error=Bindings.error(saved)
			if load_error.is_empty():bindings=saved.duplicate()
			else:load_error="Invalid keyboard preferences; using defaults. "+load_error
	elif code!=OK and code!=ERR_FILE_NOT_FOUND:load_error="Could not read interface preferences; using default shortcuts."

func label_for(id: String) -> String:return Bindings.label_for(bindings,id)

func decorate(control: Control,id: String,description: String,caption:="") -> Control:
	decorated.append({"control":control,"id":id,"description":description,"caption":caption});refresh_labels();return control

func refresh_labels() -> void:
	for item in decorated:
		if not is_instance_valid(item.control):continue
		item.control.tooltip_text=item.description+" • "+label_for(item.id)
		if not item.caption.is_empty():item.control.text=item.caption+" ["+label_for(item.id)+"]"
	if not app or not app.tool:return
	var ids:=["pen","eraser","fill","sample","select"];var titles:=["Pen","Eraser","Fill","Pick color","Select area"]
	for i in range(ids.size()):app.tool.set_item_text(i,titles[i]+" ["+label_for(ids[i])+"]")
	if app.play_button:app.play_button.tooltip_text="Play / pause • "+label_for("play")

func save(candidate: Dictionary) -> String:
	var problem:=Bindings.error(candidate)
	if not problem.is_empty():return problem
	var prefs:=ConfigFile.new();var code:=prefs.load(app.display_prefs_path)
	if code!=OK and code!=ERR_FILE_NOT_FOUND:return "Cannot read existing preferences; no shortcuts changed."
	prefs.set_value("shortcuts","version",1);prefs.set_value("shortcuts","keys",candidate)
	var path: String=ProjectSettings.globalize_path(app.display_prefs_path)
	var temporary:=path+".shortcuts-%d.tmp" % OS.get_process_id()
	if prefs.save(temporary)!=OK:return "Cannot save keyboard preferences; no shortcuts changed."
	if DirAccess.rename_absolute(temporary,path)!=OK:
		DirAccess.remove_absolute(temporary);return "Cannot commit keyboard preferences; no shortcuts changed."
	bindings=candidate.duplicate();refresh_labels()
	if app.canvas:app.refresh_workspace()
	return ""

func assign(id: String,value: int) -> String:
	if not Bindings.DEFAULTS.has(id):return "Unknown shortcut action."
	var candidate:=bindings.duplicate();candidate[id]=value
	return save(candidate)

func open() -> void:
	if app.exporting:return
	app.release_mouse()
	if not is_instance_valid(dialog):build()
	cancel_capture();info.text=load_error if not load_error.is_empty() else "Click a shortcut, then press a key. Changes save immediately."
	refresh_rows();dialog.popup_centered(Vector2i(560,520))

func build() -> void:
	dialog=AcceptDialog.new();dialog.title="Keyboard shortcuts";dialog.exclusive=false;dialog.dialog_close_on_escape=false;dialog.min_size=Vector2i(530,420);app.add_child(dialog)
	dialog.window_input.connect(func(event):
		if capture(event):dialog.set_input_as_handled()
		elif event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:dialog.hide();dialog.set_input_as_handled())
	dialog.visibility_changed.connect(func():
		if not dialog.visible:cancel_capture())
	dialog.focus_exited.connect(cancel_capture)
	var box:=VBoxContainer.new();dialog.add_child(box)
	var instructions: Label=app.label(box,"Personal keyboard preferences. Mouse, WASD, Alt bone reveal and Escape stay unchanged.")
	instructions.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var scroll:=ScrollContainer.new();scroll.custom_minimum_size=Vector2(510,300);scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;box.add_child(scroll)
	var list:=VBoxContainer.new();list.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(list)
	for id in Bindings.DEFAULTS:
		var row:=HBoxContainer.new();list.add_child(row)
		var title: Label=app.label(row,Bindings.TITLES[id]);title.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		var change: Button=app.button(row,"",begin_capture.bind(id));change.custom_minimum_size.x=145
		var clear: Button=app.button(row,"Clear",clear_binding.bind(id));clear.tooltip_text="Leave this action without a keyboard shortcut; its button still works."
		rows[id]=change
	info=app.label(box,"");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;info.custom_minimum_size=Vector2(500,64)
	app.button(box,"Restore default shortcuts",restore_defaults)

func refresh_rows() -> void:
	for id in rows:rows[id].text="Press a key…" if pending==id else label_for(id)

func begin_capture(id: String) -> void:
	pending=id;info.text="Press a key for %s. Optional Ctrl / Shift. Escape cancels." % Bindings.TITLES[id];refresh_rows()

func cancel_capture() -> void:
	if pending.is_empty():return
	pending="";refresh_rows()
	if info:info.text="Shortcut change cancelled."

func capture(event: InputEvent) -> bool:
	if pending.is_empty() or not is_instance_valid(dialog) or not dialog.visible or not event is InputEventKey:return false
	if not event.pressed or event.echo:return true
	if event.keycode==KEY_ESCAPE:cancel_capture();return true
	if event.keycode in [KEY_CTRL,KEY_SHIFT,KEY_ALT,KEY_META]:return true
	var problem:=Bindings.key_error(event.get_keycode_with_modifiers())
	if problem.is_empty():problem=assign(pending,event.get_keycode_with_modifiers())
	if problem.is_empty():pending="";load_error="";info.text="Shortcut saved."
	else:info.text=problem+" Try another key, or Escape to cancel."
	refresh_rows();return true

func clear_binding(id: String) -> void:
	cancel_capture();var problem:=assign(id,0);info.text=problem if not problem.is_empty() else Bindings.TITLES[id]+" has no keyboard shortcut.";refresh_rows()

func restore_defaults() -> void:
	cancel_capture();var problem:=save(Bindings.DEFAULTS);info.text=problem if not problem.is_empty() else "Default shortcuts restored."
	if problem.is_empty():load_error=""
	refresh_rows()
