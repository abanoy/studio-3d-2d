extends SceneTree
const Codec=preload("res://web/web_has_container.gd")
const Storage=preload("res://src/storage.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1
 if not ok:failures+=1;print("FAIL "+label)
func _initialize() -> void:
 var folder:=OS.get_cmdline_user_args()[0]
 var plan: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder.path_join("plan.json")))
 var repacked: Array=[]
 for i in range(plan.inputs.size()):
  var source: String=plan.inputs[i];var sha:=FileAccess.get_sha256(source)
  var target:=folder.path_join("unpack-"+str(i));var result: Dictionary=Codec.unpack(source,target)
  check(not result.has("error"),"read desktop HAS "+str(i)+": "+str(result))
  if result.has("error"):continue
  var loaded: Dictionary=Storage.load_project(target)
  check(not loaded.has("error"),"ordinary project validation "+str(i)+": "+str(loaded.get("error","")))
  var packed:=folder.path_join("browser-"+str(i)+".has");var built: Dictionary=Codec.pack(target,packed)
  check(not built.has("error"),"browser package "+str(i))
  if built.has("error"):continue
  var again:=folder.path_join("again-"+str(i));var reopened: Dictionary=Codec.unpack(packed,again)
  check(not reopened.has("error"),"browser own reopen "+str(i))
  check(FileAccess.get_file_as_bytes(target.path_join("project.json"))==FileAccess.get_file_as_bytes(again.path_join("project.json")),"exact project bytes "+str(i))
  check(FileAccess.get_sha256(source)==sha,"original HAS unchanged "+str(i))
  repacked.append(packed)
 for i in range(plan.bad.size()):
  var result: Dictionary=Codec.unpack(plan.bad[i],folder.path_join("bad-"+str(i)))
  check(result.has("error"),"malformed package refuses: "+plan.bad[i])
 var file:=FileAccess.open(folder.path_join("result.json"),FileAccess.WRITE)
 file.store_string(JSON.stringify({"checks":checks,"failures":failures,"repacked":repacked}));file.close()
 print("WEB_HAS_CONTAINER "+str(checks)+"/"+str(failures));quit(0 if failures==0 else 1)
