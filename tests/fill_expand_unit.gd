extends SceneTree
const Fill=preload("res://src/fill.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func calculate(sample: Image,target: Image,radius: int,point:=Vector2i(16,12),gap:=0) -> Dictionary:
	return Fill.calculate(sample.get_data(),target.get_data(),sample.get_width(),sample.get_height(),point,PackedByteArray([30,160,220,170]),0,gap,radius)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var sample:=Drawing.blank(32,24);var target:=Drawing.blank(32,24)
	for rect in [Rect2i(5,5,22,1),Rect2i(5,18,22,1),Rect2i(5,5,1,14),Rect2i(26,5,1,14)]:sample.fill_rect(rect,Color.BLACK)
	var original:=sample.get_data();var untouched:=target.get_data()
	for radius in range(9):
		var result:=calculate(sample,target,radius)
		var bounds:=Rect2i(6-radius,6-radius,20+radius*2,12+radius*2).intersection(Rect2i(0,0,32,24))
		check(result.region==240 and result.changed==bounds.get_area() and result.expanded_pixels==bounds.get_area()-240 and result.bounds==bounds,"radius%d grows the discovered region by exact clipped square distance"%radius)
		check(sample.get_data()==original and target.get_data()==untouched,"radius%d leaves sampled ink and target snapshots unchanged"%radius)
	check(calculate(sample,target,-1).has("error") and calculate(sample,target,9).has("error"),"out-of-range expansion refuses")
	var all_paint:=Drawing.blank(32,24);all_paint.fill(Color8(30,160,220,170));var noop:=calculate(sample,all_paint,8)
	check(noop.changed==0 and noop.bounds==Rect2i(),"already-identical target is a no-op even with expansion")
	var broken:=sample.duplicate();broken.fill_rect(Rect2i(15,5,2,1),Color.TRANSPARENT);var sealed:=calculate(broken,target,1,Vector2i(16,12),2)
	check(not sealed.edge and sealed.region==240 and sealed.expanded_pixels>0 and sealed.data[(5*32+15)*4+3]==170 and broken.get_pixel(15,5).a==0,"growth can cover a virtual closure without drawing a new source line")
	var blank:=Drawing.blank(1920,1080);var full:=calculate(blank,blank,8,Vector2i(900,500))
	check(full.region==1920*1080 and full.expanded_pixels==0 and full.changed==1920*1080 and full.edge,"full-HD expansion is bounded and invents no extra canvas pixels")
	var cases: Array=[]
	for size in [Vector2i(1,1),Vector2i(2,13),Vector2i(17,2),Vector2i(19,15),Vector2i(32,24)]:
		var image:=Drawing.blank(size.x,size.y);var pixels:=image.get_data();var bytes:=pixels.duplicate()
		for i in range(size.x*size.y):
			pixels[i*4]=(i*31)%256;pixels[i*4+1]=91;pixels[i*4+3]=255 if (i*17+i*i*3)%13<3 else 0
			for c in range(4):bytes[i*4+c]=(i*7+c*53)%256
		var point:=Vector2i(int(size.x/2),int(size.y/2));pixels[(point.y*size.x+point.x)*4+3]=0
		for radius in range(9):
			var result:=Fill.calculate(pixels,bytes,size.x,size.y,point,PackedByteArray([30,160,220,170]),0,0,radius)
			cases.append({"width":size.x,"height":size.y,"radius":radius,"point":[point.x,point.y],"sample":Marshalls.raw_to_base64(pixels),"target":Marshalls.raw_to_base64(bytes),"output":Marshalls.raw_to_base64(result.data),"region":result.region,"expanded":result.expanded_pixels,"changed":result.changed,"edge":result.edge,"bounds":[result.bounds.position.x,result.bounds.position.y,result.bounds.size.x,result.bounds.size.y]})
	var report:={"checks":checks,"failures":failures,"full_hd_ms":full.worker_ms,"cases":cases}
	FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(report));report.erase("cases");print("FILL_EXPAND_UNIT ",JSON.stringify(report));quit(0 if failures==0 else 1)
