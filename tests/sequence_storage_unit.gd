extends SceneTree
const Storage=preload("res://src/storage.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Timeline=preload("res://src/timeline.gd")
const World=preload("res://src/world_document.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
	var keys: Array=[Timeline.key(0,Vector3(0,2,5),Quaternion.IDENTITY,60)]
	var image:=Drawing.blank(1920,1080);image.fill_rect(Rect2i(800,400,100,100),Color(1,0,0,.5))
	var layers: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"paint","start":0,"duration":48,"image":image}]}]
	var scene:={"schema_version":4,"video":video,"camera_keys":keys,"world":World.empty(),"layers":layers,"audio":{}}
	var clip:={"id":"clip","asset_id":"child","start":0,"duration":48,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0,"keys":[Graph.key()]}
	var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Character","scene":scene,"clips":[]}],"clips":[clip]}
	var error:=Storage.save_project(folder,video,keys,[],"",0,{},{},{},true,World.empty(),{},[],graph)
	check(error.is_empty(),"nested source scenes save without flattening or external project references")
	var saved: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("project.json")))
	check(saved.schema_version==6 and saved.sequence_graph.assets[0].scene.schema_version==4,"root schema6 explicitly encloses ordinary editable world scenes")
	check(saved.sequence_graph.assets[0].scene.layers[0].cels[0].path.begins_with("cels/content/"),"child cels share the parent's content addressed store")
	var restored:=Storage.load_project(folder)
	check(not restored.has("error") and restored.sequence_graph.assets[0].scene.layers[0].cels[0].image.get_data()==image.get_data(),"full original child pixel bytes restore")
	check(Storage.readable_manifest(folder.path_join("project.json")),"new format remains eligible for safe backup")
	var before:=FileAccess.get_sha256(folder.path_join("project.json"))
	var bad:=graph.duplicate(true);bad.assets[0].clips=[clip.duplicate(true)];bad.assets[0].clips[0].id="cycle"
	check(not Storage.save_project(folder,video,keys,[],"",0,{},{},{},true,World.empty(),{},[],bad).is_empty() and FileAccess.get_sha256(folder.path_join("project.json"))==before,"cyclic edits refuse before replacing saved manifest")
	var malformed: Dictionary=saved.duplicate(true);malformed.schema_version=4
	check(Storage.decode_project(malformed,folder).has("error"),"older schema cannot silently discard an embedded sequence graph")
	malformed=saved.duplicate(true);malformed.sequence_graph.assets[0].scene.layers[0].cels[0].path="../outside.png"
	check(Storage.decode_project(malformed,folder).has("error"),"child image path traversal refuses")
	print("SEQUENCE_STORAGE_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"folder":folder}));quit(0 if failures==0 else 1)
