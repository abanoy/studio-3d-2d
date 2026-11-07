extends SceneTree
const Frozen=preload("res://src/recovery_snapshot.gd")
const Drawing=preload("res://src/drawing.gd")
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 var hot:=Drawing.blank(32,16);hot.fill(Color(.3,.6,.1,.5));var cache:=Cache.new();var eager=Owner.from_image(hot,cache).owner;var cold=Snapshot.capture(hot).raster;var sleeping=Owner.from_snapshot(cold,cache).owner
 var layers: Array=[{"id":"ink","cels":[{"id":"hot","raster_owner":eager},{"id":"cold","raster_owner":sleeping}]}];var project:={"video":{"width":32},"layers":layers,"camera_keys":[{"frame":0}],"raster_cache":cache,"sequence_graph":{"assets":[{"scene":{"layers":[{"cels":[{"id":"nested","raster_owner":sleeping}]}]}}]}}
 var before:=hot.get_data();var frozen:=Frozen.capture(project)
 check(not frozen.has("error") and not frozen.project.has("raster_cache") and cache.decodes==0,"snapshot detaches all drawing resources without cold decoding or retained live cache")
 var cels: Array=frozen.project.layers[0].cels
 check(not is_same(cels[0].image,hot) and not cels[0].has("raster_owner") and not cels[1].has("raster_owner"),"frozen hot Image is a distinct resource and no live owner crosses the boundary")
 check(not is_same(cels[1].frozen_raster,cold) and is_same(cels[1].frozen_raster,frozen.project.sequence_graph.assets[0].scene.layers[0].cels[0].frozen_raster),"cold descriptor is independent while root and child immutable sharing is retained")
 hot.set_pixel(2,2,Color.RED);project.video.width=99;project.camera_keys[0].frame=7;layers[0].cels.clear();cold._payload[0]=cold._payload[0]^1
 check(cels[0].image.get_data()==before and frozen.project.video.width==32 and frozen.project.camera_keys[0].frame==0 and cels.size()==2,"later live pixel, metadata and structure edits cannot change captured state")
 check(cels[1].frozen_raster.verify().is_empty(),"later mutation of original cold payload cannot corrupt independently copied bytes")
 var adopted:=Frozen.adopt(frozen.project)
 check(not adopted.has("error") and not is_same(adopted.cache,cache) and adopted.cache.live_owners().size()==3,"worker adoption creates its own admitted cache and independent logical owners")
 check(Drawing.image(cels[0]).get_data()==before and Drawing.image(cels[1]).get_data()==before,"worker hot and cold pixels retain exact pre-edit RGBA")
 check(cache.decodes==0 and sleeping._cache==cache,"worker reads never mutate live document cache")
 var bad:={"layers":[],"node":Node.new()};var refused:=Frozen.capture(bad);check(refused.has("error"),"unexpected live Node refuses snapshot before work starts");bad.node.free()
 print("RECOVERY_SNAPSHOT_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
