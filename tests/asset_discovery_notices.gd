extends SceneTree
const Browser = preload("res://src/discovery/browser.gd")
const Preferences = preload("res://src/discovery/preferences.gd")
const Catalog = preload("res://src/discovery/catalog.gd")
var browser
var checks := 0
var failures: Array = []
var opened: Array = []

func _initialize() -> void:
	create_timer(20).timeout.connect(func(): quit(2))
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); printerr("FAIL: " + label)

func settle() -> void: await process_frame; await process_frame

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var folder: String = args[0]
	var reading := "--read" in args
	var settings := folder.path_join("notice-preferences.json")
	browser = Browser.new(); browser.preferences_path = settings; root.add_child(browser)
	browser.page_opener = func(url): opened.append(url); return OK
	await settle()
	var sfm := Catalog.website_url("steam_sfm", "Hatsune Miku")
	var gmod := Catalog.website_url("steam_gmod", "Miku")
	if not reading:
		browser.open_page(sfm); await settle()
		check(browser.retrieval_notice.visible and opened.is_empty(), "Steam source waits for explicit confirmation")
		check(browser.retrieval_notice.explanation.text.contains("Unknown") and browser.retrieval_notice.explanation.text.contains("not proof of ownership"), "unknown local detection and ownership limit are explicit")
		browser.retrieval_notice.remember.button_pressed = true
		browser.retrieval_notice.canceled.emit(); await settle()
		check(opened.is_empty() and browser.dismissed_notices.is_empty(), "Cancel neither opens nor remembers dismissal")
		browser.open_page(sfm); browser.cancel(); browser.retrieval_notice.confirmed.emit(); await settle()
		check(opened.is_empty(), "cancelled pending source cannot open later")
		browser.retrieval_context = func(_provider): return "Cached local scan found Source Filmmaker folders; this may be out of date."
		browser.open_page(sfm)
		check(browser.retrieval_notice.explanation.text.contains("Cached local scan") and not browser.retrieval_notice.explanation.text.contains("is Unknown"), "injected cached detection is visible without another scan")
		browser.retrieval_notice.remember.button_pressed = true
		browser.retrieval_notice.confirmed.emit(); browser.retrieval_notice.confirmed.emit(); await settle()
		check(opened == [sfm] and browser.dismissed_notices.get("steam_sfm") == true, "confirm opens once and remembers only selected source")
		check(Preferences.read_file(settings).data.dismissed_notices == {"steam_sfm":true}, "remembered choice saved using personal preferences")
		var old := Preferences.defaults(); old.erase("dismissed_notices")
		check(Preferences.validate(old).data.dismissed_notices.is_empty(), "older preference files remain valid")
		var invalid := Preferences.defaults(); invalid.dismissed_notices = {"invented":true}
		check(Preferences.validate(invalid).has("error"), "unsupported dismissal entries rejected")
	else:
		browser.open_page(sfm); await settle()
		check(opened == [sfm] and not browser.retrieval_notice.visible, "fresh process remembers source-specific dismissal")
		browser.open_page(gmod); await settle()
		check(opened.size() == 1 and browser.retrieval_notice.visible, "other source still requires its own notice")
		browser.retrieval_notice.canceled.emit()
		browser.open_page("https://steamcommunity.com.evil.invalid/workshop/?appid=1840")
		check(opened.size() == 1 and not browser.retrieval_notice.visible, "unsafe source is rejected before notice or opener")
		browser.open_page("https://polyhaven.com/models")
		check(opened.size() == 2 and not browser.retrieval_notice.visible, "unrelated source has no invented Steam requirement")
		check(not browser.online.network_enabled, "remembered notice never enables metadata networking")
	browser.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "phase":"read" if reading else "write", "scope":"Actual notice controls, intercepted source opener, and personal preferences across fresh processes; no Steam account or game launched."}
	var file := FileAccess.open(folder.path_join("notices-%s.json" % report.phase), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)
