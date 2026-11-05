extends "res://src/source_browser.gd"
func open(_as_model := true) -> void:
	app.message("Web browsers cannot scan installed games. Import an embedded GLB or a packed HAS prepared in Windows Studio.")
