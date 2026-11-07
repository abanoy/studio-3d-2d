extends RefCounted
# Main-thread capture detaches metadata and Image resources without compressing
# live pixels. The worker adopts only these copies into a private raster cache.
const Owner=preload("res://src/cel_raster_owner.gd")
const Snapshot=preload("res://src/cel_raster_snapshot.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
const Limits=preload("res://src/drawing_limits.gd")
static func clone_cold(source: Snapshot) -> Snapshot:
 var result:=Snapshot.new()
 result._size=source._size;result._payload=source._payload.duplicate();result._compressed=source._compressed;result._pixel_sha=source._pixel_sha;result._payload_sha=source._payload_sha;result._seal=source._seal
 return result
static func detach_scene(scene: Dictionary,cold_copies: Dictionary) -> String:
 scene.erase("raster_cache")
 for layer in scene.get("layers",[]):
  for cel in layer.cels:
   if cel.has("raster_owner"):
    var owner=cel.raster_owner
    if cel.has("image") or not owner is Owner:return "Invalid recovery drawing ownership."
    if owner.is_pinned():cel.image=owner._hot.duplicate()
    elif owner._cold is Snapshot:
     var id: int=owner._cold.get_instance_id()
     if not cold_copies.has(id):cold_copies[id]=clone_cold(owner._cold)
     cel["frozen_raster"]=cold_copies[id]
    else:return "Missing recovery drawing pixels."
    cel.erase("raster_owner")
   elif cel.get("image") is Image:cel.image=cel.image.duplicate()
   else:return "Missing recovery drawing pixels."
 for asset in scene.get("sequence_graph",{}).get("assets",[]):
  var why:=detach_scene(asset.scene,cold_copies)
  if not why.is_empty():return why
 return ""
static func detached_value(value,depth:=0) -> bool:
 if depth>64:return false
 if value is Dictionary:
  for key in value:
   if key is Object or not detached_value(value[key],depth+1):return false
 elif value is Array:
  for item in value:
   if not detached_value(item,depth+1):return false
 elif value is Object:return value is Image or value is Snapshot
 return true
static func capture(project: Dictionary) -> Dictionary:
 var why:=Limits.error(project.get("layers"),project.get("sequence_graph",{}))
 if not why.is_empty():return {"error":why}
 var result:=project.duplicate(true);var cold:={}
 why=detach_scene(result,cold)
 if not why.is_empty():return {"error":why}
 if not detached_value(result):return {"error":"Recovery snapshot contains unsupported live resources."}
 return {"project":result}
static func adopt_scene(scene: Dictionary,cache: Cache) -> String:
 for layer in scene.get("layers",[]):
  for cel in layer.cels:
   var prepared: Dictionary=Owner.from_snapshot(cel.frozen_raster,cache) if cel.has("frozen_raster") else Owner.from_image(cel.get("image"),cache)
   if prepared.has("error"):return prepared.error
   cel.erase("frozen_raster");cel.erase("image");cel.raster_owner=prepared.owner
 for asset in scene.get("sequence_graph",{}).get("assets",[]):
  var why:=adopt_scene(asset.scene,cache)
  if not why.is_empty():return why
 return ""
static func adopt(project: Dictionary) -> Dictionary:
 var cache:=Cache.new();var why:=adopt_scene(project,cache)
 return {"error":why} if not why.is_empty() else {"project":project,"cache":cache}
