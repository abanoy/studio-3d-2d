extends Node
const World=preload("res://src/world_document.gd")
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(120).timeout.connect(func():push_error("Late clip startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func digest(value: PackedByteArray) -> String:
	var hash_context:=HashingContext.new();hash_context.start(HashingContext.HASH_SHA256);hash_context.update(value);return hash_context.finish().hex_encode()
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	check(result.restored and app.dirty and app.has_project.path.is_empty(),"actual SIGKILL recovery opens moved project as dirty unsaved copy")
	check(app.video.duration_frames==3600 and app.video.fps_num==60 and app.frame==12 and not app.home.visible,"normal startup retains60second timing and moved-take playhead before Home")
	check(JSON.parse_string(JSON.stringify(World.portable(app.current_world()),"",true,true))==expected.world,"recovery retains complete relative source/world data")
	check(digest(app.audio_mix.pcm)==expected.pcm and Storage.image_hash(Drawing.cel_at(app.layers[1],0).image)==expected.paint,"recovery retains exact independent sound and ink")
	var picture: Image=await app.renderer.capture(app.keys,[],12,true)
	check(picture.get_data()==Image.load_from_file(folder.path_join("moved.png")).get_data(),"recovered frame12 repeats exact moved world pixels")
	check(app.timeline_navigation.span==0 and app.timeline.duration==3600 and app.frame_box.max_value==3600,"recovery resets synchronized view to full late-frame domain")
	print("LATE_CLIP_MOVE_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
