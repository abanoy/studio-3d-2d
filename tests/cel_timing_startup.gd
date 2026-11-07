extends Node
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(120).timeout.connect(func():push_error("Cel timing startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func signature(bytes: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(bytes);return context.finish().hex_encode()
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	check(result.restored and app.dirty and app.has_project.path.is_empty() and not app.home.visible,"normal startup restores moved exposures after actual SIGKILL before Home")
	var layer: Dictionary=app.cel_timing.layer_by_id(expected.layer)
	check(layer.cels[0].id==expected.a and layer.cels[0].start==1300 and layer.cels[0].duration==24 and layer.cels[1].start==1376,"recovery retains full parent exposure identity/ranges")
	check(Storage.image_hash(Drawing.image(layer.cels[0]))==expected.pixels and signature(app.audio_mix.pcm)==expected.pcm,"recovery restores exact original RGBA and independent sound")
	var child: Dictionary=app.sequence_editor.asset(expected.child).scene
	check(child.layers[1].cels[0].start==80 and child.layers[1].cels[0].duration==48 and child.layers[1].opacity==.35,"recovery retains independently moved child exposure and layer opacity")
	check(app.frame==1304 and app.frame_box.value==1304 and app.video.duration_frames==1440 and app.timeline_navigation.span==0,"recovery restores requested late playhead with correctly bounded frame control")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,1430,true)
	check(picture.get_data()==Image.load_from_file(folder.path_join("expected-1430.png")).get_data(),"recovery repeats exact edited child/parent composition")
	print("CEL_TIMING_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
