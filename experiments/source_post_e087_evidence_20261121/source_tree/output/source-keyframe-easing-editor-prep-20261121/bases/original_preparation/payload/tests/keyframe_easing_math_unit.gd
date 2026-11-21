extends SceneTree
const Easing=preload("res://src/keyframe_easing.gd")
const Timeline=preload("res://src/timeline.gd")
var checks:=0
var failures:=0
func check(value: bool,name: String) -> void:
	checks+=1
	if value:print("PASS "+name)
	else:failures+=1;push_error("FAIL "+name)
func key(frame: int,x: float,mode: String="linear") -> Dictionary:
	var row:=Timeline.key(frame,Vector3(x,2.,-3.),Quaternion(Vector3.UP,float(frame)*.01),60.+float(frame)*.01,mode)
	row["near"]=.05+frame*.001;row["far"]=1000.+frame;return row
func same(a: Dictionary,b: Dictionary) -> bool:
	return a.position.is_equal_approx(b.position) and absf(absf(a.rotation.dot(b.rotation))-1.)<1e-5 and is_equal_approx(a.fov,b.fov) and is_equal_approx(a.near,b.near) and is_equal_approx(a.far,b.far)
func _initialize() -> void:
	var keys: Array=[key(0,0.),key(10,10.),key(20,20.,"ease")]
	var original: Array=keys.duplicate(true)
	var legacy:=Easing.compile(keys,[],20)
	check(not legacy.has("error") and legacy.segments.is_empty(),"empty recipe admits without active segments")
	var zero:=Easing.compile(keys,[{"frame":10,"arrive":0.,"leave":0.}],20)
	var old_equal:=true
	for frame in range(21):old_equal=old_equal and same(Easing.sample(zero,frame),Timeline.sample(keys,frame))
	check(old_equal,"zero amounts preserve every old integer-frame sample")
	var leave:=Easing.compile(keys,[{"frame":0,"arrive":0.,"leave":1.}],20)
	var arrive:=Easing.compile(keys,[{"frame":10,"arrive":1.,"leave":0.}],20)
	check(Easing.sample(leave,5).position.x<5. and Easing.sample(arrive,5).position.x>5.,"arrival and departure independently affect the correct time direction")
	check(same(Easing.sample(leave,0),Timeline.sample(keys,0)) and same(Easing.sample(leave,10),Timeline.sample(keys,10)),"authored endpoints remain exact camera values")
	check(same(Easing.sample(leave,15),Timeline.sample(keys,15)),"unselected neighboring segment remains untouched")
	var both:=Easing.compile(keys,[{"frame":0,"arrive":0.,"leave":1.},{"frame":10,"arrive":1.,"leave":0.}],20)
	check(is_equal_approx(Easing.sample(both,2).position.x,10.*(.2*.2*(3.-2.*.2))),"full numeric easing is an independently expected Hermite time map")
	var bounded:=true
	for departure in [0.,.25,.7,1.]:
		for arrival in [0.,.3,.8,1.]:
			var previous:=-1.
			for step in range(101):
				var value:=Easing.warp(float(step)/100.,departure,arrival)
				bounded=bounded and value>=previous-1e-12 and value>=-1e-12 and value<=1.+1e-12;previous=value
	check(bounded,"all sampled control combinations are monotone and bounded")
	var ease_keys: Array=[key(0,0.,"ease"),key(10,10.)]
	var old_ease:=Easing.compile(ease_keys,[],10)
	check(same(Easing.sample(old_ease,2),Timeline.sample(ease_keys,2)),"legacy fixed Ease keeps its old curve")
	var composed:=Easing.compile(ease_keys,[{"frame":0,"arrive":0.,"leave":1.}],10)
	var t:=2.*.2*.2-.2*.2*.2
	check(is_equal_approx(Easing.sample(composed,2).position.x,10.*t*t*(3.-2.*t)),"numeric controls compose with the retained fixed Ease shape")
	var hold_keys: Array=[key(0,0.,"hold"),key(10,10.)]
	check(same(Easing.sample(Easing.compile(hold_keys,[],10),5),Timeline.sample(hold_keys,5)),"untouched Hold stays a step")
	check(Easing.compile(hold_keys,[{"frame":0,"arrive":0.,"leave":1.}],10).has("error"),"affected Hold refuses without rewriting interpolation")
	var baked:=Easing.bake(leave)
	var anchors_preserved:=true
	for anchor in original:
		var found:=false
		for result in baked.keys:
			if result.frame==anchor.frame:found=result==anchor
		anchors_preserved=anchors_preserved and found
	check(baked.added_keys==9 and anchors_preserved and keys==original,"Bake inserts only missing selected frames and preserves all authored dictionaries")
	var replay:=true
	for frame in range(21):replay=replay and same(Timeline.sample(baked.keys,frame),Easing.sample(leave,frame))
	check(replay and baked.integer_frames_sampled and not baked.subframe_equality_qualified,"ordinary baked keys reproduce integer preview samples without a subframe claim")
	check(Easing.bake(leave)==baked and Easing.compile(keys,leave.controls,20)==leave,"Recalculate and Bake are deterministic and do not accumulate helpers")
	var extra:=baked.keys.duplicate(true);extra[1].position[0]=999.
	check(keys==original and Easing.sample(leave,1).position.x!=999.,"returned Bake is independent of authored source and preview plan")
	var altered:=leave.duplicate(true);altered.controls[0].leave=0.
	check(Easing.sample(altered,1).has("error"),"recipe mutation after compile is refused")
	altered=leave.duplicate(true);altered.source_keys[0].position[0]=99.
	check(Easing.bake(altered).has("error"),"source mutation inside a frozen preview is refused")
	check(not Easing.matches(leave,[key(0,1.),key(10,10.),key(20,20.,"ease")],20) and not Easing.matches(leave,keys,21),"changed authored keys or duration invalidate the preview")
	var invalid:=0
	for value in [-.1,1.1,NAN,INF,true,".5"]:
		if Easing.compile(keys,[{"frame":0,"arrive":0.,"leave":value}],20).has("error"):invalid+=1
	check(invalid==6,"nonfinite Boolean textual and out-of-range percentages refuse")
	check(Easing.compile(keys,[{"frame":5,"arrive":0.,"leave":1.}],20).has("error") and Easing.compile(keys,[{"frame":0,"arrive":0.,"leave":1.},{"frame":0,"arrive":1.,"leave":0.}],20).has("error"),"non-key and duplicate control ownership refuses")
	check(Easing.compile([keys[1],keys[0]],[],20).has("error") and Easing.compile([keys[0],keys[0]],[],20).has("error"),"unordered or duplicate authored frames refuse")
	var bad:=keys.duplicate(true);bad[0].rotation_xyzw=[0,0,0,0]
	check(Easing.compile(bad,[],20).has("error") and Easing.sample(leave,1.5).has("error"),"invalid quaternion and fractional sample frame refuse")
	var cap:=Easing.compile([key(0,0.),key(240,10.)],[{"frame":0,"arrive":0.,"leave":1.}],240)
	check(Easing.bake(cap).keys.size()==241,"exact existing 241-key boundary is admitted")
	var overflow:=Easing.compile([key(0,0.),key(241,10.)],[{"frame":0,"arrive":0.,"leave":1.}],241)
	check(Easing.bake(overflow).has("error") and overflow.source_keys.size()==2,"over-budget Bake refuses before changing source")
	print("KEYFRAME_EASING_MATH_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"application_adopted":false,"native_or_gpu_started":false}))
	quit(0 if failures==0 else 1)
