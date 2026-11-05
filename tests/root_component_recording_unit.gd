extends SceneTree
const D=preload("res://src/root_component_document.gd")
const Recording=preload("res://src/physics_recording.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","linear","hold"]:
		var source:=D.Model.definition("res://project.godot")
		for at in [0,24]:
			var value:=D.Model.identity();value["scale"]=1.+float(at)/24.;value.position=[float(at),0.,0.]
			source.pose_keys.append({"frame":at,"pose":{},"transform":value,"interpolation":mode})
		var original: Dictionary=D.put_component(source,4,"position",[2.,3.,0.],"ease",48).data
		var before:=D.compile(original,48);var saved:=original.duplicate(true);var take:=[]
		for frame in range(6,13):
			var transform:=D.Model.identity();transform.position=[float(frame),5.,0.];transform["scale"]=1.
			take.append({"frame":frame,"pose":{},"transform":transform,"interpolation":"linear"})
		var recorded:=Recording.replace_range(original,take,6,12,48);checks+=1
		if recorded.has("error"):failures+=1;print(recorded);continue
		var after:=D.compile(recorded.data,48);var exact:=true
		for quarter in range(193):
			var frame:=float(quarter)/4.
			if frame<=5 or frame>=13:exact=exact and D.Adapter.compiled_sample(before,frame)==D.Adapter.compiled_sample(after,frame)
		checks+=1
		if not exact or original!=saved:failures+=1;print("FAIL retained component slices")
		exact=true
		for key in take:exact=exact and D.Adapter.compiled_sample(after,key.frame).position==key.transform.position and D.Adapter.compiled_sample(after,key.frame).scale==1.
		checks+=1
		if not exact or recorded.data.root_components.size()!=3:failures+=1;print("FAIL captured component controls")
		var recorder:=Recording.new();recorder.targets={"actor":original};checks+=1
		if recorder.sample_controls("actor")!=4 or recorder.sample_cost("actor",take[0])<=Recording.bytes(take[0]):failures+=1;print("FAIL component capture accounting")
		recorder.free()
	print("ROOT_COMPONENT_RECORDING "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
