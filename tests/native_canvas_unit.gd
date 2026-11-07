extends SceneTree
const Canvas=preload("res://src/canvas_size.gd")
const Storage=preload("res://src/storage.gd")
const Graph=preload("res://src/sequence_graph.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 for id in Canvas.PROFILES:
  var size: Vector2i=Canvas.PROFILES[id];var video:={"width":size.x,"height":size.y}
  check(Canvas.error(video).is_empty() and Canvas.profile(video)==id and Canvas.delivery(video)==id,"supported native metadata selects its own delivery: "+id)
  var data:={"video":video,"layers":[{"cels":[{},{},{},{}]}]}
  check(Storage.raster_reserve(data)==size.x*size.y*16,"adaptive admission estimate uses actual native pixels: "+id)
  check(Graph.mask_error({"rect":[0,0,size.x,size.y],"invert":false},size).is_empty() and not Graph.mask_error({"rect":[size.x-1,size.y-1,2,2],"invert":false},size).is_empty(),"native mask includes exact border and refuses overflow: "+id)
 for invalid in [null,[],{},true,{"width":true,"height":720},{"width":"1280","height":720},{"width":1280,"height":1080},{"width":640,"height":360},{"width":3840,"height":2160},{"width":NAN,"height":720},{"width":INF,"height":720}]:
  check(not Canvas.error(invalid).is_empty() and Canvas.size(invalid)==Vector2i.ZERO,"invalid/unsupported native metadata refuses safely: "+str(invalid))
 check(Canvas.profile({"width":1280.0,"height":720.0})=="720p","JSON whole float dimensions preserve native profile identity")
 check(Canvas.delivery({"width":960,"height":540,"output_size":"1080p"})=="1080p","explicit delivery override preserves its distinct profile")
 var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 var video:={"width":1280,"height":720,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[preload("res://src/timeline.gd").key(0,Vector3.ZERO,Quaternion.IDENTITY,60)];var world:=preload("res://src/world_document.gd").empty()
 var first:=Storage.save_project(folder,video,keys,[],"",0,{},{},{},true,world);var second:=Storage.save_project(folder,video,keys,[],"",1,{},{},{},true,world);var backup:=FileAccess.get_sha256(folder.path_join("project.backup.json"));var primary:=FileAccess.get_sha256(folder.path_join("project.json"));var invalid:=video.duplicate(true);invalid.width=900;invalid.height=900
 check(first.is_empty() and second.is_empty() and not Storage.save_project(folder,invalid,keys,[],"",2,{},{},{},true,world).is_empty() and FileAccess.get_sha256(folder.path_join("project.json"))==primary,"unsupported native save refuses before replacing a valid primary")
 var bad: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("project.json")));bad.video=invalid;var file:=FileAccess.open(folder.path_join("project.json"),FileAccess.WRITE);file.store_string(JSON.stringify(bad));file.close()
 check(not Storage.readable_manifest(folder.path_join("project.json")),"metadata-only primary with unsupported native dimensions is not eligible for rollback rotation")
 check(Storage.save_project(folder,video,keys,[],"",2,{},{},{},true,world).is_empty() and FileAccess.get_sha256(folder.path_join("project.backup.json"))==backup and not Storage.load_project(folder,"project.backup.json").has("error"),"repairing unsupported native primary preserves its valid previous backup")
 print("NATIVE_CANVAS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
