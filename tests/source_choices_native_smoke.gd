extends SceneTree
## Actual dialog -> converter -> ordinary adoption; run only on a private desktop.
const Choice = preload("res://src/source_choice_dialog.gd")
const World = preload("res://src/world_document.gd")
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
const Audio = preload("res://src/audio_track.gd")
const ShapeUI = preload("res://tests/native_shape_ui.gd")
var app
var job: Dictionary
var checks := 0
var failures := 0
var completion: Dictionary = {}
var rows: Array = []
var read_modes: Array = []
var movie := ""
var job_path := ""
var named_ledger: Dictionary = {}
var named_prefix := ""

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> bool:
	checks += 1; print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures += 1
	return ok

func normal(value: Variant) -> Variant: return JSON.parse_string(JSON.stringify(value, "", true, true))

func named_check(ok: bool, name: String) -> bool:
	var key := named_prefix + "/" + name
	if named_ledger.has(key): ok = false
	named_ledger[key] = ok; print(("PASS " if ok else "FAIL ") + "named " + key)
	if not ok: failures += 1
	return ok

func case_named(label: String) -> Dictionary:
	var result := {}
	for key in named_ledger:
		if str(key).begins_with(label + "/"): result[key] = named_ledger[key]
	return result

func authored_body(id: String) -> Dictionary:
	var target := actor(id)
	return normal({"pose": target.data.get("pose", {}), "keys": target.authored_keys(), "bones": target.order})

func jiggle_observation(expected: Dictionary, id: String, parameters: Dictionary, phase: String) -> void:
	app.world_selection.select_entity(id); app.physics_editor.sync()
	var target := actor(id); var native: Dictionary = parameters.get("native_parameters", {})
	var rules: int = int(expected.rules); var metadata: Variant = native.get("source_jiggle")
	var identity: bool = target.data.metadata.get("native_parameters", {}) == parameters and parameters.get("source_sha256", "") == expected.source_sha256
	if rules > 0:
		identity = identity and metadata is Dictionary and metadata.get("original_source_sha256") == expected.source_sha256 and metadata.get("native_mdl_sha256") == expected.source_sha256
	named_check(identity, "jiggle." + phase + ".report_identity")
	var inert: bool = not native.has("source_jiggle") if rules == 0 else metadata is Dictionary
	if rules > 0 and inert:
		inert = metadata.get("format") == "studio_source_jiggle_metadata_1" and metadata.get("status") == "retained_inert" and metadata.get("runtime_support") == "not_implemented" and metadata.get("binding_status") == "unattempted" and metadata.get("applied") == false and metadata.get("full_native_rule_layout_verified") == false and int(metadata.get("declared_jiggle_rule_count", -1)) == rules and metadata.get("rules") is Array
		if inert:
			inert = metadata.rules.size() == rules
			for row in metadata.rules:
				if not row is Dictionary or row.get("applied") != false or row.get("binding_status") != "unattempted" or int(row.get("native_procedure_type", -1)) != 5: inert = false
	named_check(inert, "jiggle." + phase + ".inactive_rules")
	var physics = app.physics_editor
	named_check(not physics.is_running() and physics.pending.is_empty() and physics.import_starts.is_empty() and not physics.recording.active and not physics.hair_toggle.button_pressed and not physics.toggle.button_pressed and target.live_pose == null and target.live_world_transform == null, "jiggle." + phase + ".no_simulation")
	named_check(authored_body(id) == expected.authored_body, "jiggle." + phase + ".authored_body")

func settled() -> void:
	for _i in range(4): await process_frame
	await RenderingServer.frame_post_draw

func write_json(path: String, value: Variant) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null: check(false, "write fresh native test evidence: " + path); return
	f.store_string(JSON.stringify(value, "  ", true, true)); f.flush(); f.close()

func actor(id: String) -> RefCounted:
	return app.renderer.world_runtime.instance(id) if app.renderer.world_runtime else null

func idle() -> bool:
	return app.has_project.pid <= 0 and not app.has_project.project_loader.busy() and not app.has_project.snapshot_writer.busy() and app.source_import.pid <= 0 and not app.exporting

func operation_done(action: String, success: bool) -> void: completion = {"action": action, "success": success}

func operation(action: String, invoke: Callable) -> bool:
	completion = {}; app.has_project.operation_finished.connect(operation_done); invoke.call()
	var until := Time.get_ticks_msec() + 180000
	while (completion.is_empty() or not idle()) and Time.get_ticks_msec() < until: await process_frame
	app.has_project.operation_finished.disconnect(operation_done); await settled()
	return check(completion.get("action") == action and completion.get("success", false) and idle(), "normal HAS " + action + " succeeds and drains snapshot/loader/packer state")

func portable_peer(id: String) -> Dictionary:
	for item in World.portable(app.current_world()).objects:
		if item.id == id: return item
	return {}

func protected_state(peer: String) -> Dictionary:
	var cel = Drawing.cel_at(app.layers[1], 0)
	return normal({"peer": portable_peer(peer), "keys": app.keys, "video": app.video,
		"paint": Storage.image_hash(Drawing.image(cel)) if cel != null else "",
		"audio": Audio.metadata(app.audio_document()), "pcm": Storage.RasterReader.digest_bytes(app.audio_mix.get("pcm", PackedByteArray()))})

func dismiss_notes() -> void:
	for child in app.get_children():
		if child is AcceptDialog and not child is ConfirmationDialog and child.title in ["Source import warnings", "Imported with limitations"]:
			child.hide(); child.queue_free()
	await settled()

func select_native(option: OptionButton, value: int, label: String) -> bool:
	for i in range(option.item_count):
		if int(option.get_item_metadata(i)) == value:
			option.select(i); option.item_selected.emit(i); return true
	return check(false, label + " native selection is present: " + str(value))

func source_dialog(path: String, placement: Dictionary) -> Dictionary:
	app.source_import.start(path, true, 0, placement)
	for child in app.get_children():
		if child is ConfirmationDialog and child.title == "Import Source model" and not child.is_queued_for_deletion():
			for controller in child.get_children():
				if controller.get_script() == Choice: return {"dialog": child, "choice": controller}
	return {}

func picture(path: String, frame: int) -> Dictionary:
	app.set_frame(frame); await settled()
	var image: Image = await app.renderer.capture(app.keys, app.layers, frame, true)
	if not check(image != null and not image.is_empty() and image.get_size() == Vector2i(1920, 1080), "derived reference capture has the authored full-HD dimensions"): return {}
	image.convert(Image.FORMAT_RGBA8)
	if not check(image.save_png(path) == OK, "derived reference pixels are retained privately"): return {}
	return {"path": path, "pixel_sha256": Storage.RasterReader.digest_bytes(image.get_data()), "width": image.get_width(), "height": image.get_height()}

func bone_transform(value: Transform3D) -> Array:
	return [value.basis.x.x, value.basis.x.y, value.basis.x.z, value.basis.y.x, value.basis.y.y, value.basis.y.z, value.basis.z.x, value.basis.z.y, value.basis.z.z, value.origin.x, value.origin.y, value.origin.z]

func active_mesh_names(path: String) -> Array:
	# Native-derived GLB names precede Godot's Node-name sanitization. Only names
	# referenced by an active scene mesh count; skeleton/bone names do not count.
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null or f.get_length() < 20: return []
	var header := f.get_buffer(12)
	if header.decode_u32(0) != 0x46546c67 or header.decode_u32(4) != 2: f.close(); return []
	var length := f.get_32(); var kind := f.get_32()
	if kind != 0x4e4f534a or length > 16 * 1024 * 1024 or length + 20 > f.get_length(): f.close(); return []
	var data = JSON.parse_string(f.get_buffer(length).get_string_from_utf8()); f.close()
	if not data is Dictionary or not data.get("nodes") is Array or not data.get("scenes") is Array: return []
	var scene: int = data.get("scene", 0)
	if scene < 0 or scene >= data.scenes.size(): return []
	var pending: Array = data.scenes[scene].get("nodes", []).duplicate(); var visited := {}; var names: Array = []
	while not pending.is_empty():
		var index := int(pending.pop_back())
		if index < 0 or index >= data.nodes.size() or visited.has(index): continue
		visited[index] = true; var node: Dictionary = data.nodes[index]
		for child in node.get("children", []): pending.append(child)
		if not node.has("mesh"): continue
		for name in [str(node.get("name", "")), str(data.get("meshes", [])[int(node.mesh)].get("name", ""))]:
			if not name.is_empty() and not names.has(name): names.append(name)
	return names

func pose_native(item: Dictionary, id: String, peer: String, parameters: Dictionary) -> bool:
	# World Undo/Redo rebuilds actors and may leave selection empty. Re-enter the
	# ordinary posing context before looking up the newly rebuilt tree bindings.
	app.world_selection.select_entity(id); await settled()
	var target := actor(id); var native: Dictionary = parameters.get("native_parameters", {}); var index: int = item.pose_native_bone_index
	if not check(index >= 0 and index < native.get("bones", []).size(), item.name + " admitted native posing index is present in the actual report"): return false
	var name: String = native.bones[index].name; var matches: Array = []
	for binding in target.order:
		if str(target.bones[binding].name) == name: matches.append(str(binding))
	var editor = app.pose_editor
	if not check(matches.size() == 1 and editor.tree_items.has(matches[0]), item.name + " native bone index resolves once in the ordinary posing tree"): return false
	var binding: String = matches[0]; var before: Dictionary = normal(target.data); var before_protected := protected_state(peer)
	var transform_before := bone_transform(target.bone_transform(binding)); var history: int = app.history.size(); var source_sha: String = target.data.sha256
	app.set_advanced(true); app.set_frame(0); editor.tree_items[binding].select(0); editor.tree.item_selected.emit(); editor.operation.select(0); editor.snap.button_pressed = false; editor.auto_key.button_pressed = true
	for lock in editor.locks: lock.button_pressed = false
	editor.refresh_values(); editor.fields[0].value = 20.0; editor.apply_numeric(); await settled(); target = actor(id)
	if not check(target != null and app.history.size() == history + 1 and target.authored_keys().any(func(key): return int(key.frame) == 0 and key.pose.has(binding)), item.name + " normal numeric posing authors one native bone key and one Undo"): return false
	var after: Dictionary = normal(target.data); var transformed := bone_transform(target.bone_transform(binding))
	check(transformed != transform_before, item.name + " admitted native bone actually moves through normal numeric posing")
	check(protected_state(peer) == before_protected, item.name + " native posing preserves peer, drawing, sound and shot keys")
	check(target.data.metadata.native_parameters == parameters and FileAccess.get_sha256(target.data.source) == source_sha, item.name + " posing preserves the actual report and prepared geometry")
	app.undo(); await settled(); target = actor(id)
	check(target != null and normal(target.data) == before and app.history.size() == history, item.name + " normal pose Undo restores exact pre-pose data")
	app.redo(); await settled(); target = actor(id)
	return check(target != null and normal(target.data) == after and bone_transform(target.bone_transform(binding)) == transformed and app.history.size() == history + 1, item.name + " normal pose Redo restores the admitted native edit")

func writer_case(item: Dictionary) -> Dictionary:
	var label: String = item.name; var case_folder: String = item.folder; var first_check := checks; var first_failure := failures
	named_prefix = label
	if not check(app.new_project(), label + " ordinary New starts an independent authored scene"): return {}
	var placement: Dictionary = app.import_actions.placement(); placement.physics_on_import = false; placement.review_height = false
	if not check(app.pose_editor.add_model(ProjectSettings.globalize_path("res://examples/tutorials/Practice figure.glb"), 0, placement).is_empty(), label + " retains an independently added Practice figure peer"): return {}
	var peer: String = app.last_import_id
	app.lighting_choice.select(2); app.change_lighting(2)
	app.pose_editor.frame_model(); var camera: Camera3D = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(47, camera.position + Vector3(0.15, 0, 0), camera.quaternion, camera.fov)]
	Drawing.insert(app.layers[1], 0, 48, Drawing.blank(1920, 1080))
	var paint: Image = Drawing.edit_image(Drawing.cel_at(app.layers[1], 0)).image; paint.fill_rect(Rect2i(60, 60, 90, 50), Color.MAGENTA); Drawing.touch(paint); app.changed()
	if not check(app.import_audio(job.tone, 24).is_empty(), label + " ordinary audio import joins the independent drawing and camera keys"): return {}
	await settled()
	var before: Dictionary = protected_state(peer); var before_world: Dictionary = normal(World.portable(app.current_world())); var history: int = app.history.size()
	app.source_import.gmod_root = job.absent_gmod; app.source_import.workshop_root = job.absent_workshop
	app.source_import.extra_roots = []; app.source_import.mount_overrides = item.mount_overrides
	var opened := source_dialog(item.source, placement)
	if not check(not opened.is_empty(), label + " opens the real Source import confirmation and chooser"): return {}
	var ui = opened.choice; var metadata_pid: int = ui.pid; var until := Time.get_ticks_msec() + 45000; var frames := 0
	while ui.pid > 0 and Time.get_ticks_msec() < until: await process_frame; frames += 1
	await settled()
	if not check(ui.pid < 0 and not ui.enabled.disabled and ui.worker_exit == 0 and ui.release_calls == 1 and not ui.worker_map_reserved, label + " real metadata child succeeds and releases its mapped entry"): return {}
	var metadata_worker := {"pid": metadata_pid, "exit": ui.worker_exit, "release_calls": ui.release_calls, "release_result": ui.release_result, "map_reserved": ui.worker_map_reserved}
	var catalogue: Dictionary = ui.catalogue.duplicate(true)
	if not check(ui.selected_member == item.member and catalogue.selected_member == item.member and catalogue.original_source_sha256 == FileAccess.get_sha256(item.source) and catalogue.native_mdl_sha256 == FileAccess.get_sha256(item.source), label + " selected loose MDL and both original checksums bind the widget catalogue"): return {}
	ui.enabled.button_pressed = bool(item.use_override)
	if item.use_override:
		if not select_native(ui.skin, int(item.skin), label + " skin"): return {}
		for key in item.bodygroups:
			var found := false
			for group in ui.groups:
				if int(group.index) == int(key): found = select_native(group.option, int(item.bodygroups[key]), label + " bodypart " + key); break
			if not check(found, label + " resolves requested native bodypart " + key): return {}
	var selected: Dictionary = ui.request().duplicate(true); var old_folder: String = app.source_import.folder
	write_json(case_folder.path_join("catalogue.json"), catalogue); write_json(case_folder.path_join("widget-request.json"), selected)
	if item.expect_all_blank:
		check(not ui.selection_valid() and opened.dialog.get_ok_button().disabled and not opened.dialog.dialog_hide_on_ok, label + " all-blank controls refuse explicit preparation")
		opened.dialog.confirmed.emit(); await settled()
		check(opened.dialog.visible and app.source_import.pid < 0 and app.source_import.folder == old_folder and normal(World.portable(app.current_world())) == before_world and protected_state(peer) == before and app.history.size() == history, label + " direct confirmation cannot bypass refusal, start conversion or mutate the authored scene")
		opened.dialog.canceled.emit(); await settled()
		var refused := {"name": label, "checks": checks - first_check, "failures": failures - first_failure, "all_blank_refused": true, "conversion_started": false, "metadata_pid": metadata_pid, "metadata_frames": frames, "metadata_worker": metadata_worker, "catalogue": case_folder.path_join("catalogue.json"), "passed": failures == first_failure, "completed_phases": ["metadata", "controls", "all_blank_refusal"]}
		write_json(case_folder.path_join("writer-result.json"), refused); return refused
	if not check(ui.selection_valid() and not opened.dialog.get_ok_button().disabled and selected.is_empty() == (not bool(item.appearance_expected)), label + " real controls preserve default omission or produce an explicit changed request"): return {}
	opened.dialog.confirmed.emit()
	if not check(app.source_import.pid > 0 and ui.pid < 0 and not ui.worker_map_reserved, label + " confirmation drains metadata then starts actual local preparation"): return {}
	var converter_pid: int = app.source_import.pid; until = Time.get_ticks_msec() + 630000
	while app.source_import.pid > 0 and Time.get_ticks_msec() < until: await process_frame
	await dismiss_notes()
	if not check(app.source_import.pid < 0 and app.last_import_id != peer and app.current_world().objects.size() == 2, label + " successful conversion is adopted once through ordinary Add model"): return {}
	var id: String = app.last_import_id; var imported: RefCounted = actor(id)
	if not check(imported != null and app.history.size() == history + 1 and app.history[-1].type == "world" and protected_state(peer) == before, label + " adoption is one world Undo and preserves peer, drawing, sound and camera"): return {}
	var bundle: String = app.source_import.folder
	var parameters = JSON.parse_string(FileAccess.get_file_as_string(bundle.path_join("parameters.json")))
	var conversion = JSON.parse_string(FileAccess.get_file_as_string(bundle.path_join("conversion-request.json")))
	if not check(parameters is Dictionary and conversion is Dictionary and imported.data.metadata.get("native_parameters", {}) == parameters and FileAccess.get_sha256(imported.data.source) == FileAccess.get_sha256(bundle.path_join("scene.glb")), label + " adopted actor retains the actual converter report and GLB checksum"): return {}
	var native: Dictionary = parameters.get("native_parameters", {}); var named := {}; var numeric := {}
	var jiggle_expected := {}
	if item.has("expected_jiggle_rules"):
		jiggle_expected = {"rules": int(item.expected_jiggle_rules), "source_sha256": FileAccess.get_sha256(item.source), "authored_body": authored_body(id)}
		jiggle_observation(jiggle_expected, id, parameters, "adoption")
	for group in catalogue.bodygroups:
		var key := str(int(group.index)); var value := int(item.bodygroups.get(key, 0)) if item.use_override else 0
		named[str(group.name)] = value; numeric[key] = value
	check(int(native.get("selected_skin", -1)) == (int(item.skin) if item.use_override else 0) and normal(native.get("selected_bodygroup_indices", {})) == normal(named), label + " retained native report records the requested skin and named bodypart choices")
	check(conversion.has("appearance") == bool(item.appearance_expected) and native.has("appearance_request") == bool(item.appearance_expected), label + " untouched defaults omit the appearance branch in both real worker request and report")
	if item.appearance_expected:
		check(normal(native.get("selected_native_bodygroup_indices", {})) == normal(numeric) and normal(native.appearance_request) == normal(selected) and normal(conversion.appearance) == normal(selected), label + " explicit native integer selection survives widget, worker and renderer report")
	var adopted: Dictionary = normal(World.portable(app.current_world())); app.undo(); await settled()
	check(actor(id) == null and normal(World.portable(app.current_world())) == before_world and app.history.size() == history and protected_state(peer) == before, label + " one Undo removes only the newly converted actor")
	if not jiggle_expected.is_empty(): named_check(actor(id) == null, "jiggle.undo_actor_absent")
	app.redo(); await settled(); imported = actor(id)
	if not check(imported != null and normal(World.portable(app.current_world())) == adopted and protected_state(peer) == before and app.history.size() == history + 1, label + " Redo restores exact native metadata and leaves the original authored work intact"): return {}
	if not jiggle_expected.is_empty(): jiggle_observation(jiggle_expected, id, parameters, "redo")
	var mesh_names := active_mesh_names(imported.data.source); var runtime_mesh_names: Array = []; var morph_names: Array = []
	for mesh in imported.root.find_children("*", "MeshInstance3D", true, false):
		runtime_mesh_names.append(str(mesh.name))
		for i in range(mesh.get_blend_shape_count()):
			var morph_name := str(mesh.mesh.get_blend_shape_name(i))
			if not morph_names.has(morph_name): morph_names.append(morph_name)
	for expected_mesh in item.get("expected_meshes", []):
		check(mesh_names.has(expected_mesh.name) == bool(expected_mesh.present), label + " preserves the admitted native-derived mesh presence: " + str(expected_mesh.name))
	for expected_morph in item.get("expected_morphs", []):
		check(morph_names.has(expected_morph.name) == bool(expected_morph.present), label + " preserves the admitted target presence without controller inference: " + str(expected_morph.name))
	if item.has("pose_native_bone_index"):
		if not await pose_native(item, id, peer, parameters): return {}
		imported = actor(id)
	app.world_selection.select_entity(id); app.pose_editor.frame_model(); camera = app.renderer.camera
	app.keys = [Timeline.key(0, camera.position, camera.quaternion, camera.fov), Timeline.key(47, camera.position + Vector3(0.15, 0, 0), camera.quaternion, camera.fov)]
	var shape_expected := {}
	if job.get("shape_ui", false) and item.has("shape_ui"):
		var shape_ui := ShapeUI.new(); shape_ui.app = app
		shape_ui.record = func(ok: bool, name: String) -> bool: return named_check(ok, "shape_ui." + name)
		shape_expected = await shape_ui.writer(item.shape_ui, id, func(): return protected_state(peer), parameters, case_folder)
		if shape_expected.is_empty(): return {}
		imported = actor(id)
	var pictures := {}; pictures["0"] = await picture(case_folder.path_join("writer-0.png"), 0); pictures["24"] = await picture(case_folder.path_join("writer-24.png"), 24)
	var expected := {"format": "has_source_choices_native_expected_1", "name": label, "object_id": id, "peer_id": peer,
		"portable_world": normal(World.portable(app.current_world())), "protected": protected_state(peer), "parameters": parameters,
		"glb_sha256": imported.data.sha256, "pictures": pictures, "projects": {}, "input_source": item.source, "bundle": bundle}
	if not shape_expected.is_empty(): expected["shape_ui"] = shape_expected
	if not jiggle_expected.is_empty(): expected["jiggle"] = jiggle_expected
	for mode in ["packed", "linked"]:
		if mode == "linked":
			# Normal linked saving deliberately keeps external originals. Reopen the
			# packed file first so its GLB/audio now originate in this isolated cache
			# and the linked save must externalize stable adjacent .assets files.
			if not await operation("unpack", func(): app.has_project.open_file(expected.projects.packed.path)): return {}
			var rebound := actor(id); var rebound_peer := actor(peer)
			var cache: String = ProjectSettings.globalize_path(app.has_project.cache_root).replace("\\", "/").simplify_path().trim_suffix("/").to_lower() + "/"
			var cached := rebound != null and rebound_peer != null
			if cached:
				for source in [str(rebound.data.source), str(rebound_peer.data.source)]:
					cached = cached and ProjectSettings.globalize_path(source).replace("\\", "/").simplify_path().to_lower().begins_with(cache)
			for clip in Audio.clips(app.audio_document()):
				cached = cached and ProjectSettings.globalize_path(clip.source.path).replace("\\", "/").simplify_path().to_lower().begins_with(cache)
			if not check(cached and app.source_import.pid < 0 and app.has_project.origins.is_empty() and app.has_project.path == expected.projects.packed.path and rebound.data.metadata.get("native_parameters", {}) == parameters
				and normal(World.portable(app.current_world())) == expected.portable_world and protected_state(peer) == expected.protected,
				label + " ordinary packed Open rebinds exact world, report, drawing, audio and keys to the isolated writer cache before linked Save"): return {}
			if not jiggle_expected.is_empty(): jiggle_observation(jiggle_expected, id, parameters, "packed_open_cached")
		var path: String = case_folder.path_join(mode + ".has")
		if not await operation("pack", func(): app.has_project.save_file(path, mode)): return {}
		check(app.has_project.path == path and not app.dirty and protected_state(peer) == expected.protected and normal(World.portable(app.current_world())) == expected.portable_world, label + " " + mode + " normal Save preserves the complete authored scene")
		if not jiggle_expected.is_empty(): jiggle_observation(jiggle_expected, id, parameters, mode + "_save")
		expected.projects[mode] = {"path": path, "sha256": FileAccess.get_sha256(path)}
	write_json(case_folder.path_join("expected.json"), expected)
	var result := {"name": label, "checks": checks - first_check, "failures": failures - first_failure, "passed": failures == first_failure,
		"all_blank_refused": false, "conversion_started": true, "converter_pid": converter_pid, "metadata_pid": metadata_pid, "metadata_frames": frames, "metadata_worker": metadata_worker,
		"bundle": bundle, "parameters": bundle.path_join("parameters.json"), "conversion_request": bundle.path_join("conversion-request.json"), "expected": case_folder.path_join("expected.json"),
		"meshes": mesh_names, "runtime_mesh_names": runtime_mesh_names, "morphs": morph_names, "completed_phases": ["metadata", "controls", "conversion", "adoption", "undo", "redo", "reference_0", "reference_24", "packed_save", "packed_open_cached", "linked_save"]}
	result["named_checks"] = case_named(label)
	write_json(case_folder.path_join("writer-result.json"), result); return result

func reader() -> void:
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(job.expected)); var id: String = expected.object_id; var peer: String = expected.peer_id
	check(not FileAccess.file_exists(expected.input_source) and not DirAccess.dir_exists_absolute(expected.bundle), "owned original native input and prepared converter bundle are offline for this fresh reader")
	for mode in ["packed", "linked"]:
		named_prefix = str(expected.name) + "/" + mode
		var first_check := checks; var first_failure := failures
		app.new_project(); app.has_project.cache_root = str(job.folder).path_join(mode + "-cache")
		check(not DirAccess.dir_exists_absolute(app.has_project.cache_root), mode + " reader cache is absent before ordinary Open")
		var saved: Dictionary = expected.projects[mode]
		if not check(FileAccess.get_sha256(saved.path) == saved.sha256, mode + " source HAS bytes match the writer"): return
		if not await operation("unpack", func(): app.has_project.open_file(saved.path)): return
		var imported := actor(id)
		if not check(imported != null and actor(peer) != null, mode + " cold Open restores both converted actor and pre-existing peer"): return
		check(normal(World.portable(app.current_world())) == expected.portable_world and protected_state(peer) == expected.protected, mode + " cold Open restores exact native report, drawing pixels, audio PCM, keys and authored world")
		check(imported.data.metadata.get("native_parameters", {}) == expected.parameters and imported.data.sha256 == expected.glb_sha256 and FileAccess.get_sha256(imported.data.source) == expected.glb_sha256, mode + " cold actor retains exact converter report and GLB bytes")
		var runtime_path: String = ProjectSettings.globalize_path(imported.data.source).replace("\\", "/").to_lower()
		var cache_path: String = ProjectSettings.globalize_path(app.has_project.cache_root).replace("\\", "/").to_lower()
		check(runtime_path.begins_with(cache_path + "/") and app.source_import.pid < 0 and app.history.is_empty() and app.redo_history.is_empty() and not app.dirty, mode + " fresh cache supplies runtime geometry without reconversion or history edits")
		if expected.has("jiggle"): jiggle_observation(expected.jiggle, id, expected.parameters, "cold_open")
		for frame in [0, 24]:
			var captured := await picture(str(job.folder).path_join(mode + "-" + str(frame) + ".png"), frame)
			check(not captured.is_empty() and captured.pixel_sha256 == expected.pictures[str(frame)].pixel_sha256, mode + " cold derived frame " + str(frame) + " exactly matches the writer reference")
		check(FileAccess.get_sha256(saved.path) == saved.sha256, mode + " Open leaves the saved package unchanged")
		if expected.has("shape_ui"):
			var shape_ui := ShapeUI.new(); shape_ui.app = app
			shape_ui.record = func(ok: bool, name: String) -> bool: return named_check(ok, "shape_ui." + name)
			await shape_ui.reader(expected.shape_ui, id, protected_state(peer) == expected.protected, job.folder, mode)
		read_modes.append({"mode": mode, "checks": checks - first_check, "failures": failures - first_failure, "frames": [0, 24], "project_sha256": saved.sha256, "passed": failures == first_failure})
	if job.get("export_movie", false):
		for i in range(app.output_size.item_count):
			if app.output_size.get_item_metadata(i) == "1080p": app.output_size.select(i); app.change_output_size(i); break
		check(app.selected_output_size() == "1080p" and int(app.video.duration_frames) == 48 and int(app.video.fps_num) == 24 and int(app.video.fps_den) == 1, "cold movie uses explicit 1080p output and original 48-frame24fps project")
		var error: String = await app.export_movie(job.folder); movie = app.last_export_folder.path_join("movie.mp4")
		check(error.is_empty() and FileAccess.file_exists(movie), "cold source-offline project exports one fresh H264/AAC movie")
		for frame in [0, 24]:
			var exported := Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png" % (frame + 1))); exported.convert(Image.FORMAT_RGBA8)
			check(Storage.RasterReader.digest_bytes(exported.get_data()) == expected.pictures[str(frame)].pixel_sha256, "cold movie PNG frame " + str(frame) + " matches the independent derived reference")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: push_error("One owned native job JSON is required"); quit(2); return
	var value = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not value is Dictionary or value.get("format") != "has_source_choices_native_job_1": push_error("Invalid native job"); quit(2); return
	job = value; job_path = args[0]; create_timer(float(job.get("watchdog_seconds", 900))).timeout.connect(func(): push_error("Native Source-choice watchdog"); quit(2))
	app = load("res://main.tscn").instantiate(); app.recovery_root = str(job.folder).path_join("recovery"); app.recent_path = str(job.folder).path_join("recent.json"); app.display_prefs_path = str(job.folder).path_join("display.cfg")
	root.add_child(app); await settled(); app.home.hide(); app.autosave_enabled.button_pressed = false
	app.has_project.cache_root = str(job.folder).path_join("writer-cache"); app.source_import.paths_file = str(job.folder).path_join("source-paths.cfg")
	check(app.video.width == 1920 and app.video.height == 1080 and app.video.duration_frames == 48, "fresh ordinary app starts at the required full-HD48-frame canvas")
	if job.mode == "writer":
		for item in job.cases:
			var row := await writer_case(item); rows.append(row)
			if row.is_empty() or not row.get("passed", false): break
	else: await reader()
	var result := {"format": "has_source_choices_native_app_result_1", "mode": job.mode, "checks": checks, "failures": failures, "cases": rows, "reader_modes": read_modes, "movie": movie,
		"named_checks": named_ledger, "native_simulation_claimed": false,
		"project_root": ProjectSettings.globalize_path("res://"), "job_path": job_path, "job_sha256": FileAccess.get_sha256(job_path),
		"source_manifest_sha256": job.source_manifest_sha256, "source_revision": job.source_revision,
		"actual_source_dialog": job.mode == "writer", "actual_native_conversion": job.mode == "writer", "actual_app": true, "derived_pixels_only": true,
		"scope": "Static Source import choices and ordinary actor/history/HAS/cold-render transport. No original Source shader, jiggle, assembly or artist fidelity claim."}
	write_json(str(job.folder).path_join("result.json"), result); print("SOURCE_CHOICES_NATIVE " + JSON.stringify(result)); await app.quit_studio(); quit(0 if failures == 0 else 1)
