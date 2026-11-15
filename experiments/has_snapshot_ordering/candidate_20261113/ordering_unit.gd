extends SceneTree
const Writer=preload("res://src/has_snapshot_writer.gd")
const Drawing=preload("res://src/drawing.gd")
const ProjectOperation=preload("res://src/has_project.gd")
class ObservedWriter extends Writer:
	var entered:=Semaphore.new()
	var release:=Semaphore.new()
	var observed: Dictionary={}
	func persist(project: Dictionary,request: Dictionary) -> String:
		observed={"fps":project.video.fps_num,"name":project.layers[0].name,"pixel":Drawing.image(project.layers[0].cels[0]).get_pixel(0,0).to_html(),"ready":request.ready,"worker_thread":not Thread.is_main_thread()}
		entered.post();release.wait();return ""
	func references(_project: Dictionary,_origins: Dictionary) -> Dictionary:return {}
class FailedWriter extends Writer:
	func _start_thread(_work: Callable) -> Error:return ERR_CANT_CREATE
var checks:=0
var failures:=0
var folder:=""
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func fixture() -> Dictionary:
	var image:=Drawing.blank(960,540);image.fill(Color.RED)
	var layers: Array=[{"id":"layer","name":"Ink","visible":true,"cels":[]}];Drawing.insert(layers[0],0,48,image)
	return {"video":{"width":960,"height":540,"fps_num":24,"fps_den":1,"duration_frames":48},"layers":layers,"world":{},"audio":{},"editor":{"frame":0}}
func request(label: String) -> Dictionary:
	return {"folder":folder.path_join(label),"ready":folder.path_join(label+"-snapshot.json"),"cancel":folder.path_join(label+"-cancel"),"origins":{"nested":{"value":"captured"}}}
func wait_entered(worker) -> void:
	while not worker.entered.try_wait():await process_frame
func complete(worker) -> Dictionary:
	worker.release.post();var result: Dictionary={}
	while result.is_empty():result=worker.poll();await process_frame
	return result
func run() -> void:
	folder=OS.get_cmdline_user_args()[0].replace("\\","/");DirAccess.make_dir_recursive_absolute(folder)
	var operation=ProjectOperation.new()
	check(operation is Node,"project-operation ordering source compiles without starting the app")
	operation.free()
	var project:=fixture();var req:=request("split");var original_ready: String=req.ready;var worker:=ObservedWriter.new()
	check(worker.prepare(project,req).is_empty(),"prepare captures a valid authored project")
	check(worker.has_prepared() and not worker.busy() and worker.thread==null,"prepare creates no thread before child launch")
	check(not FileAccess.file_exists(req.ready) and not DirAccess.dir_exists_absolute(req.folder),"prepare performs no snapshot directory or readiness writes")
	project.video.fps_num=30;project.layers[0].name="Changed";Drawing.image(project.layers[0].cels[0]).fill(Color.BLUE)
	req.ready=folder.path_join("must-not-publish.json");req.origins.nested.value="Changed"
	check(worker._prepared.request.origins.nested.value=="captured","prepare detaches nested request metadata")
	check(not worker.prepare(project,request("overwrite")).is_empty() and worker.has_prepared(),"a second prepare cannot overwrite an unlaunched capture")
	check(worker.launch().is_empty(),"launch starts the already captured snapshot")
	await wait_entered(worker)
	check(not worker.has_prepared() and worker.busy() and worker.poll().is_empty(),"launch consumes capture and ordinary polling remains nonblocking")
	check(worker.observed.fps==24 and worker.observed.name=="Ink" and worker.observed.pixel==Color.RED.to_html(),"prepared pixels and metadata retain the earlier state after live edits")
	check(worker.observed.ready==original_ready and worker.observed.worker_thread,"launch uses frozen request on its background thread")
	check(not worker.prepare(project,request("busy")).is_empty(),"prepare refuses while the snapshot thread is active")
	var result: Dictionary=await complete(worker)
	var status=JSON.parse_string(FileAccess.get_file_as_string(original_ready))
	check(result.error.is_empty() and result.background_thread and not worker.busy(),"split capture completes through the unchanged worker result contract")
	check(status.ok and not FileAccess.file_exists(req.ready),"readiness uses the captured owned address")
	check(not worker.launch().is_empty(),"a capture cannot be launched twice")
	worker=ObservedWriter.new();req=request("legacy")
	check(worker.start(project,req).is_empty(),"public start retains prepare-and-launch compatibility")
	await wait_entered(worker);result=await complete(worker)
	check(result.error.is_empty() and FileAccess.file_exists(req.ready),"legacy start retains completion and readiness behavior")
	worker=ObservedWriter.new();req=request("discard")
	check(worker.prepare(project,req).is_empty(),"discard fixture prepares")
	worker.discard_prepared()
	check(not worker.has_prepared() and not worker.busy() and not worker.launch().is_empty(),"explicit discard releases an unlaunched capture without starting work")
	check(not FileAccess.file_exists(req.ready) and not DirAccess.dir_exists_absolute(req.folder),"discard leaves no snapshot output")
	check(worker.prepare(project,req).is_empty(),"discarded writer can capture a later operation")
	check(worker.finish().is_empty() and not worker.has_prepared() and not worker.busy(),"finish drains prepared-only state without launching a thread")
	check(worker.finish().is_empty(),"finish remains idempotent after prepared discard")
	var failed:=FailedWriter.new();req=request("thread-failure")
	check(failed.prepare(project,req).is_empty() and not failed.launch().is_empty(),"explicit Thread-start failure is returned")
	check(not failed.has_prepared() and not failed.busy() and failed.thread==null,"Thread-start failure consumes and releases prepared state")
	check(not FileAccess.file_exists(req.ready) and not DirAccess.dir_exists_absolute(req.folder),"Thread-start failure publishes no successful snapshot")
	check(failed.finish().is_empty(),"Thread-start failure cleanup is safe")
	worker=ObservedWriter.new();req=request("cancel")
	check(worker.prepare(project,req).is_empty(),"cancel fixture prepares")
	var cancel_file:=FileAccess.open(req.cancel,FileAccess.WRITE);cancel_file.store_string("cancel");cancel_file.close()
	check(worker.launch().is_empty(),"prepared cancellation enters the existing worker cancellation contract")
	await wait_entered(worker);result=await complete(worker);status=JSON.parse_string(FileAccess.get_file_as_string(req.ready))
	check(not result.error.is_empty() and not status.ok and status.error.contains("cancel"),"cancelled prepared snapshot publishes failed readiness")
	check(not worker.busy() and not worker.has_prepared(),"cancelled split snapshot drains thread and capture ownership")
	worker=ObservedWriter.new()
	check(not worker.prepare(project,{}).is_empty() and not worker.has_prepared() and not worker.busy(),"missing addresses refuse before capture/thread ownership")
	project.layers[0].cels[0].erase("image");project.layers[0].cels[0].erase("raster_owner")
	check(not worker.prepare(project,request("invalid")).is_empty() and not worker.has_prepared(),"invalid drawing capture refuses without retaining pending state")
	var report:={"checks":checks,"failures":failures,"actual_thread_and_capture":true,"persistence":"observed inert persist override; existing Storage/app acceptance separate","gpu":false}
	var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report));file.close()
	print("HAS_SNAPSHOT_ORDERING_UNIT "+JSON.stringify(report));quit(0 if failures==0 else 1)
