extends Node
# Isolated CPU-fixture bridge. No model import, app edit or native PID kill.
signal received(value: Dictionary)
signal failed(reason: String)
signal ended(code: int)
const COMMAND="has_wind_preview_controller_command_1"
const EVENT="has_wind_preview_controller_event_1"
const MAX_SEND=2048
const MAX_EVENT=16384
var stdio: FileAccess
var stderr: FileAccess
var pid:=-1
var config: Dictionary={}
var buffer:=PackedByteArray()
var diagnostic:=PackedByteArray()
var seq:=0
var outstanding:=false
var controller_ready:=false
var stopped:=false
var ticket: Dictionary={"generation":0,"nonce":null}
var controller_owner: Dictionary={}
var _owned_pid:=-1
var _map_reserved:=false
var release_calls:=0
var release_result:=OK
var cached_exit:=-1
var _used:=false
var closing:=false
var pending_op:=""
var pending_generation:=0
var worker_owner: Dictionary={}
var job:=""
var request_sha:=""
var prepared_completion: Dictionary={}
var deadline:=0

func launch(value: Dictionary) -> String:
	if OS.get_name()!="Windows":return "Pinned Windows bridge only"
	if str(Engine.get_version_info().get("hash",""))!="89cea143987d564363e15d207438530651d943ac":return "Pinned Godot process-map contract required"
	if _used:return "Bridge is single-use"
	_used=true
	config=value.duplicate(true)
	if int(config.host.pid)!=OS.get_process_id():return "Fixture host identity differs"
	if not FileAccess.file_exists(str(config.python)) or not FileAccess.file_exists(str(config.controller)):return "Approved runtime/source fingerprint differs"
	if FileAccess.get_sha256(str(config.python))!=str(config.python_sha256) or FileAccess.get_sha256(str(config.controller))!=str(config.controller_sha256):return "Approved runtime/source fingerprint differs"
	if FileAccess.get_sha256(str(config.launcher))!=str(config.launcher_sha256):return "Fixture launcher fingerprint differs"
	var args:=PackedStringArray(["-I","-B","-u",str(config.launcher),"--main-root",str(config.main_root),"--owned-root",str(config.owned_root),"--parent-pid",str(int(config.host.pid)),"--parent-created-100ns",str(config.host.created_100ns),"--session",str(config.session),"--controller-sha256",str(config.controller_sha256),"--python-sha256",str(config.python_sha256),"--idle-timeout","15","--watchdog-grace","0.75"])
	var child:=OS.execute_with_pipe(str(config.python),args,false)
	if child.is_empty():return "Controller did not start"
	pid=int(child.pid);stdio=child.stdio;stderr=child.stderr
	# Pinned Windows execute_with_pipe inserted exactly this retained map entry.
	# No other owner may call OS.kill for it. Consume once before cleanup call.
	_owned_pid=pid;_map_reserved=true
	deadline=Time.get_ticks_msec()+5000
	return ""

func send(op: String,fields: Dictionary={}) -> String:
	if stopped or not controller_ready or stdio==null:return "Bridge is not ready"
	if outstanding:return "One command is already outstanding"
	for key in fields:
		if key in ["format","session","seq","op","generation","nonce"]:return "Reserved controller envelope field"
	var message: Dictionary={"format":COMMAND,"session":config.session,"seq":seq+1,"op":op,"generation":int(ticket.generation),"nonce":ticket.nonce}
	var normalized:=fields.duplicate(true)
	if op=="start":
		if not normalized.get("items") is Array:return "Missing reviewed items"
		for item in normalized.items:
			if not item is Dictionary:return "Invalid reviewed item"
			for key in ["node","primitive","component","anchor_node","segments"]:
				if item.has(key):
					var number:=whole(item[key])
					if number<0:return "Nonintegral helper selector"
					item[key]=number
			if item.has("vertex_mask"):
				if not item.vertex_mask is Array:return "Invalid vertex mask"
				for index in item.vertex_mask.size():
					var number:=whole(item.vertex_mask[index])
					if number<0:return "Nonintegral vertex selector"
					item.vertex_mask[index]=number
	message.merge(normalized,true)
	var json:=JSON.stringify(message)
	var ascii:=""
	for index in json.length():
		var code:=json.unicode_at(index)
		if code<=127:ascii+=String.chr(code)
		elif code<=65535:ascii+="\\u%04x" % code
		else:ascii+="\\u%04x\\u%04x" % [55296+((code-65536)>>10),56320+((code-65536)&1023)]
	var raw: PackedByteArray=(ascii+"\n").to_ascii_buffer()
	if raw.size()>MAX_SEND:return "Fixture command exceeds2048bytes"
	# A failed/short write may have sent a prefix. Never retry the full frame.
	if not stdio.store_buffer(raw) or stdio.get_error()!=OK:
		close_transport();return "Controller command write failed"
	seq+=1;outstanding=true;pending_op=op;pending_generation=int(ticket.generation)
	deadline=Time.get_ticks_msec()+5000
	if op=="close":closing=true;controller_ready=false
	return ""

func _process(_delta: float) -> void:
	if stopped or stdio==null:return
	if deadline>0 and Time.get_ticks_msec()>deadline:fail("Controller response timed out");return
	if observe_exit():return
	for stream_index in range(2):
		if observe_exit():return
		var stream: FileAccess=stdio if stream_index==0 else stderr
		if stream==null:continue
		var available:=mini(int(stream.get_length()),4096)
		if available<=0:continue
		var chunk:=stream.get_buffer(available)
		if stream_index==1:
			diagnostic.append_array(chunk)
			if diagnostic.size()>MAX_EVENT:fail("Controller diagnostics exceeded cap");return
			if not chunk.is_empty():fail("Controller reported startup/transport diagnostic");return
		else:
			buffer.append_array(chunk)
			if buffer.size()>MAX_EVENT:fail("Controller frame exceeded cap");return
			while buffer.has(10):
				var end:=buffer.find(10)
				var raw:=buffer.slice(0,end);buffer=buffer.slice(end+1)
				if not admit(raw):return
	observe_exit()

func observe_exit() -> bool:
	if pid<=0 or OS.is_process_running(pid):return false
	var code:=OS.get_process_exit_code(pid)
	if closing and code==0:
		close_transport();ended.emit(code)
	else:fail("Controller ended with exit "+str(code))
	return true

func admit(raw: PackedByteArray) -> bool:
	if stopped:return false
	for byte in raw:
		if byte>127:fail("NonASCII controller event");return false
	var value=JSON.parse_string(raw.get_string_from_ascii())
	if not value is Dictionary or value.get("format")!=EVENT or value.get("session")!=config.session:
		fail("Foreign or malformed controller event");return false
	if not value.get("ticket") is Dictionary or not value.ticket.has("generation") or not value.ticket.has("nonce"):
		fail("Missing controller draft ticket");return false
	if whole(value.ticket.generation)<0 or whole(value.get("seq",-1))<0:
		fail("Nonintegral controller identity");return false
	var kind:=str(value.get("event",""))
	if kind=="ready":
		if not value.get("controller") is Dictionary or not value.get("host") is Dictionary or not value.get("python") is Dictionary or not value.get("source_sha256") is Dictionary:
			fail("Incomplete controller ready identity");return false
		if controller_ready or seq!=0 or whole(value.get("seq",-1))!=0 or whole(value.controller.get("pid",-1))!=pid or value.host!=config.host or value.python.get("sha256")!=config.python_sha256 or value.source_sha256.get("controller")!=config.controller_sha256 or whole(value.ticket.generation)!=0 or value.ticket.nonce!=null:
			fail("Controller ready identity differs");return false
		controller_owner=value.controller.duplicate(true);controller_ready=true
	else:
		if not kind in ["started","running","prepared","refused","invalidated","cancelled","closed"]:
			fail("Unknown controller event");return false
		if not outstanding or int(value.get("seq",-1))!=seq:
			fail("Stale or unsolicited controller event");return false
		var generation:=whole(value.ticket.generation)
		var phase:=str(value.get("phase",""))
		if generation<pending_generation or not phase in ["stopped","building","prepared_hidden"] or (phase=="stopped" and value.ticket.nonce!=null) or (phase!="stopped" and not hex_text(value.ticket.nonce,32)):
			fail("Invalid controller ticket transition");return false
		if kind=="started":
			if pending_op!="start" or generation!=pending_generation+1 or phase!="building" or not value.get("owner") is Dictionary or not hex_text(value.get("request_file_sha256"),64):
				fail("Started event differs from pending request");return false
			var owner: Dictionary=value.owner
			var path:=str(value.get("job","")).replace("\\","/").simplify_path()
			var boundary:=str(config.owned_root).replace("\\","/").simplify_path()+"/"
			if whole(owner.get("pid",-1))<=0 or not str(owner.get("created_100ns","")).is_valid_int() or whole(owner.get("generation",-1))!=generation or owner.get("nonce")!=value.ticket.nonce or not path.begins_with(boundary):
				fail("Started worker ownership/path differs");return false
			worker_owner=owner.duplicate(true);job=str(value.job);request_sha=str(value.request_file_sha256);prepared_completion={}
		elif kind in ["running","prepared"]:
			if pending_op!="poll" or generation!=pending_generation or value.ticket.nonce!=ticket.nonce:
				fail("Poll event differs from pending ticket");return false
			if kind=="running":
				if phase!="building" or value.get("owner")!=worker_owner:fail("Running worker identity differs");return false
			else:
				var completion=value.get("completion")
				if phase!="prepared_hidden" or str(value.get("job",""))!=job or not completion is Dictionary:
					fail("Prepared candidate identity is incomplete");return false
				if completion.get("format")!="has_wind_helper_preview_1" or whole(completion.get("generation",-1))!=generation or completion.get("nonce")!=ticket.nonce or completion.get("request_file_sha256")!=request_sha or not hex_text(completion.get("receipt_sha256"),64):
					fail("Prepared completion differs from request");return false
				if prepared_completion.is_empty():
					if value.get("job_closed")!=true or value.get("process_handle_closed")!=true or value.get("owner")!=worker_owner:
						fail("Prepared worker cleanup is not confirmed");return false
				elif completion!=prepared_completion:fail("Prepared completion changed");return false
				prepared_completion=completion.duplicate(true)
		elif kind in ["cancelled","closed","invalidated"]:
			if phase!="stopped" or (generation<=pending_generation and not (kind=="closed" and ticket.nonce==null)) or (kind=="cancelled" and pending_op!="cancel") or (kind=="closed" and pending_op!="close"):
				fail("Stopped event differs from pending request");return false
		outstanding=false
	ticket=value.ticket.duplicate(true)
	deadline=0
	if kind=="closed":closing=true;controller_ready=false
	received.emit(value)
	return true

func whole(value) -> int:
	if not (value is int or value is float):return -1
	var number:=float(value)
	return int(number) if is_finite(number) and number>=0 and number<2147483648 and floor(number)==number else -1

func hex_text(value,length: int) -> bool:
	if not value is String or value.length()!=length:return false
	for index in value.length():
		if not value[index] in "0123456789abcdef":return false
	return true

func fail(reason: String) -> void:
	close_transport();failed.emit(reason)

func close_pipes() -> void:
	stopped=true;controller_ready=false;outstanding=false
	if stdio!=null:stdio.close()
	if stderr!=null:stderr.close()
	stdio=null;stderr=null;buffer.clear();diagnostic.clear()

func release_owned_process() -> Dictionary:
	if not _map_reserved:return {"attempted":false,"release_calls":release_calls,"result":release_result,"cached_exit":cached_exit}
	if stdio!=null or stderr!=null:return {"attempted":false,"error":"Close pipes first","release_calls":release_calls}
	# Under this exclusive successful-launch invariant, exactGodot4.6 kill uses
	# process_map's retained HANDLE, removes entry and closes both native handles.
	# Never retry even FAILED: a second call could reach its generic PID fallback.
	_map_reserved=false
	var owned:=_owned_pid;_owned_pid=-1
	cached_exit=OS.get_process_exit_code(owned) if not OS.is_process_running(owned) else -1
	release_calls+=1
	release_result=OS.kill(owned)
	pid=-1
	return {"attempted":true,"release_calls":release_calls,"result":release_result,"cached_exit":cached_exit}

func close_transport() -> void:
	close_pipes();release_owned_process()

func _exit_tree() -> void:
	close_transport()
