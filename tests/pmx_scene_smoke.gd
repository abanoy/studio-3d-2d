extends SceneTree
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var app
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(180).timeout.connect(func():push_error("PMX scene watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
func jobs() -> void:
	while app.has_project.pid>0:await process_frame
	await settle()
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var reading: bool="--read" in args
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cold-cache" if reading else "cache")
	var packed:=folder.path_join("Street.has")
	if reading:
		app.has_project.open_file(packed);await jobs()
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
		check(not app.has_project.path.is_empty() and app.current_world().objects.size()==1,"cold HAS restores native PMX environment")
		check(Storage.image_hash(await app.renderer.capture(app.keys,app.layers,0,true))==expected.pixels,"cold PMX scene and independent overlay render exactly")
	else:
		check(app.load_scene(args[1]).is_empty(),"prepared native PMX imports through ordinary Scene")
		await settle();app.frame_3d_scene();await settle()
		check(app.renderer.last_framing.error.is_empty(),"native street geometry frames with finite bounds")
		app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)];app.video.duration_frames=24
		var cel:=Drawing.blank(1920,1080);cel.fill_rect(Rect2i(20,20,80,80),Color.CYAN);Drawing.insert(app.layers[1],0,24,cel);app.changed()
		var image: Image=await app.renderer.capture(app.keys,app.layers,0,true);image.save_png(folder.path_join("street.png"))
		check(image.get_size()==Vector2i(1920,1080) and image.get_pixel(40,40).g>0.9,"PMX environment composites with a separate editable overlay")
		app.has_project.save_file(packed,"packed");await jobs();check(app.has_project.path==packed,"native PMX environment saves as self-contained HAS")
		FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pixels":Storage.image_hash(image)}))
		var why: String=await app.export_movie(folder)
		check(why.is_empty() and Storage.image_hash(Image.load_from_file(app.last_export_folder.path_join("frame_000001.png")))==Storage.image_hash(image),"native PMX movie frame equals scene and overlay preview")
	var result:={"checks":checks,"failures":failures};print("PMX_SCENE "+JSON.stringify(result));app.free();quit(0 if failures==0 else 1)
