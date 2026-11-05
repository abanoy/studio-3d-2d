extends SceneTree
const P=preload("res://src/mmd_pose_shapes.gd")
func _initialize() -> void:
	var rows: Array=[{"node":2,"names":["blink","mouth"]},{"node":3,"names":["blink"]}]
	var group: Dictionary={"native_name":"happy","error":"","binds":[{"node":"2","index":"0","weight":.5}]}
	var groups: Dictionary={"entries":[group],"error":""}
	var result:=P.resolve([{"name":"blink","weight":.2},{"name":"happy","weight":.6},{"name":"unknown","weight":1}],rows,groups)
	assert(result.matched.size()==2 and result.skipped.size()==1)
	assert(is_equal_approx(result.values["2"]["0"],.5) and is_equal_approx(result.values["3"]["0"],.2))
	assert(not result.values["2"].has("1"))
	assert(P.resolve([{"name":"blink","weight":101}],rows,groups).has("error"))
	assert(P.resolve([{"name":"blink","weight":NAN}],rows,groups).has("error"))
	assert(P.resolve([{"name":"blink","weight":1},{"name":"blink","weight":1}],rows,groups).has("error"))
	var unsupported: Dictionary=group.duplicate(true);unsupported.error="Unsupported native material effects."
	result=P.resolve([{"name":"happy","weight":1}],rows,{"entries":[unsupported],"error":""})
	assert(result.values.is_empty() and result.matched.is_empty() and result.skipped[0].reason==unsupported.error)
	result=P.resolve([{"name":"happy","weight":1}],rows,{"entries":[group,group],"error":""})
	assert(result.values.is_empty() and result.skipped.size()==1)
	result=P.resolve([{"name":"blink","weight":1}],[{"node":2,"names":["blink","blink"]}],{})
	assert(result.values.is_empty() and result.skipped.size()==1)
	var collision: Dictionary=group.duplicate(true);collision.native_name="blink"
	result=P.resolve([{"name":"blink","weight":1}],rows,{"entries":[collision]})
	assert(result.values.is_empty() and result.skipped.size()==1)
	print("MMD_POSE_SHAPES_UNIT failures=0");quit(0)
