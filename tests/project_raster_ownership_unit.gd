extends SceneTree
const Adoption=preload("res://src/project_raster_ownership.gd")
const Drawing=preload("res://src/drawing.gd")
const Budget=preload("res://src/cel_raster_budget.gd")
const Reader=preload("res://src/cel_raster_reader.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func scene(cel: Dictionary) -> Dictionary:return {"layers":[{"cels":[cel]}]}
func _initialize() -> void:
 var image:=Drawing.blank(32,16);image.fill(Color(.2,.4,.7,.5));var original:=image.get_data();var cel:={"id":"root","image":image};var child_image:=image.duplicate();var child:={"id":"child","image":child_image};var data:=scene(cel);data.sequence_graph={"assets":[{"scene":scene(child)}]}
 check(Adoption.adopt(data).is_empty(),"eager root and nested drawings adopt together")
 check(not cel.has("image") and not child.has("image") and is_same(Drawing.image(cel),image) and is_same(Drawing.image(child),child_image),"adoption preserves exact writable Image identities and pixels without compression")
 var budget:=Budget.new(0);budget.install(data.raster_cache)
 check(budget.sample().owners==2 and budget.sample().hot_bytes==4096,"all incoming eager root/child bytes join shared accounting")
 check(Adoption.adopt(data).is_empty() and budget.sample().owners==2,"repeated adoption preserves owners and does not register duplicates")
 var token:=Drawing.raster_token(cel);Drawing.edit_image(cel).image.fill(Color.RED);Drawing.touch(image)
 check(Drawing.image(child).get_data()==original and Drawing.raster_token(cel)!=token,"editing adopted root keeps child independent with valid revision")
 var good:={"id":"good","image":child_image.duplicate()};var broken:={"id":"bad","image":null};var invalid:=scene(good);invalid.sequence_graph={"assets":[{"scene":scene(broken)}]}
 check(not Adoption.adopt(invalid).is_empty() and good.has("image") and not good.has("raster_owner") and not invalid.has("raster_cache"),"late invalid child refuses without partially publishing eager ownership")
 var rejected:=scene({"image":image});rejected.raster_cache=false
 check(not Adoption.adopt(rejected).is_empty() and rejected.layers[0].cels[0].has("image"),"invalid cache refuses without altering incoming pixels")
 var other:=scene({"raster_owner":cel.raster_owner})
 check(not Adoption.adopt(other).is_empty(),"owner from another incoming cache cannot silently escape accounting")
 image=null;child_image=null
 check(budget.step().released and budget.sample().hot_bytes==2048,"unborrowed small-project drawing can cool through existing idle policy")
 check(Drawing.image(child).get_data()==original,"cooled legacy child materializes exact original RGBA")
 var empty:={"layers":[]};check(Adoption.adopt(empty).is_empty() and empty.has("raster_cache"),"empty project obtains an independent cache for later authored drawings")
 print("PROJECT_RASTER_OWNERSHIP_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
