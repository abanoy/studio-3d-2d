extends "res://tests/walking_path_smoke.gd"
const World=preload("res://src/world_document.gd")
const Output=preload("res://src/output_size.gd")
var expected: Dictionary={}
func _initialize() -> void:
	create_timer(360).timeout.connect(func():push_error("Settings matrix watchdog");quit(2));call_deferred("run")
func canonical(value):return JSON.parse_string(JSON.stringify(value,"",true,true))
func personal() -> Dictionary:
	return canonical({"scale":app.get_window().content_scale_factor,"navigation":app.navigation_scheme,"shortcuts":app.keyboard_shortcuts.bindings,"slots":app.workspace_layout.locations,"advanced":app.advanced_mode,"height_offer":app.import_actions.offer_height,"encoder_path":app.encoder_path.text,"encoder_quality":app.selected_movie_profile(),"png_drawings_only":app.png_drawing_only.button_pressed,"recovery_enabled":app.autosave_enabled.button_pressed,"recovery_schedule":app.autosave_schedule.selected,"recovery_interval":app.autosave_interval.value,"recovery_actions":app.autosave_action_limit.value,"brush_radius":app.radius.value,"brush_opacity":app.brush_opacity.value,"brush_pressure":app.brush_pressure.button_pressed,"brush_smoothing":app.brush_smoothing.value,"tool":app.tool.selected})
func configure_session(profile: String) -> void:
	var alpha:=profile=="a";app.set_advanced(not alpha);app.import_actions.offer_height=not alpha
	app.encoder_path.text=app.default_ffmpeg() if alpha else folder.path_join("personal-machine-only/ffmpeg-unavailable")
	app.encoder_quality.select(0 if alpha else 1);app.png_drawing_only.button_pressed=not alpha
	app.autosave_enabled.button_pressed=false;app.autosave_schedule.select(0 if alpha else 1);app.autosave_interval.value=1 if alpha else 2;app.autosave_action_limit.value=25 if alpha else 17;app.refresh_recovery_schedule(false)
	app.radius.value=5 if alpha else 12;app.brush_opacity.value=100 if alpha else 65;app.brush_pressure.button_pressed=alpha;app.brush_smoothing.value=0 if alpha else .5;app.tool.select(0 if alpha else 1)
func configure_personal(profile: String) -> void:
	var alpha:=profile=="a";app.set_advanced(true);app.show_display_settings();await settled()
	var scale: OptionButton
	for control in app.display_dialog.find_children("*","OptionButton",true,false):
		if control!=app.navigation_choices:scale=control;break
	scale.select(0 if alpha else 1);scale.item_selected.emit(0 if alpha else 1);app.navigation_choices.select(0 if alpha else 1);app.navigation_choices.item_selected.emit(0 if alpha else 1);app.display_dialog.hide()
	check(app.keyboard_shortcuts.assign("pen",KEY_F7 if alpha else KEY_F8).is_empty(),"personal "+profile+" shortcut saves independently")
	var ws=app.workspace_layout;ws.reset()
	if not alpha:ws.panels.world.get_child(0).get_child(1).get_popup().id_pressed.emit(1)
	await settled();ws.path=folder.path_join("layout-"+profile+".json");ws.save();configure_session(profile);await settled()
	DirAccess.copy_absolute(app.display_prefs_path,folder.path_join("profile-"+profile+".cfg"))
func state() -> Dictionary:
	return canonical({"video":app.video,"palette":app.palette,"art":Storage.image_hash(Drawing.image(app.layers[1].cels[0])),"pcm":Storage.RasterReader.digest_bytes(app.audio_mix.pcm),"objects":app.current_world().objects.size(),"frame":app.frame})
func check_project(name: String,owner: Dictionary) -> void:
	check(state()==expected.projects[name].state,"project "+name+" restores complete video/palette/art/PCM/frame setting matrix")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,12,true);check(picture.get_data()==Image.load_from_file(folder.path_join(name+"-native.png")).get_data(),"project "+name+" final pixels reproduce despite personal presentation differences")
	check(personal()==owner and not app.has_dialog(app),"project "+name+" preserves personal controls/layout without a settings prompt")
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var reader:="--read" in args;var profile:="a" if "--profile-a" in args else "b"
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("profile-"+profile+".cfg" if reader else "personal.cfg");app.recovery_root=folder.path_join("reader-recovery-"+profile if reader else "recovery");app.recent_path=folder.path_join("recents-"+profile+".json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache-"+profile if reader else "writer-cache")
	if reader:
		expected=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.workspace_layout.path=folder.path_join("layout-"+profile+".json");app.workspace_layout.load_layout();configure_session(profile);await settled();var owner:=personal();check(owner==expected.personal[profile],"fresh process loads its own persisted preferences and independently configured session controls "+profile)
		for name in ["b","a"]:
			var prefs_sha:=FileAccess.get_sha256(app.display_prefs_path);app.has_project.open_file(folder.path_join(name+".has"));await wait_job();await check_project(name,owner);check(FileAccess.get_sha256(app.display_prefs_path)==prefs_sha,"Open "+name+" does not rewrite personal preference bytes")
		app.new_project();check(personal()==owner and app.video.width==1920 and app.video.fps_num==24 and not app.video.has("output_size"),"New restores content defaults while retaining personal profile "+profile)
		print("SETTINGS_MATRIX_READ "+JSON.stringify({"checks":checks,"failures":failures,"profile":profile}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var prefs:=ConfigFile.new();prefs.set_value("unrelated","keep","settings-matrix-sentinel");prefs.save(app.display_prefs_path)
	expected={"personal":{},"projects":{},"movies":{}}
	await configure_personal("a");expected.personal.a=personal();var map:=folder.path_join("map.glb");DirAccess.copy_absolute("res://examples/tutorials/Practice room.glb",map);var source_sha:=FileAccess.get_sha256(map)
	for name in ["a","b"]:
		app.new_project();check(personal()==expected.personal.a,"New "+name+" retains personal profile A")
		app.show_project_options();await settled()
		if name=="a":
			check(app.project_canvas.apply("540p").is_empty() and app.project_timing.apply_values(30000,1001).is_empty() and app.project_timing.apply_duration(61).is_empty(),"project A sets native540/rational rate/61frames")
		else:check(app.video.width==1920 and app.video.fps_num==24 and app.video.duration_frames==48,"project B starts native1080/24fps/48frames")
		app.visibility_fade.value=0 if name=="a" else 725;app.project_options.hide();app.change_lighting(0 if name=="a" else 2)
		if name=="b":app.video["world_background"]="legacy_blue";app.renderer.set_background("legacy_blue");app.changed()
		app.output_size.select(1 if name=="a" else 2);app.output_size.item_selected.emit(1 if name=="a" else 2)
		check(app.append_object(Model.definition(map),"environment").is_empty(),"project "+name+" keeps original map geometry")
		app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Timeline.from_camera(0,app.renderer.camera,"ease"),Timeline.from_camera(app.video.duration_frames,app.renderer.camera,"ease")]
		app.mode.select(0);app.change_mode(0);app.set_frame(0);app.create_cel(false);var art: Image=Drawing.edit_image(Drawing.cel_at(app.layers[1],0)).image;art.fill_rect(Rect2i(30,30,40,20),Color.RED if name=="a" else Color.CYAN);Drawing.touch(art);app.palette=[{"name":"Project "+name,"rgba":"ff0000ff" if name=="a" else "00ffffff"}];app.palette_editor.refresh(true);app.changed();check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"project "+name+" independent paint/palette/audio settings load")
		app.set_frame(12);var picture: Image=await app.renderer.capture(app.keys,app.layers,12,true);picture.save_png(folder.path_join(name+"-native.png"));expected.projects[name]={"state":state()}
		app.has_project.save_file(folder.path_join(name+".has"),"packed");await wait_job();check(not app.dirty and FileAccess.file_exists(folder.path_join(name+".has")),"ordinary project "+name+" packed Save stores its own content settings")
		var movie_parent:=folder.path_join("movie-"+name);DirAccess.make_dir_recursive_absolute(movie_parent);var error: String=await app.export_movie(movie_parent);check(error.is_empty(),"project "+name+" actual movie follows saved content settings")
		if not error.is_empty():print("MATRIX_EXPORT_ERROR "+error);await app.quit_studio();quit(1);return
		expected.movies[name]=app.last_finished_movie
		var delivered: Image=Output.resample(picture,Output.PROFILES[app.selected_output_size()]);check(delivered.get_data()==Image.load_from_file(app.last_export_folder.path_join("frame_000013.png")).get_data(),"project "+name+" export frame matches selected delivery from native preview")
	var clean_history: int=app.history.size();await configure_personal("b");expected.personal.b=personal();check(not app.dirty and app.history.size()==clean_history,"changing personal preferences leaves saved scene/history clean")
	var owner:=personal();var prefs_sha:=FileAccess.get_sha256(app.display_prefs_path)
	for name in ["a","b"]:
		app.has_project.open_file(folder.path_join(name+".has"));await wait_job();await check_project(name,owner)
	check(FileAccess.get_sha256(app.display_prefs_path)==prefs_sha,"both project opens leave personal preferences byte-identical")
	var directory:=folder.path_join("directory");check(Storage.save_project(directory,app.video,app.keys,app.layers,"",app.frame,app.audio_clip,{}, {},false,app.current_world(),{},app.palette).is_empty(),"directory Save keeps the same setting boundary")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("project.json")));manifest.video.visibility_fade_ms=-1;FileAccess.open(directory.path_join("bad.json"),FileAccess.WRITE).store_string(JSON.stringify(manifest));var current:=state();var current_root=app.renderer.world_runtime.root
	check(not app.open_project(directory,"bad.json") and state()==current and personal()==owner and app.renderer.world_runtime.root==current_root,"refused malformed Open preserves content and personal settings atomically")
	check(app.open_project(directory) and personal()==owner,"directory Open preserves personal choices without importing UI preferences")
	app.has_project.open_file(folder.path_join("a.has"));await wait_job();app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var checkpoint: String=app.recovery_root.path_join(app.recovery_session);check(app.open_project(checkpoint) and personal()==owner and canonical(app.video)==expected.projects.a.state.video,"recovery Open restores content settings without replacing personal profile")
	prefs=ConfigFile.new();prefs.load(app.display_prefs_path);check(prefs.get_value("unrelated","keep")=="settings-matrix-sentinel" and FileAccess.get_sha256(map)==source_sha,"preference updates and project operations preserve unrelated settings and original geometry")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true));print("SETTINGS_MATRIX_WRITE "+JSON.stringify({"checks":checks,"failures":failures,"movies":expected.movies}));await app.quit_studio();quit(0 if failures==0 else 1)
