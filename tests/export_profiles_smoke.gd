extends SceneTree
const Encoder=preload("res://src/encoder.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(210).timeout.connect(func():push_error("Export profiles watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func job() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func equal(a,b) -> bool:return JSON.parse_string(JSON.stringify(a,"",true,true))==JSON.parse_string(JSON.stringify(b,"",true,true))
func quality(index: int) -> void:app.encoder_quality.select(index);app.encoder_quality.item_selected.emit(index)
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0]
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	if "--read" in args:
		app.has_project.open_file(folder.path_join("Profiles.has"));await job()
		check(app.selected_movie_profile()=="standard","new session defaults Standard when reopening an ordinary project")
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		check(Storage.image_hash(Drawing.image(Drawing.cel_at(app.layers[1],0)))==expected.pixels,"ordinary HAS retains exact authored pixels independently of delivery profile")
		var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true)
		check(Storage.image_hash(preview)==expected.render,"cold project renders exact original uncompressed movie input")
		print("EXPORT_PROFILES_READ ",JSON.stringify({"checks":checks,"failures":failures}));app.free();quit(0 if failures==0 else 1);return
	check(app.load_demo_room(),"original procedural scene loads for actual profile exports")
	check(app.selected_movie_profile()=="standard" and not app.encoder_quality.is_visible_in_tree(),"Simple exports keep the existing Standard default")
	app.set_advanced(true);check(app.encoder_quality.is_visible_in_tree() and app.encoder_quality.item_count==3,"Advanced offers Standard, Smaller file and High quality")
	var invalid:=Encoder.new();invalid.profile="unknown"
	var refused: String=await invalid.encode(self,app.encoder_path.text,folder.path_join("not-created"),app.video)
	check(not refused.is_empty() and invalid.process_id==-1 and not DirAccess.dir_exists_absolute(folder.path_join("not-created")) and not Encoder.profile_error(true).is_empty(),"encoder API rejects unknown or malformed profiles before launching a process")
	var art:=Drawing.blank(1920,1080)
	for y in range(128):
		for x in range(128):art.set_pixel(600+x,400+y,Color(float((x*13+y*7)%256)/255,float((x*3+y*19)%256)/255,float((x*23+y*11)%256)/255,1))
	app.layers[1].cels.clear();Drawing.insert(app.layers[1],0,48,art);app.changed()
	var cue:=ProjectSettings.globalize_path("res://examples/tutorials/Practice cue.wav");var cue_hash:=FileAccess.get_sha256(cue)
	check(app.import_audio(cue,24).is_empty(),"original practice cue joins movie at frame24")
	var world: Dictionary=World.portable(app.current_world());var shots: Array=app.keys.duplicate(true);var pixels:=art.get_data()
	var preview: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	var error: String=await app.export_movie(folder);var standard: String=app.last_finished_movie;var standard_folder: String=app.last_export_folder
	var standard_log:=FileAccess.get_file_as_string(standard_folder.path_join("encoder.log"))
	check(error.is_empty() and standard_log.begins_with("Profile: standard\n") and standard_log.contains('"-crf", "18"') and standard_log.contains('"-preset", "fast"') and standard_log.contains('"-b:a", "192k"'),"actual default MP4 retains original video/audio encoding parameters")
	check(Image.load_from_file(standard_folder.path_join("frame_000001.png")).get_data()==preview.get_data(),"Standard uses exact unchanged compositor input")
	var standard_hash:=FileAccess.get_sha256(standard)
	quality(1);var captured:=false
	var change_during_export:=func():
		if app.exporting and app.encoder_quality.disabled:quality(2)
	process_frame.connect(change_during_export)
	error=await app.export_movie(folder);process_frame.disconnect(change_during_export)
	var small: String=app.last_finished_movie;var small_folder: String=app.last_export_folder
	var small_log:=FileAccess.get_file_as_string(small_folder.path_join("encoder.log"))
	captured=small_log.begins_with("Profile: small\n")
	check(error.is_empty() and captured and small_log.contains('"-crf", "24"') and small_log.contains('"-b:a", "128k"'),"Smaller file profile is captured at start despite later widget mutation")
	check(FileAccess.get_sha256(small_folder.path_join("frame_000001.png"))==FileAccess.get_sha256(standard_folder.path_join("frame_000001.png")) and FileAccess.get_sha256(small_folder.path_join("mixed_audio.wav"))==FileAccess.get_sha256(standard_folder.path_join("mixed_audio.wav")),"profile changes leave rendered source frames and synchronized PCM identical")
	quality(0)
	var cancel_at_encode:=func():
		if app.exporting and app.encoder!=null and app.encoder.process_id>0:app.cancel_button.pressed.emit()
	process_frame.connect(cancel_at_encode);error=await app.export_movie(folder);process_frame.disconnect(cancel_at_encode)
	var retry_folder: String=app.last_export_folder;var first_hash:=FileAccess.get_sha256(retry_folder.path_join("frame_000001.png"));var mix_hash:=FileAccess.get_sha256(retry_folder.path_join("mixed_audio.wav"))
	check(error.to_lower().contains("cancel") and app.retry_encode_button.visible and app.last_finished_movie==small and FileAccess.get_file_as_string(retry_folder.path_join("encoder.log")).begins_with("Profile: standard\n"),"cancelled profile encode retains complete retry input and previous successful movie")
	app.encoder_quality.set_item_metadata(2,"unknown");quality(2);var retry: Dictionary=app.retry_render.duplicate(true);await app.retry_saved_movie()
	check(not app.exporting and app.retry_render==retry and app.retry_encode_button.visible and app.last_finished_movie==small and app.status.text.contains("profile"),"invalid retry profile refuses before changing frames, previous movie or retry state")
	app.encoder_quality.set_item_metadata(2,"high");quality(2);await app.retry_saved_movie();var high: String=app.last_finished_movie
	var high_log:=FileAccess.get_file_as_string(high.get_basename()+".log")
	check(high.get_base_dir()==retry_folder and high.get_file()!="movie.mp4" and high_log.begins_with("Profile: high\n") and high_log.contains('"-crf", "14"') and high_log.contains('"-preset", "slow"') and high_log.contains('"-b:a", "256k"'),"Retry MP4 actually encodes a separate High quality file with chosen settings")
	check(FileAccess.get_sha256(standard)==standard_hash and FileAccess.get_sha256(retry_folder.path_join("frame_000001.png"))==first_hash and FileAccess.get_sha256(retry_folder.path_join("mixed_audio.wav"))==mix_hash,"quality retry preserves original movie, PNG source and exact audio mix")
	app.encoder_quality.set_item_metadata(2,"unknown");var previous_folder: String=app.last_export_folder;error=await app.export_movie(folder)
	check(not error.is_empty() and not app.exporting and app.last_export_folder==previous_folder,"invalid normal profile refuses before creating a render folder")
	var image_error: String=await app.export_images(folder,true)
	check(image_error.is_empty() and FileAccess.file_exists(app.last_export_folder.path_join("sequence.json")),"PNG-only output remains independent of MP4 profile selection")
	app.encoder_quality.set_item_metadata(2,"high");quality(2)
	check(equal(world,World.portable(app.current_world())) and equal(shots,app.keys) and art.get_data()==pixels and FileAccess.get_sha256(cue)==cue_hash,"all profiles, failures and retries preserve authored world, camera, art and original cue")
	app.has_project.save_file(folder.path_join("Profiles.has"),"packed");await job();check(FileAccess.file_exists(folder.path_join("Profiles.has")),"ordinary scene remains saveable while High quality is selected")
	var expected:={"pixels":Storage.image_hash(art),"render":Storage.image_hash(preview)};FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify(expected,"",true,true))
	print("EXPORT_PROFILES_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movies":{"standard":standard,"small":small,"high":high},"reference":standard_folder.path_join("frame_000001.png")}));app.free();quit(0 if failures==0 else 1)
