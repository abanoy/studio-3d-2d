extends SceneTree
const PathData=preload("res://src/movement_path.gd")
const D=PathData.Components
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","linear","hold"]:
		var source:=D.Model.definition("res://project.godot")
		for at in [0,24]:
			var value:=D.Model.identity();value["scale"]=1.+float(at)/24.;value.position=[float(at),0.,0.]
			var q:=Quaternion(Vector3.UP,float(at)/24.);value.rotation_xyzw=[q.x,q.y,q.z,q.w]
			source.pose_keys.append({"frame":at,"pose":{},"transform":value,"interpolation":mode})
		var promoted:=D.put_component(source,6,"rotation_xyzw",[0.,0.,0.,1.],"linear",48)
		var changed:=PathData.change(promoted.data,12,Vector3(5,2,1),48);checks+=1
		if changed.has("error"):failures+=1;print(changed);continue
		var before:=D.compile(promoted.data,48);var after:=D.compile(changed.data,48);var exact:=true
		for quarter in range(193):
			var a:=D.Adapter.compiled_sample(before,float(quarter)/4.);var b:=D.Adapter.compiled_sample(after,float(quarter)/4.)
			exact=exact and a.rotation_xyzw==b.rotation_xyzw and a.scale==b.scale
		checks+=1
		if not exact or D.Adapter.compiled_sample(after,12).position!=[5.,2.,1.]:failures+=1;print("FAIL path edits independent position")
		checks+=1
		if PathData.controls(changed.data).map(func(key):return key.frame)!=[0,12,24]:failures+=1;print("FAIL rotation-only path dot")
		var line:=PathData.preview(changed.data,{"fps_num":24,"fps_den":1,"duration_frames":48});checks+=1
		if line.size()!=49 or not line.any(func(point):return point.frame==12 and point.position==Vector3(5,2,1)):failures+=1;print("FAIL component preview")
		var removed:=PathData.remove(changed.data,12,48);var restored:=D.compile(removed.data,48);exact=true
		for quarter in range(193):exact=exact and D.Adapter.compiled_sample(before,float(quarter)/4.)==D.Adapter.compiled_sample(restored,float(quarter)/4.)
		checks+=1
		if not exact:failures+=1;print("FAIL path deletion changes peers")
	print("ROOT_COMPONENT_PATH "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
