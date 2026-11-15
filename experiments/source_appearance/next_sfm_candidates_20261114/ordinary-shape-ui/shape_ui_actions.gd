extends RefCounted
# DRAFT: source inspection only; not parsed or executed under current GPU lease.
# These helpers drive attached ordinary controls. They never set a mesh channel.

static func open_shapes(app) -> String:
	if app.pose_editor.shape_button.disabled or not app.pose_editor.shape_button.visible:
		return "The ordinary Shapes / expressions button is unavailable."
	app.pose_editor.shape_button.pressed.emit()
	return ""

static func filter_area(editor, area: String) -> String:
	for index in range(editor.area_filter.item_count):
		if editor.area_filter.get_item_text(index) == area:
			editor.area_filter.select(index)
			editor.area_filter.item_selected.emit(index)
			return ""
	return "Expected ordinary area filter is absent: " + area

static func choose_exact(editor, source_node: int, target_index: int, native_name: String) -> String:
	var declared := false
	for row in editor.rows():
		if int(row.node) == source_node and target_index >= 0 and target_index < row.names.size():
			declared = str(row.names[target_index]) == native_name
	if not declared:
		return "Imported source-node/target/name identity differs from the bound GLB."
	editor.search.text = native_name
	editor.search.text_changed.emit(native_name)
	var matching: Array[int] = []
	for index in range(editor.shapes.item_count):
		if editor.result_nodes[index] == source_node and int(editor.shapes.get_item_metadata(index)) == target_index:
			matching.append(index)
	if matching.size() != 1:
		return "The ordinary list did not expose exactly one expected source binding."
	editor.shapes.select(matching[0])
	editor.shapes.item_selected.emit(matching[0])
	return ""

static func apply_amount(editor, value: float) -> String:
	if not is_finite(value) or not editor.amount.editable:
		return "Ordinary Amount control is unavailable or the amount is invalid."
	editor.amount.value = value
	if editor.apply_button.disabled:
		return "Apply is disabled; treat unchanged amount as a separate no-op case."
	editor.apply_button.pressed.emit()
	return ""

static func reset_selected(editor) -> String:
	if editor.reset_button.disabled:
		return "Use base amount here is unavailable."
	editor.reset_button.pressed.emit()
	return ""

static func reset_tracked_at_frame(editor) -> String:
	if editor.reset_all.disabled:
		return "Use all base amounts here is unavailable."
	editor.reset_all.pressed.emit()
	return ""

static func imported_defaults_off(app) -> String:
	if not app.pose_editor.source_shape.visible or app.pose_editor.source_shape.disabled:
		return "Advanced imported-default setting is unavailable."
	app.pose_editor.source_shape.button_pressed = false
	return ""
