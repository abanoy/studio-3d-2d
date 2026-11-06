extends SceneTree
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Drawing=preload("res://src/drawing.gd")
const Overlay=preload("res://src/drawing_overlay_cache.gd")
const Sampler=preload("res://src/color_sampler.gd")
const Onion=preload("res://src/onion_editor.gd")
const Runtime=preload("res://src/sequence_runtime.gd")
const World=preload("res://src/world_document.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func temporary_source(overlay,cache,image: Image) -> WeakRef:
	var snapshot=Snapshot.capture(image).raster;var owner=Owner.from_snapshot(snapshot,cache).owner
	overlay.sample([{"visible":true,"cels":[{"start":0,"duration":2,"raster_owner":owner}]}],0,4,3,0)
	return weakref(owner)
func _initialize() -> void:
	var image:=Drawing.blank(4,3);image.fill(Color(.2,.5,.8,.5));var raw:=image.get_data();var snapshot=Snapshot.capture(image).raster;var cache:=Cache.new(48);var owner=Owner.from_snapshot(snapshot,cache).owner
	var cel:={"id":"cold","start":0,"duration":2,"raster_owner":owner};var layer:={"id":"ink","name":"Ink","visible":true,"opacity":.5,"cels":[cel]};var overlay:=Overlay.new()
	var result:=overlay.sample([layer],0,4,3,0)
	check(not result.has("error") and result.changed and result.image.get_data()==Drawing.composite([layer],0,4,3).get_data(),"preview cache builds exact cold-owner composite")
	var before:=cache.decodes;cache.clear();var held:=overlay.sample([layer],1,4,3,0)
	check(not held.changed and is_same(result.image,held.image) and cache.decodes==before,"held preview cache hit keeps stable owner identity without rehydrating evicted decoded pixels")
	check(not owner.is_pinned() and Drawing.raster_size(cel)==Vector2i(4,3),"readonly preview and dimensions never pin editable pixels")
	var sample:=Sampler.drawing_pixel([layer],0,Vector2i(1,1));var expected:=Drawing.composite([layer],0,4,3).get_pixel(1,1)
	check(sample.color==expected and not owner.is_pinned(),"visible sampler matches composited cold alpha without pinning")
	check(Sampler.drawing_pixel([layer],0,Vector2i(1,1),null,0).color==image.get_pixel(1,1),"raw active-layer sampler preserves original cold color and alpha")
	var scene:={"clips":[],"scene":{"world":World.empty(),"layers":[layer]}};var runtime:=Runtime.new();before=cache.decodes
	check(runtime.picture_stamp(scene,0,true,true)==runtime.picture_stamp(scene,1,true,true) and cache.decodes==before,"held child-picture signature remains stable without decoding")
	var pin:=Drawing.edit_image(cel);Drawing.stroke(pin.image,Vector2.ZERO,Vector2(3,2),1,Color.RED,false)
	var changed:=overlay.sample([layer],1,4,3,0)
	check(changed.changed and changed.image.get_data()!=result.image.get_data() and changed.image.get_data()==Drawing.composite([layer],1,4,3).get_data(),"hot brush revision invalidates preview after cold pin")
	check(snapshot.materialize().image.get_data()==raw,"readonly and hot rendering leave original cold source unchanged")
	var corrupted=Snapshot.capture(image).raster;var bad_owner=Owner.from_snapshot(corrupted,cache).owner;var bad_cel:={"id":"bad","start":0,"duration":2,"raster_owner":bad_owner};var bad_layer:={"visible":true,"cels":[bad_cel]};overlay.sample([bad_layer],0,4,3,2);corrupted._payload[0]=corrupted._payload[0]^1
	check(overlay.sample([bad_layer],0,4,3,2).has("error"),"even a warm derived preview refuses corrupted cold payload")
	var checked:=Drawing.composite_result([bad_layer],1,4,3)
	check(checked.has("error") and checked.error.contains("bad") and checked.error.contains("frame 1"),"composite reports the failed cel/frame instead of returning blank art")
	check(Sampler.drawing_pixel([bad_layer],0,Vector2i.ONE).has("error"),"sampling corrupt cold pixels returns an error rather than a color")
	bad_layer.visible=false;check(not Drawing.composite_result([bad_layer],0,4,3).has("error"),"hidden cold source is not unnecessarily read for visible composition")
	before=cache.decodes;var neighbors:=Onion.neighbors({"cels":[cel,{"id":"later","start":3,"duration":1,"raster_owner":bad_owner}]},2)
	check(neighbors.previous.id=="cold" and neighbors.next.id=="later" and cache.decodes==before,"onion neighbor selection stays metadata-only")
	var weak: WeakRef=temporary_source(overlay,cache,image)
	check(weak.get_ref()==null and overlay.sources[0].get_ref()==null,"derived preview cache never retains discarded cold cel owners")
	check(Drawing.read_image({"image":"bad"}).has("error") and not Drawing.raster_error({}).is_empty(),"checked reads retain explicit errors for invalid ownership")
	runtime.free();print("CEL_RASTER_READ_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
