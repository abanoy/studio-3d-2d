extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Shapes=D.Model.ShapeAnimation
func _initialize() -> void:
	var checks:=0;var failures:=0
	var data: Dictionary=D.put_component(D.Model.definition("res://project.godot"),12,"position",[3.,0.,0.],"ease",48).data
	data.shape_base={"0":{"0":0.}};data.shape_pose={"0":{"0":0.}};data.shape_starts={"0":{"0":0}}
	var original:=data.duplicate(true);var baseline:=D.compile(data,48)
	var promoted:=Shapes.promote(data);checks+=1
	if promoted!=original or promoted.format!=D.FORMAT:failures+=1;print("FAIL shape promotion loses components")
	for at in [0,12,24]:
		var changed:=Shapes.put_key(data,{"frame":at,"shapes":{"0":{"0":0.75}},"interpolation":"ease"},48)
		checks+=1
		var error:=D.validate(changed,48)
		if not error.is_empty():failures+=1;print(error);continue
		var compiled:=D.compile(changed,48);var exact:=true
		for quarter in range(193):exact=exact and D.Adapter.compiled_sample(baseline,float(quarter)/4.)==D.Adapter.compiled_sample(compiled,float(quarter)/4.)
		checks+=1
		if not exact or Shapes.sample(changed,at)["0"]["0"]!=.75 or data!=original:failures+=1;print("FAIL independent shape target/root preservation")
		var removed:=Shapes.remove_key(changed,at,"0","0");checks+=1
		if not D.validate(removed,48).is_empty() or Shapes.sample(removed,at)["0"]["0"]!=0.:failures+=1;print("FAIL shape removal")
	var hidden:=data.duplicate(true);D.Model.Visibility.put(hidden,6,false);checks+=1
	if not D.Model.Visibility.validate(hidden,48).is_empty() or D.Model.Visibility.target(hidden,6) or hidden.root_components!=data.root_components:failures+=1;print("FAIL visibility isolation")
	print("ROOT_COMPONENT_SHAPES "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
