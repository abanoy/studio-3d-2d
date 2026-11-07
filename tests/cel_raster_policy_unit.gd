extends SceneTree
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const LIMIT=64*1024*1024
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func scene(count: int) -> Dictionary:
	var cels: Array=[]
	for i in range(count):cels.append({"id":"cel"+str(i),"start":i,"duration":1,"path":"drawing.png","pixel_sha256":""})
	return {"schema_version":4,"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"world":World.empty(),"camera_keys":[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)],"layers":[{"id":"ink","name":"Ink","visible":true,"cels":cels}],"audio":{},"editor":{"frame":0}}
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);var picture:=Drawing.blank(1920,1080);picture.fill_rect(Rect2i(10,10,100,100),Color.RED);picture.save_png(folder.path_join("drawing.png"));var hash:=Storage.image_hash(picture)
	check(Storage.raster_reserve(null)==0 and Storage.raster_reserve({})==0 and Storage.raster_reserve({"layers":false})==0,"policy estimate handles absent/malformed tracks without validating them")
	check(Storage.raster_reserve(scene(8))<=LIMIT and Storage.raster_reserve(scene(9))>LIMIT,"64MiB policy separates eight and nine fullHD cel records")
	for count in [8,9]:
		var data:=scene(count)
		for cel in data.layers[0].cels:cel.pixel_sha256=hash
		FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(data));var loaded:=Storage.load_project(folder,"project.json",true,LIMIT)
		check(not loaded.has("error") and loaded.layers[0].cels.all(func(cel):return cel.has("raster_owner") if count==9 else cel.has("image")),"automatic policy installs expected ownership for%dcel project"%count)
		var eager:=Storage.load_project(folder,"project.json",false,LIMIT);check(not eager.has("error") and eager.layers[0].cels[0].has("image"),"explicit eager path remains available at%dcel size"%count)
		var forced:=Storage.load_project(folder,"project.json",true,0);check(not forced.has("error") and forced.layers[0].cels[0].has("raster_owner"),"explicit adaptive path remains available at%dcel size"%count)
	var root_scene:=scene(4);var child:=scene(5);root_scene.schema_version=6;root_scene.sequence_graph={"format":"studio_sequences_1","assets":[{"id":"child","name":"Child","scene":child,"clips":[]}],"clips":[]}
	for doc in [root_scene,child]:
		for cel in doc.layers[0].cels:cel.pixel_sha256=hash
	check(Storage.raster_reserve(root_scene)==9*1920*1080*4,"policy counts root and child cel records globally")
	FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(root_scene));var nested:=Storage.load_project(folder,"project.json",true,LIMIT)
	check(not nested.has("error") and nested.layers[0].cels[0].has("raster_owner") and nested.sequence_graph.assets[0].scene.layers[0].cels[0].has("raster_owner"),"nested threshold enables one shared adaptive context for parent and child")
	root_scene.layers[0].cels[3].path="../drawing.png";FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE).store_string(JSON.stringify(root_scene))
	check(Storage.load_project(folder,"project.json",true,LIMIT).has("error"),"automatic policy does not bypass unsafe path rejection")
	print("CEL_RASTER_POLICY_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
