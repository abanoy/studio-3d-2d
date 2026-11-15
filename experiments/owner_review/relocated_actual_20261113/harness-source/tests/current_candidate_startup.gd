extends Node
var finished:=false
var recovery:={}
func _ready() -> void:
	get_tree().create_timer(30).timeout.connect(func():get_tree().quit(2))
	call_deferred("run")
func completed(result: Dictionary) -> void:
	recovery=result;finished=true
func run() -> void:
	# Running as a scene, not --script: app takes its ordinary automatic recovery
	# and Home startup path, with no smoke flags or forced Home call.
	var app=load("res://main.tscn").instantiate();app.startup_recovery_finished.connect(completed);add_child(app)
	while not finished:await get_tree().process_frame
	for i in range(4):await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var ok: bool=app.home.visible and app.home.new_button.visible and app.home.tutorials_button.visible and not app.advanced_mode and app.current_world().objects.is_empty()
	var path: String=OS.get_cmdline_user_args()[0]
	var result:={"home_visible":app.home.visible,"simple":not app.advanced_mode,"empty":app.current_world().objects.is_empty(),"recovery":recovery,"profile":OS.get_user_data_dir()}
	app.get_viewport().get_texture().get_image().save_png(path.get_base_dir().path_join("normal-home.png"))
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(result));print("CURRENT_REVIEW_STARTUP ",JSON.stringify(result));get_tree().quit(0 if ok else 1)
