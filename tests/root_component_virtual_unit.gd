extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Model=D.Model
func _initialize() -> void:
	var model:=D.Body.promote(Model.definition("res://project.godot"),48)
	var transform:=Model.identity();transform["scale"]=1.;transform.position=[3.,0.,0.]
	var source:=D.Body.view(model);var piece: Dictionary=source.pieces[0]
	piece.placeholder=false;piece.legacy_channels=[];piece.length=13;piece.origin=0;piece.untrimmed=true;piece.controls={"@root":[{"frame":12,"value":transform,"interpolation":"ease"}]}
	var body:={"data":source}
	model=D.Body.install(model,body.data);var original:=D.promote(model,48);var checks:=0;var failures:=0
	checks+=1
	if D.controls(original.data).map(func(key):return key.frame)!=[12]:failures+=1;print("FAIL synthetic leading point exposed")
	var baseline:=D.compile(original.data,48);var edited:=D.put_component(original.data,0,"position",[7.,0.,0.],"ease",48);checks+=1
	if edited.has("error"):failures+=1;print(edited);quit(1);return
	if not D.controls(edited.data).any(func(key):return key.frame==0 and key.components.keys()==["position"]):failures+=1;print("FAIL explicit leading point")
	var removed:=D.remove_component(edited.data,0,"position",48);var restored:=D.compile(removed.data,48);var exact:=true
	for quarter in range(193):exact=exact and D.Adapter.compiled_sample(baseline,float(quarter)/4.)==D.Adapter.compiled_sample(restored,float(quarter)/4.)
	checks+=1
	if not exact or D.controls(removed.data).map(func(key):return key.frame)!=[12]:failures+=1;print("FAIL virtual lead-in restoration")
	print("ROOT_COMPONENT_VIRTUAL "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
