extends SceneTree
const Browser = preload("res://src/discovery/browser.gd")
const Preferences = preload("res://src/discovery/preferences.gd")
const Catalog = preload("res://src/discovery/catalog.gd")
const StudioTheme = preload("res://src/studio_theme.gd")
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

func click_notice(control: Control) -> void:
	var window: Window = browser.retrieval_notice
	var point := control.get_global_rect().get_center()
	var move := InputEventMouseMotion.new(); move.position = point; move.global_position = point; window.push_input(move, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new(); event.position = point; event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT; event.pressed = pressed; window.push_input(event, true)
		await process_frame
	await settle()

func capture_notice(folder: String, phase: String) -> void:
	if DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	check(root.get_texture().get_image().save_png(folder.path_join("notice-%s.png" % phase)) == OK, "capture themed requirements notice")
	var window: Window = browser.retrieval_notice
	check(window.size.x <= root.size.x and window.size.y <= root.size.y, "requirements notice fits the viewport")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var folder: String = args[0]
	var reading := "--read" in args
	root.size = Vector2i(1240, 860); root.gui_embed_subwindows = true
	StudioTheme.set_style("light" if reading else "neon"); root.theme = StudioTheme.make_theme()
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
		await capture_notice(folder, "neon")
		browser.retrieval_notice.remember.button_pressed = true
		if DisplayServer.get_name() != "headless": await click_notice(browser.retrieval_notice.get_cancel_button())
		else: browser.retrieval_notice.canceled.emit(); await settle()
		check(opened.is_empty() and browser.dismissed_notices.is_empty(), "Cancel neither opens nor remembers dismissal")
		browser.open_page(sfm); browser.cancel(); browser.retrieval_notice.confirmed.emit(); await settle()
		check(opened.is_empty(), "cancelled pending source cannot open later")
		browser.retrieval_context = func(_provider): return "Cached local scan found Source Filmmaker folders; this may be out of date."
		browser.open_page(sfm)
		check(browser.retrieval_notice.explanation.text.contains("Cached local scan") and not browser.retrieval_notice.explanation.text.contains("is Unknown"), "injected cached detection is visible without another scan")
		if DisplayServer.get_name() != "headless":
			await click_notice(browser.retrieval_notice.remember)
			await click_notice(browser.retrieval_notice.get_ok_button())
		else: browser.retrieval_notice.remember.button_pressed = true; browser.retrieval_notice.confirmed.emit()
		browser.retrieval_notice.confirmed.emit(); await settle()
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
		await capture_notice(folder, "classic")
		browser.retrieval_notice.canceled.emit()
		browser.open_page("https://steamcommunity.com.evil.invalid/workshop/?appid=1840")
		check(opened.size() == 1 and not browser.retrieval_notice.visible, "unsafe source is rejected before notice or opener")
		browser.open_page("https://polyhaven.com/models")
		check(opened.size() == 2 and not browser.retrieval_notice.visible, "unrelated source has no invented Steam requirement")
		check(not browser.online.network_enabled, "remembered notice never enables metadata networking")
	browser.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "phase":"read" if reading else "write", "display_driver":DisplayServer.get_name(), "theme":"classic" if reading else "neon", "scope":"Notice controls, intercepted source opener and personal preferences across fresh processes. Graphical mode additionally uses pointer clicks/captures; headless mode emits control signals. No Steam account or game launched."}
	var file := FileAccess.open(folder.path_join("notices-%s.json" % report.phase), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)
