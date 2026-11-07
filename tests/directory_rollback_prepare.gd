extends SceneTree
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const SceneIO=preload("res://src/scene3d.gd")
const Timeline=preload("res://src/timeline.gd")
func _initialize() -> void:
 var base:=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(base);var source:=base.path_join("original.glb");var folder:=base.path_join("project");SceneIO.make_fixture(source)
 var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48};var keys: Array=[Timeline.key(0,Vector3.ZERO,Quaternion.IDENTITY,60)]
 var error:=Storage.save_project(folder,video,keys,[],"",0,{},{},{},true,World.empty())
 if not error.is_empty():push_error(error);quit(1);return
 var world:=World.empty();var actor:=World.object(source,"environment","Original figure");world.objects=[actor];error=Storage.save_project(folder,video,keys,[],"",1,{},{},{},true,world)
 if not error.is_empty():push_error(error);quit(1);return
 DirAccess.remove_absolute(folder.path_join(World.asset_path(actor.sha256)))
 var proof:={"project":folder,"original":source,"original_sha256":FileAccess.get_sha256(source),"primary_sha256":FileAccess.get_sha256(folder.path_join("project.json")),"backup_sha256":FileAccess.get_sha256(folder.path_join("project.backup.json"))}
 var file:=FileAccess.open(base.path_join("expected.json"),FileAccess.WRITE);file.store_string(JSON.stringify(proof));file.flush();file.close();print("DIRECTORY_ROLLBACK_PREPARED "+JSON.stringify(proof));quit()
