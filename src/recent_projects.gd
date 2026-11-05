extends RefCounted
const Journal=preload("res://src/recovery_journal.gd")
const LIMIT:=12
var file_path: String
var error:=""

func read() -> Array:
	var file:=FileAccess.open(file_path,FileAccess.READ)
	if not file or file.get_length()>65536:return []
	var parser:=JSON.new()
	if parser.parse(file.get_as_text())!=OK:return []
	var data=parser.data
	if not data is Dictionary or data.get("format")!="studio_recent_projects_1" or not data.get("projects") is Array or data.projects.size()>LIMIT:return []
	var rows: Array=[];var seen:={}
	for row in data.projects:
		if not row is Dictionary or not valid_path(row.get("path")) or seen.has(row.path.to_lower()):return []
		if not (row.get("opened_at") is int or row.get("opened_at") is float) or not is_finite(float(row.opened_at)) or row.opened_at<0:return []
		seen[row.path.to_lower()]=true;rows.append(row)
	return rows

static func valid_path(value) -> bool:
	return value is String and value.length()<=4096 and value.is_absolute_path() and not "://" in value and value.get_extension().to_lower()=="has"

func write(rows: Array) -> bool:
	error=""
	if rows.size()>LIMIT:return false
	var text:=JSON.stringify({"format":"studio_recent_projects_1","projects":rows},"",true,true)
	while text.to_utf8_buffer().size()>65536 and rows.size()>1:
		rows.pop_back();text=JSON.stringify({"format":"studio_recent_projects_1","projects":rows},"",true,true)
	if text.to_utf8_buffer().size()>65536:error="Recent-project entry is too large.";return false
	if DirAccess.make_dir_recursive_absolute(file_path.get_base_dir())!=OK:error="Cannot create the recent-project list.";return false
	var file:=FileAccess.open(file_path+".tmp",FileAccess.WRITE)
	if not file:error="Cannot save the recent-project list.";return false
	file.store_string(text);file.flush();var code:=file.get_error();file.close()
	if code!=OK or DirAccess.rename_absolute(file_path+".tmp",file_path)!=OK:error="Cannot commit the recent-project list.";return false
	return true

func remember(path: String,folder: String,revision: int) -> bool:
	path=ProjectSettings.globalize_path(path).replace("\\","/").simplify_path()
	if not valid_path(path) or not FileAccess.file_exists(path):return false
	var rows:=read();var row:={"path":path,"opened_at":Time.get_unix_time_from_system(),"preview_folder":"","preview":""}
	for previous in rows:
		if previous.path.to_lower()==path.to_lower():row=previous.duplicate(true);break
	row.opened_at=Time.get_unix_time_from_system();row.path=path
	if revision>=0:
		row.preview="";row.preview_folder=""
		for entry in Journal.entries(folder):
			if entry.revision==revision and not entry.preview.is_empty():row.preview=entry.preview;row.preview_folder=folder;break
	rows=rows.filter(func(previous):return previous.path.to_lower()!=path.to_lower());rows.push_front(row)
	if rows.size()>LIMIT:rows.resize(LIMIT)
	return write(rows)

func forget(path: String) -> bool:
	return write(read().filter(func(row):return row.path.to_lower()!=path.to_lower()))

static func preview(row: Dictionary,recovery_root: String) -> Image:
	var folder=row.get("preview_folder","")
	if not folder is String or not row.get("preview","") is String:return null
	# Only our managed session previews are read; arbitrary config paths are inert.
	if folder.replace("\\","/").simplify_path().get_base_dir().to_lower()!=recovery_root.replace("\\","/").simplify_path().to_lower():return null
	return Journal.preview(folder,row.preview)
