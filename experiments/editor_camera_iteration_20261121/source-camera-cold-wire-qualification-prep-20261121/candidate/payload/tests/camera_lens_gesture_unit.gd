extends SceneTree
const Lens=preload("res://src/camera_lens_gesture.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	check(Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,1.).fov==57.,"wheel up narrows field of view")
	check(Lens.plan(60.,MOUSE_BUTTON_WHEEL_DOWN,1.).fov==63.,"wheel down widens field of view")
	check(Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,.5).fov==58.5,"fractional wheel factor remains proportional")
	check(Lens.plan(16.,MOUSE_BUTTON_WHEEL_UP,1.).fov==15.,"lens has bounded narrow limit")
	check(Lens.plan(119.,MOUSE_BUTTON_WHEEL_DOWN,1.).fov==120.,"lens has bounded wide limit")
	check(not Lens.plan(15.,MOUSE_BUTTON_WHEEL_UP,1.).changed and not Lens.plan(120.,MOUSE_BUTTON_WHEEL_DOWN,1.).changed,"limit steps are no-ops")
	check(Lens.plan(60.,MOUSE_BUTTON_LEFT,1.).has("error"),"nonwheel button refuses")
	check(Lens.plan(NAN,MOUSE_BUTTON_WHEEL_UP,1.).has("error"),"nonfinite camera lens refuses")
	check(Lens.plan(1.,MOUSE_BUTTON_WHEEL_UP,1.).has("error") and Lens.plan(179.,MOUSE_BUTTON_WHEEL_DOWN,1.).has("error"),"legacy lens outside editor range refuses without a jump")
	check(Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,0.).has("error") and Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,-1.).has("error"),"zero and negative wheel factors refuse")
	check(Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,INF).has("error") and Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,9.).has("error"),"nonfinite and excessive wheel factors refuse")
	check(Lens.plan("60",MOUSE_BUTTON_WHEEL_UP,1.).has("error") and Lens.plan(60.,MOUSE_BUTTON_WHEEL_UP,"1").has("error"),"text values are not silently coerced")
	print("CAMERA_LENS_GESTURE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
