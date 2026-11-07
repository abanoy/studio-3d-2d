extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("Shared raster reader watchdog");quit(2));call_deferred("run")
func live() -> Dictionary:
	var cels:=[]
	for cel in app.layers[0].cels:cels.append([cel.id,cel.start,cel.duration,Drawing.raster_token(cel)[0],Storage.image_hash(Drawing.image(cel))])
	return {"cels":cels,"frame":app.frame,"session":app.recovery_session,"revision":app.recovery_revision,"history":app.history.size(),"world":app.current_world().duplicate(true),"keys":app.keys.duplicate(true)}
func independent(expected: Dictionary) -> bool:
	if app.layers.size()!=1 or app.layers[0].cels.size()!=32:return false
	var ids:={}
	for i in range(32):
		var cel: Dictionary=app.layers[0].cels[i];ids[Drawing.raster_token(cel)[0]]=true
		if cel.id!=expected.ids[i] or Storage.image_hash(Drawing.image(cel))!=(expected.edited if i==7 else expected.base):return false
	return ids.size()==32
func source_project(folder: String) -> String:
	DirAccess.make_dir_recursive_absolute(folder);var image:=Drawing.blank(1920,1080)
	if "--noise-art" in OS.get_cmdline_user_args():
		var pixels:=PackedByteArray();pixels.resize(1920*1080*4);var random:=RandomNumberGenerator.new();random.seed=917
		for i in range(pixels.size()):pixels[i]=random.randi_range(0,255)
		image=Image.create_from_data(1920,1080,false,Image.FORMAT_RGBA8,pixels)
	else:image.fill_rect(Rect2i(100,100,200,100),Color(.2,.7,.8,.5))
	image.save_png(folder.path_join("drawing.png"));var digest:=Storage.image_hash(image);var cels:=[]
	for i in range(32):cels.append({"id":"cel"+str(i),"start":i,"duration":1,"path":"drawing.png","pixel_sha256":digest})
	var project:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60),Timeline.key(48,Vector3(1,1,5),Quaternion.IDENTITY,60)],"world":World.empty(),"layers":[{"id":"ink","name":"Ink","visible":true,"cels":cels}],"audio":{},"editor":{"frame":0}}
	FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(project));return digest
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate()
	if not "--auto-open" in args:app.cold_cel_loading="--adaptive-open" in args;app.cold_cel_min_bytes=0
	app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("shared.has"));await wait_job()
		check(app.has_project.path==folder.path_join("shared.has") and independent(expected),"cold packed Open preserves32independent raster identities and all edited/peer RGBA")
		app.set_frame(7);await settled();check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,7,1920,1080).get_data(),"cold edited cel shows exact actual GPU preview")
		var picture: Image=await app.renderer.capture(app.keys,app.layers,7,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-7.png")).get_data(),"cold final composition matches original edited movie input")
		app.set_frame(8);await settled();check(Storage.image_hash(Drawing.image(app.layers[0].cels[8]))==expected.base and app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,8,1920,1080).get_data(),"cold neighboring cel retains original raster and preview")
		check(Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"cold packed source retains exact independent audio mix")
		print("CEL_RASTER_READER_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var source:=folder.path_join("source-project");var base:=source_project(source);var source_sha:=FileAccess.get_sha256(source.path_join("drawing.png"));var source_manifest:=FileAccess.get_sha256(source.path_join("project.json"))
	check(app.open_project(source),"ordinary directory project opens32cel records referencing one original PNG")
	if "--auto-open" in args:check(app.cold_cel_loading and app.cold_cel_min_bytes==64*1024*1024 and app.layers[0].cels.all(func(cel):return cel.has("raster_owner")),"unchanged app defaults automatically cold-load a larger project")
	if not "--auto-open" in args and not "--adaptive-open" in args:
		var eager_state: Dictionary=app.raster_budget.sample()
		check(not app.cold_cel_loading and eager_state.owners==32 and eager_state.hot_bytes==32*1920*1080*4,"eager decoder path joins all32owned drawings before the app publishes them")
	if "--noise-art" in args:
		var state: Dictionary=app.raster_budget.sample()
		check(state.owners==32 and state.hot_owners==32 and state.hot_bytes==32*1920*1080*4,"raw full-HD source registers all32independent owners and conservative bytes")
	var expected: Dictionary={"base":base,"edited":base,"ids":[]}
	for cel in app.layers[0].cels:expected.ids.append(cel.id)
	check(independent(expected),"ordinary Open provides32distinct editable raster identities with exact source RGBA")
	check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"independent audio starts at frame24")
	app.mode.select(0);app.change_mode(0);app.active_layer=0;app.layer_choice.select(0);app.tool.select(0);app.set_frame(7);await settled();var image: Image;var history: int=app.history.size()
	app.color.color=Color.RED;app.radius.value=6;var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(300,300));app.paint_segment(Vector2(340,300));press.pressed=false;app.canvas_input(press,Vector2(340,300));await settled();image=Drawing.image(app.layers[0].cels[7]);expected.edited=Storage.image_hash(image)
	check(expected.edited!=base and app.history.size()==history+1 and independent(expected),"actual brush changes only cel7 while31copy-on-write peers remain exact")
	check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,7,1920,1080).get_data(),"edited shared-source cel updates actual GPU overlay exactly")
	app.undo();await settled();var undo_expected:=expected.duplicate(true);undo_expected.edited=base
	check(independent(undo_expected) and is_same(Drawing.image(app.layers[0].cels[7]),image),"pixel Undo restores source bytes without merging cel identity")
	app.redo();await settled();check(independent(expected) and is_same(Drawing.image(app.layers[0].cels[7]),image),"pixel Redo reapplies only the edited cel")
	app.set_frame(8);await settled();check(Storage.image_hash(Drawing.image(app.layers[0].cels[8]))==base and app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,8,1920,1080).get_data(),"adjacent frame still shows independent original drawing")
	app.set_frame(7);await settled();check(independent(expected),"reverse seek retains edited and original ownership")
	var before:=live();var bad_folder:=folder.path_join("bad-project");DirAccess.make_dir_recursive_absolute(bad_folder);DirAccess.copy_absolute(source.path_join("drawing.png"),bad_folder.path_join("drawing.png"));var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(source.path_join("project.json")))
	for kind in ["unsafe","checksum","missing","changed"]:
		var bad:=manifest.duplicate(true)
		if kind=="unsafe":bad.layers[0].cels[31].path="../drawing.png"
		elif kind=="checksum":bad.layers[0].cels[31].pixel_sha256=false
		elif kind=="missing":bad.layers[0].cels[31].path="absent.png"
		else:
			var changed:=Drawing.blank(1920,1080);changed.fill(Color.MAGENTA);changed.save_png(bad_folder.path_join("changed.png"));bad.layers[0].cels[31].path="changed.png"
		FileAccess.open(bad_folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(bad))
		check(not app.open_project(bad_folder) and live()==before,"late "+kind+" repeated-cel failure refuses before replacing live document/history")
	var packed:=folder.path_join("shared.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"normal packed Save retains32editable cel records")
	app.new_project();app.has_project.open_file(packed);await wait_job();check(independent(expected),"ordinary packed reopen keeps all separate identities and edited/peer RGBA")
	app.mode.select(0);app.change_mode(0);app.set_frame(7);await settled()
	var picture: Image=await app.renderer.capture(app.keys,app.layers,7,true);picture.save_png(folder.path_join("expected-7.png"))
	var error: String=await app.export_movie(folder);check(error.is_empty(),"32cel shared-source scene exports through ordinary renderer")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000008.png")).get_data()==picture.get_data(),"edited frame7 movie input matches reopened preview exactly")
	check(independent(expected) and FileAccess.get_sha256(source.path_join("drawing.png"))==source_sha and FileAccess.get_sha256(source.path_join("project.json"))==source_manifest,"painting/history/save/export preserve31peer cels and original source project bytes")
	expected["movie"]=app.last_export_folder.path_join("movie.mp4");expected["pcm"]=Storage.RasterReader.digest_bytes(app.audio_mix.pcm);expected["source_png_sha256"]=source_sha;expected["source_manifest_sha256"]=source_manifest
	app.set_frame(7);app.changed()
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	app.autosave_tick(true)
	while app.recovery_preview.busy():app.poll_recovery_preview();await process_frame
	check(app.checkpoint_revision==app.recovery_revision,"ordinary recovery checkpoint saves all independent shared-source cels")
	expected["recovery"]=app.recovery_session;var expected_file:=FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE);expected_file.store_string(JSON.stringify(expected,"",true,true));expected_file.flush();expected_file.close()
	app.tree_exiting.connect(func():FileAccess.open(folder.path_join("graceful-exit.txt"),FileAccess.WRITE).store_string("unexpected"))
	print("CEL_RASTER_READER_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":expected.movie}))
	if "--crash" in args:OS.kill(OS.get_process_id());quit(2);return
	await app.quit_studio();quit(0 if failures==0 else 1)
