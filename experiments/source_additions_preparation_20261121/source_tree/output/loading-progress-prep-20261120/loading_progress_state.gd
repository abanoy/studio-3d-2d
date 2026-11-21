extends RefCounted
# Authored/unrun operation state; UI never decides whether a result may install.
const FORMAT := "has_loading_progress_1"
const MAX_COUNT := 1000000000000
var token := ""
var busy := false
var cancelling := false
var sequence := -1
var phase := ""
var label := ""
var completed: Variant = null
var total: Variant = null
var unit := ""
var terminal := "idle"
var _seen: Dictionary = {}
var _operations: Dictionary = {}

static func identifier(value: Variant,limit: int=96) -> bool:
	if not value is String or value.is_empty() or value.length()>limit:return false
	for c in value:
		if not c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-":return false
	return true
static func whole(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(float(value)) and value>=0 and value<=MAX_COUNT
static func text(value: Variant) -> bool:
	if not value is String or value.is_empty() or value.length()>200:return false
	for i in range(value.length()):
		if value.unicode_at(i)<32:return false
	return true
func begin(operation: String,title: String) -> bool:
	if busy or not identifier(operation) or not text(title) or _operations.has(operation) or _operations.size()>=4096:return false
	_operations[operation]=true
	token=operation;busy=true;cancelling=false;sequence=-1;phase="";label=title;completed=null;total=null;unit="";terminal="running";_seen.clear()
	return true
func update(value: Variant) -> bool:
	if not busy or not value is Dictionary or value.size()!=8:return false
	for key in ["format","token","sequence","phase","label","completed","total","unit"]:
		if not value.has(key):return false
	if value.format!=FORMAT or value.token!=token or not whole(value.sequence) or int(value.sequence)<=sequence or not identifier(value.phase,48) or not text(value.label):return false
	var known: bool = value.total!=null
	if known:
		if not whole(value.total) or value.total<=0 or not whole(value.completed) or value.completed>value.total or not value.unit in ["bytes","items","steps"]:return false
	elif value.completed!=null or value.unit!="":return false
	if value.phase==phase:
		if total!=null and (not known or value.total!=total or value.unit!=unit or value.completed<completed):return false
	elif _seen.has(value.phase) or _seen.size()>=64:return false
	sequence=int(value.sequence);phase=value.phase;label=value.label;completed=int(value.completed) if known else null;total=int(value.total) if known else null;unit=value.unit;_seen[phase]=true
	return true
func request_cancel(operation: String) -> bool:
	if not busy or token!=operation or cancelling:return false
	cancelling=true;terminal="cancelling";return true
func finish(operation: String,success: bool) -> bool:
	if not busy or operation!=token:return false
	busy=false;terminal="cancelled" if cancelling else "succeeded" if success else "failed"
	return true
func snapshot() -> Dictionary:
	return {"token":token,"busy":busy,"cancelling":cancelling,"sequence":sequence,"phase":phase,"label":label,"completed":completed,"total":total,"unit":unit,"terminal":terminal}
