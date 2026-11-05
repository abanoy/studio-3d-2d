extends Node
const Audio=preload("res://src/audio_track.gd")
var app
var dialog: ConfirmationDialog
var last: SpinBox
var before:={}
var video:={}
var session:=""
var revision:=0
var identity:=""

func open() -> void:
	if app.exporting or app.audio_clip.is_empty():return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	if is_instance_valid(dialog):dialog.queue_free()
	before=app.audio_document().duplicate(true);video=app.video.duplicate(true);session=app.recovery_session;revision=app.recovery_revision;identity=app.audio_clip.id
	var full: Dictionary=app.audio_clip.duplicate();full.erase("source_out_sample")
	dialog=ConfirmationDialog.new();dialog.title="Shorten sound";dialog.ok_button_text="Apply";dialog.exclusive=false
	var box:=VBoxContainer.new();dialog.add_child(box)
	app.label(box,app.audio_clip.source.name.left(100)+"\nStarts at frame %d. The last frame is included." % int(app.audio_clip.start_frame))
	var maximum:=mini(int(video.duration_frames)-1,Audio.last_frame(full,video))
	last=app.spin(box,"Last frame",int(app.audio_clip.start_frame),maximum,mini(maximum,Audio.last_frame(app.audio_clip,video)));last.step=1
	app.label(box,"Original samples stay available. Undo restores the previous end.")
	app.button(box,"Restore original end",restore_end)
	app.add_child(dialog);dialog.confirmed.connect(apply);dialog.canceled.connect(dialog.queue_free);dialog.popup_centered(Vector2i(520,240))

func valid() -> bool:
	return not app.exporting and session==app.recovery_session and revision==app.recovery_revision and video==app.video and app.audio_clip.get("id","")==identity and app.audio_document()==before

func commit(ending: int) -> void:
	if not valid():
		app.message("The sound or scene changed. Open Shorten sound again.")
		if is_instance_valid(dialog):dialog.queue_free()
		return
	if ending<=app.audio_clip.source_in_sample or ending>app.audio_clip.source.frames:
		app.message("Choose a sound end after its source trim and within the original sound.");return
	var restore_full: bool=ending==app.audio_clip.source.frames and app.audio_clip.has("source_out_sample")
	if ending==Audio.source_end(app.audio_clip) and not restore_full:
		app.message("Sound end unchanged.")
	else:
		if ending==app.audio_clip.source.frames:app.audio_clip.erase("source_out_sample")
		else:app.audio_clip["source_out_sample"]=ending
		app.commit_audio(before)
		app.message("Sound end updated. Undo restores its previous length.")
	if is_instance_valid(dialog):dialog.queue_free()

func apply() -> void:
	if not valid():commit(0);return
	var clip: Dictionary=app.audio_clip
	var endpoint:=Audio.end_at_frame(clip,int(last.value),video)
	if endpoint.has("error"):app.message(endpoint.error);return
	commit(endpoint.sample)

func drag_context(id: String) -> Dictionary:
	if app.exporting or app.audio_clip.get("id","")!=id:return {}
	app.stop();app.finish_stroke();app.pose_editor.finish_drag()
	app.message("Drag the sound's end. Release to apply; Escape cancels.")
	return {"session":app.recovery_session,"revision":app.recovery_revision,"video":app.video.duplicate(true),"before":app.audio_document().duplicate(true),"id":id}

func apply_drag(id: String,ending_frame: int,context: Dictionary) -> void:
	if app.exporting or context.get("id","")!=id or context.get("session","")!=app.recovery_session or context.get("revision",-1)!=app.recovery_revision or context.get("video",{})!=app.video or context.get("before",{})!=app.audio_document():
		app.message("The sound or scene changed. Drag its end again.");return
	for index in range(app.audio_clips.size()):
		var clip: Dictionary=app.audio_clips[index]
		if clip.id!=id:continue
		var endpoint:=Audio.end_at_frame(clip,ending_frame,app.video)
		if endpoint.has("error"):app.message(endpoint.error);return
		if endpoint.sample==Audio.source_end(clip):return
		app.selected_audio=index
		if endpoint.sample==clip.source.frames:clip.erase("source_out_sample")
		else:clip["source_out_sample"]=endpoint.sample
		app.commit_audio(context.before,id)
		app.message("Sound end moved. Undo restores its previous length.")
		return

func restore_end() -> void:
	commit(int(app.audio_clip.source.frames) if valid() else 0)

func _exit_tree() -> void:
	if is_instance_valid(dialog):dialog.queue_free()
