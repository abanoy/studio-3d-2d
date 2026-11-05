extends Node
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(120).timeout.connect(func():push_error("Long project startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for n in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	check(result.restored and app.dirty and app.has_project.path.is_empty(),"normal startup restores dirty long project after SIGKILL")
	check(app.video.duration_frames==1440 and app.frame==1300 and not app.home.visible,"recovery retains late playhead and precedes Home")
	check(app.frame_box.max_value==1440 and app.renderer.world_runtime.duration==1440,"recovery installs longer posing and transport bounds")
	check(app.audio_mix.pcm.hex_encode().sha256_text()==expected.pcm,"recovery restores exact60second sparse PCM")
	check(not app.reference_sheet.document().is_empty() and app.reference_sheet.image!=null,"recovery retains kept reference without original source")
	var child: Dictionary=app.sequence_editor.asset(expected.child)
	check(not child.is_empty() and child.scene.video.duration_frames==240,"recovery retains editable bounded child")
	var image: Image=await app.renderer.capture(app.keys,app.layers,1300,true)
	check(image.get_data()==Image.load_from_file(folder.path_join("late.png")).get_data(),"recovery reproduces exact late world ink and child pixels")
	print("EXTENDED_TIMING_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
