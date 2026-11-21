extends SceneTree
const Model=preload("res://src/model.gd")
const Fit=preload("res://src/secondary_body_colliders.gd")
const Spring=preload("res://src/secondary_spring.gd")
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var scene:=Node3D.new();root.add_child(scene)
	var sk:=Skeleton3D.new();sk.name="Rig";scene.add_child(sk)
	var names: Array=["Body","upper_arm.L","forearm.L","hand.L","HairA","HairEnd"]
	var parents: Array=[-1,0,1,2,0,4]
	var rest: Array=[Vector3.ZERO,Vector3(0,2,0),Vector3(.5,0,0),Vector3(.5,0,0),Vector3(0,3,.3),Vector3(0,-1,0)]
	for i in range(names.size()):
		sk.add_bone(names[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,rest[i]))
		if parents[i]>=0:sk.set_bone_parent(i,parents[i])
	sk.reset_bone_poses()
	var vertices:=PackedVector3Array();var bones:=PackedInt32Array();var weights:=PackedFloat32Array()
	for i in range(4103):
		var bone:=4;var point:=Vector3(0,2.7,.3)
		if i<6:
			bone=1 if i<3 else 2;point=Vector3(.25 if i<3 else .75,2,0)+[Vector3(0,0,.03),Vector3(0,0,-.03),Vector3(0,.03,0)][i%3]
		vertices.append(point)
		for slot in range(4):bones.append(bone if slot==0 else 0);weights.append(1. if slot==0 else 0.)
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_BONES]=bones;arrays[Mesh.ARRAY_WEIGHTS]=weights
	var geometry:=ArrayMesh.new();geometry.add_surface_from_arrays(Mesh.PRIMITIVE_POINTS,arrays)
	var mesh:=MeshInstance3D.new();mesh.mesh=geometry;scene.add_child(mesh);mesh.skeleton=mesh.get_path_to(sk);mesh.skin=sk.create_skin_from_rest_transforms()
	var actor:=Model.new();actor.root=scene;actor.data={"metadata":{},"pose":{}};actor.inventory(scene)
	var joints: Array=[]
	for name in ["HairA","HairEnd"]:joints.append({"binding":{"kind":"bone","id":"Rig::"+name},"stiffness":1.,"drag":.4,"radius":.01,"gravity":.1,"gravity_direction":[0,-1,0]})
	var definition:={"source_family":"HAS","colliders":[],"chains":[{"joints":joints,"center":{},"end_extension":0.,"colliders":[]}]}
	scene.set_meta("has_secondary_rig",definition)
	check(Fit.build(actor).colliders.size()==2,"synthetic oversized hair retains two real fitted arm segments")
	mesh.position.x=.1;var unsupported: Dictionary=Fit.build(actor);mesh.position.x=0
	check(unsupported.colliders.is_empty() and "matching mesh and skeleton" in unsupported.reason,"nonidentity mesh-to-skeleton frame does not activate generated contact")
	var before: PackedByteArray=var_to_bytes(definition);var connections: int=geometry.get_signal_connection_list("changed").size()
	var made: Dictionary=Spring.construct(actor)
	check(not made.has("error"),"4097 affected vertices keep ordinary Hair and clothes available")
	if not made.has("error"):
		var runner: RefCounted=made.runner
		check(runner.skin_contact==null and not runner.contact_info.skin_surface_available and "4096" in runner.contact_info.skin_reason,"unsupported surface budget is explicit and never claims an active skin cache")
		check(geometry.get_signal_connection_list("changed").size()==connections,"failed optional cache leaves no resource callback attached")
		for i in range(4):await process_frame
		var result: Dictionary=runner.step(1./120.,Vector3.ZERO)
		check(not result.has("error") and not result.pose.is_empty(),"existing ordinary spring and segment path still produces a pose")
		var host: Node3D=runner.host;runner.dispose()
		check(not is_instance_valid(host) and var_to_bytes(scene.get_meta("has_secondary_rig"))==before and geometry.surface_get_array_len(0)==4103,"fallback disposal preserves source declaration and geometry")
	else:
		for label in ["surface fallback reason","callback cleanup","ordinary spring step","fallback disposal"]:check(false,label)
	var imported: Dictionary=definition.duplicate(true);imported.source_family="VRM1"
	imported.colliders=[{"shape":"sphere","binding":{"kind":"bone","id":"Rig::Body"},"offset":[0,0,0],"radius":.03}];imported.chains[0].colliders=[0]
	scene.set_meta("has_secondary_rig",imported)
	var legacy: Dictionary=Spring.construct(actor)
	check(not legacy.has("error") and legacy.runner.skin_contact==null and legacy.runner.contact_info.is_empty() and legacy.runner.chains[0].colliders.size()==1,"an existing imported collider keeps its original runner path without generated caches")
	if not legacy.has("error"):
		for i in range(4):await process_frame
		legacy.runner.dispose()
	scene.set_meta("has_secondary_rig",definition)
	actor.release_render_bounds();scene.free();await process_frame
	print("SECONDARY_BODY_CONTACT_BUDGET "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"synthetic_only":true}));quit(0 if failures==0 else 1)
