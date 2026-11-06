extends SceneTree
const Owner=preload("res://src/cel_raster_owner.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var image:=Drawing.blank(32,16);image.fill(Color(.3,.5,.8,.5));image.set_pixel(0,0,Color(.7,.2,.3,0));var original:=image.get_data();var snapshot=Snapshot.capture(image).raster;var cache:=Cache.new(2048)
	var owner=Owner.from_snapshot(snapshot,cache).owner;var peer=Owner.from_snapshot(snapshot,cache).owner
	var cel:={"id":"a","start":0,"duration":2,"raster_owner":owner};var sibling:={"id":"b","start":2,"duration":2,"raster_owner":peer};var token:=Drawing.raster_token(cel)
	check(not owner.is_pinned() and Drawing.raster_bytes(cel,true)==2048 and Drawing.raster_bytes(cel)<2048 and cache.decodes==0,"owner identity and byte accounting never hydrate cold pixels")
	var a:=Drawing.image(cel);var b:=Drawing.image(sibling)
	check(a.get_data()==original and b.get_data()==original and not is_same(a,b) and not owner.is_pinned(),"cold owners borrow distinct exact images without pinning")
	a.fill(Color.RED);check(Drawing.image(cel).get_data()==original and Drawing.image(sibling).get_data()==original,"unadopted read edits cannot alter either authoritative cel")
	check(Drawing.edit_image(cel,token,a).has("error") and not owner.is_pinned(),"changed borrowed pixels refuse adoption atomically")
	a=Drawing.image(cel);var pinned:=Drawing.edit_image(cel,token,a)
	check(not pinned.has("error") and is_same(pinned.image,a) and is_same(Drawing.image(cel),a) and owner.is_pinned(),"explicit pin adopts the verified selection image and preserves exact writable identity")
	check(Drawing.raster_token(cel)==token and Drawing.raster_bytes(cel)==2048,"pinning identical content alone leaves the stable revision unchanged")
	var before:=a.get_region(Rect2i(0,0,16,16));Drawing.stroke(a,Vector2(4,4),Vector2(12,8),2,Color.RED,false);var after:=a.get_region(Rect2i(0,0,16,16));var edited:=a.get_data()
	check(edited!=original and Drawing.raster_token(cel)!=token and Drawing.image(sibling).get_data()==original,"ordinary brush edits update owner token and preserve cold peer")
	check(Drawing.edit_image(cel,token,a).has("error"),"stale pre-stroke token refuses a later edit")
	var history:={"image":a,"before":before,"after":after};cache.clear();a=null;pinned={}
	history.image.blit_rect(history.before,Rect2i(0,0,16,16),Vector2i.ZERO);Drawing.touch(history.image)
	check(Drawing.image(cel).get_data()==original and is_same(Drawing.image(cel),history.image),"pixel Undo image remains authoritative after cache eviction and caller release")
	history.image.blit_rect(history.after,Rect2i(0,0,16,16),Vector2i.ZERO);Drawing.touch(history.image)
	check(Drawing.image(cel).get_data()==edited and Drawing.image(sibling).get_data()==original,"pixel Redo retains authoritative identity and independent peers")
	var checkpoint: Dictionary=owner.snapshot();history.image.fill(Color.BLUE);Drawing.touch(history.image)
	check(checkpoint.raster.materialize().image.get_data()==edited and Drawing.image(cel).get_data()!=edited,"worker/save snapshot freezes authored pixels independently of subsequent edits")
	var ordinary:={"id":"old","start":0,"duration":4,"image":image};var eager_token:=Drawing.raster_token(ordinary)
	check(is_same(Drawing.image(ordinary),image) and is_same(Drawing.edit_image(ordinary).image,image) and Drawing.raster_bytes(ordinary)==2048,"legacy eager cel keeps exact Image ownership and accounting")
	check(Drawing.edit_image(ordinary,eager_token,image.duplicate()).has("error"),"legacy stale selection identity still refuses")
	var cold_layer:={"id":"ink","name":"Ink","visible":true,"opacity":.5,"cels":[sibling]};var eager_layer:=cold_layer.duplicate(true);eager_layer.cels=[{"id":"same","start":2,"duration":2,"image":image}]
	check(Drawing.composite([cold_layer],2,32,16).get_data()==Drawing.composite([eager_layer],2,32,16).get_data(),"actual Drawing composite matches eager pixels with cold owner, hold and layer opacity")
	var replacement_layer:=cold_layer.duplicate(true);var replacement:=Drawing.blank(32,16);replacement.fill(Color.MAGENTA);Drawing.insert(replacement_layer,2,4,replacement)
	check(is_same(Drawing.image(replacement_layer.cels[0]),replacement) and not replacement_layer.cels[0].has("raster_owner") and Drawing.image(sibling).get_data()==original,"existing-start insert replaces ownership without changing a peer or stale cold shadow")
	var direct=Owner.from_image(image).owner;check(is_same(direct.read().image,image) and direct.is_pinned(),"wrapping an existing editable Image preserves pixel-history identity")
	check(Owner.from_snapshot(null,cache).has("error") and Owner.from_snapshot(snapshot,null).has("error") and Owner.from_image(null).has("error") and Owner.new().read().has("error"),"invalid owner construction/read refuses")
	var borrow: Image=peer.read().image;check(peer.pin([],borrow).has("error") and not peer.is_pinned(),"borrowed-image adoption requires an explicit current token")
	var victim=Snapshot.capture(image).raster;var broken=Owner.from_snapshot(victim,cache).owner;victim._payload[0]=victim._payload[0]^1
	var bad_layer:={"id":"bad","name":"Bad","visible":true,"cels":[{"id":"bad","start":0,"duration":1,"raster_owner":broken}]}
	check(broken.pin().has("error") and Drawing.composite([bad_layer],0,32,16)==null and not broken.is_pinned(),"corrupt cold source refuses editing/composition without blank substitution")
	check(Drawing.image({})==null and Drawing.edit_image({}).has("error") and Drawing.raster_token({}).is_empty(),"missing pixel ownership has explicit failure semantics")
	var ambiguous:={"image":image,"raster_owner":peer}
	check(Drawing.image(ambiguous)==null and Drawing.edit_image(ambiguous).has("error") and Drawing.raster_token(ambiguous).is_empty() and Drawing.raster_bytes(ambiguous)==0,"two simultaneous authoritative pixel representations refuse instead of shadowing artwork")
	check(Drawing.image({"image":"invalid"})==null and Drawing.edit_image({"raster_owner":false}).has("error"),"mistyped eager pixels or cold owner refuse without native type exceptions")
	print("CEL_RASTER_OWNER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
