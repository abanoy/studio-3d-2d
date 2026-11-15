extends "res://tests/wind_review_gpu_common.gd"
const Rig=preload("res://src/physics_rig.gd")
const Prop=preload("res://src/physics_prop.gd")

func body_identities(simulation: RefCounted) -> Dictionary:
	var result: Dictionary={}
	for id in simulation.bodies:result[id]=simulation.bodies[id].get_instance_id()
	return result

func body_positions(simulation: RefCounted) -> Dictionary:
	var result: Dictionary={}
	for id in simulation.bodies:result[id]=simulation.bodies[id].global_position
	return result

func movement(before: Dictionary,simulation: RefCounted) -> float:
	var maximum:=0.
	for id in before:maximum=maxf(maximum,before[id].distance_to(simulation.bodies[id].global_position))
	return maximum

func run() -> void:
	setup_request()
	for running in [false,true]:
		await fresh_app("body-"+str(running));app.load_demo_room();await settled()
		var source: RefCounted=await add_source(source_path())
		if source==null:await finish("WIND_REVIEW_GPU_PRIMARY");return
		var source_id: String=source.data.id;var box:=folder.path_join("peer-box.glb")
		if not FileAccess.file_exists(box):check(box_asset(box)==OK,"create an owned solid peer")
		var data:=Model.definition(box);data.position=[1.2,3.8,0]
		check(app.append_object(data,"model").is_empty(),"ordinary world adoption installs an independent peer prop")
		var peer: RefCounted=app.renderer.active_model();var peer_id: String=peer.data.id
		source=app.renderer.world_runtime.instance(source_id)
		await add_media();app.world_selection.select_entity(source_id,false);app.mode.select(2);app.change_mode(2)
		app.physics_editor.toggle.button_pressed=true;await settled()
		app.world_selection.select_entity(peer_id,false);app.physics_editor.toggle.button_pressed=true;await settled()
		check(app.physics_editor.active(source_id) and app.physics_editor.simulations[source_id] is Rig and app.physics_editor.active(peer_id) and app.physics_editor.simulations[peer_id] is Prop,"actual native ragdoll and independent prop physics are both running")
		if not app.physics_editor.active(source_id) or not app.physics_editor.active(peer_id):await finish("WIND_REVIEW_GPU_PRIMARY");return
		var primary: RefCounted=app.physics_editor.simulations[source_id];var prop: RefCounted=app.physics_editor.simulations[peer_id]
		var primary_ids:=body_identities(primary);var prop_node: RigidBody3D=prop.body;var prop_instance:=prop_node.get_instance_id()
		# Explicit test impulses exercise genuine ongoing engine physics.
		for body in primary.bodies.values():body.linear_velocity+=Vector3(.2,0,0)
		prop_node.linear_velocity=Vector3(.7,0,0)
		app.world_selection.select_entity(source_id,false)
		var before:=document_state();var original_root: Node3D=source.root;var original_peer_root: Node3D=peer.root
		if not await open_review() or not await begin_review(running):await finish("WIND_REVIEW_GPU_PRIMARY");return
		var review=app.local_wind_review;var start:=body_positions(primary);var peer_start:=prop_node.global_position
		check(app.physics_editor.simulations[source_id]==primary and app.physics_editor.simulations[peer_id]==prop and body_identities(primary)==primary_ids and prop.body.get_instance_id()==prop_instance,"starting the try-out preserves original body and peer simulator identities")
		for i in range(40):await physics_frame
		await settled()
		check(movement(start,primary)>.0001 and prop_node.global_position.distance_to(peer_start)>.0001,"real primary and peer motion continue while the local try-out is open")
		check(review.phase=="running" and review.simulation.primary==null and review.candidate.root.global_transform.is_equal_approx(source.root.global_transform),"candidate follows the current source placement without borrowing its primary solver")
		var alignment:=0.
		for id in primary.bodies:alignment=maxf(alignment,review.candidate.bone_transform(id).origin.distance_to(source.bone_transform(id).origin))
		check(alignment<.002,"candidate's body follows the actual current primary pose within native transform precision")
		check(document_matches(before) and app.renderer.world_runtime.instance(source_id).root==original_root and app.renderer.world_runtime.instance(peer_id).root==original_peer_root,"ongoing preview preserves authored content, media, roots and history")
		review.window.close_requested.emit();await settled()
		check(app.physics_editor.simulations[source_id]==primary and app.physics_editor.simulations[peer_id]==prop and body_identities(primary)==primary_ids and prop.body==prop_node,"closing only the try-out leaves both real simulations alive and identical")
		check(primary.running and prop.running and not prop_node.freeze,"both original simulations retain their running state after close")
		# Give each existing real body a known motion after the close observation.
		# This does not restart a simulator or unfreeze a body; it prevents a
		# legitimately settled fixture from vacuously testing only its moving peer.
		for body in primary.bodies.values():body.linear_velocity+=Vector3(.2,.6,0)
		prop_node.linear_velocity+=Vector3(.7,.6,0)
		var continued:=body_positions(primary);var peer_continued:=prop_node.global_position
		for i in range(8):await physics_frame
		check(movement(continued,primary)>.00001 or prop_node.global_position.distance_to(peer_continued)>.00001,"normal motion continues after the owned candidate is gone")
		check(movement(continued,primary)>.00001,"the original primary itself moves after the owned candidate is gone")
		check(prop_node.global_position.distance_to(peer_continued)>.00001,"the independent original prop itself moves after the owned candidate is gone")
		if not await open_review() or not await begin_review(running):await finish("WIND_REVIEW_GPU_PRIMARY");return
		var temporary: WeakRef=weakref(review.candidate.root);var record=app.physics_editor.recording;record.scope.select(0 if running else 1)
		check(record.start() and record.active,"real Local/World Record starts from existing physics after cancelling the try-out")
		var expected: Array=[source_id] if running else [source_id,peer_id];var actual: Array=record.targets.keys();expected.sort();actual.sort()
		check(actual==expected and not app.local_wind_active() and (temporary.get_ref()==null or not temporary.get_ref().visible),"Record targets only actual original simulations and never the disposable candidate")
		record.cancel("Discard owned test recording",false)
		check(document_matches(before,false),"discarding the explicit test take leaves original authored content and media intact")
		metrics["running" if running else "warming"]={"native_body_count":primary_ids.size(),"candidate_body_alignment":alignment,"record_scope":"local" if running else "world","record_target_count":expected.size()}
		app.free();app=null;await settled()
	await finish("WIND_REVIEW_GPU_PRIMARY")
