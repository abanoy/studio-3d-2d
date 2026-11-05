extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var failures:=0;var checks:=0
	for mode in ["ease","linear","hold"]:
		var model:=D.Model.definition("res://project.godot")
		for at in [0,12,24]:
			var value:=D.Model.identity();value.position=[float(at),0.,0.];value["scale"]=1.+float(at)/24.
			model.pose_keys.append({"frame":at,"pose":{"arm":value.duplicate(true)},"transform":value,"interpolation":mode})
		var promoted:=D.put_component(model,6,"position",[4.,2.,0.],mode,96)
		var cut:=D.edit_clip(promoted.data,"split","",8,96)
		var index:=D.Model.Clips.index_id(cut.data,cut.right_id)
		var piece: Dictionary=cut.data.animation_clips[index].duplicate(true)
		var tracks: Dictionary=cut.data.root_components[piece.id].duplicate(true)
		var original: Dictionary=cut.data.duplicate(true)
		var pasted:=D.paste_clip(cut.data,piece,tracks,50,96);checks+=1
		if pasted.has("error"):failures+=1;print(pasted);continue
		var before:=D.compile(cut.data,96);var after:=D.compile(pasted.data,96);var exact:=true
		for quarter in range(int(piece.length)*4):
			var delta:=float(quarter)/4.
			exact=exact and D.Adapter.compiled_sample(before,float(piece.start)+delta)==D.Adapter.compiled_sample(after,50.+delta)
			exact=exact and D.Body.B.sample_channel(D.Body.view(D.legacy_view(cut.data)),float(piece.start)+delta,"arm")==D.Body.B.sample_channel(D.Body.view(D.legacy_view(pasted.data)),50.+delta,"arm")
		checks+=1
		if not exact:failures+=1;print("FAIL pasted slice motion")
		tracks.position.clear();piece.keys.clear();checks+=1
		if cut.data!=original or pasted.data.root_components[pasted.clip_id].position.is_empty():failures+=1;print("FAIL clipboard isolation")
		checks+=1
		if not D.paste_clip(cut.data,original.animation_clips[index],original.root_components[cut.right_id],9,96).has("error") or cut.data!=original:failures+=1;print("FAIL overlap refusal")
		var legacy:=D.paste_clip(cut.data,original.animation_clips[index],{},50,96);checks+=1
		if legacy.has("error") or not legacy.data.root_components.has(legacy.clip_id) or not D.controls(legacy.data).any(func(key):return key.frame>=50):failures+=1;print("FAIL legacy pasted root catalogue")
	print("ROOT_COMPONENT_PASTE "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
