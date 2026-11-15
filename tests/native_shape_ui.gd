extends RefCounted
## Opt-in native-derived shape controls. Author only through attached ordinary UI.
const Shape = preload("res://src/source_shape.gd")
var app
var record: Callable

func normal(value: Variant) -> Variant: return JSON.parse_string(JSON.stringify(value, "", true, true))

func settled() -> void:
	for _i in range(4): await app.get_tree().process_frame
	await RenderingServer.frame_post_draw

func actor(id: String) -> RefCounted: return app.renderer.world_runtime.instance(id)

func weights(id: String) -> Dictionary:
	var result := {}
	for row in actor(id).root.get_meta(Shape.META).rows:
		var values: Array = []
		for index in range(row.names.size()): values.append(row.mesh.get_blend_shape_value(index))
		result[str(row.node)] = values
	return result

func value(id: String, control: Dictionary) -> float:
	return float(weights(id).get(str(int(control.node)), [])[int(control.index)])

func choose(id: String, control: Dictionary) -> bool:
	app.world_selection.select_entity(id)
	var editor = app.pose_editor.animated_shapes
	var declared := false
	for row in editor.rows():
		if int(row.node) == int(control.node) and row.names.size() == int(control.target_count) and int(control.index) < row.names.size():
			declared = str(row.names[int(control.index)]) == str(control.name)
	if not declared: return false
	var area := -1
	var area_label: String = "Other / unassigned" if control.area == "Other" else str(control.area)
	for index in range(editor.area_filter.item_count):
		if editor.area_filter.get_item_text(index) == area_label: area = index
	if area < 0: return false
	editor.area_filter.select(area); editor.area_filter.item_selected.emit(area)
	editor.search.text = str(control.name); editor.search.text_changed.emit(str(control.name))
	var found: Array[int] = []
	for index in range(editor.shapes.item_count):
		if int(editor.result_nodes[index]) == int(control.node) and int(editor.shapes.get_item_metadata(index)) == int(control.index): found.append(index)
	if found.size() != 1: return false
	editor.shapes.select(found[0]); editor.shapes.item_selected.emit(found[0])
	return true

func apply(id: String, control: Dictionary, frame: int, amount: float) -> bool:
	app.set_frame(frame); await settled()
	if not choose(id, control): return false
	var editor = app.pose_editor.animated_shapes
	editor.amount.value = amount
	if editor.apply_button.disabled: return false
	editor.apply_button.pressed.emit(); await settled()
	return absf(value(id, control) - amount) < .00001

func unchanged_other_weights(before: Dictionary, after: Dictionary, control: Dictionary) -> bool:
	var expected := before.duplicate(true)
	expected[str(int(control.node))][int(control.index)] = after[str(int(control.node))][int(control.index)]
	return normal(expected) == normal(after)

func geometry(id: String, control: Dictionary) -> Dictionary:
	# Compare the engine's baked mix against an independent sum of its immutable
	# imported base/target arrays. This does not call the application's CPU cache.
	var maximum_error := 0.0; var nonzero := 0
	for row in actor(id).root.get_meta(Shape.META).rows:
		var mesh: ArrayMesh = row.mesh.mesh
		var baked: ArrayMesh = row.mesh.bake_mesh_from_current_blend_shape_mix()
		if baked == null or baked.get_surface_count() != mesh.get_surface_count(): return {"error": "Missing baked mix"}
		for surface in range(mesh.get_surface_count()):
			var base: PackedVector3Array = mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var actual: PackedVector3Array = baked.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var targets: Array = mesh.surface_get_blend_shape_arrays(surface)
			if base.size() != actual.size(): return {"error": "Baked vertex count differs"}
			var expected := base.duplicate()
			for index in range(row.names.size()):
				var amount: float = row.mesh.get_blend_shape_value(index)
				var selected: bool = int(row.node) == int(control.node) and index == int(control.index)
				if amount == 0.0 and not selected: continue
				var target: PackedVector3Array = targets[index][Mesh.ARRAY_VERTEX]
				if target.size() != base.size(): return {"error": "Target vertex count differs"}
				for vertex in range(base.size()):
					var delta: Vector3 = target[vertex] - base[vertex] if mesh.blend_shape_mode == Mesh.BLEND_SHAPE_MODE_NORMALIZED else target[vertex]
					if selected and delta.length_squared() > .000000000000000001: nonzero += 1
					expected[vertex] += amount * delta
			for vertex in range(base.size()): maximum_error = maxf(maximum_error, actual[vertex].distance_to(expected[vertex]))
	return {"maximum_error": maximum_error, "nonzero_delta_vertices": nonzero}

func capture(frame: int, path: String) -> Dictionary:
	app.set_frame(frame); await settled()
	var image: Image = await app.renderer.capture(app.keys, app.layers, frame, true)
	if image == null or image.is_empty() or image.get_size() != Vector2i(1920, 1080): return {}
	image.convert(Image.FORMAT_RGBA8)
	if image.save_png(path) != OK: return {}
	return {"path": path, "png_sha256": FileAccess.get_sha256(path)}

func image_matches(path: String, reference: String) -> bool:
	var actual := Image.load_from_file(path); var expected := Image.load_from_file(reference)
	if actual == null or expected == null or actual.get_size() != expected.get_size(): return false
	actual.convert(Image.FORMAT_RGBA8); expected.convert(Image.FORMAT_RGBA8)
	return actual.get_data() == expected.get_data()

func writer(controls: Array, id: String, protected_state: Callable, parameters: Dictionary, folder: String) -> Dictionary:
	app.world_selection.select_entity(id); app.set_advanced(false); await settled()
	var button = app.pose_editor.shape_button
	var available: bool = button.visible and not button.disabled
	if available: button.pressed.emit(); await settled()
	if not record.call(available and app.pose_editor.shape_window.visible, "available"): return {}
	var baseline: Variant = protected_state.call(); var original_body: Array = actor(id).authored_keys().duplicate(true); var bone_ids: Array = actor(id).order.duplicate()
	app.pose_editor.auto_key.button_pressed = true
	for index in range(app.pose_editor.interpolation.item_count):
		if app.pose_editor.interpolation.get_item_text(index) == "linear": app.pose_editor.interpolation.select(index)
	var catalogue_ok := true; var observations := []
	for index in range(controls.size()):
		var control: Dictionary = controls[index]; var prefix := "target_" + str(index) + "."
		var bound := choose(id, control); catalogue_ok = catalogue_ok and bound
		if not record.call(bound, prefix + "binding"): return {}
		app.set_frame(12); await settled()
		var unedited_image: Image = await app.renderer.capture(app.keys, app.layers, 12, true)
		app.set_frame(0); await settled(); var initial_weights := weights(id)
		var history: int = app.history.size()
		var first := await apply(id, control, 0, .2)
		record.call(first and app.history.size() == history + 1 and unchanged_other_weights(initial_weights, weights(id), control), prefix + "key_0")
		var before_second: Variant = normal(actor(id).data); history = app.history.size()
		var second := await apply(id, control, 24, .8)
		record.call(second and app.history.size() == history + 1 and absf(float(actor(id).sample_shapes(0)[str(int(control.node))][str(int(control.index))]) - .2) < .00001, prefix + "key_24")
		var after_second: Variant = normal(actor(id).data)
		app.set_frame(12); await settled()
		record.call(absf(value(id, control) - .5) < .00001 and absf(float(actor(id).sample_shapes(12)[str(int(control.node))][str(int(control.index))]) - .5) < .00001, prefix + "middle")
		var observed := geometry(id, control); observations.append(observed)
		var edited_image: Image = await app.renderer.capture(app.keys, app.layers, 12, true)
		record.call(not observed.has("error") and observed.maximum_error < .00001 and observed.nonzero_delta_vertices > 0 and unedited_image != null and edited_image != null and unedited_image.get_data() != edited_image.get_data(), prefix + "geometry")
		app.undo(); await settled(); record.call(normal(actor(id).data) == before_second and app.history.size() == history, prefix + "undo")
		app.redo(); await settled(); record.call(normal(actor(id).data) == after_second and app.history.size() == history + 1 and absf(value(id, control) - .5) < .00001, prefix + "redo")
		choose(id, control); var editor = app.pose_editor.animated_shapes; var before_no_op: Variant = normal(actor(id).data); history = app.history.size()
		editor.amount.value = editor.amount.value
		record.call(editor.apply_button.disabled and normal(actor(id).data) == before_no_op and app.history.size() == history, prefix + "no_op")
		editor.reset_button.pressed.emit(); await settled(); var reset_data: Variant = normal(actor(id).data)
		record.call(absf(value(id, control)) < .00001 and app.history.size() == history + 1, prefix + "reset")
		app.undo(); await settled(); record.call(normal(actor(id).data) == after_second and absf(value(id, control) - .5) < .00001, prefix + "reset_undo")
		app.redo(); await settled(); record.call(normal(actor(id).data) == reset_data and absf(value(id, control)) < .00001, prefix + "reset_redo")
		app.undo(); await settled(); record.call(normal(actor(id).data) == after_second and app.history.size() == history and absf(value(id, control) - .5) < .00001, prefix + "reset_final_undo")
	record.call(catalogue_ok, "catalogue")
	app.set_advanced(true); app.world_selection.select_entity(id); await settled()
	var before_off: Variant = normal(actor(id).data); var shape_keys: Variant = normal(actor(id).authored_shape_keys()); var before_weights := weights(id); var off_history: int = app.history.size()
	var toggle = app.pose_editor.source_shape; var starts_on: bool = Shape.enabled(actor(id).data) and toggle.button_pressed and toggle.visible and not toggle.disabled
	if starts_on: toggle.button_pressed = false
	await settled(); var after_off: Variant = normal(actor(id).data)
	record.call(starts_on and not Shape.enabled(actor(id).data) and app.history.size() == off_history + 1 and weights(id) == before_weights and normal(actor(id).authored_shape_keys()) == shape_keys, "defaults_off")
	app.undo(); await settled(); record.call(normal(actor(id).data) == before_off and weights(id) == before_weights, "off_undo")
	app.redo(); await settled(); record.call(normal(actor(id).data) == after_off and weights(id) == before_weights, "off_redo")
	record.call(protected_state.call() == baseline and actor(id).authored_keys() == original_body and actor(id).order == bone_ids and actor(id).data.metadata.get("native_parameters", {}) == parameters, "protected_state")
	app.set_advanced(false); app.pose_editor.shape_window.hide(); await settled()
	var middle := await capture(12, folder.path_join("writer-shape-12.png"))
	return {"controls": controls, "shape_keys": normal(actor(id).authored_shape_keys()), "shape_base": normal(actor(id).data.get("shape_base", {})), "source_shape": normal(Shape.setting(actor(id).data)), "middle": middle, "geometry": observations}

func reader(expected: Dictionary, id: String, protected_ok: bool, folder: String, mode: String) -> void:
	app.world_selection.select_entity(id); app.set_advanced(false); await settled()
	app.pose_editor.shape_button.pressed.emit(); await settled()
	var catalogue_ok: bool = app.pose_editor.shape_window.visible
	for index in range(expected.controls.size()):
		var control: Dictionary = expected.controls[index]
		var bound := choose(id, control); catalogue_ok = catalogue_ok and bound
		record.call(bound, "target_" + str(index) + ".binding")
		app.set_frame(12); await settled()
		record.call(bound and absf(value(id, control) - .5) < .00001, "target_" + str(index) + ".middle")
	record.call(catalogue_ok, "catalogue")
	record.call(normal(actor(id).authored_shape_keys()) == expected.shape_keys and normal(actor(id).data.get("shape_base", {})) == expected.shape_base, "authored_values")
	record.call(not Shape.enabled(actor(id).data) and normal(Shape.setting(actor(id).data)) == expected.source_shape, "defaults_off")
	record.call(protected_ok and app.history.is_empty() and app.redo_history.is_empty() and not app.dirty, "protected_state")
	app.pose_editor.shape_window.hide(); var middle := await capture(12, folder.path_join(mode + "-shape-12.png"))
	record.call(not middle.is_empty() and not expected.middle.is_empty() and FileAccess.get_sha256(expected.middle.path) == expected.middle.png_sha256 and image_matches(middle.path, expected.middle.path), "middle_pixels")
