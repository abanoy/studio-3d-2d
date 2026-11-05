extends "res://src/app.gd"
# Test constructor only: normal production _ready/recovery remain inherited.
func _init() -> void:
	var args:=OS.get_cmdline_user_args();recovery_root=str(args[0]).path_join("recovery")
	var label: String=args[1]
	if label in ["current-pid-mismatch","current-pid-match"]:
		var expected:=Recovery.read_json(str(args[0]).path_join("expected.json"));var folder: String=expected.checkpoint
		assert(folder.replace("\\","/").simplify_path().begins_with(recovery_root.replace("\\","/").simplify_path()+"/"))
		var owner:=Recovery.read_json(folder.path_join("session.json"))
		if label=="current-pid-match":owner=Recovery.owner_record()
		else:owner.pid=OS.get_process_id()
		assert(Recovery.valid_creation(owner.get("created_100ns")));Recovery.write_json(folder.path_join("session.json"),owner)
	if label=="helper-unavailable":
		# Existing read-only executable returns no helper protocol. No missing-exe
		# OS error, no process control, no production test bypass or visible app.
		var alternate:=OS.get_environment("WINDIR").path_join("System32/where.exe");assert(FileAccess.file_exists(alternate));OS.set_environment("HYBRID_PYTHON",alternate)
