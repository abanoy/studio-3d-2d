extends SceneTree
const Actual=preload("res://src/secondary_skin_contact.gd")
const Reference=preload("res://tests/reference/secondary_skin_contact_baseline.gd")
var solver: Script=Actual
var checks:=0
var failures:=0
var records: Array=[]
func need(ok: bool,label: String) -> void:
	checks+=1
	if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+label)
func _init() -> void:call_deferred("run")
func valid_turn(center: Vector3,point: Vector3,a: Vector3,b: Vector3,radius: float,pole: Vector3) -> bool:
	var turn: Dictionary=solver.rotation(center,point,a,b,radius,pole)
	if turn.is_empty():return false
	if not turn.get("rotation") is Quaternion:return false
	var q: Quaternion=turn.rotation
	if not q.is_finite() or absf(q.length()-1.)>.000001:return false
	var moved: Vector3=center+q*(point-center)
	if not moved.is_finite() or absf(moved.distance_to(center)-point.distance_to(center))>.000001:return false
	# Independent engine geometry primitive, not the tested point_distance helper.
	var nearest: Vector3=Geometry3D.get_closest_point_to_segment(moved,a,b)
	var clear: bool=moved.distance_to(nearest)>=radius
	records.append({"clear":clear,"radius_preserved":true,"finite_unit_quaternion":true})
	return clear
func run() -> void:
	var args: PackedStringArray=OS.get_cmdline_user_args()
	var reference: bool="--reference" in args
	if reference:solver=Reference
	var source_path: String="res://tests/reference/secondary_skin_contact_baseline.gd" if reference else "res://src/secondary_skin_contact.gd"
	var pin_index: int=args.find("--source-sha")
	var expected_sha: String=args[pin_index+1] if pin_index>=0 and pin_index+1<args.size() else ""
	need(expected_sha.length()==64 and FileAccess.get_sha256(source_path)==expected_sha,"selected source hash matches wrapper pin")
	var a:=Vector3(0,-2,0);var b:=Vector3(0,2,0)
	need(valid_turn(Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.UP),"vertical orbit parallel positive pole")
	need(valid_turn(Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.DOWN),"vertical orbit antiparallel positive pole")
	need(valid_turn(Vector3.ZERO,Vector3.DOWN,a,b,.5,Vector3.DOWN),"vertical orbit parallel negative pole")
	need(valid_turn(Vector3.ZERO,Vector3.DOWN,a,b,.5,Vector3.UP),"vertical orbit antiparallel negative pole")
	need(valid_turn(Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.ZERO),"vertical orbit zero pole")
	need(valid_turn(Vector3.ZERO,Vector3.RIGHT,Vector3(-2,0,0),Vector3(2,0,0),.5,Vector3.RIGHT),"horizontal orbit parallel pole")
	need(solver.downward_rotation(Vector3.ZERO,Vector3.UP,a,b,.5).is_empty(),"downward helper preserves upward collinear refusal")
	need(solver.downward_rotation(Vector3.ZERO,Vector3.DOWN,a,b,.5).is_empty(),"downward helper preserves downward collinear refusal")
	need(solver.rotation(Vector3.ZERO,Vector3.ZERO,a,b,.5,Vector3.UP).is_empty(),"zero lever remains refused")
	need(solver.rotation(Vector3.ZERO,Vector3(0,.0000005,0),a,b,.5,Vector3.UP).is_empty(),"subthreshold lever remains refused")
	need(solver.rotation(Vector3.ZERO,Vector3(0,.2,0),a,b,.5,Vector3.UP).is_empty(),"contained orbit remains blocked")
	need(solver.rotation(Vector3.ZERO,Vector3(0,.2,0),a,b,.5,Vector3.ZERO).is_empty(),"contained orbit with zero pole remains blocked")
	need(valid_turn(Vector3(0,.2,0),Vector3(0,.1,0),Vector3.ZERO,Vector3.ZERO,.25,Vector3.UP),"degenerate capsule positive endpoint escape")
	need(valid_turn(Vector3(0,-.2,0),Vector3(0,-.1,0),Vector3.ZERO,Vector3.ZERO,.25,Vector3.DOWN),"degenerate capsule negative endpoint escape")
	need(valid_turn(Vector3.ZERO,Vector3.RIGHT,a,b,.5,Vector3.RIGHT),"already clear orbit stays clear finite and same length")
	need(valid_turn(Vector3.ZERO,Vector3(.1,.8,0),a,b,.5,Vector3.RIGHT),"ordinary noncollinear escape stays clear")
	need(var_to_bytes(solver.rotation(Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.UP))==var_to_bytes(solver.rotation(Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.UP)),"degenerate result deterministic")
	var inputs: Array=[Vector3.ZERO,Vector3.UP,a,b,.5,Vector3.UP];var before:=var_to_bytes(inputs)
	solver.rotation(inputs[0],inputs[1],inputs[2],inputs[3],inputs[4],inputs[5])
	need(var_to_bytes(inputs)==before,"input values unchanged")
	need(expected_sha.length()==64 and FileAccess.get_sha256(source_path)==expected_sha,"selected source hash unchanged after controls")
	print("SECONDARY_CONTACT_ROTATION "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"graphics_used":false,"private_assets_read":false,"reference_mode":reference,"selected_source_sha256":FileAccess.get_sha256(source_path),"user_profile":OS.get_user_data_dir()}))
	quit(1 if failures else 0)
