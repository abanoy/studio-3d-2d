extends "res://src/app.gd"
# Isolate storage before unchanged production _ready; no startup override.
func _init() -> void:
	cold_cel_loading="--adaptive-open" in OS.get_cmdline_user_args()
	var folder: String=OS.get_cmdline_user_args()[0]
	recovery_root=folder.path_join("recovery");recent_path=folder.path_join("startup-recents.json");display_prefs_path=folder.path_join("startup-prefs.cfg")
