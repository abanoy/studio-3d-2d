extends "res://src/krita_import.gd"
var key_enabled: CheckButton
var key_color: OptionButton
var similarity: SpinBox
var softness: SpinBox

func worker_script() -> String:return "res://tools/prepare_video.py"
func source_extensions() -> Array:return ["mp4","mov","mkv","webm","avi"]
func import_title() -> String:return "Import video artwork"
func job_group() -> String:return "video-imports"
func success_message() -> String:return "Video added as editable held drawings. Undo removes this import."
func worker_arguments(args: Array) -> Array:
	var result:=args.duplicate()
	if "--inspect" in result:result.append_array(["--ffmpeg",app.encoder_path.text])
	return result
func setup(owner_app) -> void:
	app=owner_app
	launch=app.button(app.drawing_section,"Import video artwork…",choose)
	launch.tooltip_text="Preview local video with original alpha or optional green/blue keying, then add editable drawing holds."
func choose() -> void:
	if not phase.is_empty():app.message("Finish or cancel the current video import first.");return
	if not available():app.message("Choose Draw mode with room for another layer, drawing and frame.");return
	app.choose_file(import_title(),PackedStringArray(["*.mp4,*.mov,*.mkv,*.webm,*.avi ; Video artwork"]),begin)
func show_layers() -> void:
	phase="layers";review=ConfirmationDialog.new();review.title="Review video artwork";review.exclusive=false;review.get_ok_button().text="Prepare preview";app.add_child(review)
	var box:=VBoxContainer.new();review.add_child(box)
	var caption:=Label.new();caption.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;caption.custom_minimum_size.x=500;box.add_child(caption)
	caption.text="%s · %s × %s\nFit the complete video into the canvas, starting at frame %d. Original transparency is preserved. Audio is separate: use Import audio.\nThe complete range must fit the remaining scene frames and drawing capacity." % [source.get_file(),inventory.get("width",0),inventory.get("height",0),at]
	key_enabled=CheckButton.new();key_enabled.text="Remove a green or blue background";box.add_child(key_enabled)
	key_color=OptionButton.new();key_color.add_item("Green background");key_color.add_item("Blue background");box.add_child(key_color)
	similarity=app.spin(box,"Color tolerance",0.01,1,0.1);similarity.step=0.01;similarity.value=0.1
	softness=app.spin(box,"Edge softness",0,1,0.05);softness.step=0.01;softness.value=0.05
	review.confirmed.connect(prepare);review.canceled.connect(cancel);review.close_requested.connect(cancel);review.popup_centered(Vector2i(540,340))
func prepare() -> void:
	if phase!="layers" or not valid() or external_busy():fail("The scene changed or another operation is running. Import video again.");return
	similarity.apply();softness.apply()
	request={"source":source,"source_sha256":inventory.get("source_sha256"),"output":job.path_join("prepared"),"cancel":job.path_join("cancel"),"result":job.path_join("result.json"),"ffmpeg":app.encoder_path.text,"width":video.width,"height":video.height,"fps_num":video.fps_num,"fps_den":video.fps_den,"available_frames":int(video.duration_frames)-at,"max_cels":slots(),"chroma":{"enabled":key_enabled.button_pressed,"color":"00ff00" if key_color.selected==0 else "0000ff","similarity":similarity.value,"blend":softness.value}}
	var file:=FileAccess.open(job.path_join("request.json"),FileAccess.WRITE)
	if not file:fail("Cannot write video preparation request.");return
	file.store_string(JSON.stringify(request));file.close();review.hide();phase="prepare";response=request.result;last_stage="";start([job.path_join("request.json")],"Preparing video drawings…")
