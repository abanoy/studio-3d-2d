extends SceneTree
const Drawing=preload("res://src/drawing.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Recovery=preload("res://src/recovery.gd")
const Store=preload("res://src/lesson_store.gd")
var app
var checks:=0
var failures:=0
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
		elif mode=="recovery":check(app.restore_checkpoint({"folder":reference.recovery,"manifest":"project.json"}),"restore duration checkpoint")
		elif mode=="lesson":
			var lesson:=Store.new();lesson.root=folder.path_join("lessons");check(lesson.load_snapshot(app,"basic-pose","1234","step_01"),"restore duration lesson snapshot")
		app.show_project_options();check(app.video.duration_frames==24 and pcm()==reference.mix,"fresh length and exact mix: "+mode)
		check(app.project_timing.duration.value==24 and app.frame_box.max_value==24 and app.renderer.world_runtime.duration==24,"fresh UI and posing duration agree: "+mode)
		print("PROJECT_DURATION_READ ",JSON.stringify({"mode":mode,"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	var asset:=folder.path_join("figure.glb");SceneIO.make_pose_fixture(asset);check(app.pose_editor.add_model(asset).is_empty(),"original rig imports")
	app.pose_editor.record_key();var id: String=app.renderer.active_instance_id
	var end: Dictionary=app.keys[0].duplicate(true);end.frame=48;app.keys.append(end)
	Drawing.insert(app.layers[1],0,48,Drawing.blank(1920,1080));Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.set_pixel(70,70,Color.CYAN)
	check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"sound begins at frame24")
	app.show_project_options();await settle();check(not app.advanced_mode and app.project_timing.duration.is_visible_in_tree(),"scene length is available in Simple")
	var video: Dictionary=app.video.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);var shots: Array=app.keys.duplicate(true);var audio: Dictionary=app.audio_document().duplicate(true);var prefix: PackedByteArray=app.audio_mix.pcm.duplicate();var view: Dictionary=app.renderer.view_state();var history: int=app.history.size()
	app.project_timing.duration.value=96
	for child in app.project_timing.duration.get_parent().get_children():
		if child is Button and child.text=="Apply scene length":child.pressed.emit()
	check(app.video.duration_frames==96 and app.history.size()==history+1,"Apply extends scene in one Undo")
	check(app.current_world()==world and app.keys==shots and app.audio_document()==audio and app.layers[1].cels[0].duration==48 and app.renderer.view_state()==view,"extension retains scene, keys, drawing holds, audio source and view")
	check(app.audio_mix.samples==192000 and app.audio_mix.pcm.slice(0,prefix.size())==prefix,"extended mix preserves old prefix and adds new scene time")
	check(app.frame_box.max_value==96 and app.renderer.world_runtime.duration==96,"playhead and posing validation use extended duration")
	app.project_timing.duration.value=80;app.set_frame(72);check(app.project_timing.duration.value==80,"scrubbing preserves unapplied length input")
	app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[0].value+=.2;app.pose_editor.apply_numeric()
	check(app.history.size()==history+2,"model auto-keys beyond former scene end")
	var edited: Dictionary=app.current_world().duplicate(true)
	check(not app.project_timing.apply_duration(48).is_empty() and app.video.duration_frames==96 and app.current_world()==edited,"shortening refuses later model animation unchanged")
	app.undo();app.undo();check(app.video==video and app.audio_mix.pcm==prefix and app.frame<=48 and app.renderer.world_runtime.duration==48,"Undo length restores exact mix and clamps playhead")
	app.redo();app.redo();check(app.video.duration_frames==96 and app.current_world()==edited and app.renderer.world_runtime.duration==96,"Redo length then model key works at extended frame")
	app.undo()
	check(not app.project_timing.apply_duration(24).is_empty() and app.video.duration_frames==96,"camera keys beyond new end protect shortening")
	app.keys=shots.slice(0,1);end.frame=24;app.keys.append(end)
	check(not app.project_timing.apply_duration(24).is_empty(),"drawing exposure beyond new end protects shortening")
	app.set_frame(0);app.active_layer=1;app.exposure.value=24;app.set_exposure()
	check(not app.project_timing.apply_duration(24).is_empty(),"sound starting at new end protects shortening")
	var old: Dictionary=app.audio_document().duplicate(true);app.audio_clip.start_frame=0;app.commit_audio(old)
	check(app.project_timing.apply_duration(24).is_empty() and app.video.duration_frames==24 and app.audio_mix.samples==48000,"valid shortening keeps end-boundary camera key and clips sound at scene end")
	var short_mix:=pcm();app.undo();check(app.video.duration_frames==96 and app.audio_mix.samples==192000,"shorten Undo restores longer audio mix")
	app.redo();check(app.video.duration_frames==24 and pcm()==short_mix,"shorten Redo restores exact short mix")
	history=app.history.size();check(app.project_timing.apply_duration(24).is_empty() and app.history.size()==history,"same length is a no-op")
	for bad in [0,1441,12.5,true,NAN]:check(not app.project_timing.apply_duration(bad).is_empty() and app.video.duration_frames==24 and app.history.size()==history,"invalid length refuses: "+str(bad))
	app.physics_editor.recording.active=true;check(not app.project_timing.apply_duration(48).is_empty() and app.video.duration_frames==24,"recording protects duration");app.physics_editor.recording.active=false
	app.exporting=true;check(not app.project_timing.apply_duration(48).is_empty() and app.video.duration_frames==24,"export protects duration");app.exporting=false
	app.pose_editor.dragging=true;check(not app.project_timing.apply_duration(48).is_empty() and app.video.duration_frames==24 and app.history.size()==history,"pending pose edit protects timing without committing its key");app.pose_editor.dragging=false
	check(app.project_timing.apply_values(2,1).is_empty(),"slow valid rate is available within the audio budget")
	var bounded: Dictionary=app.video.duplicate(true);var bounded_mix:=pcm();history=app.history.size()
	check(not app.project_timing.apply_duration(240).is_empty() and app.video==bounded and pcm()==bounded_mix and app.history.size()==history,"over-budget extension preserves timing, mix and history")
	app.undo()
	check(app.project_timing.apply_values(24000,1001).is_empty() and app.audio_mix.samples==48048,"duration shares exact fractional audio clock")
	old=app.audio_document().duplicate(true);app.audio_clip.start_frame=12;app.commit_audio(old)
	app.get_window().size=Vector2i(1200,760);app.show_project_options();await settle()
	var scale: Vector2=app.get_viewport().get_screen_transform().get_scale()
	check(app.project_options.position.y>=0 and (app.project_options.position.y+app.project_options.size.y)*scale.y<=app.get_window().size.y,"scene options fit the smaller desktop window")
	app.get_viewport().get_texture().get_image().save_png(folder.path_join("duration-options.png"));app.project_options.hide()
	var expected: Image=await app.renderer.capture(app.keys,app.layers,12,true)
	var packed:=folder.path_join("duration.has");app.has_project.save_file(packed,"packed");await job();check(app.has_project.path==packed,"changed length saves packed")
	var linked:=folder.path_join("linked.has");app.has_project.save_file(linked,"linked");await job();check(app.has_project.path==linked,"changed length saves linked")
	app.changed();app.autosave_tick(true);var recovery: String=app.recovery_root.path_join(app.recovery_session)
	var store:=Store.new();store.root=folder.path_join("lessons");check(store.save(app,"basic-pose","1234",1,false,"step_01"),"length enters lesson snapshot")
	var mix:=pcm();FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"packed":packed,"linked":linked,"recovery":recovery,"mix":mix}))
	check(await app.export_movie(folder)=="","short fractional-rate movie exports")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data()==expected.get_data(),"duration movie matches preview with independent drawing")
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	app.show_project_options();app.project_timing.duration.value=99;app.new_project();check(app.project_timing.duration.value==48,"New resets open pending length field")
	check(app.project_timing.apply_duration(240).is_empty() and app.frame_box.max_value==240,"silent empty scene accepts existing 240-frame limit")
	check(app.project_timing.apply_duration(1).is_empty() and app.video.duration_frames==1,"empty scene accepts one rendered frame")
	check(FileAccess.get_sha256(asset)==world.objects[0].sha256,"original geometry stays unchanged")
	var result:={"checks":checks,"failures":failures,"project":packed,"movie":movie,"mix":mix,"id":id};FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("PROJECT_DURATION_SMOKE ",JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
