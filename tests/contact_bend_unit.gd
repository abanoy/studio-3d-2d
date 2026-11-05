extends SceneTree
const Bend=preload("res://src/contact_bend.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:failures+=1;print("FAIL "+label)
func _initialize() -> void:
	var legs: Array=[[Vector3(.1,1,0),Vector3(.098,.5,0),Vector3(.1,0,0)],[Vector3(-.1,1,0),Vector3(-.098,.5,0),Vector3(-.1,0,0)]]
	var saved:=legs.duplicate(true);var hints:=Bend.hints(legs)
	check(hints.size()==2 and hints[0].z>.9 and hints[1].z>.9,"ambiguous sideways offsets prefer anatomical forward")
	check(legs==saved,"hint assessment is read-only")
	for angle in [0.,.7,2.9]:
		for scale in [.01,1.,30.]:
			var t:=Transform3D(Basis(Quaternion(Vector3(1,2,3).normalized(),angle)).scaled(Vector3.ONE*scale),Vector3(2,-4,3))
			var moved:=[]
			for leg in legs:
				var points:=[]
				for point in leg:points.append(t*point)
				moved.append(points)
			var actual:=Bend.hints(moved)
			check(actual.size()==2 and actual[0].distance_to(t*hints[0])<.00001*maxf(1,scale) and actual[1].distance_to(t*hints[1])<.00001*maxf(1,scale),"hints follow inherited orientation and positive uniform scale")
	var bent:=legs.duplicate(true);bent[0][1].z=.12
	var mixed:=Bend.hints(bent)
	check(mixed.size()==2 and mixed[0]==null and mixed[1] is Vector3,"clear authored knee bend keeps its existing direction")
	bent[1][1].z=-.12
	check(Bend.hints(bent)==[null,null],"both deliberate forward and reverse bends remain authoritative")
	check(Bend.hints([]).is_empty(),"missing pair gives no inferred hint")
	var collapsed:=legs.duplicate(true);collapsed[0]=[Vector3.ZERO,Vector3.ZERO,Vector3.ZERO]
	check(Bend.hints(collapsed).is_empty(),"degenerate leg gives no inferred hint")
	var overlapping:=legs.duplicate(true);overlapping[1]=overlapping[0].duplicate()
	check(Bend.hints(overlapping).is_empty(),"ambiguous left/right landmarks give no inferred hint")
	print("CONTACT_BEND "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
