extends SceneTree
const Drawing=preload("res://src/drawing.gd")
class LessonApp:
	extends RefCounted
	var frame:=24
	var layers: Array=[]
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var image:=Drawing.blank(256,1)
	for i in range(256):image.set_pixel(i,0,Color8(22,45,88,i))
	var bytes:=image.get_data();var faded:=Drawing.faded(image,.5).get_data();var correct:=true
	for i in range(256):
		if faded[i*4]!=22 or faded[i*4+1]!=45 or faded[i*4+2]!=88 or faded[i*4+3]!=roundi(i*.5):correct=false
	check(correct and image.get_data()==bytes,"all256 alpha values round exactly while original straight RGB and pixels stay unchanged")
	check(is_same(Drawing.faded(image,1),image),"full opacity reuses the unchanged original image")
	for value in [-.1,1.1,NAN,INF,true,"0.5",null]:check(not Drawing.opacity_error([{"opacity":value}]).is_empty(),"invalid opacity refuses: "+str(value))
	check(Drawing.opacity_error([{}, {"opacity":0},{"opacity":.25},{"opacity":1}]).is_empty(),"old missing field and normalized endpoints remain valid")
	var full:=Drawing.blank(1920,1080);full.fill(Color8(255,40,60,203));var start:=Time.get_ticks_usec();var first:=Drawing.layer_image(full,.5);var full_ms:=(Time.get_ticks_usec()-start)/1000.0
	var pixels:=Drawing.opacity_pixels;var builds:=Drawing.opacity_builds
	check(is_same(first,Drawing.layer_image(full,.5)) and Drawing.opacity_pixels==pixels and Drawing.opacity_builds==builds,"held images reuse exact cached faded pixels without another traversal")
	full.fill_rect(Rect2i(100,100,10,12),Color.BLUE);Drawing.touch(full,Rect2i(100,100,10,12));start=Time.get_ticks_usec();var patch:=Drawing.layer_image(full,.5);var patch_ms:=(Time.get_ticks_usec()-start)/1000.0
	check(Drawing.opacity_pixels-pixels==120 and patch.get_pixel(101,101).b==1 and patch.get_data()[(101*1920+101)*4+3]==128 and patch.get_data()[3]==102,"a small dirty region updates only120 pixels, preserving unchanged alpha")
	check(patch.get_data()==Drawing.faded(full,.5).get_data(),"partial refresh equals an independent whole-image opacity calculation exactly")
	full.fill_rect(Rect2i(5,5,2,2),Color.BLACK);Drawing.touch(full,Rect2i(5,5,2,2));full.fill_rect(Rect2i(20,20,2,2),Color.WHITE);Drawing.touch(full,Rect2i(20,20,2,2));pixels=Drawing.opacity_pixels
	check(Drawing.layer_image(full,.5).get_data()==Drawing.faded(full,.5).get_data() and Drawing.opacity_pixels-pixels==17*17,"multiple pending strokes accumulate their dirty union")
	full.fill(Color.GREEN);Drawing.touch(full);pixels=Drawing.opacity_pixels
	check(Drawing.layer_image(full,.5).get_data()==Drawing.faded(full,.5).get_data() and Drawing.opacity_pixels-pixels==1920*1080,"whole-image replacements invalidate the complete cache")
	check(Drawing.layer_image(full,.2).get_data()==Drawing.faded(full,.2).get_data(),"changing opacity rebuilds the source image at the new amount")
	var source:=Drawing.blank(2,2);source.fill(Color.RED);var hidden:={"visible":true,"opacity":0.0,"cels":[{"start":0,"duration":8,"image":source}]};var old:=hidden.duplicate();old.erase("opacity")
	check(Drawing.composite([hidden],0,2,2).get_pixel(0,0).a==0 and Drawing.composite([old],0,2,2).get_pixel(0,0)==Color.RED,"zero opacity is absent while old layer output remains exact")
	var kept: Array=[]
	for i in range(8):var candidate:=Drawing.blank(2,2);kept.append(candidate);Drawing.layer_image(candidate,.5)
	check(Drawing.opacity_cache.size()==4,"derived cache stays bounded to four rasters across many cel images")
	var teacher=preload("res://src/tutorials.gd").new();var lesson:=LessonApp.new();teacher.app=lesson
	var ink:=Drawing.blank(16,16);ink.fill(Color8(255,0,0,1));lesson.layers=[{"name":"Ink","visible":true,"opacity":.01,"cels":[{"start":0,"duration":48,"image":ink}]}]
	check(not teacher.visible_ink(),"tutorial does not count paint that rounds to invisible after layer opacity")
	ink.fill(Color.RED);Drawing.touch(ink);lesson.layers[0].opacity=.25
	check(teacher.visible_ink(),"tutorial still recognizes actually visible faint ink");teacher.free()
	Drawing.opacity_cache.clear()
	print("OPACITY_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"full_hd_ms":full_ms,"patch120_ms":patch_ms}));quit(0 if failures==0 else 1)
