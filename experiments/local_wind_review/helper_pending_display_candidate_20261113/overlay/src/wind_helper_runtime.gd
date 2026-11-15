extends RefCounted
# Resolve only the already-approved Windows runtime; never launch a bare hint.
const PYTHON_SHA256="03573716a7fcbd8b7fed8fe0163bbfbd3a852546920d6a666123f307c8dac7d9"
static func approved(path: String) -> bool:
	return path.is_absolute_path() and FileAccess.file_exists(path) and path.get_file().to_lower()=="python.exe" and FileAccess.get_sha256(path)==PYTHON_SHA256
static func resolve_hint(hint: String,path_value: String) -> Dictionary:
	if hint.is_absolute_path():return {"path":hint} if approved(hint) else {"error":"The selected Python installation has changed or is unsupported."}
	if not hint.to_lower() in ["python","python.exe"]:return {"error":"Choose the supported Python installation before trying this setup."}
	for directory in path_value.split(";",false):
		var base: String=directory.trim_prefix('"').trim_suffix('"')
		if not base.is_absolute_path():continue
		var candidate:=base.path_join("python.exe")
		if approved(candidate):return {"path":candidate}
	return {"error":"The supported Python installation could not be found."}
static func configuration(app) -> Dictionary:
	if OS.get_name()!="Windows":return {"error":"This setup preview currently needs the supported Windows runtime."}
	var hint: String=app.helper_preview_runtime_path
	if hint.is_empty():
		var saved:=ConfigFile.new()
		if saved.load("user://helper-runtime.cfg")==OK:
			hint=str(saved.get_value("runtime","python",""))
			if not hint.is_empty() and not hint.is_absolute_path():return {"error":"The saved Python installation must be an absolute path."}
	if hint.is_empty():hint=app.source_import.python()
	var python:=resolve_hint(hint,OS.get_environment("PATH"))
	if python.has("error"):return python
	var code_root:=ProjectSettings.globalize_path("res://").simplify_path().trim_suffix("/")
	var controller:=code_root.path_join("tools/wind_preview_controller.py")
	if not FileAccess.file_exists(controller):return {"error":"This Studio build does not include setup preview support."}
	var work_root: String=app.helper_preview_work_root
	if work_root.is_empty():work_root=OS.get_user_data_dir().path_join("helper-preview")
	if not work_root.is_absolute_path():return {"error":"Setup preview needs an absolute profile work folder."}
	if DirAccess.make_dir_recursive_absolute(work_root)!=OK:return {"error":"Cannot create the setup preview work folder."}
	var session:=Crypto.new().generate_random_bytes(16).hex_encode()
	return {"main_root":code_root,"work_root":work_root,"owned_root":work_root.path_join(session),"python":python.path,"python_sha256":PYTHON_SHA256,"controller":controller,"controller_sha256":FileAccess.get_sha256(controller),"launcher":controller,"launcher_sha256":FileAccess.get_sha256(controller),"session":session}
