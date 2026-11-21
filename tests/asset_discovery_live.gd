extends SceneTree
## Explicit live metadata/UI probe. Public titles/links only; no model/image files.
const Browser = preload("res://src/discovery/browser.gd")
var browser
var started := 0
var observations := {}
var failures: Array = []
var opened: Array = []

func _initialize() -> void:
	started = Time.get_ticks_msec()
	call_deferred("_run")

func _process(_delta: float) -> bool:
	if Time.get_ticks_msec() - started > 75000:
		printerr("Live metadata probe exceeded 75 seconds."); quit(1)
	return false

func idle() -> void:
	while browser.online.loading: await process_frame
	await process_frame; await process_frame

func snapshot() -> Dictionary:
	var sources := {}
	var ids := {}
	var samples: Array = []
	for row in browser.visible_rows:
		sources[row.provider] = int(sources.get(row.provider, 0)) + 1
		ids[row.provider + ":" + row.id] = true
		if samples.size() < 6:
			samples.append({"title":row.title, "url":row.url, "source":row.provider, "formats":row.formats, "access":row.access})
	return {"listings":browser.visible_rows.size(), "unique_ids":ids.size(), "sources":sources, "statuses":browser.online.statuses.duplicate(), "message":browser.status.text, "queries":browser.online.tried.duplicate(), "samples":samples}

func _run() -> void:
	root.size = Vector2i(1240, 860)
	browser = Browser.new(); browser.preferences_path = ""; root.add_child(browser)
	browser.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	browser.page_opener = func(url): opened.append(url); return OK
	await process_frame
	observations.cold_start_offline = not browser.online.network_enabled and browser.online.rows.is_empty()
	browser.tabs.current_tab = 1
	browser.network.button_pressed = true
	browser.search_button.pressed.emit(); await idle()
	observations.initial = snapshot()
	if not browser.visible_rows.is_empty():
		browser.tree.get_root().get_first_child().select(0)
		browser.open_selected()
	observations.source_click_intercepted = opened.duplicate()
	# Explicit optional preview opt-in; request one public CDN thumbnail only.
	for row in browser.online.rows:
		if row.provider == "polyhaven" and not str(row.get("thumbnail_url", "")).is_empty():
			browser.selected = row; browser.thumbnails.button_pressed = true
			var until := Time.get_ticks_msec() + 10000
			while browser.thumbnail.message.begins_with("Loading") and Time.get_ticks_msec() < until: await process_frame
			observations.thumbnail = {"loaded":browser.thumbnail.texture != null, "message":browser.thumbnail.message, "url":row.thumbnail_url, "source":row.provider}
			browser.thumbnails.button_pressed = false
			break
	var first_ids: Array = []
	for row in browser.online.rows: first_ids.append(row.provider + ":" + row.id)
	if browser.online.has_more:
		browser.more_button.pressed.emit(); await idle()
	observations.second_batch = snapshot()
	for id in first_ids:
		var found := false
		for row in browser.online.rows:
			if row.provider + ":" + row.id == id: found = true; break
		if not found: failures.append("Second batch lost an earlier listing."); break
	browser.website.select(2); browser.search.text = "Hatsune Miku"
	browser.search_button.pressed.emit(); await idle()
	observations.name_search = snapshot()
	browser.format_filter.select(browser.Catalog.FORMATS.find("MMD")); browser.format_filter.item_selected.emit(browser.format_filter.selected); await idle()
	observations.mmd_filter = snapshot()
	for row in browser.visible_rows:
		if "MMD" not in row.formats or row.provider != "sketchfab": failures.append("Website/format filter admitted a nonmatching result.")
	browser.format_filter.select(0) # Next query uses all formats.
	# Original-script query is submitted separately; no translation service.
	browser.expand.button_pressed = false
	browser.search.text = "初音ミク"; browser.search_button.pressed.emit(); await idle()
	observations.japanese_search = snapshot()
	browser.search.text = "cancel-probe"; browser.search_button.pressed.emit()
	var deadline := Time.get_ticks_msec() + 2000
	while not is_instance_valid(browser.online._http) and browser.online.loading and Time.get_ticks_msec() < deadline: await process_frame
	var in_flight: bool = is_instance_valid(browser.online._http)
	browser.cancel_button.pressed.emit()
	await create_timer(0.2).timeout
	observations.cancel = {"request_existed":in_flight, "loading":browser.online.loading, "http_released":not is_instance_valid(browser.online._http), "message":browser.online.message}
	if browser.online.loading: failures.append("Cancellation left loading active.")
	browser.network.button_pressed = false
	for name in ["initial", "second_batch", "name_search", "japanese_search"]:
		if observations[name].listings != observations[name].unique_ids: failures.append(name + " contains repeated identities.")
	observations.failures = failures
	observations.seconds = (Time.get_ticks_msec() - started) / 1000.0
	observations.scope = "Actual metadata/UI and one explicitly enabled public CDN thumbnail; browser opening intercepted. No model download, native appearance or ownership claim. Provider availability is an observation."
	print("LIVE_METADATA_OBSERVATION " + JSON.stringify(observations))
	var file := FileAccess.open("res://output/asset-discovery-live.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(observations, "  ")); file.close()
	browser.queue_free(); await process_frame
	quit(1 if not failures.is_empty() else 0)
