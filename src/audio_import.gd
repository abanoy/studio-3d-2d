extends Node
const Audio=preload("res://src/audio_track.gd")
var app
var pid:=-1
var request:={}
var cancelled:=false
var session:=""
var revision:=0
var video:={}
var at:=0
var progress: AcceptDialog

func begin(path: String,start_frame: int) -> void:
	if pid>0:app.message("A sound is already being prepared. Finish or cancel it first.");return
	if app.exporting:return
	if OS.has_feature("web"):app.message("MP3/Ogg import is available in desktop Studio. Use PCM16 WAV in this web preview.");return
	if not path.get_extension().to_lower() in ["mp3","ogg"]:app.message("Choose a WAV, MP3 or Ogg audio file.");return
	if start_frame<0 or start_frame>=int(app.video.duration_frames):app.message("Choose a frame before the end of the movie for this sound.");return
	if app.audio_clips.size()>=Audio.MAX_CLIPS:app.message("This scene already has16 sound clips.");return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	session=app.recovery_session;revision=app.recovery_revision;video=app.video.duplicate(true);at=start_frame
	var folder:=ProjectSettings.globalize_path("res://output/audio-imports/%d-%d-%d" % [int(Time.get_unix_time_from_system()),OS.get_process_id(),Time.get_ticks_usec()])
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:app.message("Cannot create the sound preparation folder.");return
	request={"source":path,"output":folder.path_join("audio.wav"),"result":folder.path_join("result.json"),"cancel":folder.path_join("cancel"),"ffmpeg":app.encoder_path.text}
	var file:=FileAccess.open(folder.path_join("request.json"),FileAccess.WRITE)
	if not file:app.message("Cannot write the sound preparation request.");return
	file.store_string(JSON.stringify(request));file.close();cancelled=false
	pid=OS.create_process(app.source_import.python(),[ProjectSettings.globalize_path("res://tools/prepare_audio.py"),folder.path_join("request.json")],false)
	if pid<=0:app.message("Cannot start sound preparation. Check the desktop Python setting.");return
	progress=AcceptDialog.new();progress.title="Preparing sound";progress.dialog_text="Reading the sound for frame %d…\nYour original file stays unchanged." % at;progress.ok_button_text="Cancel";progress.exclusive=false
	app.add_child(progress);progress.confirmed.connect(cancel);progress.close_requested.connect(cancel);progress.popup_centered(Vector2i(460,150))
	app.message("Preparing sound…")

func cancel() -> void:
	if pid<=0:return
	var file:=FileAccess.open(request.cancel,FileAccess.WRITE)
	if not file:app.message("Cannot signal cancellation. Waiting for sound preparation to finish.");return
	file.store_string("cancel");file.close();cancelled=true
	if is_instance_valid(progress):progress.hide()
	app.message("Cancelling sound import…")

func _process(_delta: float) -> void:
	if pid<=0 or OS.is_process_running(pid):return
	pid=-1
	if is_instance_valid(progress):progress.queue_free()
	if cancelled:app.message("Sound import cancelled. No clip was added.");return
	if session!=app.recovery_session or revision!=app.recovery_revision or video!=app.video or app.exporting or app.playing:
		app.message("The scene changed during sound preparation. Add the sound again.");return
	var file:=FileAccess.open(request.result,FileAccess.READ)
	if not file or file.get_length()>16384:app.message("Sound preparation ended without a readable result.");return
	var result=JSON.parse_string(file.get_as_text())
	if not result is Dictionary:app.message("Cannot read sound preparation result.");return
	if not result.get("ok",false):app.message(str(result.get("error","Cannot prepare this sound.")));return
	if not result.get("path") is String or result.path.replace("\\","/").simplify_path()!=request.output.replace("\\","/").simplify_path() or FileAccess.get_sha256(request.output)!=result.get("sha256"):
		app.message("The prepared sound changed. Add the original sound again.");return
	var decoded:=Audio.read_wav(request.output)
	if decoded.has("error"):app.message(decoded.error);return
	decoded.name=str(result.get("source_name",request.source.get_file())).left(200)
	app.append_audio(decoded,at)

func _exit_tree() -> void:
	if pid>0:
		var file:=FileAccess.open(request.cancel,FileAccess.WRITE)
		if file:file.store_string("cancel");file.close()
	if is_instance_valid(progress):progress.queue_free()
