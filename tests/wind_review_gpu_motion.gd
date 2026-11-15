extends "res://tests/wind_review_gpu_common.gd"
var source: RefCounted

func measure(speed: float,direction_index: int,ticks: int) -> Dictionary:
	var review=app.local_wind_review
	review.master.button_pressed=false;review.strength.value=speed;review.direction.select(direction_index);review.direction.item_selected.emit(direction_index)
	if not await begin_review():return {"error":"try-out did not run"}
	review.set_physics_process(false)
	var ids:=selected_ids();var excluded: Array=[]
	for group in review.catalog.groups:
		if not review.wind_ids.has(group.id):excluded.append_array(group.rotating_ids)
	# The expected excluded pose comes from the authored animation, independently
	# of WindReview.baseline_pose (which is itself under test).
	var authored: Dictionary=source.sample(app.frame,true);var expected_excluded: Dictionary={}
	for id in excluded:expected_excluded[id]=authored.get(id,Model.identity()).duplicate(true)
	if request.mode=="procedural":
		var recorded: Dictionary=expected_excluded.get(recorded_exclusion_binding,Model.identity())
		var expected_rotation:=Quaternion(Vector3.FORWARD,-.045)
		check(recorded_exclusion_binding in excluded and Timeline.quaternion(recorded.rotation_xyzw).angle_to(expected_rotation)<.00001 and Timeline.quaternion(recorded.rotation_xyzw).angle_to(Quaternion.IDENTITY)>.02,"the unchecked procedural skirt independently samples its known nonzero recorded half-way pose")
	var reference: Dictionary={};var prior: Dictionary={};var late_range:=0.;var maximum_step:=0.;var stable:=true;var samples: Array=[];var force_samples: Array=[];var sum_axis:=0.
	for tick in range(ticks):
		review._physics_process(1./120.)
		if review.phase!="running":return {"error":"try-out stopped during stepping"}
		var current: Dictionary=review.simulation.latest
		for id in excluded:stable=stable and current.has(id) and current[id]==expected_excluded[id]
		if not prior.is_empty():maximum_step=maxf(maximum_step,angle(prior,current,ids))
		prior=current.duplicate(true)
		var chain: Dictionary=review.simulation.runner.chains[0];var point:=Definition.binding_transform(review.candidate,chain.source.joints[0].binding).origin
		var force:=Airflow.unsteady_force([review.local_field()],point,review.simulation.age)
		sum_axis+=force.dot(app.renderer.camera.global_basis.x)
		if tick>=ticks-240:
			if reference.is_empty():reference=current.duplicate(true)
			late_range=maxf(late_range,angle(reference,current,ids))
			if tick%4==0:samples.append(current.duplicate(true));force_samples.append(force)
	var turns:=0
	for id in ids:
		for axis in range(3):
			var sign_before:=0;var count:=0
			for i in range(1,samples.size()):
				var delta: float=samples[i].get(id,Model.identity()).rotation_xyzw[axis]-samples[i-1].get(id,Model.identity()).rotation_xyzw[axis]
				if absf(delta)<.00001:continue
				var sign_now:=1 if delta>0 else -1
				if sign_before!=0 and sign_now!=sign_before:count+=1
				sign_before=sign_now
			turns=maxi(turns,count)
	var force_variation:=0.
	for force in force_samples:force_variation=maxf(force_variation,force.distance_to(force_samples[0]))
	return {"speed":speed,"direction":direction_index,"ticks":ticks,"selected_rotators":ids.size(),"excluded_rotators":excluded.size(),"excluded_channels_exact":stable,"late_range_degrees":rad_to_deg(late_range),"maximum_step_degrees":rad_to_deg(maximum_step),"reversals":turns,"mean_camera_x_force":sum_axis/ticks,"late_force_variation":force_variation,"final_pose":review.simulation.latest.duplicate(true)}

func run() -> void:
	setup_request();await fresh_app("motion")
	source=await add_source(source_path(),request.mode=="procedural")
	if source==null:await finish("WIND_REVIEW_GPU_MOTION");return
	var source_id: String=source.data.id;var peer: RefCounted
	if request.mode=="procedural":
		var box:=folder.path_join("independent-child.glb");check(box_asset(box)==OK,"create an owned independently parented peer")
		var data:=Model.definition(box);data.position=[-.7,.5,0]
		var peer_id: String=data.id;var adoption_error: String=app.append_object(data,"model")
		metrics["peer_adoption_error"]=adoption_error
		check(adoption_error.is_empty(),"ordinary Add model accepts the separate peer fixture")
		if not adoption_error.is_empty():
			print("WIND_PEER_ADOPTION_ERROR "+adoption_error);check(false,"world installs a separate model parented under the source");await finish("WIND_REVIEW_GPU_MOTION");return
		source=app.renderer.world_runtime.instance(source_id);peer=app.renderer.world_runtime.instance(peer_id)
		check(source!=null and peer!=null and peer!=source and peer_id!=source_id and peer==app.renderer.active_model(),"the peer is a real distinct adopted object rather than the prior active source")
		if source==null or peer==null or peer==source:await finish("WIND_REVIEW_GPU_MOTION");return
		# Add model deliberately creates standalone objects. Use the supported
		# world-document install route to prepare this parented test fixture.
		var parented: Dictionary=app.current_world().duplicate(true)
		for row in parented.objects:
			if row.id==peer_id:row.parent_id=source_id
		var parent_error: String=app.restore_world(parented)
		metrics["peer_parent_install_error"]=parent_error
		if not parent_error.is_empty():print("WIND_PEER_PARENT_INSTALL_ERROR "+parent_error)
		source=app.renderer.world_runtime.instance(source_id);peer=app.renderer.world_runtime.instance(peer_id)
		var parented_ok: bool=parent_error.is_empty() and source!=null and peer!=null and peer!=source and peer.data.id==peer_id and peer.data.parent_id==source_id and peer.root.get_parent()==source.root
		check(parented_ok,"world installs a separate model parented under the source")
		if not parented_ok:await finish("WIND_REVIEW_GPU_MOTION");return
		app.world_selection.select_entity(source_id,false)
	await add_media();var before:=document_state();var view: Dictionary=app.renderer.view_state();var original_meshes:=owned_source_meshes(source)
	var visibility: Dictionary={}
	for mesh in original_meshes:visibility[mesh]=mesh.visible
	if not await open_review():await finish("WIND_REVIEW_GPU_MOTION");return
	var review=app.local_wind_review;var descriptions: Array=[]
	for group in review.catalog.groups:descriptions.append({"chains":group.chain_indices.size(),"linked":group.linked,"rotators":group.rotating_ids.size()})
	if request.mode=="procedural":check(review.catalog.groups.size()==2,"independent authored hair and skirt expose two separately checked groups")
	if request.mode=="backhair":
		var native_chain:=-1;var native_group:=-1
		for i in range(review.catalog.definition.chains.size()):
			var nodes: Array=[]
			for joint in review.catalog.definition.chains[i].joints:nodes.append(int(joint.source_node))
			if nodes.slice(0,3)==[11,10,9]:native_chain=i
		for i in range(review.catalog.groups.size()):
			if native_chain in review.catalog.groups[i].chain_indices:native_group=i
		check(native_chain>=0 and native_group>=0 and review.catalog.definition.chains.size()==2,"actual configured Back hair and retained ribbon bind as two declared chains")
		if native_group>=0:
			review.parts.select(0);review.parts.item_selected.emit(0);review.wind_check.button_pressed=false
			review.parts.select(native_group);review.parts.item_selected.emit(native_group);review.wind_check.button_pressed=true
			check(review.catalog.groups[native_group].rotating_ids.size()>=3 and "regions" in review.detail.text.to_lower(),"one Back hair checkbox discloses shared weighted-region scope rather than surface independence")
	metrics.groups=descriptions;metrics.independent_exclusion_available=review.catalog.groups.size()>1
	var ticks:=1200 if request.mode=="procedural" else 480
	var zero:=await measure(0,0,ticks)
	if zero.has("error"):check(false,zero.error);await finish("WIND_REVIEW_GPU_MOTION");return
	var zero_image: Image=await native_image();zero_image.save_png(folder.path_join("zero-wind.png"))
	var weak:=await measure(3,0,ticks);var strong:=await measure(12,0,ticks)
	if weak.has("error") or strong.has("error"):check(false,"weak and strong try-outs complete");await finish("WIND_REVIEW_GPU_MOTION");return
	var strong_image: Image=await native_image();strong_image.save_png(folder.path_join("strong-wind.png"));main_picture("running")
	var ids:=selected_ids();var wind_angle:=angle(zero.final_pose,strong.final_pose,ids)
	check(wind_angle>.005,"actual spring output differs from the matching no-wind control")
	check(changed_bytes(zero_image,strong_image)>384,"the real native GPU image visibly changes beyond the existing native edge bound")
	check(zero.excluded_channels_exact and weak.excluded_channels_exact and strong.excluded_channels_exact,"unchecked chains retain their exact authored/recorded baseline channels")
	if request.mode=="procedural":
		check(zero.late_range_degrees<.1,"zero local wind adds no artificial late flutter")
		check(weak.late_range_degrees>.5 and weak.reversals>=2,"weak local wind continues moving the actual strip back and forth")
		check(strong.late_range_degrees>weak.late_range_degrees*1.2,"stronger local wind produces a larger continuing response")
	check(strong.maximum_step_degrees<1.61 and weak.maximum_step_degrees<1.61,"real response keeps the existing angular-step limit")
	var opposite:=await measure(12,1,ticks)
	if opposite.has("error"):check(false,opposite.error)
	else:check(strong.mean_camera_x_force*opposite.mean_camera_x_force<0 and strong.late_force_variation>0.00001,"the real airflow reverses with direction and varies over time")
	check(document_matches(before) and app.renderer.view_state()==view,"all wind checks preserve authored data, keys, paint, audio, history, dirty state and shot view")
	if peer:
		var peer_meshes:=owned_source_meshes(peer)
		check(peer!=source and peer.data.id!=source_id and peer.data.parent_id==source_id and peer.root.get_parent()==source.root and peer.root.is_visible_in_tree() and not peer_meshes.is_empty() and peer_meshes.all(func(mesh):return mesh.is_visible_in_tree()) and app.renderer.world_runtime.instance(peer.data.id)==peer,"temporary hiding preserves the independently parented peer")
	review.window.close_requested.emit();await settled()
	check(visibility.keys().all(func(mesh):return mesh.visible==visibility[mesh]),"closing restores each owned mesh's original visibility")
	check(document_matches(before) and app.renderer.native_readbacks==0,"closing leaves the original document and readback balance exact")
	for pair in [["zero",zero],["weak",weak],["strong",strong],["opposite",opposite]]:
		pair[1].erase("final_pose");metrics[pair[0]]=pair[1]
	metrics.wind_control_angle=wind_angle;metrics.changed_native_bytes=changed_bytes(zero_image,strong_image)
	await finish("WIND_REVIEW_GPU_MOTION")
