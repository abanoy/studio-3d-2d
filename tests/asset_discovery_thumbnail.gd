extends SceneTree
const Thumbnail = preload("res://src/discovery/thumbnail.gd")
const Browser = preload("res://src/discovery/browser.gd")
var checks := 0
var failures: Array = []
var requests := 0
var reply_status := 200
var slow := false
var png: PackedByteArray

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label); printerr("FAIL: " + label)

func _initialize() -> void:
	create_timer(20).timeout.connect(func(): quit(2))
	call_deferred("run")

func fake(_url: String) -> Dictionary:
	requests += 1
	var status := reply_status
	if slow: await create_timer(0.1).timeout
	else: await process_frame
	return {"status":status, "body":png}

func settle() -> void:
	await process_frame; await process_frame

func run() -> void:
	var image := Image.create(4, 3, false, Image.FORMAT_RGB8); image.fill(Color.CORNFLOWER_BLUE)
	png = image.save_png_to_buffer()
	for body in [png, image.save_jpg_to_buffer(), image.save_webp_to_buffer()]:
		var decoded := Thumbnail.decode(body)
		check(decoded.has("image") and decoded.image.get_size() == Vector2i(96, 96), "decode bounded generated PNG/JPEG/WebP")
	check(Thumbnail.decode("<html>challenge</html>".to_utf8_buffer()).has("error"), "malformed/non-image response rejected")
	var large := PackedByteArray(); large.resize(1024 * 1024 + 1)
	check(Thumbnail.decode(large).error.contains("1 MiB"), "encoded image byte limit enforced")
	var oversized := Image.create(1025, 2, false, Image.FORMAT_RGB8).save_png_to_buffer()
	check(Thumbnail.decode(oversized).error.contains("1024"), "oversized header refused before image decoding")
	check(not Thumbnail.safe_url("https://cdn.polyhaven.com.evil.invalid/asset_img/thumbs/a.png"), "lookalike image host rejected")
	check(not Thumbnail.safe_url("https://media.sketchfab.com/models/a/model.glb"), "model URL cannot become thumbnail request")
	var thumb = Thumbnail.new(); thumb.transport = fake; root.add_child(thumb)
	var url := "https://cdn.polyhaven.com/asset_img/thumbs/test.png"
	thumb.load_url(url); await settle()
	check(requests == 0, "preview off makes no requests")
	thumb.set_enabled(true); await thumb.load_url(url)
	check(thumb.texture != null and requests == 1, "enabled selected thumbnail loads")
	thumb.cancel(); thumb._url = ""; await thumb.load_url(url)
	check(requests == 1 and thumb.texture != null, "memory cache avoids another image request")
	for index in 9: await thumb.load_url(url + "?cache=%d" % index)
	check(thumb._cache.size() == 8, "thumbnail memory cache stays bounded to eight entries")
	reply_status = 503; await thumb.load_url(url + "?failed=1")
	check(thumb.texture == null and thumb.message.contains("unavailable"), "image outage gives a useful placeholder")
	var before := requests; slow = true; reply_status = 200
	thumb.load_url(url + "?slow=1"); thumb.set_enabled(false)
	await create_timer(0.8).timeout
	check(thumb.texture == null and not thumb.enabled, "disabled preview discards a late image")
	thumb.set_enabled(true); slow = false; reply_status = 429
	await thumb.load_url(url + "?rate=1"); before = requests
	await thumb.load_url(url + "?rate=2")
	check(requests == before and thumb.message.contains("rate limit"), "429 pauses further image requests without retry")
	thumb.queue_free(); await settle()
	# Production panel opts in separately and only previews the selected result.
	var panel = Browser.new(); panel.preferences_path = ""; root.add_child(panel)
	panel.thumbnail.transport = fake; reply_status = 200
	panel.page_opener = func(_url): return OK
	panel.tabs.current_tab = 1; panel.network.button_pressed = true
	panel.online.rows = [{"id":"preview", "title":"MMD fixture", "provider":"polyhaven", "url":"https://polyhaven.com/a/test", "keywords":"MMD", "formats":["MMD"], "access":["Unknown"], "evidence":"fixture", "thumbnail_url":url}]
	panel._schedule_refresh(); await settle()
	var item: TreeItem = panel.tree.get_root().get_first_child(); item.select(0); panel.tree.item_selected.emit(); await settle()
	before = requests
	check(not panel.thumbnails.button_pressed and not panel.preview.get_parent().visible, "panel thumbnail preview defaults off")
	panel.thumbnails.button_pressed = true
	await create_timer(0.1).timeout; await settle()
	check(panel.preview.texture != null and requests == before + 1, "panel checkbox loads only selected-item image")
	check(item.get_text(2).contains("inferred") and panel.details.text.contains("inferred"), "online format hints visibly disclose inference")
	slow = true; panel.selected.thumbnail_url = url + "?cancel=1"; panel._update_thumbnail(); await settle()
	check(panel.thumbnail.loading and not panel.cancel_button.disabled, "Cancel is available during a thumbnail request")
	panel.cancel_button.pressed.emit(); await create_timer(0.8).timeout; await settle()
	check(not panel.thumbnail.loading and panel.preview.texture == null, "panel Cancel rejects a stale thumbnail response")
	panel.network.button_pressed = false; await settle()
	check(panel.preview.texture == null and not panel.preview.get_parent().visible, "network opt-out clears thumbnail and cancels loader")
	panel.queue_free(); await settle()
	var report := {"checks":checks, "failures":failures, "scope":"Generated image buffers and injected image transport; no live artwork downloaded."}
	var file := FileAccess.open(OS.get_cmdline_user_args()[0].path_join("thumbnail-result.json"), FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("DISCOVERY_THUMBNAILS " + JSON.stringify(report))
	quit(1 if not failures.is_empty() else 0)
