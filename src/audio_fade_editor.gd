extends Node
const Audio=preload("res://src/audio_track.gd")
var app
var dialog: ConfirmationDialog
var fade_in: SpinBox
var fade_out: SpinBox
var before:={}
var video:={}
var session:=""
var revision:=0
var identity:=""
func open() -> void:
	if app.exporting or app.audio_clip.is_empty():return
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.timeline.cancel_audio()
	if is_instance_valid(dialog):dialog.queue_free()
	before=app.audio_document().duplicate(true);video=app.video.duplicate(true);session=app.recovery_session;revision=app.recovery_revision;identity=app.audio_clip.id
	dialog=ConfirmationDialog.new();dialog.title="Fade sound";dialog.ok_button_text="Apply";dialog.exclusive=false
	var box:=VBoxContainer.new();dialog.add_child(box)
	app.label(box,app.audio_clip.source.name.left(100))
	fade_in=app.spin(box,"Fade in (milliseconds)",0,60000,int(app.audio_clip.get("fade_in_ms",0)));fade_in.step=1
	fade_out=app.spin(box,"Fade out (milliseconds)",0,60000,int(app.audio_clip.get("fade_out_ms",0)));fade_out.step=1
	app.label(box,"0 turns a fade off. Long fades fit the available sound.\nOriginal samples stay unchanged. Undo restores the previous fades.")
	app.button(box,"Remove fades",func():fade_in.value=0;fade_out.value=0;apply())
	app.add_child(dialog);dialog.confirmed.connect(apply);dialog.canceled.connect(dialog.queue_free);dialog.popup_centered(Vector2i(550,260))
func valid() -> bool:
	return not app.exporting and session==app.recovery_session and revision==app.recovery_revision and video==app.video and app.audio_clip.get("id","")==identity and app.audio_document()==before
func apply() -> void:
	if not valid():
		app.message("The sound or scene changed. Open Fade sound again.")
		if is_instance_valid(dialog):dialog.queue_free()
		return
	var values:={"fade_in_ms":int(fade_in.value),"fade_out_ms":int(fade_out.value)}
	var proposed: Dictionary=app.audio_clip.duplicate()
	for field in values:
		if values[field]==0:proposed.erase(field)
		else:proposed[field]=values[field]
	var error:=Audio.clip_error(proposed,video)
	if not error.is_empty():app.message(error);return
	if proposed==app.audio_clip:app.message("Sound fades unchanged.")
	else:
		for field in values:
			if proposed.has(field):app.audio_clip[field]=proposed[field]
			else:app.audio_clip.erase(field)
		app.commit_audio(before);app.message("Sound fades updated. Undo restores the previous fades.")
	if is_instance_valid(dialog):dialog.queue_free()
func _exit_tree() -> void:
	if is_instance_valid(dialog):dialog.queue_free()
