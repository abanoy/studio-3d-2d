extends "res://src/app.gd"
# Only paths change; production _ready and its automatic recovery remain intact.
func _init() -> void:
	var folder: String=OS.get_cmdline_user_args()[0]
	recovery_root=folder.path_join("recovery")
	recent_path=folder.path_join("recents.json")
	display_prefs_path=folder.path_join("prefs.cfg")
