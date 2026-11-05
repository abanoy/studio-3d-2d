extends SceneTree
const Curves=preload("res://src/root_component_curves.gd")
const Model=Curves.Model
func _initialize() -> void:
	var failures:=0;var checks:=0
	for mode in ["ease","linear","hold"]:
		var keys:=[]
		for at in [0,24,48]:
			var value:=Model.identity();value["scale"]=1.+float(at)/48.;value.position=[float(at)/12.,float(at)/48.,0.]
			var q:=Quaternion(Vector3.UP,float(at)/24.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			keys.append({"frame":at,"value":value,"interpolation":mode})
		var tracks:=Curves.split(keys);var exact:=true;checks+=1
		if not Curves.validate(tracks).is_empty():failures+=1;print(Curves.validate(tracks))
		for quarter in range(193):
			var at:=float(quarter)/4.;var pair:=Model.curve_pair(keys,at)
			exact=exact and Curves.sample(tracks,at,keys[0].value)==Model.blend_transform(pair.a.value,pair.b.value,pair.t)
		checks+=1
		if not exact:failures+=1
		var changed: Dictionary=tracks.duplicate(true);var value:=Model.identity();value["scale"]=1.;value.position=[3.,2.,1.]
		Model.Timeline.put_key(changed.position,{"frame":12,"value":value,"interpolation":"ease"});exact=true
		for quarter in range(193):
			var at:=float(quarter)/4.;var a:=Curves.sample(tracks,at,keys[0].value);var b:=Curves.sample(changed,at,keys[0].value)
			exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
		checks+=1
		if not exact or Curves.sample(changed,12,keys[0].value).position!=[3.,2.,1.]:failures+=1
		var saved: Dictionary=JSON.parse_string(JSON.stringify(tracks));var edit:=Curves.put(saved,"position",12,[3.,2.,1.],"ease");checks+=1
		if edit.has("error") or edit.data.rotation_xyzw!=saved.rotation_xyzw or edit.data.scale!=saved.scale or edit.data==saved:failures+=1;print("EDIT "+str(edit))
		for bad in [["position",-1,[0.,0.,0.],"ease"],["scale",12,-1.,"ease"],["position",12,[NAN,0.,0.],"ease"],["rotation_xyzw",12,[0.,0.,0.,0.],"ease"],["position",12,[0.,0.,0.],"unknown"]]:
			checks+=1
			if not Curves.put(saved,bad[0],bad[1],bad[2],bad[3]).has("error"):failures+=1;print("ACCEPTED_BAD "+str(bad))
		var wrong:=saved.duplicate(true);wrong.format="studio_root_components_2";checks+=1
		if Curves.validate(wrong).is_empty():failures+=1
	print("ROOT_COMPONENT_CURVES "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
