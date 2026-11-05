extends SceneTree
const Fill=preload("res://src/fill.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func calculate(image: Image,point: Vector2i,connections: int,tolerance:=0) -> Dictionary:
	return Fill.calculate(image.get_data(),Drawing.blank(image.get_width(),image.get_height()).get_data(),image.get_width(),image.get_height(),point,PackedByteArray([30,160,220,170]),tolerance,0,0,connections)
func record(cases: Array,sample: PackedByteArray,target: PackedByteArray,size: Vector2i,point: Vector2i,connections: int,gap:=0,grow:=0,tolerance:=0) -> void:
	var r:=Fill.calculate(sample,target,size.x,size.y,point,PackedByteArray([30,160,220,170]),tolerance,gap,grow,connections)
	var c:={"width":size.x,"height":size.y,"point":[point.x,point.y],"connections":connections,"gap":gap,"grow":grow,"tolerance":tolerance,"sample":Marshalls.raw_to_base64(sample),"target":Marshalls.raw_to_base64(target),"error":r.has("error")}
	if not c.error:
		c.merge({"output":Marshalls.raw_to_base64(r.data),"region":r.region,"expanded":r.expanded_pixels,"changed":r.changed,"edge":r.edge,"peak":r.pending_peak,"actual_connections":r.connectivity,"bounds":[r.bounds.position.x,r.bounds.position.y,r.bounds.size.x,r.bounds.size.y]})
	cases.append(c)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var corner:=Drawing.blank(2,2);corner.set_pixel(1,0,Color.BLACK);corner.set_pixel(0,1,Color.BLACK);var original:=corner.get_data()
	check(calculate(corner,Vector2i.ZERO,4).region==1 and calculate(corner,Vector2i.ZERO,8).region==2,"diagonal pixels stay separate with edges only and join with corners")
	check(calculate(corner,Vector2i(1,1),8).region==2 and corner.get_data()==original,"diagonal traversal works in reverse and leaves the source unchanged")
	var defaults:=Fill.calculate(original,original,2,2,Vector2i.ZERO,PackedByteArray([30,160,220,170]),0);var explicit:=Fill.calculate(original,original,2,2,Vector2i.ZERO,PackedByteArray([30,160,220,170]),0,0,0,4)
	check(defaults.data==explicit.data and defaults.region==explicit.region and defaults.connectivity==4,"omitted connectivity preserves exact four-connected behavior")
	check(calculate(corner,Vector2i.ZERO,0).has("error") and calculate(corner,Vector2i.ZERO,6).has("error") and calculate(corner,Vector2i.ZERO,9).has("error"),"only4and8 are accepted")
	var gradient:=Drawing.blank(3,3);gradient.fill(Color.WHITE)
	for i in range(3):gradient.set_pixel(i,i,Color8(i*10,i*10,i*10))
	check(calculate(gradient,Vector2i.ZERO,8,12).region==2 and calculate(gradient,Vector2i.ZERO,4,12).region==1,"corner mode keeps seed-based tolerance without gradient drift")
	var thin:=Drawing.blank(1,13);check(calculate(thin,Vector2i(0,6),8).region==13,"one-pixel-wide canvas has no wrapping or diagonal overflow")
	var checker:=Drawing.blank(513,257);checker.fill(Color.BLACK)
	for y in range(257):
		for x in range(513):
			if (x+y)%2==0:checker.set_pixel(x,y,Color.TRANSPARENT)
	var connected:=calculate(checker,Vector2i.ZERO,8)
	check(connected.region==65921 and connected.pending_peak<=513*257 and connected.edge,"large checkerboard joins through corners with a bounded pending frontier")
	var blank:=Drawing.blank(1920,1080);var full:=calculate(blank,Vector2i(900,500),8)
	check(full.region==1920*1080 and full.changed==1920*1080 and full.pending_peak<=1920*1080 and full.edge,"eight-connected full-HD traversal is iterative and bounded")
	var cases: Array=[]
	# Every binary3x3 pattern, every seed, both graph definitions.
	for bits in range(512):
		var sample:=PackedByteArray();sample.resize(36);var target:=sample.duplicate()
		for i in range(9):
			sample[i*4+3]=255 if (bits&(1<<i))!=0 else 0
			if sample[i*4+3]==0:sample[i*4]=i*23;sample[i*4+1]=71
			for c in range(4):target[i*4+c]=(i*7+c*53)%256
		for seed in range(9):
			for connections in [4,8]:record(cases,sample,target,Vector2i(3,3),Vector2i(seed%3,int(seed/3)),connections)
	# Independent oracle also checks morphology ordering, tolerance, irregular sizes
	# and rejected narrow seeds with the new connectivity selection.
	for serial in range(12):
		var size:=Vector2i(7+serial%4,5+serial%3);var sample:=PackedByteArray();sample.resize(size.x*size.y*4);var target:=sample.duplicate()
		for i in range(size.x*size.y):
			var alpha:=255 if (i*17+i*i*3+serial)%13<4 else 0
			for c in range(3):sample[i*4+c]=(i*19+c*7)%23
			sample[i*4+3]=alpha
			for c in range(4):target[i*4+c]=(i*7+c*53)%256
		for connections in [4,8]:
			for gap in range(3):
				for grow in range(3):record(cases,sample,target,size,Vector2i(int(size.x/2),int(size.y/2)),connections,gap,grow,12)
	var report:={"checks":checks,"failures":failures,"full_hd_ms":full.worker_ms,"checker_ms":connected.worker_ms,"checker_peak":connected.pending_peak,"cases":cases}
	FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(report));report.erase("cases");print("FILL_CONNECTIONS_UNIT ",JSON.stringify(report));quit(0 if failures==0 else 1)
