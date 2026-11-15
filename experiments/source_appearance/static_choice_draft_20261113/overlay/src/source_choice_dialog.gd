extends Node
## Draft: static choices for a new import. The conversion worker rechecks all data.
var dialog: ConfirmationDialog
var box: VBoxContainer
var source_path := ""
var members: OptionButton
var python_path := ""
var pid := -1
var generation := 0
var status_path := ""
var selected_member := ""
var inspection_started := 0
var catalogue := {}
var enabled: CheckBox
var note: Label
var fields: VBoxContainer
var skin: OptionButton
var groups: Array = []

func attach(owner_dialog: ConfirmationDialog, owner_box: VBoxContainer, path: String, choices: OptionButton, python_executable: String) -> void:
	dialog = owner_dialog; box = owner_box; source_path = path; members = choices; python_path = python_executable
	enabled = CheckBox.new(); enabled.text = "Choose skin and parts for this import"; enabled.disabled = true; box.add_child(enabled)
	note = Label.new(); note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; box.add_child(note)
	fields = VBoxContainer.new(); fields.visible = false; box.add_child(fields)
	enabled.toggled.connect(func(on: bool): fields.visible = on; update_validity())
	members.item_selected.connect(func(_index: int): inspect_member())
	dialog.tree_exiting.connect(invalidate)
	inspect_member()

func invalidate() -> void:
	generation += 1
	if pid > 0 and OS.is_process_running(pid): OS.kill(pid)
	pid = -1

func _exit_tree() -> void:
	invalidate()

func inspect_member() -> void:
	invalidate()
	catalogue = {}; groups.clear(); skin = null
	enabled.set_pressed_no_signal(false); enabled.disabled = true; fields.visible = false
	for child in fields.get_children(): child.queue_free()
	dialog.get_ok_button().disabled = false
	selected_member = members.get_item_text(members.selected)
	if not selected_member.to_lower().ends_with(".mdl"):
		note.text = "Maps use the default appearance of their included props."; return
	if source_path.get_extension().to_lower() not in ["mdl", "gma", "vpk"]:
		note.text = "Default preparation is available. Extra appearance choices are not available for this container yet."; return
	note.text = "Reading available skins and parts… Default preparation is available."
	var root := ProjectSettings.globalize_path("res://output/compatibility")
	if DirAccess.make_dir_recursive_absolute(root) != OK:
		unavailable("Cannot create the metadata result folder."); return
	status_path = root.path_join("appearance-" + str(Time.get_ticks_usec()) + "-" + str(generation) + ".json")
	var args := PackedStringArray([ProjectSettings.globalize_path("res://tools/prepare_source.py"), source_path, "--appearance-catalogue", "--member", selected_member, "--status-file", status_path])
	pid = OS.create_process(python_path, args, false)
	inspection_started = Time.get_ticks_msec()
	if pid < 0: unavailable("Cannot start metadata inspection. Check the Python path.")

func unavailable(reason: String) -> void:
	catalogue = {}; enabled.disabled = true; enabled.set_pressed_no_signal(false); fields.visible = false
	note.text = "Default preparation is available. " + reason.left(500)
	dialog.get_ok_button().disabled = false

func _process(_delta: float) -> void:
	if pid <= 0: return
	if OS.is_process_running(pid):
		if Time.get_ticks_msec() - inspection_started > 30000:
			invalidate(); unavailable("Appearance inspection timed out. The default import path remains available.")
		return
	pid = -1
	if not is_instance_valid(dialog) or not dialog.visible: return
	var file := FileAccess.open(status_path, FileAccess.READ)
	if file == null or file.get_length() > 300 * 1024:
		if file: file.close()
		unavailable("No bounded appearance catalogue was returned."); return
	var value = JSON.parse_string(file.get_as_text()); file.close()
	if not value is Dictionary or not value.get("ok", false):
		unavailable(str(value.get("error", "Metadata inspection failed.")) if value is Dictionary else "Metadata inspection failed."); return
	var data = value.get("catalogue")
	if not valid_catalogue(data): unavailable("The appearance catalogue is not valid for this selection."); return
	catalogue = data
	skin = OptionButton.new()
	for row in catalogue.skins:
		skin.add_item("Skin " + str(row.index) + (" (default)" if row.index == 0 else ""))
		skin.set_item_metadata(skin.item_count - 1, int(row.index))
	fields.add_child(skin); skin.item_selected.connect(func(_i: int): update_validity())
	for group in catalogue.bodygroups:
		var label := Label.new(); label.text = display_name(group.display_name); fields.add_child(label)
		var option := OptionButton.new(); option.tooltip_text = "Native group " + str(group.index) + ": " + str(group.name)
		for choice in group.choices:
			option.add_item(display_name(choice.display_name) + (" (hidden)" if choice.true_blank else ""))
			option.set_item_metadata(option.item_count - 1, int(choice.index))
		fields.add_child(option); groups.append({"index": int(group.index), "option": option, "choices": group.choices})
		option.item_selected.connect(func(_i: int): update_validity())
	enabled.disabled = false
	note.text = "Defaults stay unchanged unless you choose another skin or part. These choices are fixed for the newly prepared model. Textures remain approximate."
	update_validity()

func display_name(value: Variant) -> String:
	return str(value).replace("\n", " ").replace("\r", " ").replace("\t", " ").left(96)

func sha(value: Variant) -> bool:
	if not value is String or value.length() != 64: return false
	for c in value:
		if c not in "0123456789abcdef": return false
	return true

func valid_catalogue(data: Variant) -> bool:
	if not data is Dictionary or data.get("format") != "studio_source_mdl_choices_1" or data.get("selected_member") != selected_member: return false
	if not sha(data.get("original_source_sha256")) or not sha(data.get("native_mdl_sha256")) or not sha(data.get("catalogue_sha256")): return false
	if not data.get("skins") is Array or data.skins.is_empty() or data.skins.size() > 256: return false
	if not data.get("bodygroups") is Array or data.bodygroups.is_empty() or data.bodygroups.size() > 256: return false
	for i in range(data.skins.size()):
		if not data.skins[i] is Dictionary or data.skins[i].get("index") != i: return false
	for i in range(data.bodygroups.size()):
		var group = data.bodygroups[i]
		if not group is Dictionary or group.get("index") != i or not group.get("choices") is Array or group.choices.is_empty() or group.choices.size() > 256: return false
		if not group.get("name") is String or not group.get("display_name") is String: return false
		for j in range(group.choices.size()):
			var choice = group.choices[j]
			if not choice is Dictionary or choice.get("index") != j or not choice.get("true_blank") is bool or not choice.get("display_name") is String: return false
	return true

func selection_valid() -> bool:
	if not enabled.button_pressed: return true
	if catalogue.is_empty() or not is_instance_valid(skin): return false
	for group in groups:
		if not group.choices[group.option.selected].true_blank: return true
	return false

func update_validity() -> void:
	dialog.get_ok_button().disabled = not selection_valid()
	if enabled.button_pressed and not selection_valid(): note.text = "Keep at least one visible part before preparing the model."
	elif enabled.button_pressed: note.text = "Only the selected static appearance will be exported. It does not change models already in your scene."

func request() -> Dictionary:
	if not enabled.button_pressed or not selection_valid(): return {}
	var bodygroups := {}; var changed: bool = skin.get_selected_metadata() != 0
	for group in groups:
		var value: int = group.option.get_selected_metadata()
		bodygroups[str(int(group.index))] = value; changed = changed or value != 0
	# Untouched/default controls preserve the original worker route exactly.
	if not changed: return {}
	return {"format": "studio_source_appearance_request_1", "source_sha256": catalogue.original_source_sha256,
		"native_mdl_sha256": catalogue.native_mdl_sha256, "skin": int(skin.get_selected_metadata()), "bodygroups": bodygroups}
