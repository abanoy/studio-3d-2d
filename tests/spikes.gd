extends SceneTree
const SceneIO = preload("res://src/scene3d.gd")
const Renderer = preload("res://src/renderer.gd")
const Drawing = preload("res://src/drawing.gd")
const Timeline = preload("res://src/timeline.gd")
const Encoder = preload("res://src/encoder.gd")
var failures := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, text: String) -> void:
	print(("PASS " if ok else "FAIL ") + text)
	if not ok:
		failures += 1

func run() -> void:
	var output := ProjectSettings.globalize_path("res://output/spikes")
	DirAccess.make_dir_recursive_absolute(output)
	var fixture := output.path_join("room.glb")
	check(SceneIO.make_fixture(fixture) == OK, "create original GLB fixture")
	var original_hash := FileAccess.get_sha256(fixture)
	var renderer := Renderer.new()
	root.add_child(renderer)
	renderer.setup()
	check(renderer.import_scene(fixture).is_empty(), "runtime GLB import")
	var keys := [Timeline.key(0, Vector3(-1.5, 2, 5), Quaternion.IDENTITY, 60), Timeline.key(48, Vector3(1.5, 1.6, 3), Quaternion(Vector3.UP, -0.15), 52)]
	var image := Drawing.blank(1920, 1080)
	var start := Time.get_ticks_usec()
	for i in range(100):
		Drawing.stroke(image, Vector2(800 + i * 3, 540), Vector2(803 + i * 3, 540), 9, Color.RED, false)
	print("BENCH 100 full-HD mouse segments: %.3f ms" % ((Time.get_ticks_usec() - start) / 1000.0))
	var layers := [{"visible": true, "cels": [{"start": 0, "duration": 48, "image": image}]}]
	await process_frame
	var first := await renderer.capture(keys, layers, 0)
	check(first.get_width() == 1920 and first.get_height() == 1080, "full-HD GPU readback")
	check(first.get_pixel(900, 540).r > 0.95, "RGBA cel composites over 3D")
	layers[0].visible = false
	var hidden := await renderer.capture(keys, layers, 0)
	check(hidden.get_pixel(900, 540) != first.get_pixel(900, 540), "layer visibility isolation")
	layers[0].visible = true
	var repeat := await renderer.capture(keys, layers, 0)
	check(repeat.get_data() == first.get_data(), "same frame repeats exactly on this GPU")
	check(FileAccess.get_sha256(fixture) == original_hash, "painting preserves original GLB hash")
	start = Time.get_ticks_usec()
	for frame in range(48):
		var rendered := await renderer.capture(keys, layers, frame)
		check(rendered.save_png(output.path_join("frame_%06d.png" % (frame + 1))) == OK, "write frame %d" % frame)
	print("BENCH render+PNG 48 full-HD frames: %.3f s" % ((Time.get_ticks_usec() - start) / 1000000.0))
	var encoder := Encoder.new()
	var ffmpeg := OS.get_environment("HYBRID_FFMPEG")
	if ffmpeg.is_empty(): ffmpeg = "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
	check(Encoder.detect(ffmpeg).ok, "H264/AAC encoder detection")
	var video := {"fps_num": 24, "fps_den": 1, "duration_frames": 48}
	var error := await encoder.encode(self, ffmpeg, output, video)
	check(error.is_empty(), "silent MP4 encode: " + error)
	print("SPIKES failures=", failures, " output=", output)
	quit(0 if failures == 0 else 1)
