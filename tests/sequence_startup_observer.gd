extends Node
const Graph=preload("res://src/sequence_graph.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(60).timeout.connect(func():push_error("Nested startup watchdog");get_tree().quit(2))
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for i in range(3):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0]
	var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	var editor=app.sequence_editor
	check(result.restored and app.dirty and app.has_project.path.is_empty(),"normal startup automatically restores a dirty unsaved enclosing project after abrupt writer exit")
	check(editor.active_owner==expected.asset and app.frame==6 and not app.home.visible,"automatic recovery restores child editor/frame with priority over Home")
	check(editor.root_document.world.objects.size()==2 and editor.graph.assets.size()==1 and editor.graph.clips.size()==2,"crash recovery retains both parent backgrounds and shared child instances")
	check(Storage.image_hash(app.layers[1].cels[0].image)==expected.paint and app.renderer.world_runtime.instances.size()==1,"recovered child keeps exact independent pixels and the native editable rig")
	if expected.get("full_masks",false):
		var masks: bool=editor.graph.format==Graph.MASK_FORMAT
		for clip in editor.graph.clips:
			var mask: Dictionary=clip.get("mask",{});var r: Array=mask.get("rect",[])
			masks=masks and r.size()==4 and not mask.get("invert",true) and Rect2i(int(r[0]),int(r[1]),int(r[2]),int(r[3]))==Rect2i(0,0,1920,1080)
		check(masks,"automatic startup retains mask graph alongside restored editable child context")
	print("SEQUENCE_EDITOR_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));get_tree().quit(0 if failures==0 else 1)
