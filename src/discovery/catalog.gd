extends RefCounted
## Metadata only. No importer, model loader, subprocess or account access.
const FORMATS := ["All", "MMD", "SFM", "VRM", "GMod", "glTF", "FBX", "OBJ", "Blend", "Source MDL", "Unknown"]
const PROVIDERS := [
	{"id":"polyhaven", "name":"Poly Haven", "mode":"API", "note":"Public model metadata; cached in memory for 10 minutes. File format and access stay Unknown without item evidence."},
	{"id":"sketchfab", "name":"Sketchfab", "mode":"API", "note":"Public search API, 24 per request. Access may be blocked; no account or download API is used."},
	{"id":"bowlroll", "name":"BowlRoll", "mode":"Feed", "note":"Japanese MikuMikuDance RSS feed only; recent entries, not a full-site search. May contain motions or other non-model files. Use website search for the full directory."},
	{"id":"steam_sfm", "name":"Steam Workshop (SFM)", "mode":"Website only", "note":"Official QueryFiles API needs a key. Open website search; no scraping, subscriptions or ownership assumptions."},
	{"id":"steam_gmod", "name":"Steam Workshop (GMod)", "mode":"Website only", "note":"Official QueryFiles API needs a key. Access and retrieval depend on the app/item; check its source page."},
	{"id":"sfmlab", "name":"SFMLab", "mode":"Website only", "note":"Terms restrict scraping; Anubis protection observed. Search in your browser. API catalogue access has not been established."},
	{"id":"booth", "name":"BOOTH", "mode":"Website only", "note":"Japanese/English marketplace search; no verified public catalogue API. Listings can be paid or require login; check each page."},
	{"id":"vroid", "name":"VRoid Hub", "mode":"Website only", "note":"Japanese/English VRM directory. API needs registered application/OAuth. Public preview does not prove download permission."}
]
# Explicit proper-name aliases, not generated translations. Source and scope in docs.
const ALIASES := {"hatsune miku":["初音ミク", "初音未来"], "miku hatsune":["初音ミク", "初音未来"], "初音ミク":["Hatsune Miku", "Miku Hatsune", "初音未来"], "初音未来":["Hatsune Miku", "初音ミク"]}

static func normalize(value: String) -> String:
	var out := value.to_lower().strip_edges()
	# Deterministic full-width ASCII and ideographic-space folding.
	var folded := ""
	for char in out:
		var code := char.unicode_at(0)
		folded += String.chr(code - 0xfee0) if code >= 0xff01 and code <= 0xff5e else " " if code == 0x3000 else char
	out = folded.replace("_", " ").replace("-", " ")
	while out.contains("  "): out = out.replace("  ", " ")
	return out

static func variations(query: String, expand := true) -> Array:
	var original := query.strip_edges().left(200)
	if original.is_empty(): return []
	var out: Array = [original]
	if not expand: return out
	var normal := normalize(original)
	var words := normal.split(" ", false)
	if normal != original: out.append(normal)
	if words.size() > 1:
		words.reverse()
		out.append(" ".join(words))
	# Aliases precede broad words so a six-request budget includes original scripts.
	for alias in ALIASES.get(normal, []): out.append(alias)
	for word in normal.split(" ", false): out.append(word)
	var unique: Array = []
	for value in out:
		if value not in unique: unique.append(value)
	return unique.slice(0, 8)

static func provider(id: String) -> Dictionary:
	for row in PROVIDERS:
		if row.id == id: return row
	return {}

static func website_url(id: String, query: String) -> String:
	var q := query.left(200).uri_encode()
	match id:
		"polyhaven": return "https://polyhaven.com/models" + ("?search=" + q if not q.is_empty() else "")
		"sketchfab": return "https://sketchfab.com/search?type=models&q=" + q
		"bowlroll": return "https://bowlroll.net/file/keyword/" + q if not q.is_empty() else "https://bowlroll.net/file/"
		"steam_sfm": return "https://steamcommunity.com/workshop/browse/?appid=1840&searchtext=" + q
		"steam_gmod": return "https://steamcommunity.com/workshop/browse/?appid=4000&searchtext=" + q
		"sfmlab": return "https://sfmlab.com/" # Search form is protected; do not invent its query syntax.
		"booth": return "https://booth.pm/en/search/" + q if not q.is_empty() else "https://booth.pm/en/browse/3D%20Models"
		"vroid": return "https://hub.vroid.com/en/" # OAuth API only; use the website search UI.
	return ""

static func safe_page(url: String) -> bool:
	for host in ["polyhaven.com", "sketchfab.com", "bowlroll.net", "steamcommunity.com", "sfmlab.com", "booth.pm", "hub.vroid.com"]:
		if url.begins_with("https://" + host + "/") and not url.contains("\n") and not url.contains("\r"): return true
	return false

static func formats(text: String) -> Array:
	var value := normalize(text)
	var out: Array = []
	var patterns := {"MMD":"(^|[^a-z0-9])(mmd|pmx|pmd|mikumikudance)([^a-z0-9]|$)", "SFM":"(^|[^a-z0-9])(sfm|source filmmaker)([^a-z0-9]|$)", "GMod":"(^|[^a-z0-9])(gmod|garry.?s mod)([^a-z0-9]|$)", "VRM":"(^|[^a-z0-9])vrm([^a-z0-9]|$)", "glTF":"(^|[^a-z0-9])(glb|gltf)([^a-z0-9]|$)", "FBX":"(^|[^a-z0-9])fbx([^a-z0-9]|$)", "OBJ":"(^|[^a-z0-9])obj([^a-z0-9]|$)", "Blend":"(^|[^a-z0-9])blend([^a-z0-9]|$)"}
	for key in patterns:
		var regex := RegEx.create_from_string(patterns[key])
		if regex.search(value): out.append(key)
	if value.contains(".mdl"): out.append("Source MDL")
	return out

static func local_format(path: String) -> Array:
	match path.get_extension().to_lower():
		"pmx", "pmd": return ["MMD"]
		"vrm": return ["VRM"]
		"mdl": return ["Source MDL"] # Same extension serves different Source apps; do not guess.
		"glb", "gltf": return ["glTF"]
		"fbx": return ["FBX"]
		"obj": return ["OBJ"]
		"blend": return ["Blend"]
	return []

static func rank(row: Dictionary, query: String, variants: Array) -> int:
	var title := normalize(str(row.get("title", "")))
	var exact := normalize(query)
	if exact.is_empty(): return 0
	if title == exact: return 0
	if title.contains(exact): return 1
	for variant in variants:
		var normal := normalize(str(variant))
		if normal.contains(" ") and title.contains(normal): return 2
		if normal in ["初音ミク", "初音未来"] and title.contains(normal): return 2
	return 5

static func matches(row: Dictionary, query: String, variants: Array, format: String) -> bool:
	var types: Array = row.get("formats", [])
	if format == "Unknown" and not types.is_empty(): return false
	if format != "All" and format != "Unknown" and format not in types: return false
	if query.strip_edges().is_empty(): return true
	var text := normalize(str(row.get("title", "")) + " " + str(row.get("keywords", "")))
	for variant in variants:
		if text.contains(normalize(str(variant))): return true
	return false

static func identity(row: Dictionary) -> String:
	return str(row.get("provider", "")) + ":" + str(row.get("id", row.get("url", "")))

static func canonical_url(row: Dictionary) -> String:
	# Only used as a duplicate key, never to rewrite the source page being opened.
	return str(row.get("provider", "")) + ":" + str(row.get("url", "")).get_slice("?", 0).get_slice("#", 0).trim_suffix("/")
