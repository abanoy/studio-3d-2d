extends "res://src/app.gd"
var upload_callback: JavaScriptObject
var upload_action: Callable
var upload_revision:=-1
var upload_frame:=-1
var upload_active:=false

func _ready() -> void:
	# Browser file dialogs require a live trusted input event, not a later frame.
	Input.use_accumulated_input=false
	upload_callback=JavaScriptBridge.create_callback(upload_finished)
	super._ready()
	autosave_enabled.button_pressed=false;autosave_enabled.disabled=true
	recovery_status.text="Browser preview • download .has to keep your edits"
	tool.set_item_disabled(2,true)
	if home:
		home.tutorials_button.disabled=true
		home.tutorials_button.tooltip_text="Guided lessons are available in Windows Studio. Browser lessons are still being adapted."
	var tips:={"Add scene":"Browser: choose an embedded GLB environment.","Add model":"Browser: choose an embedded GLB model. Prepare other formats in Windows Studio.","Installed":"Use Windows Studio to browse installed games.","Recover":"Browser recovery is still being developed. Download .has to keep your edits.","Export movie":"Browser movie export is still being developed. Windows Studio can render your downloaded .has."}
	for control in find_children("*","Button",true,false):
		if control is Button and tips.has(control.text):control.tooltip_text=tips[control.text]
	JavaScriptBridge.eval("window.HAS_STUDIO_READY = true")

func recover_latest(_session: String,_revision: int) -> void:
	startup_recovery_result={"restored":false,"attempts":[],"cancelled":false}
	home.open_home();home.feedback("Browser preview. Open a packed .has, or start a scene. Download your work before closing.")
	startup_recovery_finished.emit(startup_recovery_result)

func autosave_tick(force := false) -> void:
	if force:show_recovery()
func show_recovery(_history_view := false) -> void:message("Browser recovery is still being developed. Download a packed .has before closing this tab.")
func export_dialog() -> void:message("Browser movie export is still being developed. Download .has and open it in Windows Studio to export MP4 with audio.")
func export_elsewhere() -> void:export_dialog()

func choose_file(title: String,filters: PackedStringArray,action: Callable,_initial_dir := "") -> void:
	if exporting or upload_active:return
	stop();finish_stroke();pose_editor.finish_drag();release_mouse()
	var accepted: PackedStringArray=[]
	for item in filters:
		for extension in ["glb","wav","has"]:
			if item.contains("*."+extension) and not ("."+extension) in accepted:accepted.append("."+extension)
	if accepted.is_empty():message("This browser preview opens packed .has, embedded .glb and PCM16 .wav files. Native conversions need Windows Studio.");return
	message("Choose a local file. Its contents stay in this browser.")
	var directory: String=ProjectSettings.globalize_path("user://uploads/"+str(Time.get_ticks_usec()))
	if DirAccess.make_dir_recursive_absolute(directory)!=OK:message("Cannot create browser upload folder.");return
	upload_action=action;upload_revision=recovery_revision;upload_frame=frame;upload_active=true
	JavaScriptBridge.get_interface("HASFiles").pick(title,','.join(accepted),directory,upload_callback)

func upload_finished(args: Array) -> void:
	if not upload_active:return
	upload_active=false
	if args.size()!=2 or not args[0] is String or not args[1] is String:message("Browser file selection did not complete.");return
	if not args[1].is_empty():message(args[1]);return
	if args[0].is_empty():return
	if upload_revision!=recovery_revision or upload_frame!=frame or exporting:message("Scene changed while choosing a file. Choose the file again.");return
	upload_action.call(args[0])

func choose_directory(_title: String,_action: Callable,_initial_dir := "") -> void:
	message("Browser files use uploads and downloads. Local folders and native converters are available in Windows Studio.")
