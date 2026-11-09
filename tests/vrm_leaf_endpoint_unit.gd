extends SceneTree
const Definition=preload("res://src/secondary_rig.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func definition(leaf: Dictionary,kind: String="offset",collider: bool=false):
	var value=Definition.new();value.nodes=[{"children":[1]},leaf];value.parents={1:0}
	value.bindings={0:{"kind":"bone","id":"Rig::root","source_node":0},1:{"kind":kind,"id":"Rig::root","source_node":1,"position":[0,1,0],"rotation_xyzw":[0,0,0,1],"scale":[1,1,1]}}
	var native:={"boneGroups":[{"bones":[0]}]}
	if collider:native.colliderGroups=[{"node":1,"colliders":[{"offset":{},"radius":0.01}]}]
	value.parse_v0(native);return value
func _initialize() -> void:
	var leaf:={"name":"Unweighted terminal"};var result=definition(leaf)
	check(result.error.is_empty() and result.chains.size()==1 and result.chains[0].end_extension==0.0,"non-deforming terminal offset is the real chain endpoint")
	check(result.chains[0].joints.size()==2 and result.chains[0].joints[1].source_node==1 and leaf=={"name":"Unweighted terminal"},"source terminal reference and original data remain intact")
	for value in [{"mesh":0},{"camera":0},{"extensions":{"KHR_lights_punctual":{}}},{"extensions":7}]:
		var rejected=definition(value)
		check(rejected.chains[0].end_extension>0,"geometry/camera/extension nodes cannot silently become passive endpoints")
	var weighted=definition({},"bone")
	check(weighted.chains[0].end_extension>0,"poseable skin leaf keeps native virtual-tail behavior")
	var collider=definition({},"offset",true)
	check(collider.chains[0].end_extension>0,"collider-bearing leaf cannot silently become a passive endpoint")
	print("VRM_LEAF_ENDPOINTS "+JSON.stringify({"checks":checks,"failures":failures}));quit(0 if failures==0 else 1)
