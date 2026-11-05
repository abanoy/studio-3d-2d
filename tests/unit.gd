extends SceneTree
const Timeline = preload("res://src/timeline.gd")
const Drawing = preload("res://src/drawing.gd")
const Storage = preload("res://src/storage.gd")
const SceneIO = preload("res://src/scene3d.gd")
var failures := 0
var total := 0

func check(ok: bool, text: String) -> void:
	total += 1
	print(("PASS " if ok else "FAIL ") + text)
	if not ok: failures += 1

func _initialize() -> void:
	var a := Timeline.key(0, Vector3.ZERO, Quaternion.IDENTITY, 60, "linear")
	var b := Timeline.key(48, Vector3(4, 2, -2), Quaternion(Vector3.UP, PI / 2), 50)
	var keys := [a, b]
	check(Timeline.sample(keys, 0).position == Vector3.ZERO, "camera exact frame 0")
	check(Timeline.sample(keys, 24).position == Vector3(2, 1, -1), "camera exact midpoint 24")
	check(Timeline.sample(keys, 48).position == Vector3(4, 2, -2), "camera endpoint 48")
	check(is_equal_approx(Timeline.sample(keys, 24).fov, 55), "FOV interpolation")
	check(Timeline.sample(keys, 24).rotation.is_normalized(), "slerp normalized")
	a.interpolation = "hold"
	check(Timeline.sample(keys, 47).position == Vector3.ZERO, "hold before boundary")
	check(Timeline.sample(keys, 48).position == Vector3(4, 2, -2), "hold reaches next key")
	a.interpolation = "ease"
	check(Timeline.sample(keys, 12).position.x < 1, "ease acceleration")
	Timeline.put_key(keys, Timeline.key(24, Vector3.ONE, Quaternion.IDENTITY, 70))
	Timeline.put_key(keys, Timeline.key(24, Vector3(2, 2, 2), Quaternion.IDENTITY, 70))
	check(keys.size() == 3 and keys[1].frame == 24, "replace key without duplicate; sorted")
	check(is_equal_approx(Timeline.seconds(24000, {"fps_num": 24000, "fps_den": 1001}), 1001), "rational time no accumulated delta")
	var image := Drawing.blank(32, 32)
	Drawing.stroke(image, Vector2(3, 16), Vector2(29, 16), 2, Color.RED, false)
	check(image.get_pixel(16, 16) == Color.RED, "continuous raster segment")
	check(image.get_pixel(16, 2).a == 0, "actual transparent background")
	Drawing.stroke(image, Vector2(16, 16), Vector2(16, 16), 2, Color.RED, true)
	check(image.get_pixel(16, 16).a == 0, "eraser removes alpha")
	var layer := {"visible": true, "cels": []}
	Drawing.insert(layer, 0, 48, image)
	var second := Drawing.blank(32, 32)
	Drawing.insert(layer, 2, 48, second)
	check(Drawing.cel_at(layer, 0).image == image and Drawing.cel_at(layer, 1).image == image, "held cel on twos")
	check(Drawing.cel_at(layer, 2).image == second, "cel advances at boundary")
	check(Drawing.cel_at(layer, 48).is_empty(), "end-exclusive exposure")
	layer.visible = false
	check(Drawing.composite([layer], 0, 32, 32).get_pixel(5, 16).a == 0, "hidden layer excluded")
	check(not Storage.safe_relative("../secrets"), "reject parent traversal")
	check(not Storage.safe_relative("C:/secret"), "reject absolute Windows path")
	check(not Storage.safe_relative("a\\b"), "reject backslash traversal")
	check(not Storage.safe_relative("https://host/a"), "reject URL")
	check(Storage.safe_relative("cels/revision/ink.png"), "accept project-local asset")
	check(Storage.load_project("res://does-not-exist").has("error"), "missing project readable error")
	check(SceneIO.load_glb("res://no.glb").has("error"), "missing GLB readable error")
	print("UNIT %d checks; failures=%d" % [total, failures])
	quit(0 if failures == 0 else 1)
