extends RefCounted
# CPU/files only. No live app, owner/cache, renderer or scene node crosses here.
const Frozen=preload("res://src/recovery_snapshot.gd")
const Storage=preload("res://src/storage.gd")
const World=preload("res://src/world_document.gd")
const FORMAT="studio_has_snapshot_ready_1"
var thread: Thread
var _prepared: Dictionary={}
func busy() -> bool:return thread!=null and thread.is_started()
func prepare(project: Dictionary,request: Dictionary) -> String:
	if busy() or has_prepared():return "A project snapshot is already being saved."
	for field in ["folder","ready","cancel"]:
		if not request.get(field) is String or request[field].is_empty():return "Missing project snapshot address."
	var began:=Time.get_ticks_usec();var frozen:=Frozen.capture(project)
	if frozen.has("error"):return frozen.error
	var copied:=request.duplicate(true);copied["capture_ms"]=(Time.get_ticks_usec()-began)/1000.
	_prepared={"project":frozen.project,"request":copied}
	return ""
func has_prepared() -> bool:return not _prepared.is_empty()
func discard_prepared() -> void:_prepared={}
func _start_thread(work: Callable) -> Error:return thread.start(work,Thread.PRIORITY_LOW)
func launch() -> String:
	if busy():return "A project snapshot is already being saved."
	if not has_prepared():return "No captured project snapshot is ready to start."
	var captured: Dictionary=_prepared;_prepared={}
	thread=Thread.new();var why:=_start_thread(_run.bind(captured.project,captured.request))
	if why!=OK:thread=null;return "Cannot start project snapshot worker."
	return ""
func start(project: Dictionary,request: Dictionary) -> String:
	var why:=prepare(project,request)
	return why if not why.is_empty() else launch()
func poll() -> Dictionary:
	return finish() if busy() and not thread.is_alive() else {}
func finish() -> Dictionary:
	discard_prepared()
	if not busy():return {}
	var result: Dictionary=thread.wait_to_finish();thread=null;return result
func persist(project: Dictionary,request: Dictionary) -> String:
	return Storage.save_project(request.folder,project.video,project.camera_keys,project.layers,str(project.get("source","")),int(project.editor.frame),project.audio,{},project.get("model",{}),true,project.world,{"sequence_editor":project.sequence_context} if not project.get("sequence_context",{}).is_empty() else {},project.get("palette",[]),project.get("sequence_graph",{}),null,project.get("reference_sheet",{}),request.cancel)
func references(project: Dictionary,origins: Dictionary) -> Dictionary:
	var result: Dictionary={};var sheet: Dictionary=project.get("reference_sheet",{})
	if not sheet.is_empty():result["references/"+sheet.sha256+".png"]=ProjectSettings.globalize_path(sheet.source)
	var scenes: Array=[project]
	for asset in project.get("sequence_graph",{}).get("assets",[]):scenes.append(asset.scene)
	var sources: Array=[]
	for scene in scenes:
		for clip in preload("res://src/audio_track.gd").clips(scene.get("audio",{})):sources.append(clip.source.path)
		if not scene.get("world",{}).is_empty():
			for row in World.assets(scene.world):
				var absolute:=ProjectSettings.globalize_path(row.source).replace("\\","/");var original: String=origins.get(absolute,absolute)
				result[row.path]=original if FileAccess.file_exists(original) and FileAccess.get_sha256(original)==row.sha256 else absolute
		else:sources.append_array([str(scene.get("source","")),str(scene.get("model",{}).get("source",""))])
	var seen: Dictionary={}
	for source in sources:
		if str(source).is_empty():continue
		var absolute:=ProjectSettings.globalize_path(source).replace("\\","/")
		if seen.has(absolute):continue
		seen[absolute]=true
		var digest:=FileAccess.get_sha256(absolute);var original: String=origins.get(absolute,absolute)
		result["assets/"+digest+"."+absolute.get_extension().to_lower()]=original if FileAccess.file_exists(original) and FileAccess.get_sha256(original)==digest else absolute
	return result
func publish(path: String,packet: Dictionary) -> String:
	var why:=Storage.write_path_error(path.get_base_dir(),path.get_file())
	if not why.is_empty():return why
	if FileAccess.file_exists(path):return "Project snapshot status already exists."
	var temporary:=Storage.fresh_temporary(path,".tmp")
	if temporary.is_empty():return "Cannot create project snapshot status."
	var file:=FileAccess.open(temporary,FileAccess.WRITE)
	if file==null:return "Cannot write project snapshot status."
	var serialized:=JSON.stringify(packet,"",true,true);file.store_string(serialized);file.flush();var code:=file.get_error();file.close()
	if code!=OK or FileAccess.get_file_as_string(temporary)!=serialized:return "Cannot verify project snapshot status."
	return "" if DirAccess.rename_absolute(temporary,path)==OK else "Cannot publish project snapshot status."
func _run(project: Dictionary,request: Dictionary) -> Dictionary:
	var began:=Time.get_ticks_usec();var adopted:=Frozen.adopt(project)
	var why: String=adopted.error if adopted.has("error") else persist(adopted.project,request)
	var links: Dictionary={}
	if why.is_empty() and FileAccess.file_exists(request.cancel):why="Project saving cancelled. Previous save preserved."
	if why.is_empty():links=references(adopted.project,request.get("origins",{}))
	var status:={"format":FORMAT,"ok":why.is_empty(),"error":why,"references":links}
	var published:=publish(request.ready,status)
	if not published.is_empty():why=published
	return {"error":why,"capture_ms":request.capture_ms,"worker_ms":(Time.get_ticks_usec()-began)/1000.,"background_thread":not Thread.is_main_thread()}
