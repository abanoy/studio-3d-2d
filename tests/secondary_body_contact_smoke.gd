extends "res://tests/secondary_body_colliders_smoke.gd"
const Live=preload("res://src/secondary_live.gd")
const Airflow=preload("res://src/airflow.gd")
const Definition=preload("res://src/secondary_rig.gd")
func clearance(actor: RefCounted,runner: RefCounted) -> Dictionary:
	var particle:=INF;var segment:=INF;var points:=0;var links:=0
	for chain in runner.chains:
		var pivots: Array=[]
		for joint in chain.source.joints:pivots.append(Definition.binding_transform(actor,joint.binding).origin)
		for collider in chain.colliders:
			var c: Dictionary=collider.definition;var a: Transform3D=Definition.binding_transform(actor,c.binding)
			var b: Vector3=Definition.binding_transform(actor,c.tail_binding).origin
			var radius: float=c.radius*a.basis.get_scale().x
			for i in range(pivots.size()):
				var scale: float=Definition.binding_transform(actor,chain.source.joints[i].binding).basis.get_scale().x
				var hair: float=chain.source.joints[i].radius*scale
				particle=minf(particle,Fit.point_segment(pivots[i],a.origin,b)-radius-hair);points+=1
				if i==0:continue
				var pair: PackedVector3Array=Geometry3D.get_closest_points_between_segments(pivots[i-1],pivots[i],a.origin,b)
				segment=minf(segment,pair[0].distance_to(pair[1])-radius-hair);links+=1
	return {"particle_clearance":particle,"segment_clearance":segment,"particle_pairs":points,"segment_pairs":links}
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=2 or DisplayServer.get_name()!="headless" or FileAccess.get_sha256(args[1])!=PROJECT_SHA:push_error("Use owned headless output and protected saved case");quit(2);return
	var folder: String=args[0];var archive: String=args[1]
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle()
	app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(archive)
	while app.has_project.pid>0:await process_frame
	await settle()
	var actor: RefCounted
	for value in app.renderer.world_runtime.instances.values():
		if value.data.sha256==MODEL_SHA:actor=value
	check(actor!=null,"saved Miku installs through normal Open")
	if actor==null:await app.quit_studio();quit(1);return
	actor.apply(0,true);var data: PackedByteArray=var_to_bytes(actor.data);var definition: PackedByteArray=var_to_bytes(actor.root.get_meta("has_secondary_rig"));var history: int=app.history.size()
	var made: Dictionary=Spring.construct(actor)
	check(not made.has("error"),"ordinary scratch runner with generated arm collisions starts headlessly")
	if made.has("error"):await app.quit_studio();quit(1);return
	var runner: RefCounted=made.runner;await settle()
	var live:=Live.new();live.rig=actor;live.runner=runner;live.initial_pose=actor.sample(0,true);live.latest=live.initial_pose.duplicate(true);live.initial_world=actor.root.global_transform;live.start()
	var fields: Array=Airflow.collect(app.renderer,0.,{})
	check(not fields.is_empty() and runner.chains[0].colliders.size()==4,"saved fan field and four actual runtime arm capsules are present")
	var initial: Dictionary=clearance(actor,runner);var error:="";var minimum_segment: float=initial.segment_clearance;var active_minimum:=INF
	for tick in range(480):
		error=live.advance(1./120.,0,0.,false,fields,app.renderer.world_runtime)
		if not error.is_empty():break
		var current: Dictionary=clearance(actor,runner);minimum_segment=minf(minimum_segment,current.segment_clearance);active_minimum=minf(active_minimum,current.segment_clearance)
	check(error.is_empty(),"480 fixed CPU ticks produce ordinary secondary poses")
	var final: Dictionary=clearance(actor,runner)
	check(is_finite(final.particle_clearance) and is_finite(final.segment_clearance),"whole-link and particle clearance measurements remain finite")
	check(active_minimum>=-.00005,"all480 displayed fixed ticks clear whole arm capsules at the existing measurement tolerance")
	var moved: bool=live.latest!=live.initial_pose
	check(moved,"saved airflow produces a changed hair pose")
	var local_positions_preserved:=true
	for id in live.latest:
		if live.latest[id].position!=live.initial_pose.get(id,{"position":[0,0,0]}).position:local_positions_preserved=false
	check(local_positions_preserved,"contact deflection changes rotations without stretching or translating authored joints")
	var first_output: PackedByteArray=var_to_bytes(live.latest)
	live.stop();live.dispose();actor.apply(0,true);await settle()
	made=Spring.construct(actor);runner=made.runner;await settle()
	live=Live.new();live.rig=actor;live.runner=runner;live.initial_pose=actor.sample(0,true);live.latest=live.initial_pose.duplicate(true);live.initial_world=actor.root.global_transform;live.start()
	for tick in range(480):
		error=live.advance(1./120.,0,0.,false,fields,app.renderer.world_runtime)
		if not error.is_empty():break
	check(error.is_empty() and var_to_bytes(live.latest)==first_output,"fresh identical fixed-step run produces exact same recordable FK pose")
	live.stop();live.dispose();actor.apply(0,true);await settle()
	check(var_to_bytes(actor.data)==data and var_to_bytes(actor.root.get_meta("has_secondary_rig"))==definition and app.history.size()==history,"Off disposal restores authored model and leaves source rig and Undo intact")
	check(FileAccess.get_sha256(archive)==PROJECT_SHA and actor.live_pose==null,"original project remains unchanged and live ownership is released")
	print("SECONDARY_BODY_CONTACT "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"ticks_per_run":480,"runs":2,"initial":initial,"final":final,"minimum_segment_clearance":minimum_segment,"active_minimum_segment_clearance":active_minimum,"contact_clearance_tolerance_changed":false,"graphics_or_skin_surface_contact_qualified":false}));await app.quit_studio();quit(0 if failures==0 else 1)
