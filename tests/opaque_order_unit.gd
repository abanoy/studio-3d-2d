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
 var cutout:=StandardMaterial3D.new();cutout.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR;cutout.alpha_scissor_threshold=0.3
 var solid:=StandardMaterial3D.new();var hash_alpha:=StandardMaterial3D.new();hash_alpha.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
 var prepass:=StandardMaterial3D.new();prepass.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
 check(SceneIO.stable_opaque_order([cutout,glass,solid,cutout,hash_alpha,prepass]) and cutout.render_priority==-128 and solid.render_priority==-127,"cutout and solid depth ties share stable source order with deduplicated references")
 check(cutout.transparency==BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR and is_equal_approx(cutout.alpha_scissor_threshold,0.3) and glass.render_priority==0 and hash_alpha.render_priority==0 and prepass.render_priority==0,"cutout coverage and other transparency sorting remain unchanged")
 var explicit_cutout:=StandardMaterial3D.new();explicit_cutout.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR;explicit_cutout.render_priority=9
 check(not SceneIO.stable_opaque_order([neutral,explicit_cutout]) and neutral.render_priority==0 and explicit_cutout.render_priority==9,"explicit cutout priority preserves complete material-set contract")
 print("OPAQUE_ORDER "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
