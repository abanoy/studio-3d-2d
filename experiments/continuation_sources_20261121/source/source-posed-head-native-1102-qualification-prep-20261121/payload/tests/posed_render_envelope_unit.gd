extends SceneTree
const E=preload("res://src/posed_render_envelope.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func inside(box: AABB,point: Vector3) -> bool:
	return point.x>=box.position.x-0.00001 and point.y>=box.position.y-0.00001 and point.z>=box.position.z-0.00001 and point.x<=box.end.x+0.00001 and point.y<=box.end.y+0.00001 and point.z<=box.end.z+0.00001
func _initialize() -> void:
	var base:=AABB(Vector3(10,20,30),Vector3(2,4,6))
	var transforms: Array=[Transform3D(Basis.IDENTITY,Vector3(5,-3,7)),Transform3D(Basis(Vector3(0,0,1),PI*.5),Vector3(-2,8,1))]
	for sum in [0.9995,1.,1.0005]:
		var result:=E.calculate(base,transforms,sum,sum,false)
		var contained:=not result.has("error")
		# Independent direct skin evaluation, including endpoints and interior
		# vertices, with 4/8 positive influence slots and non-unit total weights.
		for count in [4,8]:
			for fraction in [0.,.25,.5,.75,1.]:
				var point: Vector3=base.position+base.size*Vector3(fraction,1.-fraction,fraction*.5)
				var actual:=Vector3.ZERO
				for slot in range(count):actual+=(transforms[slot%2]*point)*float(sum)/count
				contained=contained and inside(result.bounds,actual)
		check(contained,"direct4/8-influence points enclosed at sum "+str(sum))
	var interval:=E.calculate(base,transforms,.9995,1.0005,false)
	var full_interval:=not interval.has("error")
	for sum in [.9995,.99975,1.,1.00025,1.0005]:
		for share in [0.,.1,.5,.9,1.]:
			var point:=base.get_center()
			var actual: Vector3=(transforms[0]*point)*(float(sum)*share)+(transforms[1]*point)*(float(sum)*(1.-share))
			full_interval=full_interval and inside(interval.bounds,actual)
	check(full_interval,"actual sum interval and independent unequal influence mixtures are enclosed")
	var offset:=AABB(Vector3(100,100,100),Vector3.ONE)
	var below:=E.calculate(offset,[Transform3D.IDENTITY],.999,.999,false)
	check(not offset.encloses(below.bounds) and inside(below.bounds,Vector3(100,100,100)*.999),"below-one weights move offset geometry outside the old unscaled union")
	var above:=E.calculate(offset,[Transform3D.IDENTITY],1.001,1.001,false)
	check(not offset.encloses(above.bounds) and inside(above.bounds,Vector3(101,101,101)*1.001),"above-one weights move offset geometry outside the old unscaled union")
	check(not below.bounds.has_point(Vector3.ZERO),"tight positive sum interval does not add the distant local origin")
	var mixed:=E.calculate(base,transforms,.999,1.001,true)
	check(mixed.bounds.encloses(base),"mixed weighted and unskinned surfaces retain the raw geometry")
	check(E.calculate(base,[],1.,1.,true).bounds==base,"fully unskinned geometry retains its intrinsic bound")
	check(E.calculate(base,[],1.,1.,false).has("error"),"missing weighted geometry refuses")
	for pair in [[0.,1.],[-1.,1.],[1.1,1.],[NAN,1.],[1.,INF]]:
		check(E.calculate(base,transforms,pair[0],pair[1],false).has("error"),"invalid weight interval refuses "+str(pair))
	var invalid:=Transform3D.IDENTITY;invalid.origin.x=INF
	check(E.calculate(base,[invalid],1.,1.,false).has("error"),"non-finite skin transform refuses")
	check(E.calculate(AABB(Vector3.ZERO,Vector3(-1,1,1)),transforms,1.,1.,false).has("error"),"negative intrinsic extent refuses")
	check(E.calculate(base,[42],1.,1.,false).has("error"),"wrong palette type refuses")
	var padding:=E.padding(offset,below.bounds)
	check(padding.margin>padding.geometric_margin and offset.grow(padding.margin).encloses(below.bounds),"derived finite margin encloses the independently shifted box")
	check(padding.margin<1.,"derived near-unit-weight padding is bounded rather than a huge diagnostic margin")
	check(E.padding(offset,AABB(Vector3(INF,0,0),Vector3.ONE)).has("error"),"non-finite padding target refuses")
	print("POSED_RENDER_ENVELOPE "+JSON.stringify({"checks":checks,"failures":failures,"graphics_or_native_assets_used":false}))
	quit(0 if failures==0 else 1)
