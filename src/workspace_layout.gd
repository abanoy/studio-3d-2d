extends Node
# Presentation only: every dock/window owns the same live editor controls.
const FORMAT := "studio_workspace_2"
const DEFAULT := {"left":"world","right":"properties","bottom":"timeline","top":""}
const DEFAULT_VERTICAL_OFFSET := -234
const EDGES := ["left","right","bottom","top"]
var app
var vertical: VSplitContainer
var top_split: VSplitContainer
var horizontal: HSplitContainer
var right_split: HSplitContainer
var slots := {}
var tabs := {}
var panels := {}
var groups := {"left":["world"],"right":["properties"],"bottom":["timeline"],"top":[]}
var locations := DEFAULT.duplicate()
var floating := {}
var drag_id := ""
var drag_start := Vector2.ZERO
var dragged := false
var path := ""
var timer: Timer
var loading := false
var preview: Panel
var preview_label: Label
var last_window_geometry := {}

func setup(owner_app, column: VBoxContainer, old_middle: HBoxContainer, hierarchy: Control, inspector: Control, transport: Control, ruler: Control, tracks: Control) -> void:
	app=owner_app
	path=ProjectSettings.globalize_path("res://output/workspace-layout.json")
	var args:=OS.get_cmdline_user_args()
	var opening_project:=args.size()==2 and args[0]=="--open-project"
	if "--script" in OS.get_cmdline_args() or not args.is_empty() and not opening_project:path=ProjectSettings.globalize_path("res://output/test-preferences/workspace-%d.json" % OS.get_process_id())
	vertical=VSplitContainer.new();vertical.name="WorkspaceVertical";vertical.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(vertical);column.move_child(vertical,0)
	top_split=VSplitContainer.new();top_split.size_flags_vertical=Control.SIZE_EXPAND_FILL;vertical.add_child(top_split)
	horizontal=HSplitContainer.new();horizontal.size_flags_vertical=Control.SIZE_EXPAND_FILL;top_split.add_child(horizontal)
	right_split=HSplitContainer.new();right_split.size_flags_horizontal=Control.SIZE_EXPAND_FILL;horizontal.add_child(right_split)
	var center: Control=old_middle.get_child(1);center.reparent(right_split,false)
	for key in EDGES:
		var slot:=VBoxContainer.new();slot.name="DockSlot"+key.capitalize();slot.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		slots[key]=slot
		if key=="left":horizontal.add_child(slot);horizontal.move_child(slot,0);slot.size_flags_horizontal=Control.SIZE_FILL
		elif key=="right":right_split.add_child(slot);slot.size_flags_horizontal=Control.SIZE_FILL
		elif key=="top":top_split.add_child(slot);top_split.move_child(slot,0)
		else:vertical.add_child(slot)
		var book:=TabContainer.new();book.name="DockTabs";book.size_flags_horizontal=Control.SIZE_EXPAND_FILL;book.size_flags_vertical=Control.SIZE_EXPAND_FILL;book.all_tabs_in_front=true;book.use_hidden_tabs_for_min_size=true;slot.add_child(book);tabs[key]=book
		book.add_theme_stylebox_override("panel",StyleBoxEmpty.new())
		for styled in [book,book.get_tab_bar()]:
			for state_name in ["tab_selected","tab_unselected","tab_hovered","tab_disabled"]:styled.add_theme_stylebox_override(state_name,app.theme.get_stylebox("pressed" if state_name=="tab_selected" else "normal","Button"))
			for color_name in ["font_selected_color","font_unselected_color","font_hovered_color"]:styled.add_theme_color_override(color_name,Color("163854"))
		book.tab_changed.connect(func(_index):save_later())
		book.get_tab_bar().gui_input.connect(func(event):
			if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
				var index: int=book.get_tab_bar().get_tab_idx_at_point(event.position)
				if index>=0:
					var panel: Control=book.get_tab_control(index)
					for id in panels:
						if panels[id]==panel:header_input(id,event);break)
	var time_box:=VBoxContainer.new()
	for control in [transport,ruler,tracks]:control.reparent(time_box,false)
	wrap_panel("world","World",hierarchy,"left");wrap_panel("properties","Properties",inspector,"right");wrap_panel("timeline","Timeline",time_box,"bottom")
	tracks.size_flags_vertical=Control.SIZE_EXPAND_FILL
	if hierarchy.get_child_count()>0 and hierarchy.get_child(0) is Label:hierarchy.get_child(0).hide()
	old_middle.queue_free()
	for split in [vertical,top_split,horizontal,right_split]:
		split.add_theme_constant_override("separation",10)
		split.get_drag_area_control().tooltip_text="Drag to resize these panels. Drag a panel title to dock, tab or detach it."
		split.dragged.connect(func(_offset):save_later())
	preview=Panel.new();preview.mouse_filter=Control.MOUSE_FILTER_IGNORE;preview.z_index=100;preview.hide();app.add_child(preview)
	var style:=StyleBoxFlat.new();style.bg_color=Color(.15,.48,.8,.18);style.border_color=Color(.15,.48,.8,.9);style.set_border_width_all(2);style.set_corner_radius_all(6);preview.add_theme_stylebox_override("panel",style)
	preview_label=Label.new();preview_label.mouse_filter=Control.MOUSE_FILTER_IGNORE;preview_label.position=Vector2(12,8);preview.add_child(preview_label)
	timer=Timer.new();timer.one_shot=true;timer.wait_time=.35;timer.timeout.connect(save);add_child(timer)
	refresh_slots()
	if not load_layout():call_deferred("apply_default_split")

func apply_default_split() -> void:
	vertical.split_offset=DEFAULT_VERTICAL_OFFSET
	top_split.split_offset=180

func wrap_panel(id: String,title: String,content: Control,slot: String) -> void:
	var panel:=VBoxContainer.new();panel.name=title;panel.size_flags_horizontal=Control.SIZE_EXPAND_FILL;panel.size_flags_vertical=Control.SIZE_EXPAND_FILL
	var header:=HBoxContainer.new();header.add_theme_constant_override("separation",2);panel.add_child(header)
	var handle:=Button.new();handle.text="⋮⋮  "+title;handle.alignment=HORIZONTAL_ALIGNMENT_LEFT;handle.size_flags_horizontal=Control.SIZE_EXPAND_FILL;handle.mouse_default_cursor_shape=Control.CURSOR_DRAG;handle.tooltip_text="Drag to a highlighted edge to dock, onto another panel to make tabs, or into open space to detach a window. Esc cancels.";header.add_child(handle)
	handle.gui_input.connect(func(event):header_input(id,event))
	var menu:=MenuButton.new();menu.text="▾";menu.tooltip_text="Dock, tab, detach or reset this panel";header.add_child(menu)
	var popup:=menu.get_popup()
	for text in ["Dock left","Dock right","Dock below","Dock above","Float panel","Reset workspace","Tab with World","Tab with Properties","Tab with Timeline"]:popup.add_item(text)
	popup.about_to_popup.connect(func():
		for i in range(3):popup.set_item_disabled(6+i,["world","properties","timeline"][i]==id))
	popup.id_pressed.connect(func(index):
		if index<4:dock(id,EDGES[index])
		elif index==4:float_panel(id)
		elif index==5:reset()
		else:tab_panel(id,["world","properties","timeline"][index-6]))
	panels[id]=panel;tabs[slot].add_child(panel)
	var body: Control=panel
	if id=="world" or id=="timeline":
		var scroll:=ScrollContainer.new();scroll.name="WorldContentScroll" if id=="world" else "TimelineContentScroll";scroll.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
		scroll.custom_minimum_size=Vector2(120,120) if id=="world" else Vector2(0,96);scroll.follow_focus=true
		scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;scroll.vertical_scroll_mode=ScrollContainer.SCROLL_MODE_AUTO
		panel.add_child(scroll);body=scroll
	if content.get_parent():content.reparent(body,false)
	else:body.add_child(content)
	content.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	content.size_flags_vertical=Control.SIZE_EXPAND_FILL

func root_point(event: InputEventMouse,window: Window,in_gui:=false) -> Vector2:
	var point:=event.global_position if in_gui else event.position
	if window==app.get_window():return point
	return (Vector2(window.position-app.get_window().position)+point*window.content_scale_factor)/app.get_window().content_scale_factor

func header_input(id: String,event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
		drag_id=id;drag_start=root_point(event,panels[id].get_window(),true);dragged=false
	elif event is InputEventMouse and panels[id].get_window()!=app.get_window():route_drag(event,panels[id].get_window(),true)

func _input(event: InputEvent) -> void:
	if not drag_id.is_empty():route_drag(event,app.get_window())

func route_drag(event: InputEvent,window: Window,in_gui:=false) -> void:
	if drag_id.is_empty():return
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:cancel_drag();return
	if event is InputEventMouseMotion:
		var point:=root_point(event,window,in_gui);dragged=dragged or point.distance_to(drag_start)>6
		if dragged:show_target(point)
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and not event.pressed:finish_drag(root_point(event,window,in_gui))

func cancel_drag() -> void:
	drag_id="";dragged=false
	if is_instance_valid(preview):preview.hide()

func target_at(point: Vector2) -> Dictionary:
	var area:=vertical.get_global_rect()
	if area.has_point(point):
		var band:=36.0
		if point.x<area.position.x+band:return {"kind":"dock","slot":"left"}
		if point.x>area.end.x-band:return {"kind":"dock","slot":"right"}
		if point.y<area.position.y+band:return {"kind":"dock","slot":"top"}
		if point.y>area.end.y-band:return {"kind":"dock","slot":"bottom"}
		for slot in EDGES:
			if slots[slot].visible and slots[slot].get_global_rect().has_point(point):return {"kind":"tab","slot":slot}
	return {"kind":"float"}

func show_target(point: Vector2) -> void:
	var target:=target_at(point);var area:=vertical.get_global_rect();var rect: Rect2
	if target.kind=="tab":rect=slots[target.slot].get_global_rect();preview_label.text="Tab here"
	elif target.kind=="dock":
		rect=area;preview_label.text="Dock "+str(target.slot)
		if target.slot in ["left","right"]:
			rect.size.x=minf(320,area.size.x*.25)
			if target.slot=="right":rect.position.x=area.end.x-rect.size.x
		else:
			rect.size.y=minf(220,area.size.y*.3)
			if target.slot=="bottom":rect.position.y=area.end.y-rect.size.y
	else:
		rect=Rect2(point+Vector2(12,12),Vector2(230,70));rect.position=rect.position.clamp(Vector2.ZERO,app.get_viewport_rect().size-rect.size);preview_label.text="Detach as a window"
	preview.position=rect.position;preview.size=rect.size;preview.show()

func finish_drag(point: Vector2) -> void:
	var id:=drag_id;var moved:=dragged;cancel_drag()
	if id.is_empty() or not moved:return
	var target:=target_at(point)
	if target.kind=="dock":dock(id,target.slot)
	elif target.kind=="tab":
		var other: String=""
		for candidate in groups[target.slot]:
			if candidate!=id and not floating.has(candidate):other=candidate;break
		if not other.is_empty():tab_panel(id,other)
	else:
		float_panel(id,Vector2i(Vector2(app.get_window().position)+point*app.get_window().content_scale_factor))

func slot_of(id: String) -> String:
	for key in groups:
		if id in groups[key]:return key
	return ""

func refresh_slots() -> void:
	for slot in EDGES:
		locations[slot]=groups[slot][0] if not groups[slot].is_empty() else ""
		var count: int=tabs[slot].get_child_count();tabs[slot].tabs_visible=count>1;slots[slot].visible=count>0

func restore_panel(id: String,slot: String) -> void:
	if floating.has(id):
		panels[id].set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
		var window: Window=floating[id];floating.erase(id);panels[id].reparent(tabs[slot],false);window.hide();window.queue_free()
	elif panels[id].get_parent()!=tabs[slot]:
		panels[id].set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT);panels[id].reparent(tabs[slot],false)

func dock(id: String,slot: String) -> void:
	if not panels.has(id) or not slots.has(slot):return
	var previous:=slot_of(id)
	if previous==slot:
		if floating.has(id):restore_panel(id,slot);refresh_slots();save_later()
		return
	# Explicit edge docking swaps an occupied dock's first panel; body drops make tabs.
	var other: String=groups[slot][0] if not groups[slot].is_empty() else ""
	groups[previous].erase(id)
	if not other.is_empty():groups[slot].erase(other);groups[previous].append(other);restore_panel(other,previous)
	groups[slot].append(id);restore_panel(id,slot);refresh_slots();tabs[slot].current_tab=panels[id].get_index();save_later()

func tab_panel(id: String,other: String) -> void:
	if id==other or not panels.has(id) or not panels.has(other):return
	var slot:=slot_of(other);var previous:=slot_of(id)
	if previous!=slot:groups[previous].erase(id);groups[slot].append(id)
	restore_panel(other,slot);restore_panel(id,slot);refresh_slots();tabs[slot].current_tab=panels[id].get_index();save_later()

func float_panel(id: String,point:=Vector2i(-100000,-100000)) -> void:
	if not panels.has(id):return
	if floating.has(id):
		if point.x!=-100000:floating[id].position=point
		return
	var window:=Window.new();window.visible=false;window.title=panels[id].name;window.theme=app.theme;window.exclusive=false;window.transient=true;window.force_native=not OS.has_feature("web");window.keep_title_visible=true;window.content_scale_factor=app.get_window().content_scale_factor
	app.add_child(window);floating[id]=window;panels[id].reparent(window,false);panels[id].set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	window.min_size=Vector2i(panels[id].get_combined_minimum_size()).max(Vector2i(220,160))
	window.close_requested.connect(func():dock(id,slot_of(id)))
	window.size=Vector2i(900,380) if id=="timeline" else Vector2i(340,600)
	window.popup_centered()
	if point.x!=-100000:window.position=point
	window.size_changed.connect(save_later);window.titlebar_changed.connect(save_later)
	window.window_input.connect(func(event):
		if not drag_id.is_empty():route_drag(event,window)
		elif event is InputEventKey and not (window.gui_get_focus_owner() is LineEdit or window.gui_get_focus_owner() is TextEdit):app._input(event))
	refresh_slots();save_later()

func reset() -> void:
	loading=true;cancel_drag()
	groups={"left":["world"],"right":["properties"],"bottom":["timeline"],"top":[]}
	for slot in groups:
		for id in groups[slot]:restore_panel(id,slot)
	refresh_slots()
	for split in [vertical,horizontal,right_split]:split.split_offset=0
	apply_default_split();loading=false;save_later()

func state() -> Dictionary:
	var windows:={};var selected:={}
	for id in floating:
		var window: Window=floating[id];windows[id]={"position":[window.position.x,window.position.y],"size":[window.size.x,window.size.y]}
	for slot in EDGES:
		var current: Control=tabs[slot].get_current_tab_control()
		if current:selected[slot]=str(current.name)
	return {"format":FORMAT,"slots":locations.duplicate(),"groups":groups.duplicate(true),"split":[vertical.split_offset,horizontal.split_offset,right_split.split_offset,top_split.split_offset],"floating":windows,"selected":selected}

func save_later() -> void:
	if not loading and timer:timer.start()

func _process(_delta: float) -> void:
	var geometry:={}
	for id in floating:
		var window: Window=floating[id];geometry[id]=[window.position,window.size]
	if geometry!=last_window_geometry:
		last_window_geometry=geometry;save_later()

func save() -> void:
	if loading or path.is_empty():return
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file:=FileAccess.open(path+".tmp",FileAccess.WRITE)
	if not file:return
	file.store_string(JSON.stringify(state()));file.close();DirAccess.rename_absolute(path+".tmp",path)

func load_layout() -> bool:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>16384:return false
	var value=JSON.parse_string(file.get_as_text())
	if not value is Dictionary:return false
	if value.get("format")=="studio_workspace_1" and value.get("slots") is Dictionary and value.slots.size()==3:
		value.groups={"left":[],"right":[],"bottom":[],"top":[]}
		for slot in ["left","right","bottom"]:value.groups[slot]=[value.slots.get(slot,"")]
		if not value.get("split") is Array or value.split.size()!=3:return false
		value.split.append(180);value.floating={};value.selected={}
	elif value.get("format")!=FORMAT:return false
	if not value.get("groups") is Dictionary or value.groups.size()!=4 or not value.get("split") is Array or value.split.size()!=4:return false
	var ids:=[]
	for slot in EDGES:
		if not value.groups.get(slot) is Array:return false
		for id in value.groups[slot]:
			if not id is String or not panels.has(id) or id in ids:return false
			ids.append(id)
	if ids.size()!=panels.size():return false
	for offset in value.split:
		if not (offset is int or offset is float) or not is_finite(float(offset)) or offset!=floor(offset) or absf(offset)>10000:return false
	if not value.get("floating") is Dictionary or not value.get("selected") is Dictionary:return false
	for id in value.floating:
		if not panels.has(id) or not value.floating[id] is Dictionary:return false
		for field in ["position","size"]:
			var pair=value.floating[id].get(field)
			if not pair is Array or pair.size()!=2:return false
			for number in pair:
				if not (number is int or number is float) or not is_finite(float(number)) or number!=floor(number) or absf(number)>50000:return false
		if value.floating[id].size[0]<1 or value.floating[id].size[1]<1:return false
	loading=true;cancel_drag();groups=value.groups.duplicate(true)
	for slot in EDGES:
		for id in groups[slot]:restore_panel(id,slot)
	refresh_slots()
	vertical.split_offset=int(value.split[0]);horizontal.split_offset=int(value.split[1]);right_split.split_offset=int(value.split[2]);top_split.split_offset=int(value.split[3])
	for id in value.floating:
		var geometry: Dictionary=value.floating[id];float_panel(id);var window: Window=floating[id];window.size=Vector2i(geometry.size[0],geometry.size[1]);var point:=Vector2i(geometry.position[0],geometry.position[1]);var reachable:=false
		for screen in range(DisplayServer.get_screen_count()):
			if DisplayServer.screen_get_usable_rect(screen).intersects(Rect2i(point,Vector2i(window.size.x,32))):reachable=true
		window.position=point if reachable else DisplayServer.screen_get_usable_rect().position+Vector2i(40,40)
	for slot in EDGES:
		for child in tabs[slot].get_children():
			if str(child.name)==value.selected.get(slot,""):tabs[slot].current_tab=child.get_index()
	loading=false;return true

func _notification(what: int) -> void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:cancel_drag()

func _exit_tree() -> void:
	if timer and not timer.is_stopped():save()
