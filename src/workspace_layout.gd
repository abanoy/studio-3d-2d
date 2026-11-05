extends Node
# Presentation only: move the same controls, never rebuild scene/editor state.
const FORMAT := "studio_workspace_1"
const DEFAULT := {"left":"world","right":"properties","bottom":"timeline"}
var app
var vertical: VSplitContainer
var horizontal: HSplitContainer
var right_split: HSplitContainer
var slots := {}
var panels := {}
var locations := DEFAULT.duplicate()
var floating := {}
var drag_id := ""
var drag_start := Vector2.ZERO
var dragged := false
var path := ""
var timer: Timer
var loading := false

func setup(owner_app, column: VBoxContainer, old_middle: HBoxContainer, hierarchy: Control, inspector: Control, transport: Control, ruler: Control, tracks: Control) -> void:
	app=owner_app
	path=ProjectSettings.globalize_path("res://output/workspace-layout.json")
	if "--script" in OS.get_cmdline_args() or OS.get_cmdline_user_args().size()>0:path=ProjectSettings.globalize_path("res://output/test-preferences/workspace-%d.json" % OS.get_process_id())
	vertical=VSplitContainer.new();vertical.name="WorkspaceVertical";vertical.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(vertical);column.move_child(vertical,0)
	horizontal=HSplitContainer.new();horizontal.size_flags_vertical=Control.SIZE_EXPAND_FILL;vertical.add_child(horizontal)
	right_split=HSplitContainer.new();right_split.size_flags_horizontal=Control.SIZE_EXPAND_FILL;horizontal.add_child(right_split)
	var center: Control=old_middle.get_child(1)
	center.reparent(right_split,false)
	for key in ["left","right","bottom"]:
		var slot:=VBoxContainer.new();slot.name="DockSlot"+key.capitalize();slot.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		slots[key]=slot
		if key=="left":horizontal.add_child(slot);horizontal.move_child(slot,0);slot.size_flags_horizontal=Control.SIZE_FILL
		elif key=="right":right_split.add_child(slot);slot.size_flags_horizontal=Control.SIZE_FILL
		else:vertical.add_child(slot)
	var time_box:=VBoxContainer.new()
	for control in [transport,ruler,tracks]:control.reparent(time_box,false)
	wrap_panel("world","World",hierarchy,"left")
	wrap_panel("properties","Properties",inspector,"right")
	wrap_panel("timeline","Timeline",time_box,"bottom")
	# The hierarchy's former caption is replaced by its draggable panel title.
	if hierarchy.get_child_count()>0 and hierarchy.get_child(0) is Label:hierarchy.get_child(0).hide()
	old_middle.queue_free()
	for split in [vertical,horizontal,right_split]:split.dragged.connect(func(_offset):save_later())
	timer=Timer.new();timer.one_shot=true;timer.wait_time=.35;timer.timeout.connect(save);add_child(timer)
	load_layout()

func wrap_panel(id: String,title: String,content: Control,slot: String) -> void:
	var panel:=VBoxContainer.new();panel.name="WorkspacePanel"+id.capitalize();panel.size_flags_horizontal=Control.SIZE_EXPAND_FILL;panel.size_flags_vertical=Control.SIZE_EXPAND_FILL
	var header:=HBoxContainer.new();header.add_theme_constant_override("separation",2);panel.add_child(header)
	var handle:=Button.new();handle.text="⋮⋮  "+title;handle.alignment=HORIZONTAL_ALIGNMENT_LEFT;handle.size_flags_horizontal=Control.SIZE_EXPAND_FILL;handle.mouse_default_cursor_shape=Control.CURSOR_DRAG;handle.tooltip_text="Drag this title to another panel to swap positions. Use the menu to float or dock it.";header.add_child(handle)
	handle.gui_input.connect(func(event):header_input(id,event))
	var menu:=MenuButton.new();menu.text="▾";menu.tooltip_text="Move or float this panel";header.add_child(menu)
	var popup:=menu.get_popup()
	for text in ["Dock left","Dock right","Dock below","Float panel","Reset workspace"]:popup.add_item(text)
	popup.id_pressed.connect(func(index):
		if index<3:dock(id,["left","right","bottom"][index])
		elif index==3:float_panel(id)
		else:reset())
	panels[id]=panel;slots[slot].add_child(panel)
	if content.get_parent():content.reparent(panel,false)
	else:panel.add_child(content)
	content.size_flags_vertical=Control.SIZE_EXPAND_FILL

func header_input(id: String,event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed:drag_id=id;drag_start=app.get_global_mouse_position();dragged=false
		else:finish_drag(app.get_global_mouse_position())
	elif event is InputEventMouseMotion and drag_id==id:
		dragged=dragged or app.get_global_mouse_position().distance_to(drag_start)>5

func _input(event: InputEvent) -> void:
	if drag_id.is_empty():return
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:drag_id="";dragged=false
	elif event is InputEventMouseMotion:dragged=dragged or event.position.distance_to(drag_start)>5
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:finish_drag(event.position)

func finish_drag(point: Vector2) -> void:
	var id:=drag_id;drag_id=""
	if id.is_empty() or not dragged:return
	dragged=false
	for key in slots:
		if slots[key].get_global_rect().has_point(point):dock(id,key);return
	# Dropping elsewhere keeps the layout; floating is an explicit menu action.

func slot_of(id: String) -> String:
	for key in locations:
		if locations[key]==id:return key
	return ""

func dock(id: String,slot: String) -> void:
	if not panels.has(id) or not slots.has(slot):return
	var previous:=slot_of(id)
	if previous==slot and not floating.has(id):return
	var other: String=locations.get(slot,"")
	if floating.has(id):
		var window: Window=floating[id];panels[id].set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT);panels[id].reparent(slots[slot],false);floating.erase(id);window.hide();window.queue_free()
	else:panels[id].reparent(slots[slot],false)
	if not other.is_empty() and other!=id:
		# A floated panel retains its last home; swapping uses that home too.
		if previous.is_empty():previous=slot
		locations[previous]=other
		if not floating.has(other):panels[other].reparent(slots[previous],false)
	locations[slot]=id
	save_later()

func float_panel(id: String) -> void:
	if not panels.has(id) or floating.has(id):return
	var window:=Window.new();window.visible=false;window.title=panels[id].get_child(0).get_child(0).text.replace("⋮⋮  ","");window.theme=app.theme;window.exclusive=false;window.transient=true;window.min_size=Vector2i(260,200);window.keep_title_visible=true
	app.add_child(window);floating[id]=window;panels[id].reparent(window,false);panels[id].set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	window.min_size=Vector2i(panels[id].get_combined_minimum_size()).max(Vector2i(260,200))
	window.close_requested.connect(func():dock(id,slot_of(id)))
	window.size=Vector2i(900,380) if id=="timeline" else Vector2i(340,600)
	window.popup_centered();window.size_changed.connect(save_later)
	window.window_input.connect(func(event):
		if event is InputEventKey and not (window.gui_get_focus_owner() is LineEdit or window.gui_get_focus_owner() is TextEdit):app._input(event))
	save_later()

func reset() -> void:
	loading=true
	for id in floating.keys():
		var window: Window=floating[id];panels[id].set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT);panels[id].reparent(slots[slot_of(id)],false);window.hide();window.queue_free()
	floating.clear();locations=DEFAULT.duplicate()
	for slot in locations:
		if panels[locations[slot]].get_parent()!=slots[slot]:panels[locations[slot]].reparent(slots[slot],false)
	for split in [vertical,horizontal,right_split]:split.split_offset=0
	loading=false;save_later()

func state() -> Dictionary:
	return {"format":FORMAT,"slots":locations.duplicate(),"split":[vertical.split_offset,horizontal.split_offset,right_split.split_offset]}

func save_later() -> void:
	if not loading and timer:timer.start()

func save() -> void:
	if loading or path.is_empty():return
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file:=FileAccess.open(path+".tmp",FileAccess.WRITE)
	if not file:return
	file.store_string(JSON.stringify(state()));file.close();DirAccess.rename_absolute(path+".tmp",path)

func load_layout() -> void:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>16384:return
	var value=JSON.parse_string(file.get_as_text())
	if not value is Dictionary or value.get("format")!=FORMAT or not value.get("slots") is Dictionary or value.slots.size()!=3 or not value.get("split") is Array or value.split.size()!=3:return
	var ids:=[]
	for slot in DEFAULT:
		if not value.slots.get(slot) is String or not panels.has(value.slots[slot]) or value.slots[slot] in ids:return
		ids.append(value.slots[slot])
	for offset in value.split:
		if not (offset is int or offset is float) or not is_finite(float(offset)) or offset!=floor(offset) or absf(offset)>4000:return
	loading=true;locations=value.slots.duplicate()
	for slot in locations:
		if panels[locations[slot]].get_parent()!=slots[slot]:panels[locations[slot]].reparent(slots[slot],false)
	vertical.split_offset=int(value.split[0]);horizontal.split_offset=int(value.split[1]);right_split.split_offset=int(value.split[2]);loading=false

func _notification(what: int) -> void:
	if what==NOTIFICATION_WM_WINDOW_FOCUS_OUT:drag_id="";dragged=false

func _exit_tree() -> void:
	if timer and not timer.is_stopped():save()
