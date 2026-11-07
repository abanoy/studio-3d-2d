extends Node
const Drawing=preload("res://src/drawing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func _ready() -> void:
 get_parent().startup_recovery_finished.connect(recovered);get_tree().create_timer(400).timeout.connect(func():push_error("Large startup watchdog");get_tree().quit(2))
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func recovered(result: Dictionary) -> void:
 var app=get_parent();app.autosave_enabled.button_pressed=false;var folder: String=OS.get_cmdline_user_args()[0];var expected: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("expected.json")))
 for i in range(5):await get_tree().process_frame
 await RenderingServer.frame_post_draw
 check(result.get("restored",false) and app.dirty and app.has_project.path.is_empty() and not app.home.visible,"ordinary startup restores dense checkpoint as an unsaved copy after real kill")
 var pixels: Array=[];var ids:={}
 for layer in app.layers:
  for cel in layer.cels:
   var captured: Dictionary=cel.raster_owner.snapshot()
   if not captured.has("error"):pixels.append(captured.raster.pixel_sha256());ids[Drawing.raster_token(cel)[0]]=true
 check(pixels==expected.pixels and ids.size()==400,"abrupt recovery retains all400exact independent editable drawings")
 check(app.frame==37 and app.video.duration_frames==101 and app.frame_box.value==37,"dense startup restores exact playhead and scene length")
 check(Storage.RasterReader.digest_bytes(app.audio_mix.pcm)==expected.pcm,"dense startup restores exact independently timed audio")
 check(app.canvas.overlay.get_image().get_data()==Image.load_from_file(folder.path_join("expected-overlay.png")).get_data(),"dense recovered GPU overlay equals original preview")
 var picture: Image=await app.renderer.capture(app.keys,app.layers,37,true);check(picture.get_data()==Image.load_from_file(folder.path_join("expected-final.png")).get_data(),"dense recovered final evaluator equals original movie input")
 check(FileAccess.get_sha256(folder.path_join("large.has"))==expected.manual_sha,"automatic dense recovery never rewrites explicit HAS")
 check(app.raster_budget.sample().accounted_bytes<=app.raster_budget.sample().owner_limit_bytes,"dense recovered document remains inside admitted ownership")
 print("LARGE_PROJECT_STARTUP "+JSON.stringify({"checks":checks,"failures":failures,"memory":app.raster_budget.sample()}));await app.quit_studio();get_tree().quit(0 if failures==0 else 1)
