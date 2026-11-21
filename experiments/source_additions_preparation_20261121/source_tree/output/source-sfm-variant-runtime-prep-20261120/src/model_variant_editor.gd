extends Node
# Static, per-selected-model controls. Existing pose/world history owns Undo;
# selection is ordinary model data and therefore follows packed/linked Saves.
const Schema = preload("res://src/model_variants.gd")
var editor
var button: Button
var window: Window
var skin: OptionButton
var choices: Dictionary = {}
var target_id := ""
var updating := false
var last_actor: RefCounted

func setup(pose_editor, parent: Node) -> void:
	editor = pose_editor
	button = editor.app.button(parent,"Appearance…",open)
	button.tooltip_text = "Choose a skin or switch retained model parts. Changes are static and can be undone."
	button.visible = false
func target() -> RefCounted:
	return editor.active_rig() if editor != null else null
func eligible(actor: RefCounted) -> bool:
	return actor != null and not Schema.manifest(actor.data).is_empty() and actor.variants != null
func close() -> void:
	if is_instance_valid(window): window.hide(); window.queue_free()
	window = null; skin = null; choices.clear(); target_id = ""; last_actor = null
func _process(_delta: float) -> void:
	if editor == null: return
	var actor: RefCounted = target()
	button.visible = eligible(actor)
	button.disabled = editor.app.playing or editor.app.exporting or editor.app.has_project.pid > 0
	if is_instance_valid(window) and (actor == null or actor != last_actor or actor.data.id != target_id or actor.variants == null): close()
	if is_instance_valid(window):
		if is_instance_valid(skin): skin.disabled = button.disabled
		for group in choices: choices[group].disabled = button.disabled
		refresh()
func open() -> void:
	close()
	var actor: RefCounted = target()
	if not eligible(actor) or button.disabled: return
	editor.app.stop(); editor.finish_drag()
	last_actor = actor; target_id = str(actor.data.id)
	window = Window.new(); window.title = "Model appearance"; window.theme = editor.app.theme; window.transient = true
	window.close_requested.connect(close); add_child(window)
	var panel: PanelContainer = PanelContainer.new(); window.add_child(panel); panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var scroll: ScrollContainer = ScrollContainer.new(); scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; panel.add_child(scroll)
	var body: VBoxContainer = VBoxContainer.new(); body.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(body)
	var declared: Dictionary = actor.variants.declared
	var selected: Dictionary = actor.variants.current
	updating = true
	if declared.skins.size() > 1:
		editor.app.label(body,"Skin")
		skin = OptionButton.new(); skin.size_flags_horizontal = Control.SIZE_EXPAND_FILL; body.add_child(skin)
		for row in declared.skins: skin.add_item(row.name if not row.name.is_empty() else "Skin " + str(row.id+1),row.id)
		skin.select(selected.skin); skin.item_selected.connect(func(index: int): choose(index,"",0))
	for group in declared.groups:
		editor.app.label(body,group.name if not group.name.is_empty() else "Part " + str(group.id+1))
		var option: OptionButton = OptionButton.new(); option.size_flags_horizontal = Control.SIZE_EXPAND_FILL; body.add_child(option)
		for row in group.choices:
			var text: String = "Hidden" if row.blank else row.name if not row.name.is_empty() else "Option " + str(row.id+1)
			option.add_item(text,row.id)
		option.select(selected.groups[str(group.id)]); choices[str(group.id)] = option
		option.item_selected.connect(choose_group.bind(str(group.id)))
	editor.app.label(body,"Applies only to this model. Undo restores the previous selection.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	editor.app.button(body,"Close",close)
	updating = false
	window.popup_centered(Vector2i(360,mini(520,maxi(240,int(editor.app.get_viewport_rect().size.y)-160))))
func choose_group(index: int, group: String) -> void:
	choose(-1,group,index)
func choose(skin_id: int, group: String, choice: int) -> void:
	if updating: return
	if editor.app.playing or editor.app.exporting or editor.app.has_project.pid > 0: refresh(); return
	var actor: RefCounted = target()
	if actor == null or actor != last_actor or str(actor.data.id) != target_id or actor.variants == null: close(); return
	var value: Dictionary = actor.data.duplicate(true)
	var selected: Dictionary = actor.variants.current.duplicate(true)
	if skin_id >= 0: selected.skin = skin_id
	if not group.is_empty(): selected.groups[group] = choice
	value[Schema.FIELD] = selected
	var error: String = editor.restore_state(value,true)
	if not error.is_empty(): editor.app.message(error)
	refresh()
func refresh() -> void:
	var actor: RefCounted = target()
	if not eligible(actor): return
	updating = true
	if is_instance_valid(skin): skin.select(actor.variants.current.skin)
	for group in choices: choices[group].select(actor.variants.current.groups[group])
	updating = false
func _exit_tree() -> void:
	close()
