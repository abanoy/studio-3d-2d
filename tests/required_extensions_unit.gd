extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	check(SceneIO.required_extensions_error({}).is_empty() and SceneIO.required_extensions_error({"extensionsRequired":[]}).is_empty(),"ordinary assets do not gain a new importer requirement")
	check(SceneIO.required_extensions_error({"extensionsRequired":["KHR_lights_punctual"]}).is_empty(),"registered engine extension remains supported")
	var error:=SceneIO.required_extensions_error({"extensionsRequired":["HAS_unavailable_test","HAS_unavailable_test","KHR_lights_punctual"]})
	check(error.contains("HAS_unavailable_test") and error.contains("compatible export") and error.count("HAS_unavailable_test")==1 and not error.contains("KHR_lights_punctual"),"unsupported required feature is named once with an action and supported names omitted")
	for value in [null,"KHR_lights_punctual",[5],[""]]:
		check(not SceneIO.required_extensions_error({"extensionsRequired":value}).is_empty(),"malformed required declaration refuses clearly")
	check(SceneIO.required_extensions_error({"extensionsUsed":["HAS_optional_metadata"]}).is_empty(),"optional metadata is not silently promoted into a required feature")
	var names: Array=[]
	for i in range(8):names.append("HAS_unavailable_%d" % i)
	error=SceneIO.required_extensions_error({"extensionsRequired":names})
	check(error.contains("HAS_unavailable_5") and not error.contains("HAS_unavailable_6") and error.contains("+2 more"),"large diagnostics list named features and an accurate remainder")
	print("REQUIRED_EXTENSIONS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
