extends SceneTree
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
const Drawing=preload("res://src/drawing.gd")
const Guard=preload("res://src/project_payload_guard.gd")
var checks:=0
var failures:=0
var base: String
var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48}
var keys: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)]
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func save(folder: String,at: int,layers: Array=[],world: Dictionary={},addressed:=true) -> String:
 return Storage.save_project(folder,video,keys,layers,"",at,{},{},{},addressed,World.empty() if world.is_empty() else world)
func bytes(path: String,data: PackedByteArray) -> void:
 var file:=FileAccess.open(path,FileAccess.WRITE);file.store_buffer(data);file.close()
func _initialize() -> void:
 base=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(base);var source:=base.path_join("original.glb");SceneIO.make_fixture(source);var source_sha:=FileAccess.get_sha256(source)
 for fault in ["missing-glb","changed-glb","missing-png","changed-pixels","broken-png","unsafe-png"]:
  var folder:=base.path_join(fault);var empty:=save(folder,0);var layer: Array=[];var world:=World.empty();var actor: Dictionary={};var image: Image
  if fault.ends_with("glb"):
   actor=World.object(source,"environment","Original figure");world.objects=[actor]
  else:
   image=Drawing.blank(1920,1080);image.fill_rect(Rect2i(100,100,60,40),Color.RED);layer=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"cel","start":0,"duration":48,"image":image}]}]
  var second:=save(folder,1,layer,world);var backup:=folder.path_join("project.backup.json");var before:=FileAccess.get_sha256(backup)
  check(empty.is_empty() and second.is_empty() and not Storage.load_project(folder,"project.backup.json").has("error"),"%s starts with a valid independent rollback" % fault)
  var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("project.json")))
  if fault.ends_with("glb"):
   var target:=folder.path_join(World.asset_path(actor.sha256))
   if fault=="missing-glb":DirAccess.remove_absolute(target)
   else:bytes(target,"changed opaque asset".to_utf8_buffer())
  else:
   var target:=folder.path_join(str(manifest.layers[0].cels[0].path))
   if fault=="missing-png":DirAccess.remove_absolute(target)
   elif fault=="changed-pixels":
    var changed:=Drawing.blank(1920,1080);changed.fill(Color.BLUE);changed.save_png(target)
   elif fault=="broken-png":bytes(target,"broken".to_utf8_buffer())
   else:
    manifest.layers[0].cels[0].path="../original.png";bytes(folder.path_join("project.json"),JSON.stringify(manifest).to_utf8_buffer())
  check(Storage.readable_manifest(folder.path_join("project.json")) and not Storage.readable_payloads(folder,folder.path_join("project.json")),"%s metadata alone is insufficient; payload guard refuses" % fault)
  var repaired:=save(folder,2);var old:=Storage.load_project(folder,"project.backup.json")
  check(repaired.is_empty() and FileAccess.get_sha256(backup)==before and not old.has("error") and old.editor.frame==0,"%s cannot overwrite good rollback while valid replacement commits" % fault)
 var folder:=base.path_join("legacy-png");save(folder,0);var art:=Drawing.blank(1920,1080);art.fill(Color.CYAN);var layer: Array=[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"old","start":0,"duration":48,"image":art}]}];save(folder,1,layer,{},false)
 var previous: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("project.json")));check(not previous.layers[0].cels[0].has("pixel_sha256") and Storage.readable_payloads(folder,folder.path_join("project.json")),"legacy PNG without stored pixel checksum still validates by bounded decode")
 var result:=save(folder,2);var loaded:=Storage.load_project(folder,"project.backup.json")
 check(result.is_empty() and not loaded.has("error") and loaded.editor.frame==1 and Storage.image_hash(Drawing.image(loaded.layers[0].cels[0]))==Storage.image_hash(art),"valid legacy previous generation still rotates into exact editable rollback")
 folder=base.path_join("healthy");save(folder,0);save(folder,1,layer);var healthy:=FileAccess.get_sha256(folder.path_join("project.json"));save(folder,2)
 check(FileAccess.get_sha256(folder.path_join("project.backup.json"))==healthy,"healthy checksummed previous generation continues normal rotation")
 var tiny:=Drawing.blank(32,16);tiny.fill(Color(.3,.6,.9,.5));var path:=base.path_join("tiny.png");tiny.save_png(path);var digest:=Storage.image_hash(tiny);var guard:=Guard.new();var data:={"video":{"width":32,"height":16},"layers":[{"cels":[{"path":"tiny.png","pixel_sha256":digest}]}]}
 check(guard.valid(base,data) and guard.valid(base,data) and guard.png.decodes==1 and guard.png.hits==1,"one validation context retains only PNG digests and reuses exact decoded identity")
 var small_source:=base.path_join("opaque.bin");bytes(small_source,"opaque inventory only".to_utf8_buffer());var row:={"path":"opaque.bin","sha256":FileAccess.get_sha256(small_source)};data={"video":{"width":32,"height":16},"model":row,"scene":row,"layers":[]};guard=Guard.new()
 check(guard.valid(base,data) and guard.files==1,"duplicate asset validation retains digest strings without reloading geometry")
 data={"video":{"width":32,"height":16},"sequence_graph":{"assets":[{"scene":{"video":{"width":32,"height":16},"layers":[{"cels":[{"path":"tiny.png","pixel_sha256":digest}]}]}}]}}
 check(Guard.new().valid(base,data),"nested scene payloads are validated in the same bounded context")
 if OS.get_name()=="Linux":
  var alias:=base.path_join("linked.png");DirAccess.open(base).create_link(path,alias);data={"video":{"width":32,"height":16},"layers":[{"cels":[{"path":"linked.png","pixel_sha256":digest}]}]}
  check(not Guard.new().valid(base,data) and FileAccess.file_exists(path),"linked previous drawing refuses before reading outside managed descendants")
 check(FileAccess.get_sha256(source)==source_sha,"all rollback faults and repairs preserve original GLB bytes")
 print("DIRECTORY_ROLLBACK_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"scope":"owned metadata/asset/pixel rollback integrity; not native-rig or physical power-loss certification"}));quit(0 if failures==0 else 1)
