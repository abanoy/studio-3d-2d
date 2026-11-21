extends "res://src/source_import.gd"
func start(_path: String,_as_model: bool,_at_frame := 0,_placement := {}) -> void:
	app.message("Native model conversion needs Windows Studio. This browser preview imports embedded GLB and packed HAS.")
