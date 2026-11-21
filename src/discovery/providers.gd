extends RefCounted
const Catalog = preload("res://src/discovery/catalog.gd")
const USER_AGENT := "HybridAnimationStudio-Discovery/0.1 (+https://github.com/abanoy/studio-3d-2d)"
const POLY_URL := "https://api.polyhaven.com/assets?type=models"
const BOWL_URL := "https://bowlroll.net/file/tag/MikuMikuDance.rss"
const SKETCH_URL := "https://api.sketchfab.com/v3/search?type=models&count=24"

static func sketch_url(query: String) -> String:
	return SKETCH_URL + ("&q=" + query.uri_encode() if not query.is_empty() else "")

static func safe_next(url: String) -> bool:
	return url.begins_with("https://api.sketchfab.com/v3/search?") and not url.contains("\n") and not url.contains("\r")

static func _record(id: String, title: String, source: String, url: String, keywords := "") -> Dictionary:
	return {"id":id, "title":title.left(512), "provider":source, "url":url, "keywords":keywords.left(4096), "formats":Catalog.formats(title + " " + keywords), "access":["Unknown"], "evidence":"No access metadata supplied.", "thumbnail_url":""}

static func parse(source: String, body: PackedByteArray) -> Dictionary:
	if body.size() > 4 * 1024 * 1024: return {"error":"Metadata exceeds the 4 MiB response limit."}
	if source == "bowlroll": return _bowl(body)
	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK: return {"error":"Malformed JSON metadata."}
	if not json.data is Dictionary: return {"error":"Expected a JSON object."}
	match source:
		"polyhaven": return _poly(json.data)
		"sketchfab": return _sketch(json.data)
	return {"error":"Unsupported metadata provider."}

static func _poly(data: Dictionary) -> Dictionary:
	var rows: Array = []
	var keys := data.keys()
	keys.sort()
	var invalid := 0
	for id in keys:
		if not id is String or not data[id] is Dictionary: invalid += 1; continue
		var value: Dictionary = data[id]
		if not value.get("name") is String or value.name.strip_edges().is_empty(): invalid += 1; continue
		if not (value.get("type") is int or value.get("type") is float) or value.type != 2: invalid += 1; continue
		var row := _record(id, value.name, "polyhaven", "https://polyhaven.com/a/" + id.uri_encode(), _words(value.get("tags", [])))
		row.thumbnail_url = value.get("thumbnail_url", "") if value.get("thumbnail_url", "") is String else ""
		row.evidence = "Public model listing; file format and access conditions were not inspected."
		# Do not infer specific formats or availability from the provider's reputation.
		rows.append(row)
	if rows.is_empty() and not data.is_empty(): return {"error":"No valid model records in Poly Haven response."}
	return {"rows":rows, "next":"", "warning":"Skipped %d invalid/non-model records." % invalid if invalid else ""}

static func _words(value) -> String:
	if not value is Array: return ""
	var out := ""
	for word in value.slice(0, 100):
		if word is String: out += " " + word
		elif word is Dictionary and word.get("name") is String: out += " " + word.name
	return out

static func _sketch(data: Dictionary) -> Dictionary:
	if not data.get("results") is Array: return {"error":"Sketchfab response has no results array."}
	var rows: Array = []
	var invalid := 0
	for value in data.results:
		if not value is Dictionary: invalid += 1; continue
		if not value.get("uid") is String or not value.get("name") is String or not value.get("viewerUrl") is String: invalid += 1; continue
		if not value.viewerUrl.begins_with("https://sketchfab.com/3d-models/") or not Catalog.safe_page(value.viewerUrl): invalid += 1; continue
		var row := _record(value.uid, value.name, "sketchfab", value.viewerUrl, _words(value.get("tags", [])))
		var thumbnails = value.get("thumbnails")
		if thumbnails is Dictionary and thumbnails.get("images") is Array:
			for candidate in thumbnails.images.slice(0, 20):
				if candidate is Dictionary and candidate.get("url") is String and (candidate.get("width") is int or candidate.get("width") is float) and (candidate.get("height") is int or candidate.get("height") is float) and candidate.width > 0 and candidate.width <= 512 and candidate.height > 0 and candidate.height <= 512:
					row.thumbnail_url = candidate.url; break
		row.access = ["Preview"]
		row.evidence = "viewerUrl supplied by the model search API. Preview means a source-site 3D viewer."
		if value.get("isDownloadable") is bool and value.isDownloadable:
			row.access.append("Downloadable")
			row.evidence += " isDownloadable=true; actual file retrieval/login was not checked."
		else:
			row.access.append("Unknown")
			row.evidence += " Download/password/login conditions Unknown."
		if value.get("isProtected") is bool and value.isProtected:
			row.access.append("Password")
			row.evidence += " isProtected=true reports password protection; no password is requested or stored."
		rows.append(row)
	var next = data.get("next", "")
	if next == null: next = ""
	if not next is String or (not next.is_empty() and not safe_next(next)): return {"error":"Rejected unexpected Sketchfab pagination URL."}
	if rows.is_empty() and not data.results.is_empty(): return {"error":"No valid records in Sketchfab response."}
	return {"rows":rows, "next":next, "warning":"Skipped %d invalid records." % invalid if invalid else ""}

static func _bowl(body: PackedByteArray) -> Dictionary:
	var text := body.get_string_from_utf8()
	if text.to_lower().contains("<html") or text.to_lower().contains("<!doctype html"):
		return {"error":"BowlRoll returned a web page instead of RSS. The published feed may have changed; use website search."}
	if text.contains("<!DOCTYPE") or text.contains("<!ENTITY"): return {"error":"RSS declarations/entities are not supported."}
	var xml := XMLParser.new()
	if xml.open_buffer(body) != OK: return {"error":"Malformed BowlRoll RSS."}
	var rows: Array = []
	var item := {}
	var field := ""
	var saw_rss := false
	var steps := 0
	var stack: Array = []
	while true:
		var error := xml.read()
		if error == ERR_FILE_EOF: break
		if error != OK: return {"error":"Malformed BowlRoll RSS."}
		steps += 1
		if steps > 100000: return {"error":"BowlRoll RSS structure exceeds the parser limit."}
		if xml.get_node_type() == XMLParser.NODE_ELEMENT:
			var name := xml.get_node_name()
			if not xml.is_empty(): stack.append(name)
			if name == "rss" or name == "rdf:RDF": saw_rss = true
			if name == "item": item = {"title":"", "link":"", "description":""}
			field = name if name in ["title", "link", "description"] else ""
		elif xml.get_node_type() in [XMLParser.NODE_TEXT, XMLParser.NODE_CDATA] and not item.is_empty() and not field.is_empty():
			item[field] = (str(item[field]) + xml.get_node_data()).left(4096)
		elif xml.get_node_type() == XMLParser.NODE_ELEMENT_END:
			if stack.is_empty() or stack.pop_back() != xml.get_node_name(): return {"error":"Malformed BowlRoll RSS nesting."}
			if xml.get_node_name() == "item" and not item.is_empty():
				var regex := RegEx.create_from_string("^https://bowlroll\\.net/file/([0-9]+)/?$")
				var match_id := regex.search(item.link.strip_edges())
				if match_id and not item.title.strip_edges().is_empty():
					var row := _record(match_id.get_string(1), item.title.strip_edges(), "bowlroll", "https://bowlroll.net/file/" + match_id.get_string(1))
					row.evidence = "Published RSS entry; access, format and whether this is a model remain unverified."
					rows.append(row)
				item = {}
			field = ""
	if not stack.is_empty(): return {"error":"Truncated BowlRoll RSS response."}
	if not saw_rss: return {"error":"Expected RSS; provider may be unavailable or returning an access challenge."}
	return {"rows":rows, "next":"", "warning":"Recent MikuMikuDance feed only; full-site search and feed pagination unavailable."}
