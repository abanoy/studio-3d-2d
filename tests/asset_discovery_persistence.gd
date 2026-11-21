extends SceneTree
const Browser = preload("res://src/discovery/browser.gd")
const Preferences = preload("res://src/discovery/preferences.gd")
const Catalog = preload("res://src/discovery/catalog.gd")
var checks := 0
var failures: Array = []
var browser

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); printerr("FAIL: " + label)

func _initialize() -> void:
	create_timer(20).timeout.connect(func(): quit(2))
	call_deferred("run")

func settle() -> void:
	await process_frame; await process_frame

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var folder: String = args[0]
	var reading := "--read" in args
	var settings := folder.path_join("preferences.json")
	var directory := folder.path_join("models-初音")
	browser = Browser.new(); browser.preferences_path = settings; root.add_child(browser)
	await settle()
	if not reading:
		DirAccess.make_dir_recursive_absolute(directory)
		for name in ["Miku.pmx", "Avatar.vrm"]:
			var file := FileAccess.open(directory.path_join(name), FileAccess.WRITE); file.store_string("synthetic filename fixture"); file.close()
		browser.picker.dir_selected.emit(directory); await settle()
		browser.format_filter.select(Catalog.FORMATS.find("VRM")); browser.format_filter.item_selected.emit(browser.format_filter.selected)
		browser.tabs.current_tab = 1; await settle()
		browser.website.select(2); browser.website.item_selected.emit(2)
		browser.format_filter.select(Catalog.FORMATS.find("MMD")); browser.format_filter.item_selected.emit(browser.format_filter.selected)
		browser.expand.button_pressed = false
		browser.network.button_pressed = true # Consent is deliberately not saved.
		check(browser._settings_error.is_empty(), "personal settings save without error")
		var data := Preferences.read_file(settings)
		if data.has("error"): printerr("PREFERENCE_READ: " + str(data.error))
		check(data.has("data") and data.data.local_format == "VRM" and data.data.online_format == "MMD", "separate local and online format preferences")
		check(not FileAccess.get_file_as_string(settings).contains("network"), "network opt-in is never persisted")
		check(not FileAccess.get_file_as_string(settings).contains("token"), "no account/token fields are persisted")
	else:
		check(browser.directories == [directory.simplify_path()], "new process restores the chosen Unicode directory")
		check(browser.tabs.current_tab == 1 and browser.website.selected == 2, "new process restores tab and provider")
		check(Catalog.FORMATS[browser.format_filter.selected] == "MMD" and not browser.expand.button_pressed, "new process restores online format and expansion")
		check(not browser.network.button_pressed and not browser.online.network_enabled and not browser.online.loading, "restart stays offline despite previous network opt-in")
		browser.tabs.current_tab = 0
		while browser.local.loading: await process_frame
		await settle()
		check(Catalog.FORMATS[browser.format_filter.selected] == "VRM" and browser.visible_rows.size() == 1, "restored local filter applies to real enumerated filenames")
		browser.clear_button.pressed.emit(); await settle()
		check(Preferences.read_file(settings).data.directories.is_empty(), "Clear directories persists the removal")
		var original := FileAccess.get_file_as_bytes(settings)
		var invalid := Preferences.defaults(); invalid.directories = ["relative/path"]
		check(not Preferences.write_file(settings, invalid).is_empty() and original == FileAccess.get_file_as_bytes(settings), "invalid save preserves the previous file")
		invalid = Preferences.defaults(); invalid.website = "invented-provider"
		check(Preferences.validate(invalid).has("error"), "unknown provider preference rejected")
		invalid = Preferences.defaults(); invalid.expand = "yes"
		check(Preferences.validate(invalid).has("error"), "malformed preference field rejected")
		var bad_path := folder.path_join("malformed.json")
		var file := FileAccess.open(bad_path, FileAccess.WRITE); file.store_string("{broken"); file.close()
		var damaged = Browser.new(); damaged.preferences_path = bad_path; root.add_child(damaged); await settle()
		check(damaged.status.text.contains("malformed") and damaged.directories.is_empty(), "malformed settings show a useful fallback")
		check(FileAccess.get_file_as_string(bad_path) == "{broken", "startup does not overwrite malformed preferences")
		damaged.queue_free(); await settle()
		file = FileAccess.open(bad_path, FileAccess.WRITE); file.store_string("x".repeat(Preferences.MAX_BYTES + 1)); file.close()
		check(Preferences.read_file(bad_path).error.contains("64 KiB"), "oversized preferences refused")
		check(not Preferences.write_file(folder, Preferences.defaults()).is_empty(), "unwritable destination reports an error")
	browser.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "phase":"read" if reading else "write"}
	var file := FileAccess.open(folder.path_join("persistence-%s.json" % report.phase), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("DISCOVERY_PERSISTENCE " + JSON.stringify(report))
	quit(1 if not failures.is_empty() else 0)
