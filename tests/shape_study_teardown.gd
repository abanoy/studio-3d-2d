extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	create_timer(30).timeout.connect(func():push_error("Study teardown watchdog");quit(2))
	var folder: String=OS.get_cmdline_user_args()[0]
	var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))
	var plan: Dictionary=plans[0]
	for row in plans:
		if row.label=="SFM":plan=row
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("teardown-recovery");root.add_child(app)
	for i in range(3):await process_frame
	app.autosave_enabled.button_pressed=false;var error: String=app.pose_editor.add_model(plan.source);app.pose_editor.open_shapes();app.set_advanced(true)
	for i in range(3):await process_frame
	var study=app.pose_editor.animated_shapes.study;study.start();var worker_pid: int=study.pid
	var started: bool=error.is_empty() and worker_pid>0 and OS.is_process_running(worker_pid)
	app.free();await create_timer(.15).timeout
	var stopped: bool=worker_pid>0 and not OS.is_process_running(worker_pid)
	var result:={"checks":2,"failures":int(not started)+int(not stopped),"actual_worker_started":started,"worker_stopped_after_app_free":stopped,"worker_pid":worker_pid,"source":plan.label}
	FileAccess.open(folder.path_join("teardown-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_STUDY_TEARDOWN "+JSON.stringify(result));quit(0 if result.failures==0 else 1)
