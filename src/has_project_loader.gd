extends RefCounted
# Owns CPU/file decode until joined. Never touches the live document or renderer.
const Storage=preload("res://src/storage.gd")
var thread: Thread
func busy() -> bool:return thread!=null and thread.is_started()
func start(request: Dictionary) -> String:
	if busy():return "A project is already being decoded."
	if not request.get("folder") is String or request.folder.is_empty() or not request.get("cancel") is String or request.cancel.is_empty():return "Missing project loading address."
	thread=Thread.new();var why:=thread.start(_run.bind(request.duplicate(true)),Thread.PRIORITY_LOW)
	if why!=OK:thread=null;return "Cannot start project loading worker."
	return ""
func poll() -> Dictionary:return finish() if busy() and not thread.is_alive() else {}
func finish() -> Dictionary:
	if not busy():return {}
	var result: Dictionary=thread.wait_to_finish();thread=null;return result
func decode(request: Dictionary) -> Dictionary:
	return Storage.load_project(request.folder,"project.json",bool(request.get("cold",false)),int(request.get("cold_min_bytes",0)),request.cancel)
func _run(request: Dictionary) -> Dictionary:
	var started:=Time.get_ticks_usec();var data:=decode(request)
	if FileAccess.file_exists(request.cancel):data={"error":"Project opening cancelled. Previous project preserved."}
	return {"data":data,"worker_ms":(Time.get_ticks_usec()-started)/1000.,"background_thread":not Thread.is_main_thread()}
