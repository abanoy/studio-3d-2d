extends SceneTree
const D=preload("res://src/root_component_document.gd")
const B=D.Body.B
const Model=D.Model
func _initialize() -> void:
	var failures:=0;var checks:=0
	for mode in ["ease","linear","hold"]:
		var model:=Model.definition("res://project.godot")
		for at in [0,24,48]:
			var value:=Model.identity();value["scale"]=1.+float(at)/48.;value.position=[float(at)/12.,0.,0.];var q:=Quaternion(Vector3.UP,float(at)/24.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			var bone:=Model.identity();bone.position=[float(at)/48.,0.,0.]
			model.pose_keys.append({"frame":at,"pose":{"arm":bone},"transform":value,"interpolation":mode})
		var promoted:=D.Body.promote(model,96);var split:=B.split(D.Body.view(promoted),12,96);var moved:=B.move(split.data,split.right_id,30,96);var legacy:=D.Body.install(promoted,moved.data)
		var original:=D.promote(legacy,96);var before:=D.compile(original.data,96)
		var edited:=D.put_component(original.data,20,"position",[5.,2.,1.],"ease",96);checks+=1
		if edited.has("error"):failures+=1;print(edited);continue
		var after:=D.compile(edited.data,96);var exact:=true
		for quarter in range(385):
			var at:=float(quarter)/4.;var a:=D.Adapter.compiled_sample(before,at);var b:=D.Adapter.compiled_sample(after,at)
			exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale and B.sample_channel(D.Body.view(legacy),at,"arm")==B.sample_channel(D.Body.view(D.legacy_view(edited.data)),at,"arm")
		checks+=1
		if not exact or D.Adapter.compiled_sample(after,20).position!=[5.,2.,1.]:failures+=1
		checks+=1
		if not D.controls(edited.data).any(func(key):return key.frame==20 and key.components.keys()==["position"]):failures+=1
		var erased:=D.remove_component(edited.data,20,"position",96);checks+=1
		if erased.has("error"):failures+=1;continue
		var erased_runtime:=D.compile(erased.data,96);exact=true
		for quarter in range(385):exact=exact and D.Adapter.compiled_sample(before,float(quarter)/4.)==D.Adapter.compiled_sample(erased_runtime,float(quarter)/4.)
		checks+=1
		if not exact or D.controls(erased.data).any(func(key):return key.frame==20):failures+=1
		for frame in [6,25,80]:
			var bone:=Model.identity();bone.position=[0.,1.,0.]
			var posed:=D.put_bones(edited.data,frame,{"other":bone},"ease",96);checks+=1
			if posed.has("error"):failures+=1;print(posed);continue
			var posed_runtime:=D.compile(posed.data,96);exact=true
			for quarter in range(385):
				var at:=float(quarter)/4.;exact=exact and D.Adapter.compiled_sample(after,at)==D.Adapter.compiled_sample(posed_runtime,at) and B.sample_channel(D.Body.view(D.legacy_view(edited.data)),at,"arm")==B.sample_channel(D.Body.view(D.legacy_view(posed.data)),at,"arm")
			checks+=1
			if not exact or B.sample_channel(D.Body.view(D.legacy_view(posed.data)),frame,"other").position!=[0.,1.,0.]:failures+=1;print("FAIL component root isolation from bone edit")
		var cut:=D.edit_clip(edited.data,"split","",40,96);checks+=1
		if cut.has("error"):failures+=1;print(cut);continue
		var cut_runtime:=D.compile(cut.data,96);exact=true
		for quarter in range(385):exact=exact and D.Adapter.compiled_sample(after,float(quarter)/4.)==D.Adapter.compiled_sample(cut_runtime,float(quarter)/4.)
		checks+=1
		if not exact:failures+=1;print("FAIL split components")
		var shifted:=D.edit_clip(cut.data,"move",cut.right_id,45,96);checks+=1
		if shifted.has("error"):failures+=1;print(shifted);continue
		var shifted_runtime:=D.compile(shifted.data,96);exact=true
		for quarter in range(105):exact=exact and D.Adapter.compiled_sample(cut_runtime,40.+float(quarter)/4.)==D.Adapter.compiled_sample(shifted_runtime,45.+float(quarter)/4.)
		checks+=1
		if not exact:failures+=1;print("FAIL move component source time")
		var removed:=D.edit_clip(shifted.data,"remove",cut.right_id,0,96);checks+=1
		if removed.has("error") or removed.data.root_components.has(cut.right_id):failures+=1
	print("ROOT_COMPONENT_GAPS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
