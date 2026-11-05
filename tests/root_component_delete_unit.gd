extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","linear","hold"]:
		var source:=D.Model.definition("res://project.godot")
		for at in [0,24]:
			var value:=D.Model.identity();value.position=[float(at),0.,0.];value["scale"]=1.
			source.pose_keys.append({"frame":at,"pose":{"arm":value.duplicate(true)},"transform":value,"interpolation":mode})
		var original:=D.promote(source,48)
		if original.has("error"):print(original);quit(1);return
		var target:=D.Model.identity();target.position=[5.,2.,0.];target["scale"]=2.
		var bone:=target.duplicate(true);bone.scale=1.
		var edited:=D.record_pose(original.data,12,{"arm":bone},target,"ease",48)
		if edited.has("error"):print(edited);quit(1);return
		var root_only:=D.Body.remove_key(edited.data,12,"@root",48);checks+=1
		if root_only.has("error") or D.authored_keys(root_only.data,48).filter(func(row):return row.frame==12)[0].authored_channels!=["arm"]:failures+=1;print("FAIL root deletion retains bone key")
		var bone_only:=D.Body.remove_key(edited.data,12,"arm",48);checks+=1
		if bone_only.has("error") or D.authored_keys(bone_only.data,48).filter(func(row):return row.frame==12)[0].authored_channels!=["@root"] or bone_only.data.root_components!=edited.data.root_components:failures+=1;print("FAIL bone deletion retains root keys")
		var before: Dictionary=edited.data.duplicate(true);var removed:=D.remove_pose_key(edited.data,12,48);checks+=1
		if removed.has("error"):failures+=1;print(removed);continue
		var a:=D.compile(original.data,48);var b:=D.compile(removed.data,48);var exact:=true
		for quarter in range(193):
			var frame:=float(quarter)/4.;exact=exact and D.Adapter.compiled_sample(a,frame)==D.Adapter.compiled_sample(b,frame)
			exact=exact and D.Body.B.sample_channel(D.Body.view(D.legacy_view(original.data)),frame,"arm")==D.Body.B.sample_channel(D.Body.view(D.legacy_view(removed.data)),frame,"arm")
		checks+=1
		if not exact:failures+=1;print("FAIL deleting pose does not restore prior curves")
		checks+=1
		if edited.data!=before or D.authored_keys(removed.data,48).map(func(key):return key.frame)!=[0,24]:failures+=1;print("FAIL neighboring keys/input preservation")
		checks+=1
		if not D.remove_pose_key(edited.data,-1,48).has("error") or edited.data!=before:failures+=1;print("FAIL invalid key refusal")
	print("ROOT_COMPONENT_DELETE "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
