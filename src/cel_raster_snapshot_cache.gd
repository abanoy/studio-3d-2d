extends RefCounted
# Document-owned decoded cache; no global cache or disk dependency.
# Callers receive separate editable resources, never the cache's own Image.
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const DEFAULT_BUDGET=2*1920*1080*4
var budget: int
var retained_bytes:=0
var decodes:=0
var hits:=0
var _entries: Array=[]
var owners: Array[WeakRef]=[]
func _init(bytes: int=DEFAULT_BUDGET) -> void:budget=clampi(bytes,0,DEFAULT_BUDGET)
func register(owner: RefCounted) -> void:
	var reference: WeakRef=weakref(owner);owners.append(reference)
func clear() -> void:_entries=[];retained_bytes=0
func read(snapshot) -> Dictionary:
	if not snapshot is Snapshot:return {"error":"Missing cold drawing snapshot."}
	var why: String=snapshot.verify()
	if not why.is_empty():return {"error":why}
	for i in range(_entries.size()-1,-1,-1):
		var row: Dictionary=_entries[i];var source=row.source.get_ref()
		if source==null:retained_bytes-=row.bytes;_entries.remove_at(i)
		elif is_same(source,snapshot):
			_entries.remove_at(i);_entries.append(row);hits+=1
			return {"image":row.image.duplicate()}
	var result: Dictionary=snapshot.materialize()
	if result.has("error"):return result
	decodes+=1;var bytes: int=result.image.get_data_size()
	if bytes>budget:return result
	while retained_bytes+bytes>budget and not _entries.is_empty():retained_bytes-=int(_entries.pop_front().bytes)
	_entries.append({"source":weakref(snapshot),"image":result.image,"bytes":bytes});retained_bytes+=bytes
	return {"image":result.image.duplicate()}
