extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	var neutral:=D.Model.identity();neutral["scale"]=1.
	var variants:=[neutral.duplicate(true),neutral.duplicate(true),neutral.duplicate(true),neutral.duplicate(true),neutral.duplicate(true),neutral.duplicate(true)]
	variants[1].position=[1.,0.,0.];variants[2].rotation_xyzw=[0.,sin(.2),0.,cos(.2)];variants[3].scale=2.
	variants[4].rotation_xyzw=[0.,0.,0.,-1.];variants[5].position=[1.,0.,0.];variants[5].scale=2.
	var expected:=[[],["position"],["rotation_xyzw"],["scale"],[],["position","scale"]]
	for index in range(variants.size()):
		checks+=1
		if D.changed_root_fields(neutral,variants[index])!=expected[index]:failures+=1;print("FAIL root edit component classification")
	for mode in ["ease","linear","hold"]:
		var source:=D.Model.definition("res://project.godot")
		for at in [0,24]:
			var value:=D.Model.identity();value["scale"]=1.+float(at)/24.;value.position=[float(at),0.,0.]
			var q:=Quaternion(Vector3.UP,float(at)/24.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			source.pose_keys.append({"frame":at,"pose":{},"transform":value,"interpolation":mode})
		var original: Dictionary=D.promote(source,48).data;var before:=D.compile(original,48)
		var transform:=D.Adapter.compiled_sample(before,12);transform.position=[3.,2.,1.]
		var draft:=original.duplicate(true);draft.position=transform.position;draft.draft_frame=12
		var key:={"frame":12,"pose":{},"transform":transform,"interpolation":"ease","authored_channels":["@root"],"root_component_fields":["position"]}
		var result:=D.Body.put(draft,key,48,original);checks+=1
		if result.has("error"):failures+=1;print(result);continue
		var after:=D.compile(result.data,48);var exact:=true
		for quarter in range(193):
			var a:=D.Adapter.compiled_sample(before,float(quarter)/4.);var b:=D.Adapter.compiled_sample(after,float(quarter)/4.)
			exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
		checks+=1
		if not exact or D.controls(result.data).filter(func(row):return row.frame==12)[0].components!={"position":"ease"}:failures+=1;print("FAIL position-only authoring")
		key.erase("root_component_fields");var whole:=D.Body.put(draft,key,48,original);checks+=1
		if whole.has("error") or D.controls(whole.data).filter(func(row):return row.frame==12)[0].components.size()!=3:failures+=1;print("FAIL deliberate whole-root recording")
		key.root_component_fields=["unknown"];var saved:=original.duplicate(true);checks+=1
		if not D.Body.put(draft,key,48,original).has("error") or original!=saved:failures+=1;print("FAIL invalid field atomic refusal")
	print("ROOT_COMPONENT_AUTHORING "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
