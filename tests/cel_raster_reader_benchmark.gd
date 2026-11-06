extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func make_project(folder: String) -> String:
	DirAccess.make_dir_recursive_absolute(folder);var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,200,100),Color(.2,.7,.8,.5));image.save_png(folder.path_join("drawing.png"));var digest:=Storage.image_hash(image);var cels:=[]
	for i in range(32):cels.append({"id":"cel"+str(i),"start":i,"duration":1,"path":"drawing.png","pixel_sha256":digest})
	var project:={"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)],"world":World.empty(),"layers":[{"id":"ink","name":"Ink","visible":true,"cels":cels}],"audio":{},"editor":{"frame":0}}
	FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(project));return digest
func one(folder: String,digest: String) -> Dictionary:
	var before:=OS.get_static_memory_usage();var started:=Time.get_ticks_usec();var loaded:=Storage.load_project(folder);var milliseconds:=(Time.get_ticks_usec()-started)/1000.;var loaded_bytes:=OS.get_static_memory_usage()-before
	if loaded.has("error"):return loaded
	var images: Array=[];var ids:={};var exact:=true
	for cel in loaded.layers[0].cels:images.append(cel.image);ids[cel.image.get_instance_id()]=true;exact=exact and Storage.image_hash(cel.image)==digest
	var pre_edit:=OS.get_static_memory_usage();images[0].set_pixel(0,0,Color.RED);var edit_bytes:=OS.get_static_memory_usage()-pre_edit;var independent: bool=images[0].get_pixel(0,0)==Color.RED
	for i in range(1,32):independent=independent and Storage.image_hash(images[i])==digest
	return {"milliseconds":milliseconds,"loaded_bytes":loaded_bytes,"edit_added_bytes":edit_bytes,"independent_edit":independent,"all_original_rgba_exact":exact,"unique_image_objects":ids.size()}
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var digest:=make_project(folder);var runs:=[]
	for i in range(3):runs.append(one(folder,digest))
	var ok:=runs.all(func(row):return not row.has("error") and row.independent_edit and row.all_original_rgba_exact and row.unique_image_objects==32)
	print("RASTER_OPEN_BENCHMARK ",JSON.stringify({"ok":ok,"runs":runs,"cel_count":32,"raster":[1920,1080],"source_sha256":FileAccess.get_sha256(folder.path_join("drawing.png")),"pixel_sha256":digest,"scope":"three same-process Storage.load_project calls on32independent cel records referencing one original PNG; existing schema4 and48frames; static memory deltas exclude fixture creation, hash assertions and post-load edit"}));quit(0 if ok else 1)
