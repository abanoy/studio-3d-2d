extends RefCounted
## Opt-in actual imported-joint checks; the native Source solver stays inactive.
const Bindings = preload("res://src/source_bone_bindings.gd")
const World = preload("res://src/world_document.gd")
var app
var record: Callable

func normal(value: Variant) -> Variant:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func snapshot(target: RefCounted) -> PackedByteArray:
	var poses: Array = []
	for id in target.order:
		var bone: Dictionary = target.bones[id]
		poses.append([id, bone.skeleton.get_bone_pose(bone.index)])
	return var_to_bytes([target.data, target.authored_keys(), poses, app.current_world(), app.history, app.redo_history])

func observe(expected: Dictionary, target: RefCounted, parameters: Dictionary, phase: String) -> void:
	var before := snapshot(target)
	var resolution := Bindings.resolve(target)
	var native: Dictionary = parameters.get("native_parameters", {})
	var count := int(expected.count)
	var crosswalk: Dictionary = native.get("source_export_crosswalk", {})
	var identity: bool = target.data.metadata.get("native_parameters", {}) == parameters
	if count > 0:
		identity = identity and crosswalk.get("proof_sha256") == expected.proof_sha256 and crosswalk.get("glb_sha256") == target.data.sha256 and crosswalk.get("original_source_sha256") == expected.source_sha256
	else:
		identity = identity and not native.has("source_export_crosswalk")
	record.call(identity, "source_binding." + phase + ".report_identity")
	var bound: bool = resolution.status == "none" and resolution.bindings.is_empty() if count == 0 else resolution.status == "bound_inactive" and resolution.bindings.size() == count and resolution.by_native.size() == count and resolution.by_gltf_node.size() == count and resolution.rule_owner_ids.size() == 49 and resolution.rule_owner_nodes.size() == 49 and Bindings.current(target, resolution)
	record.call(bound, "source_binding." + phase + ".runtime_bindings")
	if not bound: print("SOURCE_BINDING_DIAGNOSTIC " + resolution.status + " " + resolution.reason)
	record.call(snapshot(target) == before, "source_binding." + phase + ".no_mutation")
	var physics = app.physics_editor
	record.call(not physics.is_running() and physics.pending.is_empty() and physics.import_starts.is_empty() and not physics.recording.active and not physics.hair_toggle.button_pressed and not physics.toggle.button_pressed and target.live_pose == null and target.live_world_transform == null, "source_binding." + phase + ".no_simulation")

func settled() -> void:
	for _i in range(4): await app.get_tree().process_frame
	await RenderingServer.frame_post_draw

func helper(id: String, protected_state: Callable) -> void:
	app.world_selection.select_entity(id); app.set_advanced(false); await settled()
	var target: RefCounted = app.renderer.world_runtime.instance(id)
	var editor = app.physics_editor.helper_editor
	var before := snapshot(target)
	var protected_before: Variant = protected_state.call()
	var source_sha := FileAccess.get_sha256(target.data.source)
	var available: bool = editor != null and not editor.button.disabled and not is_instance_valid(editor.window)
	record.call(available, "native_helper.available")
	if not available: return
	editor.button.pressed.emit()
	var until := Time.get_ticks_msec() + 120000
	while is_instance_valid(editor.window) and (editor.pid > 0 or not editor.preview_ready) and Time.get_ticks_msec() < until:
		await app.get_tree().process_frame
	await settled()
	var ready: bool = is_instance_valid(editor.window) and editor.pid <= 0 and editor.preview_ready and editor.native_current and editor.native_joint_nodes.size() == 49 and editor.native_parent_nodes.size() == 69
	record.call(ready, "native_helper.native_current")
	if not ready:
		editor.close(); await settled(); return
	var region: Dictionary = editor.preview.get("region", {})
	var preferred: bool = editor.native_existing_chain(region, editor.native_joint_nodes, editor.native_parent_nodes)
	record.call(preferred, "native_helper.suggested")
	record.call(editor.preview.get("mode") == "existing_joints" and editor.existing_toggle.button_pressed and not editor.apply_button.disabled and editor.apply_button.text == "Enable these existing joints" and editor.info.text.begins_with("Imported hair joints. "), "native_helper.existing_mode")
	record.call(snapshot(target) == before and FileAccess.get_sha256(target.data.source) == source_sha, "native_helper.weights_unchanged")
	editor.close(); await settled()
	record.call(not is_instance_valid(editor.window) and editor.pid <= 0 and editor.preview.is_empty() and not editor.pending_preview_active() and not editor.native_current and editor.native_joint_nodes.is_empty(), "native_helper.cancelled")
	record.call(snapshot(target) == before and protected_state.call() == protected_before, "native_helper.protected_state")
	var physics = app.physics_editor
	record.call(not physics.is_running() and not physics.hair_toggle.button_pressed and not physics.toggle.button_pressed and target.live_pose == null and target.live_world_transform == null, "native_helper.no_simulation")
