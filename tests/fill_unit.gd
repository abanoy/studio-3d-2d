extends SceneTree
const Fill=preload("res://src/fill.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func calculate(image: Image,point: Vector2i,target: Image=null,tol:=0) -> Dictionary:
	return Fill.calculate(image.get_data(),(target if target else image).get_data(),image.get_width(),image.get_height(),point,PackedByteArray([250,30,60,180]),tol)
func run() -> void:
	var source:=Drawing.blank(12,10)
	for x in range(2,10):source.set_pixel(x,2,Color.BLACK);source.set_pixel(x,8,Color.BLACK)
	for y in range(2,9):source.set_pixel(2,y,Color.BLACK);source.set_pixel(9,y,Color.BLACK)
	var original:=source.get_data();var result:=calculate(source,Vector2i(4,4));var image:=Image.create_from_data(12,10,false,Image.FORMAT_RGBA8,result.data)
	check(result.region==30 and result.changed==30 and not result.edge,"closed boundary fills exactly its four-connected interior")
	check(result.bounds==Rect2i(3,3,6,5),"changed bounds are exact")
	check(source.get_data()==original and image.get_pixel(2,4)==Color.BLACK and image.get_pixel(0,0).a==0,"input, outline and exterior remain byte-identical")
	check(result.data[(4*12+4)*4+3]==180,"fill replaces with exact selected alpha")
	var transparent:=Drawing.blank(12,10);var separate:=calculate(source,Vector2i(4,4),transparent)
	check(separate.region==30 and separate.data[(4*12+4)*4]==250 and separate.data[(4*12+2)*4+3]==0 and transparent.get_data()==Drawing.blank(12,10).get_data(),"separate target fills inside sampled lines without copying or changing them")
	var repeat:=calculate(image,Vector2i(4,4));check(repeat.changed==0 and repeat.region==30,"identical fill is a true no-op")
	var outside:=calculate(source,Vector2i.ZERO);check(outside.edge and outside.region==64,"outside region reports canvas-edge spill")
	var diagonal:=Drawing.blank(2,2);diagonal.set_pixel(1,0,Color.BLACK);diagonal.set_pixel(0,1,Color.BLACK)
	check(calculate(diagonal,Vector2i.ZERO).region==1,"diagonal corners do not join under four-connectivity")
	var hidden:=Drawing.blank(2,1);hidden.set_pixel(1,0,Color(1,.4,.2,0));check(calculate(hidden,Vector2i.ZERO).region==2,"transparent hidden RGB cannot create false boundaries")
	var gradient:=Drawing.blank(3,1);gradient.set_pixel(0,0,Color8(0,0,0));gradient.set_pixel(1,0,Color8(10,10,10));gradient.set_pixel(2,0,Color8(20,20,20))
	check(calculate(gradient,Vector2i.ZERO,null,12).region==2,"tolerance compares to the seed rather than drifting along a gradient")
	check(calculate(gradient,Vector2i.ZERO).region==1,"zero tolerance preserves exact color boundaries")
	check(Fill.calculate(original,original,12,10,Vector2i(-1,0),PackedByteArray([1,2,3,4]),0).has("error"),"outside click refused")
	check(Fill.calculate(original,original,12,10,Vector2i.ZERO,PackedByteArray([1,2,3,4]),256).has("error"),"invalid tolerance refused")
	check(Fill.calculate(PackedByteArray(),original,12,10,Vector2i.ZERO,PackedByteArray([1,2,3,4]),0).has("error"),"wrong byte count refused before scanning")
	check(Fill.calculate(PackedByteArray(),PackedByteArray(),3000,3000,Vector2i.ZERO,PackedByteArray([1,2,3,4]),0).has("error"),"oversized canvas refused")
	# Independent tiny BFS oracle, including disconnected holes/branches.
	var test:=Drawing.blank(31,29)
	for y in range(29):
		for x in range(31):
			if (x*17+y*13+x*y)%7<2:test.set_pixel(x,y,Color.BLACK)
	var selected:={};var queue: Array[Vector2i]=[Vector2i(5,5)];var seed:=test.get_pixel(5,5)
	while not queue.is_empty():
		var p: Vector2i=queue.pop_back()
		if p.x<0 or p.y<0 or p.x>=31 or p.y>=29 or selected.has(p) or test.get_pixel(p.x,p.y)!=seed:continue
		selected[p]=true
		for d in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:queue.append(p+d)
	var actual:=calculate(test,Vector2i(5,5));check(actual.region==selected.size(),"scanline region agrees with independent BFS oracle")
	var expected: Image=test.duplicate()
	for p in selected:expected.set_pixel(p.x,p.y,Color8(250,30,60,180))
	check(actual.data==expected.get_data(),"every selected and untouched oracle pixel agrees exactly")
	var full:=Drawing.blank(1920,1080);var large:=calculate(full,Vector2i(900,500));check(large.region==1920*1080 and large.changed==1920*1080 and large.edge,"full-HD region uses bounded iterative traversal without recursion")
	print("FILL_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"full_hd_ms":large.worker_ms}));quit(0 if failures==0 else 1)
