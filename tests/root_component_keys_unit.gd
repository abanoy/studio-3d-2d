extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	var data: Dictionary=D.put_component(D.Model.definition("res://project.godot"),12,"position",[3.,0.,0.],"ease",48).data
	data=D.put_component(data,12,"scale",2.,"hold",48).data
	var bone:=D.Model.identity();bone.position=[0.,2.,0.]
	data=D.put_bones(data,6,{"arm":bone},"linear",48).data
	data=D.put_bones(data,12,{"arm":bone},"hold",48).data
	var original:=data.duplicate(true);var keys:=D.authored_keys(data,48);checks+=1
	if keys.map(func(key):return key.frame)!=[6,12]:failures+=1;print("FAIL synthetic/duplicate key catalogue")
	checks+=1
	if keys[0].authored_channels!=["arm"] or not keys[0].root_component_modes.is_empty() or keys[0].body_modes!={"arm":"linear"}:failures+=1;print("FAIL bone-only key")
	checks+=1
	if keys[1].authored_channels!=["@root","arm"] or keys[1].root_component_modes!={"position":"ease","scale":"hold"} or keys[1].body_modes!={"arm":"hold"}:failures+=1;print("FAIL component-specific modes")
	checks+=1
	if keys[1].transform.position!=[3.,0.,0.] or keys[1].transform.scale!=2. or keys[1].pose.arm.position!=bone.position:failures+=1;print("FAIL evaluated artist key")
	keys[1].root_component_modes.clear();keys[1].pose.arm.position.clear();checks+=1
	if data!=original or D.authored_keys(data,48)[1].root_component_modes.is_empty():failures+=1;print("FAIL catalogue isolation")
	print("ROOT_COMPONENT_KEYS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
