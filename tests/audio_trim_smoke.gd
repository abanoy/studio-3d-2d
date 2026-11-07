extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
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
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var mode: String=args[1]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-"+mode);app.recent_path=folder.path_join("recents-"+mode+".json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-"+mode)
	if mode!="writer":await reader(mode);return
	assert(app.import_audio(folder.path_join("voice.wav"),6).is_empty())
	app.audio_trim.value=100;app.apply_audio_settings()
	var before: Dictionary=app.audio_document().duplicate(true);var history: int=app.history.size();var keys: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true)
	var editor=app.audio_trim_editor;editor.open();await settle()
	assert(editor.dialog.visible and not editor.dialog.exclusive and not app.advanced_mode)
	editor.last.value=6;editor.dialog.confirmed.emit();await settle()
	print("ONE_FRAME_TRIM ",JSON.stringify({"end_sample":app.audio_clip.source_out_sample,"last_frame":Audio.last_frame(app.audio_clip,app.video),"rect_end":app.timeline.audio_rect(0).end.x,"ruler_end":app.timeline.x(7)}))
	assert(app.audio_clip.source_out_sample==6247 and Audio.last_frame(app.audio_clip,app.video)==6)
	assert(is_equal_approx(app.timeline.audio_rect(0).end.x,app.timeline.x(7)))
	assert(app.audio_mix.pcm.decode_s16(14000*4)==0)
	app.undo();assert(app.audio_document()==before)
	editor.open();await settle()
	editor.last.value=17;await settle();app.get_viewport().get_texture().get_image().save_png(folder.path_join("trim-dialog.png"));editor.dialog.confirmed.emit();await settle()
	assert(app.audio_document().format==Audio.TRIM_FORMAT and app.audio_clip.source_out_sample==26460 and app.history.size()==history+1)
	assert(app.audio_clip.source.frames==88200 and app.audio_clip.source.pcm==before.source.pcm and app.audio_clip.source.sha256==before.source.sha256)
	assert(app.timeline.audio_rect(0).end.x==app.timeline.x(18))
	for i in range(96,256):assert(app.audio_mix.peaks[i]==0)
	assert(app.audio_mix.pcm.decode_s16(36000*4)==0)
	var trimmed: Dictionary=app.audio_document().duplicate(true);var trim_pcm:=pcm_hash()
	var unchanged_history: int=app.history.size();editor.open();editor.dialog.confirmed.emit();await settle()
	assert(app.audio_document()==trimmed and app.history.size()==unchanged_history)
	app.undo();assert(app.audio_document()==before);app.redo();assert(app.audio_document()==trimmed and pcm_hash()==trim_pcm)
	history=app.history.size();app.audio_trim.value=600;app.apply_audio_settings()
	assert(app.audio_document()==trimmed and app.history.size()==history and "before the sound's end" in app.status.text)
	app.refresh_audio_controls();editor.open();editor.dialog.canceled.emit();await settle();assert(app.audio_document()==trimmed and app.history.size()==history)
	editor.open();app.retime_audio(app.audio_clip.id,8,6);editor.dialog.confirmed.emit();await settle()
	assert("scene changed" in app.status.text.to_lower() and app.audio_clip.start_frame==8)
	app.undo();assert(app.audio_document()==trimmed)
	editor.open();editor.restore_end();await settle()
	assert(not app.audio_document().has("format") and not app.audio_clip.has("source_out_sample") and app.audio_clip.source_in_sample==4410)
	app.undo();assert(app.audio_document()==trimmed and pcm_hash()==trim_pcm)
	assert(app.import_audio(folder.path_join("peer.wav"),24).is_empty())
	assert(app.audio_document().format==Audio.TRIM_FORMAT and app.audio_clips.size()==2)
	var mixed:=pcm_hash();assert(app.keys==keys and app.current_world()==world)
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(70,70,Color.CYAN)
	app.set_frame(24);var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var packed:=folder.path_join("trimmed.has");app.has_project.save_file(packed,"packed");await job();assert(app.has_project.path==packed)
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await job();assert(app.has_project.path==linked)
	app.changed();app.autosave_tick(true)
	var recovery: String=app.recovery_root.path_join(app.recovery_session)
	assert(Recovery.read_json(recovery.path_join("project.json")).audio.format==Audio.TRIM_FORMAT)
	var lesson:=Store.new();lesson.root=folder.path_join("lessons");assert(lesson.save(app,"basic-pose","1234",1,false,"step_01"))
	var data:={"packed":packed,"linked":linked,"recovery":recovery,"audio":Audio.metadata(app.audio_document()),"mix":mixed}
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(data))
	for name in ["voice.wav","peer.wav"]:assert(DirAccess.rename_absolute(folder.path_join(name),folder.path_join(name+".held"))==OK)
	app.new_project();app.has_project.open_file(packed);await job()
	assert(pcm_hash()==mixed and app.audio_clips[0].source_out_sample==26460)
	for name in ["voice.wav","peer.wav"]:assert(DirAccess.rename_absolute(folder.path_join(name+".held"),folder.path_join(name))==OK)
	assert(await app.export_movie(folder)=="")
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data())
	var wav:=Audio.read_wav(app.last_export_folder.path_join("mixed_audio.wav"));assert(wav.pcm==app.audio_mix.pcm)
	var result:={"packed":packed,"linked":linked,"movie":app.last_export_folder.path_join("movie.mp4"),"end_sample":26460,"trimmed_frames":12,"pcm_reopened_exact":true,"pixels_exact":true,"undo_exact":true,"stale_preserved":true,"restore_end_legacy":true,"source_samples_preserved":true}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("AUDIO_TRIM_SMOKE ",JSON.stringify(result));app.free();quit(0)
func reader(mode: String) -> void:
	var expected:=Recovery.read_json(folder.path_join("expected.json"))
	if mode in ["packed","linked"]:app.has_project.open_file(expected[mode]);await job()
	elif mode=="recovery":assert(app.restore_checkpoint({"folder":expected.recovery,"manifest":"project.json"}))
	elif mode=="lesson":
		var store:=Store.new();store.root=folder.path_join("lessons");assert(store.load_snapshot(app,"basic-pose","1234","step_01"))
	assert(app.audio_clips.size()==2 and app.audio_document().format==Audio.TRIM_FORMAT and app.audio_clips[0].source_out_sample==26460)
	assert(Audio.metadata(app.audio_document())==expected.audio and pcm_hash()==expected.mix)
	print("AUDIO_TRIM_READ ",mode);app.free();quit(0)
