extends Node
const Storage=preload("res://src/storage.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _ready() -> void:
	get_parent().startup_recovery_finished.connect(recovered)
	get_tree().create_timer(120).timeout.connect(func():push_error("Raster reader startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func recovered(result: Dictionary) -> void:
	var app=get_parent();app.autosave_enabled.button_pressed=false
	for i in range(5):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
	check(result.restored and app.dirty and app.has_project.path.is_empty() and not app.home.visible,"normal startup restores ordinary checkpoint after actual SIGKILL before Home")
	var exact: bool=app.layers.size()==1 and app.layers[0].cels.size()==32;var ids:={}
	if exact:
		for i in range(32):
			var cel: Dictionary=app.layers[0].cels[i];ids[cel.image.get_instance_id()]=true;exact=exact and cel.id==expected.ids[i] and Storage.image_hash(cel.image)==(expected.edited if i==7 else expected.base)
	check(exact and ids.size()==32,"startup retains32distinct Images, edited cel7 and31exact original peers")
	check(app.frame==7 and app.frame_box.value==7 and app.video.duration_frames==48,"startup restores exact saved playhead and scene bounds")
	check(app.canvas.overlay.get_image().get_data()==Drawing.composite(app.layers,7,1920,1080).get_data(),"startup actual GPU preview uses edited cel pixels")
	check(Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"startup restores exact independent PCM")
	var picture: Image=await app.renderer.capture(app.keys,app.layers,7,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-7.png")).get_data(),"startup final picture matches original movie input")
	print("CEL_RASTER_READER_STARTUP ",JSON.stringify({"checks":checks,"failures":failures}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
