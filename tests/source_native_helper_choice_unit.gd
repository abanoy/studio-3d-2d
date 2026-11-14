extends SceneTree
const Editor=preload("res://src/secondary_helper_editor.gd")
var checks:=0
var failures:=0
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func run() -> void:
	var allowed:={8:true,9:true}
	var parents:={7:-1,8:7,9:8,10:7}
	var valid:={"existing_chain":{"center_node":7,"joint_nodes":[8,9]}}
	var before:=var_to_bytes([valid,allowed,parents])
	check(Editor.native_existing_chain(valid,allowed,parents),"verified imported owners follow their actual static attachment")
	check(Editor.native_existing_chain({"existing_chain":{"center_node":7.0,"joint_nodes":[8.0,9.0]}},allowed,parents),"integral JSON node selectors retain exact identities")
	check(not Editor.native_existing_chain({},allowed,parents),"missing proposal stays ordinary manual setup")
	check(not Editor.native_existing_chain({"existing_chain":[]},allowed,parents),"wrong proposal type refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":true,"joint_nodes":[8,9]}},allowed,parents),"bool attachment cannot masquerade as an index")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":6,"joint_nodes":[8,9]}},allowed,parents),"unmapped attachment refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":8,"joint_nodes":[9]}},allowed,parents),"a procedural owner is not silently pinned as an attachment")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":[]}},allowed,parents),"empty imported owner set refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":[8,8]}},allowed,parents),"duplicate owner refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":[9]}},allowed,parents),"skipped parent refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":[10]}},allowed,parents),"non-native rotating joint stays a manual choice")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":[8.5]}},allowed,parents),"fractional selector refuses")
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":["8"]}},allowed,parents),"numeric strings do not guess a joint")
	check(not Editor.native_existing_chain(valid,allowed,{7:-1,8:true,9:8}),"corrupt parent cannot masquerade as an index")
	var excessive: Array=[]
	for index in range(65):excessive.append(index)
	check(not Editor.native_existing_chain({"existing_chain":{"center_node":7,"joint_nodes":excessive}},allowed,parents),"excessive proposed chain refuses")
	check(not Editor.native_existing_chain(valid,{},parents),"legacy models without verified native owners keep ordinary behavior")
	check(var_to_bytes([valid,allowed,parents])==before,"choosing a native suggestion never mutates source assessment or maps")
	print("SOURCE_NATIVE_HELPER_CHOICE "+JSON.stringify({"checks":checks,"failures":failures,"native_import":false,"simulation":false}))
	quit(0 if failures==0 else 1)
