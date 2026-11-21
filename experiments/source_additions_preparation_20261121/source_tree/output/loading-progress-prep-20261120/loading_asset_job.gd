extends RefCounted
# UNRUN worker candidate. No SceneTree/UI installation occurs off the main thread.
const Decoder=preload("res://src/loading_scene_bytes.gd")
const State=preload("res://src/loading_progress_state.gd")
const MAX_BYTES=128*1024*1024
const CHUNK=1024*1024
var thread: Thread
var _mutex:=Mutex.new()
var _cancelled:=false
var _packet: Dictionary={}
var _sequence:=0
var _token:=""

static func sha(value: String) -> bool:
	if value.length()!=64:return false
	for c in value:
		if not c in "0123456789abcdef":return false
	return true
func busy() -> bool:return thread!=null and thread.is_started()
func start(path: String,expected_sha: String,operation: String) -> String:
	if busy():return "An asset is already being prepared."
	if path.get_extension().to_lower()!="glb" or not expected_sha.is_empty() and not sha(expected_sha) or not State.identifier(operation):return "Invalid asset loading request."
	_cancelled=false;_packet={};_sequence=0;_token=operation
	publish("opening","Opening the model file",null,null,"")
	thread=Thread.new()
	var why: Error=thread.start(_run.bind(path,expected_sha,operation),Thread.PRIORITY_LOW)
	if why!=OK:thread=null;return "Cannot start asset preparation."
	return ""
func publish(phase: String,label: String,done: Variant,total: Variant,unit: String) -> void:
	_mutex.lock()
	_sequence+=1
	_packet={"format":State.FORMAT,"token":_token,"sequence":_sequence,"phase":phase,"label":label,"completed":done,"total":total,"unit":unit}
	_mutex.unlock()
func progress() -> Dictionary:
	_mutex.lock();var result: Dictionary=_packet.duplicate(true);_mutex.unlock();return result
func request_cancel() -> void:
	_mutex.lock();_cancelled=true;_mutex.unlock()
func cancelled() -> bool:
	_mutex.lock();var value: bool=_cancelled;_mutex.unlock();return value
func poll() -> Dictionary:
	if not busy() or thread.is_alive():return {}
	return finish()
func finish() -> Dictionary:
	if not busy():return {}
	var result: Dictionary=thread.wait_to_finish();thread=null
	# Only the main-thread owner may take or dispose newly staged scene nodes.
	if cancelled():
		if result.get("scene") is Node and is_instance_valid(result.scene):result.scene.free()
		return {"token":_token,"error":"Model loading cancelled. Current scene preserved."}
	return result
func dispose() -> void:
	request_cancel()
	var result: Dictionary=finish()
	if result.get("scene") is Node and is_instance_valid(result.scene):result.scene.free()
func _run(path: String,expected_sha: String,operation: String) -> Dictionary:
	var result: Dictionary={"token":operation}
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()<20 or file.get_length()>MAX_BYTES:
		result.error="Cannot read GLB or its size is outside the128MiB limit.";return result
	var total: int=file.get_length()
	var bytes:=PackedByteArray()
	publish("reading","Reading model data",0,total,"bytes")
	while bytes.size()<total:
		if cancelled():file.close();result.error="Model loading cancelled.";return result
		var part: PackedByteArray=file.get_buffer(mini(CHUNK,total-bytes.size()))
		if part.is_empty():file.close();result.error="Model data ended before its recorded length.";return result
		bytes.append_array(part)
		publish("reading","Reading model data",bytes.size(),total,"bytes")
	if file.get_position()!=total or file.get_length()!=total:file.close();result.error="Model data changed during reading.";return result
	file.close()
	publish("checking","Checking the model data",null,null,"")
	var hasher:=HashingContext.new()
	if hasher.start(HashingContext.HASH_SHA256)!=OK or hasher.update(bytes)!=OK:result.error="Cannot verify the model fingerprint.";return result
	var digest: String=hasher.finish().hex_encode()
	if not expected_sha.is_empty() and digest!=expected_sha:result.error="Model data differs from its expected fingerprint.";return result
	if cancelled():result.error="Model loading cancelled.";return result
	# Native GLTF stages cannot be interrupted safely. UI remains on the main thread
	# and shows an indeterminate phase; Cancel is observed before handoff.
	publish("decoding","Preparing meshes, textures and joints",null,null,"")
	var decoded: Dictionary=Decoder.from_bytes(bytes)
	if decoded.has("error"):result.error=decoded.error;return result
	result.merge(decoded,true);result.path=path;result.sha256=digest
	publish("ready","Model data is ready to add",1,1,"items")
	return result
