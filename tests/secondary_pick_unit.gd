extends SceneTree
const Helper=preload("res://src/secondary_helper_editor.gd")
class TestActor extends RefCounted:
	var root:=Node3D.new()
	var bones:={"center":true,"a":true,"b":true}
class TestRenderer extends RefCounted:
	var world_runtime
	var model: RefCounted
class TestApp extends RefCounted:
	var advanced_mode:=false
	var renderer: RefCounted
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func row(node: int,lower: Vector3,upper: Vector3,rigged:=false) -> Dictionary:
	return {"anchor_node":node,"bounds_in_anchor":[[lower.x,lower.y,lower.z],[upper.x,upper.y,upper.z]],"already_rigged":rigged}
func _initialize() -> void:
	var rows: Array=[row(0,Vector3(-1,-1,-1),Vector3(1,1,1)),row(1,Vector3(-.2,-.2,2),Vector3(.2,.2,3))]
	var transforms:={0:Transform3D.IDENTITY,1:Transform3D.IDENTITY}
	check(Helper.ray_region(rows,transforms,Vector3(0,0,5),Vector3.FORWARD)==1,"nearest front intersection wins over a larger rear area")
	check(Helper.ray_region(rows,transforms,Vector3(4,0,5),Vector3.FORWARD)==-1,"ray outside actual part bounds finds no area")
	check(Helper.ray_region(rows,transforms,Vector3(0,0,-5),Vector3.FORWARD)==-1,"areas behind the camera are not selected")
	check(Helper.ray_region(rows,transforms,Vector3(0,0,5),Vector3.FORWARD,1)==-1,"part beyond the camera range is not selected")
	var rotated:=Transform3D(Basis(Quaternion(Vector3.UP,PI/4)).scaled(Vector3(2,1,.5)),Vector3(3,0,0))
	check(Helper.ray_region([row(7,Vector3(-.2,-.2,-.2),Vector3(.2,.2,.2))],{7:rotated},Vector3(3,0,5),Vector3.FORWARD)==0,"current rotated/scaled bone transforms position the bounds")
	check(Helper.ray_region([row(7,Vector3(-.2,-.2,-.2),Vector3(.2,.2,.2))],{7:rotated},Vector3(0,0,5),Vector3.FORWARD)==-1,"transformed part does not remain selectable at its old origin")
	check(Helper.ray_region([row(0,Vector3(-1,-1,0),Vector3(1,1,0))],transforms,Vector3(0,0,5),Vector3.FORWARD)==0,"thin planar hair surfaces remain pickable")
	rows[1].already_rigged=true
	check(Helper.ray_region(rows,transforms,Vector3(0,0,5),Vector3.FORWARD)==1,"front configured part is not replaced by an editable part behind it")
	check(Helper.ray_region(rows,{0:Transform3D.IDENTITY},Vector3(0,0,5),Vector3.FORWARD)==0,"missing runtime bindings are excluded")
	check(Helper.ray_region(rows,transforms,Vector3(NAN,0,5),Vector3.FORWARD)==-1,"nonfinite camera ray is refused")
	check(Helper.ray_region(rows,transforms,Vector3(0,0,5),Vector3.ZERO)==-1,"zero ray direction is refused")
	check(Helper.ray_region([row(0,Vector3.ONE,Vector3.ZERO)],transforms,Vector3(0,0,5),Vector3.FORWARD)==-1,"inverted malformed bounds are refused")
	check(Helper.ray_region(rows,{0:Transform3D(Basis(Vector3.ZERO,Vector3.ZERO,Vector3.ZERO),Vector3.ZERO)},Vector3(0,0,5),Vector3.FORWARD)==-1,"singular joint transform is skipped without inversion")
	var current:=TestActor.new();current.root.set_meta("has_source_bones",{0:"center",1:"a",2:"b"})
	var renderer:=TestRenderer.new();renderer.model=current;var app:=TestApp.new();app.renderer=renderer
	var editor:=Helper.new();editor.app=app;editor.patch_toggle=CheckButton.new()
	var proposal:={"can_apply":false,"anchors":[{"node":0,"available":false},{"node":1,"available":false}],"region":{"existing_chain":{"center_node":0,"joint_nodes":[1,2]}}}
	check(editor.smart_existing(proposal),"Simple proposes a bound existing chain when every ordinary anchor is unavailable")
	proposal.anchors[1].available=true
	check(not editor.smart_existing(proposal),"an available nondefault anchor keeps the ordinary correction path")
	proposal.anchors[1].available=false;editor.mode_choice="weighted"
	check(not editor.smart_existing(proposal),"manual uncheck prevents an automatic selection loop")
	editor.mode_choice="auto";app.advanced_mode=true
	check(not editor.smart_existing(proposal),"Advanced keeps the explicit existing-joint opt-in")
	app.advanced_mode=false;editor.patch_toggle.button_pressed=true
	check(not editor.smart_existing(proposal),"smaller-patch review never switches itself into whole shared-chain mode")
	editor.patch_toggle.button_pressed=false;current.bones.erase("b")
	check(not editor.smart_existing(proposal),"an incomplete runtime chain is not automatically offered")
	current.bones.b=true;proposal.can_apply=true
	check(not editor.smart_existing(proposal),"a usable weighted proposal is kept without an unnecessary mode change")
	editor.patch_toggle.free();editor.free();current.root.free()
	var result:={"checks":checks,"failures":failures};print("SECONDARY_PICK_UNIT "+JSON.stringify(result));quit(0 if failures==0 else 1)
