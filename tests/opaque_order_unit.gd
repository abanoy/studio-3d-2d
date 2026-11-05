extends SceneTree
const SceneIO=preload("res://src/scene3d.gd")
var failures:=0
var checks:=0
func check(ok: bool,label: String) -> void:
 checks+=1
 if not ok:failures+=1
 print(("PASS " if ok else "FAIL ")+label)
func _initialize() -> void:
 var a:=StandardMaterial3D.new();var b:=StandardMaterial3D.new();var glass:=StandardMaterial3D.new();glass.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
 check(SceneIO.stable_opaque_order([a,glass,a,b]) and a.render_priority==-128 and b.render_priority==-127 and glass.render_priority==0,"source order, shared identity and transparency preserved")
 var custom:=StandardMaterial3D.new();custom.render_priority=5;var neutral:=StandardMaterial3D.new()
 check(not SceneIO.stable_opaque_order([neutral,custom]) and neutral.render_priority==0 and custom.render_priority==5,"explicit priority refuses without partial changes")
 custom.render_priority=0;custom.next_pass=StandardMaterial3D.new()
 check(not SceneIO.stable_opaque_order([neutral,custom]) and neutral.render_priority==0,"multipass materials retain contract")
 var rows: Array=[]
 for i in range(256):rows.append(StandardMaterial3D.new())
 check(SceneIO.stable_opaque_order(rows) and rows[0].render_priority==-128 and rows[255].render_priority==127,"all256 distinct priorities supported")
 rows=[]
 for i in range(257):rows.append(StandardMaterial3D.new())
 check(not SceneIO.stable_opaque_order(rows) and rows.all(func(m):return m.render_priority==0),"overflow leaves whole set unchanged")
 check(SceneIO.stable_opaque_order([]),"empty scenes supported")
 print("OPAQUE_ORDER "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
