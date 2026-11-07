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
var snapshot_writer=preload("res://src/has_snapshot_writer.gd").new()
var project_loader=preload("res://src/has_project_loader.gd").new()
var last_load_worker_ms:=0.
var last_install_ms:=0.
var _open_result: Dictionary={}
var last_snapshot_capture_ms:=0.
var last_snapshot_worker_ms:=0.
var _snapshot_error:=""
var _child_done:=false
var _operation_session:=""
var _operation_recovery_root:=""
var _operation_owner:=""
var _progress_label: Label

func same_document() -> bool:
	return app.recovery_root==_operation_recovery_root and app.recovery_session==_operation_session and app.sequence_editor.active_owner==_operation_owner

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
	var note := Label.new(); note.text = "Linked: smaller file; 3D/audio/reference files must remain available.\nDrawings and animation edits are always included."; options.add_child(note)
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
	var state: Dictionary=app.project_snapshot()
	start({"action":"pack", "path":selected, "storage":mode, "folder":snapshot, "cache_root":base,"cache_roots":[ProjectSettings.globalize_path("res://output/imports"),ProjectSettings.globalize_path("res://output/audio-imports"),ProjectSettings.globalize_path(app.reference_sheet.cache_root)]},state)

func save_asset(selected: String) -> void:
	if app.exporting or app.source_import.pid>0:return
	if selected.get_extension().to_lower()!="has":selected+=".has"
	if builtin(selected):app.message("Choose a personal asset package file.");return
	var target:=ProjectSettings.globalize_path(selected).simplify_path()
	var current:=ProjectSettings.globalize_path(path).simplify_path() if not path.is_empty() else ""
	if OS.get_name()=="Windows":target=target.to_lower();current=current.to_lower()
	if not current.is_empty() and target==current:
		app.message("Choose another filename; this file is the current scene.");return
	if not app.physics_editor.freeze_all():return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	var captured:=preload("res://src/asset_package.gd").snapshot(app)
	if captured.has("error"):app.message(captured.error);return
	var base:=ProjectSettings.globalize_path(cache_root)
	start({"action":"pack","path":selected,"storage":"packed","folder":base.path_join("asset_work_%d"%OS.get_process_id()),"asset_package":captured.header,"cache_root":base},captured.project)

func import_asset(selected: String,kind: String,at_frame: int) -> void:
	if app.exporting or app.source_import.pid>0:return
	var base:=ProjectSettings.globalize_path(cache_root)
	start({"action":"unpack","path":selected,"folder":base.path_join("asset_open_%d_%d"%[OS.get_process_id(),Time.get_ticks_usec()]),"relinks":{},"import_asset":true,"asset_kind":kind,"asset_frame":at_frame})

func builtin(selected: String) -> bool:
	var root:=ProjectSettings.globalize_path("res://examples/tutorials").replace("\\","/").simplify_path().to_lower()+"/"
	return ProjectSettings.globalize_path(selected).replace("\\","/").simplify_path().to_lower().begins_with(root)

func open_file(selected: String, relinks := {},as_copy := false) -> void:
	if app.exporting or app.source_import.pid > 0: return
	as_copy=as_copy or builtin(selected)
	var base := ProjectSettings.globalize_path(cache_root)
	start({"action":"unpack", "path":selected, "folder":base.path_join("open_%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()]), "relinks":relinks,"as_copy":as_copy})

func start(request: Dictionary,snapshot_state: Dictionary={}) -> void:
	app.stop(); app.release_mouse()
	var base := ProjectSettings.globalize_path(cache_root)
	DirAccess.make_dir_recursive_absolute(base)
	var prefix := base.path_join("job_%d_%d" % [OS.get_process_id(), Time.get_ticks_usec()])
	result_path = prefix + "-result.json"; cancel_path = prefix + "-cancel"
	request["result"] = result_path; request["cancel"] = cancel_path
	_snapshot_error="";_child_done=false;_open_result={}
	_operation_session=app.recovery_session;_operation_recovery_root=app.recovery_root;_operation_owner=app.sequence_editor.active_owner
	if not snapshot_state.is_empty():
		request["snapshot_ready"]=prefix+"-snapshot.json"
		var began:=Time.get_ticks_usec();var why: String=snapshot_writer.start(snapshot_state,{"folder":request.folder,"ready":request.snapshot_ready,"cancel":cancel_path,"origins":origins.duplicate(true)})
		last_snapshot_capture_ms=(Time.get_ticks_usec()-began)/1000.
		if not why.is_empty():app.message(why);operation_finished.emit(request.action,false);return
	var file := FileAccess.open(prefix+".json",FileAccess.WRITE)
	if file == null:
		_write_cancel();snapshot_writer.finish();app.message("Cannot write HAS operation request");operation_finished.emit(request.action,false);return
	file.store_string(JSON.stringify(request)); file.close()
	pending = request; revision = app.recovery_revision; cancelled = false; started = Time.get_ticks_msec()
	pid = OS.create_process(app.source_import.python(), [ProjectSettings.globalize_path("res://tools/has_project.py"), prefix+".json"], false)
	if pid < 0:
		_write_cancel();snapshot_writer.finish();app.message("Cannot start Python project worker");operation_finished.emit(request.action,false);return
	app.exporting = true
	progress = Window.new(); progress.title = "Saving .has project" if request.action == "pack" else "Opening .has project"
	progress.transient = true; progress.exclusive = true; progress.close_requested.connect(cancel)
	app.add_child(progress)
	var panel := PanelContainer.new(); panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.add_theme_stylebox_override("panel", preload("res://src/studio_theme.gd").surface("f4f7fb","dce5ee")); progress.add_child(panel)
	var box := VBoxContainer.new(); panel.add_child(box)
	_progress_label=app.label(box, "Preparing editable project and verifying assets…\n" + str(request.path));_progress_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	app.button(box, "Cancel", cancel)
	progress.popup_centered(Vector2i(650,160))

func _write_cancel() -> void:
	if cancel_path.is_empty():return
	var file:=FileAccess.open(cancel_path,FileAccess.WRITE)
	if file:file.store_string("cancel");file.close()
func cancel() -> void:
	cancelled=true;_write_cancel()
	if is_instance_valid(_progress_label):_progress_label.text="Cancelling project operation…\nThe current project stays open until saving stops."


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
	if pid<=0:return
	if project_loader.busy():
		if Time.get_ticks_msec()-started>600000 or not same_document() or app.recovery_revision!=revision:cancelled=true;_write_cancel()
		var loaded: Dictionary=project_loader.poll()
		if loaded.is_empty():return
		last_load_worker_ms=loaded.worker_ms
		if cancelled or not same_document() or app.recovery_revision!=revision:loaded.data={"error":"Project opening cancelled or document changed. Current project preserved."}
		pid=-1;app.exporting=false
		if is_instance_valid(progress):progress.hide();progress.queue_free()
		if loaded.data.has("error"):
			app.message(loaded.data.error);operation_finished.emit(pending.action,false);return
		if pending.get("import_asset",false):
			var why: String=preload("res://src/asset_package.gd").import_into(app,loaded.data,_open_result.get("asset_package",{}),pending.asset_kind,pending.path,pending.asset_frame)
			if not why.is_empty():app.message(why)
			operation_finished.emit(pending.action,why.is_empty());return
		var began:=Time.get_ticks_usec()
		var installed: bool=app.install_project_data(loaded.data,_open_result.folder)
		last_install_ms=(Time.get_ticks_usec()-began)/1000.
		if not installed:operation_finished.emit(pending.action,false);return
		_finish_open(_open_result);return
	if not _child_done:
		if OS.is_process_running(pid):
			var limit:=600000 if snapshot_writer.busy() else 120000
			if Time.get_ticks_msec()-started>limit:OS.kill(pid);cancelled=true;_child_done=true;_write_cancel()
		else:_child_done=true
	if snapshot_writer.busy():
		var captured: Dictionary=snapshot_writer.poll()
		if captured.is_empty():
			if _child_done:_write_cancel()
			return
		# Keep the existing two-minute packaging allowance separate from PNG work.
		started=Time.get_ticks_msec()
		last_snapshot_capture_ms=captured.capture_ms;last_snapshot_worker_ms=captured.worker_ms;_snapshot_error=captured.error
		if not _snapshot_error.is_empty():_write_cancel()
		elif not cancelled and is_instance_valid(_progress_label):_progress_label.text="Verifying assets and finishing the project file…\n"+str(pending.path)
	if not _child_done:return
	var result = Recovery.read_json(result_path)
	if not _snapshot_error.is_empty() and not cancelled:result={"ok":false,"error":_snapshot_error}
	if pending.get("import_asset",false) and result.get("ok",false) and not result.has("asset_package"):result={"ok":false,"error":"This HAS file is a scene. Use Open project, or choose an asset package."}
	if result.get("ok",false) and pending.action=="unpack" and not cancelled and same_document():
		_open_result=result
		var why: String=project_loader.start({"folder":result.folder,"cancel":cancel_path,"cold":app.cold_cel_loading,"cold_min_bytes":app.cold_cel_min_bytes})
		if why.is_empty():
			started=Time.get_ticks_msec()
			if is_instance_valid(_progress_label):_progress_label.text="Loading and checking project drawings…\n"+str(pending.path)
			return
		result={"ok":false,"error":why}
	elif pending.action=="unpack":result={"ok":false,"error":result.get("error","Project opening cancelled or document changed. Current project preserved.")}
	pid=-1;app.exporting=false
	if is_instance_valid(progress):progress.hide();progress.queue_free()
	if not result.get("ok",false):
		app.message(str(result.get("error", "HAS worker failed; partial cache retained and current project preserved.")))
		if not cancelled: locate_missing(result)
		operation_finished.emit(pending.action,false)
		return

	if pending.has("asset_package"):
		app.message("Saved asset package "+str(pending.path));operation_finished.emit(pending.action,true);return
	if not same_document():
		app.message("Finished saving the previous project to "+str(pending.path)+". The current project stays unchanged.")
		operation_finished.emit(pending.action,true);return
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

func _finish_open(result: Dictionary) -> void:
	path = pending.path; storage_mode = result.storage; origins = {}
	for key in result.origins: origins[str(key).replace("\\", "/")] = result.origins[key]
	if path.ends_with(".has.backup") or pending.get("as_copy",false):
		path = ""; app.project_folder = ""; app.changed()
		app.message("Practice scene opened as an unsaved copy. Save chooses a personal .has file." if pending.get("as_copy",false) else "Restored HAS backup as an unsaved copy. Save chooses a new .has file.")
		operation_finished.emit(pending.action,true)
		return
	app.message("Opened " + path + " • " + storage_mode)
	app.home.remember(path)
	operation_finished.emit(pending.action,true)

func _exit_tree() -> void:
	if project_loader.busy():_write_cancel();project_loader.finish()
	if snapshot_writer.busy():_write_cancel();snapshot_writer.finish()
