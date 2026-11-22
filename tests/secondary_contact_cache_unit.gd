extends SceneTree
const Model=preload("res://src/model.gd")
const Baseline=preload("res://tests/reference/secondary_skin_contact_baseline.gd")
const Candidate=preload("res://src/secondary_skin_contact.gd")
var checks:=0
var failures:=0
var cases: Array=[]
func need(ok: bool,label: String) -> void:
	checks+=1
	if not ok:failures+=1;push_error(label)
	else:print("PASS "+label)
func _init() -> void:call_deferred("run")
func fixture(kind: String) -> Dictionary:
	var actor=Model.new();var world:=Node3D.new();world.name="GeneratedContact";root.add_child(world);actor.root=world;actor.data=Model.definition("")
	var sk:=Skeleton3D.new();sk.name="Rig";world.add_child(sk)
	var names: Array=["Body","BodyTail","GuideA0","GuideA1","GuideB0","GuideB1"]
	var parents: Array=[-1,0,0,2,0,4]
	var origins: Array=[Vector3.ZERO,Vector3(0,1,0),Vector3(.6,.4,0),Vector3(0,-.2,0),Vector3(-.6,.4,0),Vector3(0,-.2,0)]
	for i in names.size():
		sk.add_bone(names[i]);sk.set_bone_parent(i,parents[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,origins[i]));sk.set_bone_pose_position(i,origins[i])
	sk.force_update_all_bone_transforms()
	var mesh:=MeshInstance3D.new();mesh.name="PublicStrip";world.add_child(mesh);mesh.skeleton=mesh.get_path_to(sk)
	var vertices:=PackedVector3Array();var joints:=PackedInt32Array();var weights:=PackedFloat32Array()
	for i in range(9):
		vertices.append(Vector3(.12+float(i%3)*.01,.35+float(i/3)*.03,.01))
		if kind=="clear":vertices[i]+=Vector3(3,0,0)
		if kind=="tie":vertices[i]=Vector3(.12,.4,0)
		if kind in ["cross","rotated","blocked","dependent"]:
			joints.append_array(PackedInt32Array([3,5,0,0]));weights.append_array(PackedFloat32Array([.65,.35,0,0]))
		else:
			joints.append_array(PackedInt32Array([3 if kind!="tie" or i%2==0 else 5,0,0,0]));weights.append_array(PackedFloat32Array([1,0,0,0]))
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_BONES]=joints;arrays[Mesh.ARRAY_WEIGHTS]=weights
	var resource:=ArrayMesh.new();resource.add_blend_shape("Public stretch")
	var targets: Array=[];targets.resize(Mesh.ARRAY_MAX);var delta:=vertices.duplicate()
	for i in delta.size():delta[i]+=Vector3(.01,0,0)
	targets[Mesh.ARRAY_VERTEX]=delta
	resource.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,[targets]);mesh.mesh=resource
	var skin:=Skin.new()
	for i in names.size():skin.add_bind(i,sk.get_bone_global_rest(i).affine_inverse())
	mesh.skin=skin;actor.inventory(world)
	var ids: Array=[]
	for name in names:ids.append("Rig::"+name)
	var collider:={"shape":"capsule","radius":3. if kind=="blocked" else .27,"binding":{"kind":"bone","id":ids[2] if kind=="dependent" else ids[0]},"tail_binding":{"kind":"bone","id":ids[3] if kind=="dependent" else ids[1]}}
	var chains: Array=[{"ids":[ids[2],ids[3]],"colliders":[{"definition":collider}]},{"ids":[ids[4],ids[5]],"colliders":[{"definition":collider}]}]
	var pose: Dictionary={}
	if kind=="rotated":
		var q:=Quaternion(Vector3.FORWARD,.37);pose[ids[0]]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	return {"actor":actor,"mesh":mesh,"chains":chains,"pose":pose}
func compare(kind: String) -> void:
	var item:=fixture(kind);var before: Dictionary=item.actor.data.duplicate(true)
	var base: Dictionary=Baseline.create(item.actor,item.chains);var cached: Dictionary=Candidate.create(item.actor,item.chains)
	need(not base.has("error") and not cached.has("error"),kind+" actual weighted geometry admitted by both")
	if base.has("error") or cached.has("error"):item.actor.root.free();return
	if kind=="rotated":
		base.control.constrain(item.actor,item.chains,{})
		cached.control.constrain(item.actor,item.chains,{})
	var a: Dictionary=base.control.constrain(item.actor,item.chains,item.pose)
	var b: Dictionary=cached.control.constrain(item.actor,item.chains,item.pose)
	need(not a.has("error") and not b.has("error"),kind+" both solvers return without error")
	if a.has("error") or b.has("error"):base.control.dispose();cached.control.dispose();item.actor.root.free();return
	need(a.pose==b.pose and var_to_bytes(a.pose)==var_to_bytes(b.pose),kind+" exact original local-pose dictionary preserved")
	var same:=true
	for key in ["corrections","blocked_points","remaining_pairs","minimum_gap","iteration_limit_hits"]:
		if a.stats[key]!=b.stats[key]:same=false
	need(same,kind+" exact correction residual and blocked metrics preserved")
	var branch: String="cache_fallback_calls" if kind=="dependent" else "cache_eligible_calls"
	need(b.stats.get(branch,0)==(2 if kind=="rotated" else 1),kind+" conservative collider ancestry chooses expected path on each new call")
	var debug: Dictionary=Candidate.create(item.actor,item.chains);debug.control.verify_row_cache=true
	var verified: Dictionary=debug.control.constrain(item.actor,item.chains,item.pose)
	var exercised: bool=a.stats.blocked_points>0 if kind=="blocked" else (a.stats.corrections>0 if kind in ["static","tie"] else true)
	need(not verified.has("error") and verified.pose==a.pose and var_to_bytes(verified.pose)==var_to_bytes(a.pose) and item.actor.data==before and exercised,kind+" every cached scan matches original authority without authored writes")
	if kind=="clear":
		need(b.stats.get("cached_scans",0)==0 and b.stats.get("cached_rows_evaluated",0)==0,"clear performs no cached or summary row scans")
		need(b.stats.get("authoritative_scans",0)==1 and b.stats.get("capsule_builds",0)==1,"clear performs exactly one original authoritative scan")
		need(b.stats.get("cache_initializations",0)==0 and a.stats.corrections==0 and b.stats.remaining_pairs==0,"clear allocates no row cache and changes no pose")
	cases.append({"name":kind,"baseline_corrections":a.stats.corrections,"baseline_remaining_pairs":a.stats.remaining_pairs,"candidate_counters":b.stats.duplicate(true)})
	if kind=="static":
		item.mesh.set_blend_shape_value(0,.5)
		need(base.control.constrain(item.actor,item.chains,item.pose).has("error") and cached.control.constrain(item.actor,item.chains,item.pose).has("error"),"stale actual shape still refuses both solvers")
	if kind=="cross":
		item.mesh.mesh.emit_changed()
		need(base.control.constrain(item.actor,item.chains,item.pose).has("error") and cached.control.constrain(item.actor,item.chains,item.pose).has("error"),"changed geometry resource still refuses both solvers")
	base.control.dispose();cached.control.dispose();debug.control.dispose();item.actor.root.free()
func run() -> void:
	for kind in ["static","rotated","cross","blocked","tie","dependent","clear"]:compare(kind)
	print("SECONDARY_CONTACT_CACHE_UNIT "+JSON.stringify({"checks":checks,"failures":failures,"synthetic_only":true,"graphics_used":false,"private_assets_read":false,"user_profile":ProjectSettings.globalize_path("user://"),"cases":cases}))
	quit(1 if failures else 0)
