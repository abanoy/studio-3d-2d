extends RefCounted
# Browser-only bounded adapter for the existing HAS ZIPv1, not a new format.
const MAX_TOTAL:=128*1024*1024
const MAX_META:=1024*1024
const MAX_FILES:=128

static func fail(message: String) -> Dictionary:return {"error":message}
static func integer(value,minimum: int,maximum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value==floor(value) and value>=minimum and value<=maximum
static func safe(name) -> bool:
	if not name is String or name.is_empty() or name.length()>512 or name.begins_with("/"):return false
	for character in name:
		if character.unicode_at(0)<32 or character.unicode_at(0)>126 or character in '\\:<>"|?*':return false
	for part in name.split("/"):
		if part in ["",".",".."] or part.ends_with(" ") or part.ends_with("."):return false
		var stem: String=part.get_slice(".",0).to_upper()
		if stem in ["CON","PRN","AUX","NUL"]:return false
		for i in range(1,10):
			if stem=="COM"+str(i) or stem=="LPT"+str(i):return false
	return true
static func digest(bytes: PackedByteArray) -> String:
	var hash:=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes);return hash.finish().hex_encode()
static func valid_sha(value) -> bool:
	if not value is String or value.length()!=64:return false
	for character in value:
		if not character in "0123456789abcdef":return false
	return true
static func object_json(bytes: PackedByteArray) -> Dictionary:
	if bytes.size()>MAX_META:return fail("HAS metadata exceeds 1 MiB.")
	var parser:=JSON.new()
	if parser.parse(bytes.get_string_from_utf8())!=OK or not parser.data is Dictionary:return fail("Invalid HAS metadata.")
	return {"data":parser.data}
static func inventory(project: Dictionary) -> Dictionary:
	var assets:={};var names:={"project.json":true};var slots: Array=[]
	if not integer(project.get("schema_version"),3,4):return fail("This browser build reads HAS project schema3 and4.")
	if project.get("schema_version")==4:
		if project.has("scene") or project.has("model") or not project.get("world") is Dictionary or not project.world.get("format") is String or project.world.format!="studio_world_1" or not project.world.get("objects") is Array or project.world.objects.size()>64:return fail("Invalid HAS world inventory.")
		for row in project.world.objects:
			if not row is Dictionary or row.has("source") or row.get("path")!="assets/"+str(row.get("sha256"))+".glb":return fail("Invalid managed world asset.")
			slots.append(row)
	elif project.get("schema_version")==3:
		for key in ["scene","model"]:
			if project.get(key) is Dictionary and not project[key].is_empty():slots.append(project[key])
	else:return fail("This browser build reads HAS project schema3 and4.")
	if project.get("audio") is Dictionary and not project.audio.is_empty():slots.append(project.audio)
	for row in slots:
		var name=row.get("path")
		if not safe(name) or not name.begins_with("assets/") or not name.get_extension() in ["glb","wav"] or not valid_sha(row.get("sha256")):return fail("Invalid HAS asset identity.")
		if assets.has(name) and assets[name]!=row.sha256:return fail("Conflicting HAS asset identity.")
		assets[name]=row.sha256;names[name]=true
	if not project.get("layers") is Array or project.layers.size()>4:return fail("Invalid HAS drawing inventory.")
	for layer in project.layers:
		if not layer is Dictionary or not layer.get("cels") is Array or layer.cels.size()>32:return fail("Invalid HAS cel inventory.")
		for cel in layer.cels:
			if not cel is Dictionary or not safe(cel.get("path")) or not cel.path.begins_with("cels/") or not cel.path.ends_with(".png"):return fail("Invalid HAS cel path.")
			names[cel.path]=true
	if names.size()+1>MAX_FILES:return fail("Too many HAS files.")
	return {"assets":assets,"names":names}

static func zip_directory(raw: PackedByteArray) -> Dictionary:
	if raw.size()<22 or raw.size()>MAX_TOTAL:return fail("Browser HAS files must fit within128MiB.")
	var end:=-1
	for at in range(raw.size()-22,maxi(-1,raw.size()-65558),-1):
		if raw.decode_u32(at)==0x06054b50 and at+22+raw.decode_u16(at+20)==raw.size():end=at;break
	if end<0:return fail("Invalid HAS ZIP end record.")
	var count:=raw.decode_u16(end+10);var size:=raw.decode_u32(end+12);var offset:=raw.decode_u32(end+16)
	if raw.decode_u16(end+4)!=0 or raw.decode_u16(end+6)!=0 or raw.decode_u16(end+8)!=count or count<2 or count>MAX_FILES or size>MAX_META or offset+size!=end:return fail("Unsupported HAS ZIP directory.")
	var index:={};var folded:={};var total:=0;var cursor:=offset;var spans: Array=[]
	for _i in range(count):
		if cursor+46>end or raw.decode_u32(cursor)!=0x02014b50:return fail("Invalid HAS ZIP entry.")
		var flags:=raw.decode_u16(cursor+8);var method:=raw.decode_u16(cursor+10);var compressed:=raw.decode_u32(cursor+20);var expanded:=raw.decode_u32(cursor+24)
		var length:=raw.decode_u16(cursor+28);var extra:=raw.decode_u16(cursor+30);var comment:=raw.decode_u16(cursor+32);var local:=raw.decode_u32(cursor+42)
		if cursor+46+length+extra+comment>end or (flags & ~0x80e)!=0 or not method in [0,8] or raw.decode_u16(cursor+34)!=0 or ((raw.decode_u32(cursor+38)>>16)&0xf000)==0xa000:return fail("Encrypted, linked or unsupported HAS entry.")
		var encoded:=raw.slice(cursor+46,cursor+46+length);var name:=encoded.get_string_from_utf8()
		if not safe(name) or encoded!=name.to_utf8_buffer() or folded.has(name.to_lower()):return fail("Unsafe or duplicate HAS path.")
		var limit:=MAX_META if name in ["has.json","project.json"] else MAX_TOTAL if name.ends_with(".glb") else 32*1024*1024
		total+=expanded
		if expanded>limit or total>MAX_TOTAL or local+30>offset or raw.decode_u32(local)!=0x04034b50:return fail("HAS payload exceeds browser bounds.")
		var local_length:=raw.decode_u16(local+26);var local_extra:=raw.decode_u16(local+28);var data_start:=local+30+local_length+local_extra
		if data_start+compressed>offset or raw.decode_u16(local+6)!=flags or raw.decode_u16(local+8)!=method or raw.slice(local+30,local+30+local_length)!=encoded:return fail("HAS local entry differs from its directory.")
		if (flags & 8)==0 and (raw.decode_u32(local+18)!=compressed or raw.decode_u32(local+22)!=expanded or raw.decode_u32(local+14)!=raw.decode_u32(cursor+16)):return fail("HAS local sizes differ.")
		spans.append([local,data_start+compressed]);index[name]={"bytes":expanded};folded[name.to_lower()]=true;cursor+=46+length+extra+comment
	if cursor!=end:return fail("Invalid HAS directory size.")
	spans.sort_custom(func(a,b):return a[0]<b[0])
	for i in range(1,spans.size()):
		if spans[i][0]<spans[i-1][1]:return fail("Overlapping HAS entries.")
	return {"entries":index,"bytes":total}

static func pack(folder: String,target: String) -> Dictionary:
	var project_bytes:=FileAccess.get_file_as_bytes(folder.path_join("project.json"));var parsed:=object_json(project_bytes)
	if parsed.has("error"):return parsed
	var declared:=inventory(parsed.data)
	if declared.has("error"):return declared
	var records: Array=[];var payload: Array=[];var total:=0
	var paths: Array=declared.names.keys();paths.sort()
	for name in paths:
		var file:=FileAccess.open(folder.path_join(name),FileAccess.READ)
		if file==null:return fail("A snapshot payload disappeared.")
		var size:=file.get_length();total+=size;file.close()
		if total>MAX_TOTAL or size>(MAX_TOTAL if name.ends_with(".glb") else MAX_META if name=="project.json" else 32*1024*1024):return fail("Browser packed projects must fit within128MiB.")
		var sha:=FileAccess.get_sha256(folder.path_join(name))
		if declared.assets.has(name) and declared.assets[name]!=sha:return fail("Snapshot asset checksum changed.")
		var row:={"path":name,"sha256":sha,"bytes":size};payload.append(row)
		if declared.assets.has(name):records.append(row)
	var header:={"format":"hybrid_animation_studio","version":1,"storage":"packed","assets":records,"payload":payload}
	var writer:=ZIPPacker.new();writer.compression_level=1
	if writer.open(target)!=OK:return fail("Cannot create browser HAS package.")
	if writer.start_file("has.json")!=OK or writer.write_file(JSON.stringify(header,"",true,true).to_utf8_buffer())!=OK or writer.close_file()!=OK:writer.close();return fail("Cannot write HAS inventory.")
	for row in payload:
		var bytes:=FileAccess.get_file_as_bytes(folder.path_join(row.path))
		if bytes.size()!=row.bytes or digest(bytes)!=row.sha256 or writer.start_file(row.path)!=OK or writer.write_file(bytes)!=OK or writer.close_file()!=OK:writer.close();return fail("Snapshot changed or package write failed.")
	if writer.close()!=OK:return fail("Cannot finish HAS package.")
	if FileAccess.get_file_as_bytes(target).size()>MAX_TOTAL:return fail("Browser HAS archive exceeds128MiB.")
	return {"path":target,"bytes":total}

static func unpack(source: String,folder: String) -> Dictionary:
	var raw:=FileAccess.get_file_as_bytes(source);var checked:=zip_directory(raw)
	if checked.has("error"):return checked
	raw.clear()
	if DirAccess.dir_exists_absolute(folder):return fail("Choose a new browser extraction folder.")
	var reader:=ZIPReader.new()
	if reader.open(source)!=OK:return fail("Cannot read HAS archive.")
	var result:=unpack_reader(reader,checked.entries,folder);reader.close();return result
static func unpack_reader(reader: ZIPReader,entries: Dictionary,folder: String) -> Dictionary:
	if not entries.has("has.json") or not entries.has("project.json"):return fail("Missing HAS inventory.")
	var parsed_header:=object_json(reader.read_file("has.json"));var parsed_project:=object_json(reader.read_file("project.json"))
	if parsed_header.has("error"):return parsed_header
	if parsed_project.has("error"):return parsed_project
	var header: Dictionary=parsed_header.data;var declared:=inventory(parsed_project.data)
	if declared.has("error"):return declared
	if not header.get("format") is String or header.format!="hybrid_animation_studio" or not integer(header.get("version"),1,1):return fail("Unsupported HAS container version.")
	if not header.get("storage") is String or header.storage!="packed":return fail("Open this linked project in Windows Studio and save a packed copy for the browser.")
	if not header.get("assets") is Array or not header.get("payload") is Array or header.assets.size()+header.payload.size()>MAX_FILES:return fail("Invalid HAS inventory.")
	var assets:={};var payload:={}
	for row in header.assets:
		if not row is Dictionary or not safe(row.get("path")) or assets.has(row.path) or not declared.assets.has(row.path) or row.get("sha256")!=declared.assets[row.path] or not integer(row.get("bytes"),0,MAX_TOTAL):return fail("HAS asset inventory mismatch.")
		assets[row.path]=row
	if assets.size()!=declared.assets.size():return fail("Missing HAS asset records.")
	for row in header.payload:
		if not row is Dictionary or not safe(row.get("path")) or payload.has(row.path) or not declared.names.has(row.path) or not entries.has(row.path) or not integer(row.get("bytes"),0,MAX_TOTAL) or row.bytes!=entries[row.path].bytes or not valid_sha(row.get("sha256")):return fail("HAS payload inventory mismatch.")
		if assets.has(row.path) and (row.sha256!=assets[row.path].sha256 or row.bytes!=assets[row.path].bytes):return fail("HAS asset identity differs.")
		payload[row.path]=row
	if payload.size()!=declared.names.size() or entries.size()!=payload.size()+1:return fail("Unexpected or missing HAS payload.")
	# Validate all bytes before writing a new cache or replacing any live scene.
	for name in payload:
		var bytes:=reader.read_file(name)
		if bytes.size()!=payload[name].bytes or digest(bytes)!=payload[name].sha256:return fail("HAS payload checksum differs: "+name)
	if DirAccess.make_dir_recursive_absolute(folder)!=OK:return fail("Cannot create browser project cache.")
	for name in payload:
		var target:=folder.path_join(name)
		if DirAccess.make_dir_recursive_absolute(target.get_base_dir())!=OK:return fail("Cannot create browser asset folder.")
		var file:=FileAccess.open(target,FileAccess.WRITE)
		if file==null:return fail("Cannot write browser asset.")
		file.store_buffer(reader.read_file(name));file.flush();var error:=file.get_error();file.close()
		if error!=OK:return fail("Cannot finish browser asset.")
	return {"folder":folder,"storage":"packed"}
