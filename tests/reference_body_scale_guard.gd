extends SceneTree
# Real Model/Skeleton coverage of the reference-size body physics boundary.
const Model=preload("res://src/model.gd")
const B=preload("res://src/import_basis.gd")
const IK=preload("res://src/limb_ik.gd")
const Rig=preload("res://src/physics_rig.gd")
const SHA="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
const MESSAGE="Body Physics cannot safely prepare this reference size. Posing and Hair & clothes are still available."
var checks:=0
var failures:=0

func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1

func _initialize() -> void:
	create_timer(30).timeout.connect(func():push_error("Reference body guard watchdog expired");quit(2))
	call_deferred("run")

func actor(height: String,reference:=true,artist_scale:=1.0,parent_scale:=1.0) -> RefCounted:
	var subject:=Model.new()
	subject.data={"format":"studio_model_1","id":"guard_fixture","name":"Authored arm","kind":"model","parent_id":"","start_frame":0,"source":"res://synthetic-not-read.glb","sha256":SHA,"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":artist_scale,"visible":true,"reference_only":false,"pose":{},"pose_keys":[],"draft_frame":0,"metadata":{}}
	if reference:subject.data["asset_basis"]=B.create_record(SHA,height).record
	subject.root=Node3D.new();subject.root.name="AuthoredArm"
	var sk:=Skeleton3D.new();sk.name="Rig";subject.root.add_child(sk)
	# The complete arm names/rests are from tests/limb_fixture.gd. No files or
	# importer mocks: the real Model inventories a real three-bone Skeleton3D.
	var names: Array=["upper_arm.L","forearm.L","hand.L"]
	var rest: Array=[Vector3(0,1,0),Vector3(0.8,0.15,0),Vector3(0.8,-0.15,0)]
	for i in range(3):
		sk.add_bone(names[i]);sk.set_bone_rest(i,Transform3D(Basis.IDENTITY,rest[i]))
		if i>0:sk.set_bone_parent(i,i-1)
	sk.reset_bone_poses()
	check(subject.capture_import_root(Transform3D.IDENTITY).is_empty(),"real constructor captures reference before inventory")
	subject.inventory(subject.root)
	var parent:=Node3D.new();parent.scale=Vector3.ONE*parent_scale;root.add_child(parent);parent.add_child(subject.root)
	subject.apply(0,false,true)
	check(subject.order.size()==3 and IK.chain(subject,subject.order[2]).get("ids",[]).size()==3,"fixture reaches complete structural ragdoll chain")
	return subject

func snapshot(subject: RefCounted) -> Dictionary:
	var topology: Array=[];var pending: Array=[subject.root]
	while not pending.is_empty():
		var node: Node=pending.pop_back();topology.append(node.get_instance_id());pending.append_array(node.get_children(true))
	var poses: Array=[]
	for id in subject.order:
		var info: Dictionary=subject.bones[id];poses.append(info.skeleton.get_bone_pose(info.index))
	return {"data":var_to_bytes(subject.data),"live_pose":var_to_bytes(subject.live_pose),"live_world":subject.live_world_transform,"root":subject.root.transform,"raw":subject.raw_import_root,"base":subject.base_root,"order":subject.order.duplicate(),"poses":poses,"topology":topology,"secondary":subject.root.get_meta("has_secondary_rig",{}).duplicate(true)}

func dispose_actor(subject: RefCounted) -> void:
	var parent: Node=subject.root.get_parent();parent.free()

func refused(height: String,factor: float,artist_scale:=1.0,parent_scale:=1.0) -> void:
	var subject:=actor(height,true,artist_scale,parent_scale)
	check(is_equal_approx(B.factor(subject.data),factor),"fixture has requested intrinsic factor "+str(factor))
	var retained_pose: Dictionary={subject.order[0]:Model.identity()}
	subject.live_pose=retained_pose.duplicate(true);subject.live_world_transform=subject.root.global_transform
	subject.root.set_meta("has_secondary_rig",{"format":"studio_secondary_rig_1","chains":[],"colliders":[],"error":""})
	var before:=snapshot(subject);var result: Dictionary=Rig.create(subject)
	check(result.get("error","")==MESSAGE and not result.has("physics"),"unsafe active reference refuses body physics clearly: "+str([factor,artist_scale,parent_scale]))
	check(snapshot(subject)==before,"refusal allocates no simulation/body nodes and preserves data, authored/live pose, roots and secondary metadata")
	dispose_actor(subject)

func admitted(height: String,reference: bool,artist_scale:=1.0,parent_scale:=1.0) -> void:
	var subject:=actor(height,reference,artist_scale,parent_scale)
	var before: Dictionary=subject.data.duplicate(true);var result: Dictionary=Rig.create(subject)
	check(not result.has("error") and result.has("physics"),"existing unit or legacy allocation path admits: "+str([height,reference,artist_scale,parent_scale]))
	if result.has("physics"):
		var simulation: RefCounted=result.physics
		check(simulation.bodies.size()==3 and simulation.simulator.get_parent()==subject.bones[subject.order[0]].skeleton,"admission builds the real existing three-body ragdoll under its skeleton")
		check(subject.data==before and subject.live_pose==null and subject.live_world_transform==null,"allocation retains authored model and inactive live state")
		simulation.dispose()
	dispose_actor(subject)

func prior_error_categories() -> void:
	var subject:=actor("1.8288")
	var sk: Skeleton3D=subject.bones[subject.order[0]].skeleton
	sk.scale=Vector3(1,2,1)
	var before:=snapshot(subject);var result: Dictionary=Rig.create(subject)
	check(result.get("error","")=="Ragdoll physics needs a positive uniformly scaled skeleton." and snapshot(subject)==before,"pre-existing nonuniform-skeleton category stays atomic")
	dispose_actor(subject)
	subject=actor("1.8288");sk=subject.bones[subject.order[0]].skeleton
	sk.set_bone_pose_position(1,Vector3.ZERO);sk.force_update_all_bone_transforms()
	before=snapshot(subject);result=Rig.create(subject)
	check(result.get("error","")=="A ragdoll limb has a zero-length segment. Use direct posing for this rig." and snapshot(subject)==before,"pre-existing zero-length category stays atomic")
	dispose_actor(subject)

func run() -> void:
	refused("1828.8",0.001,0.5)
	refused("0.0009144",2000.0)
	# Admission follows the complete world frame, including artist/static parent.
	refused("1.8288",1.0,2000.0)
	refused("1.8288",1.0,1.0,0.0005)
	admitted("3.6576",true)
	admitted("0.9144",true)
	admitted("1.8288",true,2.0)
	admitted("1.8288",true,1.0,0.5)
	admitted("1.8288",true)
	# Admission follows actual world size, so exact compensating factors work.
	admitted("3.6576",true,2.0)
	admitted("0.9144",true,1.0,0.5)
	# The interim boundary deliberately leaves old nonunit models unchanged.
	admitted("1.8288",false,0.5)
	admitted("1.8288",false,2.0)
	prior_error_categories()
	print("REFERENCE_BODY_SCALE_GUARD "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)
