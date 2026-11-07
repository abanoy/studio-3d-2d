extends SceneTree
const Writer=preload("res://src/has_snapshot_writer.gd")
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
class HeldWriter extends Writer:
	var entered:=Semaphore.new()
	var release:=Semaphore.new()
	func persist(project: Dictionary,request: Dictionary) -> String:
		entered.post();release.wait();return super.persist(project,request)
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	var image:=Drawing.blank(960,540);image.fill(Color.RED);var layers: Array=[{"id":"layer","name":"Ink","visible":true,"cels":[]}];Drawing.insert(layers[0],0,48,image)
	var project: Dictionary={"video":{"width":960,"height":540,"fps_num":24,"fps_den":1,"duration_frames":48},"camera_keys":[preload("res://src/timeline.gd").key(0,Vector3(0,1,3),Quaternion.IDENTITY,60)],"layers":layers,"world":preload("res://src/world_document.gd").empty(),"audio":{},"editor":{"frame":0}}
	var request: Dictionary={"folder":folder.path_join("snapshot"),"ready":folder.path_join("job-snapshot.json"),"cancel":folder.path_join("cancel"),"origins":{}}
	var worker:=HeldWriter.new();check(worker.start(project,request).is_empty(),"manual snapshot starts without blocking main thread")
	while not worker.entered.try_wait():await process_frame
	check(worker.busy() and worker.poll().is_empty(),"running worker only polls; no premature snapshot result")
	image.fill(Color.BLUE);project.video.fps_num=30;project.layers[0].name="Changed";worker.release.post();var result: Dictionary={}
	while result.is_empty():result=worker.poll();await process_frame
	var loaded:=Storage.load_project(request.folder);check(result.error.is_empty() and result.background_thread and not worker.busy(),"PNG/reference persistence completes on isolated worker")
	check(not loaded.has("error") and loaded.video.fps_num==24 and loaded.layers[0].name=="Ink" and Drawing.image(loaded.layers[0].cels[0]).get_pixel(0,0)==Color.RED,"captured pixels and metadata remain independent of later live mutations")
	var packet=JSON.parse_string(FileAccess.get_file_as_string(request.ready));check(packet.format==Writer.FORMAT and packet.ok and packet.references.is_empty(),"only a fully prepared snapshot publishes versioned readiness")
	request=request.duplicate(true);request.folder=folder.path_join("cancelled");request.ready=folder.path_join("cancelled-snapshot.json");worker=HeldWriter.new();check(worker.start(project,request).is_empty(),"second isolated snapshot starts")
	while not worker.entered.try_wait():await process_frame
	FileAccess.open(request.cancel,FileAccess.WRITE).store_string("cancel");worker.release.post();result={}
	while result.is_empty():result=worker.poll();await process_frame
	packet=JSON.parse_string(FileAccess.get_file_as_string(request.ready));check(not result.error.is_empty() and not packet.ok and not FileAccess.file_exists(request.folder.path_join("project.json")),"cancelled snapshot publishes failure and never commits its manifest")
	var wav:=AudioStreamWAV.new();wav.format=AudioStreamWAV.FORMAT_16_BITS;wav.mix_rate=48000;wav.data=PackedByteArray();var silence:=PackedByteArray();silence.resize(960);wav.data=silence;var sound:=folder.path_join("tone.wav");check(wav.save_to_wav(sound)==OK,"reference fixture writes a real local WAV")
	var map:=ProjectSettings.globalize_path("res://examples/tutorials/Practice room.glb");var reference:=folder.path_join("reference.png");image.save_png(reference)
	var linked_project: Dictionary={"world":{},"source":map,"model":{"source":map},"audio":{"source":{"path":sound}},"reference_sheet":{"source":reference,"sha256":FileAccess.get_sha256(reference)},"sequence_graph":{"assets":[{"scene":{"world":{},"source":map,"audio":{"source":{"path":sound}}}}]}}
	var links:=worker.references(linked_project,{})
	check(links.get("assets/"+FileAccess.get_sha256(sound)+".wav")==sound and links.get("assets/"+FileAccess.get_sha256(map)+".glb")==map and links.get("references/"+FileAccess.get_sha256(reference)+".png")==reference and links.size()==3,"legacy/nested audio/model/reference dependencies retain exact linked addresses")
	check(not worker.start(project,{}).is_empty() and not worker.busy(),"missing snapshot addresses refuse before starting a thread")
	print("HAS_SNAPSHOT_WRITER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
