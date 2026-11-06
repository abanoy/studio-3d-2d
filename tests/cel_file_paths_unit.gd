extends SceneTree
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func expected(layers: Array) -> Array:
	var result:=[]
	for layer in layers:
		var rows:=[]
		for cel in layer.cels:rows.append([cel.id,Storage.image_hash(cel.image),int(cel.start),int(cel.duration)])
		result.append(rows)
	return result
func verify(folder: String,wanted: Array,unique: bool) -> bool:
	var loaded:=Storage.load_project(folder)
	if loaded.has("error"):print(loaded);return false
	var actual:=expected(loaded.layers);var paths:={}
	for layer in loaded.layers:
		for cel in layer.cels:
			if not Storage.safe_relative(cel.path) or not cel.path.begins_with("cels/") or not FileAccess.file_exists(folder.path_join(cel.path)):return false
			paths[cel.path]=true
	if actual!=wanted:
		for li in range(actual.size()):
			for ci in range(actual[li].size()):
				if actual[li][ci]!=wanted[li][ci]:print("CEL_PATH_ROUNDTRIP_DIFFERENCE ",JSON.stringify({"actual":actual[li][ci],"wanted":wanted[li][ci]}));return false
	return paths.size()==32 if unique else paths.size()==4
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var marker:=folder.path_join("escaped.png");var absolute_target:=folder.path_join("absolute-target.png");var sentinel:=PackedByteArray([97,114,116,105,115,116,32,109,97,114,107,101,114]);FileAccess.open(marker,FileAccess.WRITE).store_buffer(sentinel);FileAccess.open(absolute_target,FileAccess.WRITE).store_buffer(sentinel)
	var ids: Array=["../../../escaped","../parent",folder.path_join("absolute-target"),"C:relative","folder/name","folder"+String.chr(92)+"name",".","..","NUL","CON","same","same","α paint",String.chr(1)+"data","x".repeat(512),""]
	var layers:=[]
	for li in range(2):
		var images: Array=[]
		for variant in range(2):
			var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100+li*100,100+variant*80,60,40),[Color.RED,Color.GREEN,Color.BLUE,Color(.8,.2,.7,.5)][li*2+variant]);Drawing.touch(image);images.append(image)
		var cels:=[]
		for i in range(ids.size()):cels.append({"id":ids[i],"start":i,"duration":1,"image":images[i%2]})
		layers.append({"id":"layer"+str(li),"name":"Layer "+str(li),"visible":true,"opacity":.35 if li==1 else 1.,"cels":cels})
	var wanted:=expected(layers);var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)];var project:=folder.path_join("project")
	var error:=Storage.save_project(project,video,keys,layers,"",0,{},{},{},false,World.empty())
	check(error.is_empty(),"ordinary directory Save accepts opaque cel IDs without using them as filenames")
	check(FileAccess.get_file_as_bytes(marker)==sentinel and FileAccess.get_file_as_bytes(absolute_target)==sentinel,"parent/absolute-looking IDs cannot overwrite owned markers outside the project")
	check(verify(project,wanted,true),"32row-derived paths roundtrip every exact ID/range/RGBA despite duplicate IDs")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("project.json")));var canonical:=true
	for li in range(2):
		for ci in range(16):canonical=canonical and manifest.layers[li].cels[ci].path.get_file()=="layer_%d_cel_%d.png"%[li,ci]
	check(canonical,"filenames contain only derived row numbers and a fixed PNG suffix")
	check(manifest.layers[0].cels[0].id=="../../../escaped" and manifest.layers[1].cels[10].id=="same" and manifest.layers[1].opacity==.35,"filesystem encoding never rewrites binding IDs or layer opacity")
	var first: String=manifest.layers[0].cels[0].path;var first_hash:=FileAccess.get_sha256(project.path_join(first));var previous:=FileAccess.get_file_as_bytes(project.path_join("project.json"))
	error=Storage.save_project(project,video,keys,layers,"",0,{},{},{},false,World.empty())
	var second: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("project.json")))
	check(error.is_empty() and second.layers[0].cels[0].path!=first and FileAccess.get_sha256(project.path_join(first))==first_hash,"later revision keeps previous PNG files and uses new project-local paths")
	check(FileAccess.get_file_as_bytes(project.path_join("project.backup.json"))==previous and not Storage.load_project(project,"project.backup.json").has("error"),"previous manifest remains an exact readable backup")
	var invalid:=video.duplicate(true);invalid.duration_frames=0;var before:=FileAccess.get_file_as_bytes(project.path_join("project.json"))
	check(not Storage.save_project(project,invalid,keys,layers,"",0,{},{},{},false,World.empty()).is_empty() and FileAccess.get_file_as_bytes(project.path_join("project.json"))==before,"invalid later save preserves current manifest")
	for kind in ["content","recovery"]:
		var destination:=folder.path_join(kind);var recovery: Dictionary={"session_id":"fixture"} if kind=="recovery" else {}
		error=Storage.save_project(destination,video,keys,layers,"",0,{},recovery,{},kind=="content",World.empty())
		check(error.is_empty() and verify(destination,wanted,false),kind+" retains existing pixel-addressed sharing with all IDs/pixels intact")
	var legacy_source:=folder.path_join("source.glb");preload("res://src/scene3d.gd").make_empty(legacy_source);var legacy:=folder.path_join("legacy")
	error=Storage.save_project(legacy,video,keys,layers,legacy_source,0)
	check(error.is_empty() and verify(legacy,wanted,true) and Storage.load_project(legacy).schema_version==3,"legacy scene schema3 uses safe row paths without changing runtime dispatch")
	check(expected(layers)==wanted and FileAccess.get_file_as_bytes(marker)==sentinel and FileAccess.get_file_as_bytes(absolute_target)==sentinel,"all Save variants leave original source rasters, IDs and outside markers unchanged")
	print("CEL_FILE_PATHS_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"folder":folder}));quit(0 if failures==0 else 1)
