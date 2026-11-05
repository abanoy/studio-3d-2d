extends Node
const Timing=preload("res://src/video_timing.gd")
const Audio=preload("res://src/audio_track.gd")
const World=preload("res://src/world_document.gd")
var app
var choices: OptionButton
var duration: SpinBox
var displayed_duration:=-1
var duration_session:=""
func setup(parent: Node) -> void:
	app.label(parent,"Project frame rate")
	choices=OptionButton.new();parent.add_child(choices)
	for pair in Timing.PRESETS:
		choices.add_item(Timing.label(pair[0],pair[1])+" fps"+(" (%d/%d)" % pair if pair[1]!=1 else ""))
	choices.item_selected.connect(func(index):
		if index>=0 and index<Timing.PRESETS.size():apply_values(Timing.PRESETS[index][0],Timing.PRESETS[index][1]))
	var note: Label=app.label(parent,"Frame numbers stay fixed. Changing rate changes playback speed. Sound starts stay on their frames; original audio samples stay unchanged.")
	note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;note.custom_minimum_size.x=480
	duration=app.spin(parent,"Scene length (frames)",1,240,48)
	app.button(parent,"Apply scene length",func():apply_duration(duration.value))
	var length_note: Label=app.label(parent,"Up to 240 frames. Keys and drawings keep their timing. Shortening refuses content beyond the new end; sound tails stop at the scene end.")
	length_note.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;length_note.custom_minimum_size.x=480
	sync()
func sync() -> void:
	if not choices:return
	var index:=Timing.preset_index(app.video)
	if index<0:
		index=Timing.PRESETS.size()
		var caption:="Current: %s fps (%d/%d)" % [Timing.label(app.video.fps_num,app.video.fps_den),app.video.fps_num,app.video.fps_den]
		if choices.item_count==index:choices.add_item(caption)
		else:choices.set_item_text(index,caption)
	else:
		while choices.item_count>Timing.PRESETS.size():choices.remove_item(choices.item_count-1)
	if choices.selected!=index:choices.select(index)
	if duration and (displayed_duration!=int(app.video.duration_frames) or duration_session!=app.recovery_session):
		displayed_duration=int(app.video.duration_frames);duration_session=app.recovery_session
		duration.set_value_no_signal(displayed_duration)

func apply_duration(value) -> String:
	var error:=""
	if app.exporting:error="Wait for export to finish."
	elif not Timing.whole(value,240):error="Scene length must be 1–240 whole frames."
	elif duration_session!=app.recovery_session:error="The scene changed. Review its length and try again."
	elif int(value)==int(app.video.duration_frames):sync();return ""
	elif app.physics_editor.recording and app.physics_editor.recording.active:error="Finish or cancel recording before changing scene length."
	if error.is_empty() and value<app.video.duration_frames:error=shorten_error(int(value))
	if not error.is_empty():app.message(error);sync();return error
	var proposed: Dictionary=app.video.duplicate(true);proposed.duration_frames=int(value)
	return commit(proposed,"Scene length: %d frames. Existing timing kept." % int(value))

func shorten_error(frames: int) -> String:
	for key in app.keys:
		if key.frame>frames:return "Move or remove camera keys beyond frame %d before shortening." % frames
	for layer in app.layers:
		for cel in layer.cels:
			if cel.start+cel.duration>frames:return "Shorten or move drawings in %s before shortening the scene." % layer.name
	for clip in app.audio_clips:
		if clip.start_frame>=frames:return "Move or remove sounds starting at frame %d or later before shortening." % frames
	var error:=World.validate(app.current_world(),frames)
	if not error.is_empty():return "Move or shorten object/effect animation before shortening the scene. "+error
	return ""
func apply_values(numerator,denominator) -> String:
	if app.exporting:sync();return "Wait for export to finish."
	var error:=Timing.error(numerator,denominator)
	if not error.is_empty():app.message(error);sync();return error
	if app.video.fps_num==numerator and app.video.fps_den==denominator:sync();return ""
	if app.physics_editor.recording and app.physics_editor.recording.active:
		error="Finish or cancel recording before changing frame rate.";app.message(error);sync();return error
	var proposed: Dictionary=app.video.duplicate(true);proposed.fps_num=int(numerator);proposed.fps_den=int(denominator)
	return commit(proposed,"Frame rate: %s fps. Frame numbers kept; audio mix updated." % Timing.label(numerator,denominator))

func commit(proposed: Dictionary,feedback: String) -> String:
	# Defer until an edit finishes: committing a pending pose after range validation
	# could introduce a key beyond the candidate end.
	if app.drawing or app.pose_editor.dragging or app.timeline.dragging or not app.timeline.moving_id.is_empty() or app.timeline.audio_gesture_active():
		var error:="Finish or cancel the current edit before changing project timing.";app.message(error);sync();return error
	var mixed: Dictionary={} if app.audio_clip.is_empty() else Audio.mix_document(app.audio_document(),proposed)
	if mixed.has("error"):app.message(mixed.error);sync();return mixed.error
	app.stop();app.finish_stroke();app.pose_editor.finish_drag();app.release_mouse()
	app.timeline.finish_move(true);app.timeline.cancel_audio()
	var before: Dictionary=app.video.duplicate(true);var view: Dictionary=app.renderer.view_state()
	app.video=proposed;app.audio_mix=mixed;app.renderer.video_settings=proposed
	app.push_history({"type":"video","before":before,"after":proposed.duplicate(true)})
	app.changed();app.set_frame(app.frame);app.refresh_audio_controls();app.renderer.restore_view(view);sync()
	app.message(feedback);return ""
