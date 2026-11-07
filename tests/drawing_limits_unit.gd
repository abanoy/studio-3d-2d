extends SceneTree
const Limits=preload("res://src/drawing_limits.gd")
const Timing=preload("res://src/cel_timing.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func layers(total: int) -> Array:
 var result: Array=[]
 for index in range(4):result.append({"id":"layer"+str(index),"name":"Layer "+str(index),"visible":true,"cels":[]})
 for i in range(total):result[i%4].cels.append({"id":"cel"+str(i),"start":i/4,"duration":1,"path":"missing.png"})
 return result
func _initialize() -> void:
 var full:=layers(400);check(Limits.error(full).is_empty() and Limits.MAX_CELS==400,"four layers of100drawings fit the declared project count")
 check(not Limits.error(layers(401)).is_empty(),"401st drawing refuses at project boundary")
 var root:=layers(200);var graph:={"assets":[{"scene":{"layers":layers(200)}}]}
 check(Limits.error(root,graph).is_empty(),"parent and child share one400drawing allowance")
 graph.assets[0].scene.layers=layers(201);check(not Limits.error(root,graph).is_empty(),"nested total401refuses even when each scene is individually smaller")
 for invalid in [null,false,[],{"assets":false},{"assets":[{}]}]:check(not Limits.error([],invalid).is_empty(),"malformed nested drawing metadata refuses without type errors: "+str(invalid))
 var cels: Array=[]
 for i in range(400):cels.append({"id":str(i),"start":i,"duration":1})
 check(not Timing.proposal(cels,"0",0,401).has("error"),"timing edits preserve a valid400drawing layer")
 cels.append({"id":"extra","start":400,"duration":1});check(Timing.proposal(cels,"extra",400,401).has("error"),"timing proposals refuse an over-limit layer without overlap ambiguity")
 var video:={"width":1920,"height":1080,"fps_num":24,"fps_den":1,"duration_frames":101};var keys: Array=[preload("res://src/timeline.gd").key(0,Vector3.ZERO,Quaternion.IDENTITY,60)];var world:=preload("res://src/world_document.gd").empty();var data:={"schema_version":4,"video":video,"camera_keys":keys,"layers":full,"world":world,"editor":{"frame":0},"audio":{}}
 var eager:=Storage.decode_project(data,"/unused");check(eager.has("error") and "adaptive" in str(eager.error),"large explicit eager API refuses before decoding files above its memory allowance")
 var folder: String=OS.get_cmdline_user_args()[0];var first:=Storage.save_project(folder,video,keys,[],"",0,{},{},{},true,world);var hash:=FileAccess.get_sha256(folder.path_join("project.json"));var rejected:=Storage.save_project(folder,video,keys,layers(401),"",0,{},{},{},true,world)
 check(first.is_empty() and not rejected.is_empty() and FileAccess.get_sha256(folder.path_join("project.json"))==hash,"over-count save refuses before changing a valid previous manifest")
 print("DRAWING_LIMITS_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
