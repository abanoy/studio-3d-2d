extends SceneTree
## An isolated headless experiment, not an application test or native oracle.
var stop_mutex := Mutex.new()
var stop_requested := false
var worker: Thread
var request := {}
var rows: Array = []
var source_cwd_samples: Array = []

func _initialize() -> void:
	call_deferred("run")

func stopped() -> bool:
	stop_mutex.lock(); var value: bool = stop_requested; stop_mutex.unlock(); return value

func churn(path: String) -> Dictionary:
	var count := 0; var failures := 0; var began := Time.get_ticks_msec()
	while not stopped() and Time.get_ticks_msec() - began < 60000:
		var directory := DirAccess.open(path)
		if directory == null: failures += 1
		else:
			if directory.change_dir(path) != OK: failures += 1
		count += 1
	return {"iterations": count, "directory_failures": failures}

func sample_cwd() -> Dictionary:
	# OS.get_cwd is not exposed by Godot4.6. This operation is itself a
	# DirAccess call; retain its result as intrusive sampled context, not an
	# atomic GetCurrentDirectoryW measurement of the launch instant.
	var directory := DirAccess.open(".")
	return {"kind": "intrusive_DirAccess_open_dot", "cwd": directory.get_current_dir() if directory else "", "available": directory != null}

func one_phase(label: String, path: String, attempts: int) -> Dictionary:
	stop_mutex.lock(); stop_requested = false; stop_mutex.unlock()
	var thread_error := OK
	if not path.is_empty():
		worker = Thread.new(); thread_error = worker.start(churn.bind(path))
		OS.delay_msec(10)
	var result := {"label": label, "churn_path": path, "churn_path_chars": path.length(), "thread_start": thread_error,
		"attempts": 0, "launch_failures": 0, "nonzero_child_exits": 0, "timeouts": 0, "map_close_failures": 0, "children": []}
	for i in range(attempts):
		var before: Dictionary = sample_cwd()
		var began := Time.get_ticks_msec()
		var child := OS.create_process(str(request.python), PackedStringArray(["-I", "-B", "-c", "pass"]), false)
		var record := {"attempt": i, "pid": child, "before": before, "after_create": sample_cwd(), "exit": null, "elapsed_ms": 0, "mapped_handle_closed": false}
		result.attempts += 1
		if child <= 0:
			result.launch_failures += 1
		else:
			while OS.is_process_running(child) and Time.get_ticks_msec() - began < 10000: OS.delay_msec(1)
			if OS.is_process_running(child): result.timeouts += 1
			else:
				record.exit = OS.get_process_exit_code(child)
				if record.exit != 0: result.nonzero_child_exits += 1
			# The exact Godot source keeps our process handle in process_map.
			# kill erases this owned entry and closes that original handle even
			# when the process already exited. Never call kill for an unowned ID.
			var close_result := OS.kill(child)
			record.close_result = close_result
			record.mapped_handle_closed = OS.get_process_exit_code(child) == -1
			if not record.mapped_handle_closed: result.map_close_failures += 1
			# An owned timeout was killed/closed before another child may start.
			if result.timeouts > 0: break
		record.elapsed_ms = Time.get_ticks_msec() - began
		result.children.append(record)
	stop_mutex.lock(); stop_requested = true; stop_mutex.unlock()
	if worker != null:
		result.thread_result = worker.wait_to_finish(); worker = null
	else: result.thread_result = {"iterations": 0, "directory_failures": 0}
	return result

func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: push_error("One owned request is required"); quit(2); return
	request = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if request.get("format") != "studio_source_cwd_race_probe_1" or not str(request.get("python", "")).is_absolute_path():
		push_error("Invalid owned request"); quit(2); return
	if FileAccess.get_sha256(request.python) != request.python_sha256:
		push_error("Approved Python changed"); quit(2); return
	rows.append(one_phase("control", "", 40))
	rows.append(one_phase("short_directory_churn", request.short_dir, 80))
	rows.append(one_phase("long_directory_churn", request.long_dir, 80))
	rows.append(one_phase("control_after_threads", "", 40))
	var result := {"format": "studio_source_cwd_race_result_1", "pid": OS.get_process_id(), "rows": rows,
		"maximum_python_children_alive": 1, "gpu_used": false,
		"cwd_observation_limit": "DirAccess('.') samples are intrusive and not atomic launch-time WinAPI CWD observations",
		"win32_error_code_available": false, "native_or_app_fidelity_claimed": false}
	var file := FileAccess.open(request.result, FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "\t")); file.close()
	print("SOURCE_CURRENTDIR_RACE " + JSON.stringify(result))
	quit(0)
