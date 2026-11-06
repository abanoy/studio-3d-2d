extends SceneTree
const Store=preload("res://src/lesson_store.gd")
const Recovery=preload("res://src/recovery.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var ui:={"basis":[1,0,0,0,1,0,0,0,1],"origin":[0,2,5],"fov":55,"near":.05,"far":1000,"mode":0,"advanced":false,"selected":"figure","bone":"@root","layer":1,"zoom":1.25,"pan":[12,17],"observed":{"preview_seen":true,"export_done":false}}
	var value:={"format":"studio_lesson_recovery_1","course":"basic-pose","session":"123_456","step":1,"done":false,"ui":ui,"baseline":ui.duplicate(true),"fov_baseline":55,"collapsed":false}
	check(Store.valid_recovery(value),"valid course, local address and bounded complete teacher state accepted")
	check(Store.valid_recovery(JSON.parse_string(JSON.stringify(value,"",true,true))),"canonical JSON round-trip keeps recovery state valid")
	var all_courses:=true
	for course in Store.COURSES:
		for at in range(int(Store.COURSES[course])+1):
			var candidate:=value.duplicate(true);candidate.course=course;candidate.step=at;candidate.done=at==int(Store.COURSES[course]);all_courses=all_courses and Store.valid_recovery(candidate)
	check(all_courses,"all current versioned course steps and completion boundaries are representable")
	for pair in [["format","future"],["course","unknown"],["course",false],["session","../escape"],["session","C:/escape"],["session",false],["session",""],["step",-1],["step",1.5],["step",4],["done",true],["done",0],["collapsed",0],["fov_baseline",NAN],["fov_baseline",INF],["fov_baseline",14],["fov_baseline",121],["fov_baseline","55"],["ui",{}],["baseline",{}]]:
		var candidate:=value.duplicate(true);candidate[pair[0]]=pair[1];check(not Store.valid_recovery(candidate),"invalid "+str(pair[0])+" field refused: "+str(pair[1]))
	for field in value:
		var candidate:=value.duplicate(true);candidate.erase(field);check(not Store.valid_recovery(candidate),"missing "+field+" refused")
	for pair in [["basis",[0,0,0,0,0,0,0,0,0]],["origin",[0,0,INF]],["observed",{"export_done":"yes"}],["observed",{"arbitrary":true}],["zoom",0],["layer",8],["mode",4],["selected",false]]:
		var candidate:=value.duplicate(true);candidate.ui[pair[0]]=pair[1];check(not Store.valid_recovery(candidate),"invalid nested UI "+str(pair[0])+" refused")
	var oversized:=value.duplicate(true);oversized.ui["padding"]="x".repeat(16384)
	check(not Store.valid_recovery(oversized),"oversized metadata refused before UI adoption")
	var extra:=value.duplicate(true);extra["unexpected"]={}
	check(not Store.valid_recovery(extra) and not Store.valid_recovery(null) and not Store.valid_recovery([]),"extra fields and non-object contexts refused")
	var folder: String=OS.get_cmdline_user_args()[0]
	check(not Recovery.checkpoint(folder.path_join("must-not-exist"),"123",{},[],[],"",0,{},"",0,{},{},[],{},{},{},oversized).is_empty() and not DirAccess.dir_exists_absolute(folder.path_join("must-not-exist")),"oversized recovery refuses before any project or journal writes")
	print("LESSON_RECOVERY_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
