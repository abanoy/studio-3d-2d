extends SceneTree
# Actual ordinary-app controls. Native geometry/weighted points stay in RAM.
const Model = preload("res://src/model.gd")
const Timeline = preload("res://src/timeline.gd")
const Bindings = preload("res://src/source_bone_bindings.gd")
const Native = preload("res://src/source_secondary.gd")
const Secondary = preload("res://src/secondary_live.gd")
const Airflow = preload("res://src/airflow.gd")
const Capture = preload("res://tests/source_native_five_capture.gd")
const Fixture = preload("res://tests/secondary_fixture.gd")
const Storage = preload("res://src/storage.gd")
const SUBTREE_COUNTS := {"8":[152,144,9509],"17":[184,118,9477],"18":[156,148,9505],"26":[358,222,9303],"27":[248,220,9413]}
var app
var job: Dictionary = {}
var job_path := ""
var named: Dictionary = {}
var metrics: Dictionary = {}
var failures := 0
var target_id := ""
var fan_id := ""
var binding: RefCounted
var expected: Dictionary = {}

class TickGate extends Node:
	var editor
	var runner
	var target: int
	var done := false
	var samples: Array[Vector3] = []
	var samples_by_id: Dictionary = {}
	var actor
	var bone_id := ""
	var lengths: Dictionary = {}
	var world_scale := 1.0
	var maximum_tip_error := 0.0
	var state_valid := true
	func _physics_process(_delta: float) -> void:
		if runner == null or not runner.active():
			editor.set_physics_process(false);done=true;set_physics_process(false);return
		var states: Dictionary = runner._chain.snapshot().states
		state_valid = state_valid and states.size() == 5 and runner.chains.size() == 5
		for id in lengths:
			var value: Vector3 = actor.bone_transform(id)*Vector3(0,0,lengths[id])
			var tip: Array = states.get(id,{}).get("tip",[])
			if tip.size()!=3: state_valid=false
			else:
				var desired:=Vector3(float(tip[0]),float(tip[1]),float(tip[2]))
				if not value.is_finite() or not desired.is_finite():state_valid=false
				else:
					var error: float = value.distance_to(desired)
					maximum_tip_error=maxf(maximum_tip_error,error)
					state_valid = state_valid and error <= .00002*float(runner._size_tokens[id])
			if not samples_by_id.has(id):samples_by_id[id]=[]
			samples_by_id[id].append(value)
			if id==bone_id:samples.append(value)
		if runner._tick >= target:
			editor.set_physics_process(false);done=true;set_physics_process(false)

func _initialize() -> void: call_deferred("run")

func check(ok: bool,name: String) -> bool:
	if named.has(name):ok=false
	named[name]=ok
	if not ok:failures+=1
	print(("PASS " if ok else "FAIL ")+"native_live."+name)
	return ok

func digest(value: Variant) -> String:
	return Capture.digest(JSON.stringify(value,"",true,true).to_utf8_buffer())

func actor() -> RefCounted:
	return app.renderer.world_runtime.instance(target_id) if app.renderer.world_runtime else null

func select(id: String) -> void:
	app.world_selection.select_entity(id);app.physics_editor.sync()

func settled() -> void:
	for _i in range(4):await process_frame
	await RenderingServer.frame_post_draw

func wait_job() -> void:
	var until:=Time.get_ticks_msec()+120000
	while app.has_project.pid>0 and Time.get_ticks_msec()<until:await process_frame
	await settled()

func off() -> void:
	select(target_id);app.physics_editor.hair_toggle.button_pressed=false
	app.physics_editor.set_physics_process(true)
	await settled()

func on() -> RefCounted:
	select(target_id);app.physics_editor.set_physics_process(true)
	app.physics_editor.hair_toggle.button_pressed=true
	var until:=Time.get_ticks_msec()+10000
	while app.physics_editor.pending.has(target_id) and Time.get_ticks_msec()<until:await process_frame
	return app.physics_editor.simulations.get(target_id)

func unchanged_pose(snapshot: Dictionary) -> bool:
	return actor().data==snapshot and actor().live_pose==null and actor().live_world_transform==null

func raw_report() -> Dictionary:
	return actor().data.metadata.native_parameters

func inert_report() -> bool:
	var native: Dictionary=raw_report().native_parameters
	var rules: Dictionary=native.source_jiggle
	return rules.status=="retained_inert" and rules.runtime_support=="not_implemented" and rules.applied==false and rules.full_native_rule_layout_verified==false and rules.rules.size()==49 and native.source_export_crosswalk.native_solver=="not_implemented"

func selected_bindings() -> Array:
	var resolved: RefCounted = Bindings.resolve(actor())
	var result: Array=[]
	if resolved.status!="bound_inactive":return result
	for index in [8,17,18,26,27]:result.append(resolved.bindings[index])
	return result

func selected_ids() -> Array:
	var result: Array=[]
	for entry in selected_bindings():result.append(entry.has_id)
	return result

func subtree_captures() -> Dictionary:
	var resolved: RefCounted=Bindings.resolve(actor());var result: Dictionary={}
	if resolved.status!="bound_inactive":return result
	for index in [8,17,18,26,27]:
		var native_ids: Array = [17,18] if index==17 else [26,27] if index==26 else [index]
		var chosen: Array=[]
		for native_id in native_ids:chosen.append(resolved.bindings[native_id])
		result[str(index)]=Capture.capture(actor(),chosen)
	return result

func world_bones(exclude: Array=[]) -> PackedByteArray:
	var rows: Array=[]
	for id in actor().order:
		if not exclude.has(id):rows.append([id,actor().bone_transform(id)])
	return var_to_bytes(rows)

func pose_at(frame: int) -> Dictionary:
	return {"pose":actor().sample(frame,false),"transform":actor().sample_transform(frame,false)}

func find_button(text: String) -> Button:
	for node in app.find_children("*","Button",true,false):
		if node.text==text:return node
	return null

func configure_fan(speed: float,kind: String) -> void:
	select(fan_id)
	var editor=app.physics_editor.fan_editor
	editor.speed.value=speed
	editor.enabled.button_pressed=kind!="disabled"
	if kind in ["aimed","disabled"]:editor.aim.pressed.emit()
	else:
		var fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
		var base: Dictionary=editor.aimed_world(actor(),1.0)
		var center: Vector3=base.transform*Vector3(0,.85,1.5)
		var direction: Vector3=base.transform.basis.z.normalized()
		if kind=="opposite":direction=-direction
		var origin: Vector3=center-direction*1.5-Vector3.UP*.85
		if kind=="miss":origin+=Vector3.UP*20
		var desired:=Transform3D(Basis(Quaternion(Vector3.BACK,direction)),origin)
		var local: Transform3D=fan.root.get_parent().global_transform.affine_inverse()*desired*fan.base_root.affine_inverse()
		var before: Dictionary=fan.data.duplicate(true)
		app.pose_editor.selected="@root";app.pose_editor.set_delta(local.origin,local.basis.get_rotation_quaternion());app.pose_editor.commit(before,true)
	editor.update_status()
	await settled()

func transverse_camera_fixture() -> void:
	# Establish a bending experiment instead of a nearly axial wind experiment.
	# This changes only the observer's camera fixture, never product airflow.
	var center:=Vector3.ZERO;var chosen: Array=selected_bindings()
	for entry in chosen:center+=actor().bone_transform(entry.has_id).origin
	center/=float(chosen.size())
	var forward: Vector3=actor().bone_transform(binding.has_id).basis.z.normalized()
	var direction: Vector3=forward.cross(Vector3.UP)
	if direction.length_squared()<.000000000001:direction=Vector3.RIGHT
	direction=direction.normalized()
	var camera: Camera3D=app.renderer.camera
	var distance: float=maxf(2.0,camera.global_position.distance_to(center))
	var height: float=camera.global_position.y-center.y
	camera.global_position=center-direction*distance+Vector3.UP*height;camera.look_at(center,Vector3.UP)

func controlled_fixture_admission() -> void:
	# Root keys and actual root geometry stay fixed during fan comparisons.
	app.set_frame(0);await settled();var root0: Transform3D=actor().root.global_transform
	app.set_frame(24);await settled();var root24: Transform3D=actor().root.global_transform
	var root_keys_equal: bool=actor().sample_transform(0)==actor().sample_transform(24)
	app.set_frame(12);await settled();await configure_fan(12.0,"aimed")
	var fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
	var positive: Transform3D=fan.root.global_transform;var settings: Dictionary=fan.data.metadata.airflow.duplicate(true)
	var means: Dictionary={};var all_hits:=true;var maximum_alignment:=0.0;var greatest_opposite_dot:=-INF
	var forward: Vector3=actor().bone_transform(binding.has_id).basis.z.normalized()
	maximum_alignment=absf(forward.dot(positive.basis.z.normalized()))
	for entry in selected_bindings():
		var force: Vector3=Airflow.field(positive,settings,actor().bone_transform(entry.has_id).origin)
		means[entry.has_id]=force;all_hits=all_hits and force.length_squared()>0.0
	await configure_fan(12.0,"opposite");fan=app.renderer.world_runtime.instance(fan_id)
	maximum_alignment=maxf(maximum_alignment,absf(forward.dot(fan.root.global_basis.z.normalized())))
	for entry in selected_bindings():
		var force: Vector3=Airflow.field(fan.root.global_transform,fan.data.metadata.airflow,actor().bone_transform(entry.has_id).origin)
		var previous: Vector3=means[entry.has_id]
		all_hits=all_hits and force.length_squared()>0.0
		var denominator: float=previous.length()*force.length()
		greatest_opposite_dot=maxf(greatest_opposite_dot,previous.dot(force)/denominator if denominator>0.0 else 1.0)
	metrics["controlled_fixture"]={"root_keys_equal":root_keys_equal,"root_geometry_frames0_24_exact":root0==root24,"native8_goal_mean_axis_abs_dot_max":maximum_alignment,"all5_both_mean_fields_hit":all_hits,"greatest_mean_field_normalized_dot":greatest_opposite_dot,"admission_only_no_physics_tolerance_change":true}
	check(root_keys_equal and root0==root24 and all_hits and maximum_alignment<=.0001 and greatest_opposite_dot<=-.9999,"fan.controlled_transverse_fixture")

func enable_record_root_rotation_fixture() -> void:
	# The same0.47 root-key stress remains in the actual Record pipeline, after
	# the fixed-root fan experiment. Observe actual geometry, not just key data.
	var transform: Dictionary=actor().data.pose_keys[0].transform
	var later: Dictionary=actor().data.pose_keys[1].transform
	var root_q:=Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)
	later.rotation_xyzw=[root_q.x,root_q.y,root_q.z,root_q.w]
	app.set_frame(0);await settled();var root0: Transform3D=actor().root.global_transform
	app.set_frame(24);await settled();var root24: Transform3D=actor().root.global_transform
	check(transform.scale==later.scale and transform.rotation_xyzw!=later.rotation_xyzw and root0!=root24,"import.keyed_root_rotation_constant_scale")
	metrics["record_root_rotation_fixture"]={"actual_root_geometry_changed":root0!=root24,"root_key_radians":0.47,"constant_scale":transform.scale==later.scale}
	app.set_frame(12);await settled()

func sample_profile(name: String,speed: float,kind: String) -> Dictionary:
	await off();app.set_frame(12);await configure_fan(speed,kind)
	var base: Dictionary=actor().data.duplicate(true)
	var protected:=world_bones(selected_ids())
	var report_sha:=digest(raw_report())
	var rest_capture:=Capture.capture(actor(),selected_bindings())
	var simulation: RefCounted=await on()
	var active: bool=simulation is Secondary and simulation.native_backend and simulation.runner is Native and simulation.runner.active()
	check(active,name+".on")
	if not active:return {}
	var gate:=TickGate.new();gate.editor=app.physics_editor;gate.runner=simulation.runner;gate.target=simulation.runner._tick+180
	gate.actor=actor();gate.bone_id=binding.has_id
	gate.world_scale=float(simulation.runner._size_tokens[binding.has_id])
	for id in simulation.runner._size_tokens:gate.world_scale=minf(gate.world_scale,float(simulation.runner._size_tokens[id]))
	var native: Dictionary=raw_report().native_parameters
	for row in native.source_jiggle.rules:
		if int(row.native_bone_index) in [8,17,18,26,27]:
			var id: String=simulation.runner.resolution.by_native[int(row.native_bone_index)]
			gate.lengths[id]=float(row.parameters.length)*Native.SOURCE_SCALE
	gate.process_physics_priority=100;app.add_child(gate)
	var until:=Time.get_ticks_msec()+10000
	while not gate.done and Time.get_ticks_msec()<until:await process_frame
	check(gate.done and simulation.runner._tick==gate.target and gate.state_valid and gate.maximum_tip_error<=.00002*gate.world_scale,name+".fixed_ticks")
	var captured:=Capture.capture(actor(),selected_bindings())
	var subtrees: Dictionary=subtree_captures()
	var profile_ok: bool=not captured.has("error") and captured.vertices==9661 and captured.affected==694 and captured.shared==484 and captured.unaffected==8967 and subtrees.size()==5
	for native_index in [8,17,18,26,27]:
		var domain: Dictionary=subtrees.get(str(native_index),{})
		var expected: Array=SUBTREE_COUNTS[str(native_index)]
		profile_ok=profile_ok and not domain.has("error") and domain.get("affected")==expected[0] and domain.get("shared")==expected[1] and domain.get("unaffected")==expected[2]
	check(profile_ok,name+".weighted_profile")
	check(actor().data==base and world_bones(selected_ids())==protected and digest(raw_report())==report_sha and inert_report(),name+".authored_and_64_bones")
	var maximum_tip_error: float=gate.maximum_tip_error
	var samples: Array[Vector3]=gate.samples.duplicate()
	var per_rule_samples: Dictionary=gate.samples_by_id.duplicate(true);gate.free()
	var span:=0.0
	if samples.size()>60:
		for point in samples.slice(samples.size()-60):span=maxf(span,point.distance_to(samples[-1]))
	var tips: Dictionary={};var spans: Dictionary={}
	for id in per_rule_samples:
		var values: Array=per_rule_samples[id];var extent:=0.0
		if values.size()>60:
			for point in values.slice(values.size()-60):extent=maxf(extent,point.distance_to(values[-1]))
		tips[id]=values[-1] if not values.is_empty() else Vector3.ZERO;spans[id]=extent
	metrics[name]={"native_step_processing":{"samples":simulation.runner.processing_samples,"mean_usec":float(simulation.runner.processing_total_usec)/float(maxi(1,simulation.runner.processing_samples)),"max_usec":simulation.runner.processing_max_usec,"scope":"Successful full Native.step; measured only, no FPS criterion"},"per_rule_last60_tick_spans":spans,"tick_count":180,"last60_tick_span":span,"span_duration_seconds":0.5,"native_Z_tip_error_max":maximum_tip_error,"points_sha256":captured.get("points_sha256","")}
	await off()
	var restored:=Capture.capture(actor(),selected_bindings())
	check(unchanged_pose(base) and not restored.has("error") and not rest_capture.has("error") and restored.points_sha256==rest_capture.points_sha256 and digest(raw_report())==report_sha,name+".off_restores_authored")
	return {"capture":captured,"restored":restored,"tip":samples[-1] if not samples.is_empty() else Vector3.ZERO,"span":span,"tips":tips,"spans":spans,"subtrees":subtrees}

func picture(frame: int,name: String) -> Dictionary:
	app.set_frame(frame);await settled()
	var image: Image=await app.renderer.capture(app.keys,app.layers,frame,true)
	if image==null or image.is_empty():return {"error":"empty frame"}
	image.convert(Image.FORMAT_RGBA8)
	var path: String=job.folder.path_join(name+"-"+str(frame)+".png")
	var error:=image.save_png(path)
	return {"frame":frame,"path":path,"width":image.get_width(),"height":image.get_height(),"pixel_sha256":Capture.digest(image.get_data()),"save_error":error}

func writer() -> void:
	app.new_project();app.load_demo_room();app.mode.select(2);app.change_mode(2)
	var added: String=app.pose_editor.add_model(job.glb)
	target_id=app.last_import_id;select(target_id)
	check(added.is_empty() and actor()!=null,"import.normal_add_model")
	if actor()==null:return
	var resolved: RefCounted=Bindings.resolve(actor())
	check(Native.offered(actor()) and resolved.status=="bound_inactive" and resolved.bindings.size()==69 and resolved.rule_owner_ids.size()==49 and actor().root.get_meta("has_secondary_rig",{}).get("chains",[]).is_empty(),"import.exact_69_49_no_generic")
	if resolved.status!="bound_inactive":return
	binding=resolved.bindings[8]
	check(binding.native_parent_index==7 and actor().bones[binding.has_id].name=="FrontHair1" and inert_report(),"import.native8_identity")
	# Actual native On/Off before synthetic full-pose keys.
	var fresh_data: Dictionary=actor().data.duplicate(true);var fresh_worlds:=world_bones()
	var fresh: RefCounted=await on();await settled()
	check(fresh is Secondary and fresh.native_backend and fresh.runner.chains.size()==5 and fresh.runner._chain.snapshot().states.size()==5,"import.fresh_native5_on")
	var fallback_ok: bool=fresh!=null and fresh.latest.size()>=5 and fresh_data.pose_keys.is_empty() and fresh_data.pose.size()<69
	if fresh:
		for id in selected_ids():fallback_ok=fallback_ok and fresh.latest.get(id,Model.identity()).position==fresh_data.pose.get(id,Model.identity()).position
	check(fallback_ok,"import.fresh_native5_identity_fallback")
	await off()
	check(unchanged_pose(fresh_data) and world_bones()==fresh_worlds,"import.fresh_native5_off_exact")
	actor().data.pose={binding.has_id:{"position":[0.001,-0.0015,0.0007],"rotation_xyzw":[0.0,0.0,0.0,1.0]}};actor().data.pose_keys=[];app.set_frame(0)
	var partial: Dictionary=actor().data.duplicate(true);fresh=await on();await settled()
	var partial_ok: bool=fresh is Secondary and fresh.native_backend
	if fresh:
		for id in selected_ids():partial_ok=partial_ok and fresh.latest.get(id,Model.identity()).position==partial.pose.get(id,Model.identity()).position
	await off();check(partial_ok and unchanged_pose(partial),"import.partial_native5_on_off")
	actor().data=fresh_data;app.set_frame(0)
	var original_report_sha:=digest(raw_report())
	var transform: Dictionary=actor().sample_transform(0)
	var a: Dictionary={};var b: Dictionary={}
	for index in [7,8,17,18,25,26,27]:
		var id: String=resolved.by_native[index]
		var q:=Quaternion(Vector3.RIGHT,.06 if index==8 else -.03)
		a[id]={"position":[0.0,0.0,0.0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
		q=Quaternion(Vector3.UP,-.08 if index==8 else .04)
		b[id]={"position":[0.0,0.0,0.0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	actor().data.pose=a.duplicate(true);actor().data.draft_frame=0
	var later: Dictionary=transform.duplicate(true)
	actor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":later,"interpolation":"linear"}]
	check(Model.validate(actor().data,48).is_empty() and actor().check_bindings().is_empty(),"import.nonrest_keys_valid")
	app.set_frame(12);app.pose_editor.frame_model();transverse_camera_fixture();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
	var target_before: Dictionary=actor().data.duplicate(true)
	var before12:=Capture.capture(actor(),selected_bindings())
	var button:=find_button("Add fan")
	check(button!=null,"fan.add_control")
	if button==null:return
	button.pressed.emit();fan_id=app.last_import_id
	check(fan_id!=target_id and Airflow.is_fan(app.renderer.world_runtime.instance(fan_id).data),"fan.actual_add")
	# Add model/fan can rebuild the ordinary world; rebind the existing target.
	select(target_id);resolved=Bindings.resolve(actor());binding=resolved.bindings[8]
	select(fan_id);var fan_editor=app.physics_editor.fan_editor
	var aim_rig_before:=var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))
	fan_editor.aim.pressed.emit();await settled()
	var aim_center:=Vector3.ZERO;var aim_bindings: Array=selected_bindings()
	for entry in aim_bindings:aim_center+=actor().bone_transform(entry.has_id).origin
	aim_center/=float(aim_bindings.size())
	var aim_fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
	var aim_centroid_error: float=(aim_fan.root.global_transform*Vector3(0,.85,1.5)).distance_to(aim_center)
	metrics["initial_UI_Aim"]={"anchor_count":aim_bindings.size(),"centroid_world_error":aim_centroid_error}
	check(fan_editor.target_model()==actor() and not fan_editor.aim.disabled and Native.offered(actor()) and var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))==aim_rig_before and aim_bindings.size()==5 and aim_centroid_error<=.00002,"fan.native_target_and_aim")
	var anchor: Vector3=actor().bone_transform(binding.has_id).origin
	var fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
	check(Airflow.field(fan.root.global_transform,fan.data.metadata.airflow,anchor).length()>0,"fan.actual_field_reaches_joint")
	await controlled_fixture_admission()
	var profile: Dictionary={}
	for row in [{"name":"disabled","speed":12.0,"kind":"disabled"},{"name":"zero","speed":0.0,"kind":"aimed"},{"name":"miss","speed":12.0,"kind":"miss"},{"name":"speed3","speed":3.0,"kind":"aimed"},{"name":"speed12","speed":12.0,"kind":"aimed"},{"name":"speed50","speed":50.0,"kind":"aimed"},{"name":"opposite","speed":12.0,"kind":"opposite"}]:
		profile[row.name]=await sample_profile(row.name,row.speed,row.kind)
		if profile[row.name].is_empty():return
	var control: Dictionary=profile.disabled.capture
	for name in ["zero","miss"]:
		var same:=Capture.difference(control,profile[name].capture,0.0)
		check(not same.has("error") and same.all_points_exact,"fan."+name+"_equals_disabled")
	for name in ["speed3","speed12","speed50","opposite"]:
		var delta:=Capture.difference(control,profile[name].capture,.00001)
		var every_rule: bool=not delta.has("error") and delta.unaffected_exact and delta.affected_vertices_moved>0 and delta.affected_max>.00001
		var original_front: Dictionary={}
		for index in [8,17,18,26,27]:
			var difference:=Capture.difference(profile.disabled.subtrees[str(index)],profile[name].subtrees[str(index)],.00001)
			every_rule=every_rule and not difference.has("error") and difference.affected_vertices_moved>0 and difference.affected_max>.00001
			if index==8:original_front=difference
		check(every_rule,"fan."+name+"_weighted_response")
		metrics[name]["affected_max_vs_disabled"]=original_front.get("affected_max",0.0)
		metrics[name]["union_affected_max_vs_disabled"]=delta.get("affected_max",0.0)
	var every_wiggle: bool=metrics.speed50.affected_max_vs_disabled>.001 and profile.speed50.span>.00005
	for id in profile.speed50.spans:every_wiggle=every_wiggle and profile.speed50.spans[id]>.00005
	check(every_wiggle,"fan.strong_response_and_wiggle")
	var plus: Vector3=profile.speed12.tip-profile.disabled.tip
	var minus: Vector3=profile.opposite.tip-profile.disabled.tip
	var every_opposite: bool=plus.dot(minus)<0.0
	for id in profile.speed12.tips:
		var positive: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id]
		var negative: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]
		every_opposite=every_opposite and positive.dot(negative)<0.0
	check(every_opposite,"fan.opposite_tip_directions")
	check(actor().data==target_before and digest(raw_report())==original_report_sha,"off.all_profiles_keep_authored")
	var restored12:=Capture.capture(actor(),selected_bindings())
	check(not restored12.has("error") and before12.points_sha256==restored12.points_sha256,"off.keyed12_weighted_exact")
	await configure_fan(12.0,"aimed")
	var simulation: RefCounted=await on()
	var root_id: int=actor().root.get_instance_id();var sim_id: int=simulation.get_instance_id()
	app.physics_editor.toggle.button_pressed=true;await settled()
	check(app.physics_editor.simulations.get(target_id)==simulation and simulation.get_instance_id()==sim_id and actor().root.get_instance_id()==root_id and not app.physics_editor.body_active(target_id),"body.refuse_allocation_while_native")
	await off();app.set_frame(24);var data24: Dictionary=actor().data.duplicate(true);var points24:=Capture.capture(actor(),selected_bindings())
	await on();await settled();await off()
	check(unchanged_pose(data24) and Capture.capture(actor(),selected_bindings()).points_sha256==points24.points_sha256,"off.keyed24_weighted_exact")
	app.set_frame(12);await on();await settled();app.set_frame(24);await settled()
	check(not app.physics_editor.active(target_id) and actor().data==target_before and inert_report(),"seek.restores_without_draft")
	app.set_frame(12);await on();await settled()
	app.has_project.save_file(job.folder.path_join("unrecorded.has"),"packed");await wait_job()
	check(not app.physics_editor.active(target_id) and actor().data==target_before and FileAccess.file_exists(job.folder.path_join("unrecorded.has")),"save.restores_without_draft")
	# This exact source is a partial head/torso/hair rig. No synthetic limbs may
	# be invented to make its unsupported same-actor ragdoll test appear to pass.
	var partial_before: Dictionary=actor().data.duplicate(true)
	var partial_history: int=app.history.size()
	select(target_id);app.physics_editor.toggle.button_pressed=true;await settled()
	check(not app.physics_editor.active(target_id) and not app.physics_editor.toggle.button_pressed and app.status.text=="This rig has no validated arm or leg chain for automatic ragdoll setup.","body.partial_rig_refuses_ragdoll")
	check(unchanged_pose(partial_before) and actor().root.get_instance_id()==root_id and app.history.size()==partial_history and actor().root.find_children("*","PhysicalBone3D",true,false).is_empty() and Native.offered(actor()),"body.partial_refusal_preserves_model")
	# The real Fan is a supported rigid prop. Its separate body must survive
	# native Hair On and Off on this actor without any instance/RID replacement.
	select(fan_id);app.physics_editor.toggle.button_pressed=true;await settled()
	var independent: RefCounted=app.physics_editor.simulations.get(fan_id)
	var independent_started: bool=independent!=null and app.physics_editor.body_active(fan_id)
	var independent_bodies: Dictionary=independent.bodies.duplicate() if independent_started else {}
	var independent_rid: RID=independent.body.get_rid() if independent_started else RID()
	check(independent_started and independent.running and independent_bodies.size()==1 and independent_rid.is_valid(),"body.independent_primary_started")
	var independent_native: RefCounted=await on();await settled()
	check(independent_started and independent_native is Secondary and independent_native.native_backend and app.physics_editor.simulations.get(fan_id)==independent and independent.running and independent.bodies==independent_bodies and independent.body.get_rid()==independent_rid,"body.NativeHairOn_keepssameindependent_primary")
	await off()
	check(app.physics_editor.simulations.get(fan_id)==independent and independent!=null and independent.running and independent.bodies==independent_bodies and independent.body.get_rid()==independent_rid and unchanged_pose(target_before),"body.NativeHairOff_keepssameindependent_primary")
	select(fan_id);app.physics_editor.toggle.button_pressed=false;await settled()
	app.set_frame(12);await settled()
	check(actor().data==target_before and not app.physics_editor.is_running(),"body.test_authored_restore")
	await enable_record_root_rotation_fixture()
	await configure_fan(12.0,"aimed");select(target_id)
	var world_before: Dictionary=app.current_world();var history_before: int=app.history.size()
	await on();var recording=app.physics_editor.recording
	recording.scope.select(0);recording.scope.item_selected.emit(0);recording.button.pressed.emit()
	check(recording.active and recording.targets.keys()==[target_id],"record.cancel_connected_local")
	var until:=Time.get_ticks_msec()+15000
	while recording.active and recording.last_frame<16 and Time.get_ticks_msec()<until:await process_frame
	var escape:=InputEventKey.new();escape.keycode=KEY_ESCAPE;escape.pressed=true;app._input(escape);await settled()
	check(not recording.active and not app.physics_editor.is_running() and app.current_world()==world_before and app.history.size()==history_before,"record.escape_preserves_authored")
	app.set_frame(0);await configure_fan(12.0,"aimed");select(target_id)
	world_before=app.current_world();history_before=app.history.size();var data_before: Dictionary=actor().data.duplicate(true)
	await on();recording.scope.select(0);recording.button.pressed.emit()
	check(recording.active and recording.targets.keys()==[target_id],"record.stop_connected_local")
	until=Time.get_ticks_msec()+20000
	while recording.active and recording.last_frame<24 and Time.get_ticks_msec()<until:await process_frame
	recording.button.pressed.emit();await settled()
	check(not recording.active and recording.last_error.is_empty() and not app.physics_editor.is_running() and actor().has_animation() and app.history.size()==history_before+1,"record.stop_ordinary_fk_take")
	var take: Dictionary=actor().data.duplicate(true)
	check(actor().root.get_instance_id()==root_id and digest(raw_report())==original_report_sha and inert_report(),"record.same_actor_and_immutable_report")
	app.undo();await settled()
	check(actor().data==data_before and not app.physics_editor.is_running(),"record.undo_exact")
	app.redo();await settled()
	check(actor().data==take and not app.physics_editor.is_running(),"record.redo_exact")
	var saved_poses: Dictionary={};var pictures: Dictionary={}
	for frame in [0,24]:
		saved_poses[str(frame)]=digest(pose_at(frame));pictures[str(frame)]=await picture(frame,"writer")
		check(not pictures[str(frame)].has("error") and pictures[str(frame)].save_error==OK,"record.frame_"+str(frame))
	app.set_frame(24);app.set_frame(0);app.set_frame(12);app.set_frame(24)
	check(digest(pose_at(24))==saved_poses["24"] and not app.physics_editor.is_running(),"record.arbitrary_seek")
	var packages: Dictionary={}
	for mode in ["packed","linked"]:
		if mode=="linked":
			# Ordinary packed-open -> linked-save externalizes cache-backed
			# assets beside HAS, matching the established cold-reader pipeline.
			app.has_project.open_file(packages.packed);await wait_job()
		var path: String=job.folder.path_join("native-take-"+mode+".has")
		app.has_project.save_file(path,mode);await wait_job();packages[mode]=path
		check(FileAccess.file_exists(path) and not app.physics_editor.is_running() and digest(raw_report())==original_report_sha,"record.save_"+mode)
	expected={"target_id":target_id,"report_sha256":original_report_sha,"poses":saved_poses,"pictures":pictures,"packages":packages,"metadata_rules":49,"source_sha256":str(job.expected_glb_sha256)}
	write_json(job.folder.path_join("expected.json"),expected)
	# A real generic declared-chain actor must retain the old backend contract.
	app.new_project();var fixture_path: String=job.folder.path_join("generic.glb")
	var generic_ok: bool=Fixture.create(fixture_path)==OK
	var error: String=app.pose_editor.add_model(fixture_path) if generic_ok else "fixture failed"
	target_id=app.last_import_id;select(target_id)
	var generic: RefCounted=await on() if error.is_empty() else null
	check(generic!=null and generic is Secondary and not generic.native_backend and not generic.runner is Native,"generic.existing_backend")
	if generic:await off()
	check(not app.physics_editor.is_running(),"generic.off")

func reader() -> void:
	expected=JSON.parse_string(FileAccess.get_file_as_string(job.expected));target_id=expected.target_id
	app.has_project.open_file(expected.packages[job.storage]);await wait_job()
	check(actor()!=null and not app.physics_editor.is_running() and actor().live_pose==null and actor().live_world_transform==null,"cold.no_autoactivation")
	if actor()==null:return
	var bound: RefCounted=Bindings.resolve(actor());binding=bound.bindings[8] if bound.status=="bound_inactive" else null
	check(binding!=null and bound.bindings.size()==69 and bound.rule_owner_ids.size()==49 and Native.offered(actor()),"cold.bound_profile")
	check(digest(raw_report())==expected.report_sha256 and inert_report(),"cold.report_49_unchanged")
	for frame in [0,24]:
		app.set_frame(frame);await settled()
		check(digest(pose_at(frame))==expected.poses[str(frame)],"cold.fk_"+str(frame))
		var observed:=await picture(frame,"reader-"+job.storage)
		check(not observed.has("error") and observed.pixel_sha256==expected.pictures[str(frame)].pixel_sha256,"cold.frame_"+str(frame))
	app.set_frame(24);app.set_frame(0);app.set_frame(12);app.set_frame(24)
	check(digest(pose_at(24))==expected.poses["24"] and not app.physics_editor.is_running(),"cold.arbitrary_seek")
	if job.get("export_frames",false):
		var parent: String=job.folder.path_join("export")
		DirAccess.make_dir_recursive_absolute(parent)
		var error: String=await app.export_frames(parent,true,false)
		check(error.is_empty(),"cold.export")
		for frame in [0,24]:
			var image:=Image.load_from_file(app.last_export_folder.path_join("frame_%06d.png"%(frame+1)))
			if image:image.convert(Image.FORMAT_RGBA8)
			check(image!=null and not image.is_empty() and Capture.digest(image.get_data())==expected.pictures[str(frame)].pixel_sha256,"cold.export_frame_"+str(frame))

func write_json(path: String,value: Variant) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(value,"  ",true,true)+"\n");file.close()
	else:push_error("Cannot write native live evidence")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("One owned native-live job required");quit(2);return
	job_path=args[0];var parsed=JSON.parse_string(FileAccess.get_file_as_string(job_path))
	if not parsed is Dictionary or parsed.get("format")!="has_source_native_five_transverse_live_job_3":push_error("Invalid native-live job");quit(2);return
	job=parsed;create_timer(240).timeout.connect(func():push_error("Native live watchdog");quit(2))
	app=load("res://main.tscn").instantiate();app.recovery_root=job.folder.path_join("recovery");app.recent_path=job.folder.path_join("recent.json");app.display_prefs_path=job.folder.path_join("display.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=job.folder.path_join("has-cache")
	if job.mode=="writer":await writer()
	else:await reader()
	var names: Array=named.keys();names.sort();var planned: Array=job.expected_names.duplicate();planned.sort()
	var complete: bool=names==planned
	if not complete:failures+=1;print("FAIL native live assertion set differs")
	var result={"format":"has_source_native_five_transverse_live_result_3","mode":job.mode,"storage":job.get("storage",""),"checks":named.size(),"failures":failures,"named_checks":named,"complete_assertion_set":complete,"metrics":metrics,"actual_editor":true,"native_rules_solved":5,"retained_rules":49,"native_conversion_performed":false,"same_actor_reverse_body_qualification":"UNQUALIFIED_PARTIAL_SOURCE_RIG","job_path":job_path,"job_sha256":FileAccess.get_sha256(job_path),"project_root":ProjectSettings.globalize_path("res://"),"source_manifest_sha256":job.source_manifest_sha256,"expected":job.folder.path_join("expected.json") if job.mode=="writer" else job.expected,"private_native_arrays_serialized":false}
	write_json(job.folder.path_join("result.json"),result);print("SOURCE_NATIVE_LIVE "+JSON.stringify({"checks":named.size(),"failures":failures,"complete_assertion_set":complete}))
	app.free();await process_frame;quit(0 if failures==0 else 1)
