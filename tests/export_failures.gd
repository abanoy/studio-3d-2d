extends SceneTree
const Encoder = preload("res://src/encoder.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var arguments:=OS.get_cmdline_user_args()
	var root: String=arguments[0] if not arguments.is_empty() else ProjectSettings.globalize_path("res://output")
	var frames: String=arguments[1] if arguments.size()>1 else root.path_join("spikes")
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
	error = await encoder.encode(self, negative.path_join("absent-encoder.exe"), negative, video, "", true)
	if not error.contains("absent-encoder.exe") or not error.contains("Details: ") or not FileAccess.file_exists(error.get_slice("Details: ",1)):
		print("FAIL encoder launch error lacks location or saved diagnostic: ", error)
		quit(1)
		return
	print("PASS retry reports missing executable and keeps separate diagnostic")
	var existing:=root.path_join("existing-output")
	DirAccess.make_dir_recursive_absolute(existing)
	for frame in range(1,49):
		var name:="frame_%06d.png" % frame
		if DirAccess.copy_absolute(frames.path_join(name),existing.path_join(name))!=OK:
			quit(1)
			return
	var previous_movie:=existing.path_join("movie.mp4")
	var previous_log:=existing.path_join("encoder.log")
	var prior:=FileAccess.open(previous_movie,FileAccess.WRITE)
	prior.store_string("Owned test fixture: preserve this earlier output.");prior.close()
	prior=FileAccess.open(previous_log,FileAccess.WRITE)
	prior.store_string("Owned test fixture: preserve the earlier diagnostic.\n");prior.close()
	var movie_hash:=FileAccess.get_sha256(previous_movie)
	var log_hash:=FileAccess.get_sha256(previous_log)
	encoder.finished_path="earlier-success.mp4"
	error=await encoder.encode(self,ffmpeg,existing,video)
	if not error.contains("already exists") or not encoder.finished_path.is_empty() or encoder.process_id!=-1 or FileAccess.get_sha256(previous_movie)!=movie_hash or FileAccess.get_sha256(previous_log)!=log_hash:
		print("FAIL existing movie was accepted or its prior output/log changed: ",error)
		quit(1)
		return
	print("PASS existing movie refusal preserves output/log/frames and clears stale success")
	var python:=OS.get_environment("HYBRID_PYTHON")
	if python.is_empty():python="C:/Program Files/Python313/python.exe" if OS.get_name()=="Windows" else "python3"
	var partial:=root.path_join("controlled-partial.mp4")
	var child:=OS.execute_with_pipe(python,PackedStringArray(["-I","-B","-c","import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(b'controlled partial output');sys.exit(37)",partial]),false)
	if child.is_empty():
		print("FAIL controlled exit fixture did not start")
		quit(1)
		return
	while OS.is_process_running(child.pid):await process_frame
	var exit_code:=OS.get_process_exit_code(child.pid)
	var retained:=true
	for attempt in range(3):retained=retained and not OS.is_process_running(child.pid) and OS.get_process_exit_code(child.pid)==37
	child.stdio.close();child.stderr.close()
	if exit_code!=37 or not retained or not FileAccess.file_exists(partial):
		print("FAIL controlled partial-output child lost its nonzero exit: ",exit_code)
		quit(1)
		return
	print("PASS partial output does not erase the actual exit37 across repeated process polls")
	var cancel_dir := root.path_join("cancel-encoding")
	DirAccess.make_dir_recursive_absolute(cancel_dir)
	for frame in range(1, 49):
		var name := "frame_%06d.png" % frame
		if DirAccess.copy_absolute(frames.path_join(name), cancel_dir.path_join(name)) != OK:
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
