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
	var sampled_ages: Array[float] = []
	var simulation
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
		sampled_ages.append(maxf(0.0,float(simulation.age)-1.0/120.0))
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
		var center: Vector3=actor().bone_transform(binding.has_id).origin
		var base: Dictionary=editor.aimed_world(actor(),1.0)
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

func diagnostic_context() -> Dictionary:
	# Actual scene field/goal data; this dictionary NEVER enters write_json.
	var fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
	var fields: Array=Airflow.collect(app.renderer,float(app.frame),app.physics_editor.simulations)
	var result: Dictionary={"fields":fields,"axis":fan.root.global_basis.z.normalized(),"nozzle":fan.root.global_transform*Vector3(0,.85,0),"goals":{},"origins":{},"mean_fields":{},"locals":{},"lengths":{},"native_ids":{},"settings":fan.data.metadata.airflow.duplicate(true),"fan_transform":fan.root.global_transform}
	var resolved: RefCounted=Bindings.resolve(actor())
	for index in [8,17,18,26,27]:
		var entry: RefCounted=resolved.bindings[index];var id: String=entry.has_id
		var frame: Transform3D=actor().bone_transform(id)
		result.goals[id]={"left":frame.basis.x.normalized(),"up":frame.basis.y.normalized(),"forward":frame.basis.z.normalized()}
		result.origins[id]=frame.origin;result.locals[id]=entry.skeleton.get_bone_pose(entry.skeleton_bone_index);result.native_ids[id]=index
		result.mean_fields[id]=Airflow.field(fan.root.global_transform,result.settings,frame.origin)
		for rule in raw_report().native_parameters.source_jiggle.rules:
			if int(rule.native_bone_index)==index:result.lengths[id]=float(rule.parameters.length)*Native.SOURCE_SCALE*frame.basis.get_scale().x
	return result

func diagnostic_finished(context: Dictionary, ages: Array[float]) -> void:
	context["final_origins"]={};context["final_goals"]={};context["unsteady_mean"]={};context["input_stats"]={}
	for id in context.origins:
		context.final_origins[id]=actor().bone_transform(id).origin
		var parent: String=actor().parent_id(id)
		var composed: Transform3D=actor().bone_transform(parent)*context.locals[id]
		context.final_goals[id]={"left":composed.basis.x.normalized(),"up":composed.basis.y.normalized(),"forward":composed.basis.z.normalized()}
		var total:=Vector3.ZERO;var hits:=0;var peak:=0.0;var sum_lengths:=0.0;var minimum_axis:=INF;var maximum_axis:=-INF
		for age in ages:
			var force: Vector3=Airflow.unsteady_force(context.fields,context.origins[id],age)/0.03
			var size: float=force.length();total+=force;sum_lengths+=size;peak=maxf(peak,size)
			if size>0.0:hits+=1
			minimum_axis=minf(minimum_axis,force.dot(context.axis));maximum_axis=maxf(maximum_axis,force.dot(context.axis))
		context.unsteady_mean[id]=total/float(maxi(1,ages.size()))
		context.input_stats[id]={"samples":ages.size(),"hit_samples":hits,"mean_length":sum_lengths/float(maxi(1,ages.size())),"maximum_length":peak,"minimum_own_fan_axis":minimum_axis if not ages.is_empty() else 0.0,"maximum_own_fan_axis":maximum_axis if not ages.is_empty() else 0.0}

func safe_cosine(first: Vector3, second: Vector3) -> float:
	var length: float=first.length()*second.length()
	return first.dot(second)/length if length>0.0 else 0.0

func scalar_diagnostic(profile: Dictionary) -> Dictionary:
	var positive: Dictionary=profile.speed12.diagnostic_private;var negative: Dictionary=profile.opposite.diagnostic_private;var control: Dictionary=profile.disabled.diagnostic_private
	var result: Dictionary={"format":"has_native_five_opposite_scalar_diagnostic_1","diagnostic_only":true,"fixture_and_all_existing_gates_changed":false,
		"input_sampler":"Recomputed from actual captured scene fields at authored anchors and sampled simulation ages; not a serialized backend force trace.",
		"positive_field_count":positive.fields.size(),"negative_field_count":negative.fields.size(),"fan_axis_dot":positive.axis.dot(negative.axis),
		"positive_negative_nozzle_midpoint_to_front8_distance":((positive.nozzle+negative.nozzle)*.5-positive.origins[binding.has_id]).length(),"native":{}}
	for id in positive.native_ids:
		var index: int=positive.native_ids[id]
		var dp: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id];var dm: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]
		var fp: Vector3=positive.mean_fields[id];var fm: Vector3=negative.mean_fields[id]
		var axis_p: Vector3=fp.normalized() if fp.length_squared()>0.0 else positive.axis
		var axis_m: Vector3=fm.normalized() if fm.length_squared()>0.0 else negative.axis
		var goal: Dictionary=control.goals[id];var forward: Vector3=goal.forward
		var perpendicular: Vector3=axis_p-forward*axis_p.dot(forward);var perpendicular_size: float=perpendicular.length()
		var cross_goal: Vector3=axis_p.cross(forward);var cross_size: float=cross_goal.length()
		var tangent: Vector3=perpendicular/perpendicular_size if perpendicular_size>0.000000001 else Vector3.ZERO
		var cross_axis: Vector3=cross_goal/cross_size if cross_size>0.000000001 else Vector3.ZERO
		var bp: Vector3=positive.final_origins[id]-control.final_origins[id];var bm: Vector3=negative.final_origins[id]-control.final_origins[id]
		var rp: Vector3=dp-bp;var rm: Vector3=dm-bm
		var world_dot: float=dp.dot(dm)
		var plus_residual: Vector3=profile.speed12.tips[id]-(positive.final_origins[id]+positive.final_goals[id].forward*positive.lengths[id])
		var minus_residual: Vector3=profile.opposite.tips[id]-(negative.final_origins[id]+negative.final_goals[id].forward*negative.lengths[id])
		var control_residual: Vector3=profile.disabled.tips[id]-(control.final_origins[id]+control.final_goals[id].forward*control.lengths[id])
		var ep: Vector3=plus_residual-control_residual;var em: Vector3=minus_residual-control_residual
		var nozzle_offset_p: Vector3=positive.origins[id]-positive.nozzle;var nozzle_offset_m: Vector3=negative.origins[id]-negative.nozzle
		var along_p: float=nozzle_offset_p.dot(positive.axis);var along_m: float=nozzle_offset_m.dot(negative.axis)
		var radius_p: float=float(positive.settings.radius)*positive.fan_transform.basis.get_scale().x+along_p*.15
		var radius_m: float=float(negative.settings.radius)*negative.fan_transform.basis.get_scale().x+along_m*.15
		result.native[str(index)]={"native_index":index,"parent_is_simulated":index in [18,27],"original_native8_gate":world_dot<0.0 if index==8 else null,
			"world_delta_dot":world_dot,"world_delta_normalized_dot":safe_cosine(dp,dm),"positive_delta_length":dp.length(),"negative_delta_length":dm.length(),
			"mean_positive_length":fp.length(),"mean_negative_length":fm.length(),"mean_field_normalized_dot":safe_cosine(fp,fm),"positive_mean_hit":fp.length_squared()>0.0,"negative_mean_hit":fm.length_squared()>0.0,
			"goal_forward_abs_dot_positive_mean_axis":absf(forward.dot(axis_p)),"goal_forward_abs_dot_negative_mean_axis":absf(forward.dot(axis_m)),
			"positive_delta_on_positive_mean_axis":dp.dot(axis_p),"positive_delta_on_negative_mean_axis":dp.dot(axis_m),"negative_delta_on_positive_mean_axis":dm.dot(axis_p),"negative_delta_on_negative_mean_axis":dm.dot(axis_m),
			"perpendicular_to_goal_axis_defined":perpendicular_size>0.000000001,"perpendicular_axis_raw_length":perpendicular_size,"positive_delta_on_perpendicular_to_goal":dp.dot(tangent),"negative_delta_on_perpendicular_to_goal":dm.dot(tangent),
			"cross_goal_axis_defined":cross_size>0.000000001,"positive_delta_on_cross_goal":dp.dot(cross_axis),"negative_delta_on_cross_goal":dm.dot(cross_axis),
			"positive_delta_on_goal_left":dp.dot(goal.left),"negative_delta_on_goal_left":dm.dot(goal.left),"positive_delta_on_goal_up":dp.dot(goal.up),"negative_delta_on_goal_up":dm.dot(goal.up),"positive_delta_on_goal_forward":dp.dot(forward),"negative_delta_on_goal_forward":dm.dot(forward),
			"positive_base_shift_length":bp.length(),"negative_base_shift_length":bm.length(),"base_base_dot":bp.dot(bm),"base_ray_dot":bp.dot(rm),"ray_base_dot":rp.dot(bm),"ray_ray_dot":rp.dot(rm),"dot_decomposition_residual":world_dot-bp.dot(bm)-bp.dot(rm)-rp.dot(bm)-rp.dot(rm),
			"same_tick_goal_residual_delta_dot":ep.dot(em),"positive_same_tick_goal_residual_on_perpendicular":ep.dot(tangent),"negative_same_tick_goal_residual_on_perpendicular":em.dot(tangent),
			"unsteady_mean_positive_length":positive.unsteady_mean[id].length(),"unsteady_mean_negative_length":negative.unsteady_mean[id].length(),"unsteady_means_normalized_dot":safe_cosine(positive.unsteady_mean[id],negative.unsteady_mean[id]),"unsteady_positive_on_positive_mean_axis":positive.unsteady_mean[id].dot(axis_p),"unsteady_negative_on_positive_mean_axis":negative.unsteady_mean[id].dot(axis_p),
			"positive_input_samples":positive.input_stats[id].samples,"negative_input_samples":negative.input_stats[id].samples,"positive_input_hit_samples":positive.input_stats[id].hit_samples,"negative_input_hit_samples":negative.input_stats[id].hit_samples,"positive_input_peak_length":positive.input_stats[id].maximum_length,"negative_input_peak_length":negative.input_stats[id].maximum_length,
			"positive_field_along":along_p,"negative_field_along":along_m,"positive_field_radial_fraction":(nozzle_offset_p-positive.axis*along_p).length()/radius_p,"negative_field_radial_fraction":(nozzle_offset_m-negative.axis*along_m).length()/radius_m}
	return result

func sample_profile(name: String,speed: float,kind: String) -> Dictionary:
	await off();app.set_frame(12);await configure_fan(speed,kind)
	var base: Dictionary=actor().data.duplicate(true)
	var protected:=world_bones(selected_ids())
	var report_sha:=digest(raw_report())
	var rest_capture:=Capture.capture(actor(),selected_bindings())
	var diagnostic_private: Dictionary=diagnostic_context()
	var simulation: RefCounted=await on()
	var active: bool=simulation is Secondary and simulation.native_backend and simulation.runner is Native and simulation.runner.active()
	check(active,name+".on")
	if not active:return {}
	var gate:=TickGate.new();gate.editor=app.physics_editor;gate.runner=simulation.runner;gate.target=simulation.runner._tick+180
	gate.actor=actor();gate.bone_id=binding.has_id;gate.simulation=simulation
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
	var per_rule_samples: Dictionary=gate.samples_by_id.duplicate(true)
	diagnostic_finished(diagnostic_private,gate.sampled_ages);gate.free()
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
	return {"capture":captured,"restored":restored,"tip":samples[-1] if not samples.is_empty() else Vector3.ZERO,"span":span,"tips":tips,"spans":spans,"subtrees":subtrees,"diagnostic_private":diagnostic_private}

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
	var later: Dictionary=transform.duplicate(true);var root_q:=Quaternion(Vector3(0.3,0.7,-0.2).normalized(),0.47)
	later.rotation_xyzw=[root_q.x,root_q.y,root_q.z,root_q.w]
	actor().data.pose_keys=[{"frame":0,"pose":a,"transform":transform.duplicate(true),"interpolation":"linear"},{"frame":24,"pose":b,"transform":later,"interpolation":"linear"}]
	check(transform.scale==later.scale and transform.rotation_xyzw!=later.rotation_xyzw,"import.keyed_root_rotation_constant_scale")
	check(Model.validate(actor().data,48).is_empty() and actor().check_bindings().is_empty(),"import.nonrest_keys_valid")
	app.set_frame(12);app.pose_editor.frame_model();app.keys=[Timeline.key(0,app.renderer.camera.position,app.renderer.camera.quaternion,app.renderer.camera.fov)]
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
	check(fan_editor.target_model()==actor() and not fan_editor.aim.disabled and Native.offered(actor()) and var_to_bytes(actor().root.get_meta("has_secondary_rig",{}))==aim_rig_before,"fan.native_target_and_aim")
	var anchor: Vector3=actor().bone_transform(binding.has_id).origin
	var fan: RefCounted=app.renderer.world_runtime.instance(fan_id)
	check(Airflow.field(fan.root.global_transform,fan.data.metadata.airflow,anchor).length()>0,"fan.actual_field_reaches_joint")
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
	check(plus.dot(minus)<0.0,"fan.original_native8_opposite_tip_directions")
	var every_opposite: bool=plus.dot(minus)<0.0
	for id in profile.speed12.tips:
		var positive: Vector3=profile.speed12.tips[id]-profile.disabled.tips[id]
		var negative: Vector3=profile.opposite.tips[id]-profile.disabled.tips[id]
		every_opposite=every_opposite and positive.dot(negative)<0.0
	check(every_opposite,"fan.opposite_tip_directions")
	var scalar_report: Dictionary=scalar_diagnostic(profile)
	metrics["opposite_diagnostic"]=scalar_report
	write_json(job.folder.path_join("opposite-diagnostic.json"),scalar_report)
	# Diagnostic ends here. Full writer82/1 remains failed and retained.
	return

func write_json(path: String,value: Variant) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(value,"  ",true,true)+"\n");file.close()
	else:push_error("Cannot write native live evidence")

func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("One owned native-live job required");quit(2);return
	job_path=args[0];var parsed=JSON.parse_string(FileAccess.get_file_as_string(job_path))
	if not parsed is Dictionary or parsed.get("format")!="has_source_native_five_opposite_diagnostic_job_1" or parsed.get("mode")!="writer":push_error("Invalid native-live job");quit(2);return
	job=parsed;create_timer(240).timeout.connect(func():push_error("Native live watchdog");quit(2))
	app=load("res://main.tscn").instantiate();app.recovery_root=job.folder.path_join("recovery");app.recent_path=job.folder.path_join("recent.json");app.display_prefs_path=job.folder.path_join("display.cfg")
	root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=job.folder.path_join("has-cache")
	await writer()
	var names: Array=named.keys();names.sort();var planned: Array=job.expected_names.duplicate();planned.sort()
	var complete: bool=names==planned
	if not complete:failures+=1;print("FAIL native live assertion set differs")
	var result={"format":"has_source_native_five_opposite_diagnostic_result_1","mode":job.mode,"storage":job.get("storage",""),"checks":named.size(),"failures":failures,"named_checks":named,"complete_assertion_set":complete,"metrics":metrics,"actual_editor":true,"native_rules_solved":5,"retained_rules":49,"native_conversion_performed":false,"same_actor_reverse_body_qualification":"UNQUALIFIED_PARTIAL_SOURCE_RIG","job_path":job_path,"job_sha256":FileAccess.get_sha256(job_path),"project_root":ProjectSettings.globalize_path("res://"),"source_manifest_sha256":job.source_manifest_sha256,"diagnostic_only":true,"full_writer_qualification_claimed":false,"private_native_arrays_serialized":false}
	write_json(job.folder.path_join("result.json"),result);print("SOURCE_NATIVE_LIVE "+JSON.stringify({"checks":named.size(),"failures":failures,"complete_assertion_set":complete}))
	app.free();await process_frame;quit(0 if failures==0 else 1)
