extends RefCounted
## Personal browsing choices only. Never stores accounts, network opt-in or models.
const Catalog = preload("res://src/discovery/catalog.gd")
const DEFAULT_PATH := "res://output/discovery-preferences.json"
const MAX_BYTES := 65536
const MAX_DIRECTORIES := 32

static func defaults() -> Dictionary:
	return {"version":1, "directories":[], "website":"All", "local_format":"All", "online_format":"All", "expand":true, "tab":0, "dismissed_notices":{}}

static func validate(value) -> Dictionary:
	if not value is Dictionary or value.get("version") != 1: return {"error":"Unsupported discovery preferences. Using defaults."}
	if not value.get("directories") is Array or value.directories.size() > MAX_DIRECTORIES: return {"error":"Invalid saved directory list. Using defaults."}
	var clean := defaults()
	var seen := {}
	for path in value.directories:
		if not path is String or path.length() > 4096 or path.to_utf8_buffer().has(0) or not path.is_absolute_path() or path.begins_with("res://") or path.begins_with("user://"):
			return {"error":"Invalid saved directory path. Using defaults."}
		var normalized: String = path.simplify_path()
		var key := normalized.to_lower() if OS.get_name() == "Windows" else normalized
		if not seen.has(key): clean.directories.append(normalized); seen[key] = true
	var sites: Array = ["All"]
	for source in Catalog.PROVIDERS: sites.append(source.id)
	if value.get("website") not in sites or value.get("local_format") not in Catalog.FORMATS or value.get("online_format") not in Catalog.FORMATS:
		return {"error":"Unrecognized saved website or format. Using defaults."}
	var tab = value.get("tab")
	if not value.get("expand") is bool or not (tab is int or tab is float) or (tab != 0 and tab != 1): return {"error":"Invalid saved discovery controls. Using defaults."}
	for key in ["website", "local_format", "online_format", "expand", "tab"]: clean[key] = value[key]
	clean.tab = int(tab)
	var notices = value.get("dismissed_notices", {}) # Version-1 files predating notices remain valid.
	if not notices is Dictionary or notices.size() > 2: return {"error":"Invalid saved source notices. Using defaults."}
	for key in notices:
		if key not in ["steam_sfm", "steam_gmod"] or not notices[key] is bool: return {"error":"Invalid saved source notice choice. Using defaults."}
		clean.dismissed_notices[key] = notices[key]
	return {"data":clean}

static func read_file(path: String) -> Dictionary:
	if path.is_empty() or not FileAccess.file_exists(path): return {"data":defaults()}
	var file := FileAccess.open(path, FileAccess.READ)
	if not file: return {"error":"Could not read discovery preferences. Using defaults."}
	if file.get_length() > MAX_BYTES: return {"error":"Discovery preferences exceed 64 KiB. Using defaults."}
	var json := JSON.new()
	if json.parse(file.get_as_text()) != OK: return {"error":"Discovery preferences are malformed. Using defaults."}
	return validate(json.data)

static func write_file(path: String, value: Dictionary) -> String:
	if path.is_empty(): return ""
	var checked := validate(value)
	if checked.has("error"): return checked.error
	var text := JSON.stringify(checked.data, "  ")
	if text.to_utf8_buffer().size() > MAX_BYTES: return "Discovery preferences exceed 64 KiB. Previous choices were preserved."
	var absolute := ProjectSettings.globalize_path(path)
	if DirAccess.make_dir_recursive_absolute(absolute.get_base_dir()) != OK: return "Could not create the discovery preferences directory."
	var parent := DirAccess.open(absolute.get_base_dir())
	if not parent or parent.is_link(absolute.get_file()): return "Discovery preferences cannot replace a linked file."
	var temporary := absolute + ".%d.tmp" % OS.get_process_id()
	if parent.is_link(temporary.get_file()): return "Discovery preferences temporary path is a linked file."
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if not file: return "Could not write discovery preferences. Previous choices were preserved."
	file.store_string(text); file.flush()
	var error := file.get_error(); file.close()
	if error == OK: error = DirAccess.rename_absolute(temporary, absolute)
	if error != OK:
		DirAccess.remove_absolute(temporary)
		return "Could not replace discovery preferences. Previous choices were preserved."
	return ""
