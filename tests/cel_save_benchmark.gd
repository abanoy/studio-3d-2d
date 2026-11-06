extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
	var folder:=OS.get_cmdline_user_args()[0];var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,200,100),Color(.2,.7,.8,.5));var cels:=[]
	for i in range(32):cels.append({"id":"cel"+str(i),"start":i,"duration":1,"image":image.duplicate()})
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":cels}];var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
	var error:=Storage.save_project(folder,video,keys,layers,"",0,{},{},{},true,World.empty());var runs:=[];var ok:=error.is_empty();var digest:=Storage.image_hash(image)
	for i in range(3):
		var started:=Time.get_ticks_usec();error=Storage.save_project(folder,video,keys,layers,"",0,{},{},{},true,World.empty());runs.append((Time.get_ticks_usec()-started)/1000.);ok=ok and error.is_empty()
	var loaded:=Storage.load_project(folder)
	ok=ok and not loaded.has("error")
	if not loaded.has("error"):
		for cel in loaded.layers[0].cels:ok=ok and Storage.image_hash(cel.image)==digest
	print("CEL_SAVE_BENCHMARK ",JSON.stringify({"ok":ok,"milliseconds":runs,"cels":32,"raster":[1920,1080],"scope":"warm content-addressed saves of32independent Image resources with identical pixels; fixture creation and readback excluded"}));quit(0 if ok else 1)
