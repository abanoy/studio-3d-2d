extends SceneTree
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
 var args:=OS.get_cmdline_user_args();var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3(0,1,5),Quaternion.IDENTITY,60)]
 var why:=Storage.save_project(args[0],video,keys,[],"",int(args[1]),{},{},{},true,World.empty());var loaded:=Storage.load_project(args[0]);var result:={"error":why,"load_error":loaded.get("error",""),"frame":loaded.get("editor",{}).get("frame",-1)}
 var file:=FileAccess.open(args[2],FileAccess.WRITE);file.store_string(JSON.stringify(result));file.flush();file.close();print("DIRECTORY_COMMIT_SMOKE "+JSON.stringify(result));quit()
