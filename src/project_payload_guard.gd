extends RefCounted
# One validation operation: only digest strings survive a decoded cel check.
const PNG=preload("res://src/cel_png_verifier.gd")
var png=PNG.new()
var assets: Dictionary={}
var files:=0
func path(folder: String,relative) -> String:
 if not relative is String or relative.is_empty() or relative.is_absolute_path() or relative.contains(":") or relative.contains("\\"):return ""
 var filesystem:=DirAccess.open(ProjectSettings.globalize_path("res://"));var current:=ProjectSettings.globalize_path(folder)
 if not filesystem:return ""
 for part in relative.split("/"):
  if part in ["",".",".."]:return ""
  current=current.path_join(part)
  if filesystem.is_link(current):return ""
 return current
func asset(folder: String,row,path_key: String="path",hash_key: String="sha256",limit: int=128*1024*1024) -> bool:
 if not row is Dictionary:return false
 if row.is_empty():return true
 var target:=path(folder,row.get(path_key));var wanted=row.get(hash_key)
 if target.is_empty() or not wanted is String or wanted.length()!=64:return false
 var key: String=target+"\n"+str(wanted)
 if assets.has(key):return true
 if not FileAccess.file_exists(target):return false
 var file:=FileAccess.open(target,FileAccess.READ)
 if not file:return false
 if file.get_length()>limit:file.close();return false
 file.close();files+=1
 if FileAccess.get_sha256(target)!=wanted:return false
 assets[key]=true;return true
func valid(folder: String,data: Dictionary,depth: int=0) -> bool:
 if depth>8:return false
 var video=data.get("video")
 if not video is Dictionary:return false
 for field in ["width","height"]:
  var number=video.get(field)
  if not (number is int or number is float) or not is_finite(float(number)) or number<1 or number>1920 or int(number)!=number:return false
 if video.width>1920 or video.height>1080:return false
 if data.get("schema_version",0) in [1,2,3] and (not data.get("scene") is Dictionary or data.scene.is_empty()):return false
 for key in ["scene","model","reference_sheet"]:
  if data.has(key) and not asset(folder,data[key]):return false
 var world=data.get("world",{})
 if not world is Dictionary or not world.get("objects",[]) is Array or not world.get("effects",[]) is Array:return false
 for row in world.get("objects",[]):
  if not asset(folder,row):return false
 for row in world.get("effects",[]):
  if not asset(folder,row) or not asset(folder,row,"texture_path","texture_sha256"):return false
 var audio=data.get("audio",{})
 if not audio is Dictionary:return false
 if audio.has("path") and not asset(folder,audio):return false
 if not audio.get("clips",[]) is Array:return false
 for row in audio.get("clips",[]):
  if not asset(folder,row):return false
 var layers=data.get("layers",[])
 if not layers is Array:return false
 for layer in layers:
  if not layer is Dictionary or not layer.get("cels") is Array:return false
  for cel in layer.cels:
   if not cel is Dictionary:return false
   var target:=path(folder,cel.get("path"));var expected=cel.get("pixel_sha256")
   if target.is_empty() or expected!=null and (not expected is String or expected.length()!=64):return false
   if cel.has("pixel_sha256") and expected==null:return false
   if not png.valid(target,int(video.width),int(video.height),expected):return false
 var graph=data.get("sequence_graph",{})
 if not graph is Dictionary or not graph.get("assets",[]) is Array:return false
 for child in graph.get("assets",[]):
  if not child is Dictionary or not child.get("scene") is Dictionary or not valid(folder,child.scene,depth+1):return false
 return true
