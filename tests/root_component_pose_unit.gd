extends SceneTree
const D=preload("res://src/root_component_document.gd")
func _initialize() -> void:
	var checks:=0;var failures:=0
	for mode in ["ease","linear","hold"]:
		for frame in [0,18,40]:
			var source: Dictionary=D.put_component(D.Model.definition("res://project.godot"),12,"position",[2.,0.,0.],"ease",48).data
			var original: Dictionary=source.duplicate(true)
			var transform:=D.Model.identity();transform.position=[3.,2.,1.];transform["scale"]=1.5
			var q:=Quaternion(Vector3.UP,0.5);transform.rotation_xyzw=[q.x,q.y,q.z,q.w]
			var bone:=D.Model.identity();bone.position=[0.,1.,0.]
			var result:=D.record_pose(source,frame,{"arm":bone},transform,mode,48);checks+=1
			if result.has("error"):failures+=1;print(result);continue
			var restored: Dictionary=JSON.parse_string(JSON.stringify(result.data))
			var runtime:=D.compile(restored,48);var sampled:=D.Adapter.compiled_sample(runtime,frame)
			checks+=1
			if sampled.position!=transform.position or sampled.scale!=transform.scale or not Quaternion(sampled.rotation_xyzw[0],sampled.rotation_xyzw[1],sampled.rotation_xyzw[2],sampled.rotation_xyzw[3]).is_equal_approx(q):failures+=1;print("FAIL full root target")
			checks+=1
			if D.Body.B.sample_channel(D.Body.view(D.legacy_view(restored)),frame,"arm").position!=bone.position or restored.draft_frame!=frame or source!=original:failures+=1;print("FAIL pose target/draft/isolation")
			checks+=1
			if not D.controls(restored).any(func(key):return key.frame==frame and key.components.size()==3):failures+=1;print("FAIL component key catalogue")
			var invalid:=transform.duplicate(true);invalid.scale=-1.;checks+=1
			if not D.record_pose(source,frame,{"arm":bone},invalid,mode,48).has("error") or source!=original:failures+=1;print("FAIL atomic invalid pose refusal")
	print("ROOT_COMPONENT_POSE "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
