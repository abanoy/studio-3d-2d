extends SceneTree
const Audio=preload("res://src/audio_track.gd")
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
var app
var checks:=0
var failures:=0
var folder: String
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Multiple audio watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settled() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settled()
func same(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func pcm_hash() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func audio_rows() -> Array:
	var rows:=[]
	for clip in app.audio_clips:rows.append({"id":clip.id,"sha256":clip.source.sha256,"start_frame":clip.start_frame,"source_in_sample":clip.source_in_sample,"gain_db":clip.gain_db,"muted":clip.muted})
	return rows
func write(name: String,value: Dictionary) -> void:
	var file:=FileAccess.open(folder.path_join(name),FileAccess.WRITE);file.store_string(JSON.stringify(value,"",true,true));file.close()
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var mode: String=args[1]
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-"+mode);app.recent_path=folder.path_join("recents-"+mode+".json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-"+mode)
	if mode!="writer":await reader(mode);return
	app.has_project.open_file(args[2]);await job()
	check(app.current_world().objects.size()==7,"actual five-native world/group/map is available for audio integration")
	app.audio_clip={};app.rebuild_audio()
	var world: Dictionary=World.portable(app.current_world());var shots: Array=app.keys.duplicate(true);var paint: String=Storage.image_hash(app.layers[1].cels[0].image)
	app.set_frame(18)
	for name in ["Voice — тест.wav","Music.wav","Effect.wav"]:
		app.import_audio_dialog(folder.path_join("inputs/"+name));await settled()
	check(app.audio_clips.all(func(clip):return clip.start_frame==18),"new sounds begin at the playhead in one import")
	app.set_frame(int(app.video.duration_frames));app.import_audio_dialog(folder.path_join("inputs/Effect.wav"))
	check(app.audio_clips.size()==3,"end boundary refuses a sound that could never play")
	app.set_frame(18)
	check(app.audio_clips.size()==3 and app.audio_choice.visible and not app.advanced_mode,"normal Add audio appends three selectable sounds in Simple without replacement prompts")
	if app.audio_clips.size()!=3:app.free();quit(1);return
	app.audio_choice.item_selected.emit(0);app.audio_start.value=24;app.audio_gain.value=-6;app.apply_audio_settings()
	app.audio_choice.item_selected.emit(1);app.audio_start.value=0;app.audio_gain.value=-12;app.apply_audio_settings()
	app.audio_choice.item_selected.emit(2);app.audio_start.value=12;app.audio_gain.value=-9;app.audio_trim.value=50;app.apply_audio_settings()
	check(app.audio_clip.id==app.audio_clips[2].id and app.audio_clips[0].start_frame==24 and app.audio_clips[1].gain_db==-12 and app.audio_clips[2].source_in_sample==2400,"clip chooser edits only selected timing/trim/gain while peers retain settings")
	check(same(World.portable(app.current_world()),world) and app.keys==shots and Storage.image_hash(app.layers[1].cels[0].image)==paint,"audio authoring preserves every native object, camera key and independent drawing")
	var mixed:=pcm_hash();app.audio_mute.button_pressed=true
	check(app.audio_clips[2].muted and not app.audio_clips[0].muted and pcm_hash()!=mixed,"mute affects only the selected sound")
	app.undo();check(pcm_hash()==mixed and app.audio_clips.size()==3,"mute Undo restores the complete mix and all three clips")
	app.audio_choice.item_selected.emit(2);var removed: String=app.audio_clip.id;app.remove_audio()
	check(app.audio_clips.size()==2 and app.audio_clips[0].start_frame==24,"Simple Remove removes only one clip")
	app.undo();check(app.audio_clips.size()==3 and app.audio_clips[2].id==removed and pcm_hash()==mixed,"Remove Undo restores exact independent clip identity and PCM")
	app.redo();check(app.audio_clips.size()==2,"Remove Redo keeps peer clips");app.undo()
	var timeline=app.timeline;await settled();var click:=InputEventMouseButton.new();click.button_index=MOUSE_BUTTON_LEFT;click.pressed=true;click.position=timeline.audio_rect(1).position+Vector2(20,14)
	var history: int=app.history.size();timeline._gui_input(click)
	var drag:=InputEventMouseMotion.new();drag.position=timeline.get_global_transform()*(click.position+Vector2(timeline.x(6)-timeline.x(0),0));drag.button_mask=MOUSE_BUTTON_MASK_LEFT;app._input(drag)
	check(app.audio_clips[1].start_frame==0 and app.history.size()==history,"drag previews audio timing without creating intermediate history or changing the mix")
	click.pressed=false;click.position=drag.position;app._input(click);await settled()
	check(app.audio_clips[1].start_frame==6 and app.history.size()==history+1 and app.audio_clips[0].start_frame==24,"actual audio block drag commits one timing Undo and preserves peers")
	app.undo();check(app.audio_clips[1].start_frame==0 and pcm_hash()==mixed,"audio drag Undo restores exact previous combined samples");app.redo()
	# Escape cancels a different tentative drag without editing any clip.
	click.pressed=true;click.position=timeline.audio_rect(1).position+Vector2(20,14);timeline._gui_input(click);drag.position=click.position+Vector2(50,0);timeline._gui_input(drag)
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;history=app.history.size();app._input(escape)
	check(timeline.moving_audio.is_empty() and app.audio_clips[1].start_frame==6 and app.history.size()==history,"Escape cancels tentative audio timing with no history")
	check(timeline.audio_clips.size()==3 and timeline.clip_waveforms.size()==3 and timeline.custom_minimum_size.y>=timeline.audio_y()+90,"all three sound rows have independent waveforms in the scrollable master timeline")
	var bus:=AudioServer.bus_count;AudioServer.add_bus();AudioServer.set_bus_name(bus,"MultipleSoundCapture")
	var capture:=AudioEffectCapture.new();capture.buffer_length=1;AudioServer.add_bus_effect(bus,capture);AudioServer.set_bus_mute(bus,true);app.audio_player.bus="MultipleSoundCapture"
	# Longer transport fixture avoids consuming the short film on a busy GPU.
	app.video.duration_frames=240;app.rebuild_audio();app.set_frame(24);app.toggle_play()
	var until:=Time.get_ticks_usec()+160000;var frames:=0
	while Time.get_ticks_usec()<until or frames<3:await RenderingServer.frame_post_draw;frames+=1
	var samples:=capture.get_buffer(capture.get_frames_available());var peak:=0.0
	for sample in samples:peak=maxf(peak,maxf(absf(sample.x),absf(sample.y)))
	var dummy:=AudioServer.get_driver_name()=="Dummy"
	check((dummy and not app.audio_clock) or (not dummy and app.audio_clock and peak>.08),"actual multi-sound player emits captured samples with hardware clock or explicit Dummy fallback")
	check(app.playing and app.frame>24 and absi(app.frame-floori(app.preview_sample_seconds*24))<=1,"multi-sound preview follows the same master audio clock")
	app.stop();app.audio_player.stream=null;app.audio_player.bus="Master";AudioServer.remove_bus(bus);capture=null
	app.video.duration_frames=48;app.rebuild_audio()
	app.set_frame(24);app.world_selection.clear();var image: Image=await app.renderer.capture(app.keys,app.layers,24,true);image.save_png(folder.path_join("reference.png"))
	var packed:=folder.path_join("Multiple sounds.has");app.has_project.save_file(packed,"packed");await job()
	check(app.has_project.path==packed and not app.dirty,"ordinary packed HAS saves all sound clips")
	var inputs:=folder.path_join("inputs");var held:=folder.path_join("inputs-held")
	check(DirAccess.rename_absolute(inputs,held)==OK,"only fresh test WAV inputs move away before packed Open")
	app.has_project.open_file(packed);await job()
	check(app.audio_clips.size()==3 and app.audio_clips[2].source_in_sample==2400,"packed Open restores every sound after original WAV paths disappear")
	var expected:=audio_rows();mixed=pcm_hash()
	var linked:=folder.path_join("Linked sounds.has");app.has_project.save_file(linked,"linked");await job()
	check(app.has_project.path==linked and DirAccess.dir_exists_absolute(folder.path_join("Linked sounds.assets")),"linked save externalizes managed audio to stable checksum sidecars")
	app.changed();app.autosave_tick(true)
	var recovery: String=app.recovery_root.path_join(app.recovery_session)
	check(not Recovery.read_json(recovery.path_join("project.json")).is_empty(),"ordinary quiet recovery checkpoints the audio collection")
	var lesson:=Store.new();lesson.root=folder.path_join("lessons")
	check(lesson.save(app,"basic-pose","1234",1,false,"step_01"),"ordinary lesson snapshot retains the complete multi-sound scene")
	app.set_frame(24);var own_preview: Image=await app.renderer.capture(app.keys,app.layers,24,true);own_preview.save_png(folder.path_join("reopened-preview.png"))
	var error: String=await app.export_movie(folder)
	check(error.is_empty() and Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==own_preview.get_data(),"multi-sound movie preserves exact reopened native/camera/drawing preview pixels")
	var wav:=Audio.read_wav(app.last_export_folder.path_join("mixed_audio.wav"))
	check(not wav.has("error") and wav.pcm==app.audio_mix.pcm,"encoder input WAV is exactly the same combined PCM as preview")
	app.timeline.get_parent().scroll_vertical=int(app.timeline.audio_y());app.select_audio(1);await settled();root.get_texture().get_image().save_png(folder.path_join("editor.png"))
	write("expected.json",{"world":world,"keys":shots,"paint":paint,"audio":expected,"mix":mixed,"packed":packed,"linked":linked,"recovery":recovery})
	var report:={"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4"),"mixed_wav":app.last_export_folder.path_join("mixed_audio.wav"),"packed":packed,"linked":linked,"audio_driver":AudioServer.get_driver_name(),"captured_peak":peak}
	write("writer.json",report);app.free();await process_frame;print("MULTI_AUDIO "+JSON.stringify(report));quit(0 if failures==0 else 1)

func reader(mode: String) -> void:
	var expected:=Recovery.read_json(folder.path_join("expected.json"))
	if mode in ["packed","linked"]:app.has_project.open_file(expected[mode]);await job()
	elif mode=="recovery":check(app.restore_checkpoint({"folder":expected.recovery,"manifest":"project.json"}),"fresh process restores ordinary audio recovery checkpoint")
	elif mode=="lesson":
		var store:=Store.new();store.root=folder.path_join("lessons");check(store.load_snapshot(app,"basic-pose","1234","step_01"),"fresh process restores ordinary multi-sound lesson checkpoint")
	check(app.audio_clips.size()==3,"fresh "+mode+" reader has all three clips")
	if app.audio_clips.size()!=3:app.free();quit(1);return
	check(same(audio_rows(),expected.audio) and pcm_hash()==expected.mix,"fresh "+mode+" reader preserves exact clip identities/settings/source bytes and combined PCM")
	check(same(World.portable(app.current_world()),expected.world) and same(app.keys,expected.keys) and Storage.image_hash(app.layers[1].cels[0].image)==expected.paint,"fresh "+mode+" reader preserves native world, explicit camera and independent drawing")
	# Invalid collection metadata must fail before replacing live state.
	var directory: String=app.project_folder
	if not directory.is_empty():
		var path:=directory.path_join("project.json");var bytes:=FileAccess.get_file_as_bytes(path);var bad:=Recovery.read_json(path);bad.audio.clips[1].id=bad.audio.clips[0].id
		Recovery.write_json(path,bad);var accepted: bool=app.open_project(directory)
		check(not accepted and app.open_project_error.contains("duplicate") and pcm_hash()==expected.mix,"duplicate audio identity refuses atomically and preserves current mix")
		var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(bytes);file.close()
	app.set_frame(24);var image: Image=await app.renderer.capture(app.keys,app.layers,24,true);var reference:=Image.load_from_file(folder.path_join("reference.png"));var a:=image.get_data();var b:=reference.get_data();var changed:=0;var total:=0.0
	for i in range(a.size()):
		if a[i]!=b[i]:changed+=1;total+=absf(float(a[i])-float(b[i]))
	check(changed<=384 and total/a.size()<.002,"fresh "+mode+" native rebuild preserves established image bound")
	var movie:=""
	if mode=="packed":
		var error: String=await app.export_movie(folder);movie=app.last_export_folder.path_join("movie.mp4")
		check(error.is_empty(),"fresh packed multi-sound scene exports another synchronized movie")
	var result:={"checks":checks,"failures":failures,"mode":mode,"movie":movie,"changed_channels":changed}
	write("reader-"+mode+".json",result);app.free();await process_frame;print("MULTI_AUDIO_READ "+JSON.stringify(result));quit(0 if failures==0 else 1)
