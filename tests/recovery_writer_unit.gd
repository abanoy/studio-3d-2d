extends SceneTree
const Writer=preload("res://src/recovery_writer.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
class HeldWriter extends Writer:
 var gate:=Semaphore.new()
 var mutex:=Mutex.new()
 var entered:=false
 func persist(project: Dictionary,request: Dictionary) -> String:
  mutex.lock();entered=true;mutex.unlock();gate.wait();return super.persist(project,request)
 func reached() -> bool:
  mutex.lock();var result:=entered;mutex.unlock();return result
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 create_timer(30).timeout.connect(func():push_error("Writer unit watchdog");quit(2));call_deferred("run")
func run() -> void:
 var folder: String=OS.get_cmdline_user_args()[0];var image:=Drawing.blank(1920,1080);image.fill(Color(.2,.4,.6,.5));var original:=Storage.image_hash(image);var cache:=Cache.new();var owner=Owner.from_image(image,cache).owner
 var project:={"video":{"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[preload("res://src/timeline.gd").key(0,Vector3.ZERO,Quaternion.IDENTITY,60)],"layers":[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"one","start":0,"duration":48,"raster_owner":owner}]}],"audio":{},"world":preload("res://src/world_document.gd").empty(),"editor":{"frame":3},"palette":[]}
 var request:={"root":folder,"session":"one","revision":7,"origin":"manual.has","actions":4};var writer:=HeldWriter.new();var frames:=0
 check(writer.start(project,request).is_empty(),"real checkpoint worker starts from frozen project")
 while not writer.reached():frames+=1;await create_timer(.001).timeout
 check(writer.busy() and writer.thread.is_alive() and frames>0,"main-thread processing continues while worker owns the file boundary")
 check(not writer.start(project,request).is_empty(),"second checkpoint refuses instead of growing a snapshot queue")
 image.fill(Color.RED);project.video.duration_frames=96;project.editor.frame=8;request.revision=99
 check(writer.poll().is_empty() and cache.decodes==0,"polling a held writer does not join or mutate the live cache")
 writer.gate.post();var result: Dictionary={}
 while result.is_empty():await create_timer(.001).timeout;result=writer.poll()
 check(result.error.is_empty() and result.background_thread and result.request.revision==7 and not writer.busy(),"actual filesystem commit runs off the main thread with captured request metadata")
 var restored:=Storage.load_project(folder.path_join("one"))
 check(not restored.has("error") and restored.video.duration_frames==48 and restored.editor.frame==3 and Storage.image_hash(Drawing.image(restored.layers[0].cels[0]))==original,"committed checkpoint contains pre-edit timing and exact independent pixels")
 var before:=FileAccess.get_sha256(folder.path_join("one/project.json"));DirAccess.make_dir_absolute(folder.path_join("one/project.json.tmp"));var failed:=Writer.new();check(failed.start(project,{"root":folder,"session":"one","revision":8}).is_empty(),"blocked-save fixture starts independent worker")
 result={}
 while result.is_empty():await create_timer(.001).timeout;result=failed.poll()
 check(not result.error.is_empty() and FileAccess.get_sha256(folder.path_join("one/project.json"))==before,"real temporary-path refusal reports failure and preserves previous checkpoint")
 print("RECOVERY_WRITER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
