extends SceneTree
const Runtime=preload("res://src/sequence_runtime.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Drawing=preload("res://src/drawing.gd")
const World=preload("res://src/world_document.gd")
const Timeline=preload("res://src/timeline.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _initialize() -> void:
	create_timer(280).timeout.connect(func():push_error("Sequence cache watchdog");quit(2));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];DirAccess.make_dir_recursive_absolute(folder)
	var baseline: bool="--baseline" in args
	var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":240}
	var keys: Array=[Timeline.key(0,Vector3(0,0,2),Quaternion.IDENTITY,55)]
	var red:=Drawing.blank(1920,1080);red.fill_rect(Rect2i(800,400,100,100),Color(1,0,0,.5))
	var blue:=Drawing.blank(1920,1080);blue.fill_rect(Rect2i(800,400,100,100),Color(0,0,1,.5))
	var red_hash:=Storage.image_hash(red);var blue_hash:=Storage.image_hash(blue)
	var scene:={"schema_version":4,"video":video,"camera_keys":keys,"world":World.empty(),"audio":{},"layers":[{"id":"ink","name":"Ink","visible":true,"cels":[{"id":"red","start":0,"duration":120,"image":red},{"id":"blue","start":120,"duration":120,"image":blue}]}]}
	var end:=Graph.key(240);end.offset=[400,0]
	var clip:={"id":"clip","asset_id":"paint","start":0,"duration":240,"source_in":0,"time_in":0,"key_in":0,"loop":false,"visible":true,"muted":false,"gain_db":0,"keys":[Graph.key(),end],"shadow":{"offset":[120,0],"color":[0,0,0,.5],"softness":8}}
	var graph:={"format":Graph.SHADOW_FORMAT,"assets":[{"id":"paint","name":"Held artwork","scene":scene,"clips":[]}],"clips":[clip]}
	var parent: Dictionary=scene.duplicate();parent.layers=[]
	var runtime:=Runtime.new();root.add_child(runtime);check(runtime.prepare(graph,parent).is_empty(),"240-frame two-hold sequence prepares with editable placement and shadow")
	var elapsed: Array=[];var correct:=true;var peak:=0;var first:="";var last:=""
	for frame in range(240):
		var began:=Time.get_ticks_usec();var image: Image=await runtime.render("",frame,true);elapsed.append((Time.get_ticks_usec()-began)/1000.0)
		if not image:correct=false;break
		var x:=int(850+400.0*frame/240);var color:=image.get_pixel(x,450);var shadow:=image.get_pixel(x+120,450)
		correct=correct and absf(color.a-.5)<.015 and absf(shadow.a-.25)<.02 and color.r>(.99 if frame<120 else -.01) and color.b>(.99 if frame>=120 else -.01)
		if frame==0:first=Storage.image_hash(image)
		if frame==239:last=Storage.image_hash(image)
		peak=maxi(peak,runtime.frames.size())
	check(correct,"all240 moving parent samples retain correct held artwork and independent shadow alpha")
	check(peak==1,"per-asset frame cache stays bounded throughout sequential playback")
	check(Storage.image_hash(red)==red_hash and Storage.image_hash(blue)==blue_hash,"full-span playback preserves editable source pixels")
	if not baseline:check(runtime.builds==2,"two held cels build exactly two source pictures across240 distinct parent frames")
	elapsed.sort();var total:=0.0
	for value in elapsed:total+=value
	var report:={"checks":checks,"failures":failures,"baseline":baseline,"frames":elapsed.size(),"source_builds":runtime.builds,"peak_cached_assets":peak,"total_ms":total,"mean_ms":total/elapsed.size(),"p95_ms":elapsed[int(elapsed.size()*.95)],"max_ms":elapsed[-1],"adapter":RenderingServer.get_video_adapter_name(),"first_sha256":first,"last_sha256":last,"native_fixtures":0}
	FileAccess.open(folder.path_join("baseline.json" if baseline else "verification.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	runtime.shutdown()
	while is_instance_valid(runtime):await process_frame
	print("SEQUENCE_CACHE_SMOKE ",JSON.stringify(report));quit(0 if failures==0 else 1)
