extends SceneTree
const Groups=preload("res://src/wind_review_groups.gd")
const Review=preload("res://src/wind_review.gd")
const Model=preload("res://src/model.gd")
const Spring=preload("res://src/secondary_spring.gd")
const Secondary=preload("res://src/secondary_live.gd")
const Airflow=preload("res://src/airflow.gd")
const SHA="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
class FakeBody extends RefCounted:
	var bodies: Dictionary={}
	var disposed:=false
	func dispose() -> void:disposed=true
class FakeEditor extends RefCounted:
	var simulations: Dictionary={}
	var recording: Dictionary={"active":false}
class FakeRenderer extends Node:
	var model: RefCounted
	var world_runtime: RefCounted
	var capturing_final:=false
	var before_final_capture:=Callable()
	var before_asset_replace:=Callable()
	func active_model() -> RefCounted:return model
class FakeRuntime extends RefCounted:
	var instances: Dictionary={}
	func instance(id: String) -> RefCounted:return instances.get(id)
class FakePose extends Node:
	var updates:=0
	func update_gizmo() -> void:updates+=1
class FakeCanvas extends Control:
	var review_pointer:=Callable()
	func scene_contains(point: Vector2) -> bool:return Rect2(0,0,1920,1080).has_point(point)
class FakeSelection extends Node:
	var cancelled:=0
	func cancel_gesture(_invalidate:=false) -> void:cancelled+=1
class FakeApp extends Node:
	var renderer:=FakeRenderer.new()
	var pose_editor:=FakePose.new()
	var world_selection:=FakeSelection.new()
	var canvas:=FakeCanvas.new()
	var physics_editor:=FakeEditor.new()
	var mode:=OptionButton.new()
	var frame:=4
	var recovery_revision:=7
	var playing:=false
	var exporting:=false
	func _ready() -> void:
		for node in [renderer,pose_editor,world_selection,canvas,mode]:add_child(node)
		mode.add_item("Draw");mode.add_item("Camera");mode.add_item("Pose");mode.select(2)
class Disposable extends RefCounted:
	var disposed:=0
	var primary: RefCounted
	func dispose() -> void:disposed+=1
var checks:=0
var failures:=0
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func joint(id: String,node: int) -> Dictionary:
	return {"binding":{"kind":"bone","id":id,"source_node":node},"source_node":node,"stiffness":.5,"drag":.4,"gravity":.01,"gravity_direction":[0,-1,0],"radius":.01}
func chain(name: String,ids: Array,extension: float) -> Dictionary:
	var joints: Array=[]
	for i in range(ids.size()):joints.append(joint(ids[i],i+1))
	return {"name":name,"joints":joints,"center":{},"colliders":[],"end_extension":extension}
func definition(chains: Array) -> Dictionary:
	return {"format":"studio_secondary_1","error":"","chains":chains,"colliders":[],"source_family":"VRM1"}
func fixture() -> RefCounted:
	var actor:=Model.new();actor.root=Node3D.new();root.add_child(actor.root)
	var skeleton:=Skeleton3D.new();skeleton.name="Skeleton";actor.root.add_child(skeleton)
	var names:=["Body","HairA","TipA","HairB","TipB"]
	for name in names:skeleton.add_bone(name)
	for i in range(1,names.size()):skeleton.set_bone_parent(i,0 if i in [1,3] else i-1)
	for i in range(names.size()):skeleton.set_bone_rest(i,Transform3D(Basis.IDENTITY,Vector3(.3 if i==3 else 0,1 if i==0 else .25,0)))
	skeleton.reset_bone_poses();actor.inventory(actor.root);actor.data=Model.definition("");actor.data.id="fixture"
	actor.data.pose={"Skeleton::HairA":pose(.2),"Skeleton::HairB":pose(-.3)}
	actor.data.pose_keys=[{"frame":0,"pose":actor.data.pose.duplicate(true),"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.}},{"frame":8,"pose":{"Skeleton::HairA":pose(.6),"Skeleton::HairB":pose(-.1)},"transform":{"position":[0,0,0],"rotation_xyzw":[0,0,0,1],"scale":1.}}]
	for key in actor.data.pose_keys:key["interpolation"]="linear"
	actor.data.draft_frame=-1
	actor.root.set_meta("has_secondary_rig",definition([chain("same",["Skeleton::HairA","Skeleton::TipA"],0),chain("same",["Skeleton::HairB"],.1)]))
	actor.apply(4)
	return actor
func pose(angle: float) -> Dictionary:
	var q:=Quaternion(Vector3.FORWARD,angle);return {"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
func weighted_mesh(actor: RefCounted) -> MeshInstance3D:
	var mesh:=MeshInstance3D.new();mesh.name="Weighted";actor.root.add_child(mesh)
	var skin:=Skin.new();skin.set_bind_count(2);skin.set_bind_name(0,"HairA");skin.set_bind_name(1,"HairB");skin.set_bind_bone(0,1);skin.set_bind_bone(1,3);mesh.skin=skin;mesh.skeleton=NodePath("../Skeleton")
	var arrays: Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP]);arrays[Mesh.ARRAY_BONES]=PackedInt32Array([0,1,0,0,0,0,0,0,1,0,0,0]);arrays[Mesh.ARRAY_WEIGHTS]=PackedFloat32Array([.5,.5,0,0,1,0,0,0,1,0,0,0])
	var resource:=ArrayMesh.new();resource.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);mesh.mesh=resource
	return mesh
func _initialize() -> void:run.call_deferred()
func run() -> void:
	var a:=chain("duplicate comment",["a","a_tip"],0);var b:=chain("duplicate comment",["b"],.1);var source:=definition([a,b]);var before:=JSON.stringify(source)
	var catalog:=Groups.build(source,SHA,{"a":"body","a_tip":"a","b":"body"})
	check(catalog.error.is_empty() and catalog.groups.size()==2,"same display comments remain two separately checked structural groups")
	check(Groups.rotating(a).size()==1 and Groups.rotating(b).size()==1,"real VRM1 endpoints and VRM0-style virtual tails retain their rotating-joint contract")
	var renamed:=a.duplicate(true);renamed.name="different"
	check(Groups.chain_id(a,SHA)==Groups.chain_id(renamed,SHA),"renaming a comment cannot silently change a session selection")
	var reordered:=Groups.build(definition([b,a]),SHA)
	check(catalog.groups[0].id==reordered.groups[1].id,"chain reorder preserves structural group identity")
	check(Groups.chain_id(a,SHA)!=Groups.chain_id(a,"f".repeat(64)),"another source cannot reuse an old group identity")
	var changed:=a.duplicate(true);changed.joints[0].binding.id="other"
	check(Groups.chain_id(a,SHA)!=Groups.chain_id(changed,SHA),"changing a real binding invalidates selection identity")
	changed=a.duplicate(true);changed.joints[0].stiffness+=.01
	check(Groups.chain_id(a,SHA)!=Groups.chain_id(changed,SHA),"changing solver settings invalidates selection identity")
	var filtered:=Groups.filter(catalog,[catalog.groups[1].id])
	check(filtered.chains==[b],"only the checked group enters the solver; unchecked gravity is excluded too")
	check(Groups.filter(catalog,[]).chains.is_empty(),"empty wind checks produce no solver chains")
	check(not Groups.filter(catalog,["missing"]).get("error","").is_empty(),"stale checked identities are rejected")
	check(not Groups.filter(catalog,[catalog.groups[0].id,catalog.groups[0].id]).get("error","").is_empty(),"duplicate checked identities are rejected")
	var tampered:=catalog.duplicate(true);tampered.definition.chains[0].joints[0].drag=.9
	check(not Groups.filter(tampered,[catalog.groups[0].id]).get("error","").is_empty(),"a reviewed definition cannot drift before filtering")
	check(JSON.stringify(source)==before,"catalogue and filter never rewrite the source chain declarations")
	var linked:=Groups.build(source,SHA,{},[[0,1]])
	check(linked.groups.size()==1 and linked.groups[0].linked and Groups.filter(linked,[linked.groups[0].id]).chains.size()==2,"shared weighted regions are explicitly inseparable during this try-out")
	var hierarchy:=Groups.build(source,SHA,{"b":"a","a":"body"})
	check(hierarchy.groups.size()==1,"a descendant chain cannot pretend its ancestor chain has no effect")
	check(not Groups.build(source,SHA,{},[[0,2]]).error.is_empty(),"out-of-range linked groups are rejected")
	check(not Groups.build(definition([a,a]),SHA).error.is_empty(),"repeated structural chains are rejected")
	var overlap:=b.duplicate(true);overlap.joints[0].binding.id="a"
	check(not Groups.build(definition([a,overlap]),SHA).error.is_empty(),"two chains cannot drive the same rotating bone")
	check(Groups.build(definition([]),SHA).groups.is_empty(),"a source with no declared chains remains an empty review")
	for malformed in [{},{"joints":{}},null,{"joints":[{}],"end_extension":0,"center":{},"colliders":[]}]:
		check(not Groups.build(definition([malformed]),SHA).error.is_empty(),"malformed source group is refused without guessing")
	check(not Groups.build(source,"z".repeat(64)).error.is_empty(),"malformed source digest cannot establish a checked identity")
	var actor:=fixture();var mesh:=weighted_mesh(actor);var descendants:=Groups.parents(actor)
	var weight_link:=Groups.vertex_links(actor,actor.root.get_meta("has_secondary_rig").chains,descendants)
	check(weight_link.error.is_empty() and weight_link.links==[[0,1]],"actual skin weights link chains sharing a vertex")
	var child_root:=Node3D.new();actor.root.add_child(child_root);var child_mesh:=MeshInstance3D.new();child_mesh.mesh=BoxMesh.new();child_root.add_child(child_mesh)
	check(Groups.mesh_nodes(actor.root,[child_root])==[mesh],"owned mesh traversal skips independently parented model roots")
	var snapshot: Dictionary=actor.data.duplicate(true);var app:=FakeApp.new();root.add_child(app);app.renderer.model=actor
	var review:=Review.new();review.app=app;app.add_child(review);review.catalog=Groups.build(actor.root.get_meta("has_secondary_rig"),SHA,descendants)
	var peer:=Model.new();peer.root=child_root;peer.data={"id":"independent-peer","pose":{"precise":"peer-state"}};var peer_snapshot: Dictionary=peer.data.duplicate(true)
	var runtime:=FakeRuntime.new();runtime.instances={actor.data.id:actor,peer.data.id:peer};app.renderer.world_runtime=runtime;review.target_id=actor.data.id
	check(review.actor()==actor and review.other_roots(actor)==[child_root],"source lookup and independent peer identities stay distinct in a parented world")
	var body:=FakeBody.new();body.bodies={"Skeleton::Body":true};app.physics_editor.simulations[actor.data.id]=body
	var skeleton: Skeleton3D=actor.root.get_node("Skeleton");skeleton.set_bone_pose_rotation(0,Quaternion(Vector3.UP,.7));skeleton.set_bone_pose_rotation(1,Quaternion(Vector3.RIGHT,.9));skeleton.set_bone_pose_rotation(3,Quaternion(Vector3.RIGHT,-.8))
	var baseline:=review.baseline_pose(actor);var authored: Dictionary=actor.sample(4,true)
	check(baseline["Skeleton::HairA"]==authored["Skeleton::HairA"] and baseline["Skeleton::HairB"]==authored["Skeleton::HairB"],"excluded hair keeps sampled recorded animation, not the original live hair offset")
	check(absf(Quaternion(baseline["Skeleton::Body"].rotation_xyzw[0],baseline["Skeleton::Body"].rotation_xyzw[1],baseline["Skeleton::Body"].rotation_xyzw[2],baseline["Skeleton::Body"].rotation_xyzw[3]).angle_to(Quaternion(Vector3.UP,.7)))<.00001,"a concurrently simulated body keeps its current actual local pose")
	check(actor.data==snapshot and not body.disposed,"reading the baseline preserves authored data and borrowed body lifetime")
	var live:=Secondary.new();live.primary=body;app.physics_editor.simulations[actor.data.id]=live
	check(review.body_ids(actor).has("Skeleton::Body"),"combined original body plus hair still exposes only the borrowed body bindings")
	live.primary=null;app.physics_editor.simulations[actor.data.id]=body
	var host:=SubViewport.new();host.own_world_3d=true;host.render_target_update_mode=SubViewport.UPDATE_DISABLED;root.add_child(host)
	var one:=Groups.filter(review.catalog,[review.catalog.groups[0].id]);var made:=Spring.construct(actor,one,host)
	check(not made.has("error") and made.runner.chains.size()==1 and made.runner.chains[0].ids==["Skeleton::HairA"],"synchronous construction builds exactly the checked real spring chain")
	check(host.find_world_3d().space!=actor.root.get_world_3d().space and made.runner.host.get_viewport()==host,"scratch spring nodes belong to a distinct private physics space")
	made.runner.dispose();host.free()
	var field:={"transform":Transform3D(Basis.IDENTITY,Vector3(0,-.85,-1.5)),"settings":Airflow.defaults()}
	check(Airflow.unsteady_force([field],Vector3.ZERO,.1).length()>0 and Airflow.unsteady_force([field],Vector3.ZERO,.1).distance_to(Airflow.unsteady_force([field],Vector3.ZERO,.2))>.0001,"preview uses the existing genuinely unsteady local airflow response")
	review.window=Window.new();app.add_child(review.window);review.window.visible=true
	review.parts=ItemList.new();review.wind_check=CheckButton.new();review.master=CheckButton.new();review.status=Label.new();review.detail=Label.new()
	for control in [review.parts,review.wind_check,review.master,review.status,review.detail]:review.window.add_child(control)
	for group in review.catalog.groups:review.parts.add_item(str(group.names[0]))
	review.focus_group(0)
	check(review.wind_ids.is_empty() and not review.wind_check.button_pressed,"focusing a row never silently checks it for wind")
	review.check_group(true);review.focus_group(1)
	check(review.wind_ids.size()==1 and review.wind_ids.has(review.catalog.groups[0].id) and not review.wind_check.button_pressed,"focus changes preserve the first group's check without including its neighbour")
	review.check_group(true);review.check_group(false)
	check(review.wind_ids.size()==1 and review.phase=="stopped" and actor.data==snapshot,"a per-group wind exclusion changes only session checks, with no persistent setup or scene edit")
	review.root_id=actor.root.get_instance_id();review.source_sha=actor.data.sha256;review.original_data=actor.data.duplicate(true);review.revision=app.recovery_revision;review.opened_frame=app.frame
	check(review.context_valid(),"an unchanged paused model establishes the review context")
	app.frame+=1;check(not review.context_valid(),"seeking invalidates a warming/running context before its next step");app.frame-=1
	actor.root.set_meta("has_secondary_rig",definition([]));check(not review.context_valid(),"source chain replacement invalidates the reviewed structural snapshot");actor.root.set_meta("has_secondary_rig",review.catalog.definition.duplicate(true))
	app.renderer.model=peer;check(not review.context_valid(),"switching to a peer invalidates the old source context");app.renderer.model=actor
	var candidate:=fixture();var candidate_root: Node3D=candidate.root
	var disposable:=Disposable.new();review.simulation=disposable;review.candidate=candidate
	var already_hidden:=MeshInstance3D.new();already_hidden.mesh=BoxMesh.new();actor.root.add_child(already_hidden);already_hidden.visible=false
	review.private_space=SubViewport.new();review.add_child(review.private_space);review.phase="warming";review.hidden={}
	for owned_mesh in Groups.mesh_nodes(actor.root,review.other_roots(actor)):review.hidden[owned_mesh]=owned_mesh.visible;owned_mesh.visible=false
	check(child_mesh.visible and not mesh.visible and not already_hidden.visible,"temporary hiding affects owned meshes only and leaves an independent child visible")
	var old_pointer:=func(_event,_point):return false
	app.canvas.review_pointer=Callable(review,"pointer");review.previous_pointer=old_pointer;review.pointer_pending=true
	review.schedule_warmup()
	check(RenderingServer.frame_post_draw.is_connected(review.warm_frame),"warm-up is an owned cancellable one-shot callback")
	review.stop_preview("Cancel")
	check(review.phase=="stopped" and review.simulation==null and disposable.disposed==1,"cancel synchronously destroys only the owned simulation")
	check(not candidate_root.visible and candidate_root.is_queued_for_deletion(),"cancel immediately hides the temporary model before deferred deletion")
	check(mesh.visible and child_mesh.visible and not already_hidden.visible and app.canvas.review_pointer==old_pointer,"cancel restores each owned visibility and the previous input owner")
	check(not RenderingServer.frame_post_draw.is_connected(review.warm_frame) and app.world_selection.cancelled==1,"cancel removes pending warm-up and pending selection gesture")
	review.stop_preview("Again")
	check(disposable.disposed==1 and not body.disposed and app.physics_editor.simulations[actor.data.id]==body and actor.data==snapshot,"repeated stop preserves another live simulation and all authored data")
	check(runtime.instances[peer.data.id]==peer and peer.root==child_root and peer.data==peer_snapshot and child_root.get_parent()==actor.root,"preview cleanup preserves independently parented peer identity, data, and attachment")
	check(app.renderer.before_final_capture.is_null() and app.renderer.before_asset_replace.is_null(),"an uninstalled review cannot replace renderer guards")
	review.free();app.free();actor.root.free()
	await process_frame
	check(not is_instance_valid(candidate_root),"cancelled temporary model is reclaimed on the next normal frame")
	print("WIND_REVIEW_UNIT "+JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures==0 else 1)
