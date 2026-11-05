extends SceneTree
const Adapter=preload("res://src/root_component_clips.gd")
const B=Adapter.B
const Model=B.Model
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","hold","linear"]:
		var model:=Model.definition("res://project.godot")
		for at in [0,24,48]:
			var value:=Model.identity();value["scale"]=1.+float(at)/48.;value.position=[float(at)/12.,0.,0.]
			var q:=Quaternion(Vector3.UP,float(at)/24.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			model.pose_keys.append({"frame":at,"pose":{},"transform":value,"interpolation":mode})
		var body:=B.extract(model,96);var split:=B.split(body,12,96);var moved:=B.move(split.data,split.right_id,30,96)
		for source in [body,split.data,moved.data]:
			var tracks:=Adapter.extract(source);var exact:=true
			for quarter in range(385):
				var at:=float(quarter)/4.;exact=exact and Adapter.sample(source,tracks,at)==B.sample_channel(source,at,"@root")
			checks+=1
			if not exact:failures+=1;print("FAIL source mapping "+mode)
			var piece: Dictionary=source.pieces[-1];var edited:=tracks.duplicate(true);var point:=Adapter.Components.put(edited[piece.id],"position",36,[5.,1.,2.],"ease");edited[piece.id]=point.data;exact=true
			for quarter in range(385):
				var at:=float(quarter)/4.;var a:=Adapter.sample(source,tracks,at);var b:=Adapter.sample(source,edited,at)
				exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
			checks+=1
			if not exact:failures+=1;print("FAIL peer curves "+mode)
			var prepared:=Adapter.compile(source,edited,96);checks+=1
			if prepared.has("error"):failures+=1;print(prepared);continue
			var expected:=[]
			for quarter in range(385):expected.append(Adapter.sample(source,edited,float(quarter)/4.))
			edited.clear();exact=true
			for quarter in range(384,-1,-1):exact=exact and Adapter.compiled_sample(prepared,float(quarter)/4.)==expected[quarter]
			checks+=1
			if not exact:failures+=1;print("FAIL compiled revision isolation "+mode)
	print("ROOT_COMPONENT_CLIPS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
