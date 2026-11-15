extends RefCounted
# Only retire blobs PROVEN owned by a formerly retained manifest, never scan/delete
# arbitrary cache contents. Both catalogs and both mutable generations are roots.
const Journal=preload("res://src/recovery_journal.gd")
const Storage=preload("res://src/storage.gd")
const Atomic=preload("res://src/atomic_metadata.gd")
static func path(keep: Dictionary,value) -> bool:
	if not value is String or not Storage.safe_relative(value):return false
	keep[value]=true;return true
static func references(data: Dictionary,keep: Dictionary,depth:=0) -> bool:
	if depth>8:return false
	for field in ["scene","model","reference_sheet"]:
		var row=data.get(field,{})
		if not row is Dictionary:return false
		if row.has("path") and not path(keep,row.path):return false
	var world=data.get("world",{})
	if not world is Dictionary:return false
	for field in ["objects","effects"]:
		if not world.get(field,[]) is Array:return false
		for row in world.get(field,[]):
			if not row is Dictionary or not path(keep,row.get("path")):return false
			if field=="effects" and not path(keep,row.get("texture_path")):return false
	var audio=data.get("audio",{})
	if not audio is Dictionary or not audio.get("clips",[]) is Array:return false
	if audio.has("path") and not path(keep,audio.path):return false
	for clip in audio.get("clips",[]):
		if not clip is Dictionary or not path(keep,clip.get("path")):return false
	if not data.get("layers") is Array:return false
	for layer in data.layers:
		if not layer is Dictionary or not layer.get("cels") is Array:return false
		for cel in layer.cels:
			if not cel is Dictionary or not path(keep,cel.get("path")):return false
	var graph=data.get("sequence_graph",{})
	if not graph is Dictionary or not graph.get("assets",[]) is Array:return false
	for asset in graph.get("assets",[]):
		if not asset is Dictionary or not asset.get("scene") is Dictionary or not references(asset.scene,keep,depth+1):return false
	return true
static func owned_blob(relative: String) -> bool:
	var name:=relative.get_file();var ext:=name.get_extension()
	if name.length()!=65+ext.length() or not Journal.valid_hash(name.substr(0,64)):return false
	return relative.get_base_dir()=="cels/content" and ext=="png" or relative.get_base_dir()=="assets" and ext in ["glb","wav","png","json"] or relative.get_base_dir()=="references" and ext=="png"
static func inventory(folder: String) -> Dictionary:
	var owner:=Journal.read_json(folder.path_join("session.json"),16384)
	if owner.get("pid")!=OS.get_process_id() or not Atomic.path_error(folder.path_join("session.json"),folder.get_base_dir()).is_empty():return {}
	var manifests: Dictionary={};var stamps: Dictionary={"session.json":FileAccess.get_sha256(folder.path_join("session.json"))}
	for name in ["journal.json","journal.backup.json"]:
		var target:=folder.path_join(name)
		if not FileAccess.file_exists(target):continue
		if not Atomic.path_error(target,folder.get_base_dir()).is_empty():return {}
		var catalog:=Journal.read_catalog(target)
		if catalog.is_empty():return {}
		stamps[name]=FileAccess.get_sha256(target)
		for entry in catalog.entries:manifests[Journal.manifest_name(entry.sha256)]=true
	for name in ["project.json","project.backup.json"]:
		if FileAccess.file_exists(folder.path_join(name)):manifests[name]=true
	if manifests.is_empty():return {}
	var keep: Dictionary={}
	for name in manifests:
		var target:=folder.path_join(name)
		if not Atomic.path_error(target,folder.get_base_dir()).is_empty() or not Storage.readable_manifest(target):return {}
		if Journal.is_manifest(name) and not Journal.valid_manifest(folder,name):return {}
		stamps[name]=FileAccess.get_sha256(target)
		var data:=Journal.read_json(target)
		if not references(data,keep):return {}
	return {"owner":owner,"paths":keep,"stamps":stamps}
static func stable(folder: String,stamps: Dictionary) -> bool:
	for name in stamps:
		if FileAccess.get_sha256(folder.path_join(name))!=stamps[name]:return false
	return true
static func retire(folder: String,before: Dictionary) -> Dictionary:
	var after:=inventory(folder)
	if before.is_empty() or after.is_empty() or before.owner!=after.owner or not stable(folder,after.stamps):return {"removed":0,"bytes":0,"skipped":true}
	var count:=0;var bytes:=0
	for relative in before.paths:
		if after.paths.has(relative) or not owned_blob(relative):continue
		var target:=folder.path_join(relative)
		if not Atomic.path_error(target,folder.get_base_dir()).is_empty():continue
		var file:=FileAccess.open(target,FileAccess.READ)
		if file==null:continue
		var length:=file.get_length();file.close()
		if DirAccess.remove_absolute(target)==OK:count+=1;bytes+=length
	return {"removed":count,"bytes":bytes,"skipped":false}
