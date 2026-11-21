extends SceneTree
# Root-only native probe. All model geometry/images/results remain LOCAL.
const Probe=preload("res://src/secondary_collision_probe.gd")
const Binder=preload("res://src/miku_collider_binding.gd")
const SkinBinding=preload("res://src/miku_skin_binding.gd")
const Geometry=preload("res://src/secondary_collision_geometry.gd")
const Definition=preload("res://src/secondary_rig.gd")
const Live=preload("res://src/secondary_live.gd")
const Airflow=preload("res://src/airflow.gd")
var app
var actor: RefCounted
var probe: RefCounted
var live: RefCounted
var tap: RefCounted
var cache: Dictionary={}
var checks:=0
var failures:=0
var result: Dictionary={}
var folder: String
var at_frame:=0
var editing:=false
var original_data:=PackedByteArray()
var original_world:=PackedByteArray()
var original_history:=0
var original_revision:=0
var original_pose: Array=[]
var original_root:=Transform3D.IDENTITY
func _initialize() -> void:
	create_timer(160).timeout.connect(func():push_error("Miku contact qualification watchdog");quit(2));call_deferred("run")
func check(value: bool,label: String) -> void:
	checks+=1;print(("PASS " if value else "FAIL ")+label)
	if not value:failures+=1
func settled() -> void:
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
func pose_frames() -> Array:
	var frames: Array=[]
	for id in actor.order:frames.append(actor.bone_transform(id))
	return frames
func restored() -> bool:
	if actor==null or not is_instance_valid(actor.root) or actor.live_pose!=null or actor.live_world_transform!=null:return false
	var now:=pose_frames()
	if now.size()!=original_pose.size() or SkinBinding.difference(actor.root.global_transform,original_root)>0.00001:return false
	for i in range(now.size()):
		if SkinBinding.difference(now[i],original_pose[i])>0.00001:return false
	return true
func pivots() -> Array:
	var points: Array=[]
	for joint in actor.root.get_meta("has_secondary_rig").chains[0].joints:points.append(Definition.binding_transform(actor,joint.binding).origin)
	return points
func capsules(request: Dictionary,rest:=false) -> Dictionary:
	var rows: Array=[]
	for collider in request.colliders:
		var info: Dictionary=actor.bones[collider.binding.id]
		var transform: Transform3D=info.skeleton.global_transform*info.skeleton.get_bone_global_rest(info.index) if rest else Definition.binding_transform(actor,collider.binding)
		if not Probe.IK.regular(transform.basis):return {"error":"capsule_binding_became_irregular"}
		rows.append({"start":transform*Probe.vector(collider.offset),"finish":transform*Probe.vector(collider.tail),"radius":float(collider.radius)*transform.basis.get_scale().x})
	return {"rows":rows}
func geometry(points: Array,vertices: Array,obstacles: Array) -> Dictionary:
	var radii: Array=[];var joints: Array=actor.root.get_meta("has_secondary_rig").chains[0].joints
	var scale: float=Definition.binding_transform(actor,joints[0].binding).basis.get_scale().x
	for joint in joints:radii.append(float(joint.radius)*scale)
	return Geometry.measure(points,radii,vertices,obstacles)
func aggregate(target: Dictionary,observed: Dictionary,solver_only:=false) -> void:
	for pair in [["minimum_particle_clearance","penetrating_particles"],["minimum_segment_clearance","penetrating_segments"],["minimum_skin_vertex_clearance","penetrating_skin_vertices"]]:
		if solver_only and pair[0]=="minimum_skin_vertex_clearance":continue
		if observed[pair[0]]!=null:target[pair[0]]=minf(float(target.get(pair[0],INF)),float(observed[pair[0]]))
		target[pair[1]]=int(target.get(pair[1],0))+int(observed[pair[1]])
func capture_private() -> bool:
	if actor==null or not is_instance_valid(actor.root) or not actor.root.is_inside_tree() or not is_instance_valid(app):return false
	if not app.renderer.frame_scene(actor.root):return false
	await settled()
	if not app.renderer.begin_native_readback():return false
	var notification=app.renderer.native_frame_notification;await notification.ready
	var image: Image=app.renderer.finish_native_readback()
	return image!=null and image.get_width()*image.get_height()<=8294400 and image.save_png(folder.path_join("PRIVATE_LIVE_FRAME.png"))==OK
func fail_early(code: String) -> void:
	result["error_code"]=code;result["calibration_qualified"]=false;result["capsule_contact_qualified"]=false
	var captured: bool=await capture_private()
	result["private_render_captures"]=1 if captured else 0
	await finish()
func finish() -> void:
	if live and actor and is_instance_valid(actor.root):
		# Exercise the actual user-facing Hair & clothes Off path synchronously,
		# before any automatic editor physics tick can consume this runner.
		app.physics_editor.simulations[actor.data.id]=live
		app.physics_editor.disable_hair(actor.data.id)
		check(restored(),"actual Hair & clothes Off restores explicit saved pose and world")
	if probe:probe.dispose()
	elif live:live.dispose()
	if actor and not original_pose.is_empty():
		check(restored(),"idempotent disposal leaves exact authored-context pose visible")
		check(var_to_bytes(actor.data)==original_data and var_to_bytes(app.current_world())==original_world,"model world fan settings and source data remain byte-identical")
		check(app.history.size()==original_history and app.recovery_revision==original_revision,"native probe adds no Undo entry or dirty revision")
		check(not app.physics_editor.recording.active and app.physics_editor.simulations.is_empty() and app.physics_editor.freeze_all(),"all simulations are off without Record or remaining live state")
	result["checks"]=checks;result["failures"]=failures
	result["status"]="PASS" if failures==0 and result.get("calibration_qualified",false) and result.get("candidate_contact_gate",false) else "FAIL"
	result["capsule_contact_qualified"]=result.status=="PASS" and result.get("collision_profile")=="upper_only" and result.get("initial_clean_start",false)
	result["actual_owner_contact_reproduced"]=false;result["body_triangle_contact_qualified"]=false;result["swept_contact_qualified"]=false;result["skin_shader_equivalence_qualified"]=false;result["moving_actor_inertia_qualified"]=false;result["gravity_rest_settling_qualified"]=false;result["application_adopted"]=false
	var output:=FileAccess.open(folder.path_join("PRIVATE_CONTACT_RESULT.json"),FileAccess.WRITE)
	if output:output.store_string(JSON.stringify(result));output.close()
	print("MIKU_CONTACT_QUALIFICATION ",JSON.stringify({"checks":checks,"failures":failures,"status":result.status,"calibration_qualified":result.get("calibration_qualified",false),"capsule_contact_qualified":result.capsule_contact_qualified,"application_adopted":false}))
	if is_instance_valid(app):await app.quit_studio()
	quit(0 if result.status=="PASS" else 1)
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=7:push_error("Pass private output/project/collider/alignment/context/profile/ticks");quit(2);return
	folder=args[0];editing=args[4]=="editing_true";var profile: String=args[5];var ticks:=int(args[6])
	result={"format":"has_private_miku_saved_contact_qualification_1","private_do_not_publish":true,"source_project_sha256":Binder.PROJECT_SHA,"source_asset_sha256":Probe.MIKU_SHA,"initial_editing_context":editing,"collision_profile":profile,"ticks":0,"calibration_qualified":false,"actual_saved_case_loaded":false}
	if args[4] not in ["editing_true","editing_false"] or profile not in ["original_zero_colliders","upper_only","full_lower_envelope"] or ticks<120 or ticks>Probe.MAX_TICKS:await fail_early("explicit_bounded_case_required");return
	DirAccess.make_dir_recursive_absolute(folder)
	if FileAccess.get_sha256(args[1])!=Binder.PROJECT_SHA:await fail_early("exact_private_saved_project_required");return
	var private_raw:=FileAccess.get_file_as_bytes(args[2]);var alignment_raw:=FileAccess.get_file_as_bytes(args[3])
	if SkinBinding.sha(private_raw)!=Binder.INPUT_SHA or SkinBinding.sha(alignment_raw)!=SkinBinding.ALIGNMENT_SHA:await fail_early("exact_private_inputs_required");return
	var input=JSON.parse_string(private_raw.get_string_from_utf8())
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("display.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settled();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("has-cache")
	app.has_project.open_file(args[1])
	while app.has_project.pid>0:await process_frame
	await settled()
	if app.has_project.path.replace("\\","/").simplify_path().to_lower()!=args[1].replace("\\","/").simplify_path().to_lower() or app.renderer.world_runtime==null:await fail_early("actual_cold_has_load_failed");return
	var candidates: Array=[];var fans:=0
	for instance in app.renderer.world_runtime.instances.values():
		if instance.data.get("sha256")==Probe.MIKU_SHA:candidates.append(instance)
		if Airflow.is_fan(instance.data):fans+=1
	if candidates.size()!=1 or fans!=1:await fail_early("exact_saved_one_miku_one_fan_required");return
	actor=candidates[0];at_frame=app.frame
	if at_frame!=int(actor.data.draft_frame) or actor.data.pose.size()!=6 or app.physics_editor.is_running() or app.physics_editor.recording.active:await fail_early("saved_draft_frame_six_channels_and_idle_context_required");return
	app.mode.select(2 if editing else 1);app.change_mode(app.mode.selected);app.world_selection.select_entity(actor.data.id,false);actor.apply_current(at_frame,editing);await settled()
	original_data=var_to_bytes(actor.data);original_world=var_to_bytes(app.current_world());original_history=app.history.size();original_revision=app.recovery_revision;original_pose=pose_frames();original_root=actor.root.global_transform
	result["actual_saved_case_loaded"]=true;result["sampled_pose_sha256"]=SkinBinding.sha(var_to_bytes(actor.sample(at_frame,editing)));result["saved_draft_channels"]=actor.data.pose.size();result["saved_fan_count"]=fans
	var bound:=Binder.from_bytes(actor,private_raw,["rightUpperArm","rightLowerArm"],profile!="original_zero_colliders")
	if bound.has("error"):await fail_early(bound.error);return
	var measured_request: Dictionary=bound.request
	check(bound.source_runtime_identity_resolved,"exact source nodes match actual Skeleton and independent IK chain")
	var prepared:=SkinBinding.prepare(actor,input,alignment_raw)
	if prepared.has("error"):result["calibration_failure"]=prepared;await fail_early(prepared.error);return
	cache=prepared.cache;result["calibration"]=cache.calibration;result["calibration_qualified"]=true
	check(cache.rows.size()==13111 and cache.hair.size()==989,"complete exact source mesh and hair-support correspondence calibrated")
	var before:=SkinBinding.points(actor,cache);var rest:=SkinBinding.points(actor,cache,true)
	var observed:=capsules(measured_request);var rest_observed:=capsules(measured_request,true)
	if before.has("error") or rest.has("error") or observed.has("error") or rest_observed.has("error"):await fail_early("initial_calibrated_geometry_required");return
	var initial:=geometry(pivots(),before.vertices,observed.rows);var encoded_lower: Dictionary=geometry(pivots(),rest.vertices,[rest_observed.rows[1]])
	# Rest hair vertices use rest palettes; pivots in this diagnostic are not
	# declared rest pivots. Only its skin-vertex count qualifies this derivation.
	if initial.has("error") or encoded_lower.has("error"):await fail_early("initial_full_geometry_measurement_failed");return
	var raw_rest_inside:=0
	for vertex in rest.vertices:
		if Probe.point_segment_distance(vertex,rest_observed.rows[1].start,rest_observed.rows[1].finish)-float(rest_observed.rows[1].radius)<0.:raw_rest_inside+=1
	result["initial_saved_pose_geometry"]=initial;result["encoded_rest_lower_skin_vertices_inside"]=raw_rest_inside;result["encoded_rest_lower_beyond_clearance_tolerance"]=encoded_lower.penetrating_skin_vertices;result["initial_rest_lower_envelope_overlap_warning"]=true
	check(raw_rest_inside==11,"unchanged full sleeve capsule retains eleven encoded-rest hair overlaps")
	var initial_upper:=geometry(pivots(),before.vertices,[observed.rows[0]])
	result["initial_clean_start"]=initial_upper.penetrating_particles==0 and initial_upper.penetrating_segments==0 and initial_upper.penetrating_skin_vertices==0
	var fields: Array=Airflow.collect(app.renderer,float(at_frame),{})
	var fan_stamp:=var_to_bytes(fields);result["saved_fan_field_sha256"]=SkinBinding.sha(fan_stamp)
	check(fields.size()==1,"the unchanged saved fan contributes one actual airflow field")
	if profile=="original_zero_colliders":
		var made: Dictionary=await Live.create(actor,null,at_frame,editing)
		if made.has("error"):await fail_early(made.error);return
		live=made.physics
		if live.native_backend:live.dispose();live=null;await fail_early("exact_generic_spring_reference_required");return
		tap=Probe.Tap.new();tap.delegate=live.runner;tap.chains=live.runner.chains;live.runner=tap;live.start()
		check(tap.chains.size()==1 and tap.chains[0].colliders.is_empty(),"reference uses actual original runner with zero body colliders")
	else:
		var request:=Binder.from_bytes(actor,private_raw,["rightUpperArm"] if profile=="upper_only" else ["rightUpperArm","rightLowerArm"],true)
		if request.has("error"):await fail_early(request.error);return
		var made: Dictionary=await Probe.begin(actor,at_frame,request.request,app,editing)
		if made.has("error"):await fail_early(made.error);return
		probe=made.probe;live=probe.live;tap=probe.tap
		check(tap.chains.size()==1 and tap.chains[0].colliders.size()==(1 if profile=="upper_only" else 2),"candidate uses exact measured capsule count without changing dimensions")
	var totals: Dictionary={"solver_particles_and_segments":{},"raw_fk":{},"visible_fk":{},"maximum_raw_fk_pivot_error":0.,"maximum_visible_vs_solver_pivot_error":0.,"maximum_palette_disagreement":0.}
	var failed:=""
	for tick in range(ticks):
		if probe:
			var advanced: Dictionary=probe.advance(fields,app.renderer.world_runtime)
			if advanced.has("error"):failed=advanced.error;break
		else:
			failed=live.advance(1./120.,at_frame,float(at_frame),false,fields,app.renderer.world_runtime)
			if not failed.is_empty():break
		if tap.captured.size()!=1 or tap.captured[0].size()!=7 or not tap.last_result.get("pose") is Dictionary:failed="complete_raw_modifier_output_required";break
		var solved: Array=[]
		for transform in tap.captured[0]:solved.append(transform.origin)
		var final_pose: Dictionary=live.latest.duplicate(true);var visible_pivots:=pivots();var visible:=SkinBinding.points(actor,cache)
		var raw_pose: Dictionary=live.initial_pose.duplicate(true)
		for id in tap.last_result.pose:raw_pose[id]=tap.last_result.pose[id].duplicate(true)
		actor.live_pose=raw_pose;actor.apply_current(at_frame,editing);var raw_pivots:=pivots();var raw_skin:=SkinBinding.points(actor,cache)
		actor.live_pose=final_pose;actor.apply_current(at_frame,editing)
		if visible.has("error") or raw_skin.has("error"):failed="calibrated_per_tick_skin_required";break
		totals.maximum_palette_disagreement=maxf(totals.maximum_palette_disagreement,maxf(visible.maximum_palette_disagreement,raw_skin.maximum_palette_disagreement))
		if totals.maximum_palette_disagreement>SkinBinding.CALIBRATION_TOLERANCE:failed="per_tick_source_runtime_skin_calibration_failed";break
		var current_capsules:=capsules(measured_request)
		if current_capsules.has("error"):failed=current_capsules.error;break
		# Upper-only is evaluated against its upper envelope; reference/full use both.
		var selected_capsules: Array=[current_capsules.rows[0]] if profile=="upper_only" else current_capsules.rows
		for item in [[solved,raw_skin.vertices,"solver_particles_and_segments"],[raw_pivots,raw_skin.vertices,"raw_fk"],[visible_pivots,visible.vertices,"visible_fk"]]:
			var observed_geometry:=geometry(item[0],item[1],selected_capsules)
			if observed_geometry.has("error"):failed=observed_geometry.error;break
			aggregate(totals[item[2]],observed_geometry,item[2]=="solver_particles_and_segments")
		if not failed.is_empty():break
		for i in range(7):
			totals.maximum_raw_fk_pivot_error=maxf(totals.maximum_raw_fk_pivot_error,solved[i].distance_to(raw_pivots[i]));totals.maximum_visible_vs_solver_pivot_error=maxf(totals.maximum_visible_vs_solver_pivot_error,solved[i].distance_to(visible_pivots[i]))
		result["ticks"]=tick+1
		if var_to_bytes(actor.data)!=original_data or var_to_bytes(Airflow.collect(app.renderer,float(at_frame),{}))!=fan_stamp:failed="authored_state_or_fan_changed";break
	result["measurements"]=totals;result["probe_error"]=failed
	check(failed.is_empty() and result.ticks==ticks,"bounded fixed-step actual solver raw-FK and visible-FK measurement completes")
	check(totals.maximum_palette_disagreement<=SkinBinding.CALIBRATION_TOLERANCE,"actual source inverse-bind and imported skin palettes agree throughout")
	var contacts: Dictionary=totals.visible_fk
	var contact_clear: bool=not contacts.is_empty() and int(contacts.get("penetrating_particles",1))==0 and int(contacts.get("penetrating_segments",1))==0 and int(contacts.get("penetrating_skin_vertices",1))==0
	var all_stages_clear:=contact_clear
	for stage in ["solver_particles_and_segments","raw_fk"]:
		all_stages_clear=all_stages_clear and not totals[stage].is_empty() and int(totals[stage].get("penetrating_particles",1))==0 and int(totals[stage].get("penetrating_segments",1))==0
		if stage=="raw_fk":all_stages_clear=all_stages_clear and int(totals[stage].get("penetrating_skin_vertices",1))==0
	result["raw_fk_reconstruction_agrees"]=totals.maximum_raw_fk_pivot_error<=SkinBinding.CALIBRATION_TOLERANCE
	result["candidate_contact_gate"]=failed.is_empty() and result.raw_fk_reconstruction_agrees and (profile=="original_zero_colliders" or all_stages_clear)
	check(result.raw_fk_reconstruction_agrees and (profile=="original_zero_colliders" or all_stages_clear),"candidate raw solver raw-FK and final particles segments and hair vertices clear unchanged measured capsule")
	if not all_stages_clear and profile!="original_zero_colliders":result["contact_failure_code"]="MEASURED_CAPSULE_NONPENETRATION_FAILED"
	var captured: bool=await capture_private()
	check(captured,"bounded actual native live-frame capture remains private and local")
	result["private_render_captures"]=1 if captured else 0
	await finish()
