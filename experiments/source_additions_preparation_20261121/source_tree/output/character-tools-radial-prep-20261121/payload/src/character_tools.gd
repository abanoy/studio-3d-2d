extends Node
# Opening/cancelling is read-only. Selecting an action enters an existing editor.
const Policy = preload("res://src/character_tool_policy.gd")
const StudioTheme = preload("res://src/studio_theme.gd")
var app: Control
var buttons: Array[Button] = []
var popup: PopupPanel
var actor_ref: WeakRef
var opened_revision := -1
var entries: Array = []
var choices: Array[Button] = []
var help: Label
var title: Label
var selected := 0
var last_button_state := ""

func setup(owner_app: Control) -> void: app = owner_app

func add_button(parent: Node) -> Button:
	var item := Button.new(); item.text = "Character tools"; item.icon = StudioTheme.icon("figure")
	item.expand_icon = false; item.focus_mode = Control.FOCUS_NONE; item.add_theme_constant_override("icon_max_width",22)
	parent.add_child(item); item.pressed.connect(open_from_button.bind(item))
	app.keyboard_shortcuts.decorate(item,"character_tools","Face, pose, loose parts, visibility and available model controls")
	buttons.append(item)
	return item

func target() -> RefCounted:
	return app.renderer.active_model() if app != null and is_instance_valid(app.renderer) else null

func fast_busy() -> bool:
	if app == null or not is_instance_valid(app): return true
	if app.playing or app.exporting or app.navigating or app.drawing: return true
	if app.source_import != null and app.source_import.pid > 0: return true
	if app.has_project != null and app.has_project.pid > 0: return true
	if app.pose_editor != null and app.pose_editor.dragging: return true
	if app.physics_editor != null:
		if app.physics_editor.grabbing(): return true
		if app.physics_editor.recording != null and app.physics_editor.recording.active: return true
		var helper: Node = app.physics_editor.helper_editor
		if helper != null and is_instance_valid(helper.window) and helper.window.visible: return true
	return false

func foreign_dialog(node: Node) -> bool:
	for child in node.get_children():
		if child == popup: continue
		if child is Window and child.get_flag(Window.FLAG_NO_FOCUS) and child.get_flag(Window.FLAG_MOUSE_PASSTHROUGH): continue
		if child is Window and child.visible and (child.exclusive or child is Popup): return true
		if foreign_dialog(child): return true
	return false

func current_entries(actor: RefCounted) -> Array:
	var hair_available := app.physics_editor != null and app.physics_editor.helper_editor != null
	var live := app.physics_editor != null and Policy.model(actor) and app.physics_editor.active(str(actor.data.get("id","")))
	return Policy.actions(actor,app.pose_editor,hair_available,live,app.frame)

func _process(_delta: float) -> void:
	if app == null or not is_instance_valid(app): return
	var actor: RefCounted = target()
	var busy: bool = fast_busy()
	var ready: bool = Policy.model(actor)
	var state: String = str(actor.get_instance_id() if actor != null else 0)+":"+str(busy)+":"+str(ready)
	if state != last_button_state:
		last_button_state = state
		for item in buttons:
			if not is_instance_valid(item): continue
			item.disabled = busy or not ready
			item.tooltip_text = ("Select a model or accessory in World first." if not ready else "Face, pose, loose parts, visibility and model controls")+" • "+app.keyboard_shortcuts.label_for("character_tools")
	if is_instance_valid(popup) and (busy or actor_ref == null or actor_ref.get_ref() != actor or not Policy.model(actor) or app.recovery_revision != opened_revision): close()

func open_from_button(item: Button) -> void:
	open(item.get_window() if is_instance_valid(item) else null)

func open_from_event(event: InputEventKey) -> void:
	var host: Window = app.get_window()
	for child in app.get_children():
		if child is Window and child.visible and not child.is_embedded() and child.get_window_id() == event.window_id:
			host = child; break
	open(host)

func open(preferred_host: Window=null) -> void:
	if fast_busy() or foreign_dialog(app): return
	var actor: RefCounted = target()
	if not Policy.model(actor): app.message("Select a model or accessory in World to open Character tools."); return
	close()
	actor_ref = weakref(actor); opened_revision = app.recovery_revision
	entries = current_entries(actor); selected = 0
	popup = PopupPanel.new(); popup.name = "CharacterTools"; popup.theme = app.theme
	popup.transient = true; popup.exclusive = false
	popup.popup_hide.connect(close); popup.window_input.connect(window_input)
	popup.focus_exited.connect(close)
	var host: Window = preferred_host if is_instance_valid(preferred_host) else app.get_window()
	popup.content_scale_factor = host.content_scale_factor
	if app.is_ancestor_of(host): host.add_child(popup)
	else: add_child(popup)
	var available: Vector2 = host.get_visible_rect().size
	var extent := Vector2i(mini(480,maxi(240,int(available.x)-24)),mini(460,maxi(240,int(available.y)-64)))
	var compact: bool = extent.x < 440 or extent.y < 420
	var panel := MarginContainer.new(); popup.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left","right","top","bottom"]: panel.add_theme_constant_override("margin_"+side,12)
	var content := VBoxContainer.new(); panel.add_child(content)
	title = Label.new(); title.text = "Character tools"; title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; content.add_child(title)
	var body: Control
	var scroll: ScrollContainer
	if compact:
		scroll = ScrollContainer.new(); scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; content.add_child(scroll)
		var column := VBoxContainer.new(); column.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(column); body = column
	else:
		body = Control.new(); body.custom_minimum_size = Vector2(432,300); body.size_flags_vertical = Control.SIZE_EXPAND_FILL; content.add_child(body)
	choices.clear()
	for index in range(entries.size()):
		var entry: Dictionary = entries[index]
		var item := Button.new(); item.text = entry.title; item.icon = StudioTheme.icon(entry.icon,StudioTheme.TEXT,20)
		item.expand_icon = false; item.focus_mode = Control.FOCUS_NONE
		item.disabled = not entry.enabled; item.tooltip_text = entry.reason
		item.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		item.custom_minimum_size = Vector2(118,56); body.add_child(item)
		if compact: item.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		else:
			var angle: float = -PI/2.0+TAU*float(index)/float(entries.size())
			item.size = Vector2(118,62)
			item.position = Vector2(216,150)+Vector2(cos(angle)*152.0,sin(angle)*118.0)-item.size*0.5
		item.pressed.connect(activate.bind(index))
		item.mouse_entered.connect(show_choice.bind(index))
		choices.append(item)
	help = Label.new(); help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; help.custom_minimum_size.y = 46
	content.add_child(help)
	var cancel: Button = app.button(content,"Cancel",close); cancel.focus_mode = Control.FOCUS_NONE
	popup.popup_centered(extent)
	show_choice(0)

func show_choice(index: int) -> void:
	if index < 0 or index >= entries.size(): return
	selected = index
	if is_instance_valid(title): title.text = "Character tools · "+str(entries[index].title)
	if is_instance_valid(help): help.text = str(entries[index].reason) if not str(entries[index].reason).is_empty() else "Open this existing editor. Arrows choose; Enter opens; Escape cancels."
	for i in range(choices.size()):
		var item: Button = choices[i]
		item.modulate = Color.WHITE if i == selected else Color(0.82,0.82,0.82,1.0)
		item.text = ("› " if i == selected else "")+str(entries[i].title)
		if item.get_parent().get_parent() is ScrollContainer and i == selected:
			item.get_parent().get_parent().ensure_control_visible(item)

func window_input(event: InputEvent) -> void:
	if not is_instance_valid(popup) or entries.is_empty() or not event is InputEventKey or not event.pressed or event.echo: return
	var owned_window: PopupPanel = popup
	if event.keycode == KEY_ESCAPE: close()
	elif event.keycode in [KEY_LEFT,KEY_UP]: show_choice(posmod(selected-1,entries.size()))
	elif event.keycode in [KEY_RIGHT,KEY_DOWN,KEY_TAB]: show_choice(posmod(selected+(-1 if event.shift_pressed else 1),entries.size()))
	elif event.keycode == KEY_HOME: show_choice(0)
	elif event.keycode == KEY_END: show_choice(entries.size()-1)
	elif event.keycode in [KEY_ENTER,KEY_KP_ENTER]: activate(selected)
	else: return
	if is_instance_valid(owned_window): owned_window.set_input_as_handled()

func activate(index: int) -> void:
	if not is_instance_valid(popup) or index < 0 or index >= entries.size(): return
	var actor: RefCounted = target()
	if fast_busy() or foreign_dialog(app) or actor_ref == null or actor_ref.get_ref() != actor or not Policy.model(actor) or app.recovery_revision != opened_revision: close(); return
	var current: Array = current_entries(actor)
	if not current[index].enabled:
		entries = current; show_choice(index); return
	var action: String = current[index].id
	var revision: int = opened_revision
	close()
	if target() != actor or fast_busy() or app.recovery_revision != revision or foreign_dialog(app): return
	_perform(action,actor)

func _perform(action: String,actor: RefCounted) -> void:
	if action == "face": app.pose_editor.open_shapes()
	elif action == "hair": app.physics_editor.helper_editor.open(true)
	elif action == "appearance":
		var editor: Node = Policy.optional_editor(app.pose_editor,"variant_editor")
		if editor != null: editor.open()
	elif action == "visibility": app.pose_editor.set_visibility_key(not actor.visible_at(app.frame))
	elif action in ["body","parameters"]:
		var view: Dictionary = app.renderer.view_state()
		app.mode.select(2); app.change_mode(2); app.renderer.restore_view(view)
		if action == "body": app.pose_editor.operation.grab_focus()
		else:
			var info: Node = Policy.optional_editor(app.pose_editor,"import_capabilities")
			if info != null: info.open()
			else: app.pose_editor.visible_toggle.grab_focus(); app.message("Model parameters are in the Pose inspector. Existing controls keep their usual Undo and save behavior.")

func close() -> void:
	var previous: PopupPanel = popup
	popup = null; actor_ref = null; entries.clear(); choices.clear()
	help = null; title = null; opened_revision = -1
	if is_instance_valid(previous): previous.hide(); previous.queue_free()

func _exit_tree() -> void:
	close(); buttons.clear(); app = null
