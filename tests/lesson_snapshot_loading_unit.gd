extends SceneTree
const Store=preload("res://src/lesson_store.gd")
class RejectProject:
 extends RefCounted
 var calls:=0
 var open_project_error:="controlled complete-project refusal"
 func open_project(_folder: String) -> bool:
  calls+=1;return false
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
 checks+=1;print(("PASS " if ok else "FAIL ")+label)
 if not ok:failures+=1
func _initialize() -> void:
 var root: String=OS.get_cmdline_user_args()[0];var store:=Store.new();store.root=root;var folder:=store.folder("basic-pose","123_456").path_join("resume");DirAccess.make_dir_recursive_absolute(folder);var path:=folder.path_join("project.json");var app:=RejectProject.new()
 var ui:={"basis":[1,0,0,0,1,0,0,0,1],"origin":[0,2,5],"fov":55,"near":.05,"far":1000,"mode":0,"advanced":false,"selected":"","bone":"@root","layer":1,"zoom":1.,"pan":[0,0]}
 check(Store.valid_ui(ui) and store.write_json(path,{"editor":{"lesson_ui":ui}}),"owned fixture has bounded valid lesson UI metadata")
 var original:=FileAccess.get_sha256(path)
 check(not store.load_snapshot(app,"basic-pose","123_456","resume") and app.calls==1 and store.error==app.open_project_error,"lesson loader delegates complete project validation to exactly one normal Open")
 check(FileAccess.get_sha256(path)==original,"UI inspection and refused complete-project load never rewrite source metadata")
 store.write_json(path,{"editor":[]})
 check(not store.load_snapshot(app,"basic-pose","123_456","resume") and app.calls==1,"malformed editor container refuses before invoking normal Open")
 store.write_json(path,{"editor":{"lesson_ui":{"advanced":false}}})
 check(not store.load_snapshot(app,"basic-pose","123_456","resume") and app.calls==1,"incomplete lesson UI refuses without rendering or loading assets")
 check(not store.load_snapshot(app,"basic-pose","123_456","../resume") and app.calls==1,"checkpoint ownership/name checks remain in front of all metadata reads")
 print("LESSON_SNAPSHOT_LOADING_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"scope":"bounded UI metadata and single normal-Open delegation; actual project/asset recovery verified separately"}));quit(0 if failures==0 else 1)
