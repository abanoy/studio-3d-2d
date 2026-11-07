extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Store=preload("res://src/lesson_store.gd")
func _initialize() -> void:
	create_timer(900).timeout.connect(func():push_error("Extended timing watchdog");quit(2));call_deferred("run")
func pcm() -> String:return app.audio_mix.pcm.hex_encode().sha256_text()
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		for kind in (["packed"] if "--packed-only" in args else ["linked"] if "--linked-only" in args else ["packed","linked"]):
			var path:=folder.path_join(kind+".has");app.has_project.open_file(path);await wait_job()
			check(app.has_project.path==path and app.video.duration_frames==1440 and pcm()==expected.pcm,"cold "+kind+" restores60seconds and exact sparse audio")
			app.set_frame(1300);var picture: Image=await app.renderer.capture(app.keys,app.layers,1300,true)
			check(picture.get_data()==Image.load_from_file(folder.path_join("late.png")).get_data(),"cold "+kind+" preserves late world ink and child pixels")
			check(app.frame_box.max_value==1440 and app.renderer.world_runtime.duration==1440,"cold "+kind+" installs long posing and playhead bounds")
		var store:=Store.new();store.root=folder.path_join("lessons")
		check(store.load_snapshot(app,"basic-pose","1234","step_01") and app.video.duration_frames==1440 and pcm()==expected.pcm,"lesson snapshot restores longer project and exact PCM")
		print("EXTENDED_TIMING_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	check(app.new_project(),"new empty project opens");app.show_project_options();app.project_options.hide()
	var initial_error: String=app.project_timing.apply_duration(1440)
	check(initial_error.is_empty(),"parent extends to60seconds: "+initial_error)
	if not initial_error.is_empty():quit(1);return
	var source:=folder.path_join("figure.glb");preload("res://src/scene3d.gd").make_pose_fixture(source)
	check(app.pose_editor.add_model(source).is_empty(),"long project accepts original generated rig")
	app.set_frame(1300);app.pose_editor.selected="@root";app.pose_editor.operation.select(1);app.pose_editor.refresh_values();app.pose_editor.fields[0].value+=.25;app.pose_editor.apply_numeric()
	check(app.renderer.world_runtime.duration==1440 and not app.current_world().objects.is_empty(),"pose auto-key uses late parent frame")
	var posed: Dictionary=app.current_world().duplicate(true);app.undo();check(app.current_world()!=posed,"late pose edit Undo changes authored world");app.redo();check(app.current_world()==posed,"late pose edit Redo restores exact authored world")
	app.mode.select(0);app.change_mode(0);app.active_layer=1;app.set_frame(1300);app.create_cel(false);app.exposure.value=100;app.set_exposure()
	var cel: Dictionary=Drawing.cel_at(app.layers[1],1300);Drawing.edit_image(cel).image.fill_rect(Rect2i(100,100,80,80),Color.CYAN);Drawing.touch(Drawing.image(cel));app.changed()
	check(cel.start==1300 and cel.duration==100,"late cel holds beyond former240frame limit")
	var end: Dictionary=app.keys[0].duplicate(true);end.frame=1440;app.keys.append(end)
	check(app.import_audio(folder.path_join("tone.wav"),1296).is_empty(),"sound starts at54seconds")
	var original_pcm:=pcm();var history: int=app.history.size()
	check(not app.project_timing.apply_values(12,1).is_empty() and app.video.fps_num==24 and pcm()==original_pcm and app.history.size()==history,"lower rate refuses parent beyond60seconds atomically")
	check(not app.project_timing.apply_duration(240).is_empty() and app.video.duration_frames==1440,"shortening protects late authored content")
	app.keys=[end];app.set_frame(1200);var editor=app.sequence_editor;var child: String=editor.new_sequence("Bounded child")
	check(not child.is_empty() and editor.enter(child).is_empty() and app.video.duration_frames==240 and not app.keys.is_empty() and app.keys[0].frame==0,"new child in long parent remains240frames")
	check(not app.project_timing.apply_duration(241).is_empty() and app.video.duration_frames==240,"child cannot extend beyond240frames")
	check(not app.project_timing.apply_values(12,1).is_empty() and app.video.fps_num==24,"child rate change also protects enclosing parent60second envelope")
	app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image.fill_rect(Rect2i(800,400,60,60),Color.GREEN);Drawing.touch(Drawing.image(Drawing.cel_at(app.layers[1],0)));app.changed();editor.return_to_parent();await settled()
	check(app.video.duration_frames==1440 and pcm()==original_pcm,"return to parent preserves long duration and PCM")
	app.mode.select(0);app.change_mode(0);app.set_frame(1000)
	var importer=app.video_importer;importer.begin(folder.path_join("artwork.mp4"))
	while importer.phase=="inspect":await process_frame
	check(importer.phase=="layers","late video source review opens")
	if importer.phase!="layers":quit(1);return
	importer.prepare()
	check(importer.request.available_frames==240,"long remaining scene keeps per-import240frame decode bound")
	while importer.phase in ["prepare","decode"]:await process_frame
	check(importer.phase=="candidate","late video produces editable drawing preview")
	if importer.phase!="candidate":quit(1);return
	importer.commit();await settled()
	var imported: Dictionary=app.layers[-1]
	check(imported.origin.format=="studio_drawing_origin_4" and imported.origin.at==1000 and imported.cels[0].start==1000,"late import records versioned ancestry and exact placement")
	var imported_id: String=imported.id;app.undo();check(app.layers.all(func(layer):return layer.id!=imported_id),"late import Undo removes owned layer");app.redo();check(app.layers[-1].id==imported_id,"late import Redo restores identical layer")
	var png:=folder.path_join("reference.png");var image:=Image.create(8,8,false,Image.FORMAT_RGBA8);image.fill(Color(.1,.5,.8,.5));image.save_png(png)
	app.reference_sheet.open();await settled();check(app.reference_sheet.load_sheet(png).is_empty(),"reference loads in longer project");app.reference_sheet.keep.button_pressed=true;app.reference_sheet.window.hide()
	app.set_frame(1300);var late: Image=await app.renderer.capture(app.keys,app.layers,1300,true);late.save_png(folder.path_join("late.png"))
	for kind in ["packed","linked"]:
		var path:=folder.path_join(kind+".has");app.has_project.save_file(path,kind);await wait_job();check(app.has_project.path==path,"schema8 nested reference "+kind+" commits")
	var store:=Store.new();store.root=folder.path_join("lessons");check(store.save(app,"basic-pose","1234",1,false,"step_01"),"long parent enters lesson snapshot")
	# A separate252frame movie crosses the old limit while keeping test rendering bounded.
	app.new_project();await settled();check(app.project_timing.apply_values(12,1).is_empty() and app.project_timing.apply_duration(252).is_empty(),"movie scene crosses old240frame bound")
	app.mode.select(0);app.change_mode(0);app.set_frame(241);app.active_layer=1;app.create_cel(false);var movie_cel: Dictionary=Drawing.cel_at(app.layers[1],241);movie_cel.image.fill_rect(Rect2i(150,150,80,80),Color.MAGENTA);Drawing.touch(movie_cel.image);app.changed()
	check(app.import_audio(folder.path_join("tone.wav"),244).is_empty(),"movie sound is placed past old timeline end")
	var preview: Image=await app.renderer.capture(app.keys,app.layers,245,true);preview.save_png(folder.path_join("movie-preview.png"))
	var error: String=await app.export_movie(folder);check(error.is_empty(),"longer movie exports: "+error)
	var movie: String=app.last_export_folder.path_join("movie.mp4")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000246.png")).get_data()==preview.get_data(),"exported late frame exactly matches preview")
	app.has_project.open_file(folder.path_join("packed.has"));await wait_job();app.set_frame(1300);app.changed()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	app.autosave_tick(true);check(app.checkpoint_revision==app.recovery_revision,"ordinary autosave commits long project at late frame")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pcm":original_pcm,"child":child,"movie":movie,"recovery":app.recovery_session}))
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("EXTENDED_TIMING_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":movie}))
	if "--crash" in args:OS.kill(OS.get_process_id());quit(2);return
	await app.quit_studio();quit(0 if failures==0 else 1)
