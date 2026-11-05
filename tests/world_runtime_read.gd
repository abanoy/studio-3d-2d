extends SceneTree
const Renderer = preload("res://src/renderer.gd")
const Storage = preload("res://src/storage.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2:quit(2);return
	var data:=Storage.load_project(args[0])
	if data.has("error"):push_error(data.error);quit(1);return
	var renderer:=Renderer.new();root.add_child(renderer);renderer.setup();renderer.set_background(data.video.world_background)
	var prepared:=renderer.prepare_world(data.world,int(data.video.duration_frames))
	if prepared.has("error") or not renderer.install_world(prepared,int(data.editor.frame)):
		push_error("Could not install the complete unpacked world");quit(1);return
	var actual:=await renderer.capture(data.camera_keys,data.layers,int(data.editor.frame),true)
	var expected:=Image.load_from_file(args[1]);expected.convert(Image.FORMAT_RGBA8)
	var aa:=actual.get_data();var bb:=expected.get_data();var changes:=0;var total:=0.0
	if aa.size()!=bb.size():quit(1);return
	for i in range(aa.size()):
		if aa[i]!=bb[i]:changes+=1;total+=absf(float(aa[i])-float(bb[i]))
	var mean:=total/aa.size()
	print("WORLD_RUNTIME_READ "+JSON.stringify({"objects":renderer.world_runtime.instances.size(),"changed_channels":changes,"mean_error":mean,"frame":data.editor.frame}))
	quit(0 if changes<=384 and mean<0.002 else 1)
