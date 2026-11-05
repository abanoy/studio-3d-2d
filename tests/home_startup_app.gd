extends "res://src/app.gd"
# Only local fixture storage is configured before inherited production _ready.
func _init() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	recovery_root=folder.path_join("recovery");recent_path=folder.path_join("recents.json")
