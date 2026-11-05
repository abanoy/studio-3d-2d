extends SceneTree
const Encoder = preload("res://src/encoder.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var folder := ProjectSettings.globalize_path("res://output/spikes")
	var ffmpeg := OS.get_environment("HYBRID_FFMPEG")
	if ffmpeg.is_empty(): ffmpeg = "C:/Program Files/ffmpeg/bin/ffmpeg.exe"
	var encoder := Encoder.new()
	var error := await encoder.encode(self, ffmpeg, folder, {"fps_num": 24, "fps_den": 1, "duration_frames": 48}, folder.path_join("known tone.wav"))
	print("AUDIO_SPIKE ", "PASS" if error.is_empty() else error)
	quit(0 if error.is_empty() else 1)
