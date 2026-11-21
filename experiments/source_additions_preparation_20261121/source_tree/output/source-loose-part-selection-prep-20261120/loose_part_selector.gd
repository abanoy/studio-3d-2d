extends Node
# UNRUN list-only selection + ordinary reviewed inclusion queue.
const Selection = preload("res://src/loose_part_selection.gd")
var editor: Node
var list: ItemList
var model: RefCounted = Selection.new()
var status: Label
var add_button: Button
var remove_button: Button
var committing := false
var focus_due := 0
var queue_active := false
var review_queue: Array = []
var original_included: Dictionary = {}

func setup(owner_editor: Node, rows: ItemList, parent: Node) -> void:
	editor = owner_editor; list = rows
	list.select_mode = ItemList.SELECT_MULTI
	list.gui_input.connect(list_input)
	status = editor.app.label(parent,"Select parts with Ctrl or Shift, or drag across this list. The focused part is refined below.")
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var tools := HBoxContainer.new(); parent.add_child(tools)
	add_button = editor.app.button(tools,"Include selected",include_selected)
	add_button.tooltip_text = "Review every selected part through the existing checks, then include the checked setup groups. Nothing is applied to the model yet."
	remove_button = editor.app.button(tools,"Exclude selected groups",exclude_selected)
	remove_button.tooltip_text = "A shared setup group is removed as a whole, including other areas using those joints."

func bind_rows(initial: int = -1) -> void:
	var keys := []; var disabled := []
	for index in range(editor.assessment.get("regions",[]).size()):
		keys.append(editor.region_key(editor.assessment.regions[index]))
		if list.is_item_disabled(index): disabled.append(index)
	var error: String = model.configure(keys,disabled)
	if not error.is_empty(): status.text = error; return
	if model.eligible(initial): model.click(initial)
	render()

func blocked() -> bool:
	return editor == null or not is_instance_valid(editor.window) or editor.window != get_parent() or editor.pid > 0 or editor.app.playing or editor.app.exporting or editor.app.navigating

func render() -> void:
	if not is_instance_valid(list): return
	list.deselect_all()
	for index in model.snapshot().selected: list.select(index,false)
	var focus_text: String = editor.part_names[model.focus] if model.focus >= 0 and model.focus < editor.part_names.size() else "none"
	status.text = str(model.chosen.size())+" selected · focused part: "+focus_text+". Selection does not include setup groups or choose wind."

func external_focus(index: int) -> void:
	if committing or not model.eligible(index): return
	model.cancel(); model.click(index); render()

func hold_focus_controls() -> void:
	for field in editor.fields: field.editable = false
	editor.anchors.disabled = true; editor.existing_toggle.disabled = true; editor.patch_toggle.disabled = true
	editor.include_toggle.disabled = true; editor.apply_button.disabled = true

func schedule_focus() -> void:
	focus_due = Time.get_ticks_msec()+150
	hold_focus_controls()

func focus_now() -> void:
	if blocked() or queue_active or not model.eligible(model.focus): return
	focus_due = 0
	committing = true
	editor.select_part(model.focus)
	committing = false
	render()

func list_input(event: InputEvent) -> void:
	if blocked() or queue_active: return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			var index: int = list.get_item_at_position(event.position,true)
			if model.begin(index,event.ctrl_pressed,event.shift_pressed): focus_due = 0; hold_focus_controls(); list.grab_focus(); render(); list.accept_event()
		elif model.dragging:
			model.finish(); render(); schedule_focus(); list.accept_event()
	elif event is InputEventMouseMotion and model.dragging:
		model.update(list.get_item_at_position(event.position,false)); render(); list.accept_event()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE and model.dragging:
			model.cancel(); render(); schedule_focus(); list.accept_event(); return
		if event.ctrl_pressed and event.keycode == KEY_A:
			var first := -1; var last := -1
			for index in range(model.keys.size()):
				if model.eligible(index):
					if first < 0: first = index
					last = index
			if first >= 0: model.click(first); model.click(last,false,true); render(); schedule_focus()
			list.accept_event(); return
		if event.keycode not in [KEY_UP,KEY_DOWN,KEY_HOME,KEY_END]: return
		var index: int = 0 if event.keycode == KEY_HOME else model.keys.size()-1 if event.keycode == KEY_END else model.keys.size()-1 if event.keycode == KEY_UP and model.focus < 0 else model.focus+(-1 if event.keycode == KEY_UP else 1)
		var direction: int = -1 if event.keycode in [KEY_UP,KEY_END] else 1
		while index >= 0 and index < model.keys.size() and not model.eligible(index): index += direction
		if model.eligible(index):
			if event.ctrl_pressed and not event.shift_pressed: model.focus = index
			else: model.click(index,event.ctrl_pressed,event.shift_pressed)
			render(); schedule_focus()
		list.accept_event()

func _process(_delta: float) -> void:
	if editor == null: return
	if model.dragging and blocked(): model.cancel(); render()
	if is_instance_valid(add_button):
		add_button.disabled = blocked() or queue_active or model.chosen.is_empty()
		remove_button.disabled = add_button.disabled
	if focus_due > 0 and Time.get_ticks_msec() >= focus_due and not blocked() and not model.dragging: focus_now()

func include_selected() -> void:
	if blocked() or queue_active or model.chosen.is_empty(): return
	editor.stop_pending_preview("Reviewed setup changed")
	focus_due = 0; model.cancel()
	review_queue = model.snapshot().selected.duplicate()
	original_included = editor.included.duplicate(true)
	queue_active = true
	advance_review()

func advance_review() -> void:
	if not queue_active: return
	if editor == null or not is_instance_valid(editor.window) or editor.app.recovery_revision != editor.revision:
		abort_batch("The model changed. Previous included groups were kept."); return
	while not review_queue.is_empty():
		var index: int = int(review_queue[0])
		if not model.eligible(index): abort_batch("A selected part is no longer available. Previous included groups were kept."); return
		var group: String = editor.included_key(model.keys[index])
		if group.is_empty() or not editor.included[group].valid: break
		review_queue.pop_front()
	if review_queue.is_empty():
		queue_active = false; original_included.clear(); editor.refresh_inclusions(); render()
		editor.info.text = "Selected parts were reviewed and included. Apply remains a separate action; shared joints are grouped together."
		return
	model.focus = int(review_queue[0])
	committing = true; editor.select_part(model.focus); committing = false
	if editor.pid <= 0:
		abort_batch("The selected part review could not start. Previous included groups were kept."); return
	render(); editor.refresh_inclusions()

func after_review(value: Dictionary) -> void:
	if not queue_active: return
	if review_queue.is_empty() or editor.selected_key != model.keys[int(review_queue[0])]:
		abort_batch("The reviewed part changed. Previous included groups were kept."); return
	if not value.get("can_apply",false):
		abort_batch("One selected part needs a different attachment or patch. Previous included groups were kept."); return
	var group: String = editor.included_key(editor.selected_key)
	if not group.is_empty() and editor.included[group].valid:
		review_queue.pop_front(); advance_review()
	else:
		# This preserves the existing second review and native/shared-group logic.
		editor.include_part(true)
		if editor.pid <= 0:
			abort_batch("The selected setup review could not start. Previous included groups were kept."); return
		editor.refresh_inclusions()

func abort_batch(reason: String) -> void:
	if not queue_active: return
	editor.included = original_included.duplicate(true)
	queue_active = false; review_queue.clear(); original_included.clear()
	if editor.pid <= 0 and is_instance_valid(list):
		list.mouse_filter = Control.MOUSE_FILTER_STOP; list.focus_mode = Control.FOCUS_ALL
	editor.refresh_inclusions()
	if is_instance_valid(editor.info): editor.info.text = reason

func exclude_selected() -> void:
	if blocked() or queue_active: return
	editor.stop_pending_preview("Reviewed setup changed")
	var groups := {}
	for key in model.selected_keys():
		var group: String = editor.included_key(key)
		if not group.is_empty(): groups[group] = true
	for group in groups: editor.included.erase(group)
	editor.refresh_inclusions()

func shutdown() -> void:
	if editor != null: abort_batch("Review closed; no setup was applied.")
	focus_due = 0; model.clear(); editor = null

func _exit_tree() -> void: shutdown()
