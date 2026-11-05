extends Node
signal operation_finished(action: String,success: bool)
const Storage = preload("res://src/storage.gd")
const Recovery = preload("res://src/recovery.gd")
var app
var path := ""
var storage_mode := "packed"
var origins := {}
var cache_root := "res://output/has-cache"
var pid := -1
var result_path := ""
var cancel_path := ""
var pending := {}
var revision := -1
var progress: Window
var cancelled := false
var started := 0

func clear_identity() -> void:
	path = ""; storage_mode = "packed"; origins = {}

func save_dialog() -> void:
	if app.exporting or app.source_import.pid > 0: return
	app.stop()
	var dialog := FileDialog.new(); dialog.title = "Save Hybrid Animation Studio project"
	dialog.access = FileDialog.ACCESS_FILESYSTEM; dialog.file_mode = FileDialog.FILE_MODE_SAVE_FILE
	dialog.filters = PackedStringArray(["*.has ; Hybrid Animation Studio project"])
	dialog.current_file = path.get_file() if not path.is_empty() else "Untitled.has"
	var options := VBoxContainer.new()
	dialog.get_vbox().add_child(options)
	var packed := CheckButton.new(); packed.text = "Pack assets into this file (portable)"; packed.button_pressed = storage_mode == "packed"; options.add_child(packed)
	var note := Label.new(); note.text = "Linked: smaller file; existing 3D/audio files must remain available.\nDrawings and animation edits are always included."; options.add_child(note)
	dialog.file_selected.connect(func(selected):
		var choice := "packed" if packed.button_pressed else "linked"
		dialog.hide(); dialog.queue_free(); save_file(selected, choice))
	dialog.canceled.connect(dialog.queue_free)
	app.add_child(dialog); dialog.popup_centered_ratio(0.75)

func save_current() -> void:
	if path.is_empty(): save_dialog()
	else: save_file(path, storage_mode)

func save_file(selected: String, mode: String) -> void:
	if app.exporting or app.source_import.pid > 0: return
	if selected.get_extension().to_lower() != "has": selected += ".has"
	if builtin(selected):app.message("Choose a personal project file; the included practice scene stays unchanged.");return
	if not app.physics_editor.freeze_all():return
	app.stop(); app.finish_stroke(); app.pose_editor.finish_drag()
	var base := ProjectSettings.globalize_path(cache_root)
	var snapshot := base.path_join("work_%d" % OS.get_process_id())
	var error := Storage.save_project(snapshot, app.video, app.keys, app.layers, app.source, app.frame, app.audio_document(), {}, app.renderer.model_state(), true,app.renderer.world_state())
	if not error.is_empty(): app.message(error); return
	var references := {}
	var sources: Array=[]
	for clip in app.audio_clips: sources.append(clip.source.path)
	if app.renderer.world_runtime:
		for row in app.renderer.world_state().objects:sources.append(row.source)
	else:sources.append_array([app.source,app.renderer.model.data.source if app.renderer.model else ""])
	for source_file in sources:
		if str(source_file).is_empty(): continue
		var absolute := ProjectSettings.globalize_path(source_file).replace("\\", "/")
		var key := "assets/" + FileAccess.get_sha256(absolute) + "." + absolute.get_extension().to_lower()
		var original: String=origins.get(absolute,absolute)
		references[key] = original if FileAccess.get_sha256(original)==FileAccess.get_sha256(absolute) else absolute
	start({"action":"pack", "path":selected, "storage":mode, "folder":snapshot, "references":references, "cache_root":base,"cache_roots":[ProjectSettings.globalize_path("res://output/imports")]})

func builtin(selected: String) -> bool:
	var root:=ProjectSettings.globalize_path("res://examples/tutorials").replace("\\","/").simplify_path().to_lower()+"/"
	return ProjectSettings.globalize_path(selected).replace("\\","/").simplify_path().to_lower().begins_with(root)

func open_file(selected: String, relinks := {},as_copy := false) -> void:
	if app.exporting or app.source_import.pid > 0: return
	as_copy=as_copy or builtin(selected)
	var base := ProjectSettings.globalize_path(cache_root)
	start({"action":"unpack", "path":selected, "folder":base.path_join("open_%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()]), "relinks":relinks,"as_copy":as_copy})

func start(request: Dictionary) -> void:
	app.stop(); app.release_mouse()
	var base := ProjectSettings.globalize_path(cache_root)
	DirAccess.make_dir_recursive_absolute(base)
	var prefix := base.path_join("job_%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()])
	result_path = prefix + "-result.json"; cancel_path = prefix + "-cancel"
	request["result"] = result_path; request["cancel"] = cancel_path
	var file := FileAccess.open(prefix+".json",FileAccess.WRITE)
	if file == null: app.message("Cannot write HAS operation request");operation_finished.emit(request.action,false); return
	file.store_string(JSON.stringify(request)); file.close()
	pending = request; revision = app.recovery_revision; cancelled = false; started = Time.get_ticks_msec()
	pid = OS.create_process(app.source_import.python(), [ProjectSettings.globalize_path("res://tools/has_project.py"), prefix+".json"], false)
	if pid < 0: app.message("Cannot start Python project worker");operation_finished.emit(request.action,false); return
	app.exporting = true
	progress = Window.new(); progress.title = "Saving .has project" if request.action == "pack" else "Opening .has project"
	progress.transient = true; progress.exclusive = true; progress.close_requested.connect(cancel)
	app.add_child(progress)
	var panel := PanelContainer.new(); panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.add_theme_stylebox_override("panel", preload("res://src/studio_theme.gd").surface("f4f7fb","dce5ee")); progress.add_child(panel)
	var box := VBoxContainer.new(); panel.add_child(box)
	app.label(box, "Preparing editable project and verifying assets…\n" + str(request.path)).autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	app.button(box, "Cancel", cancel)
	progress.popup_centered(Vector2i(650,160))

func cancel() -> void:
	cancelled = true
	var file := FileAccess.open(cancel_path,FileAccess.WRITE)
	if file: file.store_string("cancel"); file.close()

func locate_missing(result: Dictionary) -> void:
	if not result.get("missing") is Array or result.missing.is_empty(): return
	var missing: Dictionary = result.missing[0]
	var request := pending.duplicate(true)
	app.confirm_action("Locate the matching linked asset?\n" + str(missing.reference) + "\nThe checksum must match. Cancel keeps the current project.", func():
		app.choose_file("Locate linked asset", PackedStringArray(["*." + str(missing.asset).get_extension()]), func(replacement):
			var links: Dictionary = request.get("relinks", {}).duplicate()
			links[missing.asset] = replacement
			open_file(request.path, links)))

func _process(_delta: float) -> void:
	if pid <= 0: return
	if OS.is_process_running(pid):
		if Time.get_ticks_msec()-started > 120000: OS.kill(pid); cancelled = true
		else: return
	pid = -1; app.exporting = false
	if is_instance_valid(progress): progress.hide(); progress.queue_free()
	var result = Recovery.read_json(result_path)
	if not result.get("ok",false):
		app.message(str(result.get("error", "HAS worker failed; partial cache retained and current project preserved.")))
		if not cancelled: locate_missing(result)
		operation_finished.emit(pending.action,false)
		return
	if pending.action == "unpack":
		if not app.open_project(result.folder):operation_finished.emit(pending.action,false); return
		path = pending.path; storage_mode = result.storage; origins = {}
		for key in result.origins: origins[str(key).replace("\\", "/")] = result.origins[key]
		if path.ends_with(".has.backup") or pending.get("as_copy",false):
			path = ""; app.project_folder = ""; app.changed()
			app.message("Practice scene opened as an unsaved copy. Save chooses a personal .has file." if pending.get("as_copy",false) else "Restored HAS backup as an unsaved copy. Save chooses a new .has file.")
			operation_finished.emit(pending.action,true)
			return
		app.message("Opened " + path + " • " + storage_mode)
		app.home.remember(path)
	else:
		path = pending.path; storage_mode = pending.storage
		if app.recovery_revision == revision:
			app.dirty = false
			app.reset_recovery_schedule()
			var resolved := Recovery.resolve(app.recovery_root.path_join(app.recovery_session))
			if not app.recovered_from.is_empty():
				var error := Recovery.resolve(app.recovered_from)
				if error.is_empty(): app.recovered_from = ""
				else: resolved = error
			app.recovery_status.text = "Project saved" if resolved.is_empty() else "Saved; recovery copy retained"
		app.message("Saved " + path + " • " + storage_mode + (" • newer edits remain unsaved" if app.dirty else ""))
		app.home.remember(path,revision)
	operation_finished.emit(pending.action,true)
