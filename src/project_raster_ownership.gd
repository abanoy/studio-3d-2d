extends RefCounted
# Prepare all eager incoming cels before publishing any representation changes.
const Owner=preload("res://src/cel_raster_owner.gd")
const Cache=preload("res://src/cel_raster_snapshot_cache.gd")
static func collect(scene: Dictionary,pending: Array,cache,depth: int=0) -> String:
 if depth>8 or not scene.get("layers") is Array:return "Invalid incoming drawing layers."
 for layer in scene.layers:
  if not layer is Dictionary or not layer.get("cels") is Array:return "Invalid incoming drawing layer."
  for cel in layer.cels:
   if not cel is Dictionary:return "Invalid incoming drawing."
   if cel.has("raster_owner"):
    var owner=cel.raster_owner
    if cel.has("image") or not owner is Owner or owner._cache!=cache or not owner.integrity_error().is_empty():return "Invalid incoming drawing ownership."
   else:
    if not cel.get("image") is Image:return "Missing incoming drawing pixels."
    var adopted:=Owner.from_image(cel.image,cache)
    if adopted.has("error"):return adopted.error
    pending.append({"cel":cel,"owner":adopted.owner})
 var graph=scene.get("sequence_graph",{})
 if not graph is Dictionary or not graph.get("assets",[]) is Array:return "Invalid incoming drawing graph."
 for asset in graph.get("assets",[]):
  if not asset is Dictionary or not asset.get("scene") is Dictionary:return "Invalid incoming drawing scene."
  var why:=collect(asset.scene,pending,cache,depth+1)
  if not why.is_empty():return why
 return ""
static func adopt(data: Dictionary) -> String:
 var cache=data.get("raster_cache")
 if cache==null:cache=Cache.new()
 if not cache is Cache:return "Invalid incoming drawing cache."
 var pending: Array=[];var why:=collect(data,pending,cache)
 if not why.is_empty():return why
 for row in pending:
  row.cel.raster_owner=row.owner;row.cel.erase("image")
 data.raster_cache=cache
 return ""
