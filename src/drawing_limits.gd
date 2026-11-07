extends RefCounted
# Record count is separate from admitted retained bytes.
const MAX_CELS=400
static func count(layers) -> int:
 if not layers is Array or layers.size()>4:return MAX_CELS+1
 var total:=0
 for layer in layers:
  if not layer is Dictionary or not layer.get("cels") is Array:return MAX_CELS+1
  total+=layer.cels.size()
 return total
static func error(layers,graph={}) -> String:
 if not graph is Dictionary:return "Invalid nested drawing tracks."
 var total:=count(layers);var assets=graph.get("assets",[])
 if not assets is Array or assets.size()>4:return "Invalid nested drawing tracks."
 for asset in assets:
  if not asset is Dictionary or not asset.get("scene") is Dictionary:return "Invalid nested drawing scene."
  total+=count(asset.scene.get("layers"))
 return "" if total<=MAX_CELS else "This project exceeds the supported limit of %d drawings across its scenes." % MAX_CELS
