extends SceneTree
const Runtime=preload("res://src/wind_helper_runtime.gd")
func _initialize() -> void:
	var result:=Runtime.resolve_hint("python",OS.get_environment("PATH"))
	print("HELPER_DEFAULT_RUNTIME "+JSON.stringify(result))
	quit(0 if result.has("path") and Runtime.approved(result.path) else 1)
