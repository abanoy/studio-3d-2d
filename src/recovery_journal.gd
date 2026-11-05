extends RefCounted
# Immutable metadata + one checksummed catalog; model/WAV/cel blobs stay shared.
const MAX_ENTRIES:=12
const MAX_MANIFEST:=1024*1024
const MAX_PREVIEW:=256*1024
const PREVIEW_SIZE:=Vector2i(256,144)

static func valid_hash(value) -> bool:
	if not value is String or value.length()!=64:return false
	for character in value:
		if not character in "0123456789abcdef":return false
	return true

static func manifest_name(digest: String) -> String:return "history_"+digest+".json"
static func preview_name(digest: String) -> String:return "preview_"+digest+".png"
static func is_manifest(name: String) -> bool:return name.length()==77 and name.begins_with("history_") and name.ends_with(".json") and valid_hash(name.substr(8,64))
static func is_preview(name: String) -> bool:return name.length()==76 and name.begins_with("preview_") and name.ends_with(".png") and valid_hash(name.substr(8,64))
static func sha(data: PackedByteArray) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256);context.update(data);return context.finish().hex_encode()

static func read_json(path: String,limit:=MAX_MANIFEST) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>limit:return {}
	var parser:=JSON.new()
	if parser.parse(file.get_as_text())!=OK:return {}
	var value=parser.data
	return value if value is Dictionary else {}

static func valid_manifest(folder: String,name: String) -> bool:
	if not is_manifest(name):return false
	var file:=FileAccess.open(folder.path_join(name),FileAccess.READ)
	return file!=null and file.get_length()<=MAX_MANIFEST and FileAccess.get_sha256(folder.path_join(name))==name.substr(8,64)

static func read_catalog(path: String) -> Dictionary:
	var envelope:=read_json(path,64*1024)
	if envelope.get("format")!="studio_recovery_journal_1" or not envelope.get("payload") is String or envelope.get("sha256")!=str(envelope.get("payload")).sha256_text():return {}
	var parser:=JSON.new()
	if parser.parse(envelope.payload)!=OK:return {}
	var entries=parser.data
	if not entries is Array or entries.size()>MAX_ENTRIES:return {}
	var seen:={}
	for entry in entries:
		if not entry is Dictionary or not valid_hash(entry.get("sha256")) or seen.has(entry.sha256):return {}
		if not entry.get("preview","") is String or not entry.get("preview","").is_empty() and not valid_hash(entry.preview):return {}
		if not (entry.get("saved_at") is int or entry.get("saved_at") is float) or not is_finite(float(entry.saved_at)) or entry.saved_at<0:return {}
		if not (entry.get("revision") is int or entry.get("revision") is float) or entry.revision!=floor(entry.revision) or entry.revision<0 or entry.revision>2147483647:return {}
		seen[entry.sha256]=true
	return {"entries":entries,"payload":envelope.payload}

static func entries(folder: String) -> Array:
	for name in ["journal.json","journal.backup.json"]:
		var catalog:=read_catalog(folder.path_join(name))
		if not catalog.is_empty():return catalog.entries
	return []

static func write_bytes(path: String,data: PackedByteArray) -> String:
	if FileAccess.file_exists(path) and FileAccess.get_sha256(path)==sha(data):return ""
	var file:=FileAccess.open(path+".tmp",FileAccess.WRITE)
	if not file:return "Cannot write recovery history."
	file.store_buffer(data);file.flush();var error:=file.get_error();file.close()
	if error!=OK:return "Cannot flush recovery history."
	if DirAccess.rename_absolute(path+".tmp",path)!=OK:return "Cannot commit recovery history."
	return "" if FileAccess.get_sha256(path)==sha(data) else "Recovery history checksum failed."

static func commit(folder: String,records: Array) -> String:
	var payload:=JSON.stringify(records,"",true,true)
	var primary:=folder.path_join("journal.json")
	var previous:=read_catalog(primary)
	if not previous.is_empty() and previous.payload==payload:return ""
	if not previous.is_empty():
		var backup:=folder.path_join("journal.backup.json")
		var error:=write_bytes(backup,FileAccess.get_file_as_bytes(primary))
		if not error.is_empty():return error
	var error:=write_bytes(primary,JSON.stringify({"format":"studio_recovery_journal_1","payload":payload,"sha256":payload.sha256_text()},"",true,true).to_utf8_buffer())
	if error.is_empty():prune(folder)
	return error

static func record(folder: String) -> String:
	var records:=entries(folder);var seen:={}
	for entry in records:seen[entry.sha256]=true
	for name in ["project.backup.json","project.json"]:
		var path:=folder.path_join(name);var data:=read_json(path)
		var editor=data.get("editor",{});var info=editor.get("recovery",{}) if editor is Dictionary else {}
		if not info is Dictionary or not info.get("origin") is String or not (info.get("saved_at") is int or info.get("saved_at") is float) or not is_finite(float(info.saved_at)) or info.saved_at<0:continue
		if not (info.get("revision") is int or info.get("revision") is float) or info.revision!=floor(info.revision) or info.revision<0 or info.revision>2147483647:continue
		var digest:=FileAccess.get_sha256(path)
		if seen.has(digest):continue
		var target:=folder.path_join(manifest_name(digest))
		var error:=write_bytes(target,FileAccess.get_file_as_bytes(path))
		if not error.is_empty():return error
		records.append({"sha256":digest,"saved_at":info.saved_at,"revision":int(info.revision),"preview":""});seen[digest]=true
	records.sort_custom(func(a,b):
		if a.saved_at!=b.saved_at:return a.saved_at>b.saved_at
		return a.revision>b.revision if a.revision!=b.revision else a.sha256>b.sha256)
	if records.size()>MAX_ENTRIES:records.resize(MAX_ENTRIES)
	return "" if records.is_empty() else commit(folder,records)

static func attach_preview(folder: String,digest: String,image: Image) -> String:
	if not valid_hash(digest) or not image or image.get_size()!=PREVIEW_SIZE:return "Invalid recovery preview."
	var records:=entries(folder);var found:=-1
	for i in range(records.size()):
		if records[i].sha256==digest:found=i;break
	if found<0:return "Checkpoint is no longer retained."
	var bytes:=image.save_png_to_buffer()
	if bytes.is_empty() or bytes.size()>MAX_PREVIEW:return "Recovery preview exceeds its budget."
	var hash:=sha(bytes);var target:=folder.path_join(preview_name(hash))
	var error:=write_bytes(target,bytes)
	if not error.is_empty():return error
	records[found].preview=hash
	return commit(folder,records)

static func preview(folder: String,digest: String) -> Image:
	if not valid_hash(digest):return null
	var path:=folder.path_join(preview_name(digest));var file:=FileAccess.open(path,FileAccess.READ)
	if not file or file.get_length()>MAX_PREVIEW or FileAccess.get_sha256(path)!=digest:return null
	var bytes:=file.get_buffer(file.get_length());var image:=Image.new()
	if bytes.size()<24 or bytes.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]):return null
	var width: int=(bytes[16]<<24)|(bytes[17]<<16)|(bytes[18]<<8)|bytes[19]
	var height: int=(bytes[20]<<24)|(bytes[21]<<16)|(bytes[22]<<8)|bytes[23]
	if width!=PREVIEW_SIZE.x or height!=PREVIEW_SIZE.y:return null
	if image.load_png_from_buffer(bytes)!=OK or image.get_size()!=PREVIEW_SIZE:return null
	return image

static func prune(folder: String) -> void:
	# Delete only exact journal-owned filenames after the new index is committed.
	# Keep rollback references too. Asset/cel garbage collection is separate work.
	var keep:={}
	for name in ["journal.json","journal.backup.json"]:
		var catalog:=read_catalog(folder.path_join(name))
		if catalog.is_empty():continue
		for entry in catalog.entries:
			keep[manifest_name(entry.sha256)]=true
			if not entry.get("preview","").is_empty():keep[preview_name(entry.preview)]=true
	for name in ["project.json","project.backup.json"]:
		if FileAccess.file_exists(folder.path_join(name)):keep[manifest_name(FileAccess.get_sha256(folder.path_join(name)))]=true
	for name in DirAccess.get_files_at(folder):
		if (is_manifest(name) or is_preview(name)) and not keep.has(name):DirAccess.remove_absolute(folder.path_join(name))
