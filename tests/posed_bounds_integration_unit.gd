extends SceneTree
const Model=preload("res://src/model.gd")
const Fixture=preload("res://tests/posed_bounds_fixture.gd")
const Physics=preload("res://src/physics_rig.gd")
var checks:=0
var failures:=0
func check(value: bool,text: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+text)
	if not value:failures+=1
func _initialize() -> void:call_deferred("run")
func actor(resource: ArrayMesh=null) -> RefCounted:
	var value:=Model.new();value.root=Fixture.scene(resource);value.data=Model.definition("res://examples/room.glb");value.inventory(value.root);return value
func run() -> void:
	var a: RefCounted=actor();var mesh: MeshInstance3D=a.root.get_node("Panel")
	var b: RefCounted=actor(mesh.mesh);var other: MeshInstance3D=b.root.get_node("Panel")
	check(not a.render_bounds_diagnostics().active and mesh.extra_cull_margin==0.,"detached model inventory does not publish bounds")
	root.add_child(a.root);root.add_child(b.root)
	var id: String=a.order[0];a.data.pose={id:{"position":[5,0,0],"rotation_xyzw":[0,0,0,1]}}
	var authored: PackedByteArray=var_to_bytes(a.data);a.apply(0,true)
	check(a.render_bounds_diagnostics().active and mesh.extra_cull_margin>4.9,"ordinary Model.apply activates and derives authored-pose bounds")
	b.apply(0,true)
	check(mesh.mesh==other.mesh and other.extra_cull_margin<.001,"shared mesh peer retains its own rest margin")
	var warm: Dictionary=a.render_bounds_diagnostics();var margin: float=mesh.extra_cull_margin
	for i in range(50):a.apply(0,true)
	var steady: Dictionary=a.render_bounds_diagnostics()
	var thumbnail: Node3D=a.root.duplicate();root.add_child(thumbnail);root.remove_child(thumbnail);thumbnail.free()
	check(a.render_bounds_diagnostics().active and mesh.extra_cull_margin==margin,"duplicated thumbnail teardown cannot dispose attached original cache")
	check(steady.builds==1 and steady.stats.inventory_array_reads==warm.stats.inventory_array_reads and steady.stats.hot_array_reads==0,"warm ordinary applies never rescan arrays or vertices")
	check(steady.stats.margin_writes==warm.stats.margin_writes and steady.stats.cache_hits>=50,"warm applies reuse envelope without property writes")
	a.root.transform=Transform3D(Basis(Vector3.UP,.4).scaled(Vector3.ONE*2),Vector3(7,3,-2));a.refresh_render_bounds()
	check(mesh.extra_cull_margin==margin,"uniform parent/root motion does not inflate local padding")
	a.live_pose={id:{"position":[-3,0,0],"rotation_xyzw":[0,0,0,1]}};a.apply_current(0,true)
	check(mesh.extra_cull_margin>2.9 and mesh.extra_cull_margin<3.1,"ordinary live-pose application updates current envelope")
	a.apply(0,true,true)
	check(mesh.extra_cull_margin==margin,"final authored evaluation excludes live draft pose")
	check(var_to_bytes(a.data)==authored,"cache creation refresh and final sampling never author model data")
	var sk: Skeleton3D=a.root.get_node("Rig");var simulator:=PhysicalBoneSimulator3D.new();sk.add_child(simulator)
	var physics:=Physics.new();physics.rig=a;physics.skeleton=sk;physics.simulator=simulator;physics.initial_pose=a.data.pose.duplicate(true);physics.running=true
	sk.set_bone_global_pose_override(0,Transform3D(Basis.IDENTITY,Vector3(7,0,0)),1.,true);sk.force_update_all_bone_transforms();physics.capture()
	check(not Model.RenderBounds.Bounds.final_pose(sk).is_empty() and mesh.extra_cull_margin>6.9,"actual PhysicsRig publication refreshes final modifier palette bounds")
	physics.stop();sk.set_bone_global_pose_override(0,Transform3D.IDENTITY,0.,false);a.apply(0,true)
	check(Model.RenderBounds.Bounds.final_pose(sk).is_empty() and mesh.extra_cull_margin==margin,"physics release returns to ordinary authored bound")
	physics.dispose()
	root.remove_child(a.root)
	check(not a.render_bounds_diagnostics().active and mesh.extra_cull_margin==0.,"root detach disposes cache and restores owned margin")
	root.add_child(a.root);a.apply(0,true)
	check(a.render_bounds_diagnostics().active and a.render_bounds_diagnostics().builds==2,"reattached model rebuilds once on ordinary application")
	mesh.extra_cull_margin=99.;a.apply(0,true)
	check(a.render_bounds_diagnostics().blocked and mesh.extra_cull_margin==99.,"external margin owner wins and disables this cache")
	var builds: int=a.render_bounds_diagnostics().builds;a.apply(0,true)
	check(a.render_bounds_diagnostics().builds==builds and other.extra_cull_margin<.001,"refused cache does not rebuild every frame or disturb peer")
	a.root.free();b.root.free()
	check(not a.render_bounds_diagnostics().active and not b.render_bounds_diagnostics().active,"freed model roots release cached resource signal connections")
	if checks!=17:push_error("Expected17 integration controls");quit(2);return
	print("POSED_BOUNDS_INTEGRATION "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"synthetic_only":true,"native_or_graphics_qualified":false}));quit(0 if failures==0 else 1)
