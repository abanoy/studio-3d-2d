extends SceneTree
# Steady-frame CPU evaluation only; excludes startup, input, rendering and export.
const Storage=preload("res://src/storage.gd")
const Parts=preload("res://src/character_parts.gd")
var app
func _initialize() -> void:
	create_timer(100).timeout.connect(func():push_error("Following benchmark timeout");quit(2));call_deferred("run")
func stats(values: Array) -> Dictionary:
	values.sort();var total:=0.
	for value in values:total+=value
	return {"samples":values.size(),"mean_ms":total/values.size()/1000.,"median_ms":float(values[values.size()/2])/1000.,"p95_ms":float(values[int(ceil(values.size()*.95))-1])/1000.,"max_ms":float(values[-1])/1000.}
func run() -> void:
	var args:=OS.get_cmdline_user_args()
	if args.size()!=1:push_error("Supply an existing prepared project directory.");quit(2);return
	var folder:=ProjectSettings.globalize_path("res://output/parts-follow/benchmark-"+str(Time.get_ticks_usec()))
	DirAccess.make_dir_recursive_absolute(folder)
	app=load("res://main.tscn").instantiate();app.display_prefs_path=folder.path_join("prefs.cfg");app.recovery_root=folder.path_join("recovery");app.recent_path=folder.path_join("recents.json")
	root.gui_embed_subwindows=true;root.add_child(app)
	for i in range(4):await process_frame
	app.autosave_enabled.set_pressed_no_signal(false);app.has_project.cache_root=folder.path_join("cache");app.new_project()
	var loaded:=Storage.load_project(args[0])
	if loaded.has("error") or not app.restore_world(loaded.world).is_empty():app.free();quit(1);return
	var runtime: RefCounted=app.renderer.world_runtime;var group_id:="";var body_id:="";var target_id:="";var bones:=0
	for id in runtime.order:
		var actor: RefCounted=runtime.instance(id);bones+=actor.bones.size()
		if actor.data.kind=="group":group_id=id
		elif actor.data.metadata.character_part.role=="body":body_id=id
		elif actor.data.metadata.character_part.role=="dress":target_id=id
	var mapping: Dictionary=runtime.follow_report(target_id)
	if mapping.has("error") or mapping.matched==0:app.free();quit(1);return
	var plan: Dictionary=runtime.part_follow.plans[mapping.plan_key];var chosen:=-1
	for index in plan.links:
		if str(plan.master.names[plan.links[index]]).to_lower().contains("upperarm"):chosen=plan.links[index];break
	if chosen<0:app.free();quit(1);return
	var body: RefCounted=runtime.instance(body_id);var part: RefCounted=runtime.instance(target_id)
	var posed: Dictionary=body.data.duplicate(true);var q:=Quaternion(Vector3.FORWARD,.3)
	posed.pose[plan.master.ids[chosen]]={"position":[0,0,0],"rotation_xyzw":[q.x,q.y,q.z,q.w]}
	if not runtime.restore_instance(body_id,posed).is_empty():app.free();quit(1);return
	var body_pose: Dictionary=body.data.pose.duplicate(true);var part_pose: Dictionary=part.data.pose.duplicate(true)
	var off: Array=[];var on: Array=[]
	for enabled in [false,true,false,true]:
		var edit:=Parts.follow_edit(app.current_world(),group_id,{target_id:enabled},body_id,int(app.video.duration_frames))
		if edit.has("error") or not runtime.restore_instances(edit.after).is_empty():app.free();quit(1);return
		for warm in range(8):runtime.evaluate(0,false,body_id,app.video)
		for i in range(60):
			var start:=Time.get_ticks_usec();runtime.evaluate(0,false,body_id,app.video);var elapsed:=Time.get_ticks_usec()-start
			if enabled:on.append(elapsed)
			else:off.append(elapsed)
		if enabled and runtime.part_follow.reports[target_id].has("error"):app.free();quit(1);return
	if body.data.pose!=body_pose or part.data.pose!=part_pose:app.free();quit(1);return
	var result: Dictionary={"scope":"headless steady whole-world evaluation; no render/input/export","world_objects":runtime.instances.size(),"bones":bones,"matched":mapping.matched,"off":stats(off),"on":stats(on),"authored_poses_unchanged":true,"native_fidelity_qualified":false}
	app.free()
	for i in range(4):await process_frame
	print("PARTS_FOLLOW_BENCHMARK "+JSON.stringify(result));quit(0)
