extends SceneTree
const Editor=preload("res://src/camera_transform_editor.gd")
var checks:=0
var failures:=0
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func _initialize() -> void:
	var original:=Transform3D(Basis(Quaternion(Vector3(.2,.9,.3).normalized(),.73)),Vector3(1.23456789,-3.87654321,8.24681357))
	var initial:=[1.235,-3.877,8.247,20.,30.,40.]
	check(Editor.candidate(original,initial,initial).transform==original,"unchanged rounded fields preserve exact original transform")
	var values:=initial.duplicate();values[0]=9.125;var moved: Transform3D=Editor.candidate(original,initial,values).transform
	check(moved.basis==original.basis and moved.origin==Vector3(9.125,original.origin.y,original.origin.z),"position edit preserves all untouched float32 axes and basis")
	values=initial.duplicate();values[5]=12.5;var rotated: Transform3D=Editor.candidate(original,initial,values).transform
	check(rotated.origin==original.origin and absf(rotated.basis.determinant()-1.)<1e-6,"rotation edit preserves origin and regular basis")
	for bad in [NAN,INF,"5",true,1e13]:
		values=initial.duplicate();values[1]=bad;check(Editor.candidate(original,initial,values).has("error"),"invalid coordinate refuses "+str(bad))
	values=initial.duplicate();values[3]=36001.;check(Editor.candidate(original,initial,values).has("error"),"excessive angle refuses")
	check(Editor.candidate(original,[],[]).has("error"),"incorrect field count refuses")
	var cases: Array=[]
	for angles in [[0.,0.,0.],[0.,90.,0.],[90.,0.,0.],[0.,0.,90.],[25.,-60.,17.],[-75.,180.,-135.],[89.999,127.,-22.],[-90.,-137.,49.],[720.,-450.,1080.]]:
		var supplied: Array=[2.,3.,4.,angles[0],angles[1],angles[2]]
		var result: Transform3D=Editor.candidate(Transform3D.IDENTITY,[-1.,-1.,-1.,999.,999.,999.],supplied).transform
		cases.append({"angles":angles,"columns":[[result.basis.x.x,result.basis.x.y,result.basis.x.z],[result.basis.y.x,result.basis.y.y,result.basis.y.z],[result.basis.z.x,result.basis.z.y,result.basis.z.z]]})
	var output:={"checks":checks,"failures":failures,"cases":cases};FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify(output));print("CAMERA_TRANSFORM_UNIT ",JSON.stringify(output));quit(0 if failures==0 else 1)
