extends SceneTree
## Native Tree scrolling, guarded automatic batches and failure recovery.
const Browser = preload("res://src/discovery/browser.gd")
var browser
var failures: Array = []
var checks := 0
var requests := 0
var mode := "normal"

func _initialize() -> void: call_deferred("_run")

func check(value: bool, label: String) -> void:
	checks += 1
	if not value: failures.append(label); printerr("FAIL: " + label)

func settle() -> void:
	await process_frame; await process_frame; await process_frame

func idle() -> void:
	var deadline := Time.get_ticks_msec() + 6000
	while browser.online.loading and Time.get_ticks_msec() < deadline: await process_frame
	check(not browser.online.loading, "batch ends within deadline")
	await settle()

func transport(_source: String, _url: String, _token: int) -> Dictionary:
	requests += 1
	await process_frame
	if mode == "malformed": return {"status":200, "body":"{bad".to_utf8_buffer()}
	if mode == "unavailable": return {"status":403, "body":"Unavailable".to_utf8_buffer()}
	var records := {}
	for index in 500: records["prop_%03d" % index] = {"name":"Prop %03d" % index, "type":2}
	return {"status":200, "body":JSON.stringify(records).to_utf8_buffer()}

func wheel() -> void:
	var point: Vector2 = browser.tree.get_global_rect().get_center()
	var move := InputEventMouseMotion.new(); move.position = point; move.global_position = point; root.push_input(move, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_WHEEL_DOWN; event.pressed = pressed
		event.position = point; event.global_position = point
		root.push_input(event, true)

func scroll_batch(expected: int) -> void:
	var deadline := Time.get_ticks_msec() + 6000
	while browser.online.rows.size() < expected and Time.get_ticks_msec() < deadline:
		wheel(); await process_frame
	await idle()
	check(browser.online.rows.size() == expected, "native wheel reaches bottom and loads %d rows" % expected)

func _run() -> void:
	root.size = Vector2i(1240, 1000)
	var margin := MarginContainer.new(); margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); root.add_child(margin)
	browser = Browser.new(); browser.preferences_path = ""; margin.add_child(browser)
	browser.online.transport = transport
	browser.page_opener = func(_url): return OK
	browser.tabs.current_tab = 1; browser.website.select(1); browser.network.button_pressed = true
	browser.run_search(); await idle()
	check(browser.online.rows.size() == 100 and requests == 1, "initial batch remains bounded")
	check(is_instance_valid(browser._scrollbar), "find native Tree vertical scrollbar")
	if not is_instance_valid(browser._scrollbar): finish(); return
	var bar: VScrollBar = browser._scrollbar
	# Headless Godot does not draw Tree's internal scrollbar ranges. Exercise the
	# same input/guard path with explicit ranges; graphical mode uses native ones.
	if DisplayServer.get_name() == "headless": bar.max_value = 3000; bar.page = 400
	bar.value = bar.max_value - bar.page; await settle()
	check(browser.online.rows.size() == 100, "programmatic scrolling never requests a batch")
	var click := InputEventMouseButton.new(); click.button_index = MOUSE_BUTTON_LEFT; click.pressed = true
	browser._scroll_intent(click); await settle()
	check(browser.online.rows.size() == 100, "ordinary result click is not scroll intent")
	wheel(); browser.cancel(); await settle()
	check(browser.online.rows.size() == 100, "Cancel invalidates deferred scroll intent")
	wheel(); browser.network.button_pressed = false; browser.network.button_pressed = true; await settle()
	check(browser.online.rows.size() == 100, "off/on invalidates pending automatic batch")
	await scroll_batch(200)
	await settle(); await settle()
	check(browser.online.rows.size() == 200, "layout and idle do not chain automatic batches")
	await scroll_batch(300)
	await scroll_batch(400)
	await scroll_batch(500)
	check(not browser.online.has_more and requests == 1, "exhausted cache makes no extra metadata requests")
	for index in 10: wheel(); await process_frame
	check(requests == 1 and browser.online.rows.size() == 500, "bottom after exhaustion stays quiet")
	for bad_mode in ["malformed", "unavailable"]:
		mode = bad_mode; browser.online._poly_cache.clear(); browser.online._poly_cached_at = -1000000; browser.run_search(); await idle()
		var before := requests
		for index in 10: wheel(); await process_frame
		check(browser.online.rows.is_empty() and not browser.online.has_more and requests == before, bad_mode + " provider stops automatic retrieval")
		check(browser.status.text.contains("Malformed" if bad_mode == "malformed" else "403"), bad_mode + " has an honest visible error")
	finish()

func finish() -> void:
	browser.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "requests":requests, "display_driver":DisplayServer.get_name(), "scope":"Production wheel-input and paging guards with synthetic metadata. Headless ranges are explicitly supplied because Tree draws no scrollbars; native graphical scrolling is qualified only with --graphical."}
	var file := FileAccess.open("res://output/asset-discovery-paging.json", FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)
