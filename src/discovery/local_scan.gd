extends Node
## Cooperative filename enumeration only. Files are never opened as models.
signal changed
const Catalog = preload("res://src/discovery/catalog.gd")
const MAX_ENTRIES := 50000
const MAX_MODELS := 10000
var rows: Array = []
var loading := false
var message := "Choose a directory to browse local model filenames."
var roots: Array = []
var _queue: Array = []
var _directory: DirAccess
var _path := ""
var _depth := 0
var _entries := 0
var _seen := {}
var _errors: Array = []

func start(paths: Array) -> void:
	cancel()
	rows.clear(); roots.clear(); _queue.clear(); _seen.clear(); _errors.clear(); _entries = 0
	for path in paths:
		var clean := str(path).simplify_path()
		if not clean.is_absolute_path() or clean.begins_with("res://") or clean.begins_with("user://"):
			_errors.append("Choose an absolute filesystem directory: " + clean); continue
		if clean not in roots: roots.append(clean); _queue.append({"path":clean, "depth":0})
	loading = not _queue.is_empty()
	message = "Scanning selected directories…" if loading else "; ".join(_errors)
	if not loading and _errors.is_empty(): message = "Choose a directory to browse local model filenames."
	changed.emit()

func cancel() -> void:
	if _directory: _directory.list_dir_end(); _directory = null
	_queue.clear()
	if loading: message = "Scan cancelled. Partial filenames are kept."
	loading = false
	changed.emit()

func _process(_delta: float) -> void:
	if not loading: return
	# Both the entry count and per-frame time are bounded. No symlinks/reparse dirs.
	var deadline := Time.get_ticks_usec() + 3000
	var processed := 0
	while processed < 128 and Time.get_ticks_usec() < deadline:
		if _entries >= MAX_ENTRIES or rows.size() >= MAX_MODELS:
			_errors.append("Scan limit reached (%d entries / %d model filenames). Choose a smaller directory." % [MAX_ENTRIES, MAX_MODELS])
			_finish(); return
		if not _directory:
			if _queue.is_empty(): _finish(); return
			var next: Dictionary = _queue.pop_front()
			_path = next.path; _depth = next.depth
			var key := _path.to_lower() if OS.get_name() == "Windows" else _path
			if _seen.has(key): continue
			_seen[key] = true
			_directory = DirAccess.open(_path)
			if not _directory:
				_errors.append("Cannot read directory: " + _path); continue
			_directory.include_hidden = false; _directory.include_navigational = false
			if _directory.list_dir_begin() != OK:
				_errors.append("Cannot list directory: " + _path); _directory = null; continue
		var name := _directory.get_next()
		if name.is_empty(): _directory.list_dir_end(); _directory = null; continue
		processed += 1; _entries += 1
		var file := _path.path_join(name)
		if _directory.is_link(name): continue
		if _directory.current_is_dir():
			if _depth < 32: _queue.append({"path":file, "depth":_depth + 1})
			else: _errors.append("Skipped directories deeper than 32 levels.")
			continue
		var types := Catalog.local_format(file)
		if types.is_empty(): continue
		rows.append({"id":file, "title":name, "provider":"local", "url":"", "path":file, "keywords":"", "formats":types, "access":["Local file"], "evidence":"Filename extension only; compatibility and dependencies have not been inspected."})
	message = "%d model filenames from %d entries…" % [rows.size(), _entries]
	changed.emit()

func _finish() -> void:
	cancel()
	message = "%d local model filenames. %s" % [rows.size(), "; ".join(_errors.slice(0, 5))]
	changed.emit()
