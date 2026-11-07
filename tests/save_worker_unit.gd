extends SceneTree
const Worker=preload("res://src/save_worker.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 var good:={"ok":true,"committed":true,"directory_synced":true};check(Worker.response(0,JSON.stringify(good))==good,"successful worker status preserves exact outcome flags")
 for text in ["","{","[]","null"]:
  var failed:=Worker.response(0,text);check(failed.ok==false and not failed.error.is_empty() and failed.outcome_unknown,"missing/malformed worker status never promises old state preserved")
 for row in [{},{"ok":1},{"ok":"true"},{"ok":false,"error":""},{"ok":false,"error":1}]:
  var failed:=Worker.response(0,JSON.stringify(row));check(failed.ok==false and failed.error is String and not failed.error.is_empty(),"worker requires real success boolean or meaningful failure")
 var contrary:=Worker.response(1,JSON.stringify(good));check(contrary.ok==false and not contrary.error.is_empty(),"nonzero worker exit cannot be accepted from contradictory success JSON")
 var committed:=Worker.response(1,JSON.stringify({"ok":false,"committed":true,"error":"File was written, but sync failed"}));check(not committed.ok and committed.committed and committed.error=="File was written, but sync failed","post-promotion failure keeps committed outcome and precise error")
 print("SAVE_WORKER_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
