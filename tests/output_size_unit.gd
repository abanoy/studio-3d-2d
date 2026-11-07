extends SceneTree
const Sizes=preload("res://src/output_size.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	for id in ["1080p","720p","540p"]:check(Sizes.error(id).is_empty(),"known size accepted: "+id)
	for value in ["",true,1280,"4k"]:check(not Sizes.error(value).is_empty(),"unknown or mistyped profile refused: "+str(value))
	check(Sizes.project_error({}).is_empty(),"legacy metadata defaults without adding a field")
	for value in ["1080p","720p","540p"]:check(Sizes.project_error({"output_size":value}).is_empty(),"saved profile accepted: "+value)
	for value in [null,true,720,[],{},"4k"]:check(not Sizes.project_error({"output_size":value}).is_empty(),"invalid saved profile refuses: "+str(value))
	var full:=Image.create(1920,1080,false,Image.FORMAT_RGBA8);full.fill(Color(.2,.4,.6,1));var data:=full.get_data()
	check(is_same(Sizes.resample(full,Vector2i(1920,1080)),full) and full.get_data()==data,"default fullHD path preserves exact input and resource without resizing")
	var tiny:=Image.create(2,1,false,Image.FORMAT_RGBA8);tiny.set_pixel(0,0,Color(1,0,0,128.0/255));tiny.set_pixel(1,0,Color(0,1,0,0));var original:=tiny.get_data()
	var resized:=Sizes.resample(tiny,Vector2i.ONE);var pixel:=resized.get_data()
	check(pixel[0]>=254 and pixel[1]==0 and pixel[2]==0 and absi(int(pixel[3])-64)<=1,"independent half-coverage oracle keeps red hue and quarter alpha without hidden green bleed")
	check(tiny.get_data()==original and not is_same(tiny,resized),"alpha resizing never changes source pixels or resource")
	tiny.set_pixel(0,0,Color.RED);tiny.set_pixel(1,0,Color.GREEN);pixel=Sizes.resample(tiny,Vector2i.ONE).get_data()
	check(absi(int(pixel[0])-128)<=1 and absi(int(pixel[1])-128)<=1 and pixel[2]==0 and pixel[3]==255,"opaque center average matches independent two-pixel oracle")
	check(Sizes.resample(null,Vector2i.ONE)==null and Sizes.resample(tiny,Vector2i(0,1))==null and Sizes.resample(tiny,Vector2i(1921,1080))==null,"missing and out-of-budget resize requests refuse")
	print("OUTPUT_SIZE_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
