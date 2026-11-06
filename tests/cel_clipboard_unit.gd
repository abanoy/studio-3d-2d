extends SceneTree
const Clipboard=preload("res://src/cel_clipboard.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:
	var cels: Array=[{"id":"first","start":0,"duration":8},{"id":"later","start":24,"duration":8}]
	var before:=cels.duplicate(true)
	for at in [8,12,16,32,40]:check(not Clipboard.placement(cels,"new",at,8,48).has("error"),"free end-exclusive range accepted at%d" % at)
	for at in [0,1,7,17,23,24,31,41]:check(Clipboard.placement(cels,"new",at,8,48).has("error"),"overlap or scene overflow refused at%d" % at)
	for values in [[-1,8,48],[1.5,8,48],[true,8,48],[8,0,48],[8,1.5,48],[8,INF,48],[8,8,0],[8,8,7201]]:check(Clipboard.placement(cels,"new",values[0],values[1],values[2]).has("error"),"invalid numeric placement refused: "+str(values))
	check(Clipboard.placement(cels,"first",8,8,48).has("error"),"duplicate pasted identity refused")
	check(cels==before,"all proposals leave original exposure data unchanged")
	check(not Clipboard.placement([],"new",0,48,48).has("error"),"whole-scene paste into empty layer accepted")
	check(not Clipboard.placement([],"new",3000,24,7200).has("error"),"long-parent placement retains original length")
	check(Clipboard.placement([{"id":"bad","start":"invalid","duration":8}],"new",12,8,48).has("error"),"malformed existing range safely refused")
	var full: Array=[]
	for i in range(32):full.append({"id":str(i),"start":i,"duration":1})
	check(Clipboard.placement(full,"new",32,1,48).has("error"),"32cel layer budget remains bounded")
	print("CEL_CLIPBOARD_UNIT "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
