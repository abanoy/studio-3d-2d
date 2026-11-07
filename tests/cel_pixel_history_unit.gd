extends SceneTree
const Owner=preload("res://src/cel_raster_owner.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
const Pixels=preload("res://src/cel_pixel_history.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var original:=Drawing.blank(32,16);original.fill(Color(.2,.7,.8,.5));var bytes:=original.get_data();var snapshot=Snapshot.capture(original).raster;var cache:=Cache.new(4096);var owner=Owner.from_snapshot(snapshot,cache).owner;var cel:={"id":"ink","start":0,"duration":1,"raster_owner":owner};var layers: Array=[{"cels":[cel]}]
	var pinned: Dictionary=owner.pin();var image: Image=pinned.image;var before:=image.get_region(Rect2i(0,0,16,16));Drawing.stroke(image,Vector2(4,4),Vector2(12,8),2,Color.RED,false);var edited:=image.get_data();var after:=image.get_region(Rect2i(0,0,16,16));var token: Array=owner.token();var weak: WeakRef=weakref(image)
	var command:={"type":"pixels","image":image,"before":{Vector2i.ZERO:before},"after":{Vector2i.ZERO:after},"bytes":4096};Pixels.promote(command,layers,"child")
	check(command.has("raster_owner") and not command.has("image") and is_same(command.raster_owner,owner),"owned pixel command retains logical owner and tiles without live Image pointer")
	check(not owner.cool().cooled and owner.is_pinned(),"external stroke/selection Image handles prevent authority release")
	pinned={};image=null;var cooled: Dictionary=owner.cool()
	check(cooled.get("cooled",false) and not owner.is_pinned() and owner.token()==token,"unborrowed edited pixels cool losslessly without changing logical revision")
	check(weak.get_ref()==null,"cooling releases the previous full Image object instead of hiding a strong pin")
	check(owner.retained_bytes()<owner.decoded_bytes()/2 and Drawing.image(cel).get_data()==edited,"cooled edited backing is compressed and reconstructs exact pixels")
	cache.clear();var decodes:=cache.decodes;var wrong:=Pixels.apply(command,"before",layers,"parent")
	check(wrong.has("error") and not owner.is_pinned() and cache.decodes==decodes,"wrong scene history refuses before materialization or mutation")
	check(Pixels.apply(command,"before",[],"child").has("error") and not owner.is_pinned(),"missing owner target refuses before pinning")
	var invalid:=command.duplicate(true);invalid.before[Vector2i(31,15)]=after
	check(Pixels.apply(invalid,"before",layers,"child").has("error") and not owner.is_pinned() and owner.token()==token,"late invalid tile refuses atomically before hydrating cold history target")
	var undone:=Pixels.apply(command,"before",layers,"child")
	check(not undone.has("error") and Drawing.image(cel).get_data()==bytes,"owner-addressed Undo rehydrates cooled source and restores exact original RGBA")
	var undo_token: Array=owner.token();check(undo_token[0]==token[0] and undo_token[1]>token[1],"Undo updates pixel revision while preserving logical owner identity")
	check(owner.cool().get("cooled",false),"Undo target can cool again with no live Image in history")
	check(not Pixels.apply(command,"after",layers,"child").has("error") and Drawing.image(cel).get_data()==edited,"Redo survives repeated cooling and restores exact authored pixels")
	owner.cool();var borrow: Image=owner.read().image;var revision: Array=owner.token();var adopted: Dictionary=owner.pin(revision,borrow)
	check(not adopted.has("error") and is_same(adopted.image,borrow) and int(borrow.get_meta("studio_pixels_revision",0))==revision[1],"selection can adopt a cooled nonzero-revision borrowed image")
	var legacy:={"type":"pixels","image":borrow,"before":command.before,"after":command.after};borrow=null;adopted={}
	check(not owner.cool().cooled,"unpromoted legacy Image history conservatively blocks cooling")
	legacy={};check(owner.cool().get("cooled",false),"releasing legacy history permits safe cooling")
	var plain:=Drawing.blank(32,16);var old:={"type":"pixels","image":plain,"before":command.before,"after":command.after};Pixels.promote(old,[{"cels":[{"image":plain}]}],"")
	check(old.has("image") and not old.has("raster_owner") and not Pixels.apply(old,"after",[],"").has("error") and plain.get_region(Rect2i(0,0,16,16)).get_data()==after.get_data(),"legacy eager pixel history remains compatible and exact")
	var empty:=command.duplicate(true);empty.before={};check(Pixels.apply(empty,"before",layers,"child").has("error"),"empty tile history refuses without mutation")
	check(Pixels.apply(command,"unknown",layers,"child").has("error"),"invalid history direction refuses")
	var ambiguous:=command.duplicate();ambiguous.image=plain;check(Pixels.apply(ambiguous,"before",layers,"child").has("error"),"ambiguous owner/Image command refuses")
	print("CEL_PIXEL_HISTORY_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
