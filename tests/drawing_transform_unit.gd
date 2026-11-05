extends SceneTree
const Transform=preload("res://src/drawing_transform.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func calculate(data: PackedByteArray,rect: Rect2i,sx:=1.0,sy:=1.0,degrees:=90.0,copy:=false) -> Dictionary:return Transform.calculate(data,12,10,rect,sx,sy,degrees,copy)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var data:=PackedByteArray();data.resize(12*10*4);var rect:=Rect2i(4,3,3,2)
	for y in range(2):
		for x in range(3):
			var at:=((3+y)*12+4+x)*4;data[at]=(y*3+x+1)*30;data[at+1]=80;data[at+3]=255
	var original:=data.duplicate();var turned:=calculate(data,rect)
	check(turned.selection==Rect2i(4,3,2,3) and turned.changed,"quarter turn swaps width/height around a stable pixel-grid center")
	check(turned.data[(3*12+4)*4]==120 and turned.data[(3*12+5)*4]==30 and turned.data[(5*12+4)*4]==180,"positive rotation turns clockwise with exact opaque pixel permutation")
	var back:=calculate(turned.data,turned.selection,1,1,-90)
	check(back.data==original and data==original,"unclamped opposite quarter turn restores the original opaque raster and input remains untouched")
	var identity:=calculate(data,rect,1,1,0,true);check(not identity.changed and identity.data==original,"identity copy never builds up opacity or history")
	var scaled:=calculate(data,rect,2,2,0)
	check(scaled.selection.size==Vector2i(6,4) and scaled.data[(scaled.selection.position.y*12+scaled.selection.position.x)*4+3]==255,"axis-aligned resize keeps opaque outer edges and fits exact output bounds")
	var empty:=PackedByteArray();empty.resize(12*10*4)
	for i in range(120):empty[i*4]=255
	var invisible:=calculate(empty,rect,1.5,1.5,23);check(not invisible.changed and invisible.data==empty,"all-transparent source remains a no-op including hidden RGB")
	var corner:=calculate(data,Rect2i(0,0,3,2),2,2,30);check(not corner.has("error") and corner.repositioned and corner.selection.position==Vector2i.ZERO,"near-edge transform repositions the complete bounding box instead of cropping it")
	check(calculate(data,Rect2i(0,0,10,8),1,1,45).has("error"),"larger-than-frame rotation refuses without cutting source")
	check(calculate(data,rect,NAN,1,0).has("error") and calculate(data,rect,.049,1,0).has("error") and calculate(data,rect,4.01,1,0).has("error") and calculate(data,rect,1,1,181).has("error") and calculate(data,Rect2i(-1,0,2,2)).has("error"),"invalid scale/angle/selection refuses")
	var hidden:=PackedByteArray();hidden.resize(12*10*4);hidden[(3*12+4)*4+2]=255;hidden[(3*12+5)*4]=255;hidden[(3*12+5)*4+3]=255
	var edge:=calculate(hidden,Rect2i(4,3,2,1),2,2,17);var no_blue:=true
	for i in range(120):
		if edge.data[i*4+3]>0:no_blue=no_blue and edge.data[i*4+2]==0
	check(no_blue,"premultiplied interpolation cannot leak hidden blue RGB into visible red edges")
	var cases: Array=[]
	for serial in range(12):
		var w:=18+serial%3;var h:=16+serial%2;var bytes:=PackedByteArray();bytes.resize(w*h*4)
		for i in range(w*h):
			for ch in range(3):bytes[i*4+ch]=(i*31+ch*53+serial*11)%256
			bytes[i*4+3]=255 if serial<4 else [0,64,128,255][(i+serial)%4]
		var selected:=Rect2i(5,4,3+serial%3,2+serial%3)
		for parameters in [[1.0,1.0,90.0],[1.0,1.0,-90.0],[1.25,.75,17.0],[.5,1.5,-37.0]]:
			for copy in [false,true]:
				var result:=Transform.calculate(bytes,w,h,selected,parameters[0],parameters[1],parameters[2],copy)
				cases.append({"width":w,"height":h,"input":Marshalls.raw_to_base64(bytes),"output":Marshalls.raw_to_base64(result.data),"rect":[selected.position.x,selected.position.y,selected.size.x,selected.size.y],"scale":[parameters[0],parameters[1]],"angle":parameters[2],"copy":copy,"selection":[result.selection.position.x,result.selection.position.y,result.selection.size.x,result.selection.size.y],"changed":result.changed,"exact":serial<4 and absf(parameters[2])==90})
	var large:=PackedByteArray();large.resize(1920*1080*4)
	for y in range(400,540):
		for x in range(700,900):large[(y*1920+x)*4+1]=255;large[(y*1920+x)*4+3]=255
	var full:=Transform.calculate(large,1920,1080,Rect2i(700,400,200,140),1.15,1.15,27)
	check(full.changed and not full.has("error") and full.data.size()==large.size(),"free-angle transform on a full-HD document remains bounded")
	var report:={"checks":checks,"failures":failures,"full_hd_ms":full.worker_ms,"cases":cases};FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(report));report.erase("cases");print("DRAWING_TRANSFORM_UNIT ",JSON.stringify(report));quit(0 if failures==0 else 1)
