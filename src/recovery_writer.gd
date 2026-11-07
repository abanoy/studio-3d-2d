extends RefCounted
# One isolated checkpoint worker; only capture and completed-thread polling run
# on the main thread. Journal previews serialize with this worker in the app.
const Frozen=preload("res://src/recovery_snapshot.gd")
const Recovery=preload("res://src/recovery.gd")
var thread: Thread
func busy() -> bool:return thread!=null and thread.is_started()
func start(project: Dictionary,request: Dictionary) -> String:
 if busy():return "A recovery checkpoint is already being prepared."
 if not request.get("root") is String or not request.get("session") is String:return "Missing recovery checkpoint address."
 var started:=Time.get_ticks_usec();var frozen:=Frozen.capture(project)
 if frozen.has("error"):return frozen.error
 # Probe/cache our process identity before the worker; it receives no live app.
 Recovery.owner_record()
 var captured:=request.duplicate(true);captured["capture_ms"]=(Time.get_ticks_usec()-started)/1000.0
 thread=Thread.new();var error:=thread.start(_run.bind(frozen.project,captured),Thread.PRIORITY_LOW)
 if error!=OK:thread=null;return "Cannot start recovery checkpoint worker."
 return ""
func poll() -> Dictionary:
 if not busy() or thread.is_alive():return {}
 return finish()
func finish() -> Dictionary:
 if not busy():return {}
 var result: Dictionary=thread.wait_to_finish();thread=null;return result
func persist(project: Dictionary,request: Dictionary) -> String:
 return Recovery.checkpoint(request.root,request.session,project.video,project.camera_keys,project.layers,str(project.get("source","")),int(project.editor.frame),project.audio,str(request.get("origin","")),int(request.revision),project.get("model",{}),project.get("world",{}),project.get("palette",[]),project.get("sequence_graph",{}),project.get("sequence_context",{}),project.get("reference_sheet",{}),request.get("lesson_context",{}))
func _run(project: Dictionary,request: Dictionary) -> Dictionary:
 var started:=Time.get_ticks_usec();var adopted:=Frozen.adopt(project)
 var error: String=adopted.error if adopted.has("error") else persist(adopted.project,request)
 var folder: String=request.root.path_join(request.session)
 return {"request":request,"folder":folder,"error":error,"digest":FileAccess.get_sha256(folder.path_join("project.json")) if error.is_empty() else "","worker_ms":(Time.get_ticks_usec()-started)/1000.0,"background_thread":not Thread.is_main_thread()}
