extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var folder: String
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func pcm_hash() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func begin_edge() -> void:
	var timeline=app.timeline
	var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=timeline.audio_end_handle(0).get_center()
	timeline._gui_input(click);assert(not timeline.trimming_audio.is_empty() and timeline.moving_audio.is_empty())
func move_edge(last: int) -> Vector2:
	var timeline=app.timeline;var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT
	# Deliberately outside the panel in Y: captured gestures use the app router.
	motion.position=timeline.get_global_transform()*Vector2(timeline.x(last+1),timeline.size.y+90)
	app._input(motion);return motion.position
func release(point: Vector2) -> void:
	var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.position=point;app._input(click)
func escape() -> void:
	var key:=InputEventKey.new();key.keycode=KEY_ESCAPE;key.pressed=true;app._input(key)
func run() -> void:
	folder=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	assert(app.import_audio(folder.path_join("voice.wav"),6).is_empty());app.audio_trim.value=100;app.apply_audio_settings()
	assert(app.import_audio(folder.path_join("peer.wav"),24).is_empty())
	var before: Dictionary=app.audio_document().duplicate(true);var history: int=app.history.size();var original_pcm:=pcm_hash();var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true)
	begin_edge();var point:=move_edge(17);await settle()
	assert(app.timeline.trim_preview==17 and is_equal_approx(app.timeline.audio_rect(0).end.x,app.timeline.x(18)))
	assert(app.audio_document()==before and app.history.size()==history and pcm_hash()==original_pcm)
	var checkpoint: int=app.checkpoint_revision;app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);assert(app.checkpoint_revision==checkpoint);app.recovery_checkpoint_requested=false
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("edge-preview.png"))
	escape();assert(not app.timeline.audio_gesture_active() and app.audio_document()==before and app.history.size()==history)
	begin_edge();point=move_edge(17);release(point);await settle()
	assert(app.audio_clips[0].source_out_sample==26460 and app.history.size()==history+1 and not app.timeline.audio_gesture_active())
	assert(app.audio_clips[1]==Audio.clips(before)[1] and app.current_world()==world and app.keys==keys)
	var trimmed: Dictionary=app.audio_document().duplicate(true);var mixed:=pcm_hash()
	app.undo();assert(app.audio_document()==before and pcm_hash()==original_pcm);app.redo();assert(app.audio_document()==trimmed and pcm_hash()==mixed)
	# No movement is not a trim. Extending clamps to full source, not the shot end.
	history=app.history.size();begin_edge();release(app.timeline.get_global_transform()*app.timeline.audio_end_handle(0).get_center());assert(app.history.size()==history)
	begin_edge();point=move_edge(200);assert(app.timeline.trim_preview==27);release(point);await settle()
	assert(not app.audio_clips[0].has("source_out_sample") and app.audio_document().format==Audio.FORMAT)
	app.undo();assert(app.audio_document()==trimmed)
	begin_edge();point=move_edge(-100);assert(app.timeline.trim_preview==6);release(point);await settle()
	assert(app.audio_clips[0].source_out_sample==6247 and app.audio_mix.pcm.decode_s16(14000*4)==0)
	app.undo();assert(app.audio_document()==trimmed and pcm_hash()==mixed)
	# Context invalidation, focus and right-click cancel all leave data/history alone.
	history=app.history.size();begin_edge();point=move_edge(11);app.changed();release(point);await settle()
	assert(app.audio_document()==trimmed and app.history.size()==history and "scene changed" in app.status.text)
	begin_edge();move_edge(11);app._notification(Window.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	assert(not app.timeline.audio_gesture_active() and app.audio_document()==trimmed)
	begin_edge();move_edge(11);app.timeline.release_focus()
	assert(not app.timeline.audio_gesture_active() and app.audio_document()==trimmed)
	begin_edge();move_edge(11);var right:=InputEventMouseButton.new();right.button_index=MOUSE_BUTTON_RIGHT;right.pressed=true;app._input(right)
	assert(not app.timeline.audio_gesture_active() and app.audio_document()==trimmed)
	begin_edge();move_edge(11);app.export_controls(app,true);assert(not app.timeline.audio_gesture_active());app.export_controls(app,false)
	assert(app.audio_document()==trimmed and app.history.size()==history)
	# Existing body dragging still retimes the complete shortened sound.
	var timeline=app.timeline;var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=timeline.audio_rect(0).position+Vector2(14,15);timeline._gui_input(click)
	assert(not timeline.moving_audio.is_empty() and timeline.trimming_audio.is_empty())
	var motion:=InputEventMouseMotion.new();motion.button_mask=MOUSE_BUTTON_MASK_LEFT;motion.position=timeline.get_global_transform()*(click.position+Vector2(timeline.x(6)-timeline.x(0),0));app._input(motion);release(motion.position);await settle()
	assert(app.audio_clips[0].start_frame==12 and app.audio_clips[0].source_out_sample==26460)
	app.undo();assert(app.audio_document()==trimmed and pcm_hash()==mixed)
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(70,70,Color.CYAN)
	app.set_frame(24);var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var saved:=folder.path_join("edge-trim.has");app.has_project.save_file(saved,"packed");await job();assert(app.has_project.path==saved)
	begin_edge();move_edge(11);app.has_project.open_file(saved);await job();assert(not app.timeline.audio_gesture_active() and pcm_hash()==mixed)
	begin_edge();move_edge(11);app.new_project();assert(not app.timeline.audio_gesture_active() and app.audio_clips.is_empty())
	app.has_project.open_file(saved);await job();assert(pcm_hash()==mixed and app.audio_clips[0].source_out_sample==26460)
	assert(await app.export_movie(folder)=="")
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data())
	var result:={"project":saved,"movie":app.last_export_folder.path_join("movie.mp4"),"preview_unchanged":true,"one_step_undo":true,"outside_release":true,"escape_focus_export_new_open_cancel":true,"stale_preserved":true,"extension_restores_legacy":true,"minimum_one_frame":true,"body_move_preserved":true,"pcm_reopened_exact":true,"pixels_exact":true}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("AUDIO_EDGE_SMOKE ",JSON.stringify(result));app.free();quit(0)
