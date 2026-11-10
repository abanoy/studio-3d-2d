extends RefCounted
# Test input resolution only. Never relabel a prepared GLB as a native VRM.
const NAMES:=["AvatarSample_A.vrm","AvatarSample_Avrm0.vrm"]

static func json_file(path: String) -> Dictionary:
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()>8*1024*1024:return {}
	var parser:=JSON.new()
	if parser.parse(file.get_as_text())!=OK or not parser.data is Dictionary:return {}
	return parser.data

static func resolve(name: String) -> Dictionary:
	if not name in NAMES:return {}
	var supplied: String=OS.get_environment("HYBRID_NATIVE_INPUTS").path_join(name) if not OS.get_environment("HYBRID_NATIVE_INPUTS").is_empty() else ""
	if not supplied.is_empty() and FileAccess.file_exists(supplied):return {"path":supplied,"sha256":FileAccess.get_sha256(supplied),"provenance":"explicit owner native-input directory"}
	var desktop: String="C:/Users/noble/Desktop/"+name
	if FileAccess.file_exists(desktop):return {"path":desktop,"sha256":FileAccess.get_sha256(desktop),"provenance":"owner Desktop input"}
	for base in [ProjectSettings.globalize_path("res://output"),"C:/a/Programming/cloudflare/prototypes/studio-3d-2d/output"]:
		var manifest: Dictionary=json_file(base.path_join("native-import-verification.json"))
		var bundles=manifest.get("bundles",[])
		if not bundles is Array:continue
		for value in bundles:
			if not value is String:continue
			var parameters: String=value.path_join("parameters.json");var report:=json_file(parameters)
			if report.get("kind")!="vrm_preparation" or report.get("source_file")!=name:continue
			var expected=report.get("source_sha256","")
			if not expected is String or expected.length()!=64:continue
			var candidate: String=value.path_join("native").path_join(name)
			var file:=FileAccess.open(candidate,FileAccess.READ)
			if file==null or file.get_length()>128*1024*1024:continue
			if FileAccess.get_sha256(candidate)!=expected:continue
			return {"path":candidate,"sha256":expected,"provenance":"verified retained original VRM","report":parameters}
	return {}

static func vrm(name: String) -> String:
	var result:=resolve(name)
	if not result.is_empty():print("NATIVE_TEST_INPUT "+JSON.stringify(result))
	return str(result.get("path","C:/Users/noble/Desktop/"+name)) if name in NAMES else ""
