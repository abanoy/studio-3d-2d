extends Node
# Nonmodal read-only info, present in Simple and Advanced with the same meaning.
const Summary = preload("res://src/import_capability_summary.gd")
const Model = preload("res://src/model.gd")
var editor: Node
var button: Button
var buttons: Array[Button] = []
var window: Window
var actor_ref: WeakRef

func setup(pose_editor: Node, parent: Node) -> void:
	editor = pose_editor
	button = add_button(parent)

func add_button(parent: Node) -> Button:
	var item: Button = editor.app.button(parent,"Import info",open)
	item.tooltip_text = "Available features, stored source data, compatibility notes and possible actions."
	item.visible = false
	buttons.append(item)
	return item

func target() -> RefCounted:
	return editor.active_rig() if editor != null else null

func report_for(actor: RefCounted) -> Dictionary:
	if actor == null or actor.get_script() != Model: return {}
	var metadata: Variant = actor.data.get("metadata",{})
	if not metadata is Dictionary: return {}
	var report: Variant = metadata.get("native_parameters",{})
	return report if report is Dictionary else {}

func busy() -> bool:
	return editor == null or not is_instance_valid(editor.app) or editor.app.playing or editor.app.exporting or editor.app.has_project.pid > 0

func _process(_delta: float) -> void:
	if editor == null or not is_instance_valid(button): return
	var actor: RefCounted = target()
	for item in buttons:
		if is_instance_valid(item):
			item.visible = actor != null and actor.get_script() == Model
			item.disabled = busy()
	if is_instance_valid(window) and (busy() or actor_ref == null or actor_ref.get_ref() != actor): close()

func close() -> void:
	if is_instance_valid(window): window.hide(); window.queue_free()
	window = null; actor_ref = null

func open() -> void:
	close()
	if busy(): return
	var actor: RefCounted = target()
	var report: Dictionary = report_for(actor)
	if actor == null: return
	var summary: Dictionary = Summary.summarize(report,actor)
	actor_ref = weakref(actor)
	window = Window.new(); window.title = "Import info"; window.theme = editor.app.theme
	window.transient = true; window.exclusive = false
	window.close_requested.connect(close); add_child(window)
	var panel := PanelContainer.new(); window.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var scroll := ScrollContainer.new(); scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var body := VBoxContainer.new(); body.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(body)
	var text: Label = editor.app.label(body,Summary.plain_text(summary))
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.custom_minimum_size.x = 560
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	editor.app.label(body,"These notes describe this imported asset and the current model setup. Original import data is preserved.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	editor.app.button(body,"Refresh",open)
	editor.app.button(body,"Close",close)
	window.popup_centered(Vector2i(640,mini(600,maxi(280,int(editor.app.get_viewport_rect().size.y)-160))))

func notify_import(report: Variant) -> void:
	# Success is informational, never a mandatory dialog. Failed imports keep the
	# existing failure path and never call this method.
	if editor == null or not is_instance_valid(editor.app): return
	var summary: Dictionary = Summary.summarize(report,target())
	var count: int = int(summary.get("note_count",0))
	if not summary.actions.is_empty(): editor.app.message("Imported. Some resources or features need attention. Open Import info for the available actions.")
	elif count > 0: editor.app.message("Imported. %d compatibility notes are available in Import info." % count)
	else: editor.app.message("Imported through the standard HAS representation. Import info is available for this asset.")

func _exit_tree() -> void:
	close()
	for item in buttons:
		if is_instance_valid(item): item.queue_free()
	buttons.clear(); button = null; editor = null
