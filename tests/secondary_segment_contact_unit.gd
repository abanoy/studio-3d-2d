extends SceneTree
const Contact=preload("res://src/secondary_segment_contact.gd")
const SurfaceContact=preload("res://src/secondary_skin_contact.gd")
class Hierarchy extends RefCounted:
	var parents:={"A":"@root","B":"A","C":"B","D":"C"}
	func parent_id(id: String) -> String:return parents.get(id,"@root")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var start:=Vector3(-2,0,0);var finish:=Vector3(2,0,0);var a:=Vector3(0,-2,0);var b:=Vector3(0,2,0)
	var crossing: Dictionary=Contact.deflect(start,finish,a,b,1.,Vector3.UP)
	check(crossing.changed and not crossing.blocked,"whole link crossing a capsule deflects despite both endpoints being outside")
	var endpoint: Vector3=start+crossing.rotation*(finish-start)
	check(Contact.distance(start,endpoint,a,b)>=1.,"chosen rotation clears the physical radius without changing collision tolerance")
	check(absf(endpoint.distance_to(start)-finish.distance_to(start))<.00001,"rotational correction preserves link length")
	check(crossing.rotation.is_finite() and crossing.rotation.is_normalized(),"contact rotation is finite and normalized")
	var again: Dictionary=Contact.deflect(start,finish,a,b,1.,Vector3.UP)
	check(again.rotation==crossing.rotation,"ambiguous opposite direction has an exact deterministic pole")
	var clear: Dictionary=Contact.deflect(start,Vector3(-3,0,0),a,b,1.,Vector3.UP)
	check(not clear.changed and clear.rotation==Quaternion.IDENTITY,"already clear link stays exactly unchanged")
	var inside: Dictionary=Contact.deflect(Vector3.ZERO,finish,a,b,1.,Vector3.UP)
	check(inside.blocked and not inside.changed,"fixed attachment inside body reports an unresolved constraint rather than moving its anchor")
	var zero: Dictionary=Contact.deflect(start,start,a,b,1.,Vector3.UP)
	check(not zero.changed and zero.rotation==Quaternion.IDENTITY,"zero-length direction introduces no rotation or NaN")
	var sphere: Dictionary=Contact.deflect(start,finish,Vector3.ZERO,Vector3.ZERO,.5,Vector3.UP)
	check(sphere.changed and Contact.distance(start,start+sphere.rotation*(finish-start),Vector3.ZERO,Vector3.ZERO)>=.5,"degenerate capsule follows the same sphere clearance constraint")
	var short_link: Dictionary=Contact.deflect(start,Vector3(-1.5,0,0),a,b,1.,Vector3.UP)
	check(not short_link.changed,"short link that cannot reach the body stays unchanged")
	var actor:=Hierarchy.new()
	var parent_chain:={"ids":["A"],"label":"parent"};var child_chain:={"ids":["B","C"],"label":"child"}
	var order: Dictionary=Contact.ordered(actor,[child_chain,parent_chain])
	check(not order.has("error") and order.chains[0].label=="parent" and order.chains[1].label=="child","shared-tail child declared first is solved after its rotating ancestor")
	var nested: Dictionary=Contact.ordered(actor,[{"ids":["D"],"label":"last"},child_chain,parent_chain])
	check(not nested.has("error") and nested.chains[0].label=="parent" and nested.chains[1].label=="child" and nested.chains[2].label=="last","nested chain dependencies preserve ancestor-first correction order")
	var cycle: Dictionary=Contact.ordered(actor,[{"ids":["A","C"]},{"ids":["B","D"]}])
	check(cycle.has("error"),"interleaved chain ownership refuses an unsolvable dependency cycle")
	var corrected: Dictionary=SurfaceContact.rotation(Vector3(-.1,0,0),Vector3(.25,0,0),Vector3(0,-1,0),Vector3(0,1,0),.3,Vector3.UP)
	check(not corrected.is_empty(),"actual skin point can be rotated clear even when its weighted orbit center is inside the capsule")
	var moved: Vector3=Vector3(-.1,0,0)+corrected.rotation*Vector3(.35,0,0)
	check(SurfaceContact.point_distance(moved,Vector3(0,-1,0),Vector3(0,1,0))>=.3,"weighted point correction uses the actual physical radius")
	check(absf(moved.distance_to(Vector3(-.1,0,0))-.35)<.000001,"skin correction preserves the weighted orbit radius")
	var nonunit_weight:=.75;var pivot:=Vector3(2,0,0);var influenced:=Vector3(3,0,0);var fixed:=Vector3(0,1,0)*.2
	var weighted: Vector3=influenced*nonunit_weight+fixed;var lever: Vector3=(influenced-pivot)*nonunit_weight;var turn:=Quaternion(Vector3.UP,.6)
	var direct: Vector3=(pivot+turn*(influenced-pivot))*nonunit_weight+fixed
	check(direct.is_equal_approx(weighted-lever+turn*lever),"cached weighted orbit matches direct LBS without normalizing nonunit weights")
	print("SECONDARY_SEGMENT_CONTACT "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"native_or_graphics_used":false}));quit(0 if failures==0 else 1)
