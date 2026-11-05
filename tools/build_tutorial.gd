extends SceneTree
func _initialize() -> void:
	var error: String=preload("res://src/tutorial_assets.gd").build(OS.get_cmdline_user_args()[0])
	print("TUTORIAL_ASSETS "+JSON.stringify({"error":error}));quit(0 if error.is_empty() else 1)
