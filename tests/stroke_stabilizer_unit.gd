extends SceneTree
const Stabilizer=preload("res://src/stroke_stabilizer.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var filter:=Stabilizer.new();var points: Array[Vector2]=[Vector2(4,9),Vector2(100,20),Vector2(80,90),Vector2(500,600)]
	var exact:=true
	for p in points:exact=exact and filter.sample(p)==p
	check(exact,"distance0 preserves every raw coordinate exactly")
	filter.distance=12;filter.reset(Vector2.ZERO)
	check(filter.sample(Vector2(3,4))==Vector2.ZERO and filter.sample(Vector2(6,8))==Vector2.ZERO,"jitter inside trailing radius leaves the stable point still")
	check(filter.sample(Vector2(30,0)).is_equal_approx(Vector2(18,0)),"long movement follows exactly one radius behind the pointer")
	var corner:=filter.sample(Vector2(30,30))
	check(corner.distance_to(Vector2(30,30))<=12.00001 and corner.x>18 and corner.y>0,"turns move smoothly while staying inside the trailing radius")
	check(filter.raw==Vector2(30,30) and filter.position==corner,"raw endpoint remains separate for release-tail completion")
	filter.reset(Vector2(100,200));check(filter.sample(Vector2(100,200))==Vector2(100,200),"reset begins a new contact without bridging the previous stroke")
	var prior: Vector2=filter.raw;var position: Vector2=filter.position
	check(filter.sample(Vector2(NAN,0))==position and filter.raw==prior,"nonfinite input cannot replace stable state or endpoint")
	check(filter.reset(Vector2(INF,0))==position and filter.raw==prior,"nonfinite reset also preserves contact state")
	filter.distance=100;filter.reset(Vector2.ZERO);check(filter.sample(Vector2(100,0))==Vector2(68,0),"defensive distance cap stays at32 canvas pixels")
	filter.distance=-1;check(filter.sample(Vector2(25,35))==Vector2(25,35),"negative distance safely disables the filter")
	filter.distance=NAN;check(filter.sample(Vector2(55,65))==Vector2(55,65),"nonfinite distance safely uses raw input")
	filter.distance=24;filter.reset(Vector2.ZERO);var bounded:=true
	for i in range(1000):
		var target:=Vector2(i*1.5,sin(i*.1)*10);var result:=filter.sample(target);bounded=bounded and result.is_finite() and result.distance_to(target)<=24.0001
	check(bounded,"long mixed-direction gesture stays finite and bounded independently of clocks")
	print("STROKE_STABILIZER_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
