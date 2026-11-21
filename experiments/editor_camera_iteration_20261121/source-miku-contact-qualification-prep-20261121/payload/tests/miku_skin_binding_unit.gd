extends SceneTree
const Binding=preload("res://src/miku_skin_binding.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	create_timer(10).timeout.connect(func():quit(2));call_deferred("run")
func run() -> void:
	var raw: Array=[1,0,0,0,0,1,0,0,0,0,1,0,2,3,4,1]
	var affine:=Binding.matrix(raw)
	check(not affine.has("error") and affine.transform*Vector3.ONE==Vector3(3,4,5),"column-major source affine matrix is read without repair")
	var invalid: Array=raw.duplicate();invalid[3]=1
	check(Binding.matrix(invalid).has("error"),"nonaffine source matrix refuses")
	invalid=raw.duplicate();invalid[0]=NAN
	check(Binding.matrix(invalid).has("error"),"nonfinite source matrix refuses")
	invalid=raw.duplicate();invalid[0]=0
	check(Binding.matrix(invalid).has("error"),"singular source matrix refuses")
	check(Binding.difference(Transform3D.IDENTITY,Transform3D(Basis.IDENTITY,Vector3(.1,0,0)))>.099,"calibration metric includes translated frame error")
	var q:=Quaternion(Vector3.FORWARD,PI/2)
	var trs:=Binding.local_frame({"translation":[2,0,0],"rotation":[q.x,q.y,q.z,q.w],"scale":[2,3,4]})
	check(not trs.has("error") and (trs.transform*Vector3.RIGHT).distance_to(Vector3(2,-2,0))<.00001,"source TRS uses local scale before rotation")
	check(Binding.local_frame({"rotation":[0,0,0,2]}).has("error"),"nonunit source quaternion is refused rather than normalized")
	var worlds:=Binding.source_worlds({"nodes":[{"translation":[1,0,0],"children":[1]},{"translation":[0,2,0]}]})
	check(not worlds.has("error") and worlds.world[1].origin==Vector3(1,2,0),"source parent graph composes exact frames")
	check(Binding.source_worlds({"nodes":[{"children":[1]},{"children":[0]}]}).has("error"),"source graph cycle refuses")
	check(Binding.source_worlds({"nodes":[{"children":[2]},{"children":[2]},{}]}).has("error"),"multiple source parents refuse")
	var binary:=PackedByteArray();binary.resize(24)
	for i in range(6):binary.encode_float(i*4,float(i+1))
	var decoded: Dictionary={"doc":{"buffers":[{"byteLength":24}],"bufferViews":[{"byteLength":24}],"accessors":[{"bufferView":0,"componentType":5126,"type":"VEC3","count":2}]},"binary":binary}
	var rows:=Binding.accessor(decoded,0,"VEC3",5126,2)
	check(not rows.has("error") and rows.rows==[[1.,2.,3.],[4.,5.,6.]],"dense aligned accessor preserves exact row order")
	var altered: Dictionary=decoded.duplicate(true);altered.doc.accessors[0]["sparse"]={}
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"sparse accessor refuses instead of guessing")
	altered=decoded.duplicate(true);altered.doc.accessors[0]["normalized"]=true
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"normalized accessor refuses")
	altered=decoded.duplicate(true);altered.doc.accessors[0]["byteOffset"]=4
	check(Binding.accessor(altered,0,"VEC3",5126,2).has("error"),"accessor cannot escape its source view")
	check(Binding.accessor(decoded,0,"VEC4",5126,2).has("error") and Binding.accessor(decoded,0,"VEC3",5126,1).has("error"),"accessor shape and row bounds are exact")
	check(Binding.glb(PackedByteArray([1,2,3])).has("error"),"truncated source GLB refuses")
	print("MIKU_SKIN_BINDING_UNIT ",JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
