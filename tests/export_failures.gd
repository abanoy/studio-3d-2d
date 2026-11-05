extends SceneTree
const Encoder = preload("res://src/encoder.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var root := ProjectSettings.globalize_path("res://output")
	var negative := root.path_join("missing-sequence")
	DirAccess.make_dir_recursive_absolute(negative)
	var ffmpeg := OS.get_environment("HYBRID_FFMPEG")
	if ffmpeg.is_empty(): ffmpeg = "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
	var encoder := Encoder.new()
	var video := {"fps_num": 24, "fps_den": 1, "duration_frames": 48}
	var error := await encoder.encode(self, ffmpeg, negative, video)
	if not error.contains("FFmpeg failed") or not FileAccess.file_exists(negative.path_join("encoder.log")):
		print("FAIL missing sequence did not produce readable logged error: ", error)
		quit(1)
		return
	print("PASS failed encode preserves log and reports exit")
	var cancel_dir := root.path_join("cancel-encoding")
	DirAccess.make_dir_recursive_absolute(cancel_dir)
	for frame in range(1, 49):
		var name := "frame_%06d.png" % frame
		if DirAccess.copy_absolute(root.path_join("spikes").path_join(name), cancel_dir.path_join(name)) != OK:
			quit(1)
			return
	encoder = Encoder.new()
	create_timer(0.02).timeout.connect(encoder.cancel)
	error = await encoder.encode(self, ffmpeg, cancel_dir, video)
	if not error.contains("cancelled") or encoder.process_id != -1:
		print("FAIL cancel encoding: ", error)
		quit(1)
		return
	print("PASS cancel encoding stops owned process and preserves PNGs")
	print("EXPORT_FAILURES failures=0")
	quit(0)
