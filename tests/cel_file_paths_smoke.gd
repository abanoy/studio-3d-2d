extends "res://tests/movement_path_smoke.gd"
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Cel filename app watchdog");quit(2));call_deferred("run")
func source_project(path: String) -> Array:
	DirAccess.make_dir_recursive_absolute(path.path_join("art"));var layers:=[];var hashes:=[]
	for i in range(2):
		var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100+i*200,100,80,40),Color(.8,.2,.1,.5) if i==0 else Color(.1,.3,.9,.75));var name:="art/layer%d.png"%i;image.save_png(path.path_join(name));hashes.append(FileAccess.get_sha256(path.path_join(name)));layers.append({"id":"layer"+str(i),"name":"Layer "+str(i),"visible":true,"cels":[{"id":"same","start":0,"duration":48,"path":name}]})
	var data:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)],"world":World.empty(),"layers":layers,"audio":{},"editor":{"frame":0}}
	FileAccess.open(path.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(data));return hashes
func pixel_hashes() -> Array:
	var result:=[]
	for layer in app.layers:result.append(Storage.image_hash(layer.cels[0].image))
	return result
func run() -> void:
	var args:=OS.get_cmdline_user_args();folder=args[0];app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("reader-cache" if "--read" in args else "writer-cache")
	if "--read" in args:
		var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")));app.has_project.open_file(folder.path_join("safe.has"));await wait_job()
		check(app.has_project.path==folder.path_join("safe.has") and pixel_hashes()==expected.pixels,"cold packed Open preserves both distinct rasters despite equal cel IDs")
		check(app.layers[0].cels[0].id=="same" and app.layers[1].cels[0].id=="same","cold reader retains exact original IDs")
		app.set_frame(7);await settled();check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,7,1920,1080).get_data(),"cold actual GPU overlay matches independent layers")
		var picture: Image=await app.renderer.capture(app.keys,app.layers,7,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-7.png")).get_data(),"cold final composition matches pre-export scene")
		print("CEL_FILE_PATHS_READ ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();quit(0 if failures==0 else 1);return
	var directory:=folder.path_join("directory");var originals:=source_project(directory);check(app.open_project(directory),"Studio opens existing directory with equal cel IDs on two layers")
	var initial:=pixel_hashes();check(initial[0]!=initial[1],"source layers start with distinct exact raster data")
	check(app.import_audio(folder.path_join("tone.wav"),24).is_empty(),"independent audio imports at frame24")
	app.mode.select(0);app.change_mode(0);app.active_layer=0;app.layer_choice.select(0);app.tool.select(0);app.set_frame(7);app.color.color=Color.GREEN;app.radius.value=6
	var press:=InputEventMouseButton.new();press.button_index=MOUSE_BUTTON_LEFT;press.pressed=true;app.canvas_input(press,Vector2(400,200));app.paint_segment(Vector2(440,200));press.pressed=false;app.canvas_input(press,Vector2(440,200));await settled();var pixels:=pixel_hashes()
	check(pixels[0]!=initial[0] and pixels[1]==initial[1],"painting lower layer leaves equal-ID upper cel unchanged")
	app.save();await settled();check(not app.dirty and app.project_folder==directory,"ordinary directory Save completes through the normal app action")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("project.json")));var first: String=manifest.layers[0].cels[0].path;var second: String=manifest.layers[1].cels[0].path
	check(first!=second and Storage.safe_relative(first) and Storage.safe_relative(second),"normal Save gives equal-ID cels separate project-local PNG paths")
	check(manifest.layers[0].cels[0].id=="same" and manifest.layers[1].cels[0].id=="same","normal Save never renames document IDs")
	app.new_project();check(app.open_project(directory),"ordinary directory reopen succeeds");await settled()
	check(pixel_hashes()==pixels,"directory reopen retains painted lower layer and original upper layer exactly")
	check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,app.frame,1920,1080).get_data(),"reopened actual GPU overlay preserves both independent layers")
	app.set_frame(7);var picture: Image=await app.renderer.capture(app.keys,app.layers,7,true);picture.save_png(folder.path_join("expected-7.png"))
	var packed:=folder.path_join("safe.has");app.has_project.save_file(packed,"packed");await wait_job();check(app.has_project.path==packed,"directory project packages normally as self-contained HAS")
	var error: String=await app.export_movie(folder);check(error.is_empty(),"normal two-layer scene exports MP4")
	check(Image.load_from_file(app.last_export_folder.path_join("frame_000008.png")).get_data()==picture.get_data(),"movie frame7 equals exact reopened composition")
	var untouched:=true
	for i in range(2):untouched=untouched and FileAccess.get_sha256(directory.path_join("art/layer%d.png"%i))==originals[i]
	check(untouched and pixel_hashes()==pixels,"all saves/exports preserve imported PNGs and authored per-layer pixels")
	FileAccess.open(folder.path_join("expected.json"),FileAccess.WRITE).store_string(JSON.stringify({"pixels":pixels,"movie":app.last_export_folder.path_join("movie.mp4")}))
	print("CEL_FILE_PATHS_SMOKE ",JSON.stringify({"checks":checks,"failures":failures,"movie":app.last_export_folder.path_join("movie.mp4")}));await app.quit_studio();quit(0 if failures==0 else 1)
