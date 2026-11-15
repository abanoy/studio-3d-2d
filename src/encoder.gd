extends RefCounted
const PROFILES={"standard":{"label":"Standard","crf":"18","preset":"fast","audio":"192k"},"small":{"label":"Smaller file","crf":"24","preset":"fast","audio":"128k"},"high":{"label":"High quality","crf":"14","preset":"slow","audio":"256k"}}
var profile:="standard"
var cancelled := false
var process_id := -1
var log_text := ""
static func profile_error(value) -> String:
	return "" if value is String and PROFILES.has(value) else "Choose an available movie quality profile in Advanced → Movie encoder."

static func missing_executable(path: String) -> bool:
	return path.is_empty() or ((path.is_absolute_path() or path.contains("/") or path.contains("\\")) and not FileAccess.file_exists(path))

static func detect(path: String) -> Dictionary:
	if missing_executable(path):
		return {"ok":false,"log":"Movie encoder file is unavailable.","exit_code":-1}
	var output := []
	var code := OS.execute(path, ["-hide_banner", "-encoders"], output, true)
	var text := "\n".join(output)
	return {"ok": code == 0 and text.contains("libx264 ") and text.contains(" aac "), "log": text, "exit_code": code}

func cancel() -> void:
	if cancelled:return
	cancelled = true
	if process_id > 0 and OS.is_process_running(process_id):
		OS.kill(process_id)

func encode(tree: SceneTree, ffmpeg: String, folder: String, video: Dictionary, audio := "",retry:=false) -> String:
	finished_path=""
	var why:=profile_error(profile)
	if not why.is_empty():return why
	var selected: Dictionary=PROFILES[profile]
	var output_path := folder.path_join("movie-%d.mp4" % Time.get_ticks_usec() if retry else "movie.mp4")
	var log_path:=output_path.get_basename()+".log" if retry else folder.path_join("encoder.log")
	if FileAccess.file_exists(output_path) or DirAccess.dir_exists_absolute(output_path):
		return "Movie destination already exists. The existing movie, log and rendered frames were preserved. Retry encoding creates a separate movie."
	var args := PackedStringArray(["-hide_banner", "-nostdin", "-n", "-loglevel", "error", "-framerate", "%d/%d" % [video.fps_num, video.fps_den], "-i", folder.path_join("frame_%06d.png")])
	if not audio.is_empty():
		args.append_array(["-i", audio])
	args.append_array(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", selected.crf, "-preset", selected.preset])
	if not audio.is_empty():
		args.append_array(["-af", "apad", "-c:a", "aac", "-b:a", selected.audio])
	args.append_array(["-t", "%.9f" % (float(video.duration_frames) * video.fps_den / video.fps_num), "-movflags", "+faststart", output_path])
	var process := {} if missing_executable(ffmpeg) else OS.execute_with_pipe(ffmpeg, args, false)
	if process.is_empty():
		var reason := "Could not start FFmpeg at %s. Check the encoder location and retry. Rendered frames are preserved." % ffmpeg
		var failed_log := FileAccess.open(log_path, FileAccess.WRITE)
		if failed_log:
			failed_log.store_string(reason + "\nProfile: " + profile + "\nArguments: " + str(args))
			failed_log.flush();failed_log.close()
			return reason + "\nDetails: " + log_path
		return reason
	process_id = process.pid
	log_text = "Profile: %s\nArguments: %s\n" % [profile,str(args)]
	var error_output:=""
	# OS.kill reaps the owned Unix child. Querying that PID again can produce
	# ECHILD in Godot; cancellation already establishes this attempt's outcome.
	while not cancelled and OS.is_process_running(process_id):
		error_output += process.stderr.get_buffer(8192).get_string_from_utf8()
		await tree.process_frame
	error_output += process.stderr.get_buffer(65536).get_string_from_utf8()
	log_text += error_output
	var code := -1 if cancelled else OS.get_process_exit_code(process_id)
	process_id = -1
	var log_file := FileAccess.open(log_path, FileAccess.WRITE)
	if log_file:
		log_file.store_string(log_text + "\nExit: %d\n" % code)
		log_file.flush();log_file.close()
	if cancelled:
		return "Export cancelled. Frames and log kept in " + folder
	# FFmpeg can return0 for AVERROR_EXIT, including its -n overwrite refusal.
	# With -loglevel error, diagnostics cannot certify a completed movie.
	if code != 0 or not error_output.strip_edges().is_empty() or not FileAccess.file_exists(output_path):
		return "FFmpeg failed (exit %d). See %s\n%s" % [code, log_path, log_text.right(1000)]
	finished_path=output_path
	return ""

var finished_path: String=""
