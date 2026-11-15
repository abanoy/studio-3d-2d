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
 if not result.error.is_empty():print("WRITER_ERROR "+result.error)
 check(result.error.is_empty() and result.background_thread and result.request.revision==7 and not writer.busy(),"actual filesystem commit runs off the main thread with captured request metadata")
 var restored:=Storage.load_project(folder.path_join("one"))
 check(not restored.has("error") and restored.video.duration_frames==48 and restored.editor.frame==3 and Storage.image_hash(Drawing.image(restored.layers[0].cels[0]))==original,"committed checkpoint contains pre-edit timing and exact independent pixels")
 var before:=FileAccess.get_sha256(folder.path_join("one/project.json"));DirAccess.make_dir_absolute(folder.path_join("one/project.json.tmp"));var failed:=Writer.new();check(failed.start(project,{"root":folder,"session":"one","revision":8}).is_empty(),"blocked-save fixture starts independent worker")
 result={}
 while result.is_empty():await create_timer(.001).timeout;result=failed.poll()
 check(not result.error.is_empty() and FileAccess.get_sha256(folder.path_join("one/project.json"))==before,"real temporary-path refusal reports failure and preserves previous checkpoint")
 var Recovery=preload("res://src/recovery.gd");var reserved:=Recovery.quota(folder,"reserve","held_for_concurrency",503*1024*1024)
 check(reserved.ok,"shared near-capacity reservation is admitted without creating payload files")
 var protected:=FileAccess.get_sha256(folder.path_join("one/project.json"));var admitted:=Writer.new();check(admitted.start(project,{"root":folder,"session":"one","revision":9}).is_empty(),"competing checkpoint starts normal detached worker")
 result={}
 while result.is_empty():await create_timer(.001).timeout;result=admitted.poll()
 check("budget" in result.error and FileAccess.get_sha256(folder.path_join("one/project.json"))==protected,"concurrent reserved budget refuses actual checkpoint before replacing previous metadata")
 check(Recovery.quota(folder,"release","held_for_concurrency").ok,"only the owned reservation is released")
 var registry: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join(".quota.json")))
 check(registry.reservations.is_empty(),"successful and failed checkpoint paths leave no live reservations")
 var noise:=Drawing.blank(64,64);var rng:=RandomNumberGenerator.new();rng.seed=714
 for y in 64:
  for x in 64:noise.set_pixel(x,y,Color8(rng.randi_range(0,255),rng.randi_range(0,255),rng.randi_range(0,255),rng.randi_range(0,255)))
 var noise_layers: Array=[{"cels":[{"image":noise}]}]
 check(Recovery.drawing_reserve(noise_layers)>=noise.save_png_to_buffer().size(),"conservative reservation includes PNG overhead for incompressible art")
 print("RECOVERY_WRITER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
