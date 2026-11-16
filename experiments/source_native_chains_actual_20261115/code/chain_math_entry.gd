extends SceneTree
const Checks = preload("res://math_checks.gd")
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1: push_error("Fresh root chain math lease required"); quit(2); return
	var value = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not value is Dictionary or value.get("phase") != "ROOT_APPROVED_CHAIN_SYNTHETIC_MATH" or value.get("root_closed_all") != true or float(value.get("expires_unix",0)) <= Time.get_unix_time_from_system(): push_error("Invalid chain math authority"); quit(2); return
	if DisplayServer.get_name() != "headless" or FileAccess.get_sha256(OS.get_executable_path()) != str(value.get("engine_sha256","")): push_error("Exact headless engine required"); quit(2); return
	for pin in value.files.values():
		if not str(pin.path).is_absolute_path() or FileAccess.get_sha256(str(pin.path)) != str(pin.sha256): push_error("Changed chain math source/proof"); quit(2); return
	var path: String = value.public_result
	if not path.is_absolute_path() or FileAccess.file_exists(path): push_error("Fresh math result required"); quit(2); return
	var checks = Checks.new()
	var result: Dictionary = checks.run()
	result["root_lease_sha256"] = FileAccess.get_sha256(args[0])
	var passed: bool = result.get("status") == "PASSED_SYNTHETIC_CHAIN_MATH_ONLY" and result.get("checks") == 4012 and result.get("failures") is Array and result.failures.is_empty()
	var file := FileAccess.open(path,FileAccess.WRITE)
	if file == null: push_error("Cannot write chain math result"); quit(2); return
	file.store_string(JSON.stringify(result,"",true,true)); file.close()
	print("CHAIN_MATH "+JSON.stringify({"checks":result.get("checks",0),"passed":passed}))
	quit(0 if passed else 1)
