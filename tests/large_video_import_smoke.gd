extends "res://tests/large_project_smoke.gd"
var ingress_frames:=0
var ingress_max_gap_ms:=0.
var ingress_last:=0
var measuring:=false
func _initialize() -> void:
	create_timer(900).timeout.connect(func():push_error("Large video watchdog");quit(2));process_frame.connect(tick);call_deferred("run")
func tick() -> void:
	if not measuring:return
	var now:=Time.get_ticks_usec()
	if ingress_last>0:ingress_max_gap_ms=maxf(ingress_max_gap_ms,float(now-ingress_last)/1000.)
	ingress_last=now;ingress_frames+=1
func wait_phase(value: String) -> void:
	while not app.video_importer.phase.is_empty() and app.video_importer.phase!=value:await process_frame
	await settled()
func prepare_video(source: String) -> void:
	app.video_importer.begin(source);await wait_phase("layers")
	check(app.video_importer.phase=="layers","real400frame local video reaches ordinary review")
	if app.video_importer.phase!="layers":print("LARGE_VIDEO_ERROR "+app.status.text);return
	app.video_importer.review.confirmed.emit();await wait_phase("candidate")
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];var reading:="--read" in args
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("reader-recovery" if reading else "recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if reading else "writer-cache")
	var packed:=folder.path_join("Video400.has")
	if reading:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(packed);await wait_job()
		check(app.has_project.path==packed and total()==400 and app.video.duration_frames==400 and app.layers[2].origin.format=="studio_drawing_origin_4","cold packed source/job/cache-offline Open restores all400editable video drawings and extended ancestry")
		check(hashes()==expected.pixels,"all400cold pixel identities exactly match prepared artwork")
		for at in [399,0,137,250]:
			var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);check(picture.get_data()==Image.load_from_file(folder.path_join("frame%d.png"%at)).get_data(),"cold GPU scene/video/cel composition exactly repeats frame"+str(at))
		var budget: Dictionary=app.raster_budget.sample();check(budget.owners==400 and budget.accounted_bytes<=budget.owner_limit_bytes,"cold400video owners stay inside unchanged320MiB registered admission")
		print("LARGE_VIDEO_READ "+JSON.stringify({"checks":checks,"failures":failures,"memory":budget}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var source:=folder.path_join("source.mov");var sha:=FileAccess.get_sha256(source);var map:=folder.path_join("map.glb");DirAccess.copy_absolute("res://examples/tutorials/Practice room.glb",map);var map_sha:=FileAccess.get_sha256(map)
	app.new_project();app.show_project_options();await settled();var length_error: String=app.project_timing.apply_duration(400);app.project_options.hide();check(length_error.is_empty(),"normal parent project duration supports400frames")
	if not length_error.is_empty():print("LARGE_VIDEO_LENGTH_ERROR "+length_error);await app.quit_studio();quit(1);return
	check(app.append_object(Model.definition(map),"environment").is_empty(),"original 3D map remains independent of video artwork")
	app.renderer.camera.position=Vector3(4,3,7);app.renderer.camera.look_at(Vector3(0,1,0));app.keys=[Model.Timeline.from_camera(0,app.renderer.camera,"ease"),Model.Timeline.from_camera(400,app.renderer.camera,"ease")];var shots: Array=app.keys.duplicate(true);var world: Dictionary=app.current_world().duplicate(true);app.mode.select(0);app.change_mode(0);app.set_frame(0)
	measuring=true;var started:=Time.get_ticks_msec();await prepare_video(source);measuring=false;var first_prepare_ms:=Time.get_ticks_msec()-started;var importer=app.video_importer
	check(importer.phase=="candidate" and importer.decoded.size()==400,"real FFmpeg/incremental admission prepares400complete distinct editable holds")
	if importer.phase!="candidate":print("LARGE_VIDEO_ERROR "+app.status.text);await app.quit_studio();quit(1);return
	var first_cache=importer.raster_reader.adaptive_cache;var staged: Dictionary={"owners":first_cache.live_owners().size(),"accounted_bytes":first_cache.owned_bytes()+first_cache.retained_bytes,"limit":first_cache.owner_limit}
	check(staged.owners==400 and staged.accounted_bytes<=staged.limit and importer.decoded.all(func(cel):return cel.has("raster_owner") and not cel.has("image") and not cel.raster_owner.is_pinned()),"pending400drawings use cold registered owners under the unchanged byte limit")
	var pending: Array=importer.decoded.map(func(cel):return weakref(cel.raster_owner));importer.cancel();await settled()
	check(importer.phase.is_empty() and importer.raster_reader==null and importer.decoded.is_empty() and pending.all(func(owner):return owner.get_ref()==null) and first_cache.live_owners().is_empty() and app.layers.size()==2,"Cancel releases all400pending owners without adopting a layer")
	first_cache=null
	measuring=true;ingress_last=0;started=Time.get_ticks_msec();await prepare_video(source);measuring=false;var second_prepare_ms:=Time.get_ticks_msec()-started
	check(importer.phase=="candidate" and importer.decoded.size()==400 and app.keys==shots and app.current_world()==world,"repeat preparation leaves original camera/world unchanged")
	if importer.phase!="candidate":print("LARGE_VIDEO_ERROR "+app.status.text);await app.quit_studio();quit(1);return
	var original: Array=[];var encoded_bytes:=0
	for row in importer.candidate.holds:
		var image:=Image.load_from_file(row.path);image.convert(Image.FORMAT_RGBA8);original.append(Storage.image_hash(image));encoded_bytes+=FileAccess.get_file_as_bytes(row.path).size()
	var packet: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(importer.job.path_join("prepared/clip.json")));var unique: Dictionary={}
	for pixel in original:unique[pixel]=true
	check(original.size()==400 and unique.size()==400 and encoded_bytes<=256*1024*1024,"independent prepared PNG reads prove400uniquefullHDpixels inside unchanged256MiB staging")
	importer.scrub.value=399;await settled();check(app.frame==0 and importer.phase=="candidate","large source preview remains independent of scene playhead")
	var job: String=importer.job;var history: int=app.history.size();importer.preview.confirmed.emit();await settled()
	check(total()==400 and app.layers.size()==3 and app.history.size()==history+1 and hashes()==original,"ordinary Add adopts all400pixel-identical drawings as one Undo")
	app.undo();check(total()==0 and app.keys==shots and app.current_world()==world,"400drawing import Undo preserves original scene");app.redo();check(total()==400 and hashes()==original,"import Redo restores every prepared pixel identity")
	app.active_layer=2;app.refresh_layer_choices();app.set_frame(137);app.tool.select(0);app.brush_pressure.button_pressed=false;app.color.color=Color.CYAN;app.radius.value=6
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=true;app.canvas_input(event,Vector2(900,700));app.paint_segment(Vector2(930,700));event.pressed=false;app.canvas_input(event,Vector2(930,700));await settled();var edited:=hashes()
	check(edited.size()==400 and edited[137]!=original[137] and edited.slice(0,137)==original.slice(0,137) and edited.slice(138)==original.slice(138),"actual brush edits one imported drawing and preserves399peers")
	app.undo();check(hashes()==original,"imported brush Undo restores400originalpixels");app.redo();check(hashes()==edited,"imported brush Redo restores exact independent edit");app.undo()
	for at in [399,0,137,250]:
		app.set_frame(at);await settled();var picture: Image=await app.renderer.capture(app.keys,app.layers,at,true);picture.save_png(folder.path_join("frame%d.png"%at));check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,at,1920,1080).get_data(),"actual GPU artwork overlay matches400cel composition at"+str(at))
	app.set_frame(137);started=Time.get_ticks_msec();app.changed();app.autosave_tick(true);await preload("res://tests/recovery_wait.gd").checkpoint(app);var checkpoint_ms:=Time.get_ticks_msec()-started;var recovered:=Storage.load_project(app.recovery_root.path_join(app.recovery_session),"project.json",true,1)
	check(not recovered.has("error") and recovered.layers[2].cels.size()==400 and recovered.layers[2].origin.duration==400,"real background recovery stores all400video drawings and source history")
	recovered={};started=Time.get_ticks_msec();app.has_project.save_file(packed,"packed");await wait_job();var save_ms:=Time.get_ticks_msec()-started;check(app.has_project.path==packed and FileAccess.file_exists(packed),"ordinary packed Save retains400prepared drawings")
	var movie_error: String=await app.export_movie(folder);check(movie_error.is_empty(),"real400frame MP4 completes from admitted prepared artwork")
	if not movie_error.is_empty():print("LARGE_VIDEO_EXPORT_ERROR "+movie_error);await app.quit_studio();quit(1);return
	for at in [399,0,137,250]:check(Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png"%(at+1))).get_data()==Image.load_from_file(folder.path_join("frame%d.png"%at)).get_data(),"MP4 input exactly matches final scene/video frame"+str(at))
	var budget: Dictionary=app.raster_budget.sample();check(budget.owners==400 and budget.accounted_bytes<=budget.owner_limit_bytes and app.keys==shots and app.current_world()==world and FileAccess.get_sha256(source)==sha and FileAccess.get_sha256(map)==map_sha,"large video workflow preserves source/map/camera/world and registered byte bound")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pixels":original,"source_sha":sha,"map_sha":map_sha}));var proof: Dictionary={"checks":checks,"failures":failures,"movie":app.last_finished_movie,"job":job,"first_prepare_ms":first_prepare_ms,"second_prepare_ms":second_prepare_ms,"checkpoint_ms":checkpoint_ms,"save_ms":save_ms,"ingress_application_frames":ingress_frames,"ingress_max_frame_gap_ms":ingress_max_gap_ms,"prepared_PNG_bytes":encoded_bytes,"staged_memory":staged,"final_memory":budget,"source_duration":packet.source.source_duration}
	print("LARGE_VIDEO_WRITE "+JSON.stringify(proof));await app.quit_studio();quit(0 if failures==0 else 1)
