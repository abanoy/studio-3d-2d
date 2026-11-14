extends Node
const DEFAULT_GMOD := "C:/Program Files (x86)/Steam/steamapps/common/GarrysMod"
const DEFAULT_WORKSHOP := "C:/Program Files (x86)/Steam/steamapps/workshop/content/4000"
var paths_file := "res://output/source-paths.cfg"
var gmod_root := DEFAULT_GMOD
var workshop_root := DEFAULT_WORKSHOP
var extra_roots: Array = []
var mount_overrides := {}
var app
var pid := -1
const PREPARATION_PROCESS_ENGINE := "89cea143987d564363e15d207438530651d943ac"
var _preparation_map_pid := -1
var _preparation_map_reserved := false
var folder := ""
var result_path := ""
var cancel_path := ""
var actor := false
var progress: Window
var progress_label: Label
var cancel_button: Button
var cancelled := false
var generic := false
var native_family := ""
var import_frame := 0
var placement_context := {}

func _ready() -> void:
	load_paths()

func load_paths() -> void:
	var config := ConfigFile.new()
	config.load(paths_file)
	gmod_root = str(config.get_value("source", "gmod", DEFAULT_GMOD))
	workshop_root = str(config.get_value("source", "workshop", DEFAULT_WORKSHOP))
	var extra = config.get_value("source", "extra_roots", [])
	extra_roots = extra if extra is Array else []
	var overrides = config.get_value("source", "mount_overrides", {})
	mount_overrides = overrides if overrides is Dictionary else {}
	if not OS.get_environment("HYBRID_GMOD").is_empty(): gmod_root = OS.get_environment("HYBRID_GMOD")
	if not OS.get_environment("HYBRID_GMOD_WORKSHOP").is_empty(): workshop_root = OS.get_environment("HYBRID_GMOD_WORKSHOP")

func save_paths() -> Error:
	var config := ConfigFile.new()
	config.set_value("source", "gmod", gmod_root)
	config.set_value("source", "workshop", workshop_root)
	config.set_value("source", "extra_roots", extra_roots)
	config.set_value("source", "mount_overrides", mount_overrides)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(paths_file).get_base_dir())
	return config.save(paths_file)

func default_browse_dir() -> String:
	if DirAccess.dir_exists_absolute(workshop_root): return workshop_root
	if DirAccess.dir_exists_absolute(gmod_root.path_join("garrysmod")): return gmod_root.path_join("garrysmod")
	return gmod_root if DirAccess.dir_exists_absolute(gmod_root) else ""

func path_field(box: Node, dialog: Window, title: String, value: String) -> LineEdit:
	app.label(box, title)
	var row := HBoxContainer.new()
	box.add_child(row)
	var field := LineEdit.new()
	field.text = value
	field.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(field)
	app.button(row, "Browse…", func():
		var picker := FileDialog.new()
		picker.title = title
		picker.access = FileDialog.ACCESS_FILESYSTEM
		picker.file_mode = FileDialog.FILE_MODE_OPEN_DIR
		dialog.add_child(picker)
		if DirAccess.dir_exists_absolute(field.text): picker.current_dir = field.text
		picker.dir_selected.connect(func(path): field.text = path; picker.queue_free())
		picker.canceled.connect(picker.queue_free)
		picker.popup_centered(Vector2i(720, 440)))
	return field

func python() -> String:
	var override := OS.get_environment("HYBRID_PYTHON")
	return override if not override.is_empty() else "python"

func inspect_source_members(path: String) -> Dictionary:
	var output: Array=[]
	var code:=OS.execute(python(),[ProjectSettings.globalize_path("res://tools/prepare_source.py"),path,"--catalog"],output,true,false)
	var text:="".join(output)
	return {"code":code,"data":JSON.parse_string(text),"text":text}

func make_appearance_ui() -> Node:
	return preload("res://src/source_choice_dialog.gd").new()

func _spawn_preparation(args: PackedStringArray) -> int:
	var created := OS.create_process(python(),args,false)
	# Only this actual creator reserves the pinned Windows process-map entry.
	# Test overrides which bypass it must not claim ownership of their fake PID.
	if created > 0 and OS.get_name() == "Windows" and str(Engine.get_version_info().get("hash", "")) == PREPARATION_PROCESS_ENGINE:
		_preparation_map_pid = created
		_preparation_map_reserved = true
	return created

func _release_preparation_map_entry(owned: int) -> Error:
	return OS.kill(owned)

func _release_completed_preparation() -> void:
	if not _preparation_map_reserved: return
	var owned := _preparation_map_pid
	if owned <= 0 or OS.is_process_running(owned): return
	# A completed mapped child may report FAILED from TerminateProcess while
	# still erasing its entry and closing both handles. Consume once; never retry.
	_preparation_map_reserved = false
	_preparation_map_pid = -1
	_release_preparation_map_entry(owned)

func _exit_tree() -> void:
	# A live preparer retains its cooperative cancellation/child-cleanup path.
	_release_completed_preparation()

func start(path: String, as_model: bool, at_frame := 0, placement := {}) -> void:
	if pid > 0 or app.exporting: return
	if app.height_review and app.height_review.pending:app.message("Finish the pending height review first.");return
	if path.get_extension().to_lower() in ["pmd", "pmx", "vrm"]:
		launch(path,"",as_model,0.08 if path.get_extension().to_lower() in ["pmd","pmx"] else 1.0,"",null,"","Y",at_frame,placement)
		return
	if path.get_extension().to_lower() == "vroid":
		app.message("Open this project in VRoid Studio and save a VRM avatar, then add that VRM here. Native .vroid project import is not available yet.")
		return
	if path.get_extension().to_lower() in ["fbx", "obj", "gltf"]:
		generic_dialog(path, as_model, at_frame,placement)
		return
	app.stop()
	var catalog: Array = []
	var inspected := inspect_source_members(path)
	var code: int = inspected.code
	var data = inspected.data
	catalog.append(str(inspected.text))
	if code != 0 or not data is Dictionary:
		app.message("Cannot inspect Source file. Python is required. " + "".join(catalog).left(400))
		return
	var choices: Array = data.get("models" if as_model else "maps", [])
	if choices.is_empty():
		app.message("This archive has no " + ("MDL models. Use Add scene for BSP maps." if as_model else "BSP maps. Use Add model for MDL models."))
		return
	var dialog := ConfirmationDialog.new()
	dialog.title = "Import Source model" if as_model else "Import Source map"
	dialog.ok_button_text = "Prepare and import"
	dialog.dialog_hide_on_ok = false
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(720, minf(480, maxf(240, app.get_viewport_rect().size.y - 180)))
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	dialog.add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(box)
	app.label(box, path.get_file())
	var members := OptionButton.new()
	members.custom_minimum_size.x = 580
	for member in choices: members.add_item(str(member))
	box.add_child(members)
	var appearance_ui = null
	if as_model:
		appearance_ui = make_appearance_ui()
		dialog.add_child(appearance_ui)
		appearance_ui.attach(dialog, box, path, members, python())
	var text: Label = app.label(box, "Converts locally with Blender / SourceIO into the same standard GLB used by MMD.\nTextures are approximate. No game scripts run. Your current scene changes only after success.\nNative copies, parameters, editable Blender file and warnings stay in output/compatibility.")
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	app.label(box, "Standalone models and maps do not require a game installation. Installed content folders are optional for browsing or resolving missing dependencies. Studio supplies neither games nor add-ons.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var game_field := path_field(box, dialog, "Optional Garry's Mod content", gmod_root)
	var workshop_field := path_field(box, dialog, "Installed Workshop content (4000)", workshop_root)
	app.button(box, "Browse installed models and maps…", func():
		gmod_root = game_field.text.strip_edges()
		workshop_root = workshop_field.text.strip_edges()
		if save_paths() != OK: app.message("Cannot save Source folder preferences."); return
		dialog.hide(); dialog.queue_free()
		app.source_browser.open(as_model))
	var scale: SpinBox = app.spin(box, "Source unit scale", 0.0001, 1, 0.01905)
	scale.step = 0.00001; scale.value = 0.01905
	var content := LineEdit.new()
	content.placeholder_text = "Optional additional content directory or _dir.vpk"
	content.tooltip_text = "Validated installed content is optional. Add a folder or VPK only when your model needs files from it."
	box.add_child(content)
	app.add_child(dialog)
	dialog.confirmed.connect(func():
		if appearance_ui != null and not appearance_ui.selection_valid(): return
		var appearance: Dictionary = appearance_ui.request() if appearance_ui != null else {}
		gmod_root = game_field.text.strip_edges()
		workshop_root = workshop_field.text.strip_edges()
		if save_paths() != OK: app.message("Cannot save Source folder preferences."); dialog.queue_free(); return
		dialog.hide()
		if appearance_ui != null: appearance_ui.invalidate()
		launch(path, str(choices[members.selected]), as_model, scale.value, content.text.strip_edges(),null,"","Y",at_frame,placement,appearance)
		dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free)
	dialog.popup_centered(Vector2i(760, 560))

func generic_dialog(path: String, as_model: bool, at_frame := 0, placement := {}) -> void:
	app.stop()
	var dialog := ConfirmationDialog.new(); dialog.title = "Import 3D model" if as_model else "Import 3D environment"
	dialog.ok_button_text = "Prepare and import"
	var scroll := ScrollContainer.new(); scroll.custom_minimum_size = Vector2(680, 250); scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; dialog.add_child(scroll)
	var box := VBoxContainer.new(); box.size_flags_horizontal = Control.SIZE_EXPAND_FILL; scroll.add_child(box)
	app.label(box, path.get_file() + " → standard GLB\nGeometry, PBR textures and skinned bind pose. Native animation clips remain in editable.blend.\nYour existing project changes only after successful conversion.").autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var scale: SpinBox = app.spin(box, "Uniform scale", 0.0001, 10000, 1); scale.step = 0.0001; scale.value = 1
	var root: LineEdit = path_field(box, dialog, "Asset folder (shared textures/buffers must stay inside)", path.get_base_dir())
	var up := OptionButton.new(); up.add_item("OBJ: Y up"); up.add_item("OBJ: Z up")
	box.add_child(up); up.visible = path.get_extension().to_lower() == "obj"
	app.add_child(dialog)
	dialog.confirmed.connect(func(): dialog.hide(); launch(path, "", as_model, scale.value, "", null, root.text.strip_edges(), "Y" if up.selected == 0 else "Z",at_frame,placement); dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free); dialog.popup_centered(Vector2i(760, 360))

func launch(path: String, member: String, as_model: bool, scale: float, content := "", dependency_mounts = null, asset_root := "", obj_up := "Y", at_frame := 0, placement := {}, appearance := {}) -> void:
	if app.height_review and app.height_review.pending:app.message("Finish the pending height review first.");return
	if pid > 0: return
	generic = path.get_extension().to_lower() in ["fbx", "obj", "gltf"]
	native_family = "mmd" if path.get_extension().to_lower() in ["pmd","pmx"] else ("vrm" if path.get_extension().to_lower()=="vrm" else "")
	actor = as_model
	import_frame = at_frame
	placement_context = placement.duplicate(true)
	cancelled = false
	app.stop(); app.finish_stroke(); app.pose_editor.finish_drag(); app.release_mouse()
	folder = ProjectSettings.globalize_path("res://output/compatibility/source-" + str(Time.get_unix_time_from_system()).replace(".", "-") + "-" + str(Time.get_ticks_usec()))
	DirAccess.make_dir_recursive_absolute(folder.get_base_dir())
	result_path = folder + "-result.json"
	cancel_path = folder + "-cancel"
	var worker := "prepare_"+native_family+".py" if not native_family.is_empty() else ("prepare_generic.py" if generic else "prepare_source.py")
	var args := PackedStringArray([ProjectSettings.globalize_path("res://tools/"+worker), path, "--output", folder, "--scale", str(scale), "--status-file", result_path, "--cancel-file", cancel_path])
	if generic:
		args.append_array(["--asset-root", asset_root if not asset_root.is_empty() else path.get_base_dir(), "--obj-up", obj_up])
	elif native_family.is_empty(): args.append_array(["--gmod", gmod_root, "--workshop", workshop_root])
	if path.get_extension().to_lower() in ["gma", "bin", "vpk"]: args.append_array(["--member", member])
	if dependency_mounts != null:
		var plan := FileAccess.open(folder + "-mounts.json", FileAccess.WRITE)
		if plan == null: app.message("Cannot write dependency mount plan."); return
		plan.store_string(JSON.stringify(Array(dependency_mounts))); plan.close()
		args.append_array(["--mount-plan", folder + "-mounts.json"])
	elif not generic and native_family.is_empty() and (not extra_roots.is_empty() or not mount_overrides.is_empty()):
		var settings := FileAccess.open(folder + "-mount-settings.json", FileAccess.WRITE)
		if settings == null: app.message("Cannot write dependency settings."); return
		settings.store_string(JSON.stringify({"extra": extra_roots, "overrides": mount_overrides})); settings.close()
		args.append_array(["--mount-settings", folder + "-mount-settings.json"])
	if not appearance.is_empty():
		if generic or not native_family.is_empty() or not as_model:
			app.message("Appearance choices apply only to one Source model."); return
		var appearance_path := folder + "-appearance.json"
		var appearance_json := JSON.stringify(appearance)
		if appearance_json.to_utf8_buffer().size() > 64 * 1024:
			app.message("Appearance request is too large."); return
		var appearance_file := FileAccess.open(appearance_path, FileAccess.WRITE)
		if appearance_file == null: app.message("Cannot write the appearance request."); return
		appearance_file.store_string(appearance_json); appearance_file.close()
		args.append_array(["--appearance", appearance_path])
	if not content.is_empty(): args.append_array(["--content", content])
	pid = _spawn_preparation(args)
	if pid < 0: app.message("Cannot start local asset preparation. Check the installed Python path."); return
	progress = Window.new()
	progress.title = "Importing model" if actor else "Importing environment"
	progress.transient = true
	progress.exclusive = true
	progress.close_requested.connect(cancel)
	var background := Panel.new()
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.add_theme_stylebox_override("panel", preload("res://src/studio_theme.gd").surface("f4f7fb", "dce5ee"))
	progress.add_child(background)
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	progress.add_child(box)
	progress_label = app.label(box, "Converting locally… The editor will stay responsive.\n" + path.get_file() + "\nLarger maps can take several minutes.\n" + folder)
	progress_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cancel_button = app.button(box, "Cancel preparation", cancel)
	app.add_child(progress)
	progress.popup_centered(Vector2i(660, 200))

func cancel() -> void:
	if pid <= 0: return
	cancelled = true
	var file := FileAccess.open(cancel_path, FileAccess.WRITE)
	if file: file.store_string("cancel"); file.close()
	progress_label.text = "Cancelling import… Partial files retained."
	cancel_button.disabled = true

func _process(_delta: float) -> void:
	if pid <= 0 or OS.is_process_running(pid): return
	_release_completed_preparation()
	pid = -1
	if is_instance_valid(progress): progress.hide(); progress.queue_free()
	var result = JSON.parse_string(FileAccess.get_file_as_string(result_path)) if FileAccess.file_exists(result_path) else null
	if cancelled: app.message("Import cancelled. Current project preserved. Partial files: " + folder); return
	if not result is Dictionary or not result.get("ok", false):
		app.message(str(result.get("error", "Preparation ended without a result")) if result is Dictionary else "Local preparation failed. Check the installed tools and the import log.")
		return
	var error := ""
	if actor: error = app.pose_editor.add_model(str(result.glb),import_frame,placement_context)
	else:
		error=app.load_scene(str(result.glb),import_frame)
		if not error.is_empty():return
		app.mode.select(1); app.change_mode(1); app.frame_3d_scene()
	if not error.is_empty(): return
	var report = JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("parameters.json")))
	if not actor and report is Dictionary: apply_view(report)
	var count: int = report.get("warnings", []).size() if report is Dictionary else 0
	var skipped: int = report.get("mount_warnings", []).size() if report is Dictionary else 0
	app.message(("3D asset" if generic or not native_family.is_empty() else "Source asset") + " imported through standard GLB. %d resource warnings; %d dependency packages skipped. Details: %s" % [count, skipped, folder])
	if actor and app.height_review and app.height_review.pending:app.message("3D asset prepared. Review its height to finish adding the model. Details: "+folder)
	elif actor and app.renderer.active_model():app.message(app.status.text+app.placement_message(app.renderer.active_model().data))
	if count > 0:
		var dialog := AcceptDialog.new()
		dialog.exclusive = false
		dialog.title = "Imported with limitations" if not native_family.is_empty() else "Source import warnings"
		var summary := "Import notes"
		if report.get("missing_textures") is Array:
			var missing: int = report.missing_textures.size()
			summary = "Missing texture files: %d" % missing
		dialog.dialog_text = "%s\n%s\n\nFull details: %s" % [summary, "\n".join(report.warnings.slice(0, 6)), folder.path_join("parameters.json")]
		app.add_child(dialog)
		dialog.confirmed.connect(dialog.queue_free)
		dialog.canceled.connect(dialog.queue_free)
		dialog.close_requested.connect(dialog.queue_free)
		dialog.popup_centered(Vector2i(740, 340))

func apply_view(report: Dictionary) -> bool:
	var view = report.get("suggested_view")
	if not view is Dictionary: return false
	var p = view.get("position")
	var t = view.get("target")
	if not p is Array or not t is Array or p.size() != 3 or t.size() != 3: return false
	app.renderer.camera.position = Vector3(p[0], p[1], p[2])
	app.renderer.camera.look_at(Vector3(t[0], t[1], t[2]), Vector3.UP)
	return true
