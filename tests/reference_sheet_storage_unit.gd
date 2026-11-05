extends SceneTree
const Data=preload("res://src/reference_sheet_data.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var png:=folder.path_join("Original sheet α.png");var image:=Image.create(32,16,false,Image.FORMAT_RGBA8);image.fill(Color(1,.25,.5,.5));image.save_png(png)
	var loaded:=Data.read_image(png);check(not loaded.has("error") and loaded.image.get_data()==image.get_data(),"bounded PNG read preserves exact original transparency")
	var cached:=Data.cache_image(loaded,folder.path_join("cache"));check(not cached.has("error") and FileAccess.get_sha256(cached.source)==loaded.sha256,"owned content cache preserves original PNG bytes")
	var reference:={"format":Data.FORMAT,"name":"Original sheet α.png","source":cached.source,"sha256":loaded.sha256}
	var portable:=Data.portable(reference);check(Data.error(reference).is_empty() and Data.error(portable,true).is_empty(),"live and portable reference identities validate strictly")
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,2,5),Quaternion.IDENTITY,60)]
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[]}]
	var legacy:=folder.path_join("legacy");var why:=Storage.save_project(legacy,video,keys,layers,"res://examples/room.glb",0,{},{},{},true,{}, {},[],{},null,reference)
	check(why.is_empty(),"schema7 wraps a legacy scene without requiring a world conversion")
	if not why.is_empty():print(why);quit(1);return
	var saved: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(legacy.path_join("project.json")))
	check(saved.schema_version==7 and saved.content_schema_version==3 and saved.reference_sheet==JSON.parse_string(JSON.stringify(portable)),"portable manifest declares explicit content schema and reference PNG")
	var restored:=Storage.load_project(legacy)
	check(not restored.has("error") and restored.schema_version==3 and restored.reference_sheet.sha256==reference.sha256 and restored.reference_sheet.name==reference.name,"decode retains legacy runtime dispatch with validated project reference")
	check(Storage.readable_manifest(legacy.path_join("project.json")),"recovery catalog recognizes the versioned manifest")
	var bad_versions: Array=[true,0,7,3.5,"3",NAN]
	check(bad_versions.all(func(version):var bad:=saved.duplicate(true);bad.content_schema_version=version;return Data.unwrap(bad).has("error")),"invalid wrapper versions refuse without recursive schema ambiguity")
	var bad_refs: Array=[]
	for pair in [["path","../escape.png"],["path","references/other.png"],["sha256","bad"],["name","bad\nname"],["name","a/b.png"],["name",""],["format","unknown"]]:
		var bad:=portable.duplicate(true);bad[pair[0]]=pair[1];bad_refs.append(bad)
	var unknown:=portable.duplicate(true);unknown["script"]="../../run.gd";bad_refs.append(unknown)
	check(bad_refs.all(func(value):return not Data.error(value,true).is_empty()),"malformed paths names identities and unknown fields all refuse")
	for version in [3,4,5,6]:
		var downgrade:=saved.duplicate(true);downgrade.schema_version=version
		check(Storage.decode_project(downgrade,legacy).has("error"),"known reference fields cannot downgrade to schema"+str(version))
	var before:=FileAccess.get_file_as_bytes(legacy.path_join("project.json"));var changed:=reference.duplicate(true);changed.sha256="0".repeat(64)
	why=Storage.save_project(legacy,video,keys,layers,"res://examples/room.glb",0,{},{},{},true,{}, {},[],{},null,changed)
	check(not why.is_empty() and FileAccess.get_file_as_bytes(legacy.path_join("project.json"))==before,"changed reference source refuses before replacing a good manifest")
	var missing:=saved.duplicate(true);missing.reference_sheet.sha256="1".repeat(64);missing.reference_sheet.path="references/"+missing.reference_sheet.sha256+".png"
	check(Storage.decode_project(missing,legacy).has("error"),"missing managed reference source refuses before installing project")
	for mode in [4,5,6]:
		var world:=World.empty()
		if mode==5:world.format=World.EFFECT_FORMAT;world["effects"]=[]
		var graph:={}
		if mode==6:
			var child:={"schema_version":4,"video":video,"camera_keys":keys,"layers":layers,"audio":{},"world":World.empty()}
			graph={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Child","scene":child,"clips":[]}],"clips":[]}
		var target:=folder.path_join("content"+str(mode));why=Storage.save_project(target,video,keys,layers,"",0,{},{},{},true,world,{},[],graph,null,reference)
		var result:=Storage.load_project(target) if why.is_empty() else {"error":why}
		check(not result.has("error") and result.schema_version==mode and result.reference_sheet.sha256==reference.sha256,"reference round-trips existing content schema"+str(mode))
	check(FileAccess.get_sha256(png)==loaded.sha256,"original reference PNG remains byte-identical")
	print("REFERENCE_SHEET_STORAGE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
