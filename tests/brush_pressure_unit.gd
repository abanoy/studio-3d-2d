extends SceneTree
const Brush=preload("res://src/brush_stroke.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func pen():
	var result=Brush.new();result.radius=20;result.pressure_size=true;result.ink=Color.CYAN;return result
func _initialize() -> void:
	var a:=Vector2(16,32);var b:=Vector2(112,32);var image:=Drawing.blank(128,64);var brush=pen()
	check(brush.paint(image,a,b,2,14),"a sparse pressure segment paints a continuous taper")
	check(image.get_pixel(20,39).a==0 and image.get_pixel(108,39).a>.99,"light pressure is narrow and stronger pressure widens")
	var original:=image.get_data();brush.paint(image,a,b,2,14)
	check(original==image.get_data(),"repeating the same pressure segment leaves opacity exact")
	var dense:=Drawing.blank(128,64);var segments=pen()
	for x in range(16,112):segments.paint(dense,Vector2(x,32),Vector2(x+1,32),2+(x-16)*.125,2+(x+1-16)*.125)
	var maximum:=0;var raw:=dense.get_data()
	for i in range(3,raw.size(),4):maximum=maxi(maximum,absi(raw[i]-original[i]))
	check(maximum<=1,"linear pressure subdivisions agree within one RGBA8 alpha unit")
	var cap:=Drawing.blank(64,64);pen().paint(cap,Vector2(30,32),Vector2(32,32),1,12)
	var circle:=Drawing.blank(64,64);Drawing.stroke(circle,Vector2(32,32),Vector2(32,32),12,Color.CYAN,false)
	check(cap.get_data()==circle.get_data(),"rapid widening correctly contains the smaller starting disc")
	var stationary:=Drawing.blank(64,64);pen().paint(stationary,Vector2(32,32),Vector2(32,32),12,1)
	check(stationary.get_data()==circle.get_data(),"stationary pressure change uses the maximum radius without division by zero")
	var opacity:=Drawing.blank(128,64);var faint=pen();faint.opacity=.4;faint.paint(opacity,a,b,2,14)
	check(absf(opacity.get_pixel(70,32).a-.4)<.005,"pressure controls size independently of stroke opacity")
	var erased:=Drawing.blank(128,64);erased.fill(Color(.2,.4,.6,.8));var eraser=pen();eraser.erase=true;eraser.opacity=.25;eraser.paint(erased,a,b,2,14)
	check(absf(erased.get_pixel(70,32).a-.6)<.005 and erased.get_pixel(20,39).a>.79,"gentle erasing follows the tapered footprint")
	var empty:=Drawing.blank(64,64);var bad=pen();check(not bad.paint(empty,a,b,NAN,5) and bad.before.is_empty(),"nonfinite radius refuses before allocating tiles")
	check(not bad.paint(empty,a,b,5,65) and bad.before.is_empty(),"pressure radius cannot exceed the64pixel brush limit")
	var cases: Array=[]
	for spec in [[Vector2(7,9),Vector2(57,39),1.5,11.0],[Vector2(7,9),Vector2(57,39),11.0,1.5],[Vector2(30,20),Vector2(32,21),1.0,12.0],[Vector2(30,20),Vector2(32,21),12.0,1.0],[Vector2(20,20),Vector2(20,20),2.0,9.0],[Vector2(-3,-2),Vector2(64,47),.25,8.0]]:
		var sample:=Drawing.blank(64,48);pen().paint(sample,spec[0],spec[1],spec[2],spec[3]);cases.append({"from":[spec[0].x,spec[0].y],"to":[spec[1].x,spec[1].y],"radii":[spec[2],spec[3]],"rgba":Marshalls.raw_to_base64(sample.get_data())})
	var result:={"checks":checks,"failures":failures,"subdivision_alpha_error":maximum,"reference_cases":cases}
	FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(result));print("BRUSH_PRESSURE_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
