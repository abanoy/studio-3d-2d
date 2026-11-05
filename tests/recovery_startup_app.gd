extends "res://src/app.gd"
# Isolate storage before the unchanged production _ready runs. No startup override.
func _init() -> void:
	recovery_root=str(OS.get_cmdline_user_args()[0]).path_join("recovery")
