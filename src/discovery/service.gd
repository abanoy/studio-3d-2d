extends Node
## One cancellable metadata request at a time. No model/thumbnail downloads.
signal changed
const Catalog = preload("res://src/discovery/catalog.gd")
const Providers = preload("res://src/discovery/providers.gd")
const BATCH_SIZE := 100
const MAX_REQUESTS := 6
var network_enabled := false
var loading := false
var rows: Array = []
var statuses := {}
var query := ""
var variants: Array = []
var format := "All"
var website := "All"
var expanded := true
var tried: Array = []
var message := "Online access is off. Local browsing works without a connection."
var has_more := false
var _generation := 0
var _seen := {}
var _pool := {}
var _offsets := {}
var _sketch_streams: Array = []
var _stream_index := 0
var _http: HTTPRequest
var _poly_cache: Array = []
var _poly_cached_at := -1000000
var _last_request := -1000000
var _cooldowns := {}
# Injectable transport for deterministic interaction tests. Receives (source,url,token).
# Returns {status,body} or {error}; it must yield for a cancellation test.
var transport: Callable

func set_network(enabled: bool) -> void:
	network_enabled = enabled
	if not enabled:
		cancel()
		message = "Online access is off. No metadata requests will be sent."
		changed.emit()
	else:
		message = "Online access enabled. Press Search to load model listings."
		changed.emit()

func search(text: String, site := "All", type := "All", expand := true) -> void:
	cancel()
	rows.clear(); _seen.clear(); _pool.clear(); _offsets.clear(); tried.clear(); statuses.clear()
	query = text.strip_edges().left(200); website = site; format = type; expanded = expand
	variants = Catalog.variations(query, expand)
	_sketch_streams.clear(); _stream_index = 0
	for variant in variants if not variants.is_empty() else [""]:
		_sketch_streams.append({"query":variant, "url":Providers.sketch_url(variant)})
	for source in Catalog.PROVIDERS:
		if site != "All" and site != source.id: continue
		statuses[source.id] = source.note if source.mode == "Website only" else "Not requested yet."
		if _paused(source.id): statuses[source.id] = "Rate limited. Wait before using Search to retry. An unrecognized Retry-After pauses this provider for the session; website search is still available."
	if not network_enabled:
		message = "Enable online access, then Search. Website links open only when clicked."
		changed.emit()
		return
	has_more = true
	fetch_more()

func cancel() -> void:
	_generation += 1
	if is_instance_valid(_http): _http.cancel_request()
	if loading: message = "Cancelled. Partial results are kept; Search retries this query."
	loading = false
	changed.emit()

func _exit_tree() -> void:
	_generation += 1
	if is_instance_valid(_http): _http.cancel_request()

func fetch_more() -> void:
	if loading or not network_enabled or not has_more: return
	loading = true
	var token := _generation
	var start_count := rows.size()
	message = "Loading metadata… target about 100 new results."
	changed.emit()
	var sources: Array = []
	for source in ["polyhaven", "sketchfab", "bowlroll"]:
		if website == "All" or website == source: sources.append(source)
	# First round asks every enabled metadata provider; extra rounds fill toward 100.
	var requests := 0
	var rounds := 0
	while rows.size() - start_count < BATCH_SIZE and requests < MAX_REQUESTS and rounds < 5:
		var progress := false
		for source in sources:
			if token != _generation: return
			var before := rows.size()
			var budget := BATCH_SIZE - (rows.size() - start_count)
			if budget <= 0: break
			if _has_pool(source):
				_drain(source, mini(40, budget))
			elif requests < MAX_REQUESTS and _can_request(source):
				requests += 1
				await _load(source, token)
				if token != _generation: return
				_drain(source, mini(40, budget))
			progress = progress or rows.size() > before or _can_request(source) or _has_pool(source)
			changed.emit()
		rounds += 1
		if not progress: break
	if token != _generation: return
	# Rank the new batch; preserve previous batches and their scroll order.
	var batch := rows.slice(start_count)
	batch.sort_custom(func(a, b):
		var ar := Catalog.rank(a, query, variants); var br := Catalog.rank(b, query, variants)
		return ar < br if ar != br else str(a.title).naturalnocasecmp_to(str(b.title)) < 0)
	rows = rows.slice(0, start_count) + batch
	loading = false
	has_more = false
	for source in sources: has_more = has_more or _can_request(source) or _has_pool(source)
	message = "%d listings loaded (%d new; target about 100). %s" % [rows.size(), rows.size() - start_count, "More metadata is available." if has_more else "No more results from the available sources. Website-only sources are not counted."]
	changed.emit()

func _has_pool(source: String) -> bool:
	return int(_offsets.get(source, 0)) < _pool.get(source, []).size()

func _paused(source: String) -> bool:
	var until := int(_cooldowns.get(source, 0))
	return until == -1 or until > Time.get_ticks_msec()

func _can_request(source: String) -> bool:
	if _paused(source): return false
	if source == "sketchfab":
		for stream in _sketch_streams:
			if not stream.url.is_empty(): return true
		return false
	return not _pool.has(source)

func _drain(source: String, budget: int) -> void:
	var pool: Array = _pool.get(source, [])
	var offset := int(_offsets.get(source, 0))
	var added := 0
	while offset < pool.size() and added < budget:
		var row: Dictionary = pool[offset]; offset += 1
		if not Catalog.matches(row, query, variants, format): continue
		var key := Catalog.identity(row)
		var page_key := Catalog.canonical_url(row)
		if _seen.has("id:" + key) or _seen.has("page:" + page_key): continue
		_seen["id:" + key] = true; _seen["page:" + page_key] = true
		rows.append(row); added += 1
	_offsets[source] = offset

func _load(source: String, token: int) -> void:
	var url := Providers.POLY_URL if source == "polyhaven" else Providers.BOWL_URL
	var stream: Dictionary = {}
	if source == "sketchfab":
		for _i in _sketch_streams.size():
			stream = _sketch_streams[_stream_index % _sketch_streams.size()]
			_stream_index += 1
			if not stream.url.is_empty(): break
		url = stream.url
		tried.append("Sketchfab: " + (stream.query if not stream.query.is_empty() else "discovery feed"))
	statuses[source] = "Loading…"
	changed.emit()
	var result: Dictionary
	if source == "polyhaven" and Time.get_ticks_msec() - _poly_cached_at < 600000:
		result = {"rows":_poly_cache, "next":"", "warning":"Using this session's cached metadata (up to 10 minutes)."}
	else:
		var response: Dictionary = await _request(source, url, token)
		if token != _generation: return
		if response.has("error"): result = response
		elif int(response.get("status", 0)) == 429:
			var wait_seconds := 60
			var pause_session := false
			for header in response.get("headers", []):
				var parts := str(header).split(":", true, 1)
				if parts.size() == 2 and parts[0].to_lower() == "retry-after":
					var hint := parts[1].strip_edges()
					if hint.is_valid_int() and hint.length() < 12: wait_seconds = maxi(60, int(hint))
					else: pause_session = true
			# Never shorten the provider's delay. HTTP-date/unknown hints pause the
			# provider for the session rather than guessing an earlier retry time.
			_cooldowns[source] = -1 if pause_session else Time.get_ticks_msec() + wait_seconds * 1000
			result = {"error":"HTTP 429: rate limited. Retry-After could not be interpreted; this provider is paused for the session." if pause_session else "HTTP 429: rate limited. Wait at least %d seconds before Search retries this provider." % wait_seconds}
		elif int(response.get("status", 0)) != 200:
			result = {"error":"HTTP %d. Access unavailable; no login/challenge bypass or automatic retry." % int(response.get("status", 0))}
		elif not response.get("body") is PackedByteArray: result = {"error":"Missing metadata response body."}
		else: result = Providers.parse(source, response.body)
	if token != _generation: return
	if result.has("error"):
		statuses[source] = str(result.error) + " Use the website link or Search to retry."
		_pool[source] = []; _offsets[source] = 0
		if source == "sketchfab":
			# One 403/429/malformed response stops this provider, including alias streams.
			for entry in _sketch_streams: entry.url = ""
		return
	var records: Array = result.get("rows", [])
	if source == "polyhaven": _poly_cache = records; _poly_cached_at = Time.get_ticks_msec()
	if source == "sketchfab": stream.url = result.get("next", "")
	_pool[source] = records; _offsets[source] = 0
	statuses[source] = "%d metadata entries. %s" % [records.size(), result.get("warning", "")]

func _request(source: String, url: String, token: int) -> Dictionary:
	# No redirects/cookies/auth. The only hosts are fixed API/feed endpoints and a
	# validated same-endpoint Sketchfab cursor. Never request an item download URL.
	if url not in [Providers.POLY_URL, Providers.BOWL_URL] and not Providers.safe_next(url): return {"error":"Rejected unexpected metadata endpoint."}
	while Time.get_ticks_msec() - _last_request < 600:
		await get_tree().process_frame
		if token != _generation: return {"error":"Cancelled."}
	_last_request = Time.get_ticks_msec()
	if transport.is_valid(): return await transport.call(source, url, token)
	var request := HTTPRequest.new()
	request.timeout = 12.0
	request.body_size_limit = 4 * 1024 * 1024
	request.max_redirects = 0
	request.use_threads = true
	add_child(request)
	_http = request
	var reply := {"done":false}
	request.request_completed.connect(func(result, status, headers, body):
		reply.done = true
		var errors := {HTTPRequest.RESULT_CANT_RESOLVE:"Cannot resolve the provider hostname; check connection/DNS.", HTTPRequest.RESULT_CANT_CONNECT:"Cannot connect to the provider.", HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR:"Secure connection failed; check your clock/certificates or provider access.", HTTPRequest.RESULT_TIMEOUT:"Metadata request timed out after 12 seconds.", HTTPRequest.RESULT_BODY_SIZE_LIMIT_EXCEEDED:"Metadata exceeds the 4 MiB response limit."}
		if result != HTTPRequest.RESULT_SUCCESS: reply.error = errors.get(result, "Metadata request failed (%d); check your connection or provider access." % result)
		else: reply.status = status; reply.body = body; reply.headers = headers)
	var error := request.request(url, PackedStringArray(["User-Agent: " + Providers.USER_AGENT, "Accept: application/json, application/rss+xml, application/xml"]))
	if error != OK: reply.done = true; reply.error = "Could not start metadata request (%d)." % error
	while not reply.done and token == _generation and is_inside_tree(): await get_tree().process_frame
	if token != _generation: request.cancel_request(); reply = {"error":"Cancelled."}
	request.queue_free()
	if _http == request: _http = null
	return reply
