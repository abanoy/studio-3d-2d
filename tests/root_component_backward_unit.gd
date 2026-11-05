extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Model=D.Model
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","linear","hold"]:
		var model:=D.Body.promote(Model.definition("res://project.godot"),48)
		var body:=D.Body.view(model);body.start_frame=12
		var piece: Dictionary=body.pieces[0]
		piece.start=12;piece.length=13;piece.placeholder=false;piece.legacy_channels=[];piece.untrimmed=true;piece.auto_extend=true
		piece.controls={"@root":[],"arm":[]}
		for at in [0,12]:
			var value:=Model.identity();value.position=[float(at),0.,0.];value["scale"]=1.+float(at)/12.
			var q:=Quaternion(Vector3.UP,float(at)/12.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			piece.controls["@root"].append({"frame":at,"value":value,"interpolation":mode})
			piece.controls.arm.append({"frame":at,"value":value.duplicate(true),"interpolation":mode})
		var original:=D.put_component(D.Body.install(model,body),18,"position",[9.,2.,0.],mode,48)
		if original.has("error"):print(original);quit(1);return
		var before:=D.compile(original.data,48);var untouched: Dictionary=original.data.duplicate(true)
		for earlier in [0,6]:
			var bone:=Model.identity();bone.position=[0.,1.,0.]
			var edited:=D.put_bones(original.data,earlier,{"other":bone},mode,48);checks+=1
			if edited.has("error"):failures+=1;print(edited);continue
			var after:=D.compile(edited.data,48);var exact:=true
			for quarter in range(193):
				var frame:=float(quarter)/4.
				exact=exact and D.Adapter.compiled_sample(before,frame)==D.Adapter.compiled_sample(after,frame)
				exact=exact and D.Body.B.sample_channel(body,frame,"arm")==D.Body.B.sample_channel(D.Body.view(D.legacy_view(edited.data)),frame,"arm")
			checks+=1
			if not exact:failures+=1;print("FAIL backward extension changes peer curves: ",mode,earlier)
			checks+=1
			if edited.data.animation_clips.size()!=1 or edited.data.animation_clips[0].start!=earlier or D.controls(edited.data)!=D.controls(original.data) or original.data!=untouched:failures+=1;print("FAIL backward extension ownership/key times")
			checks+=1
			if D.Body.B.sample_channel(D.Body.view(D.legacy_view(edited.data)),earlier,"other").position!=[0.,1.,0.]:failures+=1;print("FAIL earlier bone target")
	print("ROOT_COMPONENT_BACKWARD "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
