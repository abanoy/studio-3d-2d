extends SceneTree
const View=preload("res://src/timeline_view.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var view:=View.new()
	for width in [400,1200]:
		view.size=Vector2(width,160)
		for duration in [1,12,48,1440,7200]:
			view.duration=duration
			for span in [0.,12.,22.5,float(duration)*.5]:
				view.window_span=span;view.window_start=duration*.7
				var start:=view.visible_start();var end:=start+view.visible_span()
				var aligned:=is_equal_approx(view.x(start),view.LEFT) and is_equal_approx(view.x(end),width-16)
				var exact:=true
				for frame in [0,1,maxi(0,duration-1),duration,roundi(start),roundi(end)]:exact=exact and view.frame_at(Vector2(view.x(frame),0))==frame
				check(aligned and exact,"bounded fractional/whole range maps both directions: "+str([width,duration,span]))
	view.duration=1440;view.window_span=12;view.window_start=-100
	check(view.visible_start()==0 and view.frame_at(Vector2(-100000,0))==0,"negative view and pointer clamp to first project frame")
	view.window_start=100000
	check(view.visible_start()==1428 and view.frame_at(Vector2(100000,0))==1440,"past-end view and pointer clamp to project boundary")
	view.free();print("TIMELINE_NAVIGATION_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
