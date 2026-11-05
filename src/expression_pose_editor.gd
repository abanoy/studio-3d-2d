extends Node
# Explicit grouped pose authoring; stored animation remains standard deform keys.
const Presets=preload("res://src/expression_presets.gd")
var editor
var panel: VBoxContainer
var choices: OptionButton
var amount: SpinBox
var apply_button: Button
var info: Label
var root_id:=0
var catalogue:={}

func setup(owner_editor,parent: Node) -> void:
	editor=owner_editor;panel=VBoxContainer.new();parent.add_child(panel)
	editor.app.label(panel,"Expressions / emotes")
	choices=OptionButton.new();choices.clip_text=true;panel.add_child(choices);choices.item_selected.connect(func(_index):refresh())
	var line:=HBoxContainer.new();panel.add_child(line);editor.app.label(line,"Strength")
	amount=SpinBox.new();amount.min_value=0;amount.max_value=1;amount.step=.05;amount.value=1;line.add_child(amount)
	apply_button=editor.app.button(panel,"Use expression pose",apply_pose)
	info=editor.app.label(panel,"");info.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART

func entry() -> Dictionary:
	if choices.selected<0 or choices.selected>=catalogue.get("entries",[]).size():return {}
	return catalogue.entries[choices.selected]

func sync() -> void:
	var actor: RefCounted=editor.actor();var next: int=actor.root.get_instance_id() if actor else 0
	if next!=root_id:
		root_id=next;catalogue=actor.root.get_meta(Presets.META,{"entries":[],"error":""}) if actor else {};choices.clear()
		for value in catalogue.get("entries",[]):choices.add_item(str(value.label).left(100))
	panel.visible=not catalogue.get("entries",[]).is_empty() or not catalogue.get("error","").is_empty()
	for i in range(choices.item_count):
		var value: Dictionary=catalogue.entries[i]
		choices.set_item_text(i,(str(value.native_name) if editor.app.advanced_mode else str(value.label)).left(100))
	refresh()

func refresh() -> void:
	var value:=entry();var reason: String=catalogue.get("error","")
	if not value.is_empty():reason=value.error
	var busy: bool=editor.app.playing or editor.app.exporting or editor.app.pose_editor.contacts.live_busy() or editor.app.source_import.pid>0 or editor.app.has_project.pid>0
	apply_button.disabled=value.is_empty() or not reason.is_empty() or busy or editor.dirty
	choices.disabled=busy;amount.editable=not busy
	if not reason.is_empty():info.text=reason;return
	if value.is_empty():info.text="";return
	info.text="Replaces embedded expression controls; keeps other deforms.\nCreates ordinary editable deform keys (or a draft with Auto-key off)."
	if value.binary:info.text+="\nBinary source: strength above 0.5 gives a full pose; otherwise off. Key interpolation stays editable."
	if editor.app.advanced_mode:
		info.text+="\nOriginal: "+str(value.native_name)+" · "+str(value.group)+" · "+str(value.binds.size())+" bindings"
		for bind in value.binds.slice(0,12):info.text+="\n"+str(bind.node)+":"+str(bind.index)+" "+str(bind.native_name)+" × "+str(bind.weight)
		if value.binds.size()>12:info.text+="\n… "+str(value.binds.size()-12)+" more bindings (all are applied)."
	if editor.dirty:info.text+="\nApply or discard the pending deform amount first."

func apply_pose() -> void:
	var actor: RefCounted=editor.actor();var value:=entry()
	if actor==null or actor.root.get_instance_id()!=root_id or value.is_empty():return
	if editor.dirty or editor.app.playing or editor.app.exporting or editor.app.pose_editor.contacts.live_busy() or editor.app.source_import.pid>0 or editor.app.has_project.pid>0:
		editor.app.message("Finish the pending edit and stop live motion before using an expression pose.");return
	var evaluated:=Presets.evaluate(catalogue,{value.id:amount.value})
	if not evaluated.error.is_empty():editor.app.message(evaluated.error);return
	var error: String=editor.app.pose_editor.set_shape_amounts(evaluated.values)
	if not error.is_empty():editor.app.message(error);return
	editor.signature="";editor.sync()
