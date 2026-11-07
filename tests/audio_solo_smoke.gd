extends "res://tests/shortcut_editor_smoke.gd"
const Audio=preload("res://src/audio_track.gd")
func pcm_hash() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func silent() -> bool:
	for value in app.audio_mix.pcm:
		if value!=0:return false
	return true
func button_named(node: Node,text: String) -> Button:
	if node is Button and node.text==text:return node
	for child in node.get_children():
		var found:=button_named(child,text)
		if found:return found
	return null
func click_solo() -> void:
	await settle();app.inspector_scroll.ensure_control_visible(app.audio_solo);await settle();await click(app.audio_solo)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var mode: String=args[1] if args.size()>1 else "writer"
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join(mode+"-prefs.cfg");app.recovery_root=folder.path_join(mode+"-recovery");app.recent_path=folder.path_join(mode+"-recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join(mode+"-cache")
	if mode!="writer":
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		if mode=="recovery":check(app.restore_checkpoint({"folder":expected.recovery,"manifest":"project.json"}),"actual checkpoint restores a solo scene")
		else:app.has_project.open_file(expected[mode]);await wait_job()
		check(Audio.metadata(app.audio_document())==expected.audio and app.audio_document().format==Audio.SOLO_FORMAT,"cold reader preserves solo, fades, trim and independent peer settings")
		check(pcm_hash()==expected.pcm,"cold reader rebuilds exactly the same isolated preview/export PCM")
		app.select_audio(0);await settle();check(app.audio_solo.button_pressed and not app.audio_mute.button_pressed,"selected clip displays its saved Solo state")
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.paint,"solo persistence keeps independent editable drawing")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,6,true))==expected.render,"cold visual output remains exactly equal to writer")
		app.audio_solo.button_pressed=false;check(app.audio_document().get("format")==Audio.FADE_FORMAT and pcm_hash()!=expected.pcm,"turning Solo off in a cold scene restores peer and child sound")
		app.undo();check(pcm_hash()==expected.pcm and app.audio_solo.button_pressed,"cold Solo Undo restores exact mix and checkbox")
		print("AUDIO_SOLO_READ ",JSON.stringify({"checks":checks,"failures":failures,"mode":mode}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original animated environment loads")
	var world_source: String=app.source;var world_sha:=FileAccess.get_sha256(world_source)
	var child: String=app.sequence_editor.new_sequence("Child sound")
	check(not child.is_empty() and app.sequence_editor.enter(child).is_empty(),"ordinary editable child scene opens")
	check(app.import_audio(folder.path_join("nested.wav"),0).is_empty(),"independent child sound imports")
	app.sequence_editor.return_to_parent();check(app.sequence_editor.add_instance(child).is_empty(),"child sound instance joins the parent timeline")
	check(app.import_audio(folder.path_join("voice.wav"),0).is_empty() and app.import_audio(folder.path_join("peer.wav"),0).is_empty(),"two independent parent sound clips import")
	app.select_audio(0);app.set_advanced(false);await settle();app.history.clear();app.redo_history.clear();app.history_bytes=0
	var baseline:=pcm_hash();var before: Dictionary=app.audio_document().duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true);var child_audio: Dictionary=app.sequence_editor.asset(child).scene.audio.duplicate(true)
	var voice_only: Dictionary=Audio.mix_document(Audio.document([app.audio_clips[0]]),app.video)
	await click_solo();check(app.audio_solo.button_pressed and app.audio_document().format==Audio.SOLO_FORMAT and app.history.size()==1,"actual Simple Solo click authors one versioned undoable setting")
	check(app.audio_mix.pcm==voice_only.pcm and pcm_hash()!=baseline,"preview isolates the selected voice and suppresses peer plus child sound")
	check(not app.audio_clips[1].muted and not app.audio_clips[1].has("solo") and app.sequence_editor.asset(child).scene.audio==child_audio,"solo changes no peer mute flags or child content")
	await settle();app.inspector_scroll.ensure_control_visible(app.audio_mute);await settle();await click(app.audio_mute);check(silent() and app.audio_clips[0].solo and app.audio_clips[0].muted,"actual Mute still silences a soloed clip")
	app.undo();check(app.audio_mix.pcm==voice_only.pcm and not app.audio_mute.button_pressed,"Mute Undo restores exact isolated voice")
	app.undo();check(app.audio_document()==before and pcm_hash()==baseline and not app.audio_solo.button_pressed,"Solo Undo restores exact original parent and child mix")
	app.redo();check(app.audio_mix.pcm==voice_only.pcm and app.audio_solo.button_pressed,"Solo Redo restores exact isolated voice")
	app.select_audio(1);await click_solo();var parent_only: Dictionary=Audio.mix_document(app.audio_document(),app.video)
	check(app.audio_clips[0].solo and app.audio_clips[1].solo and app.audio_mix.pcm==parent_only.pcm and app.audio_mix.pcm!=voice_only.pcm,"two actual Solo controls play both parent clips without child sound")
	app.undo();app.select_audio(0);check(app.audio_mix.pcm==voice_only.pcm and not app.audio_clips[1].has("solo"),"second Solo Undo restores first isolated clip")
	await click_solo();check(app.audio_document()==before and pcm_hash()==baseline,"clearing the last Solo restores the exact previous mix and legacy format")
	app.undo();app.select_audio(0);app.set_advanced(true);await settle();app.audio_gain.value=-6;var apply_audio:=button_named(app,"Apply audio settings");app.inspector_scroll.ensure_control_visible(apply_audio);await settle();await click(apply_audio)
	check(app.audio_clips[0].gain_db==-6 and app.audio_clips[1].gain_db==0 and app.audio_clips[0].solo,"gain changes only the selected soloed clip")
	app.audio_fade_editor.open();app.audio_fade_editor.fade_in.value=100;app.audio_fade_editor.fade_out.value=100;app.audio_fade_editor.apply();await settle()
	app.audio_trim_editor.open();app.audio_trim_editor.last.value=17;app.audio_trim_editor.apply();await settle()
	check(app.audio_document().format==Audio.SOLO_FORMAT and app.audio_clips[0].fade_in_ms==100 and app.audio_clips[0].source_out_sample==33075,"solo coexists with authored gain/fades/end trim")
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,90,60),Color.CYAN);Drawing.insert(app.layers[1],0,48,image);app.changed();var paint:=Storage.image_hash(image)
	check(app.current_world()==world and app.keys==shots and FileAccess.get_sha256(world_source)==world_sha,"sound isolation and edits preserve world, camera and original environment")
	var packed:=folder.path_join("Solo.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"ordinary packed HAS saves Solo with its dependencies")
	var linked:=folder.path_join("Solo linked.has");app.has_project.save_file(linked,"linked");await wait_job();check(app.has_project.path==linked,"ordinary linked HAS saves the same Solo intent")
	app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var recovery: String=app.recovery_root.path_join(app.recovery_session)
	check(app.checkpoint_revision==app.recovery_revision,"ordinary recovery protects Solo and child scene content")
	var audio: Dictionary=Audio.metadata(app.audio_document());var expected_pcm:=pcm_hash();app.set_frame(6);var picture: Image=await app.renderer.capture(app.keys,app.layers,6,true);var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000007.png")).get_data()==picture.get_data(),"actual movie uses identical solo-scene visual input")
	var file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"audio":audio,"pcm":expected_pcm,"paint":paint,"render":Storage.image_hash(picture),"packed":packed,"linked":linked,"recovery":recovery},"",true,true));file.close()
	print("AUDIO_SOLO_WRITE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));app.free();quit(0 if failures==0 else 1)
