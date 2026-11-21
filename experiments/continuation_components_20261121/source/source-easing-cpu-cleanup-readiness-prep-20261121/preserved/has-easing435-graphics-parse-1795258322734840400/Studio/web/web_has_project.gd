extends "res://src/has_project.gd"
const WebContainer=preload("res://web/web_has_container.gd")

func save_dialog() -> void:
	if app.exporting:return
	var dialog:=ConfirmationDialog.new();dialog.title="Download project";dialog.ok_button_text="Download .has"
	var box:=VBoxContainer.new();dialog.add_child(box)
	app.label(box,"A packed copy downloads to your browser. Keep it to preserve your work.")
	app.label(box,"Browser preview:128MiB maximum. Linked files need Windows Studio.")
	var filename:=LineEdit.new();filename.text="Untitled.has";filename.max_length=100;box.add_child(filename);dialog.register_text_enter(filename)
	dialog.confirmed.connect(func():dialog.hide();save_file(filename.text,"packed");dialog.queue_free())
	dialog.canceled.connect(dialog.queue_free);app.add_child(dialog);dialog.popup_centered(Vector2i(670,170));filename.grab_focus()

func save_file(selected: String,mode: String) -> void:
	if app.exporting:return
	if mode!="packed":app.message("Browser projects download as packed .has files. Use Windows Studio for linked assets.");return
	var filename:=selected.get_file().strip_edges()
	if filename.is_empty() or filename.length()>100 or filename.contains(":"):app.message("Choose a short project filename.");return
	if filename.get_extension().to_lower()!="has":filename+=".has"
	if not app.physics_editor.freeze_all():return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	var snapshot: String=ProjectSettings.globalize_path("user://web-projects/save-"+str(Time.get_ticks_usec()))
	var error: String=Storage.save_project(snapshot,app.video,app.keys,app.layers,app.source,app.frame,app.audio_clip,{},app.renderer.model_state(),true,app.renderer.world_state())
	if not error.is_empty():app.message(error);return
	var packed:=WebContainer.pack(snapshot,snapshot+".has")
	if packed.has("error"):app.message(packed.error);operation_finished.emit("pack",false);return
	JavaScriptBridge.download_buffer(FileAccess.get_file_as_bytes(packed.path),filename,"application/zip")
	app.message("Download prepared: "+filename+". Check your browser downloads; your edits stay marked unsaved.")
	# The download API cannot confirm a durable OS save. Never mark these edits clean.
	operation_finished.emit("pack",true)

func open_file(selected: String,_relinks := {},_as_copy := false) -> void:
	if app.exporting:return
	var folder: String=ProjectSettings.globalize_path("user://web-projects/open-"+str(Time.get_ticks_usec()))
	var unpacked:=WebContainer.unpack(selected,folder)
	if unpacked.has("error"):app.message(unpacked.error);operation_finished.emit("unpack",false);return
	if not app.open_project(folder):operation_finished.emit("unpack",false);return
	path="";app.project_folder=""
	app.message("Opened "+selected.get_file()+". Save downloads a separate packed copy.")
	operation_finished.emit("unpack",true)

func _process(_delta: float) -> void:pass
