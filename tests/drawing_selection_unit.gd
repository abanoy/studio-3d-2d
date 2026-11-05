extends SceneTree
const Selection=preload("res://src/drawing_selection.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	check(Selection.rectangle(Vector2(14.9,10.8),Vector2(3.2,2.9),Vector2i(20,15))==Rect2i(3,2,11,8),"reverse marquee snaps to output pixels without resampling")
	check(Selection.rectangle(Vector2(-500,-300),Vector2(900,600),Vector2i(20,15))==Rect2i(0,0,20,15),"marquee clips at canvas boundaries")
	check(not Selection.rectangle(Vector2(NAN,1),Vector2.ONE,Vector2i(20,15)).has_area(),"nonfinite pointer cannot create an invalid selection")
	var image:=Drawing.blank(12,10);image.fill_rect(Rect2i(2,2,3,2),Color.RED);var original:=image.get_data();var rect:=Rect2i(2,2,3,2)
	var moved:=Selection.move(image,rect,Vector2i(2,1));var copied:=Selection.move(image,rect,Vector2i(2,1),true)
	check(moved.changed and moved.image.get_pixel(2,2).a==0 and moved.image.get_pixel(4,3)==Color.RED and image.get_data()==original,"overlapping move uses a detached patch and preserves source")
	check(copied.image.get_pixel(2,2)==Color.RED and copied.image.get_pixel(4,3)==Color.RED,"copy leaves original pixels intact")
	var clamped:=Selection.move(image,rect,Vector2i(900,-900))
	check(clamped.offset==Vector2i(7,-2) and clamped.selection==Rect2i(9,0,3,2) and clamped.image.get_pixel(11,1)==Color.RED,"entire selection stays inside the canvas without clipping away pixels")
	image.set_pixel(2,2,Color(1,0,0,0.5));original=image.get_data()
	check(not Selection.move(image,rect,Vector2i.ZERO,true).changed and image.get_data()==original,"stationary Shift-click never stacks opacity")
	var empty:=Drawing.blank(12,10);empty.fill(Color(1,0.3,0.6,0));var hidden:=empty.get_data()
	check(not Selection.move(empty,rect,Vector2i(3,3)).changed and empty.get_data()==hidden,"fully transparent selection preserves even hidden RGB and creates no edit")
	check(Selection.move(image,Rect2i(-1,0,2,2),Vector2i.ONE).has("error") and Selection.move(image,Rect2i(11,9,3,3),Vector2i.ONE).has("error") and Selection.move(image,Rect2i(),Vector2i.ONE).has("error"),"invalid/empty selection refuses before editing")
	var rgb:=Image.create(4,4,false,Image.FORMAT_RGB8);check(Selection.move(rgb,Rect2i(0,0,2,2),Vector2i.ONE).has("error"),"non-RGBA image refuses")
	var cases: Array=[];var preserved:=true
	for serial in range(24):
		var w:=9+serial%4;var h:=7+serial%3;var bytes:=PackedByteArray();bytes.resize(w*h*4)
		for i in range(w*h):
			for channel in range(3):bytes[i*4+channel]=(i*31+channel*53+serial*11)%256
			bytes[i*4+3]=([0,64,128,255][(i+serial)%4] if serial>=8 else [0,255][(i+serial)%2])
		var source:=Image.create_from_data(w,h,false,Image.FORMAT_RGBA8,bytes);var selection:=Rect2i(1+serial%2,1,3+serial%3,3)
		for copy in [false,true]:
			for delta in [Vector2i(-99,99),Vector2i(1,1),Vector2i(-1,0),Vector2i.ZERO]:
				var result:=Selection.move(source,selection,delta,copy)
				preserved=preserved and source.get_data()==bytes
				cases.append({"width":w,"height":h,"input":Marshalls.raw_to_base64(bytes),"output":Marshalls.raw_to_base64(result.image.get_data()),"rect":[selection.position.x,selection.position.y,selection.size.x,selection.size.y],"requested":[delta.x,delta.y],"offset":[result.offset.x,result.offset.y],"copy":copy,"changed":result.changed,"exact":serial<8})
	check(preserved,"all independent-oracle input images remain byte-identical")
	var large:=Drawing.blank(1920,1080);large.fill_rect(Rect2i(200,200,1200,700),Color.CYAN);var started:=Time.get_ticks_usec();var large_result:=Selection.move(large,Rect2i(200,200,1200,700),Vector2i(100,50));var large_ms:=(Time.get_ticks_usec()-started)/1000.0
	check(large_result.changed and large_result.image.get_pixel(1499,949)==Color.CYAN and large.get_pixel(1499,949).a==0,"large full-HD selection translates without clipping and preserves source")
	var report:={"checks":checks,"failures":failures,"large_ms":large_ms,"cases":cases};FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(report));report.erase("cases");print("DRAWING_SELECTION_UNIT ",JSON.stringify(report));quit(0 if failures==0 else 1)
