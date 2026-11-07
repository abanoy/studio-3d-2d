extends SceneTree
const Timing=preload("res://src/video_timing.gd")
const Audio=preload("res://src/audio_track.gd")
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
var app
var checks:=0
var failures:=0
class Clock extends RefCounted:
	var root:=Node3D.new()
	var evaluation_error:=""
	var seconds:=-1.
	func evaluate(value: float) -> void:seconds=value
func _initialize() -> void:
	create_timer(150).timeout.connect(func():quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func pcm() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var mode: String=args[1] if args.size()>1 else "writer"
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("recovery-"+mode);app.recent_path=folder.path_join("recents-"+mode+".json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache-"+mode)
	if mode!="writer":
		var reference:=Recovery.read_json(folder.path_join("expected.json"))
		if mode in ["packed","linked"]:app.has_project.open_file(reference[mode]);await job()
		elif mode=="recovery":check(app.restore_checkpoint({"folder":reference.recovery,"manifest":"project.json"}),"restore rational-rate recovery checkpoint")
		elif mode=="lesson":
			var lesson:=Store.new();lesson.root=folder.path_join("lessons");check(lesson.load_snapshot(app,"basic-pose","1234","step_01"),"restore rational-rate lesson snapshot")
		app.show_project_options();check(app.video.fps_num==24000 and app.video.fps_den==1001 and pcm()==reference.mix,"fresh reader restores exact rational rate and mix: "+mode)
		check(app.project_timing.choices.selected==3 and "23.976 fps" in app.transport_info.text,"fresh reader shows the saved frame rate: "+mode)
		print("PROJECT_TIMING_READ ",JSON.stringify({"mode":mode,"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	for pair in Timing.PRESETS:check(Timing.error(pair[0],pair[1]).is_empty(),"valid frame-rate preset "+str(pair))
	for pair in [[0,1],[24,0],[121,1],[24000,1002],[true,1],[NAN,1],[24000.5,1001]]:check(not Timing.error(pair[0],pair[1]).is_empty(),"invalid frame rate refuses "+str(pair))
	check(Timing.error(25,2).is_empty() and Timing.error(1,1001).is_empty(),"older valid rational rates stay readable")
	var fx:=Clock.new();var runtime:=preload("res://src/world_runtime.gd").new();runtime.effects={"clock":fx};runtime.data={"effects":[{"id":"clock","visible":true,"start_frame":0,"end_frame":48,"source_in_seconds":0}]}
	runtime.evaluate(24,false,"",{"fps_num":24000,"fps_den":1001});check(runtime.evaluation_error.is_empty() and absf(fx.seconds-1.001)<1e-9,"particle clock accepts NTSC rational project time");runtime.effects.clear();fx.root.free()
	var asset:=folder.path_join("figure.glb");SceneIO.make_pose_fixture(asset);check(app.pose_editor.add_model(asset).is_empty(),"original rig is available for timing isolation")
	app.pose_editor.record_key();app.set_frame(24);Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],24)).image.set_pixel(70,70,Color.CYAN)
	check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"audio marker is placed at frame24")
	app.show_project_options();await settle();check(not app.advanced_mode and app.project_timing.choices.is_visible_in_tree(),"project frame rate is accessible in Simple options")
	var before: Dictionary=app.video.duplicate(true);var mixed:=pcm();var audio: Dictionary=app.audio_document().duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true);var history: int=app.history.size();var view: Dictionary=app.renderer.view_state()
	app.project_timing.choices.select(3);app.project_timing.choices.item_selected.emit(3);await settle()
	check(app.video.fps_num==24000 and app.video.fps_den==1001 and app.history.size()==history+1,"actual rate preset changes project timing in one Undo step")
	check(app.audio_mix.samples==96096 and pcm()!=mixed and app.audio_mix.pcm.decode_s16(48047*4)==0 and absi(app.audio_mix.pcm.decode_s16(48049*4))>1000,"NTSC mix duration and frame24 onset follow exact rational sample placement")
	check(app.audio_document()==audio and app.current_world()==world and app.keys==shots and app.frame==24 and app.renderer.view_state()==view,"rate change keeps frame addresses, source audio, scene records and editor view")
	check("23.976 fps" in app.transport_info.text,"transport shows the actual fractional rate without integer truncation")
	var ntsc: Dictionary=app.video.duplicate(true);var ntsc_mix:=pcm();app.undo();check(app.video==before and pcm()==mixed and app.project_timing.choices.selected==2,"Undo restores original rate, exact mix and selector")
	app.redo();check(app.video==ntsc and pcm()==ntsc_mix and app.project_timing.choices.selected==3,"Redo restores NTSC timing and exact mix")
	check(app.project_timing.apply_values(12,1).is_empty() and app.audio_mix.samples==192000 and absi(app.audio_mix.pcm.decode_s16(96001*4))>1000,"integer12fps keeps the sound at frame24 and extends project time")
	app.undo();check(app.video==ntsc and pcm()==ntsc_mix,"integer-rate Undo restores the exact fractional mix")
	check(app.project_timing.apply_values(25,2).is_empty() and app.project_timing.choices.selected==Timing.PRESETS.size(),"a valid older custom rational rate is displayed without forcing a preset")
	app.undo();check(app.video==ntsc and pcm()==ntsc_mix and app.project_timing.choices.selected==3,"custom-rate Undo restores the correct selector and mix")
	history=app.history.size();check(app.project_timing.apply_values(24000,1001).is_empty() and app.history.size()==history,"same rate is a no-op")
	check(not app.project_timing.apply_values(121,1).is_empty() and app.video==ntsc and app.history.size()==history,"invalid rate preserves the project and history")
	check(not app.project_timing.apply_values(1,1001).is_empty() and app.video==ntsc and pcm()==ntsc_mix,"over-budget audio duration refuses before replacing settings or samples")
	app.physics_editor.recording.active=true;check(not app.project_timing.apply_values(30,1).is_empty() and app.video==ntsc,"recording protects its captured frame rate");app.physics_editor.recording.active=false
	await settle();app.get_viewport().get_texture().get_image().save_png(folder.path_join("timing-options.png"));app.project_options.hide()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,24,true)
	var saved:=folder.path_join("ntsc.has");app.has_project.save_file(saved,"packed");await job();check(app.has_project.path==saved,"NTSC project saves as ordinary packed HAS")
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await job();check(app.has_project.path==linked,"rational-rate project also saves linked assets")
	app.changed();app.autosave_tick(true);var recovery: String=app.recovery_root.path_join(app.recovery_session)
	var store:=Store.new();store.root=folder.path_join("lessons");check(store.save(app,"basic-pose","1234",1,false,"step_01"),"rational project timing enters a lesson snapshot")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"packed":saved,"linked":linked,"recovery":recovery,"mix":ntsc_mix}))
	app.new_project();app.has_project.open_file(saved);await job();check(app.video.fps_num==24000 and app.video.fps_den==1001 and pcm()==ntsc_mix,"packed reopening restores exact rate and audio PCM")
	var legacy=load(folder.path_join("previous_storage.gd"));var cache: String=app.audio_clips[0].source.path.get_base_dir().get_base_dir()
	var legacy_result: Dictionary=legacy.load_project(cache)
	check(FileAccess.file_exists(cache.path_join("project.json")) and legacy_result.has("error") and "fps" in legacy_result.error,"actual previous reader refuses unsupported numerator rather than changing timing")
	check(await app.export_movie(folder)=="","NTSC MP4 export succeeds")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000025.png")).get_data()==expected.get_data(),"NTSC movie frame matches preview exactly")
	var result:={"checks":checks,"failures":failures,"project":saved,"movie":app.last_export_folder.path_join("movie.mp4"),"mix":ntsc_mix};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("PROJECT_TIMING_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
