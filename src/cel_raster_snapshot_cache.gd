extends RefCounted
# Document-owned decoded cache; no global cache or disk dependency.
# Callers receive separate editable resources, never the cache's own Image.
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const DEFAULT_BUDGET=2*1920*1080*4
const DEFAULT_OWNER_LIMIT=320*1024*1024
var budget: int
var owner_limit: int
var retained_bytes:=0
var decodes:=0
var hits:=0
var _entries: Array=[]
var owners: Array[WeakRef]=[]
func _init(bytes: int=DEFAULT_BUDGET,owned_bytes: int=DEFAULT_OWNER_LIMIT) -> void:
	budget=clampi(bytes,0,DEFAULT_BUDGET);owner_limit=clampi(owned_bytes,0,DEFAULT_OWNER_LIMIT)
func live_owners() -> Array:
	var result: Array=[];var seen:={}
	for i in range(owners.size()-1,-1,-1):
		var owner=owners[i].get_ref()
		if owner==null:owners.remove_at(i)
		elif owner.get_script()==load("res://src/cel_raster_owner.gd") and not seen.has(owner.get_instance_id()):seen[owner.get_instance_id()]=true;result.append(owner)
	return result
func owned_bytes() -> int:
	var total:=0;var cold:={}
	for owner in live_owners():
		if owner.is_pinned():total+=owner.retained_bytes()
		elif owner._cold!=null and not cold.has(owner._cold.get_instance_id()):cold[owner._cold.get_instance_id()]=true;total+=owner.retained_bytes()
	return total
func snapshot_cost(snapshot) -> int:
	for owner in live_owners():
		if not owner.is_pinned() and is_same(owner._cold,snapshot):return 0
	return snapshot.storage_bytes()
func enforce(extra: int=0) -> void:
	var owned:=owned_bytes()
	while owned+retained_bytes+extra>owner_limit and not _entries.is_empty():retained_bytes-=int(_entries.pop_front().bytes)
func admit(extra: int) -> String:
	if extra<0 or owned_bytes()+extra>owner_limit:return "Drawing memory budget reached. Wait for inactive artwork to cool, or save and reopen the project to release older Undo drawings."
	enforce(extra);return ""
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
	if bytes>budget or owned_bytes()+bytes>owner_limit:return result
	while (retained_bytes+bytes>budget or owned_bytes()+retained_bytes+bytes>owner_limit) and not _entries.is_empty():retained_bytes-=int(_entries.pop_front().bytes)
	_entries.append({"source":weakref(snapshot),"image":result.image,"bytes":bytes});retained_bytes+=bytes
	return {"image":result.image.duplicate()}
