extends SceneTree
# Optional protected input is never embedded; only scalar geometry metrics leave this test.
const Spring=preload("res://src/secondary_spring.gd")
const ReferenceSkin=preload("res://tests/reference/secondary_skin_contact_baseline.gd")
const ContactFK=preload("res://src/secondary_segment_contact.gd")
const Motion=preload("res://src/generated_secondary_motion.gd")
const Bounds=preload("res://src/pose_bounds.gd")
const Shape=preload("res://src/source_shape.gd")
var app
var checks:=0
var failures:=0
var mesh: MeshInstance3D
var surface:=0
var selected: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks+=1;print(("PASS " if ok else "FAIL ")+label)
	if not ok:failures+=1
func settle() -> void:
	for i in range(4):await process_frame
func geometry() -> Dictionary:
	var arrays: Array=mesh.mesh.surface_get_arrays(surface)
	var vertices: PackedVector3Array=Shape.vertices(mesh,surface,arrays[Mesh.ARRAY_VERTEX])
	var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES];var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
	var context:={"error":"","palettes":{},"updated":{}};var palette: Array=Bounds.palette(mesh,context)
	if not context.error.is_empty():return {"error":context.error}
	var stride: int=bones.size()/vertices.size();var center:=Vector3.ZERO;var points:=PackedVector3Array()
	for index in selected:
		var v:=int(index);var p:=Vector3.ZERO
		for j in range(stride):p+=(palette[bones[v*stride+j]]*vertices[v])*weights[v*stride+j]
		var world: Vector3=mesh.global_transform*p;center+=world;points.append(world)
	return {"error":"","count":selected.size(),"center":center/selected.size(),"points":points}
func complete_fk(pose: Dictionary,actor: RefCounted) -> Dictionary:
	var context: Dictionary={"cache":{},"visiting":{},"error":""};var worlds: Dictionary={}
	for id in actor.order:worlds[id]=ContactFK.world(actor,str(id),pose,context)
	return {"error":context.error,"worlds":worlds}
func same_solver_metrics(a: Dictionary,b: Dictionary) -> bool:
	for key in ["vertices","array_reads","refreshes","corrections","blocked_points","hot_array_reads","remaining_pairs","minimum_gap","iteration_limit_hits"]:
		if not a.has(key) or not b.has(key) or a[key]!=b[key]:return false
	return true
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=5 or DisplayServer.get_name()!="headless":quit(2);return
	var folder: String=args[0];var candidate: String=args[1];var spec: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[2]));var original: String=args[3]
	var source_sha:=FileAccess.get_sha256(original);var candidate_sha:=FileAccess.get_sha256(candidate)
	var expected_cache_sha: String=args[4];var cache_sha: String=FileAccess.get_sha256("res://src/secondary_skin_contact.gd")
	if cache_sha!=expected_cache_sha:quit(2);return
	root.size=Vector2i(1400,900);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache")
	check(app.pose_editor.add_model(candidate).is_empty(),"ordinary Add model loads the owned reconstructed candidate")
	var actor: RefCounted=app.renderer.active_model();var authored: Dictionary=actor.data.duplicate(true)
	var matches: Array=[]
	for item in actor.root.find_children("*","MeshInstance3D",true,false):
		if item.mesh==null or item.skin==null:continue
		for s in range(item.mesh.get_surface_count()):
			var arrays: Array=item.mesh.surface_get_arrays(s)
			if arrays[Mesh.ARRAY_VERTEX].size()==int(spec.source_vertices):matches.append([item,s])
	check(matches.size()==1,"selected original source surface maps uniquely into the imported candidate")
	if matches.size()!=1:await app.quit_studio();quit(1);return
	mesh=matches[0][0];surface=int(matches[0][1]);selected=spec.selected_vertices
	var arrays: Array=mesh.mesh.surface_get_arrays(surface);var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var max_error:=0.
	for i in range(vertices.size()):
		var p: Array=spec.positions[i];max_error=maxf(max_error,vertices[i].distance_to(Vector3(p[0],p[1],p[2])))
	check(max_error<.000001 and selected.size()==int(spec.reviewed_vertices),"all reviewed vertex IDs retain exact source geometry correspondence")
	actor.data.metadata[Motion.KEY]={"format":Motion.FORMAT,"mode":"natural"};actor.apply(0,true)
	var data: PackedByteArray=var_to_bytes(actor.data);var rig: PackedByteArray=var_to_bytes(actor.root.get_meta("has_secondary_rig"));var originals: Dictionary={}
	for id in actor.order:
		if not Motion.normalized(str(actor.bones[id].name)).begins_with("haslooserebuilt"):originals[id]=actor.bone_transform(id)
	var before: Dictionary=geometry();var made: Dictionary=Spring.construct(actor)
	check(not made.has("error"),"generated multi-anchor guides construct through the ordinary simulation path")
	if made.has("error"):print(str(made.error));await app.quit_studio();quit(1);return
	var runner: RefCounted=made.runner;var anchors: Dictionary={}
	runner.defer_skin_contact=true
	# Spring constructs the ACTUAL installed production solver. Do not mistake
	# that new solver for the legacy baseline after adoption.
	var cached_control: RefCounted=runner.skin_contact
	var baseline_made: Dictionary=ReferenceSkin.create(actor,runner.chains)
	if baseline_made.has("error"):
		print("FAIL native reference baseline construction");runner.dispose();await app.quit_studio();quit(1);return
	var baseline_ref: RefCounted=baseline_made.control
	var lease_held: bool=runner.rest_view_token>0 and runner.rest_view_controller!=0
	for chain in runner.chains:anchors[chain.ids[0]]=actor.bone_transform(chain.ids[0]).origin
	await settle()
	var chain_count: int=runner.chains.size();var natural_chains:=0
	var collider_count:=0
	for chain in runner.chains:
		if chain.natural_gravity:natural_chains+=1
		collider_count+=chain.colliders.size()
	check(chain_count==int(spec.expected_chains) and actor.order.size()-originals.size()==int(spec.expected_guide_bones),"all expected guide chains and new skin bones are present")
	check(runner.skin_contact!=null and collider_count>0,"ordinary body colliders and weighted-surface contact are actually active")
	var issue:="";var minimum_gap:=0.;var maximum_remaining:=0;var started:=Time.get_ticks_usec()
	var compared_ticks:=0;var exact_pose:=true;var exact_fk:=true;var exact_metrics:=true;var input_preserved:=true
	var baseline_usec:=0;var cached_usec:=0;var baseline_max_usec:=0;var cached_max_usec:=0
	var first_mismatch_tick: int=-1;var first_mismatch_kind: String=""
	for tick in range(720):
		actor.live_pose={};actor.apply_current(0,true);var step: Dictionary=runner.step(1./120.,Vector3.ZERO)
		if step.has("error"):issue=str(step.error);break
		var raw_pose: Dictionary=step.pose;var raw_bytes: PackedByteArray=var_to_bytes(raw_pose)
		var baseline_result: Dictionary={};var cached_result: Dictionary={};var call_started: int=0;var elapsed: int=0
		# Alternate order. Only the ordinary constrain call is timed: no FK,
		# comparisons, actor apply, logging or baseline instrumentation is inside.
		if tick%2==0:
			call_started=Time.get_ticks_usec();baseline_result=baseline_ref.constrain(actor,runner.chains,raw_pose);elapsed=Time.get_ticks_usec()-call_started
			baseline_usec+=elapsed;baseline_max_usec=maxi(baseline_max_usec,elapsed)
			call_started=Time.get_ticks_usec();cached_result=cached_control.constrain(actor,runner.chains,raw_pose);elapsed=Time.get_ticks_usec()-call_started
			cached_usec+=elapsed;cached_max_usec=maxi(cached_max_usec,elapsed)
		else:
			call_started=Time.get_ticks_usec();cached_result=cached_control.constrain(actor,runner.chains,raw_pose);elapsed=Time.get_ticks_usec()-call_started
			cached_usec+=elapsed;cached_max_usec=maxi(cached_max_usec,elapsed)
			call_started=Time.get_ticks_usec();baseline_result=baseline_ref.constrain(actor,runner.chains,raw_pose);elapsed=Time.get_ticks_usec()-call_started
			baseline_usec+=elapsed;baseline_max_usec=maxi(baseline_max_usec,elapsed)
		if baseline_result.has("error") or cached_result.has("error"):
			issue="Baseline or staged contact cache refused at tick%d"%tick;first_mismatch_tick=tick;first_mismatch_kind="solver_error";break
		var tick_pose: bool=baseline_result.pose==cached_result.pose and var_to_bytes(baseline_result.pose)==var_to_bytes(cached_result.pose)
		var baseline_fk: Dictionary=complete_fk(baseline_result.pose,actor);var cached_fk: Dictionary=complete_fk(cached_result.pose,actor)
		var tick_fk: bool=baseline_fk.error.is_empty() and cached_fk.error.is_empty() and baseline_fk.worlds==cached_fk.worlds and var_to_bytes(baseline_fk.worlds)==var_to_bytes(cached_fk.worlds)
		var tick_metrics: bool=same_solver_metrics(baseline_result.stats,cached_result.stats)
		var tick_input: bool=var_to_bytes(raw_pose)==raw_bytes
		exact_pose=exact_pose and tick_pose;exact_fk=exact_fk and tick_fk;exact_metrics=exact_metrics and tick_metrics;input_preserved=input_preserved and tick_input
		compared_ticks+=1
		# Only the baseline result drives the ordinary next tick trajectory.
		actor.live_pose=baseline_result.pose;actor.apply_current(0,true)
		minimum_gap=minf(minimum_gap,runner.skin_contact.stats.minimum_gap);maximum_remaining=maxi(maximum_remaining,int(runner.skin_contact.stats.remaining_pairs))
		if not tick_pose or not tick_fk or not tick_metrics or not tick_input:
			first_mismatch_tick=tick;first_mismatch_kind="pose_or_fk" if not tick_pose or not tick_fk else ("metrics" if not tick_metrics else "input_mutation")
			issue="Exact native cache comparison failed";break
	var tick_usec:=float(Time.get_ticks_usec()-started)/720.;var after: Dictionary=geometry();var anchor_error:=0.;var original_error:=0.
	for id in anchors:anchor_error=maxf(anchor_error,actor.bone_transform(id).origin.distance_to(anchors[id]))
	for id in originals:
		var current: Transform3D=actor.bone_transform(id);var saved: Transform3D=originals[id]
		original_error=maxf(original_error,current.origin.distance_to(saved.origin))
		for axis in range(3):original_error=maxf(original_error,current.basis[axis].distance_to(saved.basis[axis]))
	var drop: float=before.center.y-after.center.y
	check(issue.is_empty() and before.error.is_empty() and after.error.is_empty(),"all guide groups simulate with ordinary contacts enabled")
	check(drop>.01,"entire reviewed section centroid settles downward by more than one centimeter")
	check(anchor_error<.000001 and original_error<.000001,"every guide attachment and original native body/hair joint stays fixed")
	var final_remaining: int=runner.skin_contact.stats.remaining_pairs if runner.skin_contact else 0
	var skin_vertices: int=runner.skin_contact.stats.vertices if runner.skin_contact else 0
	var skin_refreshes: int=runner.skin_contact.stats.refreshes if runner.skin_contact else 0
	var baseline_solver_stats: Dictionary=baseline_ref.stats.duplicate(true);var cached_solver_stats: Dictionary=cached_control.stats.duplicate(true)
	baseline_ref.dispose();runner.dispose();actor.live_pose=null;actor.apply(0,true);var restored: Dictionary=geometry()
	var restored_error:=0.
	for v in range(before.points.size()):restored_error=maxf(restored_error,before.points[v].distance_to(restored.points[v]))
	check(restored_error<.000001,"Off restores every reviewed vertex to authored geometry")
	check(var_to_bytes(actor.data)==data and var_to_bytes(actor.root.get_meta("has_secondary_rig"))==rig,"simulation preserves authored keys and imported rig declarations")
	check(FileAccess.get_sha256(original)==source_sha and FileAccess.get_sha256(candidate)==candidate_sha,"original native asset and new owned candidate remain read-only")
	check(compared_ticks==720 and exact_pose and exact_fk and input_preserved,"every native tick preserves exact complete pose/FK dictionaries and bytes without mutating raw input")
	check(compared_ticks==720 and exact_metrics,"every native tick preserves exact corrections blocked residual minimum-gap and iteration-hit metrics")
	check(cache_sha==expected_cache_sha and str(cached_control.get_script().resource_path)=="res://src/secondary_skin_contact.gd" and lease_held and baseline_solver_stats.refreshes==720 and cached_solver_stats.refreshes==720 and cached_solver_stats.get("cache_eligible_calls",0)==720 and cached_solver_stats.get("cache_fallback_calls",0)==0 and cached_solver_stats.get("broad_tests",0)>0 and cached_solver_stats.get("narrow_tests",0)>0 and baseline_solver_stats.corrections>0,"actual production cache executes all720 independently timed calls under ordinary flexible lease")
	var metrics:={"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"selected_vertices":selected.size(),"chains":chain_count,"natural_chains":natural_chains,"collider_instances":collider_count,"skin_vertices":skin_vertices,"skin_refreshes":skin_refreshes,"centroid_drop":drop,"average_tick_usec":tick_usec,"anchor_error":anchor_error,"original_joint_error":original_error,"maximum_off_vertex_error":restored_error,"minimum_contact_gap":minimum_gap,"maximum_remaining_contact_pairs":maximum_remaining,"final_remaining_contact_pairs":final_remaining}
	metrics["production_skin_sha256"]=cache_sha;metrics["compared_ticks"]=compared_ticks
	metrics["exact_pose"]=exact_pose;metrics["exact_full_fk"]=exact_fk;metrics["exact_solver_metrics"]=exact_metrics;metrics["raw_input_preserved"]=input_preserved
	metrics["baseline_solver_mean_usec"]=float(baseline_usec)/maxi(1,compared_ticks);metrics["candidate_solver_mean_usec"]=float(cached_usec)/maxi(1,compared_ticks)
	metrics["baseline_solver_max_usec"]=baseline_max_usec;metrics["candidate_solver_max_usec"]=cached_max_usec
	metrics["comparison_order_alternated"]=true;metrics["whole_tick_includes_both_solvers_and_comparisons"]=true
	metrics["first_mismatch_tick"]=first_mismatch_tick;metrics["first_mismatch_kind"]=first_mismatch_kind
	metrics["baseline_solver_stats"]={};metrics["candidate_solver_stats"]={}
	for key in ["vertices","array_reads","refreshes","corrections","blocked_points","hot_array_reads","remaining_pairs","minimum_gap","iteration_limit_hits"]:
		metrics.baseline_solver_stats[key]=baseline_solver_stats.get(key);metrics.candidate_solver_stats[key]=cached_solver_stats.get(key)
	for key in ["cache_eligible_calls","cache_fallback_calls","broad_tests","narrow_tests","row_cache_hits","row_cache_misses","row_summaries","cache_verification_scans"]:
		if cached_solver_stats.has(key):metrics.candidate_solver_stats[key]=cached_solver_stats[key]
	print("SECONDARY_CONTACT_CACHE_NATIVE "+JSON.stringify(metrics));FileAccess.open(folder.path_join("metrics.json"),FileAccess.WRITE).store_string(JSON.stringify(metrics,"",true,true))
	await app.quit_studio();quit(0 if failures==0 else 1)
