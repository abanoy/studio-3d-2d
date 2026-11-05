extends Node
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(60).timeout.connect(func():push_error("Reference startup watchdog");get_tree().quit(2))
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for i in range(4):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	var sheet=app.reference_sheet
	check(result.restored and app.dirty and app.has_project.path.is_empty(),"normal startup restores dirty unsaved project after actual abrupt exit")
	check(not sheet.document().is_empty() and sheet.source_hash==expected.reference and Storage.image_hash(sheet.image)==expected.pixels,"normal startup restores kept reference exactly without original or writer cache")
	check(not sheet.guide.visible,"recovered reference guide remains an optional editing view")
	check(app.sequence_editor.active_owner==expected.child and app.frame==6 and not app.home.visible,"reference recovery retains active child/frame and startup priority over Home")
	app.sequence_editor.return_to_parent()
	var image: Image=await app.renderer.capture(app.keys,app.layers,0,true)
	check(image.get_data()==Image.load_from_file(folder.path_join("nested.png")).get_data() and app.audio_mix.pcm==Marshalls.base64_to_raw(expected.audio),"recovered enclosing scene retains exact picture and PCM with reference excluded")
	print("REFERENCE_PROJECT_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
