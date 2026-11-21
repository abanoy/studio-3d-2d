extends Node
# Read-only report UI; source/session ownership is checked before and during use.
const Summary=preload("res://src/import_capability_summary.gd")
const Model=preload("res://src/model.gd")
var editor: Node
var button: Button
var buttons: Array[Button]=[]
var window: Window
var actor_ref: WeakRef
var context: Dictionary={}
var summary_text: Label
var world_refs: Array[WeakRef]=[]
func setup(pose_editor: Node,parent: Node) -> void:
	editor=pose_editor;button=add_button(parent)
func add_button(parent: Node) -> Button:
	var item: Button=editor.app.button(parent,"Import info",open)
	item.tooltip_text="Available features, stored import data, compatibility notes and possible actions."
	item.visible=false;buttons.append(item);return item
func bind_world_action(selection: Node) -> void:
	for ref in world_refs:
		if ref.get_ref()==selection:return
	world_refs.append(weakref(selection))
func target() -> RefCounted:
	return editor.active_rig() if is_instance_valid(editor) and is_instance_valid(editor.app) else null
func owner_id() -> String:
	var sequence=editor.app.get("sequence_editor")
	return str(sequence.active_owner) if sequence else ""
func report_for(actor: RefCounted) -> Dictionary:
	if actor==null or actor.get_script()!=Model:return {}
	var metadata: Variant=actor.data.get("metadata",{})
	if not metadata is Dictionary:return {}
	var report: Variant=metadata.get("native_parameters",{})
	return report if report is Dictionary else {}
func root_id(actor: RefCounted) -> int:
	return actor.root.get_instance_id() if is_instance_valid(actor.root) else 0
func snapshot(actor: RefCounted) -> Dictionary:
	return {"session":str(editor.app.get("recovery_session")),"owner":owner_id(),"id":actor.data.get("id",""),"source":actor.data.get("source",""),"sha256":actor.data.get("sha256",""),"root":root_id(actor),"report":report_for(actor).duplicate(true)}
func matches() -> bool:
	var actor: RefCounted=target()
	if actor==null or actor_ref==null or actor_ref.get_ref()!=actor or context.is_empty():return false
	return str(editor.app.get("recovery_session"))==context.session and owner_id()==context.owner and actor.data.get("id","")==context.id and actor.data.get("source","")==context.source and actor.data.get("sha256","")==context.sha256 and root_id(actor)==context.root and report_for(actor)==context.report
func busy() -> bool:
	if not is_instance_valid(editor) or not is_instance_valid(editor.app):return true
	var app=editor.app
	if app.playing or app.exporting or app.has_project.pid>0:return true
	var importer=app.get("source_import")
	if importer and importer.pid>0:return true
	var home=app.get("home")
	if home and home.visible:return true
	var review=app.get("height_review")
	return review!=null and review.pending
func _process(_delta: float) -> void:
	if not is_instance_valid(editor) or not is_instance_valid(editor.app):close();return
	var actor: RefCounted=target()
	for item in buttons:
		if is_instance_valid(item):item.visible=actor!=null and actor.get_script()==Model;item.disabled=busy()
	if is_instance_valid(window) and (busy() or not matches()):close()
func close() -> void:
	if is_instance_valid(window):window.hide();window.queue_free()
	window=null;actor_ref=null;context.clear();summary_text=null
func open(show_window:=true) -> void:
	close()
	if busy():return
	var actor: RefCounted=target()
	if actor==null or actor.get_script()!=Model:return
	actor_ref=weakref(actor);context=snapshot(actor)
	var summary: Dictionary=Summary.summarize(context.report,actor)
	if not matches():close();return
	window=Window.new();window.title="Import info";window.theme=editor.app.theme
	window.transient=true;window.exclusive=false;window.unresizable=false;window.keep_title_visible=true
	window.min_size=Vector2i(300,180);window.close_requested.connect(close);add_child(window)
	var panel:=PanelContainer.new();window.add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var body:=VBoxContainer.new();panel.add_child(body)
	var scroll:=ScrollContainer.new();scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;body.add_child(scroll)
	var notes:=VBoxContainer.new();notes.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(notes)
	summary_text=editor.app.label(notes,Summary.plain_text(summary));summary_text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;summary_text.size_flags_horizontal=Control.SIZE_EXPAND_FILL;summary_text.custom_minimum_size.x=260
	editor.app.label(notes,"These notes describe this asset and its current setup. Original import data is preserved.").autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	var actions:=HBoxContainer.new();body.add_child(actions)
	editor.app.button(actions,"Refresh",open);editor.app.button(actions,"Close",close)
	if show_window:
		var host:=Vector2i(editor.app.get_viewport_rect().size)
		window.popup_centered(Vector2i(mini(680,maxi(300,host.x-80)),mini(620,maxi(180,host.y-120))))
func notify_import(report: Variant) -> void:
	# Async preparation facts do not borrow whichever model is currently selected.
	# Height acceptance or a later selection will expose its own retained report.
	if not is_instance_valid(editor) or not is_instance_valid(editor.app):return
	var summary: Dictionary=Summary.summarize(report)
	var count: int=int(summary.get("note_count",0))
	if not summary.actions.is_empty():editor.app.message("Imported. Some resources or features need attention. Open Import info for the available actions.")
	elif count>0:editor.app.message("Imported. %d compatibility notes are available in Import info." % count)
	else:editor.app.message("Imported through the standard HAS representation. Import info is available for this asset.")
func _exit_tree() -> void:
	close()
	for ref in world_refs:
		var selection=ref.get_ref()
		if selection:
			for item in buttons:selection.actions.erase(item)
	for item in buttons:
		if is_instance_valid(item):item.queue_free()
	buttons.clear();world_refs.clear();button=null;editor=null
