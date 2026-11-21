extends SceneTree
## Focused runtime interactions with the production controls and parsers.
const Catalog = preload("res://src/discovery/catalog.gd")
const Providers = preload("res://src/discovery/providers.gd")
const Browser = preload("res://src/discovery/browser.gd")
const StudioTheme = preload("res://src/studio_theme.gd")
const DiscoveryWindow = preload("res://src/discovery/window.gd")
var checks := 0
var failures: Array = []
var browser
var background: Panel
var requests: Array = []
var opened: Array = []
var used: Array = []
var mode := "normal"
var started := 0

func _initialize() -> void:
	started = Time.get_ticks_msec()
	call_deferred("_run")

func _process(_delta: float) -> bool:
	if Time.get_ticks_msec() - started > 70000:
		printerr("FAIL: discovery runtime test deadline"); quit(1)
	return false

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition: failures.append(label); printerr("FAIL: " + label)

func settle() -> void:
	await process_frame; await process_frame; await process_frame

func click_at(point: Vector2) -> void:
	var move := InputEventMouseMotion.new(); move.position = point; move.global_position = point; root.push_input(move, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new(); event.button_index = MOUSE_BUTTON_LEFT
		event.position = point; event.global_position = point; event.pressed = pressed
		root.push_input(event, true)
		await process_frame
	await settle()

func click_control(control: Control) -> void:
	await click_at(control.get_global_rect().get_center())

func capture_layouts() -> void:
	if DisplayServer.get_name() == "headless": return
	for style in ["neon", "light", "dark"]:
		StudioTheme.set_style(style); root.theme = StudioTheme.make_theme()
		background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee"))
		for dimensions in [Vector2i(1240, 860), Vector2i(960, 700)]:
			root.size = dimensions; await settle()
			await RenderingServer.frame_post_draw
			var image := root.get_texture().get_image()
			check(image.save_png("res://output/discovery-%s-%d.png" % [style, dimensions.x]) == OK, "capture %s layout at %d" % [style, dimensions.x])
			var boundary := root.get_visible_rect().end.x
			check(browser.tree.get_global_rect().end.x <= boundary + 1 and browser.more_button.get_global_rect().end.x <= boundary + 1, "results and paging fit %s at %d" % [style, dimensions.x])
	root.size = Vector2i(1240, 860); StudioTheme.set_style("neon"); root.theme = StudioTheme.make_theme(); await settle()
	background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee"))

func wait_idle() -> void:
	var deadline := Time.get_ticks_msec() + 10000
	while browser.online.loading and Time.get_ticks_msec() < deadline: await process_frame
	check(not browser.online.loading, "online request completes within deadline")
	await settle()

func bytes(value) -> PackedByteArray:
	return JSON.stringify(value).to_utf8_buffer()

func poly_fixture() -> Dictionary:
	var data := {}
	for index in 180: data["prop_%03d" % index] = {"name":"Prop %03d" % index, "type":2, "tags":["furniture"], "thumbnail_url":"https://example.invalid/not-fetched.png"}
	return data

func sketch_fixture(url: String) -> Dictionary:
	var results: Array = []
	var page := 2 if url.contains("cursor=2") else 1
	var is_query := url.contains("&q=")
	for index in 24:
		var id := "s%d_%02d" % [page, index]
		var title := "Hatsune Miku PMX %02d" % index if is_query else "SFM model %02d" % index
		if is_query and index == 0: title = "Hatsune Miku"
		if is_query and index == 1: title = "初音ミク VRM"
		results.append({"uid":id, "name":title, "viewerUrl":"https://sketchfab.com/3d-models/" + id, "tags":[{"name":"MMD" if is_query else "SFM"}], "isDownloadable":index % 2 == 0})
	# Provider repeats a record; suppression must use identity, not title.
	results.append(results[0].duplicate(true))
	var duplicate_page: Dictionary = results[0].duplicate(true); duplicate_page.uid = "different-id-same-page"
	results.append(duplicate_page)
	return {"results":results, "next":Providers.SKETCH_URL + "&cursor=2" if page == 1 else null}

func bowl_fixture() -> PackedByteArray:
	var xml := "<?xml version=\"1.0\"?><rss version=\"2.0\"><channel>"
	for index in 25: xml += "<item><title>初音ミク PMX %02d</title><link>https://bowlroll.net/file/%d</link><description>Metadata only</description></item>" % [index, index + 100]
	return (xml + "</channel></rss>").to_utf8_buffer()

func fake_transport(source: String, url: String, _token: int) -> Dictionary:
	requests.append({"source":source, "url":url})
	var request_mode := mode
	await process_frame
	if request_mode == "slow": await create_timer(0.3).timeout
	if request_mode == "unavailable" and source == "sketchfab": return {"status":403, "body":"Access denied".to_utf8_buffer()}
	if request_mode == "malformed" and source == "sketchfab": return {"status":200, "body":"{broken".to_utf8_buffer()}
	if request_mode == "timeout": return {"error":"Network timeout; provider unavailable."}
	if request_mode == "throttled": return {"status":429, "headers":["Retry-After: 120"], "body":"Rate limit".to_utf8_buffer()}
	if source == "polyhaven": return {"status":200, "body":bytes(poly_fixture())}
	if source == "bowlroll": return {"status":200, "body":bowl_fixture()}
	return {"status":200, "body":bytes(sketch_fixture(url))}

func _run() -> void:
	# Metadata parsers and safe outbound URLs, independent of UI/network availability.
	check(Catalog.variations("Hatsune Miku") == ["Hatsune Miku", "hatsune miku", "miku hatsune", "初音ミク", "初音未来", "hatsune", "miku"], "deterministic full/reordered/alias/individual variations")
	check(Catalog.variations("Hatsune Miku", false) == ["Hatsune Miku"], "exact-only query opt-out")
	check("初音ミク" in Catalog.variations("Ｈａｔｓｕｎｅ　Ｍｉｋｕ"), "width normalization finds documented alias")
	check("Hatsune Miku" in Catalog.variations("初音ミク"), "original-script alias expansion")
	check(Catalog.variations("Unlisted Person").size() < 7, "unknown names are not translated or invented")
	check(Catalog.local_format("same.mdl") == ["Source MDL"], "local MDL never claims SFM/GMod compatibility")
	check(Catalog.formats("objectification VRM SFM PMX") == ["MMD", "SFM", "VRM"], "format words use boundaries")
	check(not Catalog.safe_page("https://bowlroll.net.evil.invalid/file/1"), "reject provider lookalike hostname")
	check(not Catalog.safe_page("file:///C:/Windows/test.exe"), "reject local execution URL")
	check(not Catalog.safe_page("https://sketchfab.com@evil.invalid/model"), "reject userinfo hostname trick")
	check(Providers.parse("sketchfab", bytes({"results":[], "next":"https://evil.invalid/cursor"})).has("error"), "reject cross-host cursor")
	check(Providers.parse("sketchfab", bytes({"results":"oops"})).has("error"), "reject malformed result shape")
	check(Providers.parse("polyhaven", "[]".to_utf8_buffer()).has("error"), "reject non-object JSON")
	check(Providers.parse("polyhaven", "{broken".to_utf8_buffer()).has("error"), "reject malformed JSON")
	check(Providers.parse("polyhaven", bytes({"x":{"name":"Invalid type", "type":{}}})).has("error"), "malformed field type does not reach unsafe numeric cast")
	check(Providers.parse("bowlroll", "<html>challenge</html>".to_utf8_buffer()).has("error"), "RSS challenge is unavailable, not zero results")
	check(Providers.parse("bowlroll", "<!DOCTYPE html><html>directory</html>".to_utf8_buffer()).error.contains("web page instead of RSS"), "retired feed gives a plain website fallback error")
	check(Providers.parse("bowlroll", "<rss><item>".to_utf8_buffer()).has("error"), "truncated RSS is rejected")
	check(Providers.parse("bowlroll", bowl_fixture()).get("rows", []).size() == 25, "parse Japanese RSS titles/links")
	var metadata: Dictionary = Providers.parse("sketchfab", bytes(sketch_fixture(Providers.SKETCH_URL)))
	check(metadata.rows[0].access == ["Preview", "Downloadable"], "explicit viewer/download metadata labels")
	check(metadata.rows[1].access == ["Preview", "Unknown"], "missing/false download evidence does not claim preview-only")
	var protected_fixture := sketch_fixture(Providers.SKETCH_URL)
	protected_fixture.results[0].isProtected = true
	check("Password" in Providers.parse("sketchfab", bytes(protected_fixture)).rows[0].access, "password label requires explicit protected metadata")
	check("Unknown" in Providers.parse("polyhaven", bytes(poly_fixture())).rows[0].access, "public listing alone leaves access Unknown")
	var hostile: Dictionary = sketch_fixture(Providers.SKETCH_URL)
	hostile.results[0].viewerUrl = "https://evil.invalid/asset.exe"
	check(Providers.parse("sketchfab", bytes(hostile)).rows.size() == 25, "unsafe result URL is skipped")
	check(Catalog.website_url("steam_sfm", "A&B").contains("appid=1840&searchtext=A%26B"), "Steam search has separate app and encoded query")
	check(Catalog.website_url("bowlroll", "初音ミク").contains("%E5"), "Japanese website query encoded")
	root.size = Vector2i(1240, 860)
	root.theme = StudioTheme.make_theme()
	background = Panel.new(); background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.add_theme_stylebox_override("panel", StudioTheme.surface("f4f7fb", "dce5ee")); root.add_child(background)
	var margin := MarginContainer.new(); margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); root.add_child(margin)
	browser = Browser.new(); browser.preferences_path = ""; margin.add_child(browser)
	browser.online.transport = fake_transport
	browser.page_opener = func(url): opened.append(url); return OK
	browser.local_file_selected.connect(func(path): used.append(path))
	await settle()
	check(browser.tabs.get_tab_title(0) == "Local" and browser.tabs.get_tab_title(1) == "Online", "separate Local/Online tabs")
	check(requests.is_empty() and not browser.network.button_pressed, "construction is offline and sends nothing")
	# FileDialog selection route and real filesystem enumeration on synthetic empty files.
	var fixture := ProjectSettings.globalize_path("res://output/discovery-local-初音")
	DirAccess.make_dir_recursive_absolute(fixture.path_join("nested"))
	for name in ["Hatsune Miku.pmx", "voice.wav", "avatar.vrm", "same.mdl", "nested/room.glb", "other.fbx"]:
		var file := FileAccess.open(fixture.path_join(name), FileAccess.WRITE); file.store_string("synthetic filename fixture; never loaded"); file.close()
	browser.picker.dir_selected.emit(fixture)
	var local_deadline := Time.get_ticks_msec() + 4000
	while browser.local.loading and Time.get_ticks_msec() < local_deadline: await process_frame
	await settle()
	check(browser.local.rows.size() == 5, "selected directory recurses and ignores audio")
	check(requests.is_empty(), "local scan remains offline")
	browser.search.text = "Miku"; browser.search.text_changed.emit("Miku"); await settle()
	check(browser.visible_rows.size() == 1 and browser.visible_rows[0].title == "Hatsune Miku.pmx", "filename search updates real rows")
	browser.format_filter.select(Catalog.FORMATS.find("VRM")); browser.format_filter.item_selected.emit(browser.format_filter.selected); await settle()
	check(browser.visible_rows.is_empty(), "combined filename/format filtering")
	browser.search.text = ""; browser.search.text_changed.emit(""); await settle()
	check(browser.visible_rows.size() == 1 and browser.visible_rows[0].title == "avatar.vrm", "clearing search retains format filter")
	var item: TreeItem = browser.tree.get_root().get_first_child(); item.select(0); browser.tree.item_selected.emit(); await settle()
	browser.use_button.pressed.emit()
	check(used == [fixture.path_join("avatar.vrm")], "explicit local selection emits path without opening model")
	check(opened.is_empty(), "local selection never opens or executes a file")
	browser.local.start([fixture]); browser.cancel_button.pressed.emit(); await settle()
	check(not browser.local.loading and browser.local.message.contains("cancelled"), "Cancel stops local enumeration")
	browser.local.start([fixture.path_join("missing")]); await settle()
	check(browser.local.message.contains("Cannot read"), "missing directory shows useful error")
	# Online controls: tab alone does not request; permission checkbox + Search does.
	browser.tabs.current_tab = 1; await settle()
	browser.format_filter.select(0)
	await click_control(browser.search_button)
	check(requests.is_empty() and browser.status.text.contains("Enable online"), "online Search stays optional while disabled")
	browser.network.button_pressed = true
	browser.search_button.pressed.emit(); await wait_idle()
	check(browser.visible_rows.size() == 100, "initial discovery targets 100 results")
	var sources := {}
	var identities := {}
	for row in browser.visible_rows: sources[row.provider] = true; identities[Catalog.identity(row)] = true
	check(sources.size() == 3, "initial discovery mixes all working metadata providers")
	check(identities.size() == 100, "source identities suppress duplicated provider entries")
	check(browser.online.statuses.steam_sfm.contains("key") and browser.online.statuses.sfmlab.contains("scraping"), "website-only providers disclose restrictions")
	await capture_layouts()
	var first_batch: Array = browser.online.rows.duplicate(true)
	var previous_last: TreeItem = browser.tree.get_root().get_child(70)
	browser.tree.scroll_to_item(previous_last); await settle()
	browser.more_button.pressed.emit(); await wait_idle()
	check(browser.online.rows.size() == 200, "on-demand second batch targets another 100")
	check(browser.online.rows.slice(0, 100) == first_batch, "pagination preserves previous batch order")
	identities.clear()
	for row in browser.online.rows: identities[Catalog.identity(row)] = true
	check(identities.size() == 200, "pagination removes repeated IDs without merging same titles")
	# Actual viewport pointer events traverse the Tree's ordinary click handler.
	item = browser.tree.get_root().get_first_child(); item.select(0)
	browser.tree.scroll_to_item(item); await settle()
	var area: Rect2 = browser.tree.get_item_area_rect(item, 0)
	await click_at(browser.tree.global_position + area.position + Vector2(30, area.size.y / 2))
	check(opened.size() == 1 and opened[0] == item.get_metadata(0).url, "online result click opens only the source page")
	browser.open_page("javascript:alert(1)")
	check(opened.size() == 1, "unsafe schemes never reach browser opener")
	# Exact ranking, visible expansion, query reset, website/type combined filters.
	browser.search.text = "Hatsune Miku"; browser.search_button.pressed.emit(); await wait_idle()
	check(not browser.visible_rows.is_empty() and browser.visible_rows[0].title == "Hatsune Miku", "exact original title ranks ahead of expansions")
	check(browser.disclosure.text.contains("初音ミク") and browser.disclosure.text.contains("API queries sent"), "expanded searches and actual API queries disclosed")
	browser.website.select(3); browser.website.item_selected.emit(3); await wait_idle()
	check(browser.visible_rows.size() == 25 and browser.online.rows[0].provider == "bowlroll", "website filter resets pagination to BowlRoll feed")
	browser.format_filter.select(Catalog.FORMATS.find("VRM")); browser.format_filter.item_selected.emit(browser.format_filter.selected); await wait_idle()
	check(browser.visible_rows.is_empty(), "combined website and format filters can honestly return no listings")
	browser.website.select(4); browser.website.item_selected.emit(4); await wait_idle()
	check(browser.visible_rows.is_empty() and not browser.online.has_more, "Steam website-only does not invent model results")
	check(browser.status.text.contains("website search only") and not browser.website_button.disabled, "website-only provider exposes immediate search action")
	var opens_before := opened.size()
	await click_control(browser.website_button)
	check(opened.size() == opens_before + 1 and opened[-1].contains("appid=1840"), "website search action uses selected provider and query")
	browser.open_page(Catalog.website_url("steam_sfm", browser.search.text))
	check(opened[-1].contains("appid=1840"), "website-only source search opens through same safe boundary")
	# Unavailable/malformed providers leave partial results and actionable errors.
	browser.website.select(0); browser.format_filter.select(0); browser.search.text = ""; mode = "unavailable"
	browser.search_button.pressed.emit(); await wait_idle()
	check(browser.visible_rows.size() == 100 and browser.online.statuses.sketchfab.contains("403"), "unavailable provider preserves working sources")
	check(browser.status.text.contains("Sketchfab") and browser.status.text.contains("403"), "provider failure visible outside collapsed details")
	mode = "malformed"; browser.search_button.pressed.emit(); await wait_idle()
	check(browser.online.statuses.sketchfab.contains("Malformed") and browser.visible_rows.size() == 100, "malformed provider response leaves useful partial feed")
	# Cancellation during an awaited response, then supersede before it can return.
	mode = "slow"; browser.website.select(2); browser.search.text = "old"; browser.search_button.pressed.emit()
	while not browser.online.loading: await process_frame
	await settle()
	check(browser.activity.visible, "loading has a real indeterminate activity indicator")
	browser.cancel_button.pressed.emit(); await settle()
	check(not browser.online.loading and browser.status.text.contains("Cancelled"), "Cancel immediately leaves loading state")
	check(not browser.activity.visible, "Cancel hides the activity indicator")
	mode = "normal"; browser.search.text = "Hatsune Miku"; browser.search_button.pressed.emit(); await wait_idle()
	await create_timer(0.4).timeout; await settle()
	check(browser.online.query == "Hatsune Miku" and not browser.visible_rows.is_empty() and browser.visible_rows[0].title == "Hatsune Miku", "late cancelled response cannot replace newer search")
	# A later batch's exact hit must outrank the broad matches already displayed.
	var broad := {"id":"old-broad", "title":"Miku accessory", "provider":"sketchfab", "url":"https://sketchfab.com/3d-models/old-broad", "formats":[], "access":["Unknown"], "evidence":"fixture"}
	browser.online.rows = [broad]; browser.online._seen.clear()
	browser.online._pool.clear(); browser.online._offsets.clear()
	browser.online._sketch_streams = [{"query":"Hatsune Miku", "url":Providers.sketch_url("Hatsune Miku")}]
	browser.online.has_more = true; browser.more_button.pressed.emit(); await wait_idle()
	check(browser.visible_rows[0].title == "Hatsune Miku" and broad in browser.visible_rows, "later exact hits move ahead of earlier broad matches")
	browser.page_opener = func(_url): return ERR_CANT_OPEN
	browser.open_page("https://sketchfab.com/3d-models/test"); browser._schedule_refresh(); await settle()
	check(browser.status.text.contains("Could not open your default browser"), "browser launch error survives deferred UI refresh")
	browser.page_opener = func(url): opened.append(url); return OK
	mode = "timeout"; browser.search_button.pressed.emit(); await wait_idle()
	check(browser.visible_rows.is_empty() and browser.status.text.contains("timeout"), "timeout has an actionable unavailable state")
	mode = "throttled"; browser.search_button.pressed.emit(); await wait_idle()
	check(browser.online.statuses.sketchfab.contains("120 seconds"), "429 uses provider Retry-After without retrying")
	var before_retry := requests.size()
	mode = "normal"; browser.search_button.pressed.emit(); await wait_idle()
	check(requests.size() == before_retry and browser.online.statuses.sketchfab.contains("Rate limited"), "rate-limit cooldown survives a new Search")
	mode = "slow"; browser.search_button.pressed.emit(); browser.network.button_pressed = false; await settle()
	check(not browser.online.loading and not browser.online.network_enabled and browser.more_button.disabled, "disabling online access cancels requests")
	var request_count := requests.size()
	browser.search_button.pressed.emit(); await create_timer(0.7).timeout
	check(requests.size() == request_count, "network off prevents subsequent metadata requests")
	for style in ["neon", "light", "dark"]:
		StudioTheme.set_style(style); root.theme = StudioTheme.make_theme(); await settle()
		check(browser.tree.is_visible_in_tree() and browser.search.is_visible_in_tree(), "controls remain usable in " + style + " theme")
	# No files were interpreted or changed by scanning/selecting/filtering.
	check(FileAccess.get_file_as_string(fixture.path_join("avatar.vrm")) == "synthetic filename fixture; never loaded", "local original fixture remains unchanged")
	# Public host wrapper launches/cancels independently of app.gd.
	var popup: Window = DiscoveryWindow.open(root, Callable(), {"preferences_path":""})
	await settle()
	var panel = popup.get_meta("discovery_panel")
	check(panel.tabs.current_tab == 0 and not panel.online.network_enabled, "standalone integration window starts offline")
	popup.close_requested.emit(); await settle()
	check(not is_instance_valid(popup), "closing integration window frees its discovery services")
	browser.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "requests":requests.size(), "browser_opens_intercepted":opened.size(), "display_driver":DisplayServer.get_name(), "scope":"Production UI, filesystem scan and metadata fixtures; rendered layout captures only when graphical. No live-provider or native-model appearance claim."}
	var file := FileAccess.open("res://output/asset-discovery-test.json", FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("ASSET_DISCOVERY_RESULT " + JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)
