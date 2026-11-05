extends "res://src/app.gd"
# Storage isolation only; the production _ready and startup dispatch stay intact.
func _init() -> void:
	var args:=OS.get_cmdline_user_args();var folder: String=args[0];var mode: String=args[1]
	recovery_root=folder.path_join("recovery") if mode=="recovery" else folder.path_join("reader-recovery-"+mode)
	recent_path=folder.path_join("reader-preferences-"+mode+".json")
