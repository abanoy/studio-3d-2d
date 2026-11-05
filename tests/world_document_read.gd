extends SceneTree
const Storage = preload("res://src/storage.gd")
const World = preload("res://src/world_document.gd")
const SceneIO = preload("res://src/scene3d.gd")
const Model = preload("res://src/model.gd")

func _initialize() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2:quit(2);return
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(args[0]).path_join("project.json")))
	var loaded:=Storage.load_project(str(args[1]))
	if loaded.has("error"):push_error(loaded.error);quit(1);return
	if loaded.schema_version!=4 or World.portable(loaded.world)!=expected.world or loaded.video!=expected.video or loaded.editor!=expected.editor:
		push_error("World record changed through container round-trip");quit(1);return
	if loaded.layers.size()!=expected.layers.size():quit(1);return
	for i in range(loaded.layers.size()):
		for j in range(loaded.layers[i].cels.size()):
			var original:=Image.load_from_file(str(args[0]).path_join(expected.layers[i].cels[j].path))
			original.convert(Image.FORMAT_RGBA8)
			if original.get_data()!=loaded.layers[i].cels[j].image.get_data():push_error("Cel pixels changed");quit(1);return
	if not expected.audio.is_empty() and (loaded.audio.start_frame!=expected.audio.start_frame or loaded.audio.source.sha256!=expected.audio.sha256):quit(1);return
	var bound:=0
	for row in loaded.world.objects:
		var result:=SceneIO.load_glb(row.source)
		if result.has("error"):push_error(result.error);quit(1);return
		var candidate:=Model.new();candidate.root=result.scene;candidate.data=row;candidate.inventory(candidate.root)
		var error:=candidate.check_bindings()
		candidate.root.free()
		if not error.is_empty():push_error(error);quit(1);return
		bound+=1
	print("WORLD_PACKAGE_READ "+JSON.stringify({"objects":bound,"layers":loaded.layers.size(),"audio":not loaded.audio.is_empty()}))
	quit(0)
