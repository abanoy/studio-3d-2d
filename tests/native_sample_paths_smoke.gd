extends SceneTree
const Samples=preload("res://tests/native_sample_paths.gd")
func _initialize() -> void:
	create_timer(15).timeout.connect(func():push_error("Native resolver watchdog");quit(2))
	var results:=[]
	for name in Samples.NAMES:
		var value:=Samples.resolve(name)
		if value.is_empty() or not str(value.path).ends_with(".vrm") or FileAccess.get_sha256(value.path)!=value.sha256:push_error("Native sample resolver failed: "+name);quit(1);return
		results.append(value)
	if not Samples.resolve("../unknown.glb").is_empty():push_error("Foreign input accepted");quit(1);return
	print("NATIVE_SAMPLE_RESOLVER "+JSON.stringify({"verified":results,"foreign_refused":true}));quit(0)
