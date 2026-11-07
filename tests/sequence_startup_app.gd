extends "res://src/app.gd"
# Isolate storage before unchanged production _ready; no startup override.
func _init() -> void:
	if not "--auto-open" in OS.get_cmdline_user_args():
		cold_cel_loading="--adaptive-open" in OS.get_cmdline_user_args()
		cold_cel_min_bytes=0
	var folder: String=OS.get_cmdline_user_args()[0]
	recovery_root=folder.path_join("recovery");recent_path=folder.path_join("startup-recents.json");display_prefs_path=folder.path_join("startup-prefs.cfg")
