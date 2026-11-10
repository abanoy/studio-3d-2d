extends SceneTree
const Timeline=preload("res://src/timeline.gd")
var app
var failures:=0
func _initialize() -> void:
	create_timer(150).timeout.connect(func():push_error("Native fixture preparation watchdog");quit(2));call_deferred("run")
func settle() -> void:
	for i in range(5):await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var folder: String=OS.get_cmdline_user_args()[0];var plans: Array=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("native-project-plan.json")))
	app=load("res://main.tscn").instantiate();app.recovery_root=folder.path_join("native-fixture-recovery");app.display_prefs_path=folder.path_join("native-fixture-prefs.cfg");app.recent_path=folder.path_join("native-fixture-recents.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false
	var results:=[]
	for plan in plans:
		app.new_project();var error: String=app.pose_editor.add_model(plan.source);await settle()
		if not error.is_empty():push_error(error);failures+=1;continue
		app.pose_editor.frame_model();await settle()
		app.keys=[Timeline.from_camera(0,app.renderer.camera,"ease")]
		app.project_folder=plan.project;app.save();await settle()
		var saved:=FileAccess.file_exists(plan.project.path_join("project.json"))
		if not saved:failures+=1
		var rig=app.renderer.active_model();results.append({"label":plan.label,"project":plan.project,"source_sha256":FileAccess.get_sha256(plan.source),"bones":rig.order.size(),"native_metadata":not rig.data.metadata.get("native_parameters",{}).is_empty(),"saved":saved})
	print("NATIVE_FIXTURE_PROJECTS "+JSON.stringify({"failures":failures,"results":results}));app.free();quit(0 if failures==0 else 1)
