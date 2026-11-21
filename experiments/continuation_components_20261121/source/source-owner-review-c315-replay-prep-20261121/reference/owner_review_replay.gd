extends Node
# Private replay only. res:// remains the exact builder-owned review Studio.
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
const RasterReader=preload("res://src/cel_raster_reader.gd")
var app
var request: Dictionary={}
var report: Dictionary={"format":"has_owner_review_replay_1","checks":[],"failures":0}
var open_finished:=false
var open_ok:=false
var open_action:=""
var startup_finished:=false
var startup_result: Dictionary={}

func _ready() -> void:
	get_tree().create_timer(180).timeout.connect(func():push_error("Owner review replay watchdog");get_tree().quit(2))
	call_deferred("run")

func startup_completed(result: Dictionary) -> void:
	startup_result=result.duplicate(true);startup_finished=true

func normalized_path(value: String) -> String:
	var path:=value.replace("\\","/").simplify_path()
	if not path.is_absolute_path():path=ProjectSettings.globalize_path(path).replace("\\","/").simplify_path()
	path=path.trim_suffix("/")
	return path.to_lower() if OS.get_name()=="Windows" else path

func check(ok: bool,label: String) -> void:
	report.checks.append({"ok":ok,"label":label})
	if not ok:report.failures+=1
	print(("PASS " if ok else "FAIL ")+label)

func settled() -> void:
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw

func write_json(path: String,value: Variant) -> void:
	var stream:=FileAccess.open(path,FileAccess.WRITE)
	if stream:stream.store_string(JSON.stringify(value,"  ",true,true)+"\n");stream.close()
	else:push_error("Could not write replay evidence: "+path)

func state() -> Dictionary:
	var layers: Array=app.layers.duplicate(true)
	for layer in layers:
		for cel in layer.cels:
			cel.erase("image");cel.erase("raster_owner")
	return {"schema_version":4,"world":World.portable(app.current_world()),"camera_keys":app.keys.duplicate(true),"video":app.video.duplicate(true),"editor":{"frame":app.frame},"layers":layers,"audio":app.audio_document().duplicate(true),"palette":app.palette.duplicate(true)}

func camera_state() -> Dictionary:
	var camera: Camera3D=app.renderer.camera
	var t: Transform3D=camera.transform
	return {"origin":[t.origin.x,t.origin.y,t.origin.z],"basis":[t.basis.x.x,t.basis.x.y,t.basis.x.z,t.basis.y.x,t.basis.y.y,t.basis.y.z,t.basis.z.x,t.basis.z.y,t.basis.z.z],"fov":camera.fov,"near":camera.near,"far":camera.far}

func image_info(image: Image,path: String) -> Dictionary:
	if image==null or image.is_empty():return {"empty":true}
	image.convert(Image.FORMAT_RGBA8)
	var colors: Dictionary={};var lit:=0;var sampled:=0
	for y in range(0,image.get_height(),maxi(1,image.get_height()/120)):
		for x in range(0,image.get_width(),maxi(1,image.get_width()/160)):
			var color:=image.get_pixel(x,y);sampled+=1
			if maxf(color.r,maxf(color.g,color.b))>.025 and color.a>.1:lit+=1
			colors[color.to_rgba32()]=true
	var saved:=image.save_png(path)
	return {"empty":false,"width":image.get_width(),"height":image.get_height(),"pixel_sha256":RasterReader.digest_bytes(image.get_data()),"sampled_pixels":sampled,"nonblack_samples":lit,"distinct_sampled_colors":colors.size(),"save_error":saved,"png":path}

func canvas_image() -> Image:
	var image:=get_tree().root.get_texture().get_image()
	if image==null or image.is_empty():return null
	var area:=Rect2i(Vector2i(app.canvas.global_position),Vector2i(app.canvas.size)).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	return image.get_region(area) if area.has_area() else null

func finish() -> void:
	report["native_readbacks_at_finish"]=app.renderer.native_readbacks if is_instance_valid(app) else -1
	write_json(str(request.get("result","")),report)
	if is_instance_valid(app):app.free()
	await get_tree().process_frame
	print("OWNER_REVIEW_REPLAY "+JSON.stringify({"failures":report.failures,"package":request.get("package","")}))
	get_tree().quit(0 if report.failures==0 else 1)

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("Exactly one absolute replay request is required");get_tree().quit(2);return
	var parsed=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not parsed is Dictionary:push_error("Invalid replay request");get_tree().quit(2);return
	request=parsed
	report["package"]=request.package;report["profile"]=OS.get_user_data_dir();report["process_id"]=OS.get_process_id()
	report["project_root"]=ProjectSettings.globalize_path("res://")
	var ordinary_startup:=not ("--script" in OS.get_cmdline_args())
	for argument in args:
		if argument.contains("smoke"):ordinary_startup=false
	check(ordinary_startup,"replay uses ordinary scene startup without testing flags")
	if not ordinary_startup:await finish();return
	app=load("res://main.tscn").instantiate()
	app.recovery_root=request.folder.path_join("recovery")
	app.recent_path=request.folder.path_join("recent.json")
	app.display_prefs_path=request.folder.path_join("display.cfg")
	app.startup_recovery_finished.connect(startup_completed)
	add_child(app)
	app.autosave_enabled.button_pressed=false
	app.has_project.cache_root=request.folder.path_join("has-cache")
	app.reference_sheet.cache_root=request.folder.path_join("reference-cache")
	app.workspace_layout.path=request.folder.path_join("workspace-layout.json")
	var startup_began:=Time.get_ticks_msec()
	while not startup_finished and Time.get_ticks_msec()-startup_began<30000:await get_tree().process_frame
	report["normal_startup"]={"signal_seen":startup_finished,"result":startup_result,"home_visible":app.home.visible,"empty":app.current_world().objects.is_empty(),"simple":not app.advanced_mode}
	check(startup_finished and not startup_result.get("restored",true) and not startup_result.get("cancelled",true),"ordinary automatic recovery completes without restoring or cancelling the fresh scene")
	if not startup_finished:await finish();return
	await settled()
	check(app.current_world().objects.is_empty() and app.home.visible,"fresh process starts empty at Home")
	check(not FileAccess.file_exists(app.recent_path) and not FileAccess.file_exists(app.display_prefs_path),"per-project recent/display paths start absent")
	app.has_project.operation_finished.connect(func(action: String,success: bool):open_action=action;open_ok=success;open_finished=true)
	var began:=Time.get_ticks_msec()
	# Deliberately use the normal .has Python worker plus loader/install transaction.
	app.has_project.open_file(request.package)
	check(app.has_project.pid>0,"normal .has open started its Python worker")
	report["worker_pid"]=app.has_project.pid
	while not open_finished and Time.get_ticks_msec()-began<150000:await get_tree().process_frame
	report["open_ms"]=Time.get_ticks_msec()-began
	check(open_finished and open_action=="unpack" and open_ok,"normal open operation completed successfully")
	check(app.has_project.pid<0 and not app.has_project.project_loader.busy() and not app.exporting,"worker and project loader finished before replay")
	if not open_ok:
		report["open_error"]=app.open_project_error;await finish();return
	await settled()
	check(app.has_project.path==request.package and app.has_project.storage_mode=="packed","normal open retains packed package identity")
	var actual_cache:=normalized_path(app.project_folder)
	var expected_cache:=normalized_path(request.folder.path_join("has-cache"))
	report["project_folder"]=app.project_folder
	report["normalized_project_folder"]=actual_cache
	report["normalized_cache_root"]=expected_cache
	check(actual_cache.begins_with(expected_cache+"/"),"unpacked runtime assets stay in the fresh owned cache")
	check(not app.home.visible and not app.dirty and app.history.is_empty() and app.redo_history.is_empty(),"open installs an unedited project with empty Undo history")
	var before:=state();var camera_before:=camera_state()
	write_json(request.folder.path_join("observed-before.json"),before)
	var raster: Array=[]
	for layer in app.layers:
		for cel in layer.cels:
			var image:=Drawing.image(cel)
			var digest: String=RasterReader.digest_bytes(image.get_data()) if image!=null else ""
			raster.append({"layer_id":layer.id,"id":cel.id,"pixel_sha256":digest,"readable":image!=null})
			check(image!=null and digest==cel.get("pixel_sha256",""),"saved drawing pixels decode with their original checksum")
	report["rasters"]=raster
	var runtime: Array=[]
	for row in before.world.objects:
		var instance: RefCounted=app.renderer.world_runtime.instance(row.id)
		runtime.append({"id":row.id,"name":row.name,"asset_sha256":FileAccess.get_sha256(instance.data.source),"stored_sha256":row.sha256,"bones":instance.order.size(),"visible":instance.root.visible})
		check(FileAccess.get_sha256(instance.data.source)==row.sha256,"runtime asset checksum matches saved object "+row.name)
	report["runtime_objects"]=runtime
	check(app.mode.selected==1,"normal load starts in Scene / camera mode")
	app.scene_view.set_setup(true,false);app.scene_view.set_guides(false,false,false)
	await settled()
	var area: Rect2=app.canvas.scene_rect()
	check(app.canvas.scene_setup and area.size==Vector2(app.canvas.setup_size()) and area.position.length()<1.5,"Setup uses the full available scene area")
	report["setup_extent"]=[area.size.x,area.size.y]
	report["canvas_extent"]=[app.canvas.size.x,app.canvas.size.y]
	report["setup_image"]=image_info(canvas_image(),request.folder.path_join("setup.png"))
	check(not report.setup_image.get("empty",true) and report.setup_image.get("save_error",-1)==OK,"Setup canvas evidence is nonempty and saved")
	var native_setup: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true)
	report["native_setup"]=image_info(native_setup,request.folder.path_join("native-setup.png"))
	check(native_setup!=null and not native_setup.is_empty() and native_setup.get_size()==Vector2i(app.video.width,app.video.height) and report.native_setup.get("save_error",-1)==OK,"Setup captures and saves the actual native output size")
	if native_setup!=null and not native_setup.is_empty():
		check(report.native_setup.nonblack_samples>10 and report.native_setup.distinct_sampled_colors>2,"native saved camera capture contains nonuniform nonblack scene pixels")
	app.scene_view.set_setup(false,false)
	await settled()
	check(not app.canvas.scene_setup and app.canvas.scene_rect()==app.canvas.image_rect(),"Focus restores the output-shaped scene area")
	report["focus_image"]=image_info(canvas_image(),request.folder.path_join("focus.png"))
	check(not report.focus_image.get("empty",true) and report.focus_image.get("save_error",-1)==OK,"Focus canvas evidence is nonempty and saved")
	var native_focus: Image=await app.renderer.capture(app.keys,app.layers,app.frame,true)
	report["native_focus"]=image_info(native_focus,request.folder.path_join("native-focus.png"))
	check(native_setup!=null and native_focus!=null and not native_setup.is_empty() and not native_focus.is_empty() and report.native_focus.get("save_error",-1)==OK and native_setup.get_data()==native_focus.get_data(),"Setup and Focus preserve and save identical native render pixels")
	app.scene_view.set_setup(true,false)
	await settled()
	var after:=state()
	write_json(request.folder.path_join("observed-after.json"),after)
	check(before==after and camera_before==camera_state(),"view toggles and captures preserve all project state and shot camera")
	check(not app.dirty and app.history.is_empty() and app.redo_history.is_empty() and app.renderer.native_readbacks==0,"replay ends unedited with no retained readback")
	report["camera_before"]=camera_before;report["camera_after"]=camera_state()
	report["load_worker_ms"]=app.has_project.last_load_worker_ms;report["install_ms"]=app.has_project.last_install_ms
	await finish()
