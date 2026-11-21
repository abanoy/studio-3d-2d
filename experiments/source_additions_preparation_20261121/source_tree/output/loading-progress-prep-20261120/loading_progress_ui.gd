extends Node
# Non-authoritative view. Existing operation owner keeps all cancel/install guards.
const State = preload("res://src/loading_progress_state.gd")
var model: RefCounted = State.new()
var window: Window
var label: Label
var detail: Label
var bar: ProgressBar
var cancel_button: Button
var _cancel: Callable
var _owner: WeakRef

func open(app: Node,operation_owner: Node,operation: String,title: String,cancel: Callable) -> bool:
	if model.busy or not is_instance_valid(app) or not is_instance_valid(operation_owner) or not cancel.is_valid() or not model.begin(operation,title):return false
	_owner=weakref(operation_owner);_cancel=cancel
	window=Window.new();window.title=title;window.theme=app.theme;window.transient=true;window.exclusive=true
	window.close_requested.connect(request_cancel);app.add_child(window)
	var panel:=PanelContainer.new();panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);window.add_child(panel)
	panel.add_theme_stylebox_override("panel",preload("res://src/studio_theme.gd").surface("f4f7fb","dce5ee"))
	var box:=VBoxContainer.new();box.add_theme_constant_override("separation",12);panel.add_child(box)
	label=Label.new();label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;box.add_child(label)
	bar=ProgressBar.new();bar.show_percentage=false;bar.custom_minimum_size=Vector2(500,24);box.add_child(bar)
	detail=Label.new();box.add_child(detail)
	cancel_button=Button.new();cancel_button.text="Cancel";cancel_button.pressed.connect(request_cancel);box.add_child(cancel_button)
	refresh();window.popup_centered(Vector2i(600,180));return true
func refresh() -> void:
	if not is_instance_valid(window):return
	label.text="Cancelling after the current step…" if model.cancelling else model.label
	bar.indeterminate=model.total==null
	if model.total!=null:bar.min_value=0;bar.max_value=float(model.total);bar.value=float(model.completed)
	detail.text="Working…" if model.total==null else "%d / %d %s in this stage" % [model.completed,model.total,model.unit]
	cancel_button.disabled=model.cancelling
func update(packet: Variant) -> bool:
	if not model.update(packet):return false
	refresh();return true
func request_cancel() -> void:
	if not model.request_cancel(model.token):return
	refresh()
	if _owner!=null and is_instance_valid(_owner.get_ref()) and _cancel.is_valid():_cancel.call()
func finish(operation: String,success: bool) -> bool:
	if not model.finish(operation,success):return false
	close_view();return true
func close_view() -> void:
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;_owner=null;_cancel=Callable()
func _process(_delta: float) -> void:
	if model.busy and (_owner==null or not is_instance_valid(_owner.get_ref())):
		model.finish(model.token,false);close_view()
func _exit_tree() -> void:
	request_cancel();close_view()
