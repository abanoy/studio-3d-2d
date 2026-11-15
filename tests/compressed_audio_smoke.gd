extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
var app
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func audio_job() -> void:
	while app.audio_importer.pid>0:await process_frame
	await settle()
func has_job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func pcm_hash() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");app.display_prefs_path=folder.path_join("prefs.cfg");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	var keys: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true)
	assert(app.import_audio(folder.path_join("base.wav")).is_empty())
	var before: Dictionary=app.audio_document().duplicate(true);var history: int=app.history.size()
	app.set_frame(12);app.choose_audio_at_playhead()
	var picker: FileDialog
	for child in app.get_children():
		if child is FileDialog and child.visible:picker=child
	assert(is_instance_valid(picker) and "frame 12" in picker.title and "*.mp3" in picker.filters and "*.ogg" in picker.filters)
	picker.file_selected.emit(folder.path_join("Voice — тест.mp3"))
	assert(app.audio_importer.pid>0 and is_instance_valid(app.audio_importer.progress) and not app.audio_importer.progress.exclusive)
	app.set_frame(18) # Placement remains the frame captured when the picker opened.
	await audio_job()
	assert(app.audio_clips.size()==2 and app.audio_clip.start_frame==12 and app.history.size()==history+1,app.status.text)
	assert(app.audio_clip.source.name=="Voice — тест.mp3" and app.audio_clip.source.path.ends_with("audio.wav") and app.audio_clip.source.rate==48000 and app.audio_clip.source.channels==1)
	var voice_pcm:=pcm_hash();app.undo();assert(app.audio_document()==before);app.redo();assert(pcm_hash()==voice_pcm)
	app.set_frame(24);app.import_audio_dialog(folder.path_join("Effect.ogg"));await audio_job()
	assert(app.audio_clips.size()==3 and app.audio_clip.start_frame==24 and app.audio_clip.source.name=="Effect.ogg" and app.audio_clip.source.channels==2,app.status.text)
	assert(app.keys==keys and app.current_world()==world)
	var mixed:=pcm_hash();history=app.history.size();var saved: Dictionary=app.audio_document().duplicate(true)
	app.audio_importer.begin(folder.path_join("Voice — тест.mp3"),0);app.audio_importer.cancel();await audio_job()
	assert("cancelled" in app.status.text and app.audio_document()==saved and app.history.size()==history and pcm_hash()==mixed)
	var encoder: String=app.encoder_path.text
	app.encoder_path.text=folder.path_join("missing-ffmpeg.exe")
	app.audio_importer.begin(folder.path_join("Effect.ogg"),0);await audio_job()
	assert("FFmpeg is unavailable" in app.status.text and app.audio_document()==saved and app.history.size()==history)
	app.encoder_path.text=encoder
	app.audio_importer.begin(folder.path_join("Effect.ogg"),0);app.changed();await audio_job()
	assert("scene changed" in app.status.text.to_lower() and app.audio_document()==saved and app.history.size()==history)
	app.audio_importer.begin(folder.path_join("broken.mp3"),0);await audio_job()
	assert("Cannot decode" in app.status.text and app.audio_document()==saved and app.history.size()==history)
	app.audio_importer.begin(folder.path_join("Effect.ogg"),0);await audio_job()
	assert(app.audio_clips.size()==4 and app.history.size()==history+1)
	app.undo();assert(app.audio_document()==saved and pcm_hash()==mixed)
	# Actual AudioStreamPlayer output, captured and muted after effects.
	var bus:=AudioServer.bus_count;AudioServer.add_bus();AudioServer.set_bus_name(bus,"CompressedAudioCapture")
	var capture:=AudioEffectCapture.new();capture.buffer_length=1;AudioServer.add_bus_effect(bus,capture);AudioServer.set_bus_mute(bus,true);app.audio_player.bus="CompressedAudioCapture"
	app.video.duration_frames=240;app.rebuild_audio();app.set_frame(12);app.toggle_play()
	var until:=Time.get_ticks_usec()+120000;var frames:=0
	while Time.get_ticks_usec()<until or frames<3:await RenderingServer.frame_post_draw;frames+=1
	var samples:=capture.get_buffer(capture.get_frames_available());var peak:=0.
	for sample in samples:peak=maxf(peak,maxf(absf(sample.x),absf(sample.y)))
	var dummy:=AudioServer.get_driver_name()=="Dummy"
	assert((dummy and not app.audio_clock) or (not dummy and app.audio_clock and peak>.1))
	app.stop();app.audio_player.bus="Master";app.video.duration_frames=48;app.rebuild_audio();app.set_frame(24)
	assert(pcm_hash()==mixed)
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(90,90,Color.CYAN)
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var packed:=folder.path_join("compressed.has");app.has_project.save_file(packed,"packed");await has_job();assert(app.has_project.path==packed)
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await has_job();assert(app.has_project.path==linked)
	var sources: Array=[]
	for clip in app.audio_clips:
		var path: String=clip.source.path;sources.append(path);assert(DirAccess.rename_absolute(path,path+".held")==OK)
	app.new_project();app.has_project.open_file(packed);await has_job()
	assert(app.audio_clips.size()==3 and pcm_hash()==mixed and app.audio_clips[1].source.name=="Voice — тест.mp3")
	assert((await app.renderer.capture(app.keys,app.layers,24,true)).get_data()==expected.get_data())
	# Original WAV remains linked externally. Generated normalized sounds must
	# use stable HAS sidecars, without depending on disposable decode-job folders.
	assert(DirAccess.rename_absolute(sources[0]+".held",sources[0])==OK)
	app.new_project();app.has_project.open_file(linked);await has_job()
	assert(app.audio_clips.size()==3 and pcm_hash()==mixed)
	for path in sources.slice(1):assert(DirAccess.rename_absolute(path+".held",path)==OK)
	assert(await app.export_movie(folder)=="")
	assert(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data())
	var result:={"clips":3,"packed":packed,"linked":linked,"movie":app.last_export_folder.path_join("movie.mp4"),"pixels_exact":true,"pcm_reopened_exact":true,"undo_exact":true,"cancel_preserved":true,"stale_preserved":true,"missing_decoder_preserved":true,"bad_input_preserved":true,"retry_succeeded":true,"source_frames":[app.audio_clips[0].source.frames,app.audio_clips[1].source.frames,app.audio_clips[2].source.frames],"driver":AudioServer.get_driver_name(),"hardware_peak":peak}
	FileAccess.open(folder.path_join("app-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result))
	print("COMPRESSED_AUDIO ",JSON.stringify(result));app.free();quit(0)
