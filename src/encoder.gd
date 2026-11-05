extends RefCounted
var cancelled := false
var process_id := -1
var log_text := ""

static func detect(path: String) -> Dictionary:
	if path.is_empty() or ((path.is_absolute_path() or path.contains("/") or path.contains("\\")) and not FileAccess.file_exists(path)):
		return {"ok":false,"log":"Movie encoder file is unavailable.","exit_code":-1}
	var output := []
	var code := OS.execute(path, ["-hide_banner", "-encoders"], output, true)
	var text := "\n".join(output)
	return {"ok": code == 0 and text.contains("libx264 ") and text.contains(" aac "), "log": text, "exit_code": code}

func cancel() -> void:
	cancelled = true
	if process_id > 0 and OS.is_process_running(process_id):
		OS.kill(process_id)

func encode(tree: SceneTree, ffmpeg: String, folder: String, video: Dictionary, audio := "") -> String:
	var output_path := folder.path_join("movie.mp4")
	var args := PackedStringArray(["-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-framerate", "%d/%d" % [video.fps_num, video.fps_den], "-i", folder.path_join("frame_%06d.png")])
	if not audio.is_empty():
		args.append_array(["-i", audio])
	args.append_array(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast"])
	if not audio.is_empty():
		args.append_array(["-af", "apad", "-c:a", "aac", "-b:a", "192k"])
	args.append_array(["-t", "%.9f" % (float(video.duration_frames) * video.fps_den / video.fps_num), "-movflags", "+faststart", output_path])
	var process := OS.execute_with_pipe(ffmpeg, args, false)
	if process.is_empty():
		return "Could not start FFmpeg. PNGs are preserved."
	process_id = process.pid
	log_text = "Arguments: %s\n" % str(args)
	while OS.is_process_running(process_id):
		log_text += process.stderr.get_buffer(8192).get_string_from_utf8()
		await tree.process_frame
	log_text += process.stderr.get_buffer(65536).get_string_from_utf8()
	var code := OS.get_process_exit_code(process_id)
	process_id = -1
	var log_file := FileAccess.open(folder.path_join("encoder.log"), FileAccess.WRITE)
	if log_file:
		log_file.store_string(log_text + "\nExit: %d\n" % code)
	if cancelled:
		return "Export cancelled. Frames and log kept in " + folder
	if code != 0 or not FileAccess.file_exists(output_path):
		return "FFmpeg failed (exit %d). See %s\n%s" % [code, folder.path_join("encoder.log"), log_text.right(1000)]
	return ""
