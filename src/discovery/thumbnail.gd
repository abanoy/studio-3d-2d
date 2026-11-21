extends Node
## Optional selected-item preview only. Never follows redirects or model URLs.
signal changed
const USER_AGENT = preload("res://src/discovery/providers.gd").USER_AGENT
var enabled := false
var loading := false
var texture: Texture2D
var message := ""
var transport: Callable
var _generation := 0
var _http: HTTPRequest
var _url := ""
var _cache := {}
var _last_request := -100000
var _paused := false

static func safe_url(url: String) -> bool:
	if url.contains("\n") or url.contains("\r"): return false
	var path := url.get_slice("?", 0)
	if path.get_extension().to_lower() not in ["png", "jpg", "jpeg", "webp"]: return false
	return url.begins_with("https://cdn.polyhaven.com/asset_img/thumbs/") or (url.begins_with("https://media.sketchfab.com/models/") and path.contains("/thumbnails/"))

static func dimensions(body: PackedByteArray) -> Dictionary:
	if body.size() >= 24 and body.slice(0, 8).hex_encode() == "89504e470d0a1a0a":
		var w := 0; var h := 0
		for index in 4: w = (w << 8) | body[16 + index]; h = (h << 8) | body[20 + index]
		return {"size":Vector2i(w, h), "format":"png"}
	if body.size() >= 30 and body.slice(0, 4).get_string_from_ascii() == "RIFF" and body.slice(8, 12).get_string_from_ascii() == "WEBP":
		var kind := body.slice(12, 16).get_string_from_ascii()
		if kind == "VP8X": return {"size":Vector2i(1 + body[24] + (body[25] << 8) + (body[26] << 16), 1 + body[27] + (body[28] << 8) + (body[29] << 16)), "format":"webp"}
		if kind == "VP8L" and body[20] == 47: return {"size":Vector2i(1 + body[21] + ((body[22] & 63) << 8), 1 + (body[22] >> 6) + (body[23] << 2) + ((body[24] & 15) << 10)), "format":"webp"}
		if kind == "VP8 " and body.slice(23, 26).hex_encode() == "9d012a": return {"size":Vector2i((body[26] + (body[27] << 8)) & 16383, (body[28] + (body[29] << 8)) & 16383), "format":"webp"}
	if body.size() >= 4 and body[0] == 255 and body[1] == 216:
		var index := 2
		while index + 4 < body.size():
			if body[index] != 255: break
			index += 1
			while index < body.size() and body[index] == 255: index += 1
			if index + 3 >= body.size(): break
			var marker := body[index]; index += 1
			var length := (body[index] << 8) | body[index + 1]
			if length < 2 or index + length > body.size(): break
			if marker in [192,193,194,195,197,198,199,201,202,203,205,206,207] and length >= 7:
				return {"size":Vector2i((body[index + 5] << 8) | body[index + 6], (body[index + 3] << 8) | body[index + 4]), "format":"jpg"}
			index += length
	return {}

static func decode(body: PackedByteArray) -> Dictionary:
	if body.size() > 1024 * 1024: return {"error":"Thumbnail exceeds 1 MiB."}
	var header := dimensions(body)
	if header.is_empty(): return {"error":"Thumbnail is not a supported PNG, JPEG or WebP image."}
	if header.size.x <= 0 or header.size.y <= 0 or header.size.x > 1024 or header.size.y > 1024: return {"error":"Thumbnail dimensions exceed 1024 pixels."}
	var img := Image.new()
	var error: int = img.load_png_from_buffer(body) if header.format == "png" else img.load_jpg_from_buffer(body) if header.format == "jpg" else img.load_webp_from_buffer(body)
	if error != OK or img.is_empty(): return {"error":"Thumbnail image could not be decoded."}
	img.resize(96, 96, Image.INTERPOLATE_BILINEAR)
	return {"image":img}

func set_enabled(value: bool) -> void:
	if enabled == value: return
	enabled = value
	if not enabled: cancel(); _url = ""; texture = null; message = ""; changed.emit()

func cancel() -> void:
	_generation += 1
	if is_instance_valid(_http): _http.cancel_request()
	if loading:
		loading = false; texture = null; message = "Thumbnail cancelled."; changed.emit()

func load_url(url: String) -> void:
	if not enabled or url == _url: return
	cancel(); _url = url; texture = null
	if url.is_empty(): message = "No thumbnail supplied."; changed.emit(); return
	if not safe_url(url): message = "Thumbnail URL is not an approved image endpoint."; changed.emit(); return
	if _paused: message = "Thumbnails paused after a server rate limit. Reopen the browser later."; changed.emit(); return
	if _cache.has(url): texture = _cache[url].get("texture"); message = _cache[url].get("message", ""); changed.emit(); return
	var token := _generation
	loading = true; message = "Loading thumbnail…"; changed.emit()
	while Time.get_ticks_msec() - _last_request < 600:
		await get_tree().process_frame
		if token != _generation: return
	_last_request = Time.get_ticks_msec()
	var response: Dictionary
	if transport.is_valid(): response = await transport.call(url)
	else:
		var request := HTTPRequest.new(); request.timeout = 8; request.max_redirects = 0; request.body_size_limit = 1024 * 1024; request.use_threads = true
		add_child(request); _http = request
		response = {"done":false}
		request.request_completed.connect(func(result, status, _headers, body): response.done = true; response.status = status; response.body = body; response.result = result)
		var error := request.request(url, ["User-Agent: " + USER_AGENT])
		if error != OK: response.done = true; response.status = 0
		while not response.done and token == _generation: await get_tree().process_frame
		if is_instance_valid(request): request.cancel_request(); request.queue_free()
		if _http == request: _http = null
	if token != _generation or not enabled: return
	loading = false
	if response.get("status") == 429: _paused = true
	var decoded := {"error":"Thumbnail unavailable. No automatic retry."}
	if response.get("status") == 200 and response.get("result", HTTPRequest.RESULT_SUCCESS) == HTTPRequest.RESULT_SUCCESS and response.get("body") is PackedByteArray: decoded = decode(response.body)
	if decoded.has("image"): texture = ImageTexture.create_from_image(decoded.image); message = "Thumbnail from source metadata."
	else: message = decoded.error
	if _cache.size() >= 8: _cache.erase(_cache.keys()[0])
	_cache[url] = {"texture":texture, "message":message}
	changed.emit()

func _exit_tree() -> void:
	cancel()
