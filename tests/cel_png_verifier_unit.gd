extends SceneTree
const Verifier=preload("res://src/cel_png_verifier.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var folder:=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,80,40),Color.CYAN);var path:=folder.path_join("test.png");image.save_png(path);var digest:=Storage.image_hash(image);var verifier:=Verifier.new()
	check(verifier.matches(path,1920,1080,digest) and verifier.matches(path,1920,1080,digest) and verifier.reads==2 and verifier.decodes==1 and verifier.hits==1,"every file is read but identical PNG decodes once")
	check(verifier.verified.values().all(func(value):return value is String),"cache retains digest strings only")
	check(not verifier.matches(path,1920,1080,"0".repeat(64)),"cached content cannot bypass expected pixel checksum")
	DirAccess.remove_absolute(path);check(not verifier.matches(path,1920,1080,digest),"cached identity cannot conceal missing file")
	var other:=Drawing.blank(1920,1080);other.fill(Color.MAGENTA);other.save_png(path);check(not verifier.matches(path,1920,1080,digest),"changed bytes cannot borrow old verification")
	var project:=folder.path_join("project");var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"a","start":0,"duration":48,"image":image}]}];var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
	check(Storage.save_project(project,video,keys,layers,"",0,{},{},{},true,World.empty()).is_empty(),"initial content-addressed Save succeeds")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("project.json")));var cached: String=project.path_join(manifest.layers[0].cels[0].path)
	var wrong:=Image.create_from_data(960,2160,false,Image.FORMAT_RGBA8,image.get_data());wrong.save_png(cached)
	check(Storage.image_hash(wrong)==digest,"wrong-dimension fixture has identical pixel bytes")
	check(Storage.save_project(project,video,keys,layers,"",0,{},{},{},true,World.empty()).is_empty() and not Storage.load_project(project).has("error") and Image.load_from_file(cached).get_size()==Vector2i(1920,1080),"Save repairs wrong canvas dimensions even when pixel hash matches")
	FileAccess.open(cached,FileAccess.WRITE).store_string("truncated PNG")
	check(Storage.save_project(project,video,keys,layers,"",0,{},{},{},true,World.empty()).is_empty() and not Storage.load_project(project).has("error"),"Save atomically repairs truncated cached PNG")
	var before:=FileAccess.get_file_as_bytes(project.path_join("project.json"));var bad:=video.duplicate(true);bad.duration_frames=0
	check(not Storage.save_project(project,bad,keys,layers,"",0,{},{},{},true,World.empty()).is_empty() and FileAccess.get_file_as_bytes(project.path_join("project.json"))==before,"failed Save preserves previous manifest")
	print("CEL_PNG_VERIFIER_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
