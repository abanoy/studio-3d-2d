extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
var app
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func pcm() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var mode: String=args[1] if args.size()>1 else "writer"
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if mode!="writer":
		var reference:=Recovery.read_json(folder.path_join("expected.json"))
		if mode in ["packed","linked"]:app.has_project.open_file(reference[mode]);await job()
		elif mode=="recovery":assert(app.restore_checkpoint({"folder":reference.recovery,"manifest":"project.json"}))
		elif mode=="lesson":
			var lesson:=Store.new();lesson.root=folder.path_join("lessons");assert(lesson.load_snapshot(app,"basic-pose","1234","step_01"))
		assert(app.audio_document().format==Audio.FADE_FORMAT and Audio.metadata(app.audio_document())==reference.audio and pcm()==reference.mix)
		print("AUDIO_FADE_READ ",mode);app.free();quit(0);return
	assert(app.import_audio(folder.path_join("voice.wav"),6).is_empty());assert(app.import_audio(folder.path_join("peer.wav"),24).is_empty());app.select_audio(0)
	var editor=app.audio_fade_editor;var before: Dictionary=app.audio_document().duplicate(true);var original:=pcm();var history: int=app.history.size();var world: Dictionary=app.current_world().duplicate(true);var keys: Array=app.keys.duplicate(true)
	editor.open();assert(editor.dialog.visible and not editor.dialog.exclusive and not app.advanced_mode);editor.fade_in.value=100;editor.fade_out.value=200
	assert(app.audio_document()==before and pcm()==original and app.history.size()==history)
	editor.dialog.canceled.emit();await settle();assert(app.audio_document()==before)
	editor.open();editor.apply();assert(app.history.size()==history)
	editor.open();editor.fade_in.value=100;editor.fade_out.value=200;editor.apply();await settle()
	assert(app.audio_document().format==Audio.FADE_FORMAT and app.audio_clips[0].fade_in_ms==100 and app.audio_clips[0].fade_out_ms==200 and app.history.size()==history+1 and pcm()!=original)
	assert(app.audio_clips[1]==Audio.clips(before)[1] and app.current_world()==world and app.keys==keys)
	var faded: Dictionary=app.audio_document().duplicate(true);var mix:=pcm();app.undo();assert(app.audio_document()==before and pcm()==original);app.redo();assert(app.audio_document()==faded and pcm()==mix)
	editor.open();editor.fade_in.value=500;app.changed();editor.apply();assert(app.audio_document()==faded and pcm()==mix and "scene changed" in app.status.text)
	editor.open();editor.fade_in.value=500;app.select_audio(1);editor.apply();assert(app.audio_document()==faded and pcm()==mix);app.select_audio(0)
	editor.open();editor.fade_in.value=0;editor.fade_out.value=0;editor.apply();assert(app.audio_document().format==Audio.FORMAT and pcm()==original);app.undo();assert(app.audio_document()==faded and pcm()==mix)
	# End trimming and source-in changes retain the requested fade durations.
	app.audio_trim_editor.open();app.audio_trim_editor.last.value=17;app.audio_trim_editor.apply();await settle();assert(app.audio_clips[0].source_out_sample==22050 and app.audio_clips[0].fade_out_ms==200)
	var final_audio: Dictionary=Audio.metadata(app.audio_document());var final_mix:=pcm();editor.open();await settle();app.get_viewport().get_texture().get_image().save_png(folder.path_join("fade-dialog.png"));editor.dialog.hide()
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(70,70,Color.CYAN);app.set_frame(24);var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var saved:=folder.path_join("faded.has");app.has_project.save_file(saved,"packed");await job();assert(app.has_project.path==saved)
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await job();assert(app.has_project.path==linked)
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovery: String=app.recovery_root.path_join(app.recovery_session)
	assert(Recovery.read_json(recovery.path_join("project.json")).audio.format==Audio.FADE_FORMAT)
	var store:=Store.new();store.root=folder.path_join("lessons");assert(store.save(app,"basic-pose","1234",1,false,"step_01"))
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"packed":saved,"linked":linked,"recovery":recovery,"audio":final_audio,"mix":final_mix}))
	for name in ["voice.wav","peer.wav"]:assert(DirAccess.rename_absolute(folder.path_join(name),folder.path_join(name+".held"))==OK)
	app.new_project();app.has_project.open_file(saved);await job()
	var reopened: Dictionary=Audio.metadata(app.audio_document())
	FileAccess.open(folder.path_join("roundtrip.json"),FileAccess.WRITE).store_string(JSON.stringify({"expected":final_audio,"actual":reopened,"expected_pcm":final_mix,"actual_pcm":pcm(),"status":app.status.text},"",true,true))
	# JSON stores numbers; Godot reads even integral JSON numbers as doubles.
	# Compare exact JSON values, with no numeric tolerance, plus exact PCM bytes.
	if JSON.parse_string(JSON.stringify(reopened))!=JSON.parse_string(JSON.stringify(final_audio)) or pcm()!=final_mix:
		push_error("Audio fade roundtrip mismatch: "+FileAccess.get_file_as_string(folder.path_join("roundtrip.json")));app.free();quit(1);return
	for name in ["voice.wav","peer.wav"]:assert(DirAccess.rename_absolute(folder.path_join(name+".held"),folder.path_join(name))==OK)
	assert(await app.export_movie(folder)=="");assert(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data())
	var result:={"project":saved,"movie":app.last_export_folder.path_join("movie.mp4"),"mix":final_mix,"metadata":final_audio,"undo_exact":true,"stale_preserved":true,"packed_pcm_exact":true,"pixels_exact":true}
	FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("AUDIO_FADE_SMOKE ",JSON.stringify(result));app.free();quit(0)
