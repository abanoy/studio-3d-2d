extends SceneTree
const Brush=preload("res://src/brush_stroke.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func brush(amount: float,erase: bool=false):
	var result=Brush.new();result.radius=5;result.ink=Color.RED;result.opacity=amount;result.erase=erase;return result
func _initialize() -> void:
	var image:=Drawing.blank(150,80);var pen=brush(.5)
	pen.paint(image,Vector2(8,40),Vector2(140,40))
	check(absf(image.get_pixel(70,40).a-.5)<.005,"half-opacity pen creates half-alpha pixels")
	var first:=image.get_data()
	pen.paint(image,Vector2(140,40),Vector2(8,40))
	check(first==image.get_data(),"retrace within the same stroke does not darken")
	var segmented:=Drawing.blank(150,80);var many=brush(.5)
	for x in range(8,140):many.paint(segmented,Vector2(x,40),Vector2(x+1,40))
	check(first==segmented.get_data(),"dense and sparse collinear events produce identical alpha including edges")
	brush(.5).paint(image,Vector2(8,40),Vector2(140,40))
	check(absf(image.get_pixel(70,40).a-.75)<.005,"a separate stroke builds opacity normally")
	var opaque:=Drawing.blank(150,80);opaque.fill(Color(.2,.4,.7,.8));var eraser=brush(.25,true)
	eraser.ink.a=0;eraser.paint(opaque,Vector2(8,40),Vector2(140,40));var erased:=opaque.get_data()
	check(absf(opaque.get_pixel(70,40).a-.6)<.005,"eraser strength multiplies original alpha independently of color alpha")
	eraser.paint(opaque,Vector2(140,40),Vector2(8,40));check(opaque.get_data()==erased,"gentle erasing is even on a retrace")
	var under:=opaque.get_pixel(70,40);check(absf(under.r-.2)<.005 and absf(under.g-.4)<.005 and absf(under.b-.7)<.005,"erasing retains straight RGB")
	var tinted:=Drawing.blank(150,80);var translucent=brush(.5);translucent.ink.a=.5
	translucent.paint(tinted,Vector2(8,40),Vector2(140,40));check(absf(tinted.get_pixel(70,40).a-.25)<.005,"color alpha and brush opacity multiply")
	var untouched:=Drawing.blank(150,80);var zero=brush(0)
	check(not zero.paint(untouched,Vector2(8,40),Vector2(140,40)) and zero.before.is_empty(),"zero strength stores no tiles and changes no image")
	var full:=Drawing.blank(150,80);var legacy:=Drawing.blank(150,80)
	brush(1).paint(full,Vector2(8.3,12.7),Vector2(140.8,75.2));Drawing.stroke(legacy,Vector2(8.3,12.7),Vector2(140.8,75.2),5,Color.RED,false)
	check(full.get_data()==legacy.get_data(),"default full opacity retains legacy raster bytes")
	var edge:=Drawing.blank(65,65);var clipped=brush(.5);clipped.paint(edge,Vector2.ZERO,Vector2(64,64))
	check(edge.get_pixel(64,64).a>0 and clipped.before.has(Vector2i(64,64)) and clipped.before[Vector2i(64,64)].get_size()==Vector2i.ONE,"clipped single-pixel corner tiles are supported")
	var restored:=edge.duplicate()
	for pos in clipped.before:restored.blit_rect(clipped.before[pos],Rect2i(Vector2i.ZERO,clipped.before[pos].get_size()),pos)
	check(restored.get_data()==Drawing.blank(65,65).get_data(),"captured sparse tiles restore every touched pixel exactly")
	var invalid=brush(NAN);check(not invalid.paint(edge,Vector2.ZERO,Vector2.ONE) and invalid.before.is_empty(),"nonfinite strength refuses without edits")
	check(not clipped.paint(edge,Vector2(INF,1),Vector2.ZERO),"nonfinite position refuses without allocation")
	print("BRUSH_OPACITY_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
