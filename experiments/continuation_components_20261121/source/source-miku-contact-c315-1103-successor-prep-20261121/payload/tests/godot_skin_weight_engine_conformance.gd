extends SceneTree
const Weights=preload("res://src/godot_skin_weight_conversion.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	check(Weights.engine_supported(Engine.get_version_info()),"actual engine hash matches pinned source")
	for source in [[.5,.5,0.,0.],[1.,.5,.25,.25],[Weights.f32(.1),Weights.f32(.2),Weights.f32(.3),Weights.f32(.4)],[1.,0.,0.,0.]]:
		var prediction:=Weights.expected(source)
		var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
		var bones:=PackedInt32Array();var weights:=PackedFloat32Array()
		for vertex in range(3):
			for slot in range(4):bones.append(slot);weights.append(prediction.normalized_float32_weights[slot])
		arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		check(mesh.get_surface_count()==1,"actual ArrayMesh accepts synthetic four-slot surface")
		if mesh.get_surface_count()!=1:continue
		var readback: Array=mesh.surface_get_arrays(0)
		check(readback[Mesh.ARRAY_BONES]==bones and readback[Mesh.ARRAY_WEIGHTS] is PackedFloat32Array and readback[Mesh.ARRAY_WEIGHTS].size()==12,"actual imported slot order and float32 readback profile preserved")
		var exact:=true
		for vertex in range(3):
			for slot in range(4):exact=exact and readback[Mesh.ARRAY_WEIGHTS][vertex*4+slot]==prediction.readback_float32_weights[slot]
		check(exact,"every synthetic engine weight equals source-derived exact conversion")
	print("GODOT_SKIN_WEIGHT_ENGINE_CONFORMANCE ",JSON.stringify({"checks":checks,"failures":failures,"engine":Engine.get_version_info()}));quit(0 if failures==0 else 1)
