extends RefCounted
const Drawing=preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
const Journal=preload("res://src/recovery_journal.gd")
const BlobRetention=preload("res://src/recovery_blob_retention.gd")
const MAX_BYTES := 512 * 1024 * 1024
static var discovery_warning := ""
static var own_record_cache:={}

static func valid_creation(value) -> bool:
	if not value is String or value.is_empty() or value.length()>20 or value.begins_with("0"):return false
	for character in value:
		if not character in "0123456789":return false
	return value.length()<20 or value<="18446744073709551615"

static func valid_linux_start(value) -> bool:
	if not value is String:return false
	var parts: PackedStringArray=value.split(":")
	if parts.size()!=2 or parts[0].length()!=36 or not valid_creation(parts[1]):return false
	for i in 36:
		if i in [8,13,18,23]:
			if parts[0][i]!="-":return false
		elif not parts[0][i] in "0123456789abcdef":return false
	return true

static func probe_processes(pids: Array) -> Dictionary:
	var states:={};var created:={};var linux_start:={}
	var args:=PackedStringArray([ProjectSettings.globalize_path("res://tools/recovery_processes.py")])
	for pid in pids:
		if not Storage.integer(pid,1,2147483647):continue
		var key:=str(int(pid))
		if states.has(key):continue
		states[key]="unknown"
		if args.size()<=1024:args.append(key)
	if args.size()==1:return {"owners":states,"created_100ns":created,"linux_start":linux_start}
	var python:=OS.get_environment("HYBRID_PYTHON");var output: Array=[]
	var code:=OS.execute(python if not python.is_empty() else "python",args,output,false,false)
	if code==0 and not output.is_empty():
		var parser:=JSON.new()
		if parser.parse(str(output[0]))==OK and parser.data is Dictionary:
			var data: Dictionary=parser.data
			if data.get("format") in ["studio_process_liveness_1","studio_process_liveness_2"] and data.get("owners") is Dictionary:
				for pid in states:
					if data.owners.get(pid) in ["alive","exited"]:states[pid]=data.owners[pid]
					if data.get("created_100ns") is Dictionary and valid_creation(data.created_100ns.get(pid)):created[pid]=data.created_100ns[pid]
					if data.get("format")=="studio_process_liveness_2" and data.get("linux_start") is Dictionary and valid_linux_start(data.linux_start.get(pid)):linux_start[pid]=data.linux_start[pid]
	return {"owners":states,"created_100ns":created,"linux_start":linux_start}

static func owner_record() -> Dictionary:
	var pid:=OS.get_process_id()
	if own_record_cache.get("pid")!=pid:
		own_record_cache={"pid":pid}
		var info:=probe_processes([pid]);var key:=str(pid)
		if info.owners.get(key)=="alive" and valid_creation(info.created_100ns.get(key)):own_record_cache["created_100ns"]=info.created_100ns[key]
		if info.owners.get(key)=="alive" and valid_linux_start(info.linux_start.get(key)):own_record_cache["linux_start"]=info.linux_start[key]
	return own_record_cache.duplicate()

static func process_info(pids: Array) -> Dictionary:
	var foreign: Array=[];var mine:=str(OS.get_process_id())
	for pid in pids:
		if Storage.integer(pid,1,2147483647) and int(pid)!=OS.get_process_id():foreign.append(int(pid))
	var info:=probe_processes(foreign);info.owners[mine]="alive"
	if OS.get_process_id() in pids:
		var own:=owner_record()
		if valid_creation(own.get("created_100ns")):info.created_100ns[mine]=own.created_100ns
		if valid_linux_start(own.get("linux_start")):info.linux_start[mine]=own.linux_start
	return info

static func process_status(pids: Array) -> Dictionary:
	var states: Dictionary=process_info(pids).owners
	for pid in states:
		if states[pid]=="unknown":discovery_warning="Some recovery sessions could not be checked for a live owner and were left untouched. Check the configured Python installation or use Open saved backup.";break
	return states

static func owner_available(owner: Dictionary,info: Dictionary,include_current := false) -> bool:
	if not Storage.integer(owner.get("pid"),1,2147483647):
		discovery_warning="Some recovery sessions have invalid owner records and were left untouched. Use Open saved backup to inspect them.";return false
	if owner.has("created_100ns") and not valid_creation(owner.created_100ns):
		discovery_warning="Some recovery sessions have invalid owner identities and were left untouched. Use Open saved backup to inspect them.";return false
	if owner.has("linux_start") and (not valid_linux_start(owner.linux_start) or owner.has("created_100ns")):
		discovery_warning="Some recovery sessions have invalid owner identities and were left untouched. Use Open saved backup to inspect them.";return false
	var pid:=str(int(owner.pid));var state: String=info.get("owners",{}).get(pid,"unknown")
	if state=="exited":return true
	if state=="alive":
		if owner.has("linux_start"):
			var current=info.get("linux_start",{}).get(pid)
			if not valid_linux_start(current):
				discovery_warning="Some recovery owners could not be identified and were left untouched. Use Open saved backup to inspect them.";return false
			if current!=owner.linux_start:return true
		if owner.has("created_100ns"):
			var current=info.get("created_100ns",{}).get(pid)
			if not valid_creation(current):
				discovery_warning="Some recovery owners could not be identified and were left untouched. Use Open saved backup to inspect them.";return false
			if current!=owner.created_100ns:return true
		return include_current and int(owner.pid)==OS.get_process_id()
	discovery_warning="Some recovery sessions could not be checked for a live owner and were left untouched. Check the configured Python installation or use Open saved backup.";return false

static func read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 1024 * 1024: return {}
	var parser := JSON.new()
	if parser.parse(file.get_as_text()) != OK: return {}
	var parsed = parser.data
	return parsed if parsed is Dictionary else {}

static func write_json(path: String, data: Dictionary,owned_root: String="") -> String:
	return preload("res://src/atomic_metadata.gd").write_bytes(path,JSON.stringify(data).to_utf8_buffer(),path.get_base_dir() if owned_root.is_empty() else owned_root)

static func bytes_in(folder: String, depth := 0) -> int:
	if not DirAccess.dir_exists_absolute(folder): return 0
	if depth > 4: return MAX_BYTES
	var size := 0
	for name in DirAccess.get_files_at(folder):
		var file := FileAccess.open(folder.path_join(name), FileAccess.READ)
		if file: size += file.get_length()
		if size >= MAX_BYTES: return size
	for name in DirAccess.get_directories_at(folder):
		size += bytes_in(folder.path_join(name), depth + 1)
		if size >= MAX_BYTES: break
	return size

static func drawing_reserve(layers: Array,sequence_graph: Dictionary={}) -> int:
	var bytes:=0
	for layer in layers:
		for cel in layer.cels:bytes+=Drawing.raster_bytes(cel,true)
	for asset in sequence_graph.get("assets",[]):
		for layer in asset.scene.layers:
			for cel in layer.cels:bytes+=Drawing.raster_bytes(cel,true)
	return bytes

# Only used when decoded reservation would refuse. Measure one encoded image at a
# time; never substitute snapshot compression size for persisted PNG bytes.
static func encoded_drawing_reserve(layers: Array,sequence_graph: Dictionary,budget: int) -> Dictionary:
	var tracks: Array=layers.duplicate()
	for asset in sequence_graph.get("assets",[]):tracks.append_array(asset.scene.layers)
	var total:=0
	for layer in tracks:
		for cel in layer.cels:
			var read:=Drawing.read_image(cel)
			if read.has("error"):return read
			var image: Image=read.image
			var encoded: PackedByteArray=image.save_png_to_buffer()
			if encoded.is_empty():return {"error":"Cannot measure recovery drawing PNG. Previous checkpoint preserved."}
			total+=encoded.size()
			if total>budget:return {"error":"Recovery cache budget reached (512 MiB). Save manually; review output/recovery before removing old copies."}
	return {"bytes":total}

static func checkpoint(root: String, session: String, video: Dictionary, keys: Array, layers: Array, source: String, frame: int, audio: Dictionary, origin: String, revision: int, model: Dictionary = {}, world: Dictionary = {},palette: Array=[],sequence_graph: Dictionary={},sequence_context: Dictionary={},reference_sheet: Dictionary={},lesson_context: Dictionary={}) -> String:
	if JSON.stringify(lesson_context,"",true,true).to_utf8_buffer().size()>16384:return "Lesson recovery context exceeds16KiB. Previous checkpoint preserved."
	# Prefer the cheap conservative reserve; large cold projects use actual PNG
	# sizes before any checkpoint writes, bounded one encoded drawing at a time.
	var raster_estimate:=drawing_reserve(layers,sequence_graph)
	var estimate := 6 * 1024 * 1024 + raster_estimate
	var sources: Array=[]
	if not reference_sheet.is_empty():sources.append(reference_sheet.get("source",""))
	for asset in sequence_graph.get("assets",[]):
		for clip in preload("res://src/audio_track.gd").clips(asset.scene.get("audio",{})):sources.append(clip.source.path)
		for row in preload("res://src/world_document.gd").assets(asset.scene.world):sources.append(row.source)
	for clip in preload("res://src/audio_track.gd").clips(audio): sources.append(clip.source.path)
	if not world.is_empty():
		for row in preload("res://src/world_document.gd").assets(world):sources.append(row.source)
	else:sources.append_array([source,model.source if not model.is_empty() else ""])
	var counted:={}
	for path in sources:
		if counted.has(path):continue
		counted[path]=true
		if not path.is_empty():
			var file := FileAccess.open(path, FileAccess.READ)
			if file: estimate += file.get_length()
	var occupied:=bytes_in(root)
	if occupied + estimate > MAX_BYTES:
		var fixed:=occupied+estimate-raster_estimate
		if fixed>=MAX_BYTES:return "Recovery cache budget reached (512 MiB). Save manually; review output/recovery before removing old copies."
		var encoded:=encoded_drawing_reserve(layers,sequence_graph,MAX_BYTES-fixed)
		if encoded.has("error"):return encoded.error
	if not Storage.safe_relative(session) or session.contains("/"):return "Invalid recovery session address."
	var folder := root.path_join(session)
	var path_error:=preload("res://src/atomic_metadata.gd").path_error(folder.path_join("session.json"),root)
	if not path_error.is_empty():return path_error
	if DirAccess.make_dir_recursive_absolute(folder) != OK: return "Cannot create recovery directory."
	var retained_before:=BlobRetention.inventory(folder)
	var error := write_json(folder.path_join("session.json"), owner_record(),root)
	if not error.is_empty(): return error
	# Adopt both old generations before the normal writer rotates either away.
	error=Journal.record(folder)
	if not error.is_empty():return error
	var recovery:={"origin":origin,"revision":revision,"saved_at":Time.get_unix_time_from_system()}
	if not lesson_context.is_empty():recovery["lesson"]=lesson_context.duplicate(true)
	error=Storage.save_project(folder, video, keys, layers, source, frame, audio,
		recovery, model,false,world,{"sequence_editor":sequence_context} if not sequence_context.is_empty() else {},palette,sequence_graph,null,reference_sheet)
	if not error.is_empty():return error
	error=Journal.record(folder)
	if error.is_empty():BlobRetention.retire(folder,retained_before)
	return error

static func resolve(folder: String) -> String:
	var primary := folder.path_join("project.json")
	if not FileAccess.file_exists(primary) and not FileAccess.file_exists(folder.path_join("project.backup.json")): return ""
	return write_json(folder.path_join("resolved.json"), {"sha256": FileAccess.get_sha256(primary) if FileAccess.file_exists(primary) else "missing"},folder.get_base_dir())

static func candidates(root: String, exclude := "", include_current := false,include_resolved := false) -> Array:
	discovery_warning=""
	var found: Array = []
	if not DirAccess.dir_exists_absolute(root): return found
	var sessions:={};var pids: Array=[]
	for session in DirAccess.get_directories_at(root):
		if session==exclude:continue
		var owner:=read_json(root.path_join(session).path_join("session.json"))
		sessions[session]=owner
		if Storage.integer(owner.get("pid"),1,2147483647) and not int(owner.pid) in pids:pids.append(int(owner.pid))
	var owners:=process_info(pids)
	for session in sessions:
		if session == exclude: continue
		var folder := root.path_join(session)
		var owner: Dictionary=sessions[session]
		if FileAccess.file_exists(folder.path_join("session.json")) and not owner_available(owner,owners,include_current):continue
		var primary := folder.path_join("project.json")
		var resolved := read_json(folder.path_join("resolved.json"))
		var fingerprint := FileAccess.get_sha256(primary) if FileAccess.file_exists(primary) else "missing"
		var resolved_session: bool=resolved.get("sha256","none")==fingerprint
		if resolved_session and not include_resolved:continue
		var manifests: Array=["project.json","project.backup.json"];var previews:={};var seen:={}
		for entry in Journal.entries(folder):
			manifests.append(Journal.manifest_name(entry.sha256));previews[entry.sha256]=entry.get("preview","")
		for manifest in manifests:
			if Journal.is_manifest(manifest) and not Journal.valid_manifest(folder,manifest):continue
			var data := read_json(folder.path_join(manifest))
			var editor = data.get("editor", {})
			var info = editor.get("recovery", {}) if editor is Dictionary else {}
			if info is Dictionary and info.get("origin") is String and Storage.integer(info.get("revision"), 0, 2147483647) and (info.get("saved_at") is float or info.get("saved_at") is int) and is_finite(float(info.saved_at)) and info.saved_at>=0:
				var digest:=FileAccess.get_sha256(folder.path_join(manifest))
				if seen.has(digest):continue
				seen[digest]=true
				found.append({"folder":folder,"manifest":manifest,"origin":info.origin,"saved_at":info.saved_at,"revision":int(info.revision),"frame":int(editor.get("frame",0)),"preview":previews.get(digest,""),"sha256":digest,"resolved":resolved_session})
	found.sort_custom(func(a,b):
		if a.saved_at!=b.saved_at:return a.saved_at>b.saved_at
		if a.folder!=b.folder:return a.folder>b.folder
		if a.get("revision",0)!=b.get("revision",0):return a.get("revision",0)>b.get("revision",0)
		return a.manifest=="project.json" and b.manifest!="project.json")
	return found
