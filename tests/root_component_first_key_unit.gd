extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var failures:=0;var checks:=0
	for at in [0,12]:
		var original:=D.Model.definition("res://project.godot");var result:=D.put_component(original,at,"position",[3.,0.,0.],"ease",48);checks+=1
		if result.has("error"):failures+=1;print(result);continue
		var runtime:=D.compile(result.data,48);checks+=1
		if D.Adapter.compiled_sample(runtime,at).position!=[3.,0.,0.] or D.controls(result.data).map(func(key):return key.frame)!=[at]:failures+=1
		if at==12:
			var earlier:=D.put_component(result.data,0,"position",[7.,0.,0.],"ease",48);checks+=1
			if earlier.has("error"):failures+=1;print(earlier);continue
			checks+=1
			if D.controls(earlier.data).map(func(key):return key.frame)!=[0,12]:failures+=1
	print("ROOT_COMPONENT_FIRST_KEY "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
