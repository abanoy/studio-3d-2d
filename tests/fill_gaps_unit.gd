extends SceneTree
const Fill=preload("res://src/fill.gd")
const Gaps=preload("res://src/fill_gaps.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func fill(image: Image,gap: int,point:=Vector2i(20,15),target: Image=null) -> Dictionary:
	return Fill.calculate(image.get_data(),(target if target else image).get_data(),image.get_width(),image.get_height(),point,PackedByteArray([20,200,230,180]),0,gap)
func rectangle(gap: int) -> Image:
	var image:=Drawing.blank(40,32)
	for x in range(5,35):image.set_pixel(x,5,Color.BLACK);image.set_pixel(x,26,Color.BLACK)
	for y in range(5,27):image.set_pixel(5,y,Color.BLACK);image.set_pixel(34,y,Color.BLACK)
	for x in range(18,18+gap):image.set_pixel(x,5,Color.TRANSPARENT)
	return image
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for gap in range(1,9):
		var image:=rectangle(gap);var original:=image.get_data();var result:=fill(image,gap)
		check(not result.has("error") and result.region==560 and not result.edge and result.sealed_pixels>=gap,"gap%d closes without spilling or shifting the interior"%gap)
		check(image.get_data()==original and result.data[(5*40+18)*4+3]==0 and result.data[(15*40+5)*4+3]==255,"gap%d preserves original line and virtual-gap pixels"%gap)
		var open:=fill(image,gap-1);check(not open.has("error") and open.edge,"gap%d stays open below its selected threshold"%gap)
	var sample:=rectangle(3);var separate:=Drawing.blank(40,32);var result:=fill(sample,3,Vector2i(20,15),separate)
	check(result.data[(15*40+20)*4+3]==180 and result.data[(15*40+5)*4+3]==0,"separate color layer contains only exact fill RGBA, not sampled lines")
	var narrow:=Drawing.blank(9,9);narrow.fill(Color.BLACK)
	for y in range(9):narrow.set_pixel(4,y,Color.TRANSPARENT)
	check(fill(narrow,2,Vector2i(4,4)).has("error"),"removed narrow seed region refuses rather than painting an unrelated area")
	check(fill(sample,-1).has("error") and fill(sample,9).has("error"),"gap values outside0-8 refuse before work")
	var blank:=Drawing.blank(1920,1080);var full:=fill(blank,8,Vector2i(900,500))
	check(full.region==1920*1080 and full.edge and full.sealed_pixels==0,"gap filter invents no boundary on a full-HD empty canvas")
	var cases: Array=[]
	for dimensions in [Vector2i(1,1),Vector2i(2,13),Vector2i(17,2),Vector2i(19,15)]:
		var mask:=PackedByteArray();mask.resize(dimensions.x*dimensions.y)
		for i in range(mask.size()):mask[i]=int((i*17+i*i*3)%13>=3)
		for gap in range(1,9):cases.append({"width":dimensions.x,"height":dimensions.y,"gap":gap,"input":Marshalls.raw_to_base64(mask),"output":Marshalls.raw_to_base64(Gaps.close(mask,dimensions.x,dimensions.y,gap))})
	var result_data:={"checks":checks,"failures":failures,"full_hd_ms":full.worker_ms,"cases":cases};FileAccess.open(OS.get_cmdline_user_args()[0].path_join("domain.json"),FileAccess.WRITE).store_string(JSON.stringify(result_data));print("FILL_GAPS_UNIT ",JSON.stringify({"checks":checks,"failures":failures,"full_hd_ms":full.worker_ms}));quit(0 if failures==0 else 1)
