extends "res://tests/helper_preview_gpu.gd"
# Separate graphical case: real independent prop physics and a separately
# owned, posed/skinned child model. This file does not replace any product code.
const Prop=preload("res://src/physics_prop.gd")

func exact_child(child: RefCounted,before: Dictionary) -> bool:
	return is_instance_valid(child.root) and child.data==before.data and source_pose(child)==before.pose and Model.Shape.snapshot(child.root)==before.shapes and child.root.global_transform==before.transform and child.root.visible==before.root_visible and before.meshes.keys().all(func(mesh):return is_instance_valid(mesh) and mesh.visible==before.meshes[mesh] and mesh.is_visible_in_tree())

func peer_case() -> void:
	var source: RefCounted=await prepare_case("peer-and-child")
	if source==null:return
	var source_id: String=source.data.id
	# Reuse the already-owned skinned source as another ordinary model. Its
	# source-node tags intentionally overlap, while instance ownership differs.
	var child_data:=Model.definition(source.data.source);child_data.name="Separate posed child";child_data.position=[1.15,.35,0.];child_data.scale=.3
	var error: String=app.append_object(child_data,"model")
	check(error.is_empty(),"ordinary Add creates a separate skinned child candidate")
	if not error.is_empty():return
	var child_id: String=child_data.id
	var box:=folder.path_join("independent-peer-box.glb")
	check(box_asset(box)==OK,"create the owned solid peer fixture")
	var peer_data:=Model.definition(box);peer_data.name="Independent moving prop";peer_data.position=[40.,8.,40.]
	error=app.append_object(peer_data,"model")
	check(error.is_empty(),"ordinary Add creates an independent solid prop far outside the camera")
	if not error.is_empty():return
	var peer_id: String=peer_data.id
	# Every Add reconstructs the world; never retain obsolete Model/root objects.
	source=app.renderer.world_runtime.instance(source_id)
	var child: RefCounted=app.renderer.world_runtime.instance(child_id)
	var peer: RefCounted=app.renderer.world_runtime.instance(peer_id)
	check(source!=null and child!=null and peer!=null and source!=child and peer!=child,"all three instances are reacquired after ordinary world rebuilds")
	if source==null or child==null or peer==null:return
	var head: String=child.root.get_meta("has_source_bones",{}).get(2,"")
	check(not head.is_empty(),"child has its own actual source-node Head binding")
	if head.is_empty():return
	var q:=Quaternion(Vector3.RIGHT,-.31);child.data.pose={head:{"position":[.015,.02,0.],"rotation_xyzw":[q.x,q.y,q.z,q.w]}};child.data.draft_frame=12
	child.data.metadata.source_shape={"format":"studio_source_shape_2","enabled":false,"overrides":{"3":{"0":.25}}}
	# Author a parent relation in a valid world fixture, then install through the
	# normal prepared-world reader. The child stays a distinct registered actor.
	var world: Dictionary=app.current_world().duplicate(true)
	for row in world.objects:
		if row.id==child_id:row.parent_id=source_id
	error=app.restore_world(world)
	check(error.is_empty(),"normal world installation retains an explicitly parented child actor")
	if not error.is_empty():return
	source=app.renderer.world_runtime.instance(source_id);child=app.renderer.world_runtime.instance(child_id);peer=app.renderer.world_runtime.instance(peer_id)
	check(child.root.get_parent()==source.root and child.data.parent_id==source_id,"separate registered child root is actually attached under the source root")
	app.world_selection.select_entity(source_id,false);app.mode.select(2);app.change_mode(2);app.pose_editor.apply_frame();app.changed();await settled()
	head=child.root.get_meta("has_source_bones",{}).get(2,"")
	check(not head.is_empty() and child.bones.has(head),"reinstalled child retains exact source-node2 bone correspondence")
	if head.is_empty() or not child.bones.has(head):return
	var info: Dictionary=child.bones[head];var expected:=Transform3D(Basis(info.base.basis.get_rotation_quaternion()*q).scaled(info.base.basis.get_scale()),info.base.origin+Vector3(.015,.02,0.))
	var actual: Transform3D=info.skeleton.get_bone_pose(info.index)
	var child_shapes: Dictionary=Model.Shape.snapshot(child.root)
	check(actual.is_equal_approx(expected) and not actual.is_equal_approx(info.base),"child's actual Head local pose equals imported base times authored nonzero rotation plus translation")
	check(child_shapes.get("3",[]).size()>0 and child_shapes["3"][0]==.25,"child's actual effective morph is the nonzero authored quarter strength")
	app.physics_editor.enable_body(peer);await settled()
	check(app.physics_editor.active(peer_id) and app.physics_editor.simulations[peer_id] is Prop and not app.physics_editor.active(source_id) and not app.physics_editor.active(child_id),"only the real independent prop solver runs; target and child stay idle")
	if not app.physics_editor.active(peer_id) or not app.physics_editor.simulations[peer_id] is Prop:return
	var prop: RefCounted=app.physics_editor.simulations[peer_id];var body: RigidBody3D=prop.body;var body_id:=body.get_instance_id();var body_map: Dictionary=prop.bodies
	body.linear_velocity=Vector3(.7,.2,0.)
	var source_root: Node3D=source.root;var child_root: Node3D=child.root;var peer_root: Node3D=peer.root
	var peer_authored: Dictionary=peer.data.duplicate(true);var before:=document_state();var original_pose:=source_pose(source)
	var source_meshes: Dictionary={};var child_meshes: Dictionary={}
	for mesh in owned_source_meshes(source):source_meshes[mesh]=mesh.visible
	for mesh in owned_source_meshes(child):child_meshes[mesh]=mesh.visible
	check(not source_meshes.is_empty() and not child_meshes.is_empty() and child_meshes.keys().all(func(mesh):return not source_meshes.has(mesh)),"independent inventory separates source meshes from its registered child's meshes")
	var child_before: Dictionary={"data":child.data.duplicate(true),"pose":source_pose(child),"shapes":Model.Shape.snapshot(child.root),"transform":child.root.global_transform,"root_visible":child.root.visible,"meshes":child_meshes}
	var original: Image=await native_image(false)
	var peer_start:=body.global_position
	if not await open_pending() or not await start_pending():return
	check(app.physics_editor.simulations.get(peer_id)==prop and prop.body==body and body.get_instance_id()==body_id and is_same(prop.bodies,body_map) and prop.bodies.get("@root")==body and prop.running and not body.freeze,"preparation and visible wind retain the exact peer solver, body dictionary and running state")
	check(app.renderer.world_runtime.instance(source_id).root==source_root and app.renderer.world_runtime.instance(child_id).root==child_root and app.renderer.world_runtime.instance(peer_id).root==peer_root,"preparation retains all original source, child and peer root identities")
	check(mesh_id_set(host.player.hidden.keys())==mesh_id_set(source_meshes.keys()) and host.player.hidden.keys().all(func(mesh):return not mesh.visible),"pending wind hides exactly the source-owned meshes, excluding the separate child")
	check(source.root.visible and exact_child(child,child_before),"separate child remains visible with exact authored pose, effective morph, transform and data during wind")
	check(host.player.simulation.primary==null and not app.physics_editor.simulations.has(host.candidate.data.id),"derived wind solver borrows neither peer body nor authored physics registry")
	check(document_matches(before) and source_pose(source)==original_pose and peer.data==peer_authored,"preview preserves authored snapshot, original target pose and peer authoring exactly")
	for i in 60:await physics_frame
	await settled()
	var moved:=body.global_position.distance_to(peer_start);metrics["peer_movement_during_prepare_and_wind"]=moved
	check(moved>.0001 and prop.running and not body.freeze,"actual independent prop moves throughout pending setup and running wind")
	check(host.phase=="running" and exact_child(child,child_before) and source_pose(source)==original_pose and document_matches(before),"continued wind preserves child/source state while unrelated real physics advances")
	root.get_texture().get_image().save_png(folder.path_join("pending-helper-peer-child-main.png"))
	var candidate_ref: WeakRef=weakref(host.candidate.root);var space_ref: WeakRef=weakref(host.player.private_space)
	helper.try_wind.button_pressed=false;await settled()
	assert_restored(before,original_pose,source,source_meshes,"peer-and-child master Off")
	check(exact_child(child,child_before) and child.root.get_parent()==source.root,"Stop restores source visibility without touching the visible child or its parent relation")
	check(candidate_ref.get_ref()==null and space_ref.get_ref()==null,"Stop reclaims the exact derived candidate and private wind world")
	check(app.physics_editor.simulations.get(peer_id)==prop and prop.body==body and is_same(prop.bodies,body_map) and prop.bodies.get("@root")==body and prop.running and not body.freeze,"Stop leaves the identical peer body solver alive and running")
	check(changed_bytes(original,await native_image(false))==0,"Stop restores exact source-and-child native pixels while the off-camera peer keeps moving")
	var continued:=body.global_position
	for i in 12:await physics_frame
	check(body.global_position.distance_to(continued)>.00001 and prop.running and not body.freeze,"the same real peer body continues moving after Stop")
	check(document_matches(before) and exact_child(child,child_before) and peer.data==peer_authored,"post-Stop physics leaves all authored snapshot and child pose/morph state exact")
	# Applying would restore the complete world, so active peers must still cause
	# the conservative refusal rather than silently freezing or replacing them.
	helper.apply()
	check(helper.pid<=0 and is_instance_valid(helper.window) and document_matches(before) and app.physics_editor.simulations.get(peer_id)==prop,"Apply refuses a live peer before build, preserving history and exact original solver")
	helper.install({})
	check(document_matches(before) and exact_child(child,child_before) and app.physics_editor.simulations.get(peer_id)==prop,"late install refuses live peer before accessing a candidate or replacing the world")
	helper.close();await settled()
	check(app.physics_editor.simulations.get(peer_id)==prop and prop.running and not body.freeze,"closing loose-part review still leaves unrelated real physics running")
	check(app.renderer.native_readbacks==0,"peer-and-child captures release all native readback scopes")
	app.free();app=null;helper=null;host=null;await settled(8)
	check(root.get_child_count()==0,"application teardown releases original actors, independent body and all preview roots")

func run() -> void:
	setup_request()
	await peer_case()
	await finish("PENDING_HELPER_PEERS_GPU",{"prototype_only":true,"native_fidelity":false,"new_movies":false,"peer_child_case":true})
