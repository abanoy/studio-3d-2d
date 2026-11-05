extends SceneTree
const Runtime=preload("res://src/sequence_runtime.gd")
const Graph=preload("res://src/sequence_graph.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func collect(runtime: Node,completed: Dictionary,id: String) -> void:
	var image: Image=await runtime.render("",0,true)
	completed[id]=image
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var document:=Storage.load_project(folder)
	if document.has("error"):print(document.error);quit(1);return
	var runtime:=Runtime.new();root.add_child(runtime)
	check(runtime.prepare(document.sequence_graph,document).is_empty(),"editable child runtime prepares")
	var source: Image=document.sequence_graph.assets[0].scene.layers[0].cels[0].image
	var before:=source.get_data()
	var image: Image=await runtime.render("",0,true)
	check(image!=null and image.get_pixel(0,0).a==0,"empty child background remains transparent")
	var pixel:=image.get_pixel(850,450)
	check(pixel.r>.99 and pixel.g<.01 and absf(pixel.a-.5)<.01,"transparent viewport readback preserves straight half-alpha red")
	var builds:=runtime.builds
	var again: Image=await runtime.render("",0,true)
	check(runtime.builds==builds and again.get_data()==image.get_data(),"same local frame reuses bounded cached scene picture")
	check(source.get_data()==before,"nested compositing never alters editable source pixels")
	image.save_png(folder.path_join("sequence-half-alpha.png"))
	var held: Image=await runtime.render("",12,true)
	check(runtime.builds==builds and held.get_data()==image.get_data(),"different parent frames reuse the same held artwork picture exactly")
	var original:=source.get_pixel(850,450);source.set_pixel(850,450,Color.BLUE);preload("res://src/drawing.gd").touch(source,Rect2i(850,450,1,1))
	var edited: Image=await runtime.render("",12,true)
	check(runtime.builds==builds+1 and edited.get_pixel(850,450).b>.99,"a marked pixel revision invalidates held artwork even at the same frame")
	source.set_pixel(850,450,original);preload("res://src/drawing.gd").touch(source,Rect2i(850,450,1,1))
	var restored: Image=await runtime.render("",13,true)
	check(runtime.builds==builds+2 and restored.get_data()==image.get_data() and source.get_data()==before,"restoring source pixels builds once and restores the exact cached appearance")
	runtime.free()
	# Two actual compositing levels, each with its own local range and loops.
	var child: Dictionary=document.sequence_graph.assets[0].scene
	child.video=child.video.duplicate(true);child.video.duration_frames=2
	child.layers[0].cels[0].duration=1
	var blue: Image=source.duplicate();blue.fill_rect(Rect2i(800,400,100,100),Color.BLUE)
	child.layers[0].cels.append({"id":"blue","start":1,"duration":1,"image":blue})
	var wrapper: Dictionary=child.duplicate(true);wrapper.layers=[];wrapper.video=child.video.duplicate(true);wrapper.video.duration_frames=4
	var inner: Dictionary=document.sequence_graph.clips[0].duplicate(true);inner.id="inner";inner.duration=4;inner.loop=true
	var outer: Dictionary=inner.duplicate(true);outer.id="outer";outer.asset_id="wrapper";outer.duration=8;outer.source_in=1;outer.keys[0].offset=[100,0];outer.keys[0].opacity=.5
	var root_doc: Dictionary=wrapper.duplicate(true);root_doc.video=wrapper.video.duplicate(true);root_doc.video.duration_frames=8
	var graph:={"format":Graph.FORMAT,"assets":[{"id":"child","name":"Paint","scene":child,"clips":[]},{"id":"wrapper","name":"Wrapper","scene":wrapper,"clips":[inner]}],"clips":[outer]}
	runtime=Runtime.new();root.add_child(runtime)
	check(runtime.prepare(graph,root_doc).is_empty(),"two editable sequence levels prepare")
	var first: Image=await runtime.render("",0,true);var second: Image=await runtime.render("",1,true)
	var first_pixel:=first.get_pixel(950,450);var second_pixel:=second.get_pixel(950,450)
	check(first_pixel.b>.99 and absf(first_pixel.a-.5)<.01,"nested source-in and loop select the opaque blue hold under instance opacity")
	check(second_pixel.r>.99 and absf(second_pixel.a-.25)<.01,"nested half-alpha red and parent opacity multiply without double-darkening")
	check(first.get_pixel(0,0).a==0 and first.get_pixel(850,450).a==0,"instance translation preserves a transparent surround")
	var looped: Image=await runtime.render("",4,true)
	check(looped.get_data()==first.get_data(),"parent repeat maps through both independent local timelines")
	var completed:={};collect(runtime,completed,"active");collect(runtime,completed,"queued")
	check(runtime.busy and runtime.requests==2,"render lock counts both active and queued callers before retirement")
	runtime.shutdown()
	while is_instance_valid(runtime):await process_frame
	check(completed.has("active") and completed.has("queued") and completed.active==null and completed.queued==null,"retiring runtime completes every cancelled caller before freeing its node")
	print("SEQUENCE_RUNTIME_SMOKE ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
