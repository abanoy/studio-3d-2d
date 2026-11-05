extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
	create_timer(30).timeout.connect(func():push_error("Comparison teardown watchdog");quit(2))
	var folder: String=OS.get_cmdline_user_args()[0]
	var plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plans.json")))[0]
	var app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("teardown-recovery");root.add_child(app)
	for i in range(3):await process_frame
	app.autosave_enabled.button_pressed=false;var error: String=app.pose_editor.add_model(plan.source);app.set_advanced(true);app.pose_editor.open_shapes()
	for i in range(3):await process_frame
	var editor=app.pose_editor.animated_shapes;editor.node_index=int(editor.rows()[0].node);editor.shape_index=0;editor.rebuild()
	var comparison=editor.comparison;comparison.open()
	while comparison.phase<0:await process_frame
	var pending: bool=error.is_empty() and comparison.phase>0 and RenderingServer.frame_post_draw.is_connected(comparison.rendered)
	var weak: WeakRef=weakref(comparison);var callback: Callable=comparison.rendered
	app.free()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var cleaned: bool=weak.get_ref()==null and not RenderingServer.frame_post_draw.is_connected(callback)
	var result:={"checks":2,"failures":int(not pending)+int(not cleaned),"actual_readback_pending":pending,"released_after_app_free":cleaned}
	FileAccess.open(folder.path_join("teardown-result.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("SHAPE_COMPARISON_TEARDOWN "+JSON.stringify(result));quit(0 if result.failures==0 else 1)
