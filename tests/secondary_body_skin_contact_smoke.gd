extends "res://tests/secondary_body_contact_visual.gd"
# CPU-only actual imported skin measurement; no native rendering or old host.
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=4 or DisplayServer.get_name()!="headless" or FileAccess.get_sha256(args[1])!=PROJECT_SHA:push_error("Use owned headless data and protected saved case plus original calibration inputs");quit(2);return
	var folder: String=args[0];var archive: String=args[1]
	root.size=Vector2i(1600,1000);root.gui_embed_subwindows=true
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recent.json");root.add_child(app);await settle();app.home.hide();app.autosave_enabled.button_pressed=false;app.has_project.cache_root=folder.path_join("cache");app.has_project.open_file(archive)
	while app.has_project.pid>0:await process_frame
	await settle();var actor: RefCounted
	for value in app.renderer.world_runtime.instances.values():
		if value.data.sha256==MODEL_SHA:actor=value
	check(actor!=null,"protected exact Miku model opens headlessly")
	if actor==null:await app.quit_studio();quit(1);return
	actor.apply(0,true);var before: PackedByteArray=var_to_bytes(actor.data)
	var input: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(args[2]));var alignment: PackedByteArray=FileAccess.get_file_as_bytes(args[3])
	var prepared: Dictionary=SkinBinding.prepare(actor,input,alignment)
	check(not prepared.has("error") and prepared.cache.hair.size()==989,"original source and actual imported989-vertex hair surface calibrate")
	if prepared.has("error"):push_error(str(prepared.error));await app.quit_studio();quit(1);return
	skin_cache=prepared.cache
	var made: Dictionary=Spring.construct(actor)
	check(not made.has("error"),"runtime body and cached actual-skin contact starts")
	if made.has("error"):await app.quit_studio();quit(1);return
	var live:=Live.new();live.rig=actor;live.runner=made.runner;live.initial_pose=actor.sample(0,true);live.latest=live.initial_pose.duplicate(true);live.initial_world=actor.root.global_transform;await settle();live.start()
	var fields: Array=Airflow.collect(app.renderer,0.,{});var minimum:=INF;var pairs:=0;var palette:=0.;var error:="";var blocked:=0
	for tick in range(480):
		error=live.advance(1./120.,0,0.,false,fields,app.renderer.world_runtime)
		if not error.is_empty():break
		var measured: Dictionary=skin_clearance(actor,live.runner)
		if measured.has("error"):error=measured.error;break
		minimum=minf(minimum,measured.minimum_skin_clearance);pairs+=measured.penetrating_skin_vertex_pairs;palette=maxf(palette,measured.maximum_palette_disagreement);blocked=maxi(blocked,int(live.runner.contact_info.get("blocked_attachments",0)))
	check(error.is_empty() and palette<=SkinBinding.CALIBRATION_TOLERANCE,"all480 actual FK skin evaluations retain exact source/runtime palette agreement")
	check(pairs==0 and minimum>=-.00005,"all989 skinned hair vertices clear actual runtime arm capsules for480ticks at unchanged tolerance")
	var contact_stats: Dictionary=live.runner.contact_info.get("skin_cache",{}).duplicate(true)
	check(contact_stats.get("vertices",0)==989 and contact_stats.get("array_reads",0)>0 and contact_stats.get("hot_array_reads",-1)==0,"actual skin inventory is built once with no surface-array reads during480 hot ticks")
	var control: RefCounted=live.runner.skin_contact;var changed_mesh: MeshInstance3D
	for source in control.sources:
		var mesh: MeshInstance3D=source.mesh.get_ref()
		if mesh.mesh.get_blend_shape_count()>0:changed_mesh=mesh;break
	check(changed_mesh!=null,"saved model supplies a real blendshape mesh for stale-contact guard")
	if changed_mesh:
		var amount: float=changed_mesh.get_blend_shape_value(0);changed_mesh.set_blend_shape_value(0,amount+.01)
		var stale: Dictionary=live.runner.constrain_pose(live.latest)
		changed_mesh.set_blend_shape_value(0,amount)
		check(stale.has("error") and not live.runner.constrain_pose(live.latest).has("error"),"a changed actual blend amount refuses stale geometry and the restored shape remains usable")
	else:check(false,"real blendshape guard was exercised")
	live.stop();live.dispose();actor.apply(0,true)
	check(control.watches.is_empty() and control.rows.is_empty(),"Off disconnects resource callbacks and releases cached skin geometry")
	check(var_to_bytes(actor.data)==before and FileAccess.get_sha256(archive)==PROJECT_SHA,"actual surface check restores authored state and preserves original project")
	print("SECONDARY_BODY_SKIN_CONTACT "+JSON.stringify({"checks":checks,"failures":failures,"user_profile":OS.get_user_data_dir(),"ticks":480,"hair_vertices":989,"minimum_skin_clearance":minimum,"penetrating_skin_vertex_pairs":pairs,"maximum_palette_disagreement":palette,"blocked_attachments":blocked,"contact_stats":contact_stats,"graphics_used":false,"source_arrays_published":false}));await app.quit_studio();quit(0 if failures==0 else 1)
